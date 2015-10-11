# -*- coding: utf8 -*-

import re

s = u'see Holland (1984); Berner (2004); Hazen et al. (2012).'

reference_patterns = [
    r'(([A-Z]\S+)+(\sand\s)?([A-Z]\S+)?\s(et al.)?,?\s*\d{4}[;|,]*)',
    r'(([A-Z]\S+)+(\sand\s)?([A-Z]\S+)?\s(et al.)?,?\s*\(\d{4}\)[;|,]*)',
]

match = re.compile('|'.join(reference_patterns), re.UNICODE)
s = re.sub(match, '', s)

print s
