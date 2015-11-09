# -*- coding: utf8 -*-

import MySQLdb
import gensim
import numpy as np

from ConfigParser import SafeConfigParser


def select_sql(table_name='svo', limit=10):
    return 'SELECT subject, predicate, object FROM {} ORDER BY id'.format(table_name)


dataset = 'genes-cancer'
# dataset = 'RiMG75'
mysql_db = 'bio-kb'
# mysql_db = 'earth-kb'

# Connect to MySQL
parser = SafeConfigParser()
parser.read('config.ini')
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
    sql_results = cur.fetchall()

    embedding_dim = 200
    model_file = 'data/{}/word2vec.bin'.format(dataset)
    model = gensim.models.Word2Vec.load_word2vec_format(model_file, binary=True)
    subj_obj_embeddings = np.zeros((len(sql_results), embedding_dim))

    result_count = 0
    oov_count = 0
    word_count = 0
    for row in sql_results:
        # print row
        subj, pred, obj = row
        vec = np.zeros(embedding_dim)
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
        subj_obj_embeddings[result_count] = vec
        result_count += 1
    embedding_file = 'data/{}/subj_obj_embeddings.txt'.format(dataset)
    np.savetxt(embedding_file, subj_obj_embeddings)
    print 'Out of vocabulary result_count: {}'.format(str(oov_count))
    print 'Total word result_count: {}'.format(str(word_count))
finally:
    cur.close()
    db.close()
