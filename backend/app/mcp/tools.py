import os
import uuid
import base64
import binascii
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.utils.file_security import (
    download_public_url,
    safe_storage_path,
    stored_filename,
)

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {
    'docx', 'xlsx', 'pptx', 'pdf', 'txt', 'md', 'csv', 'html', 'htm'
}


def _check_file_extension(filename: str) -> bool:
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def _save_upload_file(content_bytes: bytes, filename: str, app) -> str:
    base_dir = Path(app.root_path).parent.absolute()
    date_str = datetime.now().strftime('%Y-%m-%d')
    upload_dir = base_dir / "storage" / "uploads" / date_str
    upload_dir.mkdir(parents=True, exist_ok=True)
    _, disk_name = stored_filename(filename)
    save_path = safe_storage_path(upload_dir, disk_name)
    with open(save_path, 'wb') as f:
        f.write(content_bytes)
    return os.path.abspath(save_path)


def _decode_base64_file(file_content: str, max_bytes: int) -> bytes:
    if not isinstance(file_content, str):
        raise ValueError('文件内容必须是Base64字符串')

    max_encoded_length = ((max_bytes + 2) // 3) * 4
    if len(file_content) > max_encoded_length:
        raise ValueError('文件超过大小限制')

    try:
        content_bytes = base64.b64decode(file_content, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError('文件内容不是有效的Base64编码') from exc

    if len(content_bytes) > max_bytes:
        raise ValueError('文件超过大小限制')
    return content_bytes


def _remove_upload_file(save_path: Optional[str]) -> None:
    if not save_path:
        return
    try:
        Path(save_path).unlink(missing_ok=True)
    except OSError:
        logger.warning('清理MCP上传文件失败: %s', save_path, exc_info=True)


def _resolve_file_input(file_content: Optional[str], file_url: Optional[str],
                         file_name: str, app) -> tuple:
    max_file_size = int(app.config['MAX_FILE_SIZE'])
    if file_content:
        content_bytes = _decode_base64_file(file_content, max_file_size)
        if not file_name:
            file_name = f"mcp_upload_{uuid.uuid4().hex[:8]}.docx"
        save_path = _save_upload_file(content_bytes, file_name, app)
        return save_path, file_name, len(content_bytes)

    elif file_url:
        content_bytes, url_name = download_public_url(
            file_url,
            max_file_size,
        )
        if not file_name:
            file_name = url_name
            if not file_name or '.' not in file_name:
                file_name = f"mcp_download_{uuid.uuid4().hex[:8]}.docx"
        save_path = _save_upload_file(content_bytes, file_name, app)
        return save_path, file_name, len(content_bytes)

    raise ValueError('请提供 file_content 或 file_url')


def translate_file(config: dict, customer_id: int, app,
                   file_content: str = None, file_url: str = None,
                   file_name: str = "", target_lang: str = "",
                   origin_lang: str = "", translate_type: str = "",
                   comparison_id: int = None) -> dict:
    from app.extensions import db
    from app.models.customer import Customer
    from app.models.translate import Translate
    from app.models.comparison import Comparison
    from app.models.prompt import Prompt
    from app.resources.task.translate_service import TranslateEngine

    mcp_config = config

    if target_lang:
        lang = target_lang
    else:
        lang = mcp_config.get('lang', '中文')

    if translate_type:
        trans_type = translate_type
    else:
        trans_type = mcp_config.get('type', 'trans_all_only_inherit')

    effective_comparison_id = comparison_id or mcp_config.get('comparison_id')

    effective_prompt_id = mcp_config.get('prompt_id', 0)
    effective_prompt = mcp_config.get('prompt', '')

    if effective_prompt_id and effective_prompt_id != 0:
        prompt_obj = Prompt.query.filter_by(id=effective_prompt_id, deleted_flag='N').first()
        if prompt_obj and prompt_obj.content:
            effective_prompt = prompt_obj.content

    if not effective_prompt:
        effective_prompt = '你是一个文档翻译助手，请将以下文本、单词或短语直接翻译成{target_lang}，不返回原文本。如果文本中包含{target_lang}文本、特殊名词（比如邮箱、品牌名、单位名词如mm、px、℃等）、无法翻译等特殊情况，请直接返回原文而无需解释原因。遇到无法翻译的文本直接返回原内容。保留多余空格。'

    save_path = None
    record_persisted = False
    try:
        try:
            save_path, resolved_name, file_size = _resolve_file_input(
                file_content, file_url, file_name, app
            )
        except Exception as e:
            return {'error': f'文件处理失败: {str(e)}'}

        if not _check_file_extension(resolved_name):
            return {'error': f'不支持的文件格式，仅支持: {", ".join(sorted(ALLOWED_EXTENSIONS))}'}
        if (
            Path(resolved_name).suffix.lower() == '.pdf'
            and str(mcp_config.get('server', 'openai')).lower() == 'baidu'
        ):
            return {'error': '百度翻译暂不支持PDF文件'}
        if file_size > int(app.config['MAX_FILE_SIZE']):
            return {'error': '文件超过大小限制'}

        customer = Customer.query.get(customer_id)
        if not customer:
            return {'error': '用户不存在'}
        if customer.status == 'disabled':
            return {'error': '用户已被禁用'}
        if customer.storage + file_size > customer.total_storage:
            return {'error': '用户存储空间不足'}

        file_uuid = str(uuid.uuid4())

        base_dir = Path(app.root_path).parent.absolute()
        date_str = datetime.now().strftime('%Y-%m-%d')
        target_dir = base_dir / "storage" / "translate" / date_str
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = str(safe_storage_path(target_dir, Path(save_path).name))

        translate_record = Translate(
            translate_no=f"TRANS{datetime.now().strftime('%Y%m%d%H%M%S')}",
            uuid=file_uuid,
            customer_id=customer_id,
            origin_filename=resolved_name,
            origin_filepath=os.path.abspath(save_path),
            target_filepath=target_path,
            status='none',
            origin_filesize=file_size,
            size=file_size,
            created_at=datetime.utcnow(),
            server='openai',
            model=mcp_config.get('model', ''),
            backup_model=mcp_config.get('backup_model', ''),
            api_url=mcp_config.get('api_url', ''),
            api_key=mcp_config.get('api_key', ''),
            prompt=effective_prompt,
            threads=int(mcp_config.get('threads', 5)),
            type=trans_type,
            lang=lang,
            origin_lang=origin_lang or '',
            comparison_id=int(effective_comparison_id) if effective_comparison_id else None,
            prompt_id=int(effective_prompt_id) if effective_prompt_id else None,
            doc2x_flag=mcp_config.get('doc2x_flag', 'N'),
            doc2x_secret_key=mcp_config.get('doc2x_secret_key', ''),
        )

        customer.storage += file_size
        db.session.add(translate_record)
        db.session.commit()
        record_persisted = True

        if not TranslateEngine(translate_record.id).execute():
            return {
                'task_id': translate_record.id,
                'status': 'failed',
                'error': '翻译任务入队失败',
            }

        return {
            'task_id': translate_record.id,
            'uuid': file_uuid,
            'file_name': resolved_name,
            'target_lang': lang,
            'status': 'none',
            'message': '翻译任务已加入队列'
        }

    except Exception as e:
        db.session.rollback()
        logger.error(f"MCP翻译任务启动失败: {e}", exc_info=True)
        return {'error': f'翻译任务启动失败: {str(e)}'}
    finally:
        if not record_persisted:
            _remove_upload_file(save_path)


def query_translate_status(customer_id: int, task_id: int = None,
                            uuid: str = None) -> dict:
    from app.models.translate import Translate

    query = Translate.query.filter_by(customer_id=customer_id, deleted_flag='N')

    if task_id:
        query = query.filter_by(id=task_id)
    elif uuid:
        query = query.filter_by(uuid=uuid)
    else:
        return {'error': '请提供 task_id 或 uuid'}

    record = query.first()
    if not record:
        return {'error': '翻译记录不存在'}

    status_map = {'none': '未开始', 'process': '进行中', 'done': '已完成', 'failed': '失败'}
    spend_time = '--'
    if record.start_at and record.end_at:
        total_seconds = (record.end_at - record.start_at).total_seconds()
        minutes = int(total_seconds // 60)
        seconds = int(total_seconds % 60)
        spend_time = f"{minutes}分{seconds}秒"

    return {
        'task_id': record.id,
        'uuid': record.uuid,
        'file_name': record.origin_filename,
        'status': record.status,
        'status_name': status_map.get(record.status, '未知'),
        'progress': float(record.process),
        'target_lang': record.lang,
        'spend_time': spend_time,
        'failed_reason': record.failed_reason,
    }


def list_translates(customer_id: int, page: int = 1, limit: int = 20,
                     status: str = None, keyword: str = None) -> dict:
    from app.models.translate import Translate

    query = Translate.query.filter_by(customer_id=customer_id, deleted_flag='N')
    if status and status in ('none', 'process', 'done', 'failed'):
        query = query.filter_by(status=status)
    if keyword:
        query = query.filter(
            Translate.origin_filename.like(f'%{keyword}%')
        )
    query = query.order_by(Translate.created_at.desc())
    pagination = query.paginate(page=page, per_page=limit, error_out=False)

    status_map = {'none': '未开始', 'process': '进行中', 'done': '已完成', 'failed': '失败'}
    data = []
    for t in pagination.items:
        data.append({
            'task_id': t.id,
            'uuid': t.uuid,
            'file_name': t.origin_filename,
            'status': t.status,
            'status_name': status_map.get(t.status, '未知'),
            'progress': float(t.process),
            'target_lang': t.lang,
        })

    return {
        'data': data,
        'total': pagination.total,
        'page': page,
    }


def download_translate(customer_id: int, task_id: int) -> dict:
    from app.models.translate import Translate
    from app.result_storage import read_result_bytes, result_exists

    record = Translate.query.filter_by(
        id=task_id, customer_id=customer_id, deleted_flag='N'
    ).first()
    if not record:
        return {'error': '翻译记录不存在'}
    if record.status != 'done':
        return {'error': f'翻译尚未完成，当前状态: {record.status}'}
    try:
        exists = result_exists(record)
        content = read_result_bytes(record) if exists else None
    except Exception as exc:
        logger.error(
            'MCP读取翻译结果失败，任务ID=%s，错误类型=%s',
            record.id,
            type(exc).__name__,
        )
        return {'error': '翻译文件读取失败'}
    if not exists:
        return {'error': '翻译文件不存在'}

    import base64 as b64
    file_b64 = b64.b64encode(content).decode()

    return {
        'task_id': record.id,
        'file_name': record.origin_filename,
        'file_content_base64': file_b64,
        'file_size': record.target_filesize or len(content),
    }


def delete_translate(customer_id: int, task_id: int) -> dict:
    from app.extensions import db
    from app.models.translate import Translate
    from app.models.customer import Customer
    from app.result_storage import delete_result

    record = Translate.query.filter_by(
        id=task_id, customer_id=customer_id, deleted_flag='N'
    ).first()
    if not record:
        return {'error': '翻译记录不存在'}

    try:
        delete_result(record)
    except Exception as exc:
        logger.error(
            'MCP删除翻译结果失败，任务ID=%s，错误类型=%s',
            record.id,
            type(exc).__name__,
        )
        return {'error': '结果文件删除失败'}
    record.deleted_flag = 'Y'
    customer = Customer.query.get(customer_id)
    if customer:
        customer.storage = max(0, customer.storage - (record.size or 0))
    db.session.commit()
    return {'message': '删除成功'}


def restart_translate(customer_id: int, task_id: int) -> dict:
    from app.extensions import db
    from app.models.translate import Translate
    from app.resources.task.translate_service import TranslateEngine

    record = Translate.query.filter_by(
        id=task_id, customer_id=customer_id, deleted_flag='N'
    ).first()
    if not record:
        return {'error': '翻译记录不存在'}
    if record.status not in ('failed', 'none'):
        return {'error': f'当前状态为 {record.status}，仅失败或未开始的任务可重启'}

    record.status = 'none'
    record.failed_reason = None
    db.session.commit()

    if not TranslateEngine(record.id).execute():
        return {'task_id': record.id, 'status': 'failed', 'error': '翻译任务入队失败'}

    return {
        'task_id': record.id,
        'status': 'none',
        'message': '翻译任务已重新加入队列',
    }


def list_comparisons(customer_id: int) -> dict:
    from app.models.comparison import Comparison

    comparisons = Comparison.query.filter_by(
        customer_id=customer_id, deleted_flag='N'
    ).all()
    data = []
    for c in comparisons:
        content_list = []
        if c.content:
            for item in c.content.split(';'):
                item = item.strip()
                if ':' in item:
                    origin, target = item.split(':', 1)
                    origin = origin.strip()
                    target = target.strip()
                    if origin and target:
                        content_list.append({'origin': origin, 'target': target})
        data.append({
            'id': c.id,
            'title': c.title,
            'origin_lang': c.origin_lang,
            'target_lang': c.target_lang,
            'terms_count': len(content_list),
        })
    return {'data': data, 'total': len(data)}


def list_prompts(customer_id: int) -> dict:
    from app.models.prompt import Prompt

    prompts = Prompt.query.filter_by(
        customer_id=customer_id, deleted_flag='N'
    ).all()
    data = []
    for p in prompts:
        data.append({
            'id': p.id,
            'title': p.title,
            'share_flag': p.share_flag,
        })
    return {'data': data, 'total': len(data)}


def get_account_info(customer_id: int) -> dict:
    from app.models.customer import Customer

    customer = Customer.query.get(customer_id)
    if not customer:
        return {'error': '用户不存在'}

    storage_mb = round(customer.storage / (1024 * 1024), 2)
    total_mb = round(customer.total_storage / (1024 * 1024), 2)

    return {
        'email': customer.email,
        'name': customer.name,
        'level': customer.level,
        'storage_mb': storage_mb,
        'total_storage_mb': total_mb,
        'storage_usage': f"{storage_mb}MB / {total_mb}MB",
    }


def get_supported_formats() -> dict:
    return {
        'formats': sorted(ALLOWED_EXTENSIONS),
        'max_file_size_mb': 30,
        'description': '支持的文件格式列表'
    }


def get_statistics() -> dict:
    from app.extensions import db
    from app.models.customer import Customer
    from app.models.translate import Translate

    total_users = Customer.query.filter_by(deleted_flag='N').count()
    total_translates = Translate.query.filter_by(deleted_flag='N').count()
    process_translates = Translate.query.filter_by(status='process', deleted_flag='N').count()
    done_translates = Translate.query.filter_by(status='done', deleted_flag='N').count()
    failed_translates = Translate.query.filter_by(status='failed', deleted_flag='N').count()
    total_storage = db.session.query(
        db.func.sum(Customer.storage)
    ).filter_by(deleted_flag='N').scalar() or 0

    return {
        'total_users': total_users,
        'total_translates': total_translates,
        'process_translates': process_translates,
        'done_translates': done_translates,
        'failed_translates': failed_translates,
        'total_storage_mb': round(total_storage / (1024 * 1024), 2),
    }


def list_customers(page: int = 1, limit: int = 20, search: str = '') -> dict:
    from app.extensions import db
    from app.models.customer import Customer

    query = Customer.query.filter_by(deleted_flag='N')
    if search:
        query = query.filter(
            db.or_(
                Customer.email.like(f'%{search}%'),
                Customer.name.like(f'%{search}%'),
            )
        )
    query = query.order_by(Customer.created_at.desc())
    pagination = query.paginate(page=page, per_page=limit, error_out=False)

    data = []
    for c in pagination.items:
        storage_mb = round(c.storage / (1024 * 1024), 2)
        total_mb = round(c.total_storage / (1024 * 1024), 2)
        data.append({
            'id': c.id,
            'email': c.email,
            'name': c.name,
            'level': c.level,
            'status': c.status,
            'storage_mb': storage_mb,
            'total_storage_mb': total_mb,
            'created_at': str(c.created_at) if c.created_at else '',
        })

    return {
        'data': data,
        'total': pagination.total,
        'page': page,
    }


def update_customer(customer_id: int, level: str = '',
                     add_storage_mb: int = 0, status: str = '') -> dict:
    from app.extensions import db
    from app.models.customer import Customer

    customer = Customer.query.get(customer_id)
    if not customer:
        return {'error': '用户不存在'}

    if level and level in ('common', 'vip'):
        customer.level = level
    if add_storage_mb > 0:
        customer.total_storage += add_storage_mb * 1024 * 1024
    if status and status in ('enabled', 'disabled'):
        customer.status = status

    db.session.commit()

    return {
        'id': customer.id,
        'email': customer.email,
        'level': customer.level,
        'status': customer.status,
        'total_storage_mb': round(customer.total_storage / (1024 * 1024), 2),
        'message': '更新成功',
    }


def admin_list_translates(page: int = 1, limit: int = 20,
                           status: str = '', keyword: str = '') -> dict:
    from app.extensions import db
    from app.models.translate import Translate

    query = Translate.query.filter_by(deleted_flag='N')
    if status and status in ('none', 'process', 'done', 'failed'):
        query = query.filter_by(status=status)
    if keyword:
        query = query.filter(
            db.or_(
                Translate.origin_filename.like(f'%{keyword}%'),
                Translate.translate_no.like(f'%{keyword}%'),
            )
        )
    query = query.order_by(Translate.created_at.desc())
    pagination = query.paginate(page=page, per_page=limit, error_out=False)

    status_map = {'none': '未开始', 'process': '进行中', 'done': '已完成', 'failed': '失败'}
    data = []
    for t in pagination.items:
        data.append({
            'task_id': t.id,
            'translate_no': t.translate_no,
            'customer_id': t.customer_id,
            'file_name': t.origin_filename,
            'status': t.status,
            'status_name': status_map.get(t.status, '未知'),
            'progress': float(t.process),
            'target_lang': t.lang,
            'model': t.model,
            'created_at': str(t.created_at) if t.created_at else '',
        })

    return {
        'data': data,
        'total': pagination.total,
        'page': page,
    }


def admin_restart_translate(task_id: int) -> dict:
    from app.extensions import db
    from app.models.translate import Translate
    from app.resources.task.translate_service import TranslateEngine

    record = Translate.query.filter_by(id=task_id, deleted_flag='N').first()
    if not record:
        return {'error': '翻译记录不存在'}

    record.status = 'none'
    record.failed_reason = None
    db.session.commit()

    if not TranslateEngine(record.id).execute():
        return {'task_id': record.id, 'status': 'failed', 'error': '翻译任务入队失败'}

    return {
        'task_id': record.id,
        'status': 'none',
        'message': '翻译任务已重新加入队列',
    }


def admin_delete_translate(task_id: int) -> dict:
    from app.extensions import db
    from app.models.translate import Translate
    from app.models.customer import Customer
    from app.result_storage import delete_result

    record = Translate.query.filter_by(id=task_id, deleted_flag='N').first()
    if not record:
        return {'error': '翻译记录不存在'}

    try:
        delete_result(record)
    except Exception as exc:
        logger.error(
            '管理员MCP删除翻译结果失败，任务ID=%s，错误类型=%s',
            record.id,
            type(exc).__name__,
        )
        return {'error': '结果文件删除失败'}
    record.deleted_flag = 'Y'
    if record.customer_id:
        customer = Customer.query.get(record.customer_id)
        if customer:
            customer.storage = max(0, customer.storage - (record.size or 0))
    db.session.commit()
    return {'message': '删除成功'}


def get_system_settings() -> dict:
    from app.extensions import db
    from app.models.setting import Setting

    settings = Setting.query.filter_by(deleted_flag='N').all()
    data = {}
    for s in settings:
        if s.group:
            if s.group not in data:
                data[s.group] = {}
            data[s.group][s.alias] = s.value
        else:
            data[s.alias] = s.value

    return {'data': data}


def get_storage_info() -> dict:
    from app.extensions import db
    from app.models.customer import Customer
    from app.models.translate import Translate
    from pathlib import Path

    total_users_storage = db.session.query(
        db.func.sum(Customer.storage)
    ).filter_by(deleted_flag='N').scalar() or 0

    total_translates = Translate.query.filter_by(deleted_flag='N').count()

    base_dir = Path(__file__).parent.parent.parent / "storage"
    storage_exists = base_dir.exists()

    return {
        'total_user_storage_mb': round(total_users_storage / (1024 * 1024), 2),
        'total_translates': total_translates,
        'storage_dir': str(base_dir),
        'storage_exists': storage_exists,
    }
