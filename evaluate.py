# -*- coding: utf8 -*-

import logging
import logging.config
import yaml
import codecs

from extract_relations import RelationExtractor


def evaluate_extraction(input_file, output_file):
    logger = logging.getLogger('extraction_evaluation')
    parser_server = 'http://localhost:8084'
    count = 0

    f_in = codecs.open(input_file, encoding='utf-8')
    f_out = codecs.open(output_file, 'w', encoding='utf-8')
    for line in f_in:
        line = line.strip()
        if line:
            logger.debug(line)
            try:
                extractor = RelationExtractor(line, logger, parser_server, entity_linking=False)
            except:
                logger.error(u'Failed to parse the sentence', exc_info=True)
            else:
                count += 1
                extractor.extract_spo()
                for relation in extractor.relations:
                    logger.debug(relation.canonical_form)
                    f_out.write('{}\t{}\n'.format(count, relation.canonical_form))
    f_in.close()
    f_out.close()


if __name__ == '__main__':
    with open('config/logging_config.yaml') as f:
        logging.config.dictConfig(yaml.load(f))

    extraction_input_file = 'data/evaluation/sentences.txt'
    extraction_outupt_file = 'data/evaluation/output.txt'
    evaluate_extraction(extraction_input_file, extraction_outupt_file)
