# -*- coding: utf8 -*-

import MySQLdb
import gensim
import yaml
import logging
import logging.config
import codecs

import numpy as np

from time import time
from matplotlib import pyplot as plt
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from sklearn import metrics
from sklearn.cluster import MiniBatchKMeans, KMeans
from ConfigParser import SafeConfigParser


def generate_input_embedding_file(logger, dataset, embedding_model_file, mysql_config):
    """Read extractions from db and look up their embeddings given an embedding embedding_model."""

    def select_sql(table_name='svo'):
        return 'SELECT DISTINCT subject_head, predicate_canonical, object_head FROM {} ORDER BY id'.format(table_name)

    def generate_embedding_file(words, type):
        embedding_file = 'data/{}/embeddings/{}s.txt'.format(dataset, type)
        embedding_label_file = 'data/{}/embeddings/{}_labels.txt'.format(dataset, type)
        embedding_label_out = codecs.open(embedding_label_file, 'w', encoding='utf-8')
        embeddings = []
        for w in words:
            if w in embedding_model:
                embeddings.append(embedding_model[w])
                embedding_label_out.write(u'{}\n'.format(w))
        np.savetxt(embedding_file, np.array(embeddings))
        embedding_label_out.close()
        logger.info('{} saved at {}'.format(type, embedding_file))
        logger.info('{} labels saved at {}'.format(type, embedding_label_file))

    conn = MySQLdb.connect(**mysql_config)
    cur = conn.cursor()

    try:
        cur.execute(select_sql())
    except MySQLdb.Error, e:
        try:
            logger.error("MySQL Error [{}]: {}".format(e.args[0], e.args[1]))
        except IndexError:
            logger.error("MySQL Error: {}".format(str(e)))
    else:
        sql_results = cur.fetchall()
        logger.info('{} triples retrieved.'.format(len(sql_results)))

        # Collect all distinct entities and relations.
        entities, relations = set(), set()
        for row in sql_results[:10000]:
            s = row[0].strip()
            p = row[1].strip()
            o = row[2].strip()
            if s:
                entities.add(s)
            if p:
                relations.add(p.replace(' ', '_'))
            if o:
                entities.add(o)
        logger.info('{} entities retrieved'.format(len(entities)))
        logger.info('{} relations retrieved'.format(len(relations)))

        embedding_model = gensim.models.Word2Vec.load_word2vec_format(embedding_model_file, binary=False)
        generate_embedding_file(entities, 'entity_embedding')
        generate_embedding_file(relations, 'relation_embedding')
    finally:
        cur.close()
        conn.close()


def agglomerative_clustering(logger, dataset, type, cluster_n, method='ward', metric='euclidean', plot=False):
    embedding_file = 'data/{}/embeddings/{}s.txt'.format(dataset, type)
    embeddings = np.loadtxt(embedding_file)
    logger.info('Loaded embeddings from {}'.format(embedding_file))

    # Start clustering.
    logger.info('Start clustering ({}, {})...'.format(cluster_n, method))
    t0 = time()
    clustering = linkage(embeddings, method=method, metric=metric)
    logger.info('Clustering time: {}s'.format(time() - t0))

    embedding_labels = []
    embedding_label_file = 'data/{}/embeddings/{}_labels.txt'.format(dataset, type)
    embedding_label_in = codecs.open(embedding_label_file)
    for row in embedding_label_in:
        if row:
            label = row.strip()
            if label:
                embedding_labels.append(label)
    embedding_label_in.close()

    clusters = fcluster(clustering, cluster_n, criterion='maxclust')    # agglomerative_clustering label starts at one
    clusters_agg = {}
    for i in xrange(len(clusters)):
        clusters_agg.setdefault(clusters[i] - 1, []).append(i)
    clustering_clusters_file = 'data/{}/clustering/{}_clusters.txt'.format(dataset, type)
    cluster_out = codecs.open(clustering_clusters_file, 'w')
    for i in xrange(len(clusters_agg)):
        cluster_out.write(u'{}\n'.format(','.join([embedding_labels[j] for j in clusters_agg[i]])))
    cluster_out.close()
    logger.info('Clustering labels saved at {}'.format(clustering_clusters_file))

    if plot:
        plt.figure()
        plt.title('{} clustering'.format(type))
        plt.ylabel('distance')
        dendrogram(
            clustering,
            leaf_rotation=90.,  # rotates the x axis labels
            leaf_font_size=14.,  # font size for the x axis labels
            labels=embedding_labels
        )
        plt.gcf().subplots_adjust(bottom=0.25)
        plt.show()
        # plt.savefig('data/{}/{}_clustering_dendrogram.png'.format(dataset, type), dpi=300)

    # Compute Silhouette Coefficient
    t0 = time()
    sc_score = metrics.silhouette_score(embeddings, clusters, metric=metric)
    logger.info('Silhouette Coefficient: {}'.format(sc_score))
    logger.info('SC computation time: {}s'.format(time() - t0))
    return sc_score


def kmeans(logger, dataset, type, cluster_n):
    embedding_file = 'data/{}/embeddings/{}s.txt'.format(dataset, type)
    embeddings = np.loadtxt(embedding_file)
    logger.info('Loaded embeddings from {}'.format(embedding_file))

    # Start clustering.
    logger.info('Start clustering ({})...'.format(cluster_n))
    k_means = KMeans(init='k-means++', n_clusters=cluster_n, n_init=10)
    t0 = time()
    k_means.fit(embeddings)
    logger.info('Clustering time: {}s'.format(time() - t0))

    clusters = k_means.labels_
    # Compute Silhouette Coefficient
    t0 = time()
    sc_score = metrics.silhouette_score(embeddings, clusters, metric='euclidean')
    logger.info('Silhouette Coefficient: {}'.format(sc_score))
    logger.info('SC computation time: {}s'.format(time() - t0))
    return sc_score


def cross_validate(logger, dataset, type, methods, cluster_numbers, result_file):
    with open(result_file, 'w') as r_out:
        for method in methods:
            for cluster_n in cluster_numbers:
                r_out.write('{}, {}, {}\n'.format(
                    method, cluster_n, agglomerative_clustering(logger, dataset, type, cluster_n, method)))


# def write_cluster_to_db(dataset, mysql_config, logger):
#     """Write clustering results (labels) back to db."""
#
#     def update_cluster_sql(relation, agglomerative_clustering, table_name='svo'):
#         return 'UPDATE {} SET agglomerative_clustering={} WHERE id={}'.format(table_name, str(agglomerative_clustering), str(relation))
#
#     def reset_cluster_sql(table_name='svo'):
#         return 'UPDATE {} SET agglomerative_clustering=NULL'.format(table_name)
#
#     conn = MySQLdb.connect(**mysql_config)
#     cur = conn.cursor()
#
#     try:
#         cur.execute(reset_cluster_sql())
#         conn.commit()
#
#         cluster_file = 'data/{}/clusters.txt'.format(dataset['dataset'])
#         with open(cluster_file) as f:
#             cluster_count = 0
#             for line in f:
#                 line = line.strip() if line else None
#                 if line:
#                     clusters = line.split()
#                     for ind in clusters:
#                         ind = int(ind)
#                         cur.execute(update_cluster_sql(dataset['db_offset'] + ind, cluster_count))
#                         conn.commit()
#                         print ind, cluster_count
#                     cluster_count += 1
#     except MySQLdb.Error, e:
#         conn.rollback()
#         try:
#             logger.error("MySQL Error [{}]: {}".format(e.args[0], e.args[1]))
#         except IndexError:
#             logger.error("MySQL Error: {}".format(str(e)))
#     finally:
#         cur.close()
#         conn.close()


if __name__ == '__main__':
    with open('config/logging_config.yaml') as f:
        logging.config.dictConfig(yaml.load(f))
    logger = logging.getLogger('clustering')

    dataset = 'pmc_c-h'
    db = 'bio-kb'

    # Read MySQL configurations.
    parser = SafeConfigParser()
    parser.read('config/mysql_config.ini')
    mysql_config = {
        'host': parser.get('MySQL', 'host'),
        'user': parser.get('MySQL', 'user'),
        'passwd': parser.get('MySQL', 'passwd'),
        'db': db
    }

    embedding_model_file = 'data/{}/embeddings/directed_embeddings.txt'.format(dataset)

    # generate_input_embedding_file(logger, dataset, embedding_model_file, mysql_config)
    agglomerative_clustering(logger, dataset, 'relation_embedding', 2000, method='average', metric='cosine', plot=True)
    # kmeans(logger, dataset, 'relation_embedding', 1000)

    clustering_methods = ['single', 'complete', 'average', 'weighted', 'centroid', 'median', 'ward']
    # entity_clustering_result_file = 'data/{}/clustering/entity_clustering_results.txt'.format(dataset)
    # entity_clustering_cluster_numbers = [2, 5, 10, 20, 50, 100]
    # cross_validate(logger, dataset, 'entity_embedding', clustering_methods,
    #                entity_clustering_cluster_numbers, entity_clustering_result_file)

    # relation_clustering_result_file = 'data/{}/clustering/relation_clustering_results.txt'.format(dataset)
    # relation_clustering_cluter_numbers = [3000]
    # cross_validate(logger, dataset, 'relation_embedding', clustering_methods,
    #                relation_clustering_cluter_numbers, relation_clustering_result_file)
