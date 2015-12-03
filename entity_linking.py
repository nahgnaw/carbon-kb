# -*- coding: utf8 -*-

import requests


class EntityLinker(object):

    def __init__(self, api='http://el.tw.rpi.edu/bio_qcv/linking?query='):
        self.api = api

    def query(self, query, delimiter=','):
        if isinstance(query, list):
            query = ','.join(query)

        if not delimiter == ',':
            query = query.replace(delimiter, ',')

        query_url = self.api + query
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
