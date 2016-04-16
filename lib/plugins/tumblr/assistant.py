#
# gfeedline - A Social Networking Client
#
# Copyright (c) 2012, Yoshizumi Endo.
# Licence: GPL3

import re
import json

from gi.repository import Gtk, Gdk

from getauthtoken import TumblrAuthorization
from ...constants import SHARED_DATA_FILE
from ...utils.urlgetautoproxy import urlget_with_autoproxy

from ...utils.authwebkit import AuthWebKitScrolledWindow
from account import AuthorizedTumblrAccount


class TumblrAuthAssistant(Gtk.Assistant):

    def __init__(self, parent=None, cb=None):
        super(TumblrAuthAssistant, self).__init__()

        gui = Gtk.Builder()
        gui.add_from_file(SHARED_DATA_FILE('assistant_facebook.glade'))
        self.label_user_fullname = gui.get_object('label_name')

        self.set_title(_('Tumblr Account Setup'))
        self.set_default_size(600, 600)
        self.set_type_hint(Gdk.WindowTypeHint.DIALOG)
        self.set_modal(True)

        self.connect('cancel', self.on_cancel)
        self.connect('close', self.on_close, cb)

        # page 1
        page1 = gui.get_object('label1')
        page1.set_text(page1.get_text().decode('utf-8') % _('Tumblr'))
        self.append_page(page1)

        self.set_page_title(page1, _('Intro'))
        self.set_page_type(page1, Gtk.AssistantPageType.INTRO)
        self.set_page_complete(page1, True)

        # page 2
        page2 = TumblrWebKitScrolledWindow()
        self.token = page2.token
        # self.page2.connect("login-started", self._set_webkit_ui_cb)

        page2.connect("token-acquired", self._get_access_token_cb)
        page2.connect("error-occurred", self.on_cancel)
        self.append_page(page2)

        self.set_page_title(page2, _('Authorization'))
        self.set_page_type(page2, Gtk.AssistantPageType.PROGRESS)
        self.set_page_complete(page2, False)

        # page 3
        page3 = gui.get_object('box2')
        confirm_label = gui.get_object('label6')
        confirm_label.set_text(confirm_label.get_text().decode('utf-8') 
                               % _('Tumblr'))
        self.append_page(page3)

        self.set_page_title(page3, _('Confirm'))
        self.set_page_type(page3, Gtk.AssistantPageType.SUMMARY)
        self.set_page_complete(page3, True)

        self.show_all()

    def _get_access_token_cb(self, w, url):
        # print "!!! ", url
        re_verifier = re.compile('.*oauth_verifier=([^#&]*)[#&]?.*')
        verifier = re_verifier.sub("\\1", url)

        try:
            token, params = TumblrAuthorization().get_access_token(
                verifier, self.token)
        except IOError, e:
            print "Warning: ", e
            return

        self.result = {'access-token': token.key,
                       'access-secret': token.secret}

        self.next_page()

        account = AuthorizedTumblrAccount('dummy', token.key, token.secret)
        account.api.user_info(cb=self._get_userinfo_cb)

    def _get_userinfo_cb(self, data):
        d = json.loads(data)

        self.user_fullname = d['response']['user']['name']
        self.result['screen-name'] = self.user_fullname

        self.idnum = None
        self.label_user_fullname.set_text(self.user_fullname)

    def on_close(self, assistant, cb):
        account = [
            'Tumblr',
            self.result['screen-name'],
            self.result['access-token'],
            self.result['access-secret'],
            ''
            ]

        cb(account)
        self.destroy()

    def on_cancel(self, *args):
        self.destroy()

class TumblrWebKitScrolledWindow(AuthWebKitScrolledWindow):

    LOGIN_URL = 'https://www.tumblr.com/login'
    ERROR_URL = 'http://www.tumblr.com/error'
    RE_TOKEN = '.*oauth_token=(.*)&.*'
           

    def _get_auth_url(self):
        url, self.token = TumblrAuthorization().open_authorize_uri()
        return url
