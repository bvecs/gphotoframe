import os
import time
import datetime

from xdg.BaseDirectory import xdg_config_home
from ...utils.sqldb import SqliteDB


class FSpotDB(SqliteDB):

    def _get_db_file(self):
        db_file_base = 'f-spot/photos.db'
        db_file = os.path.join(xdg_config_home, db_file_base)
        return db_file

class FSpotPhotoSQL(object):

    def __init__(self, target=None, period=None):
        self.period = period

        tag_list = FSpotTagList()
        self.tag_list = tag_list.get(target)

        self.photo_tabel = 'photos'
        self.time_column = 'time'

    def get_statement(self, select, rate_name=None, min=0, max=5):
        sql = ['SELECT %s FROM %s P' % (select, self.photo_tabel)]
        sql += self._tag()
        sql.append(self._rate(rate_name, min, max))
        sql.append(self._period(self.period))

        search = False
        for num, statement in enumerate(sql):
            if not statement: continue
            if search:
                sql[num] = sql[num].replace("WHERE", "AND")
            if statement.startswith("WHERE"):
                search = True

        return " ".join(sql)

    def _tag(self):
        if not self.tag_list: return ""

        join = 'INNER JOIN photo_tags PT ON PT.photo_id=P.id'
        tag = "WHERE tag_id IN (%s)" % ", ".join(map(str, self.tag_list))

        return join, tag

    def _rate(self, rate_name=None, min=0, max=5):
        if rate_name is not None:
            sql = 'WHERE rating=%s' % str(rate_name)
        elif not (min == 0 and max == 5):
            sql = 'WHERE (rating BETWEEN %s AND %s)' % (min, max)
        else:
            sql = ""
        return sql

    def _period(self, period):
        if not period: return ""

        period_days = self.get_period_days(period)
        d = datetime.datetime.now() - datetime.timedelta(days=period_days)
        epoch = int(time.mktime(d.timetuple()))

        sql = 'WHERE %s>%s' % (self.time_column, epoch)
        return sql

    def get_period_days(self, period):
        period_dic = {0 : 0, 1 : 7, 2 : 30, 3 : 90, 4 : 180, 5 : 360}
        period_days = period_dic[period]
        return period_days

class FSpotTagList(object):
    "F-Spot all photo Tags for getting photos with tag recursively."

    def __init__(self):
        self.db = FSpotDB()
        self.tag_list = []

    def get(self, target):
        if not target: return []

        sql = 'SELECT id FROM tags WHERE name="%s"' % str(target)
        id = self.db.fetchone(sql)
        self._get_with_category_id(id)

        self.db.close()
        return self.tag_list

    def _get_with_category_id(self, id):
        self.tag_list.append(id)
        sql = 'SELECT id FROM tags WHERE category_id=%s' % id
        list = self.db.fetchall(sql)
        if list:
            for i in list:
                self._get_with_category_id(i[0])

class FSpotPhotoTags(object):
    "Sorted F-Spot photo tags for Gtk.ComboBox"

    def __init__(self):
        self.stags = []
        list = [[0, '', 0]]
        db = FSpotDB()

        if not db.is_accessible:
            return

        sql = 'SELECT * FROM tags ORDER BY id'
        for tag in db.fetchall(sql):
            list.append(tag)
        db.close()

        self._sort_tags(list, [0])

    def get(self):
        return self.stags

    def _sort_tags(self, all_tags, ex_tags):
        unadded_tags = []

        for tag in all_tags:
            if tag[2] in ex_tags:
                self.stags.append(tag)
                ex_tags.append(tag[0])
            else:
                unadded_tags.append(tag)

        if unadded_tags:
            self._sort_tags(unadded_tags, ex_tags)
