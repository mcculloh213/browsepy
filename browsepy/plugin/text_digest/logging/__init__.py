import logging
import os

from typing import Optional

LOGDIR = '/var/www/browsepy/logs'
LOGGING_FORMAT = '%(asctime)s/%(name)s [%(levelname)s]: %(message)s'


def make_logger(import_name, subdir=None):
    # type: (str, Optional[str]) -> logging.Logger

    # create logger
    logger = logging.getLogger(import_name)
    logger.setLevel(logging.DEBUG)

    # create console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create file handler
    logdir = LOGDIR if not subdir else os.path.join(LOGDIR, subdir)
    if not os.path.exists(logdir):
        os.mkdir(logdir)
    fh = logging.FileHandler(os.path.join(logdir, F'{import_name}.log'))
    fh.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter(LOGGING_FORMAT)
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    # attach handlers
    logger.addHandler(ch)
    logger.addHandler(fh)

    return logger
