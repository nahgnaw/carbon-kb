# -*- coding: utf8 -*-

import json
import jsonrpclib
import nltk


class WordUnit(object):

    def __init__(self, index, word, lemma, pos):
        self._index = index
        self._word = word
        self._lemma = lemma
        self. _pos = pos

    def __str__(self):
        return self._word

    def __repr__(self):
        return self._word

    def __eq__(self, other):
        return self._index == other._index

    @property
    def index(self):
        return self._index

    @property
    def word(self):
        return self._word

    @property
    def lemma(self):
        return self._lemma

    @property
    def pos(self):
        return self._pos

    def more_info(self):
        return '({})'.format(' '.join([str(self._index), self._word, self._pos]))


class WordUnitSequence(object):

    def __init__(self, word_unit_list=None, head=None):
        if word_unit_list:
            if not type(word_unit_list) is list:
                word_unit_list = [word_unit_list]
            self._seq = word_unit_list
            self._sort()
        else:
            self._seq = []
        self._head = head if head else None

    def __str__(self):
        return ' '.join([wn.word for wn in self._seq])

    def __nonzero__(self):
        return len(self._seq)

    def __len__(self):
        return len(self._seq)

    def __getitem__(self, i):
        return self._seq[i]

    def __iter__(self):
        for ind, wn in enumerate(self._seq):
            yield ind, wn

    def _sort(self):
        if self._seq:
            self._seq = sorted(self._seq, key=lambda wn: wn.index)

    def lemmatized(self):
        return ' '.join(wn.lemma for wn in self._seq)

    def extend(self, seq):
        if seq:
            if type(seq) is list:
                self._seq.extend(seq)
            else:
                self._seq.extend(seq.sequence)
            self._sort()

    def add_word_unit(self, word_unit):
        if word_unit:
            self._seq.append(word_unit)
            self._sort()

    @property
    def sequence(self):
        return self._seq

    @property
    def head(self):
        return self._head

    @head.setter
    def head(self, head):
        self._head = head


class DependencyGraph(object):

    def __init__(self, sentence, parser_server_url=None):
        self._sentence = sentence
        self._raw = {}
        self._tree = {}
        self._words = []
        self._lemmas = []
        self._tags = []
        self._tagged_text = None
        self._dep_triples = []

        if not parser_server_url:
            parser_server_url = 'http://localhost:8080'

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
            print t[0].more_info(), t[1], t[2].more_info()

    def print_raw(self):
        print json.dumps(self._raw, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    sentence = 'The article is reviewed by Tom.'
    dg = DependencyGraph(sentence)
    dg.print_dep_triples()
