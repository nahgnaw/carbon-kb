# -*- coding: utf8 -*-

import logging
import logging.config
import yaml

from extract_relations import RelationExtractor


def evaluate_extraction(input_file, output_file):
    logger = logging.getLogger('extraction_evaluation')
    parser_server = 'http://localhost:8084'
    count = 0

    results = []
    with open(input_file) as f_in:
        for line in f_in:
            line = line.strip()
            if line:
                try:
                    extractor = RelationExtractor(line, logger, parser_server, entity_linking=False)
                except:
                    logger.error(u'Failed to parse the sentence', exc_info=True)
                else:
                    count += 1
                    extractor.extract_spo()
                    for relation in extractor.relations:
                        logger.debug(relation.canonical_form)
                        results.append('{}\t{}'.format(count, relation.canonical_form))

    with open(output_file, 'w') as f_out:
        for res in results:
            f_out.write('{}\n'.format(res))


if __name__ == '__main__':
    with open('config/logging_config.yaml') as f:
        logging.config.dictConfig(yaml.load(f))

    extraction_input_file = 'data/evaluation/sentences.txt'
    extraction_outupt_file = 'data/evaluation/output.txt'
    evaluate_extraction(extraction_input_file, extraction_outupt_file)
