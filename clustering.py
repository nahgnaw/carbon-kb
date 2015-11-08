# -*- coding: utf8 -*-

import MySQLdb
import gensim

from ConfigParser import SafeConfigParser


def select_sql(table_name='svo', limit=10):
    return 'SELECT subject, predicate, object FROM {} LIMIT {}'.format(table_name, limit)


parser = SafeConfigParser()
parser.read('config.ini')
dataset = 'genes-cancer'
mysql_db = 'bio-kb'
mysql_config = {
    'host': parser.get('MySQL', 'host'),
    'user': parser.get('MySQL', 'user'),
    'passwd': parser.get('MySQL', 'passwd'),
    'db': mysql_db
}
db = MySQLdb.connect(**mysql_config)
cur = db.cursor()
try:
    cur.execute(select_sql())
except MySQLdb.Error, e:
    try:
        print "MySQL Error [{}]: {}".format(e.args[0], e.args[1])
    except IndexError:
        print "MySQL Error: {}".format(str(e))
else:
    for row in cur.fetchall():
        print row
finally:
    cur.close()
    db.close()
