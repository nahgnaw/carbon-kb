# -*- coding: utf8 -*-

import os
import re
import codecs
import logging.config
import yaml
from segtok.segmenter import split_multi


class Sentences(object):

    def __init__(self, dataset, logger):
        self.logger = logger
        self._dataset = dataset
        self._raw_text_dir = 'data/{}/raw'.format(self._dataset)
        self._preprocessed_text_dir = 'data/{}/preprocessed'.format(self._dataset)

    def __iter__(self):
        for root, _, files in os.walk(self._raw_text_dir):
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
                                yield filename, sent
                    f.close()
                    # Move the preprocessed files to a temp directory, so we know which files are done.
                    done_filename = filename.replace('/raw/', '/raw_preprocessed/')
                    if not os.path.exists(os.path.dirname(done_filename)):
                        os.makedirs(os.path.dirname(done_filename))
                    os.rename(filename, done_filename)

    def save(self):

        # # First empty the preprocessed dir
        # file_list = [os.path.join(self._preprocessed_text_dir, d) for d in os.listdir(self._preprocessed_text_dir)
        #              if os.path.isdir(os.path.join(self._preprocessed_text_dir, d))]
        # for d in file_list:
        #     for f in os.listdir(d):
        #         os.remove(os.path.join(d, f))

        for filename, sent in self.__iter__():
            filename = filename.replace('/raw/', '/preprocessed/')
            if not os.path.exists(os.path.dirname(filename)):
                os.makedirs(os.path.dirname(filename))
            self.logger.debug(u'{} {}'.format(filename, sent))
            f = codecs.open(filename, 'a', encoding='utf-8')
            f.write(u'{}\n'.format(sent))
            f.close()

    @staticmethod
    def process_text(text):
        replacement = [
            r'(^\W*\s*)',   # Preceding non-word characters
            r'(\s*\([^()]*\))',    # Parentheses
            r'(\s*\[.*\])',    # Parentheses
            r'(\b(([\w-]+://?|www[.])[^\s()<>]+(?:\([\w\d]+\)|([^[:punct:]\s]|/))))',   # URLs
            r'(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)',  # emails
            r'([A-Za-z0-9]\))',   # List item markers with just one parenthesis
            # r'((Fig\.?u?r?e?\s\d{1,3}\.?))',  # Figure caption
            # r'(Table\.?\s\d{1,3}\.?)',    # Table caption
            # r'(([A-Z]\S+)+(\sand\s)?([A-Z]\S+)?\s(et al.)?,?\s*\d{4}[a-z]?[;|,]*)',   # Citations
            # r'(([A-Z]\S+)+(\sand\s)?([A-Z]\S+)?\s(et al.)?,?\s*\(\d{4}[a-z]?\)[;|,]*)',   # Citations
        ]
        replacement_pattern = re.compile('|'.join(replacement), re.UNICODE | re.IGNORECASE)
        text = re.sub(replacement_pattern, '', text)

        # Replace " ." with "." for sentence segmentation.
        text = text.replace(' .', '.')

        # Some uncommon replacement.
        text = text.replace('.-', '.').replace('.,', '.')

        return text


if __name__ == '__main__':
    with open('config/logging_config.yaml') as f:
        logging.config.dictConfig(yaml.load(f))
    logger = logging.getLogger('preprocess')

    # dataset = 'test'
    # dataset = 'pmc_c-h'
    dataset = 'RiMG75'

    sents = Sentences(dataset, logger)
    sents.save()
