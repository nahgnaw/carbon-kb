# -*- coding: utf8 -*-

import logging
import logging.config
import yaml
import codecs
import unicodecsv
import scipy.stats
import numpy as np

from cycler import cycler
from matplotlib import pyplot as plt
from gensim.models import Word2Vec
from numpy import arange
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
                extractor = RelationExtractor(line, parser_server, logger, entity_linking_flag=False)
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


# def evaluate_similarity(method_name, embedding_file):
#     logger = logging.getLogger()
#
#     logger.info('Loading embeddings from {}...'.format(embedding_file))
#     embedding_model = Word2Vec.load_word2vec_format(embedding_file, binary=True)
#
#     benchmark_file = 'data/evaluation/similarity/umnsrs_similarity_modified.csv'
#     result_file = 'data/evaluation/similarity/{}_similarity_pairs.csv'.format(method_name)
#     benchmark_scores = []
#     method_scores = []
#     f_in = open(benchmark_file)
#     f_out = open(result_file, 'w')
#     reader = unicodecsv.reader(f_in)
#     writer = unicodecsv.writer(f_out)
#     next(reader, None)
#     for row in reader:
#         score, _, term_1, term_2 = row[:4]
#         term_1, term_2 = term_1.lower().replace(' ', '_'), term_2.lower().replace(' ', '_')
#         score = float(score)
#         if term_1 in embedding_model and term_2 in embedding_model:
#             sim_score = float(embedding_model.similarity(term_1, term_2))
#             logger.debug('{}, {}: {}'.format(term_1, term_2, sim_score))
#             writer.writerow([sim_score, term_1, term_2])
#             benchmark_scores.append(score)
#             method_scores.append(sim_score)
#     f_in.close()
#     f_out.close()
#
#     logger.info('Computing Spearman\'s Rank Correlation...')
#     rho, p = scipy.stats.spearmanr(benchmark_scores, method_scores)
#     logger.debug('correlation coefficient: {}, p-value: {}'.format(rho, p))
#
#     x = np.arange(len(benchmark_scores))
#     y1 = np.array(method_scores)
#     y1 = (y1 - y1.mean()) / y1.std()
#     y2 = np.array(benchmark_scores)
#     y2 = (y2 - y2.mean()) / y2.std()
#
#     plt.rc('lines', linewidth=2)
#     plt.rc('axes', prop_cycle=(cycler('color', ['#E87F4D', '#9CB2B3'])))
#     plt.rc('font', **{'size': 24})
#     plt.subplot(121)
#     plt.plot(x, y1, x, y2)
#     plt.xlim([0, np.max(x)])
#     plt.xticks([])
#     plt.legend([method_name, 'benchmark'])
#     plt.subplot(122)
#     plt.scatter(y1, y2, s=40, c='#E87F4D', edgecolors='face')
#     plt.xlabel(method_name, fontsize=32)
#     plt.ylabel('benchmark', fontsize=32)
#     plt.xticks([])
#     plt.yticks([])
#     plt.show()


def generate_entity_pairs(threshold):
    input_file = 'data/evaluation/similarity/umnsrs_similarity_modified.csv'
    output_file = 'data/evaluation/similarity/entity_pairs.txt'

    f_in = open(input_file)
    f_out = open(output_file, 'w')
    reader = unicodecsv.reader(f_in)

    next(reader, None)
    for row in reader:
        score, _, term_1, term_2 = row[:4]
        term_1, term_2 = term_1.lower().split(), term_2.lower().split()
        score = float(score)
        if score >= threshold and len(term_1) == 1 and len(term_2) == 1:
            f_out.write('{},{}\n'.format(term_1[0], term_2[0]))
    f_in.close()
    f_out.close()


def compute_pair_similarity(benchmark_file, embedding_file, binary_embedding=True):
    logger = logging.getLogger()

    logger.info('Loading embeddings from {}...'.format(embedding_file))
    embedding_model = Word2Vec.load_word2vec_format(embedding_file, binary=binary_embedding)

    pair_similarities = {}
    with open(benchmark_file) as bf:
        for line in bf:
            line = line.strip()
            if line:
                pair = tuple(line.split(','))
                term_1, term_2 = pair
                if term_1 in embedding_model and term_2 in embedding_model:
                    sim_score = float(embedding_model.similarity(term_1, term_2))
                    pair_similarities[pair] = sim_score

    accuracy = []
    for threshold in arange(0.0, 1.1, 0.1):
        similar_pair_count = 0
        for pair in pair_similarities:
            if pair_similarities[pair] >= threshold:
                similar_pair_count += 1
        accuracy.append(float(similar_pair_count) / len(pair_similarities))

    logger.info('Accuracy: {}'.format(accuracy))
    return accuracy


def plot_pair_similarity_results(methods, results, output_figure):
    fig, ax = plt.subplots()
    line_colors = ['#e8814c', '#9cb2b3', '#e5cb80']
    x = arange(0.0, 1.1, 0.1)
    for i, y in enumerate(results):
        plt.plot(x, y, color=line_colors[i], linestyle='-', linewidth=2, label=methods[i])

    tick_font = {'fontname': 'Arial', 'size': '14'}
    label_font = {'fontname': 'Arial', 'size': '18'}

    ax.set_xlabel('Similarity Score Threshold', **label_font)
    ax.set_xlim(0, 1.0)
    ax.set_xticks(arange(0.0, 1.1, 0.1))
    ax.set_xticklabels(arange(0.0, 1.1, 0.1), **tick_font)
    ax.set_ylabel('Accuracy', **label_font)
    ax.set_ylim(0, 1.1)
    ax.set_yticks(arange(0.0, 1.1, 0.2))
    ax.set_yticklabels(arange(0.0, 1.1, 0.2), **tick_font)
    ax.legend(methods, fontsize=20, loc='lower left')
    ax.grid(alpha=0.6)

    fig.savefig('/Users/HanWang/Dropbox/Research/Dissertation/Thesis/figures/{}'.format(output_figure), dpi=300)

if __name__ == '__main__':
    with open('config/logging_config.yaml') as f:
        logging.config.dictConfig(yaml.load(f))

    # Evaluate extraction.
    # extraction_input_file = 'data/evaluation/extraction/sentences.txt'
    # extraction_outupt_file = 'data/evaluation/extraction/output.csv'
    # evaluate_extraction(extraction_input_file, extraction_outupt_file)

    # Evaluate pair similarities.
    methods = ['SciKB', 'Word2Vec', 'DepW2V']
    # Entities
    generate_entity_pairs(threshold=1000)
    entity_pair_similarity_results = []
    entity_pair_benchmark_file = 'data/evaluation/similarity/entity_pairs.txt'
    entity_pair_similarity_results.append(
        compute_pair_similarity(entity_pair_benchmark_file,
                                'data/pmc_c-h/embeddings/word2vec'))
                                # 'data/pmc/embeddings/scikb_directed_58m_triples_min_edge_cnt_two'))
    entity_pair_similarity_results.append(
        compute_pair_similarity(entity_pair_benchmark_file, 'data/pmc/embeddings/word2vec_58m_triples'))
    entity_pair_similarity_results.append(
        compute_pair_similarity(entity_pair_benchmark_file, 'data/pmc/embeddings/dep_w2v', False))
    plot_pair_similarity_results(methods, entity_pair_similarity_results, 'ch4_entity_pair_similarity_results.eps')
    # Relations
    relation_pair_similarity_results = []
    relation_pair_benchmark_file = 'data/evaluation/similarity/relation_pairs.txt'
    relation_pair_similarity_results.append(
        compute_pair_similarity(relation_pair_benchmark_file,
                                'data/pmc/embeddings/scikb_directed_58m_triples_min_edge_cnt_two'))
    relation_pair_similarity_results.append(
        compute_pair_similarity(relation_pair_benchmark_file, 'data/pmc/embeddings/word2vec_58m_triples'))
    relation_pair_similarity_results.append(
        compute_pair_similarity(relation_pair_benchmark_file, 'data/pmc/embeddings/dep_w2v', False))
    plot_pair_similarity_results(methods, relation_pair_similarity_results, 'ch4_relation_pair_similarity_results.eps')
