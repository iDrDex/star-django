import logging
from celery import shared_task

from legacy.models import Analysis
from .analysis import perform_analysis


@shared_task
def analysis_task(analysis_id):
    handler = RedisHandler(key='analysis:%d:log' % analysis_id)
    with extra_logging_handler('analysis', handler):
        analysis = Analysis.objects.get(pk=analysis_id)
        perform_analysis(analysis)


# Extra logging

from contextlib import contextmanager
from core.conf import redis_client

@contextmanager
def extra_logging_handler(name, handler):
    logger = logging.getLogger(name)
    logger.addHandler(handler)
    try:
        yield
    finally:
        logger.removeHandler(handler)

class RedisHandler(logging.Handler):
    def __init__(self, key):
        super(RedisHandler, self).__init__()
        self.key = key

    def emit(self, record):
        # NOTE: other option is saving json.dumps(record.__data__)
        redis_client.rpush(self.key, self.format(record))
