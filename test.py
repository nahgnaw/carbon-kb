from __future__ import unicode_literals, print_function
from spacy.en import English


nlp = English()
doc = nlp('Natural graphite is a common crustal mineral that occurs most abundantly in metamorphic rocks in pods and veins.')
for sentence in doc.sents:
    print(sentence.root.orth_)

for chunk in doc.noun_chunks:
    print(chunk.label_, chunk.orth_, chunk.root.head.dep_, chunk.root.head.orth_)

# for token in doc:
#     print (token.orth_, token.dep_, token.head.orth_)
