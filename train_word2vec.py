# -*- coding: utf8 -*-

import os
import codecs
import logging
import logging.config
import yaml

from gensim.models import Word2Vec, Phrases


class MySentences(object):
    def __init__(self, dirname):
        self.dirname = dirname

    def __iter__(self):
        for root, _, files in os.walk(self.dirname):
            for fn in files:
                if fn.endswith('.txt'):
                    filename = os.path.join(root, fn)
                    f = codecs.open(filename, encoding='utf-8')
                    for line in f.readlines():
                        if line:
                            line = line.strip()
                            if line:
                                yield line.split()


with open('config/logging_config.yaml') as f:
    logging.config.dictConfig(yaml.load(f))
logger = logging.getLogger()

corpus_path = 'data/pmc_c-h/processed_done'
model_path = 'data/pmc_c-h/embeddings/word2vec'
sentences = MySentences(corpus_path)
# bigrams = Phrases(sentences, min_count=1)
# trigrams = Phrases(bigrams[sentences], min_count=1)
model = Word2Vec(sentences, size=200, workers=4, sg=1, hs=0, negative=5, min_count=1)
model.save_word2vec_format(model_path, binary=True)
