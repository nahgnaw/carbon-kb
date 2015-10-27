# -*- coding: utf8 -*-

import os
import codecs
import traceback

from nltk.tokenize import sent_tokenize
from dependency_graph import WordUnitSequence, DependencyGraph


class Relation(object):

    def __init__(self, subj=None, pred=None, obj=None):
        self._subj = subj
        self._pred = pred
        self._obj = obj

    def __str__(self):
        return str((str(self._subj), str(self._pred), str(self._obj)))

    def lemmatized(self):
        return self._subj.lemmatized(), self._pred.lemmatized(), self._obj.lemmatized()

    @property
    def subject(self):
        return self._subj

    @subject.setter
    def subject(self, subj):
        self._subj = subj

    @property
    def predicate(self):
        return self._pred

    @predicate.setter
    def predicate(self, pred):
        self._pred = pred

    @property
    def object(self):
        return self._obj

    @object.setter
    def object(self, obj):
        self._obj = obj


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
        'conj:or': 'conj:or',
        'cc': 'cc',
        'aux': 'aux',
        'neg': 'neg',
        'xcomp': 'xcomp',
        'ccomp': 'ccomp'
    }

    _pos_tags = {
        'nn': 'NN',
        'vb': 'VB',
        'jj': 'JJ',
        'wdt': 'WDT',
        'dt': 'DT',
        'prp': 'PRP'
    }

    def __init__(self, sentence, debug=False):
        self._sentence = sentence
        self._debug = debug
        self._dep_triple_dict = {}
        self._make_dep_triple_dict()
        self._relations = []

    def _make_dep_triple_dict(self):
        dg = DependencyGraph(self._sentence)
        triples = dg.dep_triples
        if self._debug:
            dg.print_dep_triples()
        for triple in triples:
            dep = triple[1]
            if dep in self._dependencies.values():
                if dep not in self._dep_triple_dict:
                    self._dep_triple_dict[dep] = []
                self._dep_triple_dict[dep].append({
                    'head': triple[0],
                    'dependent': triple[2]
                })

    def _get_dependents(self, dependency_relation, head, dependent=None):
        dependents = []
        if dependency_relation in self._dep_triple_dict:
            if dependent:
                dependents = [t['dependent'] for t in self._dep_triple_dict[dependency_relation]
                              if head.index == t['head'].index and dependent.word == t['dependent'].word]
            else:
                dependents = [t['dependent']
                              for t in self._dep_triple_dict[dependency_relation] if head.index == t['head'].index]
        return dependents

    def _get_noun_compound(self, head):
        nn = self._get_dependents(self._dependencies['nn'], head)
        if nn:
            nn.append(head)
            return WordUnitSequence(nn)
        return WordUnitSequence(head)

    def _get_conjunctions(self, head):
        conjunctions = WordUnitSequence()
        conj_list = self._get_dependents(self._dependencies['conj:and'], head)
        conj_list.extend(self._get_dependents(self._dependencies['conj:or'], head))
        if conj_list:
            for conj in conj_list:
                conjunctions.extend(self._get_noun_compound(conj))
        cc_list = self._get_dependents(self._dependencies['cc'], head)
        if cc_list:
            for cc in cc_list:
                conjunctions.add_word_unit(cc)
        return conjunctions

    def _get_pobj_phrase(self, head):
        pobj_phrase = WordUnitSequence()
        prep_list = self._get_dependents(self._dependencies['prep'], head)
        if prep_list:
            for prep in prep_list:
                obj_list = self._get_dependents(self._dependencies['pobj'], prep)
                if obj_list:
                    for obj in obj_list:
                        if not obj.pos == self._pos_tags['wdt']:
                            obj_seq = self._expand_head_word(obj)
                            obj_seq.add_word_unit(prep)
                            pobj_phrase.extend(obj_seq)
        return pobj_phrase

    def _get_vmod_phrase(self, head):
        vmod_phrase = WordUnitSequence()
        vmod_list = self._get_dependents(self._dependencies['vmod'], head)
        if vmod_list:
            for vmod in vmod_list:
                vmod_phrase.add_word_unit(vmod)
                aux_list = self._get_dependents(self._dependencies['aux'], vmod)
                if aux_list:
                    for aux in aux_list:
                        vmod_phrase.add_word_unit(aux)
                pobj_phrase = self._get_pobj_phrase(vmod)
                if pobj_phrase:
                    vmod_phrase.extend(pobj_phrase)
                dobj_list = self._get_dependents(self._dependencies['dobj'], vmod)
                if dobj_list:
                    for dobj in dobj_list:
                        obj_seq = self._expand_head_word(dobj)
                        vmod_phrase.extend(obj_seq)
        return vmod_phrase

    def _expand_head_word(self, head):
        # Find out if the head is in a compound noun
        expansion = self._get_noun_compound(head)
        # Find out if there is any negation
        neg = self._get_dependents(self._dependencies['neg'], head)
        if neg and neg[0].pos == self._pos_tags['dt']:
            expansion.add_word_unit(neg[0])
            if self._debug:
                print '[DEBUG] "{}" head expansion with negation: "{}"'.format(head, neg)
        # Find out if the head has pobj phrase
        pobj_phrase = self._get_pobj_phrase(head)
        if pobj_phrase:
            expansion.extend(pobj_phrase)
            if self._debug:
                print '[DEBUG] "{}" head expansion with pobj phrase: "{}"'.format(head, pobj_phrase)
        # Find out if the head has vmod phrase
        vmod_phrase = self._get_vmod_phrase(head)
        if vmod_phrase:
            expansion.extend(vmod_phrase)
            if self._debug:
                print '[DEBUG] "{}" head expansion with vmod phrase: "{}"'.format(head, vmod_phrase)
        # Find out if the head has conjunctions
        conj = self._get_conjunctions(head)
        if conj:
            expansion.extend(conj)
            if self._debug:
                print '[DEBUG] "{}" head expansion with conjunction: "{}"'.format(head, conj)
        return expansion

    # Expand predicate with auxiliary and negation
    def _expand_predicate(self, pred, aux_head=None, neg_head=None):
        predicate = WordUnitSequence(word_unit_list=[pred], head=pred)
        if aux_head:
            # Find out if there is any aux
            aux = self._get_dependents(self._dependencies['aux'], aux_head)
            if aux:
                predicate.add_word_unit(aux[0])
                if self._debug:
                    print '[DEBUG] "{}" predicate expansion with auxiliary: "{}"'.format(pred, aux)
        if neg_head:
            # Find out if there is any negation
            neg = self._get_dependents(self._dependencies['neg'], neg_head)
            if neg:
                predicate.add_word_unit(neg[0])
                if self._debug:
                    print '[DEBUG] "{}" predicate expansion with negation: "{}"'.format(pred, neg)
        # Find out if there is any xcomp
        xcomp_list = self._get_dependents(self._dependencies['xcomp'], pred)
        if xcomp_list:
            for xcomp in xcomp_list:
                predicate.add_word_unit(xcomp)
                # Use the xcomp as the "head" instead of the original head
                predicate.head = xcomp
                if self._debug:
                    print '[DEBUG] "{}" predicate expansion with xcomp: "{}"'.format(pred, xcomp)
                aux = self._get_dependents(self._dependencies['aux'], xcomp)
                if aux:
                    predicate.add_word_unit(aux[0])
        return predicate

    def extract_nsubj(self):
        if self._dependencies['nsubj'] in self._dep_triple_dict:
            for triple in self._dep_triple_dict['nsubj']:
                head = triple['head']
                dependent = triple['dependent']
                # PRP and WDT cannot be subject for now
                if dependent.pos not in [self._pos_tags['prp'], self._pos_tags['wdt']]:
                    relation = Relation()
                    # The subject is the dependent
                    relation.subject = self._expand_head_word(dependent)
                    # If the dependency relation is a verb:
                    if head.pos.startswith(self._pos_tags['vb']):
                        # The predicate is the head
                        pred = head
                        relation.predicate = self._expand_predicate(pred, pred, head)
                        pred = relation.predicate.head
                        # Object for 'dobj'
                        obj_list = self._get_dependents(self._dependencies['dobj'], pred)
                        if obj_list:
                            for o in obj_list:
                                obj = self._expand_head_word(o)
                                relation.object = obj
                                self.relations.append(relation)
                        # If there is no direct objects, look for prepositional objects
                        else:
                            pobj_phrase = self._get_pobj_phrase(pred)
                            if pobj_phrase:
                                relation.predicate.add_word_unit(pobj_phrase[0])
                                relation.object = WordUnitSequence(pobj_phrase[1:])
                                self.relations.append(relation)
                    # if the dependency relation is a copular verb:
                    elif head.pos.startswith(self._pos_tags['nn']) or head.pos.startswith(self._pos_tags['jj']):
                        # The object is the head
                        obj = head
                        relation.object = self._expand_head_word(obj)
                        # Predicate
                        pred_list = self._get_dependents(self._dependencies['cop'], obj)
                        if pred_list:
                            for pred in pred_list:
                                relation.predicate = self._expand_predicate(pred, head, head)
                                self._relations.append(relation)

    def extract_nsubjpass(self):
        if self._dependencies['nsubjpass'] in self._dep_triple_dict:
            for triple in self._dep_triple_dict['nsubjpass']:
                head = triple['head']
                dependent = triple['dependent']
                relation = Relation()
                # The subject is the dependent
                relation.subject = self._expand_head_word(dependent)
                vbn = head
                pred_list = self._get_dependents(self._dependencies['auxpass'], vbn)
                if pred_list:
                    for pred in pred_list:
                        relation.predicate = self._expand_predicate(pred, head, head)
                        relation.predicate.add_word_unit(vbn)
                        pobj_phrase = self._get_pobj_phrase(vbn)
                        if pobj_phrase:
                            relation.predicate.add_word_unit(pobj_phrase[0])
                            relation.object = WordUnitSequence(pobj_phrase[1:])
                            self._relations.append(relation)

    @property
    def relations(self):
        return self._relations


def batch_test():
    dataset = 'genes-cancer'
    data_dir = 'data/{}/tmp/'.format(dataset)
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
      It was unclear what muscle function is maintained in these cancer cells.
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
