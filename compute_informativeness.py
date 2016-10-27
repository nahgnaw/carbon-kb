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
        self.model = {}
        self._doc_num = 0
        self._stopwords = set(nltk.corpus.stopwords.words('english')) if stopwords is None else stopwords
        self.logger = logger if logger else logging.getLogger()

    def generate_model(self, data_dir):
        self.logger.info('Generating model ...')
        for root, _, files in os.walk(data_dir):
            for fn in files:
                if fn.endswith('.txt'):
                    self._doc_num += 1
                    doc = set()
                    filename = os.path.join(root, fn)
                    self.logger.info('Processing file {}'.format(filename))
                    f_in = codecs.open(filename, encoding='utf-8')
                    text = f_in.read()
                    # Remove carriage returns, punctuations and digits
                    # regex = re.compile('\- |[%s\d\n]' % re.escape(string.punctuation))
                    # text = regex.sub(' ', text)
                    # Lemmatize
                    blob = TextBlob(text.lower())
                    for word, tag in blob.tags:
                        if word not in self._stopwords and len(word) > 2:
                            if tag.startswith('VB'):
                                w = word.lemmatize('v')
                            elif tag.startswith('JJ') or tag.startswith('RB'):
                                w = word.lemmatize('a')
                            else:
                                w = word.lemmatize()
                            if w not in self.model:
                                # 'tf': term frequency, 'df': document frequency
                                self.model[w] = {'tf': 1, 'df': 0}
                            else:
                                self.model[w]['tf'] += 1
                            doc.add(w)
                    for w in doc:
                        self.model[w]['df'] += 1

        self.logger.info('Computing idf ...')
        for word in self.model:
            idf = math.log(1 + float(self._doc_num) / self.model[word]['df'])
            self.model[word]['idf'] = idf
            self.logger.debug(u'IDF ({}): {}'.format(word, str(idf)))
            x_i = self.model[word]['tf'] - self.model[word]['df']
            self.model[word]['x^I'] = x_i
            self.logger.debug(u'x^I ({}): {}'.format(word, str(x_i)))

    def save_model(self, filename):
        with open(filename, 'w') as model_file:
            cPickle.dump(self.model, model_file)
        self.logger.info('Model saved at {}'.format(filename))

    def load_model(self, filename):
        with open(filename) as model_file:
            model = cPickle.load(model_file)
            self.logger.info('Model loaded from {}'.format(filename))
        return model


def compute_idf():
    logger = logging.getLogger()

    # dataset = 'acl'
    # dataset = 'pmc_mini'
    # dataset = 'RiMG75'
    dataset = 'test'
    data_dir = 'data/{}/raw'.format(dataset)
    model_file = 'data/{}/idf.pkl'.format(dataset)

    wi = WordInformativeness(logger)
    wi.generate_model(data_dir)
    wi.save_model(model_file)


# def generate_ignored_words():
#     logger = logging.getLogger()
#
#     informativeness_threshold = 1.0
#     dataset_1 = 'genes-cancer'
#     dataset_2 = 'acl'
#
#     f_out = codecs.open('data/{}/ignored_words.txt'.format(dataset_1), 'w', encoding='utf-8')
#
#     wi = WordInformativeness()
#     model_1 = wi.load_model('data/{}/idf.pkl'.format(dataset_1))
#     model_2 = wi.load_model('data/{}/idf.pkl'.format(dataset_2))
#     for word in model_1:
#         if word in model_2:
#             informativeness = (model_1[word] - model_2[word]) ** 2
#             logger.debug(u'Informativeness of {}: {}'.format(word, informativeness))
#             if informativeness < informativeness_threshold:
#                 logger.debug(u'Ignored: {}'.format(word))
#                 f_out.write(u'{}\n'.format(word))
#     f_out.close()


if __name__ == '__main__':
    with open('config/logging_config.yaml') as f:
        logging.config.dictConfig(yaml.load(f))

    compute_idf()
    # generate_ignored_words()
