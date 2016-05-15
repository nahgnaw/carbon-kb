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

    def __init__(self, logger=None, stopwords=None):
        self.logger = logger if logger else logging.getLogger()
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
                    # Remove carriage returns, punctuations and digits
                    regex = re.compile('\- |[%s\d\n]' % re.escape(string.punctuation))
                    text = regex.sub('', text)
                    # Lemmatize
                    blob = TextBlob(text.lower())
                    for word, tag in blob.tags:
                        if word not in self._stopwords and len(word) > 2:
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
        num_doc = len(doc_list)
        num_word_doc = WordQuality._n_containing(word, doc_list)
        return math.log(1 + float(num_doc) / num_word_doc)


def generate_idf_dict():
    # dataset = 'genes-cancer'
    dataset = 'acl'
    # dataset = 'RiMG75'
    # dataset = 'test'
    data_dir = 'data/{}/raw'.format(dataset)
    model_file = 'data/{}/idf.pkl'.format(dataset)

    wq = WordQuality()
    model = wq.generate_model(data_dir)
    wq.save_model(model, model_file)


def generate_ignored_word_dict():
    logger = logging.getLogger()

    idf_diff_threshold = 1.5
    dataset_1 = 'genes-cancer'
    dataset_2 = 'acl'

    wq = WordQuality()
    ignored_words = {}
    model_1 = wq.load_model('data/{}/idf.pkl'.format(dataset_1))
    model_2 = wq.load_model('data/{}/idf.pkl'.format(dataset_2))
    for word in model_1:
        if word in model_2 and abs(model_2[word] - model_1[word]) < idf_diff_threshold:
            logger.debug(u'{}: {}'.format(word, model_1[word]))
            ignored_words[word] = model_1[word]
    wq.save_model(ignored_words, 'data/{}/ignored_words.pkl'.format(dataset_1))


if __name__ == '__main__':
    with open('config/logging_config.yaml') as f:
        logging.config.dictConfig(yaml.load(f))

    # generate_idf_dict()
    generate_ignored_word_dict()
