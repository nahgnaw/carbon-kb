# -*- coding: utf8 -*-

import MySQLdb
import gensim
import numpy as np

from ConfigParser import SafeConfigParser


def generate_embedding_file(dataset, mysql_config):

    def select_sql(table_name='svo'):
        return 'SELECT subject, predicate, object FROM {} ORDER BY id'.format(table_name)

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
        model_file = 'data/{}/word2vec.bin'.format(dataset['dataset'])
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
            row_word_count = 0
            for word in word_list:
                word = word.strip()
                if word:
                    if dataset['db'] == 'earth-kb':
                        word = word.lower()
                    word_count += 1
                    if word in model:
                        vec += model[word]
                        row_word_count += 1
                    else:
                        print u'[OOV]: {}'.format(word)
                        oov_count += 1
            subj_obj_embeddings[result_count] = vec / float(row_word_count)
            result_count += 1
        embedding_file = 'data/{}/subj_obj_embeddings.txt'.format(dataset['dataset'])
        np.savetxt(embedding_file, subj_obj_embeddings)
        print 'Out of vocabulary words: {}'.format(str(oov_count))
        print 'Total words: {}'.format(str(word_count))
    finally:
        cur.close()
        db.close()


def write_cluster_to_db(dataset, mysql_config):

    def update_cluster_sql(relation, cluster, table_name='svo'):
        return 'UPDATE {} SET cluster={} WHERE id={}'.format(table_name, str(cluster), str(relation))

    def reset_cluster_sql(table_name='svo'):
        return 'UPDATE {} SET cluster=NULL'.format(table_name)

    db = MySQLdb.connect(**mysql_config)
    cur = db.cursor()

    try:
        cur.execute(reset_cluster_sql())
        db.commit()

        cluster_file = 'data/{}/clusters.txt'.format(dataset['dataset'])
        with open(cluster_file) as f:
            cluster_count = 0
            for line in f:
                line = line.strip() if line else None
                if line:
                    clusters = line.split()
                    for ind in clusters:
                        ind = int(ind)
                        cur.execute(update_cluster_sql(dataset['db_offset'] + ind, cluster_count))
                        db.commit()
                        print ind, cluster_count
                    cluster_count += 1
    except MySQLdb.Error, e:
        db.rollback()
        try:
            print "MySQL Error [{}]: {}".format(e.args[0], e.args[1])
        except IndexError:
            print "MySQL Error: {}".format(str(e))
    finally:
        cur.close()
        db.close()


if __name__ == '__main__':

    dataset = {'dataset': 'genes-cancer', 'db': 'bio-kb', 'db_offset': 6037}
    # dataset = {'dataset': 'RiMG75', 'db': 'earth-kb', 'db_offset': 1}

    # Connect to MySQL
    parser = SafeConfigParser()
    parser.read('config.ini')
    mysql_config = {
        'host': parser.get('MySQL', 'host'),
        'user': parser.get('MySQL', 'user'),
        'passwd': parser.get('MySQL', 'passwd'),
        'db': dataset['db']
    }

    # generate_embedding_file(dataset, mysql_config)
    write_cluster_to_db(dataset, mysql_config)

