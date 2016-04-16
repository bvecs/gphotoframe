import urllib
import random
# from gettext import gettext as _

from ...settings import SETTINGS_FLICKR
from auth import add_api_sig

API_KEY = '343677ff5aa31f37042513d533293062'
SECRET = '74fcfc5cd13dab2d'

class FlickrFactoryAPI(object):

    def __init__(self):
        self.api = {
            _('Contacts Photos') : FlickrFactoryContactsAPI,
            _('Favorites')       : FlickrFactoryFavoritesAPI,
            _('Group Pool')      : FlickrGroupAPI,
            _('Interestingness') : FlickrInterestingnessAPI,
            _('People Photos')   : FlickrFactoryPeopleAPI,
            _('Photo Search')    : FlickrSearchAPI,
            _('The Commons')     : FlickrCommonsAPI,
            _('Your Groups')     : FlickrYourGroupsAPI,
            }

    def create(self, api, argument=None):
        obj = self.api[api]().create(argument)
        return obj

class FlickrAPI(object):

    def __init__(self):
        self.nsid_conversion = True
        self._set_method()

    def _set_method(self):
        pass

    def create(self, argument=None):
        return self

    def is_use_own_id(self): # for Contacts Photo & Favorites
        return False

    def get_url(self, argument, page=1, per_page=100):
        url = 'http://api.flickr.com/services/rest/?'

        values = { 'api_key' : API_KEY,
                   'method'  : self.method,
                   'format'  : 'json',
                   'extras'  : ('description,date_taken,owner_name,'
                                'original_format,media,geo,'
                                'url_z,url_l,url_o,o_dims'),
                   'page'    : page,
                   'per_page': per_page,
                   'nojsoncallback' : '1' }

        values.update(self._url_argument(argument, values))
        url = url + urllib.urlencode(values)

        return url

    def _url_argument(self, argument, values):
        return {'user_id': argument}

    def set_entry_label(self):
        sensitive = False
        label = _('_User:')
        return sensitive, label

    def tooltip(self):
        return _('Enter NSID or User Name in the URL')

    def get_url_for_nsid_lookup(self, arg):
        api = FlickrNSIDAPI()
        user = arg or SETTINGS_FLICKR.get_string('nsid')
        url = api.get_url('http://www.flickr.com/photos/%s/' % user) \
            if user else None
        return url

    def parse_nsid(self, d):
        argument = d['user']['id'] if d.get('user') else None
        return argument, None

    def _add_auth_argument(self, values):
        values['auth_token'] = self.get_auth_token()
        values = add_api_sig(values, SECRET)
        return values

    def get_auth_token(self):
        return SETTINGS_FLICKR.get_string('auth-token')

    def get_interval(self):
        return SETTINGS_FLICKR.get_int('interval') or 60

    def get_page_url(self, owner, id, group=None):
        url = "http://www.flickr.com/photos/%s/%s"
        return url % (owner, id)

class FlickrAuthFactory(object):

    def __init__(self):
        self.auth_token = SETTINGS_FLICKR.get_string('auth-token')
        self._set_method()

    def create(self, argument):
        if self.auth_token:
            api = self.auth_api()
        else:
            api = self.api()

        return api.create()

class FlickrFactoryContactsAPI(FlickrAuthFactory):

    def _set_method(self):
        self.api = FlickrContactsAPI
        self.auth_api = FlickrContactsAuthAPI

    def create(self, argument):
        if self.auth_token and not argument:
            api = self.auth_api()
        else:
            api = self.api()

        return api.create()

class FlickrContactsAPI(FlickrAPI):

    def _set_method(self):
        self.method = 'flickr.photos.getContactsPublicPhotos'

    def is_use_own_id(self):
        return True

    def _url_argument(self, argument, values):
        values.update({'user_id': argument, 'count': 50})
        del values['per_page']
        return values

class FlickrContactsAuthAPI(FlickrContactsAPI):

    def _set_method(self):
        self.method = 'flickr.photos.getContactsPhotos'

    def _url_argument(self, argument, values):
        values = super(
            FlickrContactsAuthAPI, self)._url_argument(argument, values)
        return self._add_auth_argument(values)

    def get_page_url(self, owner, id, nsid):
        url = "http://www.flickr.com/photos/%s/%s/in/contacts/" 
        return url % (owner, id)

class FlickrFactoryFavoritesAPI(FlickrAuthFactory):

    def _set_method(self):
        self.api = FlickrFavoritesAPI
        self.auth_api = FlickrFavoritesAuthAPI

class FlickrFavoritesAPI(FlickrAPI):

    def _set_method(self):
        self.method = 'flickr.favorites.getPublicList'

    def is_use_own_id(self):
        return True

    def get_page_url(self, owner, id, nsid):
        url = "http://www.flickr.com/photos/%s/%s/in/faves-%s/"
        return url % (owner, id, nsid)

class FlickrFavoritesAuthAPI(FlickrFavoritesAPI):

    def _set_method(self):
        self.method = 'flickr.favorites.getList'

    def _url_argument(self, argument, values):
        values.update({'user_id': argument})
        return self._add_auth_argument(values)

class FlickrFavoritesAddAPI(FlickrAPI):

    def _set_method(self):
        self.method = 'flickr.favorites.add'

    def _url_argument(self, argument, values):
        values.update({'photo_id': argument})
        return self._add_auth_argument(values)

class FlickrFavoritesRemoveAPI(FlickrFavoritesAddAPI):

    def _set_method(self):
        self.method = 'flickr.favorites.remove'

class FlickrMetaGroupAPI(object):

    def set_entry_label(self):
        sensitive = False
        label = _('_User:')
        return sensitive, label

    def get_interval(self):
        return SETTINGS_FLICKR.get_int('interval-for-meta-group') or 20

class FlickrGroupAPI(FlickrAPI):

    def _set_method(self):
        self.method = 'flickr.groups.pools.getPhotos'

    def _url_argument(self, argument, values):
        return {'group_id': argument}

    def set_entry_label(self):
        sensitive = True
        label = _('_Group:')
        return sensitive, label

    def tooltip(self):
        return _('Enter NSID or Group Name in the URL')

    def get_url_for_nsid_lookup(self, group):
        api = FlickrGroupNSIDAPI()
        url = api.get_url('http://www.flickr.com/groups/%s/' % group) \
            if group else None
        return url

    def parse_nsid(self, d):
        argument = d['group']['id'] if d.get('group') else None
        return argument, None

    def get_page_url(self, owner, id, group):
        url = "http://www.flickr.com/photos/%s/%s/in/pool-%s/"
        return url % (owner, id, group)

class FlickrYourGroupsAPI(FlickrMetaGroupAPI, FlickrGroupAPI):

    def get_url_for_nsid_lookup(self, arg):
        api = FlickrGroupList()
        user = SETTINGS_FLICKR.get_string('nsid')
        url = api.get_url(user) if user else None
        return url

    def parse_nsid(self, d):
        list = [[g['nsid'], g['name']] for g in d['groups']['group']]
        argument, name = random.choice(list)
        return argument, name

class FlickrInterestingnessAPI(FlickrAPI):

    def _set_method(self):
        self.method = 'flickr.interestingness.getList'
        self.nsid_conversion = False

    def tooltip(self):
        return ""

class FlickrFactoryPeopleAPI(FlickrAuthFactory):

    def _set_method(self):
        self.api = FlickrPeopleAPI
        self.auth_api = FlickrPeopleAuthAPI

class FlickrPeopleAPI(FlickrAPI):

    def _set_method(self):
        self.method = 'flickr.people.getPublicPhotos'

    def _url_argument(self, argument, values):
        return {'user_id': argument}

    def set_entry_label(self):
        sensitive = True
        label = _('_User:')
        return sensitive, label

class FlickrPeopleAuthAPI(FlickrPeopleAPI):

    def _set_method(self):
        self.method = 'flickr.photos.search'

    def _url_argument(self, argument, values):
        values.update({'user_id': argument})
        return self._add_auth_argument(values)

class FlickrCommonsAPI(FlickrMetaGroupAPI, FlickrPeopleAPI):

    def get_url_for_nsid_lookup(self, arg):
        api = FlickrCommonsInstitutions()
        url = api.get_url(None)
        return url

    def parse_nsid(self, d):
        list = [[g['nsid'], g['name']['_content']]
                for g in d['institutions']['institution']]
        argument, name = random.choice(list)
        return argument, name

class FlickrSearchAPI(FlickrAPI):

    def _set_method(self):
        self.method = 'flickr.photos.search'
        self.nsid_conversion = False

    def _url_argument(self, argument, values):
        return {'tags': argument, 'tag_mode': 'all'}

    def set_entry_label(self):
        sensitive = True
        label = _('_Tags:')
        return sensitive, label

    def tooltip(self):
        return ""

class FlickrNSIDAPI(FlickrAPI):

    def _set_method(self):
        self.method = 'flickr.urls.lookupUser'

    def _url_argument(self, argument, values):
        return {'url': argument}

class FlickrGroupNSIDAPI(FlickrNSIDAPI):

    def _set_method(self):
        self.method = 'flickr.urls.lookupGroup'

class FlickrGroupList(FlickrAPI):

    def _set_method(self):
        self.method = 'flickr.people.getPublicGroups'

class FlickrCommonsInstitutions(FlickrAPI):

    def _set_method(self):
        self.method = 'flickr.commons.getInstitutions'

class FlickrExifAPI(FlickrFavoritesAddAPI):

    def _set_method(self):
        self.method = 'flickr.photos.getExif'
