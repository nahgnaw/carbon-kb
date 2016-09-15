# -*- coding: utf8 -*-

import requests
import urllib
import logging
import logging.config
import yaml
import MySQLdb

from ConfigParser import SafeConfigParser


class EntityLinker(object):

    def __init__(self, logger=None, api='http://el.tw.rpi.edu/bio_qcv/linking?query='):
        self._api = api
        self.logger = logger if logger else logging.getLogger()

    def link(self, query, delimiter=','):
        if isinstance(query, list):
            query = ','.join(query)

        if not delimiter == ',':
            query = query.replace(delimiter, ',')

        query_url = self._api + urllib.quote(query)
        self.logger.debug('Entity linking url: {}'.format(query_url))
        r = requests.get(query_url)
        if r.status_code == requests.codes.ok:
            results = r.json()['results'][0]['annotations']
            if len(results) and not results[0]['url'] == 'NIL':
                return [res['url'] for res in results if res['url'].startswith('<')]
        return None

    def write_to_db(self, db, min_id=1):

        def read_triples_sql(min_id=1, table_name='svo'):
            return u"""
                SELECT id, subject_head, subject_nn_head, object_head, object_nn_head
                FROM {}
                WHERE id >= {}
            """.format(table_name, str(min_id))

        def update_el_sql(id, el_column, el_results, table_name='svo'):
            return u"""
                UPDATE {} SET {}="{}" WHERE id={}
            """.format(table_name, el_column, el_results, str(id))

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

        # Read triples to construct el queries
        triples = None
        try:
            cur.execute(read_triples_sql(min_id=min_id))
            triples = cur.fetchall()
        except MySQLdb.Error, e:
            try:
                logger.error("MySQL Error [{}]: {}".format(e.args[0], e.args[1]))
            except IndexError:
                logger.error("MySQL Error: {}".format(str(e)))
        if triples:
            for triple in triples:
                triple_id, subj_head, subj_nn_head, obj_head, obj_nn_head = triple
                subj_el_results, obj_el_results = None, None
                if subj_head:
                    subj_head = subj_head.strip()
                    subj_nn_head = subj_nn_head.strip().split()
                    subj_el_query = [subj_head]
                    subj_el_query += [w for w in subj_nn_head if not w == subj_head]
                    if obj_nn_head:
                        subj_el_query += obj_nn_head.strip().split()
                    logger.debug(subj_el_query)
                    subj_el_results = self.link(subj_el_query)
                if obj_head:
                    obj_head = obj_head.strip()
                    obj_nn_head = obj_nn_head.strip().split()
                    obj_el_query = [obj_head]
                    obj_el_query += [w for w in obj_nn_head if not w == obj_head]
                    if subj_nn_head:
                        obj_el_query += subj_nn_head
                    logger.debug(obj_el_query)
                    obj_el_results = self.link(obj_el_query)
                if subj_el_results or obj_el_results:
                    try:
                        if subj_el_results:
                            cur.execute(update_el_sql(triple_id, 'subject_el', ','.join(subj_el_results)))
                        if obj_el_results:
                            cur.execute(update_el_sql(triple_id, 'object_el', ','.join(obj_el_results)))
                        conn.commit()
                        logger.debug(u'Updated triple {}'.format(str(triple_id)))
                    except MySQLdb.Error, e:
                        conn.rollback()
                        try:
                            logger.error("MySQL Error [{}]: {}".format(e.args[0], e.args[1]))
                        except IndexError:
                            logger.error("MySQL Error: {}".format(str(e)))
        cur.close()
        conn.close()


if __name__ == '__main__':
    with open('config/logging_config.yaml') as f:
        logging.config.dictConfig(yaml.load(f))
    logger = logging.getLogger('entity_linking_flag')

    el = EntityLinker(logger)
    el.write_to_db('bio-kb', 7917)
