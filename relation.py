# -*- coding: utf8 -*-


class Relation(object):

    def __init__(self, subj=None, pred=None, obj=None, subj_el=None, obj_el=None):
        self._subj = subj
        self._pred = pred
        self._obj = obj
        self._subj_el = subj_el
        self._obj_el = obj_el

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
    def subject_el(self):
        return self._subj_el

    @subject_el.setter
    def subject_el(self, subj_el):
        if isinstance(subj_el, list):
            subj_el = ','.join(subj_el)
        self._subj_el = subj_el

    @property
    def object_el(self):
        return self._obj_el

    @object_el.setter
    def object_el(self, obj_el):
        if isinstance(obj_el, list):
            obj_el = ','.join(obj_el)
        self._obj_el = obj_el
