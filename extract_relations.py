# -*- coding: utf8 -*-

import os
import codecs
import traceback
import MySQLdb

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

    def generate_sql(self, table_name='relations'):
        return """
            INSERT INTO {} (subject, predicate, object)
            VALUES ("{}", "{}", "{}");
        """.format(table_name, self._subj, self._pred, self._obj)


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
    }

    _subject_pos_blacklist = [
        _pos_tags['wdt'], _pos_tags['dt'], _pos_tags['prp'],
        _pos_tags['jj'], _pos_tags['jjr'], _pos_tags['jjs']
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

    def generate_relation_sql(self, relation, table_name='relations'):
        return u"""
            INSERT INTO {} (subject, predicate, object, sentence)
            VALUES ("{}", "{}", "{}", "{}");
        """.format(table_name, relation.subject, relation.predicate, relation.object, self._sentence)

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
        conj_deps = [
            self._dependencies['conj:and'],
            self._dependencies['conj:or']
        ]
        for dep in conj_deps:
            conjunction.extend(self._get_dependents(dep, head))
        # if conj_list:
        #     for conj in conj_list:
        #         conjunction.extend(self._get_noun_compound(conj))
        # cc_list = self._get_dependents(self._dependencies['cc'], head)
        # if cc_list:
        #     for cc in cc_list:
        #         conjunction.add_word_unit(cc)
        return conjunction

    def _get_noun_compound(self, head):
        nn = self._get_dependents(self._dependencies['nn'], head)
        if nn:
            nn.append(head)
            return WordUnitSequence(nn)
        return WordUnitSequence(head)

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
        # # Find out if the head has conjunctions
        # conj = self._get_conjunctions(head)
        # if conj:
        #     expansion.extend(conj)
        #     if self._debug:
        #         print '[DEBUG] "{}" head expansion with conjunction: "{}"'.format(head, conj)
        return expansion

    # Expand predicate with auxiliary and negation
    def _expand_predicate(self, predicate, pred_head):

        def expand_predicate(pred_head, dep, debug=False):
            dep_wn = self._get_dependents(dep, pred_head)
            if dep_wn:
                predicate.add_word_unit(dep_wn[0])
                if debug:
                    print '[DEBUG] "{}" predicate expansion with {}: "{}"'.format(pred_head, dep, dep_wn[0])

        # Find out if there is any aux
        expand_predicate(pred_head, self._dependencies['aux'], self._debug)
        # Find out if there is any auxpass
        expand_predicate(pred_head, self._dependencies['auxpass'], self._debug)
        # Find out if there is any negation
        expand_predicate(pred_head, self._dependencies['neg'], self._debug)
        # Find out if there is any xcomp
        xcomp_list = self._get_dependents(self._dependencies['xcomp'], pred_head)
        if xcomp_list:
            for xcomp in xcomp_list:
                predicate.add_word_unit(xcomp)
                # Use the xcomp as the "head" instead of the original head
                predicate.head = xcomp
                if self._debug:
                    print '[DEBUG] "{}" predicate expansion with xcomp: "{}"'.format(pred_head, xcomp)
                expand_predicate(xcomp, self._dependencies['aux'], self._debug)
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
                # If the dependency relation is a verb:
                if head.pos.startswith(self._pos_tags['vb']):
                    for head in head_conjunction:
                        # The predicate is the head
                        predicate = WordUnitSequence([head], head)
                        self._expand_predicate(predicate, head)
                        pred = predicate.head
                        # Check if there is any direct object
                        obj_list = self._get_dependents(self._dependencies['dobj'], pred)
                        if obj_list:
                            for obj in obj_list:
                                object = self._expand_head_word(obj)
                                relation = Relation(subject, predicate, object)
                                self.relations.append(relation)
                        # If there is no direct objects, look for prepositional objects
                        else:
                            acomp_list = self._get_dependents(self._dependencies['acomp'], pred)
                            if acomp_list:
                                for acomp in acomp_list:
                                    predicate.add_word_unit(acomp)
                            pobj_phrase = self._get_pobj_phrase(pred)
                            if pobj_phrase:
                                predicate.add_word_unit(pobj_phrase[0])
                                object = WordUnitSequence(pobj_phrase[1:])
                                if object:
                                    relation = Relation(subject, predicate, object)
                                    self.relations.append(relation)
                # If the dependency relation is a copular verb
                elif head.pos.startswith(self._pos_tags['nn']) or head.pos.startswith(self._pos_tags['jj']):
                    # The predicate is the copular verb
                    pred_list = self._get_dependents(self._dependencies['cop'], head)
                    if pred_list:
                        predicate = WordUnitSequence([pred_list[0]], pred_list[0])
                        self._expand_predicate(predicate, pred_list[0])
                        for head in head_conjunction:
                            # The object is the head
                            object = self._expand_head_word(head)
                            relation = Relation(subject, predicate, object)
                            self._relations.append(relation)


def batch_extraction(write_to_mysql=False):
    # dataset = 'genes-cancer'
    dataset = 'RiMG75'
    data_dir = 'data/{}/tmp/'.format(dataset)

    if write_to_mysql:
        mysql_config = {
            'host': 'localhost',
            'user': 'root',
            'passwd': 'root',
            'db': 'sci-kb'
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
                    f_out.write(u'{}\n'.format(sent))
                    # print sent
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
                            if write_to_mysql:
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

    if write_to_mysql:
        cur.close()
        db.close()


def single_extraction():
    sentences = u"""
        My wife and I went to the market today.
    """
    for sent in sent_tokenize(sentences):
        sent = sent.strip()
        print sent
        try:
            extractor = RelationExtractor(sent, debug=True)
        except:
            print 'Failed to parse the sentence.'
            print traceback.format_exc()
        else:
            # extractor.extract_nsubj()
            # extractor.extract_nsubjpass()
            extractor.extract_svo()
            for relation in extractor.relations:
                print relation


if __name__ == '__main__':
    single_extraction()
    # batch_extraction()
