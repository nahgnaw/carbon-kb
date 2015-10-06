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
        'vmod': u'vmod',
        'prep': u'prep',
        'pobj': u'pobj'
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
        # dg.print_dep_triples()
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

    @staticmethod
    def __concatenate(words, separator=' '):
        return separator.join(words)

    def __get_dependents(self, dependency, head_index, dependent=None):
        dependents = []
        if dependency in self.__dep_triple_dict:
            if dependent:
                dependents = [t['dependent'] for t in self.__dep_triple_dict[dependency]
                              if head_index == t['head']['index'] and dependent == t['dependent']['word']]
            else:
                dependents = [t['dependent']
                              for t in self.__dep_triple_dict[dependency] if head_index == t['head']['index']]
        return dependents

    def __get_noun_compound(self, head_index):
        nn = ''
        nn_list = self.__get_dependents(self._dependencies['nn'], head_index)
        if nn_list:
            nn = ' '.join([nn['word'] for nn in sorted(nn_list, key=lambda e: e['index'])])
        return nn

    # Extract nsubj dependencies
    def extract_nsubj(self):
        if self._dependencies['nsubj'] in self.__dep_triple_dict:
            for triple in self.__dep_triple_dict['nsubj']:
                # The subject is the dependent
                subj_index = triple['dependent']['index']
                subj = triple['dependent']['word']
                # If the subject is a compound noun, use the noun compound
                subj_nn = self.__get_noun_compound(subj_index)
                if subj_nn:
                    subj = self.__concatenate([subj_nn, subj])
                # If the dependency relation is a verb:
                if triple['head']['pos'].startswith(self._pos_tags['vb']):
                    # The predicate is the head
                    pred_index = triple['head']['index']
                    pred = triple['head']['word']
                    # Object for 'dobj'
                    obj_list = self.__get_dependents(self._dependencies['dobj'], pred_index)
                    if obj_list:
                        for o in obj_list:
                            obj = o['word']
                            # if the object is a compound noun, use the noun compound
                            obj_nn = self.__get_noun_compound(o['index'])
                            if obj_nn:
                                obj = self.__concatenate([obj_nn, obj])
                            self.__relations.append((subj, pred, obj))
                    # TODO: 'iobj' (is it necessary?)
                # if the dependency relation is a copular verb:
                elif triple['head']['pos'].startswith(self._pos_tags['nn']) \
                        or triple['head']['pos'].startswith(self._pos_tags['jj']):
                    # The object is the head
                    obj_index = triple['head']['index']
                    obj = triple['head']['word']
                    # if the object is a compound noun, use the noun compound
                    obj_nn = self.__get_noun_compound(obj_index)
                    if obj_nn:
                        obj = self.__concatenate([obj_nn, obj])
                    # Predicate
                    pred_list = self.__get_dependents(self._dependencies['cop'], obj_index)
                    if pred_list:
                        for p in pred_list:
                            pred = p['word']
                            self.__relations.append((subj, pred, obj))

    # Extract nsubjpass dependencies
    def extract_nsubjpass(self):
        if self._dependencies['nsubjpass'] in self.__dep_triple_dict:
            for triple in self.__dep_triple_dict['nsubjpass']:
                # The subject is the dependent
                subj_index = triple['dependent']['index']
                subj = triple['dependent']['word']
                # If the subject is a compound noun, use the noun compound
                subj_nn = self.__get_noun_compound(subj_index)
                if subj_nn:
                    subj = subj_nn + ' ' + subj
                # If there is a "by" following the VBN, VBN + "by" should be the predicate, and
                # the pobj of "by" should be the object
                vbn_index = triple['head']['index']
                vbn = triple['head']['word']
                pred_list = self.__get_dependents(self._dependencies['auxpass'], vbn_index)
                if pred_list:
                    pred = pred_list[0]['word']
                    pobj_list = self.__get_dependents(self._dependencies['prep'], vbn_index, 'by')
                    if pobj_list:
                        for p in pobj_list:
                            pred = self.__concatenate([pred, vbn, 'by'])
                            obj_list = self.__get_dependents(self._dependencies['pobj'], p['index'])
                            if obj_list:
                                for o in obj_list:
                                    obj = o['word']
                                    self.__relations.append((subj, pred, obj))
                    else:
                        obj = vbn
                        self.__relations.append((subj, pred, obj))

    @property
    def relations(self):
        return self.__relations


sentences = u"""
    Carbon, element 6, displays remarkable chemical flexibility and thus is unique in the diversity of its mineralogical roles.
    Carbon has the ability to bond to itself and to more than 80 other elements in a variety of bonding topologies, most commonly in 2-, 3-, and 4-coordination.
    With oxidation numbers ranging from -4 to +4, carbon is observed to behave as a cation, as an anion, and as a neutral species in phases with an astonishing range of crystal structures, chemical bonding, and physical and chemical properties.
    This versatile element concentrates in dozens of different Earth repositories, from the atmosphere and oceans to the crust, mantle, and core, including solids, liquids, and gases as both a major and trace element (Holland 1984; Berner 2004; Hazen et al. 2012).
    Therefore, any comprehensive survey of carbon in Earth must consider the broad range of carbon-bearing phases.
    """

for sentence in sent_tokenize(sentences):
    sentence = sentence.strip()
    print sentence
    extractor = RelationExtractor(sentence)
    extractor.extract_nsubj()
    extractor.extract_nsubjpass()
    print extractor.relations
