# -*- coding: utf8 -*-

import os
import codecs
import traceback
import MySQLdb

from relation import Relation
from ConfigParser import SafeConfigParser
from segtok.segmenter import split_multi
from dependency_graph import WordUnitSequence, DependencyGraph


class RelationExtractor(object):

    _dependencies = {
        'acomp': 'acomp',
        'aux': 'aux',
        'auxpass': 'auxpass',
        'cc': 'cc',
        'ccomp': 'ccomp',
        'conj:and': 'conj:and',
        'conj:or': 'conj:or',
        'cop': 'cop',
        'dobj': 'dobj',
        'neg': 'neg',
        'nn': 'nn',
        'nsubj': 'nsubj',
        'nsubjpass': 'nsubjpass',
        'num': 'num',
        'pcomp': 'pcomp',
        'pobj': 'pobj',
        'prep': 'prep',
        'vmod': 'vmod',
        'xcomp': 'xcomp',
    }

    _pos_tags = {
        'dt': 'DT',
        'nn': 'NN',
        'jj': 'JJ',
        'jjr': 'JJR',
        'jjs': 'JJS',
        'prp': 'PRP',
        'vb': 'VB',
        'wdt': 'WDT',
        'wp': 'WP',
    }

    _subject_pos_blacklist = [
        _pos_tags['wdt'], _pos_tags['dt'], _pos_tags['prp'],
        _pos_tags['jj'], _pos_tags['jjr'], _pos_tags['jjs'],
        _pos_tags['wp']
    ]

    _conjunction_dependencies = [
            _dependencies['conj:and'],
            _dependencies['conj:or']
        ]

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

    @property
    def relations(self):
        return self._relations

    def generate_relation_sql(self, relation, table_name='svo'):
        return u"""
            INSERT INTO {} (subject, predicate, object, sentence)
            VALUES ("{}", "{}", "{}", "{}");
        """.format(table_name, relation.subject, relation.predicate, relation.object, self._sentence)

    @staticmethod
    def _print_expansion_debug_info(head_word, dep, added):
        print '[DEBUG] "{}" expanded with {}: "{}"'.format(head_word, dep, added)

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

    def _get_conjunction(self, head):
        conjunction = [head]
        for dep in self._conjunction_dependencies:
            conjunction.extend(self._get_dependents(dep, head))
        return conjunction

    def _get_noun_compound(self, head):
        nn = self._get_dependents(self._dependencies['nn'], head)
        if nn:
            nn.append(head)
            return WordUnitSequence(nn)
        return WordUnitSequence(head)

    def _get_num_modifier(self, head):
        num_mod = WordUnitSequence()
        num_list = self._get_dependents(self._dependencies['num'], head)
        if num_list:
            for num in num_list:
                num_mod.add_word_unit(num)
                if self._debug:
                    self._print_expansion_debug_info(head, 'numeric modifier', num)
        return num_mod

    def _get_neg_modifier(self, head):
        neg_mod = WordUnitSequence()
        neg_list = self._get_dependents(self._dependencies['neg'], head)
        if neg_list and neg_list[0].pos == self._pos_tags['dt']:
            neg_mod.add_word_unit(neg_list[0])
            if self._debug:
                self._print_expansion_debug_info(head, 'negation', neg_list[0])
        return neg_mod

    def _get_prep_phrase(self, head):
        prep_phrase = WordUnitSequence()
        prep_list = self._get_dependents(self._dependencies['prep'], head)
        if prep_list:
            for prep in prep_list:
                # Ignore those prepositions that are far away from the head
                if abs(prep.index - head.index) < 2:
                    # Look for pobj
                    obj_list = self._get_dependents(self._dependencies['pobj'], prep)
                    if obj_list:
                        for obj in obj_list:
                            if not obj.pos == self._pos_tags['wdt']:
                                obj_seq = self._expand_head_word(obj)
                                obj_seq.add_word_unit(prep)
                                prep_phrase.extend(obj_seq)
                    # Look for pcomp
                    pcomp_list = self._get_dependents(self._dependencies['pcomp'], prep)
                    if pcomp_list:
                        for pcomp in pcomp_list:
                            prep_phrase.add_word_unit(prep)
                            for seq in self._get_predicate_object(pcomp):
                                prep_phrase.extend(seq)
                    if self._debug:
                        self._print_expansion_debug_info(head, 'prep phrase', prep_phrase)
        return prep_phrase

    def _get_vmod_phrase(self, head):
        vmod_phrase = WordUnitSequence()
        vmod_list = self._get_dependents(self._dependencies['vmod'], head)
        if vmod_list:
            for vmod in vmod_list:
                for seq in self._get_predicate_object(vmod):
                    vmod_phrase.extend(seq)
            if self._debug:
                self._print_expansion_debug_info(head, 'vmod', vmod_phrase)
        return vmod_phrase

    def _get_predicate_object(self, pred_head):
        predicate = self._expand_predicate(pred_head)
        object = WordUnitSequence()
        for ind, pred in predicate:
            pred_seq = WordUnitSequence()
            # Look for direct object
            obj_list = self._get_dependents(self._dependencies['dobj'], pred)
            if obj_list:
                for obj in obj_list:
                    obj_conjunction = self._get_conjunction(obj)
                    for o in obj_conjunction:
                        object.extend(self._expand_head_word(o))
            # Look for adjective compliment
            acomp_list = self._get_dependents(self._dependencies['acomp'], pred)
            if acomp_list:
                for acomp in acomp_list:
                    object.add_word_unit(acomp)
                    acomp_prep_phrase = self._get_prep_phrase(acomp)
                    object.extend(acomp_prep_phrase)
            # Look for prepositional objects
            prep_phrase = self._get_prep_phrase(pred)
            if len(prep_phrase) > 1:
                pred_seq.add_word_unit(prep_phrase[0])
                object.extend(WordUnitSequence(prep_phrase[1:]))

            if object:
                # If there are multiple predicate words that have objects, only take the first one.
                if pred_seq:
                    predicate = WordUnitSequence(predicate[:ind+1])
                    predicate.extend(pred_seq)
                return predicate, object
        return predicate, None

    def _expand_head_word(self, head):
        """
            Return a WordUnitSequence including the original head.
        """

        def _clean(word_unit_seq):
            # If the sequence is a single letter, ignore it
            if len(word_unit_seq) == 1 and len(word_unit_seq[0]) == 1:
                word_unit_seq = None
            return word_unit_seq

        # Find out if the head is in a compound noun
        expansion = self._get_noun_compound(head)
        # Find out if there is any numeric modifier
        num_mod = self._get_num_modifier(head)
        expansion.extend(num_mod)
        # Find out if there is any negation
        neg_mod = self._get_neg_modifier(head)
        expansion.extend(neg_mod)
        # Find out if the head has pobj phrase
        pobj_phrase = self._get_prep_phrase(head)
        expansion.extend(pobj_phrase)
        # Find out if the head has vmod phrase
        vmod_phrase = self._get_vmod_phrase(head)
        expansion.extend(vmod_phrase)
        # Cleaning
        expansion = _clean(expansion)
        return expansion

    def _expand_predicate(self, head):
        """
            Return a WordUnitSequence including the original head.
        """
        predicate = WordUnitSequence(head)

        def __expand_predicate(pred_head, debug=False):
            predicate = WordUnitSequence()
            dep_list = [
                self._dependencies['aux'],
                self._dependencies['auxpass'],
                self._dependencies['neg']
            ]
            for dep in dep_list:
                dep_wn = self._get_dependents(dep, pred_head)
                if dep_wn:
                    predicate.add_word_unit(dep_wn[0])
                    if debug:
                        self._print_expansion_debug_info(pred_head, dep, dep_wn[0])
            return predicate

        # Find out if there is any aux, auxpass, and neg
        predicate.extend(__expand_predicate(head, self._debug))
        # Find out if there is any xcomp
        xcomp_list = self._get_dependents(self._dependencies['xcomp'], head)
        if xcomp_list:
            for xcomp in xcomp_list:
                predicate.add_word_unit(xcomp)
                if self._debug:
                    self._print_expansion_debug_info(head, 'xcomp', xcomp)
                predicate.extend(__expand_predicate(xcomp, self._debug))
        return predicate

    def _extracting_condition(self, head, dependent):
        return head.word.isalpha() and dependent.word.isalpha() and dependent.pos not in self._subject_pos_blacklist

    def extract_svo(self):
        dependencies = [self._dependencies['nsubj'], self._dependencies['nsubjpass']]
        for dep in dependencies:
            if dep in self._dep_triple_dict:
                self._extract_svo(dep)

    def _extract_svo(self, dependency):
        for triple in self._dep_triple_dict[dependency]:
            head = triple['head']
            dependent = triple['dependent']
            if not self._extracting_condition(head, dependent):
                continue
            head_conjunction = self._get_conjunction(head)
            dependent_conjunction = self._get_conjunction(dependent)
            for dependent in dependent_conjunction:
                # The subject is the dependent
                subject = self._expand_head_word(dependent)
                if subject:
                    for head in head_conjunction:
                        # If the dependency relation is a verb:
                        if head.pos.startswith(self._pos_tags['vb']):
                            # The predicate is the head
                            predicate, object = self._get_predicate_object(head)
                        elif head.pos.startswith(self._pos_tags['nn']):
                            pred_list = self._get_dependents(self._dependencies['cop'], head)
                            if pred_list:
                                predicate = self._expand_predicate(pred_list[0])
                                object = self._expand_head_word(head)
                            else:
                                continue
                        elif head.pos.startswith(self._pos_tags['jj']):
                            pred_list = self._get_dependents(self._dependencies['cop'], head)
                            if pred_list:
                                predicate, object = self._get_predicate_object(head)
                                predicate.add_word_unit(pred_list[0])
                            else:
                                continue
                        else:
                            continue
                        if predicate and object:
                            self.relations.append(Relation(subject, predicate, object))


def batch_extraction(mysql_db=None):
    # dataset = 'genes-cancer'
    dataset = 'RiMG75'
    # dataset = 'test'
    data_dir = 'data/{}/processed/'.format(dataset)

    if mysql_db:
        parser = SafeConfigParser()
        parser.read('config.ini')
        mysql_config = {
            'host': parser.get('MySQL', 'host'),
            'user': parser.get('MySQL', 'user'),
            'passwd': parser.get('MySQL', 'passwd'),
            'db': mysql_db
        }
        db = MySQLdb.connect(**mysql_config)
        cur = db.cursor()

    for root, _, files in os.walk(data_dir):
        for fn in files:
            if fn.endswith('.txt'):
                filename = os.path.join(root, fn)
                output_filename = os.path.join(root, fn + '.relations')
                f_in = codecs.open(filename, encoding='utf-8')
                f_out = codecs.open(output_filename, 'w', encoding='utf-8')
                for line in f_in:
                    sent = line.strip()
                    if sent:
                        print sent
                        f_out.write(u'{}\n'.format(sent))
                        try:
                            extractor = RelationExtractor(sent, debug=False)
                        except:
                            print u'\n[ERROR] {}'.format(sent)
                            print traceback.format_exc()
                        else:
                            extractor.extract_svo()
                            for relation in extractor.relations:
                                print relation
                                f_out.write(u'{}\n'.format(relation))
                                if mysql_db:
                                    try:
                                        cur.execute(extractor.generate_relation_sql(relation))
                                        db.commit()
                                    except MySQLdb.Error, e:
                                        try:
                                            print "MySQL Error [{}]: {}".format(e.args[0], e.args[1])
                                        except IndexError:
                                            print "MySQL Error: {}".format(str(e))
                            f_out.write('\n')
                f_in.close()
                f_out.close()

    if mysql_db:
        cur.close()
        db.close()


def single_extraction():
    sentences = u"""
        Genes were selected that (A) repress MAPK signaling (PP2AC, PEA-15, DUSP7, DUSP14, PKIA) and (B) are associated with activated MAPK signaling (RSK2, RAC1, k-RAS, FADD, KSR1, MAP3K14, MAP3K10) (C) qPCR for MCF-7-miR-155 cell line expression of RSK2 isoform variant 4 and 5."""
    for sent in split_multi(sentences):
        sent = sent.strip()
        if sent:
            print sent
            try:
                extractor = RelationExtractor(sent, debug=True)
            except:
                print 'Failed to parse the sentence.'
                print traceback.format_exc()
            else:
                extractor.extract_svo()
                for relation in extractor.relations:
                    print relation


if __name__ == '__main__':
    single_extraction()
    # batch_extraction('earth-kb')
