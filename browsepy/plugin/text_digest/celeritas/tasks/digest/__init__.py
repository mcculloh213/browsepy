from browsepy.plugin.text_digest.celeritas import (
    Ignore, Reject,
    celery, states,
    )
from .. import make_task_logger

logger = make_task_logger('ai.mccullough.celeritas.digest')
