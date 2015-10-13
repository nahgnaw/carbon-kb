# -*- coding: utf8 -*-

from nltk.tokenize import sent_tokenize
from dependency_graph import DependencyGraph


class RelationExtractor(object):

    _dependencies = {
        'nsubj': 'nsubj',
        'nsubjpass': 'nsubjpass',
        'dobj': 'dobj',
        'cop': 'cop',
        'auxpass': 'auxpass',
        'nn': 'nn',
        'vmod': 'vmod',
        'prep': 'prep',
        'pobj': 'pobj',
        'conj:and': 'conj:and'
    }

    _pos_tags = {
        'nn': 'NN',
        'vb': 'VB',
        'jj': 'JJ',
        'wdt': 'WDT'
    }

    def __init__(self, sentence, debug=False):
        self.__sentence = sentence
        self.__dep_triple_dict = {}
        self.__make_dep_triple_dict(debug)
        self.__relations = []

    def __make_dep_triple_dict(self, debug):
        dg = DependencyGraph(self.__sentence)
        triples = dg.dep_triples
        if debug:
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

    def __get_conjunctions(self, head_index):
        conjunctions = []
        conj_list = self.__get_dependents(self._dependencies['conj:and'], head_index)
        for conj in conj_list:
            nn = self.__get_noun_compound(conj['index'])
            if nn:
                conjunctions.append(self.__concatenate([nn, conj['word']]))
            else:
                conjunctions.append(conj['word'])
        return conjunctions

    def __get_pobj_phrase(self, head_index):
        pobj_phrases = []
        prep_list = self.__get_dependents(self._dependencies['prep'], head_index)
        if prep_list:
            for prep in prep_list:
                obj_list = self.__get_dependents(self._dependencies['pobj'], prep['index'])
                if obj_list:
                    for o in obj_list:
                        if not o['pos'] == self._pos_tags['wdt']:
                            obj = self.__get_object(o)
                            pobj_phrases.append(self.__concatenate([prep['word'], obj]))
        return pobj_phrases

    def __get_subject(self, subj_dict):
        subj_index = subj_dict['index']
        subj = subj_dict['word']
        # If the subject is a compound noun, use the noun compound
        subj_nn = self.__get_noun_compound(subj_index)
        if subj_nn:
            subj = self.__concatenate([subj_nn, subj])
        # Find out if the subject has conjunctions
        subj_conj = self.__get_conjunctions(subj_index)
        if subj_conj:
            subj = self.__concatenate([subj, ' '.join(subj_conj)], ' & ')
        return subj

    def __get_object(self, obj_dict):
        obj_index = obj_dict['index']
        obj = obj_dict['word']
        # if the object is a compound noun, use the noun compound
        obj_nn = self.__get_noun_compound(obj_index)
        if obj_nn:
            obj = self.__concatenate([obj_nn, obj])
        # Find out if the object has prepositional object
        obj_pobj_phrases = self.__get_pobj_phrase(obj_index)
        if obj_pobj_phrases:
            obj = self.__concatenate([obj, obj_pobj_phrases[0]])
        # Find out if the object has conjunctions
        obj_conj = self.__get_conjunctions(obj_index)
        if obj_conj:
            obj = self.__concatenate([obj, ' '.join(obj_conj)], ' & ')
        # Find out if the object has vmod
        vmod_list = self.__get_dependents(self._dependencies['vmod'], obj_index)
        if vmod_list:
            vmod_phrases = []
            for vmod in vmod_list:
                pobj_phrases = self.__get_pobj_phrase(vmod['index'])
                if pobj_phrases:
                    for pobj_phrase in pobj_phrases:
                        vmod_phrases.append(self.__concatenate([vmod['word'], pobj_phrase]))
                dobj_list = self.__get_dependents(self._dependencies['dobj'], vmod['index'])
                if dobj_list:
                    for dobj in dobj_list:
                        vmod_phrases.append(self.__concatenate([vmod['word'], dobj['word']]))
            if vmod_phrases:
                vmod_phrases = '(' + self.__concatenate(vmod_phrases) + ')'
                obj = self.__concatenate([obj, vmod_phrases])
        return obj

    def extract_nsubj(self):
        if self._dependencies['nsubj'] in self.__dep_triple_dict:
            for triple in self.__dep_triple_dict['nsubj']:
                # The subject is the dependent
                subj = self.__get_subject(triple['dependent'])
                # If the dependency relation is a verb:
                if triple['head']['pos'].startswith(self._pos_tags['vb']):
                    # The predicate is the head
                    pred_index = triple['head']['index']
                    pred = triple['head']['word']
                    # Object for 'dobj'
                    obj_list = self.__get_dependents(self._dependencies['dobj'], pred_index)
                    if obj_list:
                        for o in obj_list:
                            obj = self.__get_object(o)
                            self.__relations.append((subj, pred, obj))
                    # If there is no direct objects, look for prepositional objects
                    else:
                        pobj_phrases = self.__get_pobj_phrase(pred_index)
                        if pobj_phrases:
                            for pp in pobj_phrases:
                                self.__relations.append((subj, pred, pp))
                    # TODO: 'iobj' (is it necessary?)
                # if the dependency relation is a copular verb:
                elif triple['head']['pos'].startswith(self._pos_tags['nn']) \
                        or triple['head']['pos'].startswith(self._pos_tags['jj']):
                    # The object is the head
                    obj_index = triple['head']['index']
                    obj = self.__get_object(triple['head'])
                    # Predicate
                    pred_list = self.__get_dependents(self._dependencies['cop'], obj_index)
                    if pred_list:
                        for p in pred_list:
                            pred = p['word']
                            self.__relations.append((subj, pred, obj))

    def extract_nsubjpass(self):
        if self._dependencies['nsubjpass'] in self.__dep_triple_dict:
            for triple in self.__dep_triple_dict['nsubjpass']:
                # The subject is the dependent
                subj = self.__get_subject(triple['dependent'])
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
                                    obj = self.__get_object(o)
                                    self.__relations.append((subj, pred, obj))
                    else:
                        obj = vbn
                        self.__relations.append((subj, pred, obj))

    # TODO: pattern: has the ability to ...

    @property
    def relations(self):
        return self.__relations


if __name__ == '__main__':
    sentences = u"""
       Predicted structures of stable high-pressure phases of MgCO3: a) post-magnesite phase II; b) phase III; c) Pna21-20 structure.
    """

    for sent in sent_tokenize(sentences):
        sent = sent.strip()
        print sent
        extractor = RelationExtractor(sent, debug=True)
        extractor.extract_nsubj()
        extractor.extract_nsubjpass()
        print extractor.relations
