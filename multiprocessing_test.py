# -*- coding: utf8 -*-

import os
import codecs
import yaml
import multiprocessing
import logging
import logging.config
import time
import MySQLdb

from ConfigParser import SafeConfigParser

from extract_relations import RelationExtractor


def process_file(filename, parser_server):
    logger = logging.getLogger('single_relation_extraction')

    parser = SafeConfigParser()
    parser.read('config/mysql_config.ini')
    mysql_config = {
        'host': parser.get('MySQL', 'host'),
        'user': parser.get('MySQL', 'user'),
        'passwd': parser.get('MySQL', 'passwd'),
        'db': 'bio-kb'
    }

    db = MySQLdb.connect(**mysql_config)
    cur = db.cursor()

    f_in = codecs.open(filename, encoding='utf-8')
    for line in f_in:
        sent = line.strip()
        if sent:
            logger.info(u'{}: {}'.format(filename, sent))
            try:
                extractor = RelationExtractor(sent, logger, parser_server)
            except:
                logger.error(u'Failed to extract relations.', exc_info=True)
            else:
                extractor.extract_spo()
                for relation in extractor.relations:
                    logger.info(u'RELATION: {}'.format(relation))
                    try:
                        cur.execute(insert_relation_sql(sent, relation))
                        db.commit()
                    except MySQLdb.Error, e:
                        try:
                            logger.error(u'MySQL Error [{}]: {}'.format(e.args[0], e.args[1]),
                                         exc_info=True)
                        except IndexError:
                            logger.error(u'MySQL Error: {}'.format(str(e)), exc_info=True)

    f_in.close()
    cur.close()
    db.close()


def insert_relation_sql(sentence, relation, table_name='test'):
    sentence = sentence.replace('"', '')
    return u"""
        INSERT INTO {} (subject_head, subject_nn_head, subject, subject_el, predicate, predicate_canonical,
                        object_head, object_nn_head, object, object_el, sentence)
        VALUES ("{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}");
    """.format(
        table_name,
        relation.subject.head.lemma, relation.subject.nn_head.lemma, relation.subject.lemma, relation.subject_el,
        relation.predicate.lemma, relation.predicate.canonical_form,
        relation.object.head.lemma, relation.object.nn_head.lemma, relation.object.lemma, relation.object_el,
        sentence
    )


if __name__ == '__main__':

    begin_time = time.time()

    with open('config/logging_config.yaml') as f:
        logging.config.dictConfig(yaml.load(f))

    dataset = 'test'
    data_dir = 'data/{}/processed/'.format(dataset)

    parser_servers = [
        'http://localhost:8084',
        'http://localhost:8085',
        'http://localhost:8086',
        'http://localhost:8087',
        'http://localhost:8088',
        'http://localhost:8089',
        'http://localhost:8090',
        'http://localhost:8091'
    ]

    pool = multiprocessing.Pool(7)

    file_count = 0
    for root, _, files in os.walk(data_dir):
        for fn in files:
            if fn.endswith('.txt'):
                filename = os.path.join(root, fn)
                parser = parser_servers[file_count % len(parser_servers)]
                pool.apply(process_file, args=(filename, parser))
                file_count += 1

    pool.close()
    pool.join()

    print 'Running time: {}'.format(str(time.time() - begin_time))
