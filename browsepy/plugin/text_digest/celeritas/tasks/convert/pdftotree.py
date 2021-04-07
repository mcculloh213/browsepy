import os
import pdftotree

from browsepy.file import urlpath_to_abspath
from . import celery, make_task_logger

logger = make_task_logger('ai.mccullough.celeritas.pdftotree')


@celery.task(name='convert.pdftotree', track_started=True)
def convert_pdf_to_hocr(path: str):
    logger.info('Task received!')
    if not path.endswith('.pdf'):
        pass
    pdftotree.parse()
    pass
