import os

from browsepy import datetime
from browsepy.file import abspath_to_urlpath, urlpath_to_abspath
from browsepy.plugin.text_digest.entity import (
    connect,
    )
from browsepy.plugin.text_digest.provider import ContentProvider
from . import Reject, celery, make_task_logger

logger = make_task_logger('ai.mccullough.celeritas.digest.nltk')
content_provider = ContentProvider('ai.mccullough.browsepy')


@celery.task(bind=True,
             name='digest.nltk',
             track_started=True,
             )
@connect()
def digest_text(self, urlpath: str):
    logger.info('Task received!')

