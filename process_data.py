# -*- coding: utf8 -*-

import os
import codecs
from nltk.tokenize import sent_tokenize


class CarbonSentences(object):

    def __init__(self, raw_data_dir):
        self. raw_data_dir = raw_data_dir

    def __iter__(self):
        for root, _, files in os.walk(self.raw_data_dir):
            for fn in files:
                filename = os.path.join(root, fn)
                f = codecs.open(filename, encoding='utf-8')
                for line in f:
                    line = line.strip()
                    if line:
                        for sent in sent_tokenize(line):
                            sent = self.process(sent)
                            yield sent
                f.close()

    def save(self, dir):
        f = codecs.open(dir, 'w', encoding='utf-8')
        for sent in self.__iter__():
            f.write(u'{}\n'.format(sent))

    @staticmethod
    def process(sent):
        sent = sent.lower()
        return sent

if __name__ == '__main__':
    RAW_TEXT_DIR = './data/'
    sentences = CarbonSentences(RAW_TEXT_DIR)
    for s in sentences:
        print s.encode('utf-8')
