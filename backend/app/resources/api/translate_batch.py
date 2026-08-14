import os
import tempfile
import uuid
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath

from flask import current_app, request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource

from app.extensions import db
from app.models.customer import Customer
from app.models.setting import Setting
from app.models.translate import Translate
from app.models.translate_batch import TranslateBatch
from app.resources.api.translate import (
    TranslateStartValidationError,
    _validate_translate_start,
)
from app.task_queue import enqueue_translation, queue_backend_name
from app.translate.batch_service import (
    apply_translation_values,
    extract_zip_documents,
    refresh_batch_status,
    remove_batch_directory,
)
from app.utils.file_security import safe_display_filename, safe_storage_path
from app.utils.response import APIResponse
from app.result_storage import result_exists, write_result_to_zip


def _settings():
    rows = Setting.query.filter(
        Setting.group == 'api_setting',
        Setting.deleted_flag == 'N',
    ).all()
    return {row.alias: row.value for row in rows}


def _batch_start_values(data, customer, file_name='batch'):
    normalized = data.to_dict() if hasattr(data, 'to_dict') else dict(data)
    normalized.setdefault('uuid', 'batch')
    normalized.setdefault('file_name', file_name)
    return _validate_translate_start(normalized, customer, _settings())


def _validate_batch_sources(file_names, server):
    extensions = {Path(name).suffix.lower() for name in file_names}
    if extensions & {'.doc', '.xls', '.ppt'}:
        raise TranslateStartValidationError(
            '暂不支持旧版Office文件，请转换为.docx、.xlsx或.pptx'
        )
    if server == 'baidu' and '.pdf' in extensions:
        raise TranslateStartValidationError('百度翻译暂不支持PDF文件')


def _unique_relative_name(name, used):
    path = PurePosixPath(name)
    candidate = path
    index = 2
    while candidate.as_posix().lower() in used:
        candidate = candidate.with_name(f'{path.stem} ({index}){path.suffix}')
        index += 1
    used.add(candidate.as_posix().lower())
    return candidate.as_posix()


def _serialize_batch(batch, counts, tasks):
    return {
        'id': batch.id,
        'source_type': batch.source_type,
        'origin_filename': batch.origin_filename,
        'status': batch.status,
        'total': batch.total_count,
        'pending': counts.get('none', 0),
        'processing': counts.get('process', 0),
        'done': counts.get('done', 0),
        'failed': counts.get('failed', 0),
        'files': [{
            'task_id': task.id,
            'file_name': task.batch_relative_path or task.origin_filename,
            'status': task.status,
            'progress': float(task.process or 0),
            'failed_reason': task.failed_reason,
        } for task in tasks],
    }


class TranslateBatchCreateResource(Resource):
    @jwt_required()
    def get(self):
        batches = TranslateBatch.query.filter_by(
            customer_id=get_jwt_identity()
        ).order_by(TranslateBatch.created_at.desc()).limit(20).all()
        result = []
        for batch in batches:
            counts, tasks = refresh_batch_status(batch)
            result.append(_serialize_batch(batch, counts, tasks))
        return APIResponse.success({'batches': result})

    @jwt_required()
    def post(self):
        data = request.get_json(silent=True) or request.form
        translate_ids = data.get('translate_ids')
        if not isinstance(translate_ids, list) or not translate_ids:
            return APIResponse.error('translate_ids必须是非空数组', 400)
        if len(translate_ids) > current_app.config['BATCH_MAX_FILES']:
            return APIResponse.error('批次文件数量超过限制', 400)
        try:
            translate_ids = [int(value) for value in translate_ids]
        except (TypeError, ValueError):
            return APIResponse.error('translate_ids包含无效ID', 400)

        customer_id = get_jwt_identity()
        customer = db.session.get(Customer, customer_id)
        if not customer or customer.status == 'disabled':
            return APIResponse.error('用户状态异常', 403)
        tasks = Translate.query.filter(
            Translate.id.in_(translate_ids),
            Translate.customer_id == customer_id,
            Translate.deleted_flag == 'N',
        ).all()
        if len(tasks) != len(set(translate_ids)):
            return APIResponse.error('部分翻译记录不存在', 404)
        if any(task.status not in {'none', 'failed'} for task in tasks):
            return APIResponse.error('批次只能包含未开始或失败的任务', 400)

        batch_id = str(uuid.uuid4())
        try:
            values = _batch_start_values(data, customer)
            _validate_batch_sources(
                (task.origin_filename for task in tasks), values['server']
            )
            batch = TranslateBatch(
                id=batch_id,
                customer_id=customer_id,
                source_type='files',
                status='pending',
                total_count=len(tasks),
            )
            db.session.add(batch)
            used_names = set()
            target_root = (
                Path(current_app.root_path).parent / 'storage' / 'translate'
                / datetime.now().strftime('%Y-%m-%d')
            )
            target_root.mkdir(parents=True, exist_ok=True)
            for task in tasks:
                task.batch_id = batch_id
                task.batch_relative_path = _unique_relative_name(
                    task.origin_filename, used_names
                )
                target_path = safe_storage_path(
                    target_root, Path(task.origin_filepath).name
                )
                apply_translation_values(task, values, target_path)
            db.session.flush()
            if queue_backend_name() == 'celery':
                db.session.commit()
                for task in tasks:
                    try:
                        enqueue_translation(task.id, batch_id=batch_id, commit=False)
                    except Exception as exc:
                        task.status = 'failed'
                        task.process = 0
                        task.end_at = datetime.utcnow()
                        task.failed_reason = f'任务入队失败: {exc}'[:500]
                db.session.commit()
            else:
                for task in tasks:
                    enqueue_translation(task.id, batch_id=batch_id, commit=False)
                db.session.commit()
            return APIResponse.success({'batch_id': batch_id, 'queued': True})
        except TranslateStartValidationError as exc:
            db.session.rollback()
            return APIResponse.error(str(exc), 400)
        except Exception as exc:
            db.session.rollback()
            current_app.logger.error('创建翻译批次失败: %s', exc, exc_info=True)
            return APIResponse.error('创建翻译批次失败', 500)


class TranslateBatchZipResource(Resource):
    @jwt_required()
    def post(self):
        upload = request.files.get('file')
        if not upload or not upload.filename:
            return APIResponse.error('请选择ZIP文件', 400)
        try:
            filename = safe_display_filename(upload.filename)
        except ValueError as exc:
            return APIResponse.error(str(exc), 400)
        if Path(filename).suffix.lower() != '.zip':
            return APIResponse.error('仅支持ZIP批量文件', 400)

        customer_id = get_jwt_identity()
        customer = db.session.get(Customer, customer_id)
        if not customer or customer.status == 'disabled':
            return APIResponse.error('用户状态异常', 403)

        batch_id = str(uuid.uuid4())
        batch_root = Path(current_app.root_path).parent / 'storage' / 'batches' / batch_id
        try:
            values = _batch_start_values(request.form, customer, filename)
            upload.stream.seek(0, os.SEEK_END)
            archive_size = upload.stream.tell()
            upload.stream.seek(0)
            if archive_size > current_app.config['MAX_FILE_SIZE']:
                return APIResponse.error('ZIP文件超过大小限制', 400)
            remaining_storage = max(0, customer.total_storage - customer.storage)
            max_total = min(
                current_app.config['BATCH_MAX_UNCOMPRESSED_SIZE'],
                remaining_storage,
            )
            if max_total <= 0:
                return APIResponse.error('用户存储空间不足', 403)

            with zipfile.ZipFile(upload.stream) as archive:
                extracted, total_size = extract_zip_documents(
                    archive,
                    batch_root / 'source',
                    batch_root / 'result',
                    max_files=current_app.config['BATCH_MAX_FILES'],
                    max_file_size=current_app.config['MAX_FILE_SIZE'],
                    max_total_size=max_total,
                    max_compression_ratio=current_app.config['BATCH_MAX_COMPRESSION_RATIO'],
                )
            _validate_batch_sources(
                (item['origin_filename'] for item in extracted), values['server']
            )

            batch = TranslateBatch(
                id=batch_id,
                customer_id=customer_id,
                source_type='zip',
                origin_filename=filename,
                status='pending',
                total_count=len(extracted),
            )
            db.session.add(batch)
            tasks = []
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            for index, item in enumerate(extracted, start=1):
                task = Translate(
                    translate_no=f'B{timestamp}{index:02d}',
                    uuid=str(uuid.uuid4()),
                    customer_id=customer_id,
                    origin_filename=item['origin_filename'],
                    origin_filepath=item['source_path'],
                    target_filepath=item['target_path'],
                    status='none',
                    deleted_flag='N',
                    origin_filesize=item['size'],
                    size=item['size'],
                    md5=item['md5'],
                    batch_id=batch_id,
                    batch_relative_path=item['relative_path'],
                    created_at=datetime.utcnow(),
                )
                apply_translation_values(task, values, item['target_path'])
                db.session.add(task)
                tasks.append(task)
            customer.storage += total_size
            db.session.flush()
            if queue_backend_name() == 'celery':
                db.session.commit()
                for task in tasks:
                    try:
                        enqueue_translation(task.id, batch_id=batch_id, commit=False)
                    except Exception as exc:
                        task.status = 'failed'
                        task.process = 0
                        task.end_at = datetime.utcnow()
                        task.failed_reason = f'任务入队失败: {exc}'[:500]
                db.session.commit()
            else:
                for task in tasks:
                    enqueue_translation(task.id, batch_id=batch_id, commit=False)
                db.session.commit()
            return APIResponse.success({
                'batch_id': batch_id,
                'queued': True,
                'total': len(tasks),
            })
        except (TranslateStartValidationError, ValueError, zipfile.BadZipFile) as exc:
            db.session.rollback()
            remove_batch_directory(batch_root)
            return APIResponse.error(str(exc), 400)
        except Exception as exc:
            db.session.rollback()
            remove_batch_directory(batch_root)
            current_app.logger.error('ZIP批量翻译创建失败: %s', exc, exc_info=True)
            return APIResponse.error('ZIP批量翻译创建失败', 500)


class TranslateBatchDetailResource(Resource):
    @jwt_required()
    def get(self, batch_id):
        batch = TranslateBatch.query.filter_by(
            id=batch_id, customer_id=get_jwt_identity()
        ).first_or_404()
        counts, tasks = refresh_batch_status(batch)
        return APIResponse.success(_serialize_batch(batch, counts, tasks))


class TranslateBatchDownloadResource(Resource):
    @jwt_required()
    def get(self, batch_id):
        batch = TranslateBatch.query.filter_by(
            id=batch_id, customer_id=get_jwt_identity()
        ).first_or_404()
        counts, tasks = refresh_batch_status(batch)
        if counts['none'] or counts['process']:
            return APIResponse.error('批次尚未完成', 409)
        completed = [
            task for task in tasks
            if task.status == 'done'
        ]
        if not completed:
            return APIResponse.error('批次没有可下载的成功文件', 409)

        archive_file = tempfile.SpooledTemporaryFile(
            max_size=16 * 1024 * 1024, mode='w+b'
        )
        used_names = set()
        try:
            with zipfile.ZipFile(archive_file, 'w', zipfile.ZIP_DEFLATED) as archive:
                for task in completed:
                    if not result_exists(task):
                        raise FileNotFoundError(
                            f'翻译结果不存在，任务ID={task.id}'
                        )
                    archive_name = _unique_relative_name(
                        task.batch_relative_path or task.origin_filename, used_names
                    )
                    write_result_to_zip(archive, task, archive_name)
        except Exception as exc:
            archive_file.close()
            current_app.logger.error(
                '批次结果读取失败，批次ID=%s，错误类型=%s',
                batch.id,
                type(exc).__name__,
            )
            return APIResponse.error('批次结果读取失败', 502)
        archive_file.seek(0)
        download_name = (
            batch.origin_filename
            if batch.source_type == 'zip' and batch.origin_filename
            else f'translations_{batch.id[:8]}.zip'
        )
        return send_file(
            archive_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=download_name,
        )
