# -*- coding: utf8 -*-


class Relation(object):

    def __init__(self, subj=None, pred=None, obj=None, vec_repr=False):
        self._subj = subj
        self._pred = pred
        self._obj = obj
        if vec_repr:
            self._subj_vec_list = []
            self._pred_vec_list = []
            self._obj_vec_list = []
            self._subj_vec = None
            self._pred_vec = None
            self._obj_vec = None

    def __str__(self):
        return u'({}, {}, {})'.format(str(self._subj), str(self._pred), str(self._obj))

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

    @property
    def subject_vector(self):
        return self._subj_vec

    @property
    def predicate_vector(self):
        return self._pred_vec

    @property
    def object_vector(self):
        return self._obj_vec

    def append_vector(self, component, vector):
        if component == 'subject':
            self._subj_vec_list.append(vector)
        elif component == 'predicate':
            self._pred_vec_list.append(vector)
        elif component == 'object':
            self._obj_vec_list.append(vector)
        else:
            raise ValueError('There is no such a variable: {}.'.format(component))

    def compose_vectors(self, component):
        if component == 'subject':
            for vec in self._subj_vec_list:
                self._subj_vec += vec
        elif component == 'predicate':
            for vec in self._pred_vec_list:
                self._pred_vec += vec
        elif component == 'object':
            for vec in self._obj_vec_list:
                self._obj_vec += vec
        else:
            raise ValueError('There is no such a variable: {}.'.format(component))

    @staticmethod
    def save_vector_to_file(vec, file):
        pass
