# -*- coding: utf-8 -*-
#
# Facebook Authentication UI module for GPhotoFrame
# Copyright (c) 2011, Yoshizumi Endo <y-endo@ceres.dti.ne.jp>
# Licence: GPL3

import json
import urllib
import re
# from gettext import gettext as _

from gi.repository import GObject, Gtk, Gdk, WebKit

from ..flickr.authdialog import PluginFlickrDialog
from ...utils.urlgetautoproxy import urlget_with_autoproxy
from ...settings import SETTINGS_FACEBOOK

class PluginFacebookDialog(PluginFlickrDialog):

    is_accessed = False

    def __del__(self):
        """A black magic for avoiding unintended GC for sub instances."""
        pass

    def run(self):
        self._read_conf()
        if self.token:
            self._logged_dialog()
        elif PluginFacebookDialog.is_accessed:
            self._is_accessed_dialog()
        else:
            self._facebook_auth_dialog()

        self.dialog.show()

    def _facebook_auth_dialog(self):
        self._set_webkit_ui()
        text = _('Loading...')
        self._set_dialog(text, None, None, self._cancel_cb, self._quit_cb)
        self.button_n.set_sensitive(False)

        self.spinner = self.gui.get_object('spinner_loading')
        self.vbox.remove(self.label)
        self.vbox.add(self.spinner)

    def _logged_dialog(self):
        text = _('You are logged into Facebook as %s.') % self.full_name
        self._set_dialog(text, _('_Logout'), None, self._logout_cb, self._quit_cb)

    def _is_accessed_dialog(self):
        text = _('You are not logged into Facebook.  '
                 'If you would like to redo the authentication, '
                 'you have to restart GPhotoFrame.')
        self._set_dialog(text, None, None, self._cancel_cb, self._quit_cb)
        self.button_p.set_sensitive(False)
        self.button_n.set_sensitive(True)

    def _quit_cb(self, *args):
        self._write_conf()
        self.dialog.destroy()

    def _logout_cb(self, *args):
        self.full_name = self.token = ""
        self._quit_cb()

    def _set_webkit_ui(self, *args):
        self.dialog.set_gravity(Gdk.Gravity.CENTER)
        self.dialog.set_resizable(True)
        self.dialog.resize(640, 480)

        self.sw = FacebookWebKitScrolledWindow()
        self.sw.connect("login-started", self._set_webkit_ui_cb)
        self.sw.connect("token-acquired", self._get_access_token_cb)
        self.sw.connect("error-occurred", self._cancel_cb)

    def _set_webkit_ui_cb(self, w, e):
        self.vbox.remove(self.spinner)
        self.vbox.add(self.sw)

    def _get_access_token_cb(self, w, token):
        self.token = token

        url = 'https://graph.facebook.com/me?access_token=%s' % token
        urlget_with_autoproxy(url, cb=self._get_userinfo_cb)

    def _get_userinfo_cb(self, data):
        d = json.loads(data)
        self.full_name = d['name']
        self.id = d['id']
        PluginFacebookDialog.is_accessed = True

        text = _('You are logged into Facebook as %s.  ' 
                 'If you would like to redo the authentication, '
                 'you have to restart GPhotoFrame.')
        self.label.set_text(text % self.full_name)

        self.vbox.remove(self.sw)
        self.vbox.add(self.label)
        self.dialog.resize(300, 100)

        self.button_p.set_sensitive(False)
        self.button_n.set_sensitive(True)

    def _read_conf(self):
        self.full_name = SETTINGS_FACEBOOK.get_string('full-name')
        self.token = SETTINGS_FACEBOOK.get_string('access-token')

    def _write_conf(self):
        SETTINGS_FACEBOOK.set_string('full-name', self.full_name)
        SETTINGS_FACEBOOK.set_string('access-token', self.token)

        self._update_auth_status(self.full_name) # in plugin treeview

class FacebookWebKitScrolledWindow(Gtk.ScrolledWindow):

    def __init__(self):
        super(FacebookWebKitScrolledWindow, self).__init__()
        self.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        values = { 'client_id': 157351184320900,
                   'redirect_uri': 
                   'https://www.facebook.com/connect/login_success.html',
                   'response_type': 'token',
                   'scope': 'user_photos,friends_photos,read_stream,offline_access',
                   'display': 'popup'}
        uri = 'https://www.facebook.com/dialog/oauth?' + urllib.urlencode(values)

        w = WebKit.WebView.new()
        w.set_vexpand(True)
        w.load_uri(uri)
        w.connect("document-load-finished", self._get_document_cb)

        self.add(w)
        self.show_all()

    def _get_document_cb(self, w, e):
        url = w.get_property('uri')
        re_token = re.compile('.*access_token=(.*)&.*')
        login_url = 'https://www.facebook.com/login.php?'
        error_url = 'https://www.facebook.com/connect/login_success.html?error'

        if url.startswith(login_url):
            self.emit("login-started", None)
        elif re_token.search(url):
            token = re_token.sub("\\1", url)
            self.emit("token-acquired", token)
        elif url.startswith(error_url):
            self.emit("error-occurred", None)

for signal in ["login-started", "token-acquired", "error-occurred"]:
    GObject.signal_new(signal, FacebookWebKitScrolledWindow,
                       GObject.SignalFlags.RUN_LAST, None,
                       (GObject.TYPE_PYOBJECT,))
