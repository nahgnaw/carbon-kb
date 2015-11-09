# -*- coding: utf8 -*-

import MySQLdb
import gensim
import numpy as np

from relation import Relation
from ConfigParser import SafeConfigParser


def select_sql(table_name='svo', limit=10):
    return 'SELECT subject, predicate, object FROM {} ORDER BY id LIMIT {}'.format(table_name, limit)


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
    db_result_size = 12479
    cur.execute(select_sql(limit=db_result_size))
except MySQLdb.Error, e:
    try:
        print "MySQL Error [{}]: {}".format(e.args[0], e.args[1])
    except IndexError:
        print "MySQL Error: {}".format(str(e))
else:
    model_dim = 200
    model = gensim.models.Word2Vec.load_word2vec_format('wikipedia-pubmed-and-PMC-w2v.bin', binary=True)
    relation_vectors = np.zeros((db_result_size, model_dim))
    count = 0
    oov_count = 0
    word_count = 0
    for row in cur.fetchall():
        # print row
        subj, pred, obj = row
        vec = np.zeros(model_dim)
        word_list = subj.split() + obj.split()
        for word in word_list:
            word = word.strip()
            if word:
                word_count += 1
                if word in model:
                    vec += model[word]
                else:
                    print u'[OOV]: {}'.format(word)
                    oov_count += 1
        relation_vectors[count] = vec
        count += 1
    np.savetxt('vectors.vec', relation_vectors)
    print 'Out of vocabulary count: {}'.format(str(oov_count))
    print 'Total word count: {}'.format(str(word_count))
finally:
    cur.close()
    db.close()
