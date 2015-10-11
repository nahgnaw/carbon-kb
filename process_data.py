# -*- coding: utf8 -*-

import os
import re
import codecs
import nltk.data
from nltk.tokenize import sent_tokenize


class Sentences(object):

    def __init__(self, raw_data_dir):
        self.raw_data_dir = raw_data_dir
        self.sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')

    def __iter__(self):
        for root, _, files in os.walk(self.raw_data_dir):
            for fn in files:
                filename = os.path.join(root, fn)
                f = codecs.open(filename, encoding='utf-8')
                for line in f:
                    line = line.strip()
                    if line:
                        line = self.text_process(line)
                        for sent in self.sent_detector.tokenize(line):
                            yield fn, sent
                f.close()

    def save(self, dir, debug=False):
        # First empty dir
        file_list = [f for f in os.listdir(dir)]
        for f in file_list:
            os.remove(os.path.join(dir, f))
        for fn, sent in self.__iter__():
            if debug:
                print fn, sent.encode('utf-8')
            file_path = os.path.join(dir, fn)
            f = codecs.open(file_path, 'a', encoding='utf-8')
            f.write(u'{}\n'.format(sent))
            f.close()

    @staticmethod
    def text_process(line):
        replacement = [
            r'(([A-Z]\S+)+(\sand\s)?([A-Z]\S+)?\s(et al.)?,?\s*\d{4}[;|,]*)',   # Citations
            r'(([A-Z]\S+)+(\sand\s)?([A-Z]\S+)?\s(et al.)?,?\s*\(\d{4}\)[;|,]*)',   # Citations
            r'([\(|\[]http://.*[\)|\]])',   # http
            r'(Figure \d{1,3}\.)',  # Figure caption
            r'(Table \d{1,3}\.)'    # Table caption
        ]
        replacement_pattern = re.compile('|'.join(replacement), re.UNICODE)
        line = re.sub(replacement_pattern, '', line)

        # Remove empty parenthesis
        empty_parentheses = r'(\(\s*\))'
        empty_parenthesis_pattern = re.compile(empty_parentheses, re.UNICODE)
        line = re.sub(empty_parenthesis_pattern, '', line)

        return line

if __name__ == '__main__':
    RAW_TEXT_DIR = './data/RiMG75/raw'
    sents = Sentences(RAW_TEXT_DIR)
    sents.save('./data/RiMG75/processed', debug=True)
