import logging
import os
import signal
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from app import create_app
from app.extensions import db
from app.models.translate import Translate
from app.resources.task.translate_service import TranslateEngine
from app.task_queue import (
    DEFAULT_QUEUE,
    HEARTBEAT_SECONDS,
    PDF_QUEUE,
    claim_next_job,
    complete_job,
    heartbeat_job,
    queue_backend_name,
    retry_or_fail_job,
)

logging.basicConfig(
    level=os.environ.get('LOG_LEVEL', 'INFO'),
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
)
logger = logging.getLogger('translation-worker')


def _heartbeat(app, job_id, stop_event):
    while not stop_event.wait(HEARTBEAT_SECONDS):
        try:
            with app.app_context():
                if not heartbeat_job(job_id):
                    return
        except Exception:
            logger.exception('任务 %s 心跳更新失败', job_id)


def _process_job(app, job):
    heartbeat_stop = threading.Event()
    heartbeat = threading.Thread(
        target=_heartbeat,
        args=(app, job['id'], heartbeat_stop),
        daemon=True,
    )
    heartbeat.start()
    try:
        task_id = job['payload'].get('translate_id')
        if not task_id:
            raise ValueError('队列任务缺少 translate_id')

        with app.app_context():
            task = db.session.get(Translate, task_id)
            if not task or task.deleted_flag != 'N':
                complete_job(job['id'])
                return
            if task.status in {'done', 'failed'}:
                complete_job(job['id'])
                return
            logger.info('开始任务 %s（队列 %s）', task_id, job['queue'])
            TranslateEngine(task_id).run()
            complete_job(job['id'])
            logger.info('结束任务 %s', task_id)
    except Exception as exc:
        logger.exception('队列任务 %s 执行器异常', job['id'])
        with app.app_context():
            retry_or_fail_job(job['id'], exc)
    finally:
        heartbeat_stop.set()
        heartbeat.join(timeout=2)


def run_worker():
    app = create_app()
    with app.app_context():
        backend = queue_backend_name()
    if backend != 'database':
        logger.info(
            'TRANSLATION_QUEUE_BACKEND=%s，数据库 worker 不启动',
            backend,
        )
        return

    stop_event = threading.Event()

    def stop(_signum, _frame):
        logger.info('收到停止信号，不再领取新任务')
        stop_event.set()

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    limits = {
        DEFAULT_QUEUE: max(1, int(os.environ.get('TRANSLATE_DEFAULT_CONCURRENCY', '2'))),
        PDF_QUEUE: max(1, int(os.environ.get('TRANSLATE_PDF_CONCURRENCY', '1'))),
    }
    executors = {
        queue: ThreadPoolExecutor(max_workers=limit, thread_name_prefix=f'{queue}-job')
        for queue, limit in limits.items()
    }
    active = {queue: set() for queue in limits}
    logger.info('翻译 worker 已启动：%s', limits)

    try:
        while not stop_event.is_set():
            found_job = False
            for queue, limit in limits.items():
                completed = {future for future in active[queue] if future.done()}
                for future in completed:
                    try:
                        future.result()
                    except Exception:
                        logger.exception('worker 线程异常退出')
                active[queue] -= completed

                while len(active[queue]) < limit and not stop_event.is_set():
                    with app.app_context():
                        job = claim_next_job(queue)
                    if not job:
                        break
                    found_job = True
                    active[queue].add(executors[queue].submit(_process_job, app, job))

            if not found_job:
                stop_event.wait(0.5)
    finally:
        for executor in executors.values():
            executor.shutdown(wait=False, cancel_futures=True)
        logger.info('翻译 worker 已停止领取任务')


if __name__ == '__main__':
    run_worker()
