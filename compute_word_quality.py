# -*- coding: utf8 -*-

import os
import re
import math
import string
import codecs
import logging
import logging.config
import itertools
import nltk
import yaml
import cPickle

from textblob import TextBlob


class WordQuality(object):

    def __init__(self, logger, stopwords=None):
        self.logger = logger
        self._stopwords = set(nltk.corpus.stopwords.words('english')) if stopwords is None else stopwords

    def generate_model(self, data_dir):
        self.logger.info('Generating model ...')
        doc_list = []
        for root, _, files in os.walk(data_dir):
            for fn in files:
                if fn.endswith('.txt'):
                    doc = []
                    filename = os.path.join(root, fn)
                    self.logger.info('Processing file {}'.format(filename))
                    f_in = codecs.open(filename, encoding='utf-8')
                    text = f_in.read()
                    # Remove carriage returns
                    text = text.replace('\n', ' ').lower()
                    # Remove punctuations and digits
                    regex = re.compile('[%s\d]' % re.escape(string.punctuation))
                    text = regex.sub('', text)
                    # Lemmatize
                    blob = TextBlob(text)
                    for word, tag in blob.tags:
                        if word not in self._stopwords:
                            if tag.startswith('VB'):
                                doc.append(word.lemmatize('v'))
                            elif tag.startswith('JJ') or tag.startswith('RB'):
                                doc.append(word.lemmatize('a'))
                            else:
                                doc.append(word.lemmatize())
                    doc_list.append(doc)

        model = {}
        self.logger.info('Computing idf ...')
        for word in list(itertools.chain.from_iterable(doc_list)):
            if word not in model:
                word_idf = WordQuality._idf(word, doc_list)
                model[word] = word_idf
                self.logger.debug(u'{}: {}'.format(word, str(word_idf)))
        return model

    def save_model(self, model, filename):
        with open(filename, 'w') as model_file:
            cPickle.dump(model, model_file)
        self.logger.info('Model saved at {}'.format(filename))

    def load_model(self, filename):
        with open(filename) as model_file:
            model = cPickle.load(model_file)
            self.logger.info('Model loaded from {}'.format(filename))
        return model

    @staticmethod
    def _n_containing(word, doc_list):
        return sum(1 for doc in doc_list if word in doc)

    @staticmethod
    def _idf(word, doc_list):
        return math.log(1 + float(len(doc_list)) / WordQuality._n_containing(word, doc_list))


if __name__ == '__main__':
    # Logging
    with open('logging_config.yaml') as f:
        logging.config.dictConfig(yaml.load(f))
    logger = logging.getLogger('word_quality')

    dataset = 'genes-cancer'
    # dataset = 'RiMG75'
    # dataset = 'test'
    data_dir = 'data/{}/raw'.format(dataset)
    model_file = 'data/{}/idf.bin'.format(dataset)
    wq = WordQuality(logger)
    model = wq.generate_model(data_dir)
    wq.save_model(model, model_file)
