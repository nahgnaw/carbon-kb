# -*- coding: utf8 -*-

import codecs
import yaml
import logging
import logging.config
import MySQLdb
import begin

from ConfigParser import SafeConfigParser
from collections import Counter


def read_triples_from_db(sql_query, db):
    parser = SafeConfigParser()
    parser.read('config/mysql_config.ini')
    mysql_config = {
        'host': parser.get('MySQL', 'host'),
        'user': parser.get('MySQL', 'user'),
        'passwd': parser.get('MySQL', 'passwd'),
        'db': db
    }
    conn = MySQLdb.connect(**mysql_config)
    cur = conn.cursor()

    cur.execute(sql_query)
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results


def save_graph_to_file(graph, output_file, min_edge_count, logger):
    f = codecs.open(output_file, 'w', 'utf-8')
    for vertex in graph:
        counts = Counter(graph[vertex])
        for neighbor in counts:
            weight = counts[neighbor]
            if weight >= int(min_edge_count):
                f.write(u'{}\t{}\t{}\n'.format(vertex, neighbor, str(weight)))
                f.write(u'{}\t{}\t{}\n'.format(neighbor, vertex, str(weight)))  # Have this line for undirected graph
                logger.debug(u'{}\t{}\t{}'.format(vertex, neighbor, str(weight)))
    f.close()


# Every subject_head, predicate, and object_head is considered as a vertex.
# An edge connect a pair of {subject_head, predicate} or {object_head, predicate}.
# The edge weight is the count of the cooccurence of the two connected vertexes.
def build_directed_graph_from_db(mysql_db, logger):
    sql_query = u"""
        SELECT subject_head, predicate_canonical, object_head
        FROM svo
    """
    triples = read_triples_from_db(sql_query, mysql_db)
    graph = {}
    for triple in triples:
        # logger.debug(triple)
        subject_head, predicate_canonical, object_head = triple
        subject_head = subject_head.strip().replace(' ', '_')
        predicate_canonical = predicate_canonical.strip().replace(' ', '_')
        object_head = object_head.strip().replace(' ', '_')
        graph.setdefault(subject_head, []).append(predicate_canonical)
        graph.setdefault(predicate_canonical, []).append(object_head)
    return graph


@begin.subcommand
def construct_graph(output_file, dataset, mysql_db, min_edge_count):
    with open('config/logging_config.yaml') as f:
        logging.config.dictConfig(yaml.load(f))
    logger = logging.getLogger('construct_kb_graph')

    graph_file = 'data/{}/embeddings/{}'.format(dataset, output_file)
    logger.info('Start reading triples from db ...')
    graph = build_directed_graph_from_db(mysql_db, logger)
    logger.info('Start constructing kb graph ...')
    save_graph_to_file(graph, graph_file, min_edge_count, logger)


@begin.start
def main():
    pass

if begin.start():
    pass
