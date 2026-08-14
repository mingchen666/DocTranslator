import mimetypes
import shutil
import tempfile
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath

from flask import current_app

from app.utils.file_security import safe_display_filename


class ResultStorageError(RuntimeError):
    """A translation result could not be persisted or read."""


@dataclass(frozen=True)
class FinalizedResult:
    backend_name: str
    object_key: str | None = None
    local_path: str | None = None


class ResultStorage:
    backend_name = ''

    def put_file(self, local_path, object_key, content_type=None):
        raise NotImplementedError

    def open_reader(self, record):
        raise NotImplementedError

    def exists(self, record):
        raise NotImplementedError

    def delete(self, record):
        raise NotImplementedError

    def finalize_result(self, record):
        raise NotImplementedError


class LocalResultStorage(ResultStorage):
    backend_name = 'local'

    def put_file(self, local_path, object_key, content_type=None):
        if not Path(local_path).is_file():
            raise ResultStorageError('翻译结果文件不存在')

    @contextmanager
    def open_reader(self, record):
        path = getattr(record, 'target_filepath', None)
        if not path or not Path(path).is_file():
            raise FileNotFoundError('翻译结果文件不存在')
        with open(path, 'rb') as reader:
            yield reader

    def exists(self, record):
        path = getattr(record, 'target_filepath', None)
        return bool(path and Path(path).is_file())

    def delete(self, record):
        path = getattr(record, 'target_filepath', None)
        if path:
            Path(path).unlink(missing_ok=True)

    def finalize_result(self, record):
        path = getattr(record, 'target_filepath', None)
        if not path or not Path(path).is_file():
            raise ResultStorageError('翻译未生成目标文件')
        record.target_filesize = Path(path).stat().st_size
        record.target_storage_backend = self.backend_name
        record.target_storage_key = None
        return FinalizedResult(self.backend_name, local_path=str(path))


class OssResultStorage(ResultStorage):
    backend_name = 'oss'

    def __init__(self, endpoint, bucket_name, access_key_id, access_key_secret):
        try:
            import oss2
        except ImportError as exc:
            raise RuntimeError('OSS结果存储需要安装oss2依赖') from exc
        auth = oss2.Auth(access_key_id, access_key_secret)
        self._bucket = oss2.Bucket(auth, endpoint, bucket_name)

    def put_file(self, local_path, object_key, content_type=None):
        headers = {'Content-Type': content_type} if content_type else None
        result = self._bucket.put_object_from_file(
            object_key, str(local_path), headers=headers
        )
        if not 200 <= int(getattr(result, 'status', 0)) < 300:
            raise ResultStorageError('OSS上传未成功')
        if not self._bucket.object_exists(object_key):
            raise ResultStorageError('OSS上传后校验失败')

    @contextmanager
    def open_reader(self, record):
        key = _record_object_key(record)
        reader = self._bucket.get_object(key)
        try:
            yield reader
        finally:
            close = getattr(reader, 'close', None)
            if close:
                close()

    def exists(self, record):
        return self._bucket.object_exists(_record_object_key(record))

    def delete(self, record):
        key = _record_object_key(record)
        self._bucket.delete_object(key)

    def finalize_result(self, record):
        local_path = getattr(record, 'target_filepath', None)
        if not local_path or not Path(local_path).is_file():
            raise ResultStorageError('翻译未生成目标文件')
        object_key = getattr(record, 'target_storage_key', None)
        if not object_key:
            object_key = build_object_key(record)
        content_type = mimetypes.guess_type(local_path)[0]
        self.put_file(local_path, object_key, content_type)
        record.target_filesize = Path(local_path).stat().st_size
        record.target_storage_backend = self.backend_name
        record.target_storage_key = object_key
        return FinalizedResult(
            self.backend_name,
            object_key=object_key,
            local_path=str(local_path),
        )


def _record_object_key(record):
    key = getattr(record, 'target_storage_key', None)
    if not key:
        raise ResultStorageError('OSS结果缺少对象key')
    return key


def build_object_key(record, now=None):
    task_uuid = str(getattr(record, 'uuid', '') or '').strip()
    if not task_uuid:
        task_uuid = str(uuid.uuid4())
        record.uuid = task_uuid
    try:
        task_uuid = str(uuid.UUID(task_uuid))
    except ValueError as exc:
        raise ResultStorageError('翻译任务UUID无效') from exc
    filename = safe_display_filename(
        getattr(record, 'origin_filename', None)
        or Path(getattr(record, 'target_filepath', '')).name
    )
    target_suffix = Path(getattr(record, 'target_filepath', '')).suffix
    if target_suffix and Path(filename).suffix.lower() != target_suffix.lower():
        filename = f'{Path(filename).stem}{target_suffix}'
    created = now or getattr(record, 'created_at', None) or datetime.utcnow()
    prefix = current_app.config['OSS_PREFIX']
    key = PurePosixPath(
        prefix,
        created.strftime('%Y'),
        created.strftime('%m'),
        created.strftime('%d'),
        task_uuid,
        filename,
    ).as_posix()
    if '..' in PurePosixPath(key).parts or '\\' in key or key.startswith('/'):
        raise ResultStorageError('生成的对象key不安全')
    return key


def _new_oss_storage():
    return OssResultStorage(
        current_app.config['OSS_ENDPOINT'],
        current_app.config['OSS_BUCKET'],
        current_app.config['OSS_ACCESS_KEY_ID'],
        current_app.config['OSS_ACCESS_KEY_SECRET'],
    )


def get_result_storage(backend_name=None):
    backend = str(
        backend_name or current_app.config['RESULT_STORAGE_BACKEND']
    ).strip().lower()
    if backend == 'local':
        return LocalResultStorage()
    if backend == 'oss':
        return _new_oss_storage()
    raise ResultStorageError(f'不支持的结果存储后端: {backend}')


def get_record_storage(record):
    return get_result_storage(
        getattr(record, 'target_storage_backend', None) or 'local'
    )


def result_exists(record):
    return get_record_storage(record).exists(record)


def delete_result(record):
    return get_record_storage(record).delete(record)


def read_result_bytes(record):
    with get_record_storage(record).open_reader(record) as reader:
        return reader.read()


def write_result_to_zip(archive, record, archive_name):
    with get_record_storage(record).open_reader(record) as reader:
        with archive.open(archive_name, 'w') as target:
            shutil.copyfileobj(reader, target, length=1024 * 1024)


def send_result_file(record, download_name, mimetype=None):
    from flask import send_file

    storage = get_record_storage(record)
    if storage.backend_name == 'local':
        return send_file(
            record.target_filepath,
            mimetype=mimetype,
            as_attachment=True,
            download_name=download_name,
        )

    temporary_file = tempfile.SpooledTemporaryFile(
        max_size=16 * 1024 * 1024, mode='w+b'
    )
    try:
        with storage.open_reader(record) as reader:
            shutil.copyfileobj(
                reader, temporary_file, length=1024 * 1024
            )
        temporary_file.seek(0)
        response = send_file(
            temporary_file,
            mimetype=mimetype,
            as_attachment=True,
            download_name=download_name,
        )
    except Exception:
        temporary_file.close()
        raise
    response.call_on_close(temporary_file.close)
    return response


def finalize_result(record):
    return get_result_storage().finalize_result(record)


def commit_completed_result(record, end_at=None):
    from app.extensions import db

    result = None
    try:
        result = finalize_result(record)
        record.status = 'done'
        record.process = 100.00
        record.end_at = end_at or datetime.utcnow()
        db.session.commit()
    except Exception:
        db.session.rollback()
        if result is not None:
            try:
                delete_uploaded_result(result)
            except Exception as cleanup_error:
                current_app.logger.error(
                    '结果字段提交失败且OSS对象回收失败，任务ID=%s，key=%s，错误类型=%s',
                    getattr(record, 'id', None),
                    result.object_key,
                    type(cleanup_error).__name__,
                )
        raise
    cleanup_local_result(result, task_id=getattr(record, 'id', None))
    return result


def cleanup_local_result(result, task_id=None):
    if result.backend_name == 'oss' and result.local_path:
        try:
            Path(result.local_path).unlink(missing_ok=True)
        except OSError:
            current_app.logger.warning(
                'OSS结果已提交，但本地临时结果清理失败，任务ID=%s',
                task_id,
            )


def delete_uploaded_result(result):
    if result.backend_name != 'oss' or not result.object_key:
        return
    locator = type('ResultLocator', (), {
        'target_storage_key': result.object_key,
    })()
    get_result_storage('oss').delete(locator)
