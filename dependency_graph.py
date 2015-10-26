# -*- coding: utf8 -*-

import json
import jsonrpclib
import nltk


class WordUnit(object):

    def __init__(self, index, word, lemma, pos):
        self.__index = index
        self.__word = word
        self.__lemma = lemma
        self. __pos = pos

    def __str__(self):
        return self.__word

    @property
    def index(self):
        return self.__index

    @property
    def word(self):
        return self.__word

    @property
    def lemma(self):
        return self.__lemma

    @property
    def pos(self):
        return self.__pos

    def more_info(self):
        return '({})'.format(' '.join([str(self.__index), self.__word, self.__pos]))


class WordUnitSequence(object):

    def __init__(self, word_unit_list=None, head=None):
        if word_unit_list:
            if not type(word_unit_list) is list:
                word_unit_list = [word_unit_list]
            self.__seq = word_unit_list
            self.__sort()
        else:
            self.__seq = []
        if head:
            self.__head = head

    def __str__(self):
        return ' '.join([wn.word for wn in self.__seq])

    def __nonzero__(self):
        return len(self.__seq)

    def __len__(self):
        return len(self.__seq)

    def __sort(self):
        if self.__seq:
            self.__seq = sorted(self.__seq, key=lambda wn: wn.index)

    def lemmatized(self):
        return ' '.join(wn.lemma for wn in self.__seq)

    def extend(self, seq):
        if type(seq) is list:
            self.__seq.extend(seq)
        else:
            self.__seq.extend(seq.sequence)
        self.__sort()

    def add_word_unit(self, word_unit):
        self.__seq.append(word_unit)
        self.__sort()

    def print_lemma(self):
        print ' '.join([wn.lemma for wn in self.__seq])

    @property
    def sequence(self):
        return self.__seq

    @property
    def head(self):
        return self.__head

    @head.setter
    def head(self, head):
        self.__head = head


class DependencyGraph(object):

    def __init__(self, sentence, parser_server_url=None):
        self.__sentence = sentence
        self.__raw = {}
        self.__tree = {}
        self.__words = []
        self.__lemmas = []
        self.__tags = []
        self.__tagged_text = None
        self.__dep_triples = []

        if not parser_server_url:
            parser_server_url = 'http://localhost:8080'

        parser = jsonrpclib.Server(parser_server_url)
        self.__raw = json.loads(parser.parse(self.__sentence))
        self.__tree = self.__raw['sentences'][0]
        if self.__tree:
            self.__parse_tree()

    def __parse_tree(self):
        dependencies = []
        for dep in self.__dependencies():
            dependencies.append(dep)
        dependencies = sorted(dependencies)
        words = self.__tree['words']
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
            self.__words.append(word)
            self.__lemmas.append(lemma)
            self.__tags.append(pos)
            tagged_text.append(nltk.tree.Tree(pos, [word]))
            if not rel == 'root':
                head = WordUnit(head_index, head_word, head_lemma, head_pos)
                dependent = WordUnit(index, word, lemma, pos)
                triple = (head, rel, dependent)
                self.__dep_triples.append(triple)
        self.__tagged_text = nltk.tree.Tree('S', tagged_text)

    def __dependencies(self):
        for rel, _, head, word, index in self.__tree['dependencies']:
            index = int(index)
            word_info = self.__tree['words'][index - 1][1]
            pos = word_info['PartOfSpeech']
            lemma = word_info['Lemma']
            yield index, word, lemma, pos, head, rel

    @property
    def dep_triples(self):
        return self.__dep_triples

    @property
    def text(self):
        return self.__words

    @property
    def raw(self):
        return self.__raw

    @property
    def lemmas(self):
        return self.__lemmas

    @property
    def tags(self):
        return self.__tags

    @property
    def tagged_text(self):
        return self.__tagged_text

    def print_dep_triples(self):
        for t in self.__dep_triples:
            print t[0].more_info(), t[1], t[2].more_info()

    def print_raw(self):
        print json.dumps(self.__raw, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    sentence = 'The article is reviewed by Tom.'
    dg = DependencyGraph(sentence)
    dg.print_dep_triples()
