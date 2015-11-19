# -*- coding: utf8 -*-

import itertools
import string
import codecs

import nltk
import begin


class KeywordExtractor(object):

    def __init__(self, punctuations=None, stop_words=None, good_tags=None):
        self.punctuations = punctuations if punctuations else set(string.punctuation)
        self.stop_words = stop_words if stop_words else set(nltk.corpus.stopwords.words('english'))
        self.good_tags = good_tags if good_tags else set(['NN', 'NNP', 'NNS', 'NNPS'])

    def extract_candidate_words(self, text):
        # tokenize and POS-tag words
        tagged_words = itertools.chain.from_iterable(nltk.pos_tag_sents(nltk.word_tokenize(sent)
                                                                        for sent in nltk.sent_tokenize(text)))
        # filter on certain POS tags and lowercase all words
        candidates = [word.lower() for word, tag in tagged_words
                      if tag in self.good_tags and
                      word.lower() not in self.stop_words and
                      not all(char in self.punctuations for char in word)]
        return candidates

    def compute_word_frequency(self, candidates):
        word_frequency = {}
        for word in candidates:
            word_frequency.setdefault(word, 0)
            word_frequency[word] += 1
        return sorted(word_frequency.items(), key=lambda item: item[1], reverse=True)


@begin.subcommand
def run(input_file, output_file='output.txt', verbose=True):
    f = codecs.open(input_file, encoding='utf-8')
    text = f.read().replace('\n', ' ')
    f.close()

    extractor = KeywordExtractor()
    candidates = extractor.extract_candidate_words(text)
    keywords = extractor.compute_word_frequency(candidates)

    f = codecs.open(output_file, 'w', encoding='utf-8')
    for word in keywords:
        f.write(u'{} {}\n'.format(word[0], word[1]))
        if verbose:
            print word[0], word[1]
    f.close()


@begin.start
def main():
    pass

if begin.start():
    pass
