# -*- coding: utf8 -*-

from nltk.tokenize import sent_tokenize
from dependency_graph import DependencyGraph


NSUBJ = u'nsubj'
NSUBJPASS = u'nsubjpass'
DOBJ = u'dobj'
COP = u'cop'
AUXPASS = u'auxpass'
NNMOD = u'nn'
NN = u'NN'
VB = u'VB'

sentences = """
   Carbon, element 6, displays remarkable chemical flexibility and thus is unique in the diversity of its mineralogical roles.
"""

for sentence in sent_tokenize(sentences):

    dg = DependencyGraph(sentence)
    dg.print_dep_triples()

    # grammar = r"""
    #     NP: {<DT|CD|PP\$>?<JJ.*>*<NN.*>+}   # chunk determiner/possessive, adjectives and noun
    #         {<DT|JJ>}                       # chunk determiners and adjectives
    #         }<[\.VI].*>+{                   # chink any tag beginning with V, I, or .
    #         <.*>}{<DT>                      # split a chunk at a determiner
    #         <DT|JJ>{}<NN.*>                 # merge chunk ending with det/adj with one starting with a noun
    #     P:  {<IN>}                          # Preposition
    #     V:  {<V.*>}                         # Verb
    #     PP: {<P><NP>}                       # PP -> P NP
    #     VP: {<V><NP|PP>+}                   # VP -> V (NP|PP)+
    # """
    # REL:  {<V>|<VP>|<V>.*<P>}

    # cp = nltk.RegexpParser(grammar)
    # cp = nltk.parse.api.ParserI()
    # print cp.parse(dg.tagged_text)

    relations = []
    # Extract nsubj relations
    triples = dg.get_triples_by_relation([NSUBJ, NSUBJPASS])
    for triple in triples:
        if triple[1] == NSUBJ:
            if triple[0][2].startswith(VB):
                subj_index, subj = triple[2][0:2]
                subj_nn_tuples = dg.get_dependent_by_head_relation(subj_index, NNMOD)
                subj = ' '.join([nn[1] for nn in sorted(subj_nn_tuples, key=lambda t: t[0])]) + ' ' + subj
                pred_index, pred = triple[0][0:2]
                obj_tuples = dg.get_dependent_by_head_relation(pred_index, DOBJ)
                for obj in obj_tuples:
                    obj_nn_tuples = dg.get_dependent_by_head_relation(obj[0], NNMOD)
                    obj = ' '.join([nn[1] for nn in sorted(obj_nn_tuples, key=lambda t: t[0])]) + ' ' + obj[1]
                    relations.append((subj, pred, obj, sentence))
            elif triple[0][2].startswith(NN):
                subj_index, subj = triple[2][0:2]
                subj_nn_tuples = dg.get_dependent_by_head_relation(subj_index, NNMOD)
                subj = ' '.join([nn[1] for nn in sorted(subj_nn_tuples, key=lambda t: t[0])]) + ' ' + subj
                obj_index, obj = triple[0][0:2]
                obj_nn_tuples = dg.get_dependent_by_head_relation(obj_index, NNMOD)
                obj = ' '.join([nn[1] for nn in sorted(obj_nn_tuples, key=lambda t: t[0])]) + ' ' + obj
                pred_tuples = dg.get_dependent_by_head_relation(obj_index, COP)
                for pred in pred_tuples:
                    relations.append((subj, pred, obj, sentence))
        elif triple[1] == NSUBJPASS:
            if triple[0][2].startswith(VB):
                subj_index, subj = triple[2][0:2]
                subj_nn_tuples = dg.get_dependent_by_head_relation(subj_index, NNMOD)
                subj = ' '.join([nn[1] for nn in sorted(subj_nn_tuples, key=lambda t: t[0])]) + ' ' + subj
                obj_index, obj = triple[0][0:2]
                obj_nn_tuples = dg.get_dependent_by_head_relation(obj_index, NNMOD)
                obj = ' '.join([nn[1] for nn in sorted(obj_nn_tuples, key=lambda t: t[0])]) + ' ' + obj
                pred_tuples = dg.get_dependent_by_head_relation(obj_index, AUXPASS)
                for pred in pred_tuples:
                    relations.append((subj, pred, obj, sentence))

    print relations
