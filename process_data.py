# -*- coding: utf8 -*-

import os
import codecs
from nltk.tokenize import sent_tokenize


class Sentences(object):

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
                        line = self.text_process(line)
                        for sent in sent_tokenize(line):
                            yield fn, sent
                f.close()

    def save(self, dir):
        # First empty dir
        filelist = [f for f in os.listdir(dir)]
        for f in filelist:
            os.remove(os.path.join(dir, f))
        for fn, sent in self.__iter__():
            print fn, sent.encode('utf-8')
            file_path = os.path.join(dir, fn)
            f = codecs.open(file_path, 'a', encoding='utf-8')
            f.write(u'{}\n'.format(sent))
            f.close()

    @staticmethod
    def text_process(line):
        # TODO: remove reference and http in the parentheses
        return line

if __name__ == '__main__':
    RAW_TEXT_DIR = './data/RiMG75/raw'
    sents = Sentences(RAW_TEXT_DIR)
    sents.save('./data/RiMG75/processed')
