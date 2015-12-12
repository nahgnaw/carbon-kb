# -*- coding: utf8 -*-

import json

import jsonrpclib
import nltk

from word_unit import WordUnit


class DependencyGraph(object):

    def __init__(self, sentence, logger, parser_server_url=None):
        self._sentence = sentence
        self._raw = {}
        self._tree = {}
        self._words = []
        self._lemmas = []
        self._tags = []
        self._tagged_text = None
        self._dep_triples = []
        self.logger = logger

        if not parser_server_url:
            parser_server_url = 'http://localhost:8084'

        parser = jsonrpclib.Server(parser_server_url)
        self._raw = json.loads(parser.parse(self._sentence))
        self._tree = self._raw['sentences'][0]
        if self._tree:
            self._parse_tree()

    def _parse_tree(self):
        dependencies = []
        for dep in self._dependencies():
            dependencies.append(dep)
        dependencies = sorted(dependencies)
        words = self._tree['words']
        tagged_text = []
        for dep in dependencies:
            index = dep[0]
            word = dep[1]
            lemma = dep[2]
            pos = dep[3]
            head_index = int(dep[4])
            head_word = words[head_index - 1][0]
            head_lemma = words[head_index - 1][1]['Lemma']
            head_pos = words[head_index - 1][1]['PartOfSpeech']
            rel = dep[5]
            self._words.append(word)
            self._lemmas.append(lemma)
            self._tags.append(pos)
            tagged_text.append(nltk.tree.Tree(pos, [word]))
            if not rel == 'root':
                head = WordUnit(head_index, head_word, head_lemma, head_pos)
                dependent = WordUnit(index, word, lemma, pos)
                triple = (head, rel, dependent)
                self._dep_triples.append(triple)
        self._tagged_text = nltk.tree.Tree('S', tagged_text)

    def _dependencies(self):
        for rel, _, head, word, index in self._tree['dependencies']:
            index = int(index)
            word_info = self._tree['words'][index - 1][1]
            pos = word_info['PartOfSpeech']
            lemma = word_info['Lemma']
            yield index, word, lemma, pos, head, rel

    @property
    def dep_triples(self):
        return self._dep_triples

    @property
    def text(self):
        return self._words

    @property
    def raw(self):
        return self._raw

    @property
    def lemmas(self):
        return self._lemmas

    @property
    def tags(self):
        return self._tags

    @property
    def tagged_text(self):
        return self._tagged_text

    def print_dep_triples(self):
        for t in self._dep_triples:
            self.logger.debug('{} {} {}'.format(t[0].more_info(), t[1], t[2].more_info()))

    def print_raw(self):
        self.logger.debug(json.dumps(self._raw, ensure_ascii=False, indent=4))


if __name__ == '__main__':
    sentence = u'we found that treating 6-week-old RT2 mice with EGFR inhibitors (erlotinib or CI-1033) for 3 weeks resulted in a ~30% decrease in the number of islets undergoing angiogenic switching (), indicating that Egfr activity also contributes to this pathological transition.'
    dg = DependencyGraph(sentence)
    dg.print_dep_triples()
