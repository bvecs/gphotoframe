from __future__ import division

from gi.repository import Gtk, Gdk, GObject, GLib

import constants
from image import *
from settings import SETTINGS, SETTINGS_GEOMETRY
from menu import PopUpMenu, PopUpMenuFullScreen
from utils.gnomescreensaver import GsThemeWindow, is_screensaver_mode

SETTINGS.set_boolean('fullscreen', False)

from utils.iconimage import IconImage
# FIXME
# Gtk.window_set_default_icon(IconImage('gphotoframe').get_pixbuf())

class PhotoFrameFactory(object):

    def create(self, photolist):

        if is_screensaver_mode():
            photoframe = PhotoFrameScreenSaver()
        else:
            photoframe = PhotoFrame(photolist)

        return photoframe

class PhotoFrame(object):
    """Photo Frame Window"""

    def __init__(self, photolist):

        self.photolist = photolist
        self.fixed_window_hint = Gdk.WindowTypeHint.DOCK

        gui = Gtk.Builder()
        gui.add_objects_from_file(constants.UI_FILE, ["window"])

        SETTINGS.connect("changed::fullscreen", self._change_fullscreen_cb)
        SETTINGS.connect("changed::window-sticky", self._change_sticky_cb)
        SETTINGS.connect("changed::window-fix", self._change_window_fix_cb)
        SETTINGS.connect("changed::border-color", self._set_border_color)

        # a workaround for Xfwm bug (Issue #97)
        gravity = Gdk.Gravity.NORTH_WEST \
            if SETTINGS_GEOMETRY.get_string('gravity') == 'NORTH_WEST' \
            else Gdk.Gravity.CENTER

        self.window = gui.get_object('window')
        self.window.set_gravity(gravity)

        if SETTINGS.get_boolean('window-sticky'):
            self.window.stick()
        self._set_window_state()
        self._set_window_position()

        self._set_photoimage()
        self._set_event_box()
        self._set_popupmenu(self.photolist, self)
        self._set_accelerator()

        # FIXME: Why "query-tooltip" is not enable?
        self.window.connect("query-tooltip", self.photoimage.tooltip.query_tooltip_cb)
        gui.connect_signals(self)

    def set_photo(self, photo, change=True):
        state = bool(photo)

        if change:
            if not self.photoimage.set_photo(photo): return False
            borders = self.photoimage.window_border * 2
            # self.window.resize(1, 1) # black magic?
            self.window.resize(self.photoimage.w + borders,
                               self.photoimage.h + borders)

        self.popup_menu.set_open_menu_sensitive(state)
        self.popup_menu.set_recent_menu()

        if self.is_fullscreen():
            self.fullframe.set_photo(photo, change)

        return True

    def remove_photo(self, url):
        change = bool(self.photoimage.photo and \
            self.photoimage.photo['url'] == url)
        self.set_photo(None, change)

    def check_mouse_on_frame(self):
        frame = self._get_frame_obj()
        return frame.photoimage.check_mouse_on_window() or self.popup_menu.is_show

    def has_trash_dialog(self):
        frame = self._get_frame_obj()
        return frame.photoimage.has_trash_dialog() 

    def _get_frame_obj(self):
        return self.fullframe if self.is_fullscreen() else self

    def is_fullscreen(self):
        return hasattr(self, "fullframe") and self.fullframe.window.get_window()

    def is_screensaver(self):
        return hasattr(self, 'screensaver')

    def _set_window_position(self):
        self.window.move(SETTINGS_GEOMETRY.get_int('root-x'),
                         SETTINGS_GEOMETRY.get_int('root-y'))
        self.window.resize(1, 1)
        self.window.show_all()
        self.window.get_position()

    def _set_event_box(self):
        self.ebox = Gtk.EventBox.new()
        self.ebox.add(self.photoimage.image)
        self.ebox.show()
        self.window.add(self.ebox)

        self._set_border_color()

    def _set_border_color(self, *args):
        color = SETTINGS.get_string('border-color')
        if color:
            self.ebox.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse(color))

    def _set_photoimage(self):
        self.photoimage = PhotoImageFactory().create(self)

    def _set_popupmenu(self, photolist, frame):
        self.popup_menu = PopUpMenu(self.photolist, self)

    def _set_window_state(self):
        is_bool = SETTINGS.get_boolean
        if is_bool('window-fix'):
            self.window.set_type_hint(self.fixed_window_hint)
        if is_bool('window-keep-below') or is_bool('window-fix'):
            self.window.set_keep_below(True)

    def _set_accelerator(self):
        accel_group = Gtk.AccelGroup()
        ac_set = [[ "<gph>/quit", "<control>q", self.popup_menu.on_quit ],
                  [ "<gph>/open", "<control>o", self.popup_menu.on_menuitem5_activate ],
                  [ "<gph>/fullscreen", "F11", self._toggle_fullscreen ]]
        for ac in ac_set:
            key, mod = Gtk.accelerator_parse(ac[1])
            Gtk.AccelMap.add_entry(ac[0], key, mod)
            accel_group.connect_by_path(ac[0], ac[2])

        self.window.add_accel_group(accel_group)

    def _toggle_fullscreen(self, *args):
        state = not SETTINGS.get_boolean('fullscreen')
        SETTINGS.set_boolean('fullscreen', state)

    def on_window_button_press_event(self, widget, event):
        if event.button == 1:
            if not self.photoimage.check_actor(widget, event):
                if event.type == Gdk.EventType._2BUTTON_PRESS:
                    self.popup_menu.on_menuitem5_activate()
                else:
                    x, y = int(event.x_root), int(event.y_root)
                    widget.begin_move_drag(event.button, x, y, event.time)
        elif event.button == 2:
            pass
        elif event.button == 3:
            self.popup_menu.start(widget, event)
        elif event.button == 9:
            self.photolist.next_photo()

    def on_window_enter_notify_event(self, *args):
        self.photoimage.on_enter_cb(*args)

    def on_window_window_state_event(self, widget, event):
        if event.changed_mask & Gdk.WindowState.ICONIFIED:
            state = event.new_window_state & Gdk.WindowState.ICONIFIED
            widget.set_skip_taskbar_hint(not state) # FIXME

    def on_window_query_tooltip(self, *args):
        self.photoimage.tooltip.query_tooltip_cb(*args)

    def on_window_leave_notify_event(self, widget, event):
#        if event.mode != 2:
#            return True
        self.photoimage.on_leave_cb(widget, event)

        # save geometry
        if not SETTINGS.get_boolean('window-fix'):
            x, y = widget.get_position()
            w, h = widget.get_size()

            if self.window.get_gravity() == Gdk.Gravity.CENTER:
                x += w / 2
                y += h / 2

            SETTINGS_GEOMETRY.set_int('root-x', x)
            SETTINGS_GEOMETRY.set_int('root-y', y)

        return False

    def on_window_key_press_event(self, *args):
        pass

    def on_window_motion_notify_event(self, *args):
        pass

    def on_window_realize(self, *args):
        pass

    def on_window_destroy(self, *args):
        pass

    def _change_window_fix_cb(self, settings, key):
        hint = self.fixed_window_hint \
            if settings.get_boolean(key) else Gdk.WindowTypeHint.NORMAL

        if hint == self.window.get_type_hint(): return

        self.window.hide()
        self.window.set_type_hint(hint)
        self.window.show()

        is_below = SETTINGS.get_boolean('window-fix') or \
            SETTINGS.get_boolean('window-keep-below')
        self.window.set_keep_below(is_below)

        if hint == Gdk.WindowTypeHint.NORMAL:
            if self.window.get_gravity() == Gdk.Gravity.CENTER:
                border = self.photoimage.window_border
                x = SETTINGS_GEOMETRY.get_int('root-x') - self.photoimage.w / 2
                y = SETTINGS_GEOMETRY.get_int('root-y') - self.photoimage.h / 2
                self.window.move(int(x - border), int(y - border))
            else:
                # a workaround for Xfwm bug (Issue #97)
                x = SETTINGS_GEOMETRY.get_int('root-x')
                y = SETTINGS_GEOMETRY.get_int('root-y')
                self.window.move(int(x), int(y))

    def _change_fullscreen_cb(self, settings, key):
        if settings.get_boolean(key):
            self.fullframe = PhotoFrameFullScreen(self.photolist)
            self.fullframe.set_photo(self.photoimage.photo)

    def _change_sticky_cb(self, settings, key):
        if settings.get_boolean(key):
            self.window.stick()
        else:
            self.window.unstick()

class PhotoFrameFullScreen(PhotoFrame):

    def __init__(self, photolist):
        super(PhotoFrameFullScreen, self).__init__(photolist)
        self.ui = FullScreenUI(self.photoimage, self.window)

    def _set_window_state(self):
        self.window.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse("black"))
        self.window.fullscreen()

    def _set_border_color(self):
        self.ebox.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse("black"))

    def _set_photoimage(self):
        self.photoimage = PhotoImageFullScreenFactory().create(self)

    def _set_popupmenu(self, photolist, frame):
        self.popup_menu = PopUpMenuFullScreen(self.photolist, self)

    def _check_button_cb(self, widget, event):
        self.ui.show_cb(widget, event)
        super(PhotoFrameFullScreen, self)._check_button_cb(widget, event)

    def _save_geometry_cb(self, widget, event):
        self.photoimage.on_leave_cb(widget, event)

    def _change_window_fix_cb(self, settings, key):
        pass

    def _change_fullscreen_cb(self, settings, key):
        if not settings.get_boolean(key):
            self.window.destroy()

    def on_window_key_press_event(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            SETTINGS.set_boolean('fullscreen', False)

    def on_window_motion_notify_event(self, *args): 
        self.ui.show_cb(*args)

    def on_window_realize(self, *args):
        self.ui.hide_cb(*args)

    def on_window_destroy(self, *args): 
        self.ui.stop_timer_cb(*args)

class PhotoFrameScreenSaver(PhotoFrame):

    def __init__(self):
        self.window = GsThemeWindow()
        self.screensaver = True
        self.window.show()

        self.photoimage = PhotoImageScreenSaverFactory().create(self)
        self.window.add(self.photoimage.image)

    def set_photo(self, photo, change=True):
        return self.photoimage.set_photo(photo)

    def check_mouse_on_frame(self):
        return False

class FullScreenUI(object):

    def __init__(self, photoimage, window):
        self.photoimage = photoimage
        self.cursor = Cursor()

        self.start_timer_cb(window, None)

    def is_show(self):
        return self.cursor.is_show

    def show_cb(self, widget, event):
        self.photoimage.on_enter_cb(widget, event)
        self.cursor.show(widget)

        self.stop_timer_cb()
        self.start_timer_cb(widget, event)

    def hide_cb(self, widget, event):
        self.cursor.hide(widget) # the cursor should be hide at first. 
        self.photoimage.on_leave_cb(widget, event)

    def start_timer_cb(self, widget, event):
        self._timer = GLib.timeout_add_seconds(5, self.hide_cb, widget, event)

    def stop_timer_cb(self, *args):
        if hasattr(self, "_timer"):
            GObject.source_remove(self._timer)

class Cursor(object):
    def __init__(self):
        self.is_show = True

    def show(self, widget):
        if not self.is_show:
            self.is_show = True
            widget.get_window().set_cursor(None)

    def hide(self, widget):
        if self.is_show:
            widget.set_tooltip_markup(None)

            self.is_show = False
            cursor = Gdk.Cursor.new(Gdk.CursorType.BLANK_CURSOR)
            widget.get_window().set_cursor(cursor)
            return False
