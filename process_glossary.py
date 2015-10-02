# -*- coding: utf8 -*-

import codecs

terms = []

f_in = codecs.open('data/glossary.txt', encoding='utf-8')
for line in f_in:
    line = line.strip()
    if line and line not in terms:
        terms.append(line)
f_in.close()

f_out = codecs.open('glossary.txt', 'w', 'utf-8')
for term in terms:
    f_out.write(u'{}\n'.format(term))