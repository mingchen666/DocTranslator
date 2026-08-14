# resources/to_translate.py
import json
from pathlib import Path
from flask import request, send_file, current_app, make_response
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import tempfile
import zipfile
import os
from app import db, Setting
from app.models import Customer
from app.models.translate import Translate
from app.utils.response import APIResponse
from app.utils.file_security import safe_storage_path
from app.utils.check_utils import AIChecker
from app.result_storage import (
    delete_result,
    result_exists,
    send_result_file,
    write_result_to_zip,
)


class TranslateStartValidationError(ValueError):
    """Client-supplied translation start data is invalid."""


def _required_form_text(data, field):
    value = data.get(field)
    if value is None or not str(value).strip():
        raise TranslateStartValidationError(f"{field}不能为空")
    return str(value).strip()


def _optional_non_negative_int(data, field, default=None):
    value = data.get(field)
    if value is None or str(value).strip() == '':
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise TranslateStartValidationError(f"{field}必须是整数") from exc
    if parsed < 0:
        raise TranslateStartValidationError(f"{field}不能为负数")
    return parsed


def _required_int_range(data, field, minimum, maximum):
    value = _required_form_text(data, field)
    try:
        parsed = int(value)
    except ValueError as exc:
        raise TranslateStartValidationError(f"{field}必须是整数") from exc
    if not minimum <= parsed <= maximum:
        raise TranslateStartValidationError(f"{field}必须在{minimum}到{maximum}之间")
    return parsed


def _parse_form_bool(data, field, default=False):
    value = data.get(field)
    if value is None or str(value).strip() == '':
        return default
    normalized = str(value).strip().lower()
    if normalized in {'1', 'true', 'yes', 'y', 'on'}:
        return True
    if normalized in {'0', 'false', 'no', 'n', 'off'}:
        return False
    raise TranslateStartValidationError(f"{field}必须是布尔值")


def _validate_translate_start(data, customer, settings):
    """Validate and normalize start parameters before mutating a task."""
    server = _required_form_text(data, 'server').lower()
    if server not in {'openai', 'baidu'}:
        raise TranslateStartValidationError("不支持的翻译服务")

    values = {
        'server': server,
        'model': _required_form_text(data, 'model'),
        'uuid': _required_form_text(data, 'uuid'),
        'prompt': _required_form_text(data, 'prompt'),
        'file_name': _required_form_text(data, 'file_name'),
        'threads': _required_int_range(data, 'threads', 1, 10),
        'prompt_id': _optional_non_negative_int(data, 'prompt_id'),
        'comparison_id': _optional_non_negative_int(data, 'comparison_id'),
        'origin_lang': data.get('origin_lang', ''),
        'type': data.get('type[2]', 'trans_all_only_inherit'),
        'doc2x_flag': data.get('doc2x_flag', 'N'),
        'doc2x_secret_key': data.get('doc2x_secret_key', ''),
        'app_id': data.get('app_id'),
        'app_key': data.get('app_key'),
        'backup_model': str(data.get('backup_model') or '').strip(),
    }

    extension = Path(values['file_name']).suffix.lower()
    if extension in {'.doc', '.xls', '.ppt'}:
        raise TranslateStartValidationError(
            '暂不支持旧版Office文件，请转换为.docx、.xlsx或.pptx'
        )
    if server == 'baidu' and extension == '.pdf':
        raise TranslateStartValidationError('百度翻译暂不支持PDF文件')

    if server == 'openai':
        values['lang'] = _required_form_text(data, 'lang')
        if customer.level == 'vip':
            values['api_url'] = str(settings.get('api_url', '')).strip()
            values['api_key'] = str(settings.get('api_key', '')).strip()
        else:
            values['api_url'] = _required_form_text(data, 'api_url')
            values['api_key'] = _required_form_text(data, 'api_key')
        if not values['api_url'] or not values['api_key']:
            raise TranslateStartValidationError("AI翻译服务配置不完整")
    else:
        values['app_id'] = _required_form_text(data, 'app_id')
        values['app_key'] = _required_form_text(data, 'app_key')
        values['lang'] = _required_form_text(data, 'to_lang')
        values['comparison_id'] = 1 if _parse_form_bool(data, 'needIntervene') else None

    return values

# 定义翻译配置
TRANSLATE_SETTINGS = {
    "models": ["gpt-3.5-turbo", "gpt-4"],
    "default_model": "gpt-3.5-turbo",
    "max_threads": 5,
    "prompt_template": "请将以下内容翻译为{target_lang}"
}

# 百度翻译语言映射字典
LANG_CODE_TO_CHINESE = {
    'zh': '中文',
    'en': '英语',
    'ja': '日语',
    'ko': '韩语',
    'fr': '法语',
    'de': '德语',
    'es': '西班牙语',
    'ru': '俄语',
    'ar': '阿拉伯语',
    'it': '意大利语',

    # 兼容可能出现的全称
    'chinese': '中文',
    'english': '英语',
    'japanese': '日语',
    'korean': '韩语',
    '中文': '中文',  # 防止重复转换
    '汉语': '中文'
}


def get_unified_lang_name(lang_code):
    """统一返回语言的中文名称
    """
    # 统一转为小写处理
    lower_code = str(lang_code).lower()
    return LANG_CODE_TO_CHINESE.get(lower_code, lang_code)  # 找不到时返回原值


class TranslateStartResource(Resource):
    @jwt_required()
    def post(self):
        """启动翻译任务"""
        data = request.form
        try:
            user_id = get_jwt_identity()
            customer = db.session.get(Customer, user_id)
            if not customer:
                return APIResponse.error("用户不存在", 401)
            if customer.status == 'disabled':
                return APIResponse.error("用户状态异常", 403)

            api_settings = Setting.query.filter(
                Setting.group == 'api_setting',
                Setting.deleted_flag == 'N'
            ).all()
            translate_settings = {
                setting.alias: setting.value for setting in api_settings
            }
            start_values = _validate_translate_start(
                data, customer, translate_settings
            )

            # The upload record is the source of truth for ownership and paths.
            translate = Translate.query.filter_by(
                uuid=start_values['uuid'],
                customer_id=user_id,
                deleted_flag='N',
            ).first()
            if not translate:
                return APIResponse.error("未找到对应的翻译记录", 404)

            target_dir = (
                Path(current_app.root_path).parent
                / 'storage'
                / 'translate'
                / datetime.now().strftime('%Y-%m-%d')
            )
            target_dir.mkdir(parents=True, exist_ok=True)
            disk_name = Path(translate.origin_filepath).name
            target_abs_path = str(safe_storage_path(target_dir, disk_name))

            # 更新翻译记录
            translate.server = start_values['server']
            translate.target_filepath = target_abs_path
            translate.model = start_values['model']
            translate.app_key = start_values['app_key']
            translate.app_id = start_values['app_id']
            translate.backup_model = start_values['backup_model']
            translate.type = start_values['type']
            translate.prompt = start_values['prompt']
            translate.threads = start_values['threads']
            translate.api_url = start_values.get('api_url', '')
            translate.api_key = start_values.get('api_key', '')
            translate.origin_lang = start_values['origin_lang']
            translate.comparison_id = start_values['comparison_id']
            translate.prompt_id = start_values['prompt_id']
            translate.doc2x_flag = start_values['doc2x_flag']
            translate.doc2x_secret_key = start_values['doc2x_secret_key']
            translate.lang = start_values['lang']
            translate.status = 'none'
            translate.process = 0
            translate.start_at = None
            translate.end_at = None
            translate.failed_reason = None
            # Store the task configuration and queue record atomically. This
            # prevents a process interruption from leaving a configured task
            # with no durable queue entry.
            try:
                from app.task_queue import enqueue_translation, queue_backend_name
                if queue_backend_name() == 'celery':
                    db.session.commit()
                    enqueue_translation(translate.id, commit=False)
                else:
                    enqueue_translation(translate.id, commit=False)
                    db.session.commit()
            except Exception as exc:
                db.session.rollback()
                failed_task = db.session.get(Translate, translate.id)
                if failed_task:
                    failed_task.status = 'failed'
                    failed_task.process = 0
                    failed_task.end_at = datetime.now()
                    failed_task.failed_reason = f'任务入队失败: {exc}'[:500]
                    db.session.commit()
                current_app.logger.error('翻译任务入队失败', exc_info=True)
                return APIResponse.error("任务启动失败", 500)

            return APIResponse.success({
                "task_id": translate.id,
                "uuid": translate.uuid,
                "target_path": target_abs_path
            })

        except TranslateStartValidationError as e:
            db.session.rollback()
            return APIResponse.error(str(e), 400)
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"翻译任务启动失败: {str(e)}", exc_info=True)
            return APIResponse.error("任务启动失败", 500)


# 获取翻译记录列表
class TranslateListResource(Resource):
    @jwt_required()
    def get(self):
        """获取翻译记录列表"""
        # 获取查询参数
        page = request.args.get('page', '1')
        limit = request.args.get('limit', '100')
        status_filter = request.args.get('status')
        # 将字符串参数转换为整数
        try:
            page = int(page)
            limit = int(limit)
        except ValueError:
            return APIResponse.error("Invalid page or limit value"), 400
        # 构建查询条件
        query = Translate.query.filter_by(
            customer_id=get_jwt_identity(),
            deleted_flag='N'
        )
        # 排序
        query = query.order_by(Translate.created_at.desc())
        # 检查 status_filter 是否是合法值
        if status_filter:
            valid_statuses = {'none', 'process', 'done', 'failed'}
            if status_filter not in valid_statuses:
                return APIResponse.error(f"Invalid status value: {status_filter}"), 400
            query = query.filter_by(status=status_filter)

        # 执行分页查询
        pagination = query.paginate(page=page, per_page=limit, error_out=False)

        # 处理每条记录
        data = []
        for t in pagination.items:
            # 计算花费时间（基于 created_at 和 end_at）
            # 修复时间计算（强制显示分秒格式）
            if t.start_at and t.end_at:
                spend_time = t.end_at - t.start_at
                total_seconds = spend_time.total_seconds()

                # 强制分秒格式（即使不足1分钟也显示0分xx秒）
                minutes = int(total_seconds // 60)
                seconds = int(total_seconds % 60)
                spend_time_str = f"{minutes}分{seconds}秒"
            else:
                spend_time_str = "--"

            # 获取状态中文描述
            status_name_map = {
                'none': '未开始',
                'process': '进行中',
                'done': '已完成',
                'failed': '失败'
            }
            status_name = status_name_map.get(t.status, '未知状态')

            # 获取文件类型
            file_type = self.get_file_type(t.origin_filename)

            # 格式化完成时间（精确到秒）
            end_at_str = t.end_at.strftime('%Y-%m-%d %H:%M:%S') if t.end_at else "--"

            data.append({
                'id': t.id,
                'file_type': file_type,
                'origin_filename': t.origin_filename,
                'status': t.status,
                'status_name': status_name,
                'process': float(t.process),  # 将 Decimal 转换为 float
                'spend_time': spend_time_str,  # 花费时间
                'end_at': end_at_str,  # 完成时间
                'start_at': t.start_at.strftime('%Y-%m-%d %H:%M:%S') if t.start_at else "--",
                # 开始时间
                'lang': get_unified_lang_name(t.lang),  # 标准输出语言中文名称
                'target_filepath': t.target_filepath,
                'uuid': t.uuid,
                'server': t.server,
            })

        # 返回响应数据
        return APIResponse.success({
            'data': data,
            'total': pagination.total,
            'current_page': pagination.page
        })

    @staticmethod
    def get_file_type(filename):
        """根据文件名获取文件类型"""
        if not filename:
            return "未知"
        ext = filename.split('.')[-1].lower()
        if ext in {'docx', 'doc'}:
            return "Word"
        elif ext in {'xlsx', 'xls'}:
            return "Excel"
        elif ext == 'pptx':
            return "PPT"
        elif ext == 'pdf':
            return "PDF"
        elif ext in {'txt', 'md'}:
            return "文本"
        elif ext in {'html', 'htm'}:
            return "HTML"
        else:
            return "其他"


# 获取翻译设置
class TranslateSettingResource(Resource):
    @jwt_required()
    def get(self):
        """获取翻译配置（从数据库动态加载）[^1]"""
        try:
            # 从数据库中获取翻译配置
            settings = self._load_settings_from_db()
            return APIResponse.success(settings)
        except Exception as e:
            return APIResponse.error(f"获取配置失败: {str(e)}", 500)

    @staticmethod
    def _load_settings_from_db():
        """
        从数据库加载翻译配置[^2]
        :return: 翻译配置字典
        """
        # 查询翻译相关的配置（api_setting 和 other_setting 分组）
        settings = Setting.query.filter(
            Setting.group.in_(['api_setting', 'other_setting']),
            Setting.deleted_flag == 'N'
        ).all()

        # 转换为配置字典
        config = {}
        for setting in settings:
            # 如果 serialized 为 True，则反序列化 value
            value = json.loads(setting.value) if setting.serialized else setting.value

            # 根据 alias 存储配置
            if setting.alias == 'models':
                config['models'] = value.split(',') if isinstance(value, str) else value
            elif setting.alias == 'default_model':
                config['default_model'] = value
            elif setting.alias == 'default_backup':
                config['default_backup'] = value
            elif setting.alias == 'api_url':
                config['api_url'] = value
            elif setting.alias == 'api_key':
                config['api_key'] = "sk-xxx"  # value
            elif setting.alias == 'prompt':
                config['prompt_template'] = value
            elif setting.alias == 'threads':
                config['max_threads'] = int(value) if value.isdigit() else 10  # 默认10线程

        # 设置默认值（如果数据库中没有相关配置）
        config.setdefault('models', ['gpt-3.5-turbo', 'gpt-4'])
        config.setdefault('default_model', 'gpt-3.5-turbo')
        config.setdefault('default_backup', 'gpt-3.5-turbo')
        config.setdefault('api_url', 'https://api.ezworkapi.top/v1')
        config.setdefault('api_key', '')
        config.setdefault('prompt_template', '请将以下内容翻译为{target_lang}')
        config.setdefault('max_threads', 5)

        return config


class TranslateProcessResource(Resource):
    @jwt_required()
    def post(self):
        """查询翻译进度"""
        uuid = request.form.get('uuid')
        translate = Translate.query.filter_by(
            uuid=uuid,
            customer_id=get_jwt_identity()
        ).first_or_404()

        return APIResponse.success({
            'status': translate.status,
            'progress': float(translate.process),
        })


class TranslateDeleteResource(Resource):
    @jwt_required()
    def delete(self, id):
        """软删除翻译记录[^4]"""
        # 查询翻译记录
        customer_id = get_jwt_identity()
        translate = Translate.query.filter_by(
            id=id,
            customer_id=customer_id,
            deleted_flag='N',
        ).first_or_404()
        customer = Customer.query.get(customer_id)
        try:
            delete_result(translate)
        except Exception as exc:
            current_app.logger.error(
                '删除翻译结果失败，任务ID=%s，错误类型=%s',
                translate.id,
                type(exc).__name__,
            )
            return APIResponse.error('结果文件删除失败', 502)
        # 更新 deleted_flag 为 'Y'
        translate.deleted_flag = 'Y'
        # 更新用户存储空间
        customer.storage = max(0, customer.storage - (translate.size or 0))
        db.session.commit()

        return APIResponse.success(message='删除成功!')


class TranslateDownloadResource(Resource):
    @jwt_required()
    def get(self, id):
        """通过 ID 下载单个翻译结果文件[^5]"""
        # 查询翻译记录
        translate = Translate.query.filter_by(
            id=id,
            customer_id=get_jwt_identity(),
            deleted_flag='N',
        ).first_or_404()

        # 确保文件存在
        try:
            exists = result_exists(translate)
        except Exception as exc:
            current_app.logger.error(
                '读取翻译结果状态失败，任务ID=%s，错误类型=%s',
                translate.id,
                type(exc).__name__,
            )
            return APIResponse.error('文件读取失败', 502)
        if not exists:
            return APIResponse.error('文件不存在', 404)

        # 返回文件
        try:
            response = make_response(send_result_file(
                translate, translate.origin_filename
            ))
        except Exception as exc:
            current_app.logger.error(
                '读取翻译结果失败，任务ID=%s，错误类型=%s',
                translate.id,
                type(exc).__name__,
            )
            return APIResponse.error('文件读取失败', 502)

        # 禁用缓存
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'

        return response


class TranslateDownloadAllResource(Resource):
    @jwt_required()
    def get(self):
        """批量下载所有翻译结果文件[^6]"""
        # 查询当前用户的所有翻译记录
        records = Translate.query.filter_by(
            customer_id=get_jwt_identity(),
            deleted_flag='N'  # 只下载未删除的记录
        ).all()

        zip_buffer = tempfile.SpooledTemporaryFile(
            max_size=16 * 1024 * 1024, mode='w+b'
        )
        archive_names = set()
        try:
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for record in records:
                    if record.status != 'done':
                        continue
                    if not result_exists(record):
                        raise FileNotFoundError(
                            f'翻译结果不存在，任务ID={record.id}'
                        )
                    archive_name = Path(
                        record.origin_filename or record.target_filepath
                    ).name
                    stem, suffix = os.path.splitext(archive_name)
                    candidate = archive_name
                    duplicate_index = 2
                    while candidate in archive_names:
                        candidate = f"{stem} ({duplicate_index}){suffix}"
                        duplicate_index += 1
                    archive_names.add(candidate)
                    write_result_to_zip(zip_file, record, candidate)
        except Exception as exc:
            zip_buffer.close()
            current_app.logger.error(
                '批量读取翻译结果失败，错误类型=%s', type(exc).__name__
            )
            return APIResponse.error('批量下载时读取结果文件失败', 502)

        # 重置缓冲区指针
        zip_buffer.seek(0)

        # 返回 ZIP 文件
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"translations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        )


class OpenAICheckResource(Resource):
    @jwt_required()
    def post(self):
        """OpenAI接口检测"""
        data = request.form
        required = ['api_url', 'api_key', 'model']
        if not all(k in data for k in required):
            return APIResponse.error('缺少必要参数', 400)

        is_valid, msg = AIChecker.check_openai_connection(
            data['api_url'],
            data['api_key'],
            data['model']
        )

        return APIResponse.success({'valid': is_valid, 'message': msg})


class PDFCheckResource(Resource):
    @jwt_required()
    def post(self):
        """PDF扫描件检测[^7]"""
        if 'file' not in request.files:
            return APIResponse.error('请选择PDF文件', 400)

        file = request.files['file']
        if not file.filename.lower().endswith('.pdf'):
            return APIResponse.error('仅支持PDF文件', 400)

        try:
            file_stream = file.stream
            is_scanned = AIChecker.check_pdf_scanned(file_stream)
            return APIResponse.success({'scanned': is_scanned})
        except Exception as e:
            return APIResponse.error(f'检测失败: {str(e)}', 500)


class TranslateTestResource(Resource):
    def get(self):
        """测试翻译服务[^1]"""
        return APIResponse.success(message="测试服务正常")


class TranslateDeleteAllResource(Resource):
    @jwt_required()
    def delete(self):
        """删除用户所有翻译记录并更新存储空间"""
        customer_id = get_jwt_identity()

        # 先查询需要删除的记录及其总大小
        records_to_delete = Translate.query.filter_by(
            customer_id=customer_id,
            deleted_flag='N'
        ).all()

        total_size = sum((record.size or 0) for record in records_to_delete)

        try:
            for record in records_to_delete:
                delete_result(record)
        except Exception as exc:
            db.session.rollback()
            current_app.logger.error(
                '删除全部翻译结果失败，错误类型=%s', type(exc).__name__
            )
            return APIResponse.error('结果文件删除失败', 502)

        # 执行批量删除
        Translate.query.filter_by(
            customer_id=customer_id,
            deleted_flag='N'
        ).delete()

        # 更新用户存储空间
        customer = Customer.query.get(customer_id)
        if customer:
            customer.storage = max(0, customer.storage - total_size)

        db.session.commit()
        return APIResponse.success(message="全部文件删除成功!")


class TranslateFinishCountResource(Resource):
    @jwt_required()
    def get(self):
        """获取已完成翻译数量[^3]"""
        count = Translate.query.filter_by(
            customer_id=get_jwt_identity(),
            status='done',
            deleted_flag='N'
        ).count()
        return APIResponse.success({'total': count})


class Doc2xCheckResource(Resource):
    def post(self):
        """检查Doc2x接口[^7]"""
        secret_key = request.json.get('doc2x_secret_key')
        # 模拟验证逻辑，实际需对接Doc2x服务
        if secret_key == "valid_key_123":  # 示例验证
            return APIResponse.success(message="接口正常")
        return APIResponse.error("无效密钥", 400)
