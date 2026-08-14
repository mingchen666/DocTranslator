"""Lazy Celery application configuration for the optional queue backend."""

import os

from celery import Celery
from app.config import Config


def _broker_url():
    value = os.getenv('CELERY_BROKER_URL', Config.CELERY_BROKER_URL).strip()
    if not value:
        raise RuntimeError(
            'TRANSLATION_QUEUE_BACKEND=celery时必须设置CELERY_BROKER_URL'
        )
    return value


celery = Celery('doctranslator', broker=_broker_url())
celery.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_ignore_result=True,
    task_track_started=False,
    worker_cancel_long_running_tasks_on_connection_loss=True,
    broker_transport_options={
        'visibility_timeout': int(
            os.getenv('CELERY_VISIBILITY_TIMEOUT', '21600')
        ),
    },
    task_routes={
        'app.celery_tasks.execute_translation': {
            'queue': 'translation.default',
        },
    },
)

# Register tasks without importing Celery from database-mode request code.
from app.celery_tasks import register_tasks  # noqa: E402

register_tasks(celery)
