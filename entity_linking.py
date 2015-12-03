# -*- coding: utf8 -*-

import requests
import urllib


class EntityLinker(object):

    def __init__(self, logger, api='http://el.tw.rpi.edu/bio_qcv/linking?query='):
        self._api = api
        self.logger = logger

    def query(self, query, delimiter=','):
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
                return [res['url'] for res in results]
        return None


if __name__ == '__main__':
    el = EntityLinker()
    query = 'ability'
    res = el.query(query)
    print res
