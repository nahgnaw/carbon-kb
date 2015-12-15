# -*- coding: utf8 -*-


class WordUnit(object):

    def __init__(self, index, word, lemma, pos):
        self._index = index
        self._word = word
        self._lemma = lemma
        self. _pos = pos

    def __str__(self):
        return self._word

    def __repr__(self):
        return self._word

    def __eq__(self, other):
        return self._index == other._index

    def __len__(self):
        return len(self._word)

    @property
    def index(self):
        return self._index

    @property
    def word(self):
        return self._word

    @property
    def lemma(self):
        return self._lemma.lower()

    @property
    def pos(self):
        return self._pos

    def more_info(self):
        return '({})'.format(' '.join([str(self._index), self._word, self._pos]))


class WordUnitSequence(object):

    def __init__(self, word_unit_list=None, head=None):
        if word_unit_list:
            if not type(word_unit_list) is list:
                word_unit_list = [word_unit_list]
            self._seq = word_unit_list
            self._sort()
        else:
            self._seq = []
        self._head = head if head else None
        self._nn_head = None

    def __str__(self):
        return ' '.join([wn.word for wn in self._seq])

    def __nonzero__(self):
        return len(self._seq)

    def __len__(self):
        return len(self._seq)

    def __getitem__(self, i):
        return self._seq[i]

    def __iter__(self):
        for ind, wn in enumerate(self._seq):
            yield ind, wn

    def _sort(self):
        if self._seq:
            self._seq = sorted(self._seq, key=lambda wn: wn.index)

    @property
    def lemma(self):
        return ' '.join(wn.lemma for wn in self._seq)

    def extend(self, seq):
        if seq:
            if isinstance(seq, list):
                self._seq.extend(seq)
            else:
                self._seq.extend(seq.sequence)
            self._sort()

    def add_word_unit(self, word_unit):
        if word_unit:
            self._seq.append(word_unit)
            self._sort()

    @property
    def sequence(self):
        return self._seq

    @property
    def head(self):
        return self._head

    @head.setter
    def head(self, head):
        self._head = head

    @property
    def nn_head(self):
        return self._nn_head

    @nn_head.setter
    def nn_head(self, nn):
        self._nn_head = nn