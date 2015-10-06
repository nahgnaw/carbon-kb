# -*- coding: utf8 -*-

from nltk.tokenize import sent_tokenize
from dependency_graph import DependencyGraph


class RelationExtractor(object):

    _dependencies = {
        'nsubj': u'nsubj',
        'nsubjpass': u'nsubjpass',
        'dobj': u'dobj',
        'cop': u'cop',
        'auxpass': u'auxpass',
        'nn': u'nn',
        'vmod': u'vmod'
    }

    _pos_tags = {
        'nn': u'NN',
        'vb': u'VB',
        'jj': u'JJ'
    }

    def __init__(self, sentence):
        self.__sentence = sentence
        self.__dep_triple_dict = {}
        self.__make_dep_triple_dict()
        self.__relations = []

    def __make_dep_triple_dict(self):
        dg = DependencyGraph(self.__sentence)
        triples = dg.dep_triples
        dg.print_dep_triples()
        for triple in triples:
            dep = triple[1]
            if dep in self._dependencies.values():
                if dep not in self.__dep_triple_dict:
                    self.__dep_triple_dict[dep] = []
                self.__dep_triple_dict[dep].append({
                    'head': {
                        'index': triple[0][0],
                        'word': triple[0][1],
                        'pos': triple[0][2]
                    },
                    'dependent': {
                        'index': triple[2][0],
                        'word': triple[2][1],
                        'pos': triple[2][2]
                    }
                })

    def __get_dependents(self, dependency, head_index):
        dependents = []
        if dependency in self.__dep_triple_dict:
            dependents = [t['dependent']
                          for t in self.__dep_triple_dict[dependency] if head_index == t['head']['index']]
        return dependents

    def __get_noun_compound(self, head_index):
        nn = ''
        nn_list = self.__get_dependents('nn', head_index)
        if nn_list:
            nn = ' '.join([nn['word'] for nn in sorted(nn_list, key=lambda e: e['index'])])
        return nn

    # Extract nsubj dependencies
    def extract_nsubj(self):
        if 'nsubj' in self.__dep_triple_dict:
            for triple in self.__dep_triple_dict['nsubj']:
                subj_index = triple['dependent']['index']
                subj = triple['dependent']['word']
                # If the subject is a compound noun, use the noun compound
                subj_nn = self.__get_noun_compound(subj_index)
                if subj_nn:
                    subj = subj_nn + ' ' + subj
                # If the dependency relation is a verb:
                if triple['head']['pos'].startswith(self._pos_tags['vb']):
                    # Predicate
                    pred_index = triple['head']['index']
                    pred = triple['head']['word']
                    # Object for 'dobj'
                    obj_list = self.__get_dependents('dobj', pred_index)
                    if obj_list:
                        for o in obj_list:
                            obj = o['word']
                            # if the object is a compound noun, use the noun compound
                            obj_nn = self.__get_noun_compound(o['index'])
                            if obj_nn:
                                obj = obj_nn + ' ' + obj
                            self.__relations.append((subj, pred, obj))
                    # TODO: 'iobj' (is it necessary?)
                # if the dependency relation is a copular verb:
                elif triple['head']['pos'].startswith(self._pos_tags['nn']) \
                        or triple['head']['pos'].startswith(self._pos_tags['jj']):
                    # Object
                    obj_index = triple['head']['index']
                    obj = triple['head']['word']
                    # if the object is a compound noun, use the noun compound
                    obj_nn = self.__get_noun_compound(obj_index)
                    if obj_nn:
                        obj = obj_nn + ' ' + obj
                    # Predicate
                    pred_list = self.__get_dependents('cop', obj_index)
                    if pred_list:
                        for p in pred_list:
                            pred = p['word']
                            self.__relations.append((subj, pred, obj))

    # # Extract nsubjpass dependencies
    # def extract_nsubjpass(self):
    #     if 'nsubjpass'

    @property
    def relations(self):
        return self.__relations

    #     elif triple[1] == NSUBJPASS:
    #         if triple[0][2].startswith(VB):
    #             subj_index, subj = triple[2][0:2]
    #             subj_nn_tuples = dg.get_dependent_by_head_relation(subj_index, NNMOD)
    #             subj = ' '.join([nn[1] for nn in sorted(subj_nn_tuples, key=lambda t: t[0])]) + ' ' + subj
    #             obj_index, obj = triple[0][0:2]
    #             obj_nn_tuples = dg.get_dependent_by_head_relation(obj_index, NNMOD)
    #             obj = ' '.join([nn[1] for nn in sorted(obj_nn_tuples, key=lambda t: t[0])]) + ' ' + obj
    #             pred_tuples = dg.get_dependent_by_head_relation(obj_index, AUXPASS)
    #             for pred in pred_tuples:
    #                 relations.append((subj, pred, obj, sentence))

sentences = u"""
       Gold carbon is noun silver when in action.
    """

for sentence in sent_tokenize(sentences):
    sentence = sentence.strip()
    extractor = RelationExtractor(sentence)
    extractor.extract_nsubj()
    print extractor.relations
