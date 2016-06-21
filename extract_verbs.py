# -*- coding: utf8 -*-

import os
import unicodecsv
import codecs
import logging
import begin

from collections import Counter
from nltk import pos_tag
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from segtok.segmenter import split_multi


class VerbExtractor(object):

    # Old version
    # bloom_verbs = {
    #     # Remember previously learned information.
    #     'knowledge': ['arrange', 'define', 'describe', 'duplicate', 'identify', 'label', 'list', 'match', 'memorize',
    #                  'name', 'order', 'outline', 'recognize', 'relate', 'recall', 'repeat', 'reproduce', 'select',
    #                  'state', 'tell', 'underline'],
    #     # Demonstrate an understanding of the facts.
    #     'comprehension': ['classify', 'compare', 'convert', 'defend', 'describe', 'discuss', 'distinguish', 'estimate',
    #                       'explain', 'express', 'extend', 'generalized', 'give example', 'identify', 'indicate',
    #                       'infer', 'locate', 'paraphrase', 'predict', 'recognize', 'restate', 'rewrite', 'review',
    #                       'select', 'summarize', 'tell', 'translate'],
    #     # Apply knowledge to actual situations.
    #     'application': ['apply', 'change', 'choose', 'complete', 'compute', 'construct', 'demonstrate', 'discover',
    #                     'dramatize', 'employ', 'illustrate', 'interpret', 'manipulate', 'modify', 'operate', 'practice',
    #                     'predict', 'prepare', 'produce', 'relate', 'schedule', 'show', 'sketch', 'solve', 'use',
    #                     'write'],
    #     # Break down objects or ideas into simpler parts and find evidence to support generalizations.
    #     'analysis': ['analyze', 'appraise', 'breakdown', 'calculate', 'categorize', 'compare', 'contrast', 'criticize',
    #                  'debate', 'diagram', 'differentiate', 'discriminate', 'distinguish', 'examine', 'experiment',
    #                  'identify', 'illustrate', 'infer', 'inspect', 'inventory', 'model', 'outline', 'point out',
    #                  'question', 'relate', 'select', 'separate', 'subdivide', 'test'],
    #     # Compile component ideas into a new whole or propose alternative solutions.
    #     'synthesis': ['arrange', 'assemble', 'categorize', 'collect', 'combine', 'comply', 'compose', 'construct',
    #                   'create', 'design', 'develop', 'devise', 'explain', 'formulate', 'manage', 'generate', 'organize',
    #                   'plan', 'prepare', 'propose', 'rearrange', 'reconstruct', 'relate', 'reorganize', 'revise',
    #                   'rewrite', 'setup', 'set up', 'summarize', 'synthesize', 'tell', 'write'],
    #     # Make and defend judgments based on internal evidence or external criteria.
    #     'evaluation': ['appraise', 'argue', 'assess', 'attach', 'choose', 'compare', 'conclude', 'contrast', 'defend',
    #                    'describe', 'discriminate', 'estimate', 'evaluate', 'explain', 'interpret', 'judge', 'justify',
    #                    'measure', 'relate', 'predict', 'rate', 'revise', 'score', 'select', 'summarize', 'support',
    #                    'value']
    # }

    # New version.
    # http://www.celt.iastate.edu/teaching/effective-teaching-practices/revised-blooms-taxonomy
    # http://www.personal.psu.edu/bxb11/Objectives/ActionVerbsforObjectives.pdf
    bloom_verbs = {
        # Exhibit memory of previously learned material by recalling facts, terms, basic concepts, and answers.
        'remember': ['define', 'describe', 'duplicate', 'find', 'identify', 'label', 'list', 'locate', 'memorize',
                     'name', 'recall', 'recognize', 'record', 'relate', 'remember', 'repeat', 'reproduce', 'retrieve',
                     'search', 'underline'],
        # Demonstrate understanding of facts and ideas by organizing, comparing, translating, interpreting, giving
        # descriptions, and stating main ideas.
        'understand': ['abstract', 'choose', 'clarify', 'compare', 'contrast', 'describe', 'determine', 'exemplify',
                       'explain', 'express', 'give examples', 'identify', 'illustrate', 'indicate', 'instantiate',
                       'interpret', 'map', 'match', 'organize', 'paraphrase', 'pick', 'recognize', 'report', 'restate',
                       'review', 'rewrite', 'state', 'select', 'show', 'tell', 'translate', 'respond', 'represent',
                       'simulate', 'summarize', 'understand'],
        # Solve problems to new situations by applying acquired knowledge, facts, techniques and rules in a different
        # way.
        'apply': ['apply', 'change', 'demonstrate', 'calculate', 'complete', 'compute', 'convert', 'employ', 'execute',
                  'implement', 'modify', 'operate', 'practice', 'prepare', 'show', 'solve', 'use', 'utilize', 'write'],
        # Examine and break information into parts by identifying motives or causes. Make inferences and find evidence
        # to support generalizations.
        'analyze': ['analyze', 'attribute', 'categorize', 'classify', 'conclude', 'correlate', 'debate', 'deduce',
                    'detect', 'determine', 'diagnose', 'differentiate', 'discover', 'discriminate', 'discuss',
                    'distinguish', 'estimate', 'examine', 'extend', 'generalize', 'identify', 'infer', 'inspect',
                    'integrate', 'outline', 'parse', 'predict', 'relate', 'select', 'separate', 'show', 'subsume'],
        # Present and defend opinions by making judgments about information, validity of ideas, or quality of work based
        # on a set of criteria.
        'evaluate': ['appraise', 'argue', 'assess', 'critique', 'criticize', 'defend', 'evaluate', 'judge', 'justify',
                     'measure', 'rate', 'revise', 'score', 'support', 'validate', 'value', 'test'],
        # Compile information together in a different way by combining elements in a new pattern or proposing
        # alternative solutions.
        'create': ['arrange', 'assemble', 'collect', 'combine', 'compose', 'construct', 'create', 'design', 'develop',
                   'devise', 'formulate', 'generate', 'plan', 'produce', 'propose', 'rearrange', 'reconstruct',
                   'reorganize', 'revise', 'rewrite', 'set up', 'synthesize', 'systematize']
    }

    bloom_verb_categories = ['remember', 'understand', 'apply', 'analyze', 'evaluate', 'create']

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


@begin.subcommand
def extract_from_csv(input_file_path):
    verb_category_mapping = {
        'remember': 2, 'understand': 3, 'apply': 4,
        'analyze': 5, 'evaluate': 6, 'create': 7
    }

    extractor = VerbExtractor()

    output_file_path = '{}_verbs.csv'.format(input_file_path.split('.')[0])
    f_in = open(input_file_path)
    f_out = open(output_file_path, 'w')
    reader = unicodecsv.reader(f_in, encoding='utf-8')
    writer = unicodecsv.writer(f_out, encoding='utf-8')
    writer.writerow(['dept', 'level'] + extractor.bloom_verb_categories)

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


@begin.subcommand
def extract_from_txt(input_dir):
    if not input_dir.endswith('/'):
        input_dir += '/'

    file_dir = input_dir + 'processed/'
    output_dir = input_dir + 'verbs/'
    if not os.path.exists(os.path.dirname(output_dir)):
        os.makedirs(os.path.dirname(output_dir))

    extractor = VerbExtractor()
    for root, _, files in os.walk(file_dir):
        for fn in files:
            if fn.endswith('.txt'):
                filename = os.path.join(root, fn)
                logging.info('Reading {}'.format(filename))
                f_in = codecs.open(filename, encoding='utf-8')
                text = f_in.read()
                results = {}
                for sent in split_multi(text):
                    verbs = extractor.extract(sent.lower())
                    if verbs:
                        for verb, category in verbs:
                            results.setdefault(category, []).append(verb)
                f_in.close()
                output_file = filename.replace('processed', 'verbs').replace('.txt', '_verbs.txt')
                logging.info('Writing to {}'.format(output_file))
                f_out = codecs.open(output_file, mode='w', encoding='utf-8')
                for category in extractor.bloom_verb_categories:
                    counter = Counter(results[category])
                    output_str = [u'{}({})'.format(item[0], str(item[1])) for item in counter.items()]
                    f_out.write(u'{}: {}\n'.format(category, ', '.join(output_str)))
                f_out.close()


def test():
    text = 'Describe their personal strengths, value, and priorities in order to pursue appropriate and desirable career pathways.'
    extractor = VerbExtractor()
    print extractor.extract(text)


@begin.start
@begin.logging
def run():
    pass
