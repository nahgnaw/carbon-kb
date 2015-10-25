# -*- coding: utf8 -*-

import os
import codecs
import traceback

from nltk.tokenize import sent_tokenize
from dependency_graph import WordUnitSequence, DependencyGraph


class Relation(object):

    def __init__(self, subj=None, pred=None, obj=None):
        self.__subj = subj
        self.__pred = pred
        self.__obj = obj

    def __str__(self):
        return str((str(self.__subj), str(self.__pred), str(self.__obj)))

    def lemmatized(self):
        return self.__subj.lemmatized(), self.__pred.lemmatized(), self.__obj.lemmatized()

    @property
    def subject(self):
        return self.__subj

    @subject.setter
    def subject(self, subj):
        self.__subj = subj

    @property
    def predicate(self):
        return self.__pred

    @predicate.setter
    def predicate(self, pred):
        self.__pred = pred

    @property
    def object(self):
        return self.__obj

    @object.setter
    def object(self, obj):
        self.__obj = obj


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
        'conj:and': 'conj:and',
        'cc': 'cc',
        'aux': 'aux'
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
                    'head': triple[0],
                    'dependent': triple[2]
                })

    @staticmethod
    def __concatenate(words, separator=' '):
        return separator.join(words)

    def __get_dependents(self, dependency_relation, head, dependent=None):
        dependents = []
        if dependency_relation in self.__dep_triple_dict:
            if dependent:
                dependents = [t['dependent'] for t in self.__dep_triple_dict[dependency_relation]
                              if head.index == t['head'].index and dependent.word == t['dependent'].word]
            else:
                dependents = [t['dependent']
                              for t in self.__dep_triple_dict[dependency_relation] if head.index == t['head'].index]
        return dependents

    # Return: a WordUnitSequence. Each element is a component of the noun compound.
    def __get_noun_compound(self, head):
        nn = self.__get_dependents(self._dependencies['nn'], head)
        if nn:
            nn.append(head)
            return WordUnitSequence(nn)
        return WordUnitSequence(head)

    # Return: a WordUnitSequence including the conjunctions of noun compounds of the head.
    def __get_conjunctions(self, head):
        conjunctions = WordUnitSequence()
        conj_list = self.__get_dependents(self._dependencies['conj:and'], head)
        if conj_list:
            for conj in conj_list:
                conjunctions.extend(self.__get_noun_compound(conj))
        cc_list = self.__get_dependents(self._dependencies['cc'], head)
        if cc_list:
            for cc in cc_list:
                conjunctions.add_word_unit(cc)
        return conjunctions

    # Return: a WordUnitSequence including the prepositional object phrase of the head.
    def __get_pobj_phrase(self, head):
        pobj_phrase = WordUnitSequence()
        prep_list = self.__get_dependents(self._dependencies['prep'], head)
        if prep_list:
            for prep in prep_list:
                obj_list = self.__get_dependents(self._dependencies['pobj'], prep)
                if obj_list:
                    for obj in obj_list:
                        if not obj.pos == self._pos_tags['wdt']:
                            obj_seq = self.__expand_head(obj)
                            obj_seq.add_word_unit(prep)
                            pobj_phrase.extend(obj_seq)
        return pobj_phrase

    def __get_vmod_phrase(self, head):
        vmod_phrase = WordUnitSequence()
        vmod_list = self.__get_dependents(self._dependencies['vmod'], head)
        if vmod_list:
            for vmod in vmod_list:
                vmod_phrase.add_word_unit(vmod)
                aux_list = self.__get_dependents(self._dependencies['aux'], vmod)
                if aux_list:
                    for aux in aux_list:
                        vmod_phrase.add_word_unit(aux)
                pobj_phrase = self.__get_pobj_phrase(vmod)
                if pobj_phrase:
                    vmod_phrase.extend(pobj_phrase)
                dobj_list = self.__get_dependents(self._dependencies['dobj'], vmod)
                if dobj_list:
                    for dobj in dobj_list:
                        obj_seq = self.__expand_head(dobj)
                        vmod_phrase.extend(obj_seq)
        return vmod_phrase

    # Return: a WordUnitSequence.
    def __expand_head(self, head):
        # Find out if the head is in a compound noun
        expanded_head = self.__get_noun_compound(head)
        # Find out if the head has pobj phrase
        pobj_phrase = self.__get_pobj_phrase(head)
        if pobj_phrase:
            expanded_head.extend(pobj_phrase)
        # Find out if the head has vmod phrase
        vmod_phrase = self.__get_vmod_phrase(head)
        if vmod_phrase:
            expanded_head.extend(vmod_phrase)
        # Find out if the head has conjunctions
        conj = self.__get_conjunctions(head)
        if conj:
            expanded_head.extend(conj)
        return expanded_head

    def extract_nsubj(self):
        if self._dependencies['nsubj'] in self.__dep_triple_dict:
            for triple in self.__dep_triple_dict['nsubj']:
                head = triple['head']
                dependent = triple['dependent']
                relation = Relation()
                # The subject is the dependent
                relation.subject = self.__expand_head(dependent)
                # If the dependency relation is a verb:
                if head.pos.startswith(self._pos_tags['vb']):
                    # The predicate is the head
                    pred = head
                    relation.predicate = WordUnitSequence([pred])
                    # Object for 'dobj'
                    obj_list = self.__get_dependents(self._dependencies['dobj'], pred)
                    if obj_list:
                        for o in obj_list:
                            obj = self.__expand_head(o)
                            relation.object = obj
                            self.relations.append(relation)
                    # If there is no direct objects, look for prepositional objects
                    else:
                        pobj_phrase = self.__get_pobj_phrase(pred)
                        if pobj_phrase:
                            relation.object = pobj_phrase
                            self.relations.append(relation)
                    # TODO: 'iobj' (is it necessary?)
                    # TODO: 'xcomp'  e.g. The objective of this chapter is to review the mineralogy and crystal chemistry of carbon.
                # if the dependency relation is a copular verb:
                elif head.pos.startswith(self._pos_tags['nn']) or head.pos.startswith(self._pos_tags['jj']):
                    # The object is the head
                    obj = head
                    relation.object = self.__expand_head(obj)
                    # Predicate
                    pred_list = self.__get_dependents(self._dependencies['cop'], obj)
                    if pred_list:
                        for pred in pred_list:
                            relation.predicate = WordUnitSequence([pred])
                            self.__relations.append(relation)

    def extract_nsubjpass(self):
        if self._dependencies['nsubjpass'] in self.__dep_triple_dict:
            for triple in self.__dep_triple_dict['nsubjpass']:
                head = triple['head']
                dependent = triple['dependent']
                relation = Relation()
                # The subject is the dependent
                relation.subject = self.__expand_head(dependent)
                vbn = head
                pred_list = self.__get_dependents(self._dependencies['auxpass'], vbn)
                if pred_list:
                    for pred in pred_list:
                        relation.predicate = WordUnitSequence([pred])
                        relation.object = WordUnitSequence([vbn])
                        pobj_phrase = self.__get_pobj_phrase(vbn)
                        if pobj_phrase:
                            relation.object.extend(pobj_phrase)
                        self.__relations.append(relation)

    @property
    def relations(self):
        return self.__relations


def batch_test():
    data_dir = 'data/RiMG75/tmp/'
    for root, _, files in os.walk(data_dir):
        for fn in files:
            if fn.endswith('.txt'):
                filename = os.path.join(root, fn)
                output_filename = os.path.join(root, fn + '.relations')
                f_in = codecs.open(filename, encoding='utf-8')
                f_out = codecs.open(output_filename, 'w', encoding='utf-8')
                for line in f_in:
                    sent = line.strip()
                    f_out.write(u'{}\n'.format(sent))
                    try:
                        extractor = RelationExtractor(sent, debug=False)
                    except:
                        print 'Failed to parse the sentence.'
                        print(traceback.format_exc())
                    else:
                        extractor.extract_nsubj()
                        extractor.extract_nsubjpass()
                        for relation in extractor.relations:
                            print sent
                            print relation
                            f_out.write(u'{}\n'.format(relation))
                        f_out.write('\n')
                f_in.close()
                f_out.close()


def test():
    sentences = u"""
       This versatile element concentrates in dozens of different Earth repositories, from the atmosphere and oceans to the crust, mantle, and core, including solids, liquids, and gases as both a major and trace element .
    """
    for sent in sent_tokenize(sentences):
        sent = sent.strip()
        print sent
        try:
            extractor = RelationExtractor(sent, debug=True)
        except:
            print 'Failed to parse the sentence.'
            print(traceback.format_exc())
        else:
            extractor.extract_nsubj()
            extractor.extract_nsubjpass()
            for relation in extractor.relations:
                print relation


if __name__ == '__main__':
    test()
    # batch_test()
