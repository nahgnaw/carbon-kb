# -*- coding: utf8 -*-

import json
import jsonrpclib
import nltk


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
            word = dep[1]
            lemma = dep[2]
            tag = dep[3]
            head_index = int(dep[4])
            head = words[head_index - 1][0]
            head_tag = words[head_index - 1][1]["PartOfSpeech"]
            rel = dep[5]
            self.__words.append(word)
            self.__lemmas.append(lemma)
            self.__tags.append(tag)
            tagged_text.append(nltk.tree.Tree(tag, [word]))
            if not rel == 'root':
                triple = ((head_index, head, head_tag), rel, (dep[0], dep[1], dep[3]))
                self.__dep_triples.append(triple)
        self.__tagged_text = nltk.tree.Tree('S', tagged_text)

    def __dependencies(self):
        for rel, _, head, word, n in self.__tree['dependencies']:
            n = int(n)
            word_info = self.__tree['words'][n - 1][1]
            tag = word_info['PartOfSpeech']
            lemma = word_info['Lemma']
            yield n, word, lemma, tag, head, rel

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
            print t

    def print_raw(self):
        print json.dumps(self.__raw, ensure_ascii=False, indent=4)
