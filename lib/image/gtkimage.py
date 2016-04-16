from __future__ import division

import os
from xml.sax.saxutils import escape

from gi.repository import Gtk, Gdk, GdkPixbuf, GObject

from tooltip import ToolTip
from ..constants import CACHE_DIR
from ..settings import SETTINGS, SETTINGS_FILTER, SETTINGS_GEOMETRY

class PhotoImage(object):

    def __init__(self, photoframe):
        self.window = photoframe.window
        self.photoframe = photoframe
        self.tooltip = ToolTip(self.window)

    def set_photo(self, photo=False):
        if photo is not False:
            self.photo = photo

        width, height = self._get_max_display_size()
        self.pixbuf = PhotoImagePixbuf(self.window, width, height)

        if self.pixbuf.set(self.photo) is False:
            return False

        self._set_tips(self.photo)
        # self.window.resize(1, 1) # FIXME: black magic?
        self._set_photo_image(self.pixbuf.data)
        self.window_border = SETTINGS.get_int('border-width')

        return True

    def on_enter_cb(self, widget, event):
        pass

    def on_leave_cb(self, widget, event):
        pass

    def check_actor(self, stage, event):
        return False

    def check_mouse_on_window(self):
        window, x, y = Gdk.Window.at_pointer() or [None, None, None]
        result = window is self.image.get_window()
        return result

    def has_trash_dialog(self):
        return False

    def _get_max_display_size(self):
        width = SETTINGS_GEOMETRY.get_int('max-width') or 400
        height = SETTINGS_GEOMETRY.get_int('max-height') or 300
        return width, height

    def _set_tips(self, photo):
        self.tooltip.update_photo(photo)

class PhotoImageGtk(PhotoImage):

    def __init__(self, photoframe):
        super(PhotoImageGtk, self).__init__(photoframe)

        self.image = Gtk.Image()
        self.image.show()

    def _set_photo_image(self, pixbuf):
        self.image.set_from_pixbuf(pixbuf)
        self.w = pixbuf.get_width()
        self.h = pixbuf.get_height()

    def clear(self):
        self.image.clear()

class PhotoImagePixbuf(object):

    def __init__(self, window, max_w=400, max_h=300):
        self.window = window
        self.max_w = max_w
        self.max_h = max_h

    def set(self, photo):
        if not photo:
            pixbuf = self._no_image()
            self.data = pixbuf
            return True

        try:
            filename = photo['filename']
            if not self._file_size_is_ok(filename, photo): return False

            photo.get_exif()
            orientation = photo.get('orientation')
            rotation = self._get_orientation(orientation)

            if photo.get('size'):
                org_w, org_h = photo['size']
                w, h = self.get_scale(org_w, org_h, 
                                      self.max_w, self.max_h, rotation)
                # print org_w, org_h, w, h, " ", photo
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(filename, w, h)
            else:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file(filename)

        except (GObject.GError, OSError), err_info:
            print err_info
            return False

        rotation = self._get_orientation(pixbuf.get_option('orientation') or 1)

        # scale
        if 'size' not in photo:
            org_w, org_h = pixbuf.get_width(), pixbuf.get_height()
            w, h = self.get_scale(org_w, org_h, 
                                  self.max_w, self.max_h, rotation)
            pixbuf = pixbuf.scale_simple(w, h, GdkPixbuf.InterpType.BILINEAR)

        # rotate
        pixbuf = pixbuf.rotate_simple(rotation)

        if not self._aspect_ratio_is_ok(pixbuf): return False
        if not self._image_size_is_ok(org_h, org_w): return False

        # photo.get_exif()

        if self.max_src_size > 800:
            url = photo.get('url')
            path = 'thumb_' + url.replace('/', '_')
            filename = os.path.join(CACHE_DIR, path)
            pixbuf.savev(filename, "jpeg", [], [])

        self.data = pixbuf
        return True

    def _get_orientation(self, orientation=1):
        if not orientation:
            orientation = 1
        orientation = int(orientation)

        if orientation == 6:
            rotate = 270
        elif orientation == 8:
            rotate = 90
        else:
            rotate = 0

        # print "a", orientation, rotate

        return rotate

    def get_scale(self, src_w, src_h, max_w, max_h, rotation=0):
        if rotation:
            max_w, max_h = max_h, max_w

        if src_w / max_w > src_h / max_h:
            ratio = max_w / src_w
        else:
            ratio = max_h / src_h

        w = int( src_w * ratio + 0.4 )
        h = int( src_h * ratio + 0.4 )

        self.max_src_size = src_w if src_w > src_h else src_h
        return w, h

    def _file_size_is_ok(self, filename, photo):
        min = SETTINGS_FILTER.get_double('min-file-size-kb') * 1024
        max = SETTINGS_FILTER.get_double('max-file-size-mb') * 1024 ** 2
       
        size = os.path.getsize(filename)

        url = photo.get('url')

        if min > 0 and size < min:
            print "Skip a small image (%.2f KB): %s" % (size / 1024, url)
            return False
        elif max > 0 and size > max:
            print "Skip a large image (%.2f MB): %s" % (size / 1024**2, url)
            return False
        elif url.find('static.flickr.com') > 0 and size < 4000:
            # ad-hoc for avoiding flickr no image.
            # print "Obsolete URL: %s" % photo.get('url')
            return False
        else:
            return True

    def _aspect_ratio_is_ok(self, pixbuf):
        aspect = pixbuf.get_width() / pixbuf.get_height()

        max = SETTINGS_FILTER.get_double('aspect-max') or 0
        min = SETTINGS_FILTER.get_double('aspect-min') or 0

        # print aspect, max, min

        if min < 0 or max < 0:
            print "Error: aspect_max or aspect_min is less than 0."
            return True
        elif min > 0 and max > 0 and min >= max:
            print "Error: aspect_max is not greater than aspect_min."
            return True

        if (min > 0 and aspect < min ) or (max > 0 and max < aspect):
            print "Skip a tall or wide image (aspect ratio: %s)." % aspect
            return False
        else:
            return True

    def _image_size_is_ok(self, w, h):
        if w is None or h is None:
            print "no size!"
            return True

        min_width = SETTINGS_FILTER.get_int('min-width') or 0
        min_height = SETTINGS_FILTER.get_int('min-height') or 0
        if min_width <= 0 or min_height <= 0: return True

        if w < min_width or h < min_height:
            print "Skip a small size image (%sx%s)." % (w, h)
            return False
        else:
            return True

    def _no_image(self):
        w = int(self.max_w)
        h = int(self.max_h)

        pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8 , w, h)
        pixbuf.fill(0x00000000)
        return pixbuf

class PhotoImageFullScreen(PhotoImageGtk):

    def _get_max_display_size(self):
        screen = Gdk.Screen.get_default()
        display_num = screen.get_monitor_at_window(self.window.get_window())
        geometry = screen.get_monitor_geometry(display_num)
        return geometry.width, geometry.height

    def _set_tips(self, photo):
        self.tooltip.update_text() # Erase Tooltip

class PhotoImageScreenSaver(PhotoImageFullScreen):

    def _get_max_display_size(self):
        return self.window.w, self.window.h
