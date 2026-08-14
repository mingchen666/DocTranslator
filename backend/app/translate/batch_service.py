import hashlib
import shutil
import stat
from datetime import datetime
from pathlib import Path, PurePosixPath

from app.extensions import db
from app.models.translate import Translate
from app.utils.file_security import safe_storage_path


MODERN_EXTENSIONS = {
    '.docx', '.xlsx', '.pptx', '.pdf', '.txt', '.csv', '.md', '.html', '.htm'
}
LEGACY_OFFICE_EXTENSIONS = {'.doc', '.xls', '.ppt'}


def apply_translation_values(task, values, target_path):
    task.server = values['server']
    task.target_filepath = str(target_path)
    task.model = values['model']
    task.app_key = values['app_key']
    task.app_id = values['app_id']
    task.backup_model = values['backup_model']
    task.type = values['type']
    task.prompt = values['prompt']
    task.threads = values['threads']
    task.api_url = values.get('api_url', '')
    task.api_key = values.get('api_key', '')
    task.origin_lang = values['origin_lang']
    task.comparison_id = values['comparison_id']
    task.prompt_id = values['prompt_id']
    task.doc2x_flag = values['doc2x_flag']
    task.doc2x_secret_key = values['doc2x_secret_key']
    task.lang = values['lang']
    task.status = 'none'
    task.process = 0
    task.start_at = None
    task.end_at = None
    task.failed_reason = None


def _safe_member_path(info):
    name = info.filename.replace('\\', '/')
    path = PurePosixPath(name)
    if path.is_absolute() or not path.parts:
        raise ValueError(f'ZIP包含非法路径: {info.filename}')
    if any(part in {'', '.', '..'} for part in path.parts):
        raise ValueError(f'ZIP包含非法路径: {info.filename}')
    if ':' in path.parts[0]:
        raise ValueError(f'ZIP包含非法路径: {info.filename}')
    mode = (info.external_attr >> 16) & 0xFFFF
    if mode and stat.S_ISLNK(mode):
        raise ValueError(f'ZIP不允许符号链接: {info.filename}')
    if info.flag_bits & 0x1:
        raise ValueError(f'ZIP不允许加密文件: {info.filename}')
    if path.suffix.lower() == '.zip':
        raise ValueError(f'ZIP不允许嵌套压缩包: {info.filename}')
    return path


def _unique_relative_path(path, used_paths):
    candidate = path
    index = 2
    while candidate.as_posix().lower() in used_paths:
        candidate = candidate.with_name(f'{path.stem} ({index}){path.suffix}')
        index += 1
    used_paths.add(candidate.as_posix().lower())
    return candidate


def extract_zip_documents(
    archive,
    source_root,
    target_root,
    max_files,
    max_file_size,
    max_total_size,
    max_compression_ratio,
):
    """Validate and extract supported documents without using ZipFile.extract."""
    accepted = []
    used_paths = set()
    total_size = 0

    if len(archive.infolist()) > max_files * 10:
        raise ValueError('ZIP条目数量异常')

    for info in archive.infolist():
        if info.is_dir() or info.filename.startswith('__MACOSX/'):
            continue
        relative_path = _safe_member_path(info)
        extension = relative_path.suffix.lower()
        if extension in LEGACY_OFFICE_EXTENSIONS:
            raise ValueError(
                f'暂不支持旧版Office文件，请转换为现代格式: {info.filename}'
            )
        if extension not in MODERN_EXTENSIONS:
            continue
        if info.file_size > max_file_size:
            raise ValueError(f'ZIP内文件超过大小限制: {info.filename}')
        ratio = info.file_size / max(1, info.compress_size)
        if info.file_size > 1024 * 1024 and ratio > max_compression_ratio:
            raise ValueError(f'ZIP压缩比异常: {info.filename}')

        total_size += info.file_size
        if total_size > max_total_size:
            raise ValueError('ZIP解压后总大小超过限制')
        if len(accepted) >= max_files:
            raise ValueError(f'ZIP最多允许{max_files}个文档')

        accepted.append((info, _unique_relative_path(relative_path, used_paths)))

    if not accepted:
        raise ValueError('ZIP中没有支持的文档')

    source_root = Path(source_root)
    target_root = Path(target_root)
    extracted = []
    for info, relative_path in accepted:
        source_path = safe_storage_path(source_root, *relative_path.parts)
        target_path = safe_storage_path(target_root, *relative_path.parts)
        source_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        written = 0
        digest = hashlib.md5()
        with archive.open(info) as source, source_path.open('wb') as destination:
            while True:
                chunk = source.read(1024 * 1024)
                if not chunk:
                    break
                written += len(chunk)
                if written > max_file_size or written > info.file_size:
                    raise ValueError(f'ZIP成员大小异常: {info.filename}')
                destination.write(chunk)
                digest.update(chunk)
        if written != info.file_size:
            raise ValueError(f'ZIP成员大小不一致: {info.filename}')
        extracted.append({
            'origin_filename': relative_path.name,
            'relative_path': relative_path.as_posix(),
            'source_path': str(source_path),
            'target_path': str(target_path),
            'size': written,
            'md5': digest.hexdigest(),
        })
    return extracted, total_size


def refresh_batch_status(batch):
    tasks = Translate.query.filter_by(batch_id=batch.id, deleted_flag='N').all()
    counts = {'none': 0, 'process': 0, 'done': 0, 'failed': 0}
    for task in tasks:
        counts[task.status] = counts.get(task.status, 0) + 1

    total = max(batch.total_count or 0, len(tasks))
    counts['failed'] += max(0, total - len(tasks))

    if counts['none'] or counts['process']:
        batch.status = 'process' if counts['process'] or counts['done'] else 'pending'
        batch.finished_at = None
    elif counts['done'] == total:
        batch.status = 'done'
        batch.finished_at = batch.finished_at or datetime.utcnow()
    elif counts['failed'] == total:
        batch.status = 'failed'
        batch.finished_at = batch.finished_at or datetime.utcnow()
    else:
        batch.status = 'partial'
        batch.finished_at = batch.finished_at or datetime.utcnow()
    db.session.commit()
    return counts, tasks


def remove_batch_directory(path):
    shutil.rmtree(path, ignore_errors=True)
