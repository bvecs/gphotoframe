import gtk
from gettext import gettext as _

from ..constants import UI_FILE
from ..plugins import PHOTO_TARGET_TOKEN
from ..utils.config import GConf
from treeview import PreferencesTreeView


class PhotoSourceTreeView(PreferencesTreeView):
    """Photo Source TreeView"""

    def __init__(self, gui, widget, liststore, parent, plugin_liststore):
        super(PhotoSourceTreeView, self).__init__(gui, widget, liststore, parent)
        self.plugin_liststore = plugin_liststore

        self._add_text_column(_("Source"), 0)
        self._add_text_column(_("Target"), 1, 150)
        self._add_text_column(_("Argument"), 2, 100)
        self._add_text_column(_("Weight"), 3)

    def get_signal_dic(self):
        dic = {
            "on_button3_clicked" : self._new_button_cb,
            "on_button4_clicked" : self._prefs_button_cb,
            "on_button5_clicked" : self._delete_button_cb,
            "on_treeview1_cursor_changed" : self._cursor_changed_cb,
            "on_treeview1_query_tooltip"  : self._query_tooltip_cb,
            }
        return dic

    def _query_tooltip_cb(self, treeview, x, y, keyboard_mode, tooltip):
        nx, ny = treeview.convert_widget_to_bin_window_coords(x, y)
        path_tuple = treeview.get_path_at_pos(nx, ny)

        if path_tuple is not None:
            row_id, col = path_tuple[:2]
            col_id = col.get_sort_column_id()
            row = self.liststore[row_id]

            plugin_tip = row[5].get_tooltip()
            tip = plugin_tip if plugin_tip and col_id == 2 else row[col_id]

            if tip and isinstance(tip, str) and col_id > 0:
                treeview.set_tooltip_row(tooltip, row_id)
                tooltip.set_text(tip)
                return True

        return False

    def _set_button_sensitive(self, state):
        self.gui.get_object('button4').set_sensitive(state)
        self.gui.get_object('button5').set_sensitive(state)

    def _new_button_cb(self, widget):
        photodialog = PhotoSourceDialog(self.parent)
        (response_id, v) = photodialog.run(self.plugin_liststore)

        if response_id == gtk.RESPONSE_OK:
            self.liststore.append(v)

    def _prefs_button_cb(self, widget):
        treeselection = self.treeview.get_selection()
        (model, iter) = treeselection.get_selected()

        photodialog = PhotoSourceDialog(self.parent, model[iter])
        (response_id, v) = photodialog.run(self.plugin_liststore)

        if response_id == gtk.RESPONSE_OK:
            self.liststore.append(v, iter)
            self.liststore.remove(iter)

    def _delete_button_cb(self, widget):
        treeselection = self.treeview.get_selection()
        (model, iter) = treeselection.get_selected()
        self.liststore.remove(iter)
        self._set_button_sensitive(False)


class PhotoSourceDialog(object):
    """Photo Source Dialog"""

    def __init__(self, parent, data=None):
        self.gui = gtk.Builder()
        self.gui.add_from_file(UI_FILE)

        self.conf = GConf()
        self.parent = parent
        self.data = data

    def run(self, plugin_liststore):
        dialog = self.gui.get_object('photo_source')
        dialog.set_transient_for(self.parent)
        source_list = plugin_liststore.available_list()

        # source
        source_widget = self.gui.get_object('combobox4')
        for str in source_list:
            source_widget.append_text(str)

        recent = self.conf.get_string('recents/source')
        source_num = source_list.index(self.data[0]) if self.data \
            else source_list.index(recent) if recent in source_list \
            else 0
        source_widget.set_active(source_num)

        # target
        self._change_combobox(source_widget, self.data)

        # argument
        argument_widget = self.gui.get_object('entry1')
        if self.data:
            argument_widget.set_text(self.data[2])

        # weight
        weight = self.data[3] if self.data \
            else self.conf.get_int('default_weight', 3)
        weight_widget = self.gui.get_object('spinbutton3')
        weight_widget.set_value(weight)
        weight_widget.set_tooltip_markup(
            _("The photo source should be ignored if the weight is 0."))

        # run
        target_widget = self.gui.get_object('combobox4')
        target_widget.connect('changed', self._change_combobox)

        response_id = dialog.run()

        argument = argument_widget.get_text() \
            if argument_widget.get_property('sensitive') else ''

        v = { 'source'  : source_widget.get_active_text(),
              'target'  : self.ui.get(),
              'argument': argument,
              'weight'  : weight_widget.get_value(),
              'options' : self.ui.get_options() }

        dialog.destroy()
        if response_id == gtk.RESPONSE_OK:
            self.conf.set_string('recents/source', v['source'])
        return response_id, v

    def _change_combobox(self, combobox, data=None):
        self.gui.get_object('button8').set_sensitive(True)

        text = combobox.get_active_text()
        token = PHOTO_TARGET_TOKEN

        self.ui = token[text](self.gui, data)
        self.ui.make()