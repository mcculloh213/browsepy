import os
import re
import string

from collections import defaultdict
from nltk import pos_tag
from nltk.corpus import stopwords, wordnet
from nltk.stem import PorterStemmer, WordNetLemmatizer
from nltk.tokenize import word_tokenize

from browsepy import datetime
from browsepy.file import abspath_to_urlpath, urlpath_to_abspath
from browsepy.plugin.text_digest.entity import (
    connect,
    )
from browsepy.plugin.text_digest.provider import ContentProvider
from typing import List
from . import Reject, celery, make_task_logger

logger = make_task_logger('ai.mccullough.celeritas.digest.nltk')
content_provider = ContentProvider('ai.mccullough.browsepy')

__DEFAULT_STOP_WORDS__ = set(stopwords.words('english'))


def __to_lower_case(text: str) -> str:
    return text.lower()


def __remove_numbers(text: str, pattern: str = r'\d+') -> str:
    return re.sub(pattern, '', text)


def __remove_punctuation(text: str, punctuation: str = string.punctuation) -> str:
    translation_table = str.maketrans('', '', punctuation)
    return text.translate(translation_table)


def __remove_whitespace(text: str) -> str:
    return text.strip()


def __tokenize_text(text: str, stop_words: List[str]) -> List[str]:
    _sw = set(__DEFAULT_STOP_WORDS__)
    _sw.update(*stop_words)
    return [token for token in word_tokenize(text) if token not in _sw]


def __tag_pos(tokens: List[str]):
    return pos_tag(tokens)


def __wordnet_pos(pos: str) -> str:
    if pos.startswith('J'):
        return wordnet.ADJ
    elif pos.startswith('V'):
        return wordnet.VERB
    elif pos.startswith('N'):
        return wordnet.NOUN
    elif pos.startswith('R'):
        return wordnet.ADV
    else:
        return wordnet.NOUN


@celery.task(bind=True,
             name='digest.nltk',
             track_started=True,
             )
@connect(alias='celeritas')
def digest_text(self, urlpath: str):
    logger.info('Task received!')

