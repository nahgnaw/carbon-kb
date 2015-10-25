# -*- coding: utf8 -*-

import os
import re
import codecs
import nltk.data


class Sentences(object):

    def __init__(self, raw_data_dir):
        self.raw_data_dir = raw_data_dir
        self.sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')
        extra_abbr = ['dr', 'vs', 'mr', 'mrs', 'prof', 'inc', 'i.e', 'fig', 'p', 'et al', 'e.g', 'etc', 'eq']
        self.sent_detector._params.abbrev_types.update(extra_abbr)

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
            r'(([A-Z]\S+)+(\sand\s)?([A-Z]\S+)?\s(et al.)?,?\s*\d{4}[a-z]?[;|,]*)',   # Citations
            r'(([A-Z]\S+)+(\sand\s)?([A-Z]\S+)?\s(et al.)?,?\s*\(\d{4}[a-z]?\)[;|,]*)',   # Citations
            r'([\(|\[]http://.*[\)|\]])',   # http
            r'(Figure \d{1,3}\.)',  # Figure caption
            r'(Table \d{1,3}\.)',    # Table caption
            r'(\([A-Za-z]\))'   # List item marker
        ]
        replacement_pattern = re.compile('|'.join(replacement), re.UNICODE)
        line = re.sub(replacement_pattern, '', line)

        # Remove empty parenthesis
        empty_parentheses = r'(\(\s*\))'
        empty_parenthesis_pattern = re.compile(empty_parentheses, re.UNICODE)
        line = re.sub(empty_parenthesis_pattern, '', line)

        return line

if __name__ == '__main__':
    dataset = 'RiMG75'
    raw_text_dir = 'data/{}/raw'.format(dataset)
    processed_text_dir = 'data/{}/processed'.format(dataset)
    sents = Sentences(raw_text_dir)
    sents.save(processed_text_dir, debug=True)
