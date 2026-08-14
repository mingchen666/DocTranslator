"""Celery task entry points for translation execution."""

from datetime import datetime
import os
import threading

from celery.exceptions import Retry
from redis import Redis

from app import create_app
from app.config import Config
from app.extensions import db
from app.models.translate import Translate
from app.resources.task.translate_service import TranslateEngine


def _redelivered(request):
    return bool((request.delivery_info or {}).get('redelivered'))


def _translation_lock(task_id):
    url = os.getenv('CELERY_BROKER_URL', Config.CELERY_BROKER_URL)
    client = Redis.from_url(
        url,
        socket_connect_timeout=5,
        socket_timeout=5,
    )
    key = f'doctranslator:translation-lock:{task_id}'
    lock = client.lock(
        key,
        timeout=Config.CELERY_LOCK_TIMEOUT,
        thread_local=False,
    )
    if not lock.acquire(blocking=False):
        return None
    return lock


def _refresh_lock(lock, stop_event):
    interval = max(10, Config.CELERY_LOCK_TIMEOUT // 3)
    while not stop_event.wait(interval):
        try:
            if not lock.extend(
                Config.CELERY_LOCK_TIMEOUT,
                replace_ttl=True,
            ):
                return
        except Exception:
            return


def register_tasks(celery):
    """Register the bound task on a supplied Celery application."""
    @celery.task(
        bind=True,
        name='app.celery_tasks.execute_translation',
        acks_late=True,
        reject_on_worker_lost=True,
        ignore_result=True,
        max_retries=Config.CELERY_MAX_RETRIES,
    )
    def execute_translation(self, task_id, batch_id=None):
        app = create_app()
        redelivered = _redelivered(self.request)
        lock = None
        heartbeat_stop = threading.Event()
        heartbeat = None
        try:
            lock = _translation_lock(task_id)
            if lock is None:
                if redelivered:
                    raise self.retry(
                        countdown=max(15, Config.CELERY_LOCK_TIMEOUT // 2),
                        max_retries=100,
                    )
                return {'status': 'already-running'}
            heartbeat = threading.Thread(
                target=_refresh_lock,
                args=(lock, heartbeat_stop),
                daemon=True,
                name=f'celery-lock-{task_id}',
            )
            heartbeat.start()
            # A normal duplicate sees process and exits; a broker-redelivered
            # task may reclaim it after the previous worker was lost.
            with app.app_context():
                record = db.session.get(Translate, task_id)
                if not record or record.deleted_flag != 'N':
                    return
                if record.status in {'done', 'failed'}:
                    return
                if record.status == 'process' and not _redelivered(self.request):
                    return
                if record.status == 'process':
                    record.status = 'none'
                    record.process = 0
                    record.failed_reason = None
                    db.session.commit()
                return TranslateEngine(task_id).run()
        except Retry:
            raise
        except Exception as exc:
            if self.request.retries >= self.max_retries:
                try:
                    with app.app_context():
                        db.session.rollback()
                        record = db.session.get(Translate, task_id)
                        if record and record.status not in {'done', 'failed'}:
                            record.status = 'failed'
                            record.process = 0
                            record.failed_reason = f'Celery任务重试失败: {exc}'[:500]
                            record.end_at = datetime.utcnow()
                            db.session.commit()
                except Exception:
                    pass
                raise
            raise self.retry(
                exc=exc,
                countdown=min(300, 10 * (2 ** self.request.retries)),
            )
        finally:
            heartbeat_stop.set()
            if heartbeat is not None:
                heartbeat.join(timeout=2)
            if lock is not None:
                try:
                    lock.release()
                except Exception:
                    pass

    return execute_translation
