from gi.repository import Gtk, Gdk
# from gettext import gettext as _

from ..constants import UI_FILE
from ..settings import SETTINGS, SETTINGS_RECENTS
from ..plugins import PHOTO_TARGET_TOKEN, PLUGIN_INFO_TOKEN
from treeview import PreferencesTreeView


class PhotoSourceTreeView(PreferencesTreeView):
    """Photo Source TreeView"""

    def __init__(self, gui, widget, liststore, parent, plugin_liststore):
        super(PhotoSourceTreeView, self).__init__(gui, widget, liststore, parent)
        self.plugin_liststore = plugin_liststore

        # liststore order
        column_names = ['source', 'target', 'argument', 'weight']
        columns = [ gui.get_object('treeviewcolumn_%s' % x)
                    for x in column_names]

        for col in columns:
            if col.get_sort_indicator(): # check if the filed was clicked
                break
        else:
            columns[0].clicked() # sort by 'source' column

    def on_treeview1_query_tooltip(self, treeview, x, y, keyboard_mode, tooltip):
        nx, ny = treeview.convert_widget_to_bin_window_coords(x, y)
        path_tuple = treeview.get_path_at_pos(nx, ny)

        if path_tuple is not None:
            row_id, col = path_tuple[:2]
            col_id = col.get_sort_column_id()
            row = self.liststore[row_id]

            plugin_tip = row[6].get_tooltip() # liststore object
            tip = plugin_tip if plugin_tip and col_id == 2 else row[col_id]

            if tip and isinstance(tip, str) and col_id > 0:
                treeview.set_tooltip_row(tooltip, row_id)
                tooltip.set_text(tip)
                return True

        return False

    def _set_button_sensitive(self, state):
        self.gui.get_object('button4').set_sensitive(state)
        self.gui.get_object('button5').set_sensitive(state)

    def _set_coursor_to(self, iter):
        model = self.treeview.get_model()
        row = model.get_path(iter)
        self.treeview.set_cursor(row, None, False)

    def on_treeview1_button_press_event(self, widget, event):
        if event.type == Gdk.EventType._2BUTTON_PRESS:
            self.on_button4_clicked(widget)
            return True

    def on_button3_clicked(self, widget): # _new_button_cb
        photodialog = PhotoSourceDialog(self.parent)
        (response_id, v) = photodialog.run(self.plugin_liststore)

        if response_id == Gtk.ResponseType.OK:
            new_iter = self.liststore.append(v)
            self._set_coursor_to(new_iter)

    def on_button4_clicked(self, widget): #_prefs_button_cb
        treeselection = self.treeview.get_selection()
        (model, iter) = treeselection.get_selected()

        photodialog = PhotoSourceDialog(self.parent, model[iter])
        (response_id, v) = photodialog.run(self.plugin_liststore)

        if response_id == Gtk.ResponseType.OK:
            new_iter = self.liststore.append(v, iter)

            self.liststore.remove(iter)
            self._set_coursor_to(new_iter)

    def on_button5_clicked(self, widget): # _delete_button_cb
        treeselection = self.treeview.get_selection()
        (model, iter) = treeselection.get_selected()

        self.liststore.remove(iter)
        self._set_button_sensitive(False)

class PhotoSourceDialog(object):
    """Photo Source Dialog"""

    def __init__(self, parent, data=None):
        self.gui = Gtk.Builder()
        self.gui.add_from_file(UI_FILE)

        self.parent = parent
        self.data = data

    def run(self, plugin_liststore):
        dialog = self.gui.get_object('photo_source')
        dialog.set_transient_for(self.parent)
        source_list = plugin_liststore.available_list()

        source_widget = SourceComboBox(self.gui, source_list, self.data)
        argument_widget = ArgumentEntry(self.gui, self.data)
        weight_widget = WeightEntry(self.gui, self.data)

        # run
        response_id = dialog.run()

        v = { 'source'  : source_widget.get_active_text(),
              'target'  : source_widget.get_target(),
              'argument': argument_widget.get_text(),
              'weight'  : weight_widget.get_value(),
              'options' : source_widget.ui.get_options() }

        dialog.destroy()
        if response_id == Gtk.ResponseType.OK:
            SETTINGS_RECENTS.set_string('source', v['source'])
        return response_id, v

class SourceComboBox(object):

    def __init__(self, gui, source_list, photoliststore):
        self.data = photoliststore

        self.widget = widget = gui.get_object('combobox4')
        self.button = gui.get_object('button8')
        liststore = widget.get_model()

        for name in source_list:
            pixbuf = PLUGIN_INFO_TOKEN[name]().get_icon_pixbuf()
            list = [pixbuf, name]
            liststore.insert_before(None, list)

        renderer = Gtk.CellRendererPixbuf()
        widget.pack_start(renderer, False)
        widget.add_attribute(renderer, 'pixbuf', 0)

        renderer = Gtk.CellRendererText()
        widget.pack_start(renderer, False)
        widget.add_attribute(renderer, 'text', 1)

        recent = SETTINGS_RECENTS.get_string('source').decode('utf-8') #FIXME
        # liststore source
        source_num = source_list.index(
            photoliststore[1].decode('utf-8')) if photoliststore \
            else source_list.index(recent) if recent in source_list \
            else 0
        widget.set_active(source_num)

        widget.connect('changed', self._change_combobox, gui)

        # target
        self._change_combobox(None, gui, photoliststore)

    def get_active_text(self):
        model = self.widget.get_model()
        iter = self.widget.get_active_iter()
        text = model[iter][1]
        return text

    def get_target(self):
        return self.ui.get().decode('utf-8') #FIXME

    def _change_combobox(self, widget, gui, data=None):
        self.button.set_sensitive(True)

        text = self.get_active_text().decode('utf-8')
        token = PHOTO_TARGET_TOKEN

        self.ui = token[text](gui, data)
        self.ui.make()

class ArgumentEntry(object):

    def __init__(self, gui, photoliststore):

        self.widget = gui.get_object('entry1')
        if photoliststore:
            self.widget.set_text(photoliststore[3]) # liststore argument

    def get_text(self):
        argument = self.widget.get_text() \
            if self.widget.get_property('sensitive') else ''
        return argument

class WeightEntry(object):

    def __init__(self, gui, photoliststore):

        default_weight = SETTINGS.get_int('default-weight')
        # liststore weight
        weight = photoliststore[4] if photoliststore else default_weight 
        self.widget = gui.get_object('spinbutton3')
        self.widget.set_value(weight)
        self.widget.set_tooltip_markup(
            _("The photo source should be ignored if the weight is 0."))

    def get_value(self):
        return int(self.widget.get_value())
