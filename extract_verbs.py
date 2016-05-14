# -*- coding: utf8 -*-

import unicodecsv
import codecs
import yaml
import logging
import logging.config

from collections import Counter
from nltk import pos_tag
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from segtok.segmenter import split_multi


class VerbExtractor(object):

    bloom_verbs = {
        # Remember previously learned information.
        'knowledge': ['arrange', 'define', 'describe', 'duplicate', 'identify', 'label', 'list', 'match', 'memorize',
                     'name', 'order', 'outline', 'recognize', 'relate', 'recall', 'repeat', 'reproduce', 'select',
                     'state', 'tell', 'underline'],
        # Demonstrate an understanding of the facts.
        'comprehension': ['classify', 'compare', 'convert', 'defend', 'describe', 'discuss', 'distinguish', 'estimate',
                          'explain', 'express', 'extend', 'generalized', 'give example', 'identify', 'indicate',
                          'infer', 'locate', 'paraphrase', 'predict', 'recognize', 'restate', 'rewrite', 'review',
                          'select', 'summarize', 'tell', 'translate'],
        # Apply knowledge to actual situations.
        'application': ['apply', 'change', 'choose', 'complete', 'compute', 'construct', 'demonstrate', 'discover',
                        'dramatize', 'employ', 'illustrate', 'interpret', 'manipulate', 'modify', 'operate', 'practice',
                        'predict', 'prepare', 'produce', 'relate', 'schedule', 'show', 'sketch', 'solve', 'use',
                        'write'],
        # Break down objects or ideas into simpler parts and find evidence to support generalizations.
        'analysis': ['analyze', 'appraise', 'breakdown', 'calculate', 'categorize', 'compare', 'contrast', 'criticize',
                     'debate', 'diagram', 'differentiate', 'discriminate', 'distinguish', 'examine', 'experiment',
                     'identify', 'illustrate', 'infer', 'inspect', 'inventory', 'model', 'outline', 'point out',
                     'question', 'relate', 'select', 'separate', 'subdivide', 'test'],
        # Compile component ideas into a new whole or propose alternative solutions.
        'synthesis': ['arrange', 'assemble', 'categorize', 'collect', 'combine', 'comply', 'compose', 'construct',
                      'create', 'design', 'develop', 'devise', 'explain', 'formulate', 'manage', 'generate', 'organize',
                      'plan', 'prepare', 'propose', 'rearrange', 'reconstruct', 'relate', 'reorganize', 'revise',
                      'rewrite', 'setup', 'set up', 'summarize', 'synthesize', 'tell', 'write'],
        # Make and defend judgments based on internal evidence or external criteria.
        'evaluation': ['appraise', 'argue', 'assess', 'attach', 'choose', 'compare', 'conclude', 'contrast', 'defend',
                       'describe', 'discriminate', 'estimate', 'evaluate', 'explain', 'interpret', 'judge', 'justify',
                       'measure', 'relate', 'predict', 'rate', 'revise', 'score', 'select', 'summarize', 'support',
                       'value']
    }

    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self._invert_dict()
        self.logger = logging.getLogger()

    def _invert_dict(self):
        self.inverted_bv = {}
        for category in self.bloom_verbs:
            for verb in self.bloom_verbs[category]:
                self.inverted_bv.setdefault(verb, []).append(category)

    def extract(self, sentence):
        results = []
        self.logger.debug(u'SENTENCE: {}'.format(sentence))
        tokens = word_tokenize(sentence.lower())
        tokens_pos = pos_tag(tokens)
        for token in tokens_pos:
            if token[1].startswith('VB'):
                lemma = self.lemmatizer.lemmatize(token[0], pos='v')
                if lemma in self.inverted_bv:
                    for category in self.inverted_bv[lemma]:
                        results.append((lemma, category))
        self.logger.debug(u'VERBS: {}'.format(results))
        return results


def extract_from_csv():
    verb_category_mapping = {
        'knowledge': 2, 'comprehension': 3, 'application': 4,
        'analysis': 5, 'synthesis': 6, 'evaluation': 7
    }

    input_file_path = 'data/gdot/learning-outcome/learning_outcome.csv'
    output_file_path = '{}_verbs.csv'.format(input_file_path.split('.')[0])
    f_in = open(input_file_path)
    f_out = open(output_file_path, 'w')
    reader = unicodecsv.reader(f_in, encoding='utf-8')
    writer = unicodecsv.writer(f_out, encoding='utf-8')

    extractor = VerbExtractor()
    for row in reader:
        course = row[0].strip()
        level = row[1].strip()
        text = ' '.join([cell.strip() for cell in row[2:]])
        verbs = extractor.extract(text)
        if verbs:
            output_row = [[] for _ in xrange(8)]
            output_row[0], output_row[1] = course, level
            for verb, category in verbs:
                output_row[verb_category_mapping[category]].append(verb)
            for i in xrange(len(output_row)):
                if i > 1:
                    counter = Counter(output_row[i])
                    output_row[i] = ','.join([u'{}({})'.format(w, c) for w, c in counter.items()])
            writer.writerow(output_row)

    f_in.close()
    f_out.close()


def extract_from_txt():
    extractor = VerbExtractor()
    input_file_path = 'data/gdot/forum/mtle_4150_forum_2.txt'
    f_in = codecs.open(input_file_path, encoding='utf-8')
    text = f_in.read()
    results = {}
    for sent in split_multi(text):
        verbs = extractor.extract(sent.lower())
        if verbs:
            for verb, category in verbs:
                results.setdefault(category, []).append(verb)
    f_in.close()

    output_file_path = '{}_verbs.txt'.format(input_file_path.split('.')[0])
    f_out = codecs.open(output_file_path, mode='w', encoding='utf-8')
    for category in results:
        counter = Counter(results[category])
        output_str = [u'{}({})'.format(item[0], str(item[1])) for item in counter.items()]
        f_out.write(u'{}: {}\n'.format(category, ', '.join(output_str)))
    f_out.close()


def test():
    text = 'Describe their personal strengths, value, and priorities in order to pursue appropriate and desirable career pathways.'
    extractor = VerbExtractor()
    print extractor.extract(text)


if __name__ == '__main__':
    with open('config/logging_config.yaml') as f:
        logging.config.dictConfig(yaml.load(f))

    # test()
    extract_from_csv()
    # extract_from_txt()
