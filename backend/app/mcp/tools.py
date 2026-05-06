import os
import uuid
import base64
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'docx', 'xlsx', 'pptx', 'pdf', 'txt', 'md', 'csv', 'xls', 'doc', 'html', 'htm'}


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
    save_path = str(upload_dir / filename)
    with open(save_path, 'wb') as f:
        f.write(content_bytes)
    return os.path.abspath(save_path)


def _resolve_file_input(file_content: Optional[str], file_url: Optional[str],
                         file_name: str, app) -> tuple:
    if file_content:
        content_bytes = base64.b64decode(file_content)
        if not file_name:
            file_name = f"mcp_upload_{uuid.uuid4().hex[:8]}.docx"
        save_path = _save_upload_file(content_bytes, file_name, app)
        return save_path, file_name, len(content_bytes)

    elif file_url:
        import requests
        resp = requests.get(file_url, timeout=120, stream=True)
        resp.raise_for_status()
        content_bytes = resp.content
        if not file_name:
            from urllib.parse import urlparse, unquote
            file_name = unquote(urlparse(file_url).path.split('/')[-1])
            if not file_name or '.' not in file_name:
                file_name = f"mcp_download_{uuid.uuid4().hex[:8]}.docx"
        save_path = _save_upload_file(content_bytes, file_name, app)
        return save_path, file_name, len(content_bytes)

    else:
        if not file_name or not os.path.exists(file_name):
            raise ValueError(f"文件不存在: {file_name}")
        file_size = os.path.getsize(file_name)
        return file_name, os.path.basename(file_name), file_size


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

    try:
        save_path, resolved_name, file_size = _resolve_file_input(
            file_content, file_url, file_name, app
        )
    except Exception as e:
        return {'error': f'文件处理失败: {str(e)}'}

    if not _check_file_extension(resolved_name):
        return {'error': f'不支持的文件格式，仅支持: {", ".join(sorted(ALLOWED_EXTENSIONS))}'}

    try:
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
        target_path = str(target_dir / resolved_name)

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

        TranslateEngine(translate_record.id).execute()

        return {
            'task_id': translate_record.id,
            'uuid': file_uuid,
            'file_name': resolved_name,
            'target_lang': lang,
            'status': 'process',
            'message': '翻译任务已启动'
        }

    except Exception as e:
        db.session.rollback()
        logger.error(f"MCP翻译任务启动失败: {e}", exc_info=True)
        return {'error': f'翻译任务启动失败: {str(e)}'}


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

    record = Translate.query.filter_by(
        id=task_id, customer_id=customer_id, deleted_flag='N'
    ).first()
    if not record:
        return {'error': '翻译记录不存在'}
    if record.status != 'done':
        return {'error': f'翻译尚未完成，当前状态: {record.status}'}
    if not record.target_filepath or not os.path.exists(record.target_filepath):
        return {'error': '翻译文件不存在'}

    import base64 as b64
    with open(record.target_filepath, 'rb') as f:
        file_b64 = b64.b64encode(f.read()).decode()

    return {
        'task_id': record.id,
        'file_name': record.origin_filename,
        'file_content_base64': file_b64,
        'file_size': os.path.getsize(record.target_filepath),
    }


def delete_translate(customer_id: int, task_id: int) -> dict:
    from app.extensions import db
    from app.models.translate import Translate
    from app.models.customer import Customer

    record = Translate.query.filter_by(
        id=task_id, customer_id=customer_id
    ).first()
    if not record:
        return {'error': '翻译记录不存在'}

    record.deleted_flag = 'Y'
    customer = Customer.query.get(customer_id)
    if customer:
        customer.storage = max(0, customer.storage - record.size)
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

    TranslateEngine(record.id).execute()

    return {
        'task_id': record.id,
        'status': 'process',
        'message': '翻译任务已重新启动',
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
            for item in c.content.split('; '):
                if ':' in item:
                    origin, target = item.split(':', 1)
                    content_list.append({'origin': origin.strip(), 'target': target.strip()})
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

    TranslateEngine(record.id).execute()

    return {
        'task_id': record.id,
        'status': 'process',
        'message': '翻译任务已重新启动',
    }


def admin_delete_translate(task_id: int) -> dict:
    from app.extensions import db
    from app.models.translate import Translate
    from app.models.customer import Customer

    record = Translate.query.filter_by(id=task_id).first()
    if not record:
        return {'error': '翻译记录不存在'}

    record.deleted_flag = 'Y'
    if record.customer_id:
        customer = Customer.query.get(record.customer_id)
        if customer:
            customer.storage = max(0, customer.storage - record.size)
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
