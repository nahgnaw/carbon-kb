# -*- coding: utf8 -*-

import MySQLdb
import gensim
import yaml
import logging
import logging.config
import codecs
import random
import unicodecsv

import numpy as np

from time import time
from matplotlib import pyplot as plt
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from sklearn import metrics
from sklearn.cluster import MiniBatchKMeans, KMeans
from ConfigParser import SafeConfigParser


def generate_embedding_file(embedding_model_name, embedding_model,
                            embedding_type, items, cluster_label_ground_truth_file=None):
    """Produce a file containing the embeddings of given words.
       Produce a file containing the clustering ground truth (labels) of given words."""
    embedding_file = 'data/{}/embeddings/{}_{}.npy'.format(dataset, embedding_model_name, embedding_type)
    embedding_label_file = 'data/{}/embeddings/{}_{}_labels.txt'.format(dataset, embedding_model_name, embedding_type)
    embedding_out = codecs.open(embedding_label_file, 'w', encoding='utf-8')
    embeddings = []

    if cluster_label_ground_truth_file:
        cluster_labels = []
        for _ in xrange(len(items[0]) - 1):
            cluster_labels.append([])

    counter = 0
    for item in items:
        if item[0] in embedding_model and -1 not in item[1:]:
            counter += 1
            embeddings.append(embedding_model[item[0]])
            embedding_out.write(u'{}\n'.format(item[0]))
            for i, x in enumerate(item[1:]):
                cluster_labels[i].append(str(x))

    np.save(embedding_file, np.array(embeddings))
    embedding_out.close()

    logger.info('{} {} saved at {}'.format(counter, embedding_type, embedding_file))
    logger.info('embedding labels saved at {}'.format(embedding_label_file))

    if cluster_label_ground_truth_file:
        cluster_label_out = codecs.open(cluster_label_ground_truth_file, 'w', encoding='utf-8')
        logger.info('cluster label ground truth saved at {}'.format(cluster_label_ground_truth_file))
        for i in xrange(len(cluster_labels)):
            cluster_label_out.write(u'{}\n'.format(','.join(cluster_labels[i])))
            logger.info('cluster group {}: {} labels'.format(i, len(cluster_labels[i])))
        cluster_label_out.close()


def generate_embedding_file_from_csv(embedding_model_name, embedding_type, csv_file):
    """Read entities or relations from a csv file and look up their embeddings given an embedding model."""
    items = []
    csv_in = open(csv_file)
    csv_reader = unicodecsv.reader(csv_in)
    for row in csv_reader:
        row_len = len(row)
        if row_len:
            item = [row[1].strip()]
            for x in row[2:]:
                item.append(int(x))
            items.append(item)
    logger.info('{} items retrieved'.format(len(items)))

    cluster_label_ground_truth_file = None
    if len(items[0]) > 1:
        cluster_label_ground_truth_file = \
            'data/evaluation/clustering/{}_ground_truth.txt'.format(embedding_type)

    embedding_model_file = 'data/{}/embeddings/{}'.format(dataset, embedding_model_name)
    embedding_model = gensim.models.Word2Vec.load_word2vec_format(embedding_model_file, binary=True)
    generate_embedding_file(embedding_model_name, embedding_model, embedding_type,
                            items, cluster_label_ground_truth_file)


def generate_embedding_file_from_mysql(embedding_model_name, result_n):
    """Read entities and relations from a MySQL db and look up their embeddings given an embedding model."""

    def select_sql(table_name='svo'):
        return 'SELECT DISTINCT subject_head, predicate_canonical, object_head FROM {} ORDER BY id'.format(table_name)

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

        if result_n > len(sql_results):
            logger.error('There are not so many results returned from the database!')
            exit()

        # Collect distinct entities and relations.
        entities, relations = set(), set()
        # Randomly pick rows.
        rows = random.sample(xrange(len(sql_results)), result_n)
        for i in rows:
            row = sql_results[i]
            s = row[0].strip()
            p = row[1].strip()
            o = row[2].strip()
            if s:
                entities.add((s.replace(' ', '_'),))
            if p:
                relations.add((p.replace(' ', '_'),))
            if o:
                entities.add((o.replace(' ', '_'),))
        logger.info('{} entities retrieved'.format(len(entities)))
        logger.info('{} relations retrieved'.format(len(relations)))

        embedding_model_file = 'data/{}/embeddings/{}'.format(dataset, embedding_model_name)
        embedding_model = gensim.models.Word2Vec.load_word2vec_format(embedding_model_file, binary=True)
        generate_embedding_file(embedding_model_name, embedding_model, 'entities', list(entities))
        generate_embedding_file(embedding_model_name, embedding_model, 'relations', list(relations))
    finally:
        cur.close()
        conn.close()


def agglomerative_clustering(embedding_model_name, embedding_type, cluster_label_ground_truth_file,
                             cluster_n, method='ward', metric='euclidean', plot=False):
    embedding_file = 'data/{}/embeddings/{}_{}.npy'.format(dataset, embedding_model_name, embedding_type)
    embeddings = np.load(embedding_file)
    logger.info('Loaded embeddings from {}'.format(embedding_file))

    # Start clustering.
    logger.info('Start clustering ({}, {})...'.format(cluster_n, method))
    t0 = time()
    clustering = linkage(embeddings, method=method, metric=metric)
    logger.info('Clustering time: {}s'.format(time() - t0))

    embedding_labels = []
    embedding_label_file = 'data/{}/embeddings/{}_{}_labels.txt'.format(dataset, embedding_model_name, embedding_type)
    embedding_label_in = codecs.open(embedding_label_file)
    for row in embedding_label_in:
        if row:
            label = row.strip()
            if label:
                embedding_labels.append(label)
    embedding_label_in.close()

    cluster_label_prediction = fcluster(clustering, cluster_n, criterion='maxclust')    # 1-based index
    # logger.info('Cluster label prediction: {}'.format(cluster_label_prediction))
    clusters_agg = {}
    for i in xrange(len(cluster_label_prediction)):
        clusters_agg.setdefault(cluster_label_prediction[i] - 1, []).append(i)
    clustering_clusters_file = 'data/{}/clustering/{}_clusters.txt'.format(dataset, embedding_type)
    cluster_out = codecs.open(clustering_clusters_file, 'w')
    for i in xrange(len(clusters_agg)):
        cluster_out.write(u'{}\n'.format(','.join([embedding_labels[j] for j in clusters_agg[i]])))
    cluster_out.close()
    logger.info('Clustering labels saved at {}'.format(clustering_clusters_file))

    if cluster_label_ground_truth_file:
        # Read cluster label ground truth
        cluster_label_ground_truth = []
        with open(cluster_label_ground_truth_file) as f:
            for line in f:
                if line:
                    cluster_label_ground_truth.append(map(int, line.strip().split(',')))

        # Compute Ajusted Rand Index
        for i in xrange(len(cluster_label_ground_truth)):
            ari = metrics.adjusted_rand_score(cluster_label_ground_truth[i], cluster_label_prediction)
            logger.info('Ajusted Rand Index for cluster group {}: {}'.format(i, ari))
            ami = metrics.adjusted_mutual_info_score(cluster_label_ground_truth[i], cluster_label_prediction)
            logger.info('Ajusted Mutual Information Score for cluster group {}: {}'.format(i, ami))
            chv = metrics.homogeneity_completeness_v_measure(cluster_label_ground_truth[i], cluster_label_prediction)
            logger.info('V-measure score for cluster group {}: {}'.format(i, chv))

    # Compute Silhouette Coefficient
    t0 = time()
    sc_score = metrics.silhouette_score(embeddings, cluster_label_prediction, metric=metric)
    logger.info('Silhouette Coefficient: {}'.format(sc_score))
    logger.info('SC computation time: {}s'.format(time() - t0))

    if plot:
        plt.rc('lines', linewidth=2)
        plt.figure()
        plt.title('{} Clustering'.format('Relation'), fontsize=28)
        plt.yticks([])
        dendrogram(
            clustering,
            leaf_rotation=90.,  # rotates the x axis labels
            leaf_font_size=14.,  # font size for the x axis labels
            labels=embedding_labels
        )
        plt.gcf().subplots_adjust(bottom=0.25)
        plt.show()
        # plt.savefig('data/{}/{}_clustering_dendrogram.png'.format(dataset, type), dpi=300)

    return sc_score


def kmeans(embedding_model, embedding_type, cluster_n, cluster_label_ground_truth_file):
    embedding_file = 'data/{}/embeddings/{}_{}.npy'.format(dataset, embedding_model, embedding_type)
    embeddings = np.load(embedding_file)
    logger.info('Loaded embeddings from {}'.format(embedding_file))

    # Start clustering.
    logger.info('Start clustering ({})...'.format(cluster_n))
    k_means = KMeans(init='k-means++', n_clusters=cluster_n, n_init=10)
    t0 = time()
    k_means.fit(embeddings)
    logger.info('Clustering time: {}s'.format(time() - t0))
    cluster_label_prediction = k_means.labels_
    logger.info('Cluster label prediction: {}'.format(cluster_label_prediction))

    # Read cluster label ground truth
    cluster_label_ground_truth = []
    with open(cluster_label_ground_truth_file) as f:
        for line in f:
            if line:
                cluster_label_ground_truth.append(map(int, line.strip().split(',')))

    # Compute Ajusted Rand Index
    for i in xrange(len(cluster_label_ground_truth)):
        logger.info('Cluster label ground truth: {}'.format(cluster_label_ground_truth[i]))
        ari = metrics.adjusted_rand_score(cluster_label_ground_truth[i], cluster_label_prediction)
        logger.info('Ajusted Rand Index for cluster group {}: {}'.format(i, ari))

    # Compute Silhouette Coefficient
    t0 = time()
    sc_score = metrics.silhouette_score(embeddings, cluster_label_prediction, metric='euclidean')
    logger.info('Silhouette Coefficient: {}'.format(sc_score))
    logger.info('SC computation time: {}s'.format(time() - t0))
    return sc_score


def cross_validate(embedding_type, methods, cluster_numbers, result_file):
    with open(result_file, 'w') as r_out:
        for method in methods:
            for cluster_n in cluster_numbers:
                r_out.write('{}, {}, {}\n'.format(
                    method, cluster_n, agglomerative_clustering(embedding_type, cluster_n, method)))


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

    embedding_model_name = 'scikb_directed'
    # embedding_model_name = 'word2vec'
    # embedding_model_name = 'pmc_w2v'

    # embedding_type = 'entities'
    embedding_type = 'relations'

    # benchmark_file = 'data/evaluation/clustering/{}.csv'.format(embedding_type)
    # generate_embedding_file_from_csv(embedding_model_name, embedding_type, benchmark_file)
    # generate_embedding_file_from_mysql(embedding_model_name, 100)

    # cluster_label_ground_truth_file = 'data/evaluation/clustering/{}_ground_truth.txt'.format(embedding_type)
    cluster_label_ground_truth_file = None
    # cluster_n: all-3,40; e1-15; e2-7; e3-18
    agglomerative_clustering(embedding_model_name, embedding_type, cluster_label_ground_truth_file,
                             20, method='ward', metric='euclidean', plot=True)
    # kmeans(embedding_model_name, 'entities', 26, cluster_label_ground_truth_file)

    # Cross validation for clustering parameters.
    # clustering_methods = ['single', 'complete', 'average', 'weighted', 'centroid', 'median', 'ward']
    # entity_clustering_result_file = 'data/{}/clustering/entity_clustering_results.txt'.format(dataset)
    # entity_clustering_cluster_numbers = [2, 5, 10, 20, 50, 100]
    # cross_validate('entity_embedding', clustering_methods,
    #                entity_clustering_cluster_numbers, entity_clustering_result_file)

    # relation_clustering_result_file = 'data/{}/clustering/relation_clustering_results.txt'.format(dataset)
    # relation_clustering_cluter_numbers = [3000]
    # cross_validate('relation_embedding', clustering_methods,
    #                relation_clustering_cluter_numbers, relation_clustering_result_file)
