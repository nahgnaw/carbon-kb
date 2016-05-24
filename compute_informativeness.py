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


class WordInformativeness(object):

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
                word_idf = WordInformativeness._idf(word, doc_list)
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
        num_word_doc = WordInformativeness._n_containing(word, doc_list)
        return math.log(1 + float(num_doc) / num_word_doc)


def compute_idf():
    dataset = 'acl'
    # dataset = 'genes-cancer'
    # dataset = 'RiMG75'
    data_dir = 'data/{}/raw'.format(dataset)
    model_file = 'data/{}/idf.pkl'.format(dataset)

    wi = WordInformativeness()
    model = wi.generate_model(data_dir)
    wi.save_model(model, model_file)


def generate_ignored_words():
    logger = logging.getLogger()

    informativeness_threshold = 1.0
    dataset_1 = 'genes-cancer'
    dataset_2 = 'acl'

    f_out = codecs.open('data/{}/ignored_words.txt'.format(dataset_1), 'w', encoding='utf-8')

    wi = WordInformativeness()
    model_1 = wi.load_model('data/{}/idf.pkl'.format(dataset_1))
    model_2 = wi.load_model('data/{}/idf.pkl'.format(dataset_2))
    for word in model_1:
        if word in model_2:
            informativeness = (model_1[word] - model_2[word]) ** 2
            logger.debug(u'Informativeness of {}: {}'.format(word, informativeness))
            if informativeness < informativeness_threshold:
                logger.debug(u'Ignored: {}'.format(word))
                f_out.write(u'{}\n'.format(word))
    f_out.close()


if __name__ == '__main__':
    with open('config/logging_config.yaml') as f:
        logging.config.dictConfig(yaml.load(f))

    # compute_idf()
    generate_ignored_words()
