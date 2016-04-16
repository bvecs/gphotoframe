from __future__ import division

try:
    from gi.repository import Clutter, GtkClutter
except ImportError:
    from ...utils.nullobject import Null
    GtkClutter = Null()
    GtkClutter.Texture = Null()

from ..animation import FadeAnimationTimeline
from ...settings import SETTINGS_UI

import os  # FIXME (for pixbuf)
from ...constants import CACHE_DIR # FIXME (for pixbuf)

class Texture(GtkClutter.Texture):

    def __init__(self, stage=None):
        super(Texture, self).__init__()
        super(Texture, self).hide() # FIXME?

        self.set_reactive(True)
        self.connect('button-press-event', self._on_button_press_cb)
        if stage:
            stage.add_actor(self)

        self._set_animation_timeline()

    def change(self, pixbuf, x, y):
        self._set_texture_from_pixbuf(pixbuf)
        self.set_position(x, y)

    def _set_animation_timeline(self):
        self.timeline = FadeAnimationTimeline(self)

    def _on_button_press_cb(self, actor, event):
        pass

    def _set_texture_from_pixbuf(self, pixbuf):
        bpp = 4 if pixbuf.props.has_alpha else 3

        # FIXME
        tmp_file = os.path.join(CACHE_DIR, 'gphotoframe_tmp.png')
        pixbuf.savev(tmp_file, 'png', [], [])
        self.set_from_file(tmp_file)

#         self.set_from_rgb_data(
#             pixbuf.get_pixels(),
#             pixbuf.props.has_alpha,
#             pixbuf.props.width,
#             pixbuf.props.height,
#             pixbuf.props.rowstride,
#             bpp)

class IconTexture(Texture):

    def __init__(self, stage):
        super(IconTexture, self).__init__(stage)
        self.has_animation = SETTINGS_UI.get_boolean('animate-icons')

        if self.has_animation:
            self.set_opacity(0)

    def show(self):
        super(IconTexture, self).show()
        super(IconTexture, self).set_reactive(True)

        if self.has_animation and not self.get_opacity():
            self.timeline.fade_in()

    def hide(self):
        super(IconTexture, self).set_reactive(False)

        if not self.has_animation:
            super(IconTexture, self).hide()
        elif self.get_opacity():
            self.timeline.fade_out()

    def _set_animation_timeline(self):
        self.timeline = FadeAnimationTimeline(self, 200)

class ActorIcon(object):

    def __init__(self):
        self._get_ui_data()
        self.icon_offset = 0

    def set_icon(self, photoimage, x_offset, y_offset):
        self.photo = photoimage.photo
        self.photoimage = photoimage

        if self.photo:
            self.icon_image = self._get_icon()
            self.x, self.y = self._calc_position(
                photoimage, self.icon_image, self.position, 
                x_offset - self.icon_offset, y_offset)

    def _calc_position(self, photoimage, icon, position, image_x, image_y):
        icon_pixbuf = icon.get_pixbuf()

        side = photoimage.w if photoimage.w > photoimage.h else photoimage.h
        offset = int(side / 60)
        offset = 10 if offset < 10 else offset

        if position == 0 or position == 3:
            x = image_x + offset
        else:
            x = image_x + photoimage.w - icon_pixbuf.get_width() - offset

        if position == 0 or position == 1:
            y = image_y + offset
        else:
            y = image_y + photoimage.h - icon_pixbuf.get_height() - offset

        # print x, y, offset
        return x, y

    def _set_ui_options(self, settings, position=None):
        self.is_shown_always = settings.get_boolean('always-show')
        self.position = position if position else settings.get_int('position')

        settings.connect("changed::always-show", 
                         self._change_ui_always_show_cb)
        settings.connect("changed::position", self._change_ui_position_cb)

    def _change_ui_always_show_cb(self, settings, key):
        self.is_shown_always = settings.get_boolean(key)
        self.show() if self.is_shown_always else self.hide()

    def _change_ui_position_cb(self, settings, key):
        self.position = settings.get_int(key)

    def _enter_cb(self, w, e, tooltip):
        pass

    def _leave_cb(self, w, e, tooltip):
        tooltip.update_photo(self.photo)
