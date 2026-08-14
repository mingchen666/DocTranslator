import json
import logging
import time
import uuid
from datetime import datetime

from flask import current_app, has_app_context

from app.extensions import db
from app.models.job import FailedJob, Job
from app.models.translate import Translate

logger = logging.getLogger(__name__)

DEFAULT_QUEUE = 'default'
PDF_QUEUE = 'pdf'
LEASE_SECONDS = 600
HEARTBEAT_SECONDS = 30
MAX_ATTEMPTS = 3
CELERY_DEFAULT_QUEUE = 'translation.default'
CELERY_PDF_QUEUE = 'translation.pdf'


def queue_backend_name():
    if has_app_context():
        value = current_app.config.get('TRANSLATION_QUEUE_BACKEND', 'database')
    else:
        import os
        value = os.getenv('TRANSLATION_QUEUE_BACKEND', 'database')
    value = str(value).strip().lower()
    if value not in {'database', 'celery'}:
        raise RuntimeError(
            'TRANSLATION_QUEUE_BACKEND必须是database或celery'
        )
    return value


def _celery_queue_for(queue):
    return CELERY_PDF_QUEUE if queue == PDF_QUEUE else CELERY_DEFAULT_QUEUE


def _publish_celery(task_id, batch_id, queue):
    from app.celery_app import celery

    return celery.send_task(
        'app.celery_tasks.execute_translation',
        args=[task_id, str(batch_id) if batch_id else None],
        kwargs={},
        queue=_celery_queue_for(queue),
        task_id=f'translation-{task_id}',
    )


def queue_for_task(task):
    return PDF_QUEUE if str(task.origin_filepath).lower().endswith('.pdf') else DEFAULT_QUEUE


def enqueue_translation(task_id, batch_id=None, commit=True):
    """Enqueue one translation using the configured backend."""
    task = db.session.get(Translate, task_id)
    if not task:
        raise ValueError(f'任务 {task_id} 不存在')

    queue = queue_for_task(task)
    payload = {'translate_id': task.id}
    if batch_id:
        payload['batch_id'] = str(batch_id)

    if queue_backend_name() == 'celery':
        # Celery mode publishes after the caller's task configuration has been
        # committed. Callers that are already inside a larger transaction pass
        # commit=False and commit before invoking this function.
        if commit:
            db.session.commit()
        _publish_celery(task.id, batch_id, queue)
        return True

    # Avoid duplicate pending jobs when a client retries the start request.
    for existing in Job.query.filter_by(queue=queue).all():
        try:
            existing_payload = json.loads(existing.payload)
        except (TypeError, ValueError):
            continue
        if existing_payload.get('translate_id') == task.id:
            return True

    now = int(time.time())
    db.session.add(Job(
        queue=queue,
        payload=json.dumps(payload, separators=(',', ':')),
        attempts=0,
        reserved_at=None,
        available_at=now,
        created_at=now,
    ))
    if commit:
        db.session.commit()
    return True


def claim_next_job(queue, lease_seconds=LEASE_SECONDS):
    """Claim one available job and return a detached payload."""
    for _ in range(10):
        now = int(time.time())
        stale_before = now - lease_seconds
        available = db.or_(
            Job.reserved_at.is_(None),
            Job.reserved_at < stale_before,
        )
        candidate = db.session.query(Job.id).filter(
            Job.queue == queue,
            Job.available_at <= now,
            available,
        ).order_by(Job.id.asc()).first()
        if not candidate:
            return None

        # The conditional UPDATE is the claim. If another worker won after
        # our SELECT, rowcount is zero and we retry with the next snapshot.
        updated = Job.query.filter(
            Job.id == candidate.id,
            Job.queue == queue,
            Job.available_at <= now,
            available,
        ).update({
            Job.reserved_at: now,
            Job.attempts: Job.attempts + 1,
        }, synchronize_session=False)
        if not updated:
            db.session.rollback()
            continue

        db.session.commit()
        job = db.session.get(Job, candidate.id)
        return {
            'id': job.id,
            'queue': job.queue,
            'payload': json.loads(job.payload),
            'attempts': job.attempts,
        }
    return None


def heartbeat_job(job_id):
    job = db.session.get(Job, job_id)
    if not job:
        return False
    job.reserved_at = int(time.time())
    db.session.commit()
    return True


def complete_job(job_id):
    job = db.session.get(Job, job_id)
    if job:
        db.session.delete(job)
        db.session.commit()


def retry_or_fail_job(job_id, error):
    """Release a crashed job with backoff, or persist it in failed_jobs."""
    job = db.session.get(Job, job_id)
    if not job:
        return

    message = str(error)[:4000]
    if (job.attempts or 0) < MAX_ATTEMPTS:
        delay = min(300, 2 ** max(0, job.attempts - 1) * 10)
        job.reserved_at = None
        job.available_at = int(time.time()) + delay
        db.session.commit()
        return

    db.session.add(FailedJob(
        uuid=str(uuid.uuid4()),
        connection='database',
        queue=job.queue,
        payload=job.payload,
        exception=message,
        failed_at=datetime.utcnow(),
    ))
    try:
        task_id = json.loads(job.payload).get('translate_id')
    except (TypeError, ValueError):
        task_id = None
    task = db.session.get(Translate, task_id) if task_id else None
    if task and task.status not in {'done', 'failed'}:
        task.status = 'failed'
        task.process = 0
        task.failed_reason = f'队列任务重试失败: {message}'[:500]
        task.end_at = datetime.utcnow()
    db.session.delete(job)
    db.session.commit()
