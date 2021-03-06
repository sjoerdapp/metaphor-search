#!/usr/bin/env python
# coding: utf-8

# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>

import os
import numpy
import shutil
import logging
import argparse

from sear.index import InvertedIndex                # The index itself.
from sear.utils import IndexingPipeline             # Utility which will control indexing process.

from sear.storage import LdbStorage                 # Storage for raw indexed documents.
from sear.lexicon import DictLexicon                # Term lexicon backend.

from metaphor.ruwac import RuwacParser
from metaphor.ruwac import RuwacStream
from metaphor.ruwac import RuwacIndexer

from metaphor.gigaword import GigawordStream
from metaphor.gigaword import GigawordParser


logging.basicConfig(level=logging.INFO)


arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("-t", "--test",         type=int, choices=(0, 1), default=0)
arg_parser.add_argument("-s", "--test_size",    type=str, choices=("tiny", "medium", "large"), default="tiny")
arg_parser.add_argument("-l", "--language",     type=str, default=None)
arg_parser.add_argument("-c", "--corpus",       type=str, choices=("ruwac", "gigaword"), default=None)
arg_parser.add_argument("-i", "--input",        type=str)
arg_parser.add_argument("-o", "--output",       type=str)
arguments = arg_parser.parse_args()


logging.info("Initializing output directory structure.")

if arguments.test == 1:

    input_path = os.path.join(
        arguments.input,
        "test_data",
        arguments.test_size,
        arguments.language,
        "document.txt"
    )
    output_path = os.path.join(
        arguments.output,
        "test_out",
        arguments.test_size,
        arguments.language,
        "document"
    )
else:

    input_path = arguments.input
    output_path = arguments.output

logging.info("Input: %s" % input_path)
logging.info("Output: %s" % output_path)


if os.path.exists(output_path):
    shutil.rmtree(output_path)
os.makedirs(output_path)



logging.info("Initializing lexicon.")
lexicon = DictLexicon(output_path)
lexicon.load()


logging.info("Initializing storage.")
storage = LdbStorage(output_path)
storage.init_db()
storage.open_db()


logging.info("Initializing index.")
index = InvertedIndex(output_path, field_properties=[
    ("document_id", numpy.int32),
])
index.init_index()
index.open()


logging.info("Initializing ruwac stream and its parser.")

if arguments.language == "spa" or arguments.language == "eng":
    sentence_stream = GigawordStream(open(input_path, "rb"))
    sentence_parser = GigawordParser(language=arguments.language)
elif arguments.language == "rus":
    sentence_stream = RuwacStream(open(input_path, "rb"))
    sentence_parser = RuwacParser()
else:
    raise Exception("Unsupported language: %s" % arguments.language)

sentence_indexer = RuwacIndexer(lexicon)


logging.info("Initializing indexing pipeline.")
indexing_pipeline = IndexingPipeline(lexicon, index, storage)


logging.info("Start indexing file: %s" % input_path)
input_mb_size = float(os.path.getsize(input_path)) / (1024 ** 2)
logging.info("Input size: %.2fMB" % input_mb_size)
indexing_pipeline.index_stream(sentence_stream, sentence_parser, sentence_indexer)


logging.info("Closing index.")
index.close()


logging.info("Closing storage.")
storage.close_db()


logging.info("Dumping lexicon.")
lexicon.dump()


logging.info("No way, it's done!")
