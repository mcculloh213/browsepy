from browsepy.plugin.text_digest.celeritas import celery
from . import make_task_logger
import time

logger = make_task_logger(__name__)


@celery.task(name='sleeper', track_started=True)
def sleeper(delay: int):
    logger.info('Task received!')
    logger.info(F'Requested Delay: {delay * 10} seconds.')
    time.sleep(delay * 10)
    logger.info(F'Delay complete!')
    return True
