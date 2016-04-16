from __future__ import division

try:
    from gi.repository import Clutter, GtkClutter
except ImportError:
    from ..utils.nullobject import Null
    GtkClutter = Null()

from gi.repository import Gtk

from actor import *
from gtkimage import *
from ..settings import SETTINGS, SETTINGS_UI

class PhotoImageClutter(PhotoImage):

    def __init__(self, photoframe):
        super(PhotoImageClutter, self).__init__(photoframe)

        # GtkClutter.init(None)
        
        self.image = self.embed = GtkClutter.Embed.new()
        self.stage = self.embed.get_stage()
        color = self._get_border_color()
        is_ok, clutter_color = Clutter.Color().from_string(color)

        self.stage.set_color(clutter_color)
        self.embed.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse(color))
        self.embed.show()

        self.photo_image = base.Texture(self.stage)
        self.photo_image.show()
        self.map = map.MapFactory().create(self.stage, self)

        self.actors = self._get_actors()
        self.actors[1].set_map(self.map) # geo icon
        self.trash_actors = self.actors[3:5]

    def _get_actors(self):
        actor_class = [ source.ActorSourceIcon,
                        info.ActorGeoIcon,
                        info.ActorInfoIcon,
                        trash.ActorTrashIcon,
                        trash.ActorRemoveCatalogIcon,
                        favicon.ActorFavIcon,
                        share.ActorShareIcon, ]

        return  [cls(self.stage, self.tooltip) for cls in actor_class]

    def _get_border_color(self):
        return SETTINGS.get_string('border-color') or '#edeceb'

    def _set_photo_image(self, pixbuf):
        self.window_border = 0
        self.w = pixbuf.get_width()
        self.h = pixbuf.get_height()

        x, y = self._get_image_position()
        self._change_texture(pixbuf, x, y)

    def _change_texture(self, pixbuf, x, y):
        self.photo_image.change(pixbuf, x, y)

        for actor in self.actors:
            actor.set_icon(self, x, y)

    def _get_image_position(self):
        border = SETTINGS.get_int('border-width')
        return border, border

    def clear(self):
        pass

    def on_enter_cb(self, w, e):
        for actor in self.actors:
            actor.show(True)

    def on_leave_cb(self, w, e):
        for actor in self.actors + [self.map]:
            actor.hide()

    def check_actor(self, stage, event):
        x, y = int(event.x), int(event.y)
        actor = self.stage.get_actor_at_pos(Clutter.PickMode.REACTIVE, x, y)
        result = (actor != self.photo_image)
        return result

    def has_trash_dialog(self):
        return True in [trash.dialog.is_show for trash in self.trash_actors]

class PhotoImageClutterFullScreen(PhotoImageClutter, PhotoImageFullScreen):

    def __init__(self, photoframe):
        super(PhotoImageClutterFullScreen, self).__init__(photoframe)

        self.photo_image2 = base.Texture(self.stage)
        self.photo_image2.show()
        self.actors2 = self._get_actors()
        self.trash_actors += self.actors2[3:5]
        self.is_first = True # image1 or image2

        self.has_animation = SETTINGS_UI.get_boolean('animate-fullscreen')
        if self.has_animation:
            self.photo_image.set_opacity(0)

    def _change_texture(self, pixbuf, x, y):
        if not self.has_animation:
            super(PhotoImageClutterFullScreen, self)._change_texture(pixbuf, x, y)
            return

        image1, image2 = self.photo_image, self.photo_image2
        actors1, actors2 = self.actors, self.actors2

        if not self.is_first:
            image1, image2 = image2, image1
            actors1, actors2 = actors2, actors1

        image1.change(pixbuf, x, y)
        image1.timeline.fade_in()
        image2.timeline.fade_out()

        for a1, a2 in zip(actors1, actors2):
            a1.set_icon(self, x, y)
            a2.hide(True)

        self.is_first = not self.is_first

    def _get_image_position(self):
        root_w, root_h = self._get_max_display_size()
        x = (root_w - self.w) / 2
        y = (root_h - self.h) / 2
        return x, y

    def _get_border_color(self):
        return 'black'

    def check_mouse_on_window(self):
        is_mouse_on = super(PhotoImageClutterFullScreen, self).check_mouse_on_window()
        return is_mouse_on if self.photoframe.ui.is_show() else False

    def on_enter_cb(self, w, e):
        for actor in self._get_active_actors():
            actor.show(True)

    def on_leave_cb(self, w, e):
        for actor in self._get_active_actors():
            actor.hide()

    def _get_active_actors(self):
        return self.actors2 if self.is_first and self.has_animation \
            else self.actors

class PhotoImageClutterScreenSaver(PhotoImageClutterFullScreen,
                                   PhotoImageScreenSaver):

    def __init__(self, photoframe):
        super(PhotoImageClutterScreenSaver, self).__init__(photoframe)
        if not SETTINGS_UI.get_boolean('icons-on-screensaver'):
            self.actors = []

    def check_mouse_on_window(self):
        return False
