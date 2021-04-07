import os

from celery import Celery, states
from celery.exceptions import Ignore, Reject

CELERY_BROKER = 'CELERY_BROKER_URL'
CELERY_BACKEND = 'CELERY_RESULT_BACKEND'
REDIS_CONTAINER = 'redis://localhost:6379'

celery = Celery(__name__)
celery.conf.broker_url = os.environ.get(CELERY_BROKER, REDIS_CONTAINER)
celery.conf.result_backend = os.environ.get(CELERY_BACKEND, REDIS_CONTAINER)
celery.conf.task_serializer = 'json'
celery.conf.accept_content = ['json']
celery.conf.result_serializer = 'json'

AsyncResult = celery.AsyncResult
