from browsepy.plugin.text_digest.logging import make_logger


def make_task_logger(import_name):
    return make_logger(import_name, 'celeritas')

logger = make_task_logger('ai.mccullough.celeritas')
