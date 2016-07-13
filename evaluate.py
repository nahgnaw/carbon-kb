# -*- coding: utf8 -*-

import logging
import logging.config
import yaml
import codecs
import unicodecsv
import scipy.stats
import numpy as np

from matplotlib import pyplot as plt
from gensim.models import Word2Vec
from extract_relations import RelationExtractor


def evaluate_extraction(input_file, output_file):
    logger = logging.getLogger()
    parser_server = 'http://localhost:8084'
    count = 0

    f_in = codecs.open(input_file, encoding='utf-8')
    f_out = open(output_file, 'w')
    writer = unicodecsv.writer(f_out)
    for line in f_in:
        line = line.strip()
        if line:
            logger.debug(line)
            try:
                extractor = RelationExtractor(line, parser_server, logger, entity_linking=False)
            except:
                logger.error(u'Failed to parse the sentence', exc_info=True)
            else:
                count += 1
                extractor.extract_spo()
                for relation in extractor.relations:
                    logger.debug(relation.lemma)
                    row = [''] * 5
                    row[0], row[1] = count, line
                    row[2:5] = relation.lemma
                    writer.writerow(row)
    f_in.close()
    f_out.close()


def similarity_benchmark(method_name, embedding_file):
    logger = logging.getLogger()

    logger.info('Loading embeddings from {}...'.format(embedding_file))
    embedding_model = Word2Vec.load_word2vec_format(embedding_file, binary=True)

    benchmark_file = 'data/evaluation/similarity/umnsrs_similarity_modified.csv'
    result_file = 'data/evaluation/similarity/{}_similarity_pairs.csv'.format(method_name)
    benchmark_scores = []
    method_scores = []
    f_in = open(benchmark_file)
    f_out = open(result_file, 'w')
    reader = unicodecsv.reader(f_in)
    writer = unicodecsv.writer(f_out)
    next(reader, None)
    for row in reader:
        score, _, term_1, term_2 = row[:4]
        term_1, term_2 = term_1.lower(), term_2.lower()
        score = float(score)
        if term_1 in embedding_model and term_2 in embedding_model:
            sim_score = embedding_model.similarity(term_1, term_2)
            logger.debug('{}, {}: {}'.format(term_1, term_2, sim_score))
            writer.writerow([sim_score, term_1, term_2])
            benchmark_scores.append(score)
            method_scores.append(sim_score)
    f_in.close()
    f_out.close()

    logger.info('Computing Spearman\'s Rank Correlation...')
    rho, p = scipy.stats.spearmanr(benchmark_scores, method_scores)
    logger.debug('correlation coefficient: {}, p-value: {}'.format(rho, p))

    x = np.arange(len(benchmark_scores))
    y1 = np.array(benchmark_scores)
    y1 = (y1 - y1.mean()) / y1.std()
    y2 = np.array(method_scores)
    y2 = (y2 - y2.mean()) / y2.std()
    plt.plot(x, y1, x, y2)
    plt.legend(['benchmark', method_name])
    plt.show()


if __name__ == '__main__':
    with open('config/logging_config.yaml') as f:
        logging.config.dictConfig(yaml.load(f))

    # extraction_input_file = 'data/evaluation/extraction/sentences.txt'
    # extraction_outupt_file = 'data/evaluation/extraction/output.csv'
    # evaluate_extraction(extraction_input_file, extraction_outupt_file)

    # method_name = 'scikb'
    # embedding_file = 'data/pmc_c-h/embeddings/scikb_directed'
    method_name = 'word2vec'
    embedding_file = 'data/pmc_c-h/embeddings/pmc_w2v'
    similarity_benchmark(method_name, embedding_file)
