import os
import logging

import concurrent.futures

from sanitizer_factory import SanitizerFactory

logger = logging.getLogger('sanitizer')

def sanitize(src_dir, dest_dir):
    factory = SanitizerFactory()

    entries = [entry.path for entry in os.scandir(src_dir)]

    def process(path):
        logger.info(f'processing: {path}')
        factory.create(path).process(dest_dir)

    with concurrent.futures.ProcessPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(process, entries))
