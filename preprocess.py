# -*- coding: utf8 -*-

import os
import re
import codecs
import logging
import logging.config
import yaml
import nltk.data
from segtok.segmenter import split_single, split_multi


class Sentences(object):

    def __init__(self, dataset, logger):
        self.logger = logger
        self._dataset = dataset
        self._raw_data_dir = 'data/{}/raw'.format(self._dataset)
        self._processed_text_dir = 'data/{}/processed'.format(self._dataset)
        # self.sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')
        # extra_abbr = ['dr', 'vs', 'mr', 'mrs', 'prof', 'inc', 'i.e', 'fig', 'figs', 'p', 'et al', 'e.g', 'etc', 'eq']
        # self.sent_detector._params.abbrev_types.update(extra_abbr)

    def __iter__(self):
        for root, _, files in os.walk(self._raw_data_dir):
            for fn in files:
                if fn.endswith('.txt'):
                    filename = os.path.join(root, fn)
                    f = codecs.open(filename, encoding='utf-8')
                    text = f.read()
                    if text:
                        text = self.process_text(text)
                        for sent in split_multi(text):
                            # Discard very long and very short sentences
                            if sent and len(sent) < 1000 and len(sent.split()) > 2:
                                sent = sent.strip()
                                yield fn, sent
                    f.close()

    def save(self, dir=None):
        if not dir:
            dir = self._processed_text_dir
        # First empty dir
        file_list = [f for f in os.listdir(dir) if f.endswith('.txt')]
        for f in file_list:
            os.remove(os.path.join(dir, f))
        for fn, sent in self.__iter__():
            self.logger.debug(u'{} {}'.format(fn, sent))
            file_path = os.path.join(dir, fn)
            f = codecs.open(file_path, 'a', encoding='utf-8')
            f.write(u'{}\n'.format(sent))
            f.close()

    def process_text(self, text):
        replacement = [
            r'(\s*\([^()]*\))',    # Parentheses
            r'(\s*\[.*\])',    # Parentheses
            r'(\b(([\w-]+://?|www[.])[^\s()<>]+(?:\([\w\d]+\)|([^[:punct:]\s]|/))))',   # url
            r'([A-Za-z0-9]\))',   # List item markers with just one parenthesis
            # r'((Fig\.?u?r?e?\s\d{1,3}\.?))',  # Figure caption
            # r'(Table\.?\s\d{1,3}\.?)',    # Table caption
            # r'(([A-Z]\S+)+(\sand\s)?([A-Z]\S+)?\s(et al.)?,?\s*\d{4}[a-z]?[;|,]*)',   # Citations
            # r'(([A-Z]\S+)+(\sand\s)?([A-Z]\S+)?\s(et al.)?,?\s*\(\d{4}[a-z]?\)[;|,]*)',   # Citations
        ]
        replacement_pattern = re.compile('|'.join(replacement), re.UNICODE | re.IGNORECASE)
        text = re.sub(replacement_pattern, '', text)

        if self._dataset == 'genes-cancer':
            text = text.replace('.-', '.').replace('.,', '.')

        return text


if __name__ == '__main__':
    with open('config/logging_config.yaml') as f:
        logging.config.dictConfig(yaml.load(f))
    logger = logging.getLogger('preprocess')

    # dataset = 'test'
    # dataset = 'genes-cancer'
    dataset = 'RiMG75'

    sents = Sentences(dataset, logger)
    sents.save()
