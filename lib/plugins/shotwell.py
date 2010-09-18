import os
import sqlite3

import gtk
from gettext import gettext as _

from ..utils.iconimage import IconImage
from base import *
from fspot.__init__ import *
from fspot.rating import RateList
from fspot.sqldb import FSpotDB, FSpotPhotoSQL

def info():
    return [ShotwellPlugin, ShotwellPhotoList, PhotoSourceShotwellUI]

class ShotwellPlugin(FSpotPlugin):

    def __init__(self):
        self.name = 'Shotwell'
        self.icon = ShotwellIcon
        self.db_class = ShotwellDB

class ShotwellPhotoList(FSpotPhotoList):

    def prepare(self):
        self.db = ShotwellDB()
        self.period = self.options.get('period')

        if self.db:
            self.sql = ShotwellPhotoSQL(self.target, self.period)
            self.photos = self.rate_list = RateList(self, ShotwellDB)

    def get_photo(self, cb):
        rate = self.rate_list.get_random_weight()
        columns = 'filename, id'
        sql = self.sql.get_statement(columns, rate.name)
        sql += ' ORDER BY random() LIMIT 1;'

        photo = self.db.fetchall(sql)
        if not photo: return False
        filename, id = photo[0]

        data = { 'url' : 'file:/' + filename,
                 'rate' : rate.name,
                 'filename' : filename,
                 'title' : os.path.basename(filename), # without path
                 'id' : id,
                 'fav' : ShotwellFav(rate.name, id, self.rate_list),
                 'icon' : ShotwellIcon }

        self.photo = Photo(data)
        cb(None, self.photo)

class PhotoSourceShotwellUI(PhotoSourceUI):

    def get_options(self):
        return self.options_ui.get_value()

    def _make_options_ui(self):
        self.options_ui = PhotoSourceOptionsFspotUI(self.gui, self.data)

    def _label(self):
        tags = ShotwellPhotoTags()
        sorted_tags = tags.get()
        return sorted_tags

class ShotwellFav(FSpotFav):

    def _prepare(self):
        self.sql_table = 'PhotoTable'
        self.db_class = ShotwellDB

class ShotwellIcon(IconImage):

    def __init__(self):
        self.icon_name = 'shotwell'

# sql

class ShotwellDB(FSpotDB):

    def __init__(self):
        db_file = self._get_db_file()
        self.is_accessible = True if db_file else False
        if db_file:
            self.db = sqlite3.connect(db_file)

    def _get_db_file(self):
        db_file_base = '.shotwell/data/photo.db'
        db_file = os.path.join(os.environ['HOME'], db_file_base)

        if not os.access(db_file, os.R_OK):
            db_file = None
        return db_file

class ShotwellPhotoSQL(FSpotPhotoSQL):

    def __init__(self, target=None, period=None):
        self.period = period
        self.target = target

        self.photo_tabel = 'PhotoTable'
        self.time_column = 'timestamp'

    def _tag(self):
        if not self.target: return ""

        sql = 'SELECT photo_id_list FROM TagTable WHERE name="%s"' % str(self.target)
        db = ShotwellDB()
        photo_id_list = db.fetchone(sql)
        db.close()

        tag = "WHERE id IN (%s)" % photo_id_list.rstrip(',')
        return [tag]

class ShotwellPhotoTags(object):
    "Sorted Shotwell photo tags for gtk.ComboBox"

    def __init__(self):
        self.list = ['']
        db = ShotwellDB()

        if not db.is_accessible:
            return

        sql = 'SELECT name FROM TagTable'
        for tag in db.fetchall(sql):
            self.list.append(tag[0])
        db.close()

        self.list.sort()

    def get(self):
        return self.list