import os
import sys
import sqlite3


class SqliteDB(object):

    def __init__(self):
        db_file = self._get_db_file()
        if not os.access(db_file, os.R_OK):
            print "Not found: ", db_file
            db_file = None

        self.is_accessible = bool(db_file)
        if db_file:
            self.db = sqlite3.connect(db_file)

    def fetchall(self, sql):
        try:
            data = self.db.execute(sql).fetchall()
            return data
        except:
            print "%s: %s" % (sys.exc_info()[1], sql)

    def fetchone_raw(self, sql):
        try:
            data = self.db.execute(sql).fetchone()
            return data
        except:
            print "%s: %s" % (sys.exc_info()[1], sql)

    def fetchone(self, sql):
        try:
            data = self.db.execute(sql).fetchone()[0]
            return data
        except:
            print "%s: %s" % (sys.exc_info()[1], sql)

    def execute(self, sql):
        data = self.db.execute(sql)
        return data

    def commit(self):
        self.db.commit()

    def close(self):
        self.db.close()

    def execute_with_commit(self, sql):
        try:
            self.execute(sql)
            self.commit()
        except:
            print "%s: %s" % (sys.exc_info()[1], sql)

    def _get_db_file(self):
        pass
