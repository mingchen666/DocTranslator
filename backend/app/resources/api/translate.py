# resources/to_translate.py
import json
from pathlib import Path

from flask import request, send_file, current_app, make_response
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from io import BytesIO
import zipfile
import os

from app import db, Setting
from app.models import Customer
from app.models.translate import Translate
from app.resources.task.translate_service import TranslateEngine
from app.utils.response import APIResponse
from app.utils.check_utils import AIChecker

# 定义翻译配置（硬编码示例）
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
        """启动翻译任务（支持绝对路径和多参数）"""
        data = request.form
        required_fields = [
            'server', 'model', 'lang', 'uuid',
            'prompt', 'threads', 'file_name'
        ]

        # 参数校验
        if not all(field in data for field in required_fields):
            return APIResponse.error("缺少必要参数", 400)

        # 验证OpenAI配置
        if data['server'] == 'openai' and not all(k in data for k in ['api_url', 'api_key']):
            return APIResponse.error("AI翻译需要API地址和密钥", 400)

        # if data['server'] == 'openai':
        #     return APIResponse.error("Doc2x服务需要密钥", 400)
        # elif data['server'] == 'baidu':
        #     return APIResponse.error("Doc2x服务需要密钥", 400)
        try:
            # 获取用户信息
            user_id = get_jwt_identity()
            customer = Customer.query.get(user_id)
            # # 判断用户是否是会员，会员不需要填写api，key
            # if customer.level != 'vip' and not data['api_key']:
            #     return APIResponse.error("缺少key !", 400)
            if customer.status == 'disabled':
                return APIResponse.error("用户状态异常", 403)

            # 生成绝对路径（跨平台兼容）
            def get_absolute_storage_path(filename):
                # 获取项目根目录的父目录（假设storage目录与项目目录同级）
                base_dir = Path(current_app.root_path).parent.absolute()
                # 按日期创建子目录（如 storage/translate/2024-01-20）
                date_str = datetime.now().strftime('%Y-%m-%d')
                # 创建目标目录（如果不存在）
                target_dir = base_dir / "storage" / "translate" / date_str
                target_dir.mkdir(parents=True, exist_ok=True)
                # 返回绝对路径（保持原文件名）
                return str(target_dir / filename)

            origin_filename = data['file_name']

            # 生成翻译结果绝对路径
            target_abs_path = get_absolute_storage_path(origin_filename)

            # 获取翻译类型（取最后一个type值）
            translate_type = data.get('type[2]', 'trans_all_only_inherit')

            # 查询或创建翻译记录
            translate = Translate.query.filter_by(uuid=data['uuid']).first()
            if not translate:
                return APIResponse.error("未找到对应的翻译记录", 404)

            # 从系统里面获取api_setting 分组的配置
            api_settings = Setting.query.filter(
                Setting.group == 'api_setting',  # 只查询 api_setting 分组
                Setting.deleted_flag == 'N'  # 未删除的记录
            ).all()
            # 转换成字典
            translate_settings = {}
            for setting in api_settings:
                translate_settings[setting.alias] = setting.value
            # 更新翻译记录
            translate.server = data.get('server', 'openai')
            translate.origin_filename = data['file_name']
            translate.target_filepath = target_abs_path  # 存储翻译结果的绝对路径

            translate.model = data['model']
            translate.app_key = data.get('app_key', None)
            translate.app_id = data.get('app_id', None)
            translate.backup_model = data['backup_model']
            translate.type = translate_type
            translate.prompt = data['prompt']
            translate.threads = int(data['threads'])
            # 会员用户下使用系统的api_url和api_key
            if customer.level == 'vip':
                translate.api_url = translate_settings.get('api_url', '').strip()
                translate.api_key = translate_settings.get('api_key', '').strip()
            else:
                translate.api_url = data.get('api_url', '')
                translate.api_key = data.get('api_key', '')
            translate.backup_model = data.get('backup_model', '')
            translate.origin_lang = data.get('origin_lang', '')
            translate.size = data.get('size', 0)  # 更新文件大小
            # 获取 comparison_id 并转换为整数
            comparison_id = data.get('comparison_id', 0)  # 默认值为 '0'
            translate.comparison_id = int(comparison_id) if comparison_id else None
            prompt_id = data.get('prompt_id', '0')
            translate.prompt_id = int(prompt_id) if prompt_id else None
            translate.doc2x_flag = data.get('doc2x_flag', 'N')
            translate.doc2x_secret_key = data.get('doc2x_secret_key', '')
            if data['server'] == 'baidu':
                translate.lang = data['to_lang']
                translate.comparison_id = 1 if data.get('needIntervene', False) else None  # 使用术语库
            else:
                translate.lang = data['lang']
            # 使用 UTC 时间并格式化
            # current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')
            # translate.created_at = current_time
            # 保存到数据库
            # 更新用户已用存储空间
            customer.storage += int(translate.size)
            db.session.commit()
            # with current_app.app_context():  # 确保在应用上下文中运行
            # 启动翻译引擎，传入 current_app
            TranslateEngine(translate.id).execute()

            return APIResponse.success({
                "task_id": translate.id,
                "uuid": translate.uuid,
                "target_path": target_abs_path
            })

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

        # 检查 status_filter 是否是合法值
        if status_filter:
            valid_statuses = {'none', 'process', 'done', 'failed', 'processing'}
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
                'processing': '进行中',
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


class TranslateSettingResource66(Resource):
    @jwt_required()
    def get(self):
        """获取翻译配置[^2]"""
        return APIResponse.success(TRANSLATE_SETTINGS)


class TranslateProcessResource(Resource):
    @jwt_required()
    def post(self):
        """查询翻译进度[^3]"""
        uuid = request.form.get('uuid')
        translate = Translate.query.filter_by(
            uuid=uuid,
            customer_id=get_jwt_identity()
        ).first_or_404()

        return APIResponse.success({
            'status': translate.status,
            'progress': float(translate.process),
            'download_url': translate.target_filepath if translate.status == 'done' else None
        })


class TranslateDeleteResource(Resource):
    @jwt_required()
    def delete(self, id):
        """软删除翻译记录[^4]"""
        # 查询翻译记录
        customer_id = get_jwt_identity()
        translate = Translate.query.filter_by(
            id=id,
            customer_id=customer_id
        ).first_or_404()
        customer = Customer.query.get(customer_id)
        # 更新 deleted_flag 为 'Y'
        translate.deleted_flag = 'Y'
        # 更新用户存储空间
        customer.storage -= translate.size
        db.session.commit()

        return APIResponse.success(message='删除成功!')


class TranslateDownloadResource(Resource):
    # @jwt_required()
    def get(self, id):
        """通过 ID 下载单个翻译结果文件[^5]"""
        # 查询翻译记录
        translate = Translate.query.filter_by(
            id=id,
            # customer_id=get_jwt_identity()
        ).first_or_404()

        # 确保文件存在
        if not translate.target_filepath or not os.path.exists(translate.target_filepath):
            return APIResponse.error('文件不存在', 404)

        # 返回文件
        response = make_response(send_file(
            translate.target_filepath,
            as_attachment=True,
            download_name=os.path.basename(translate.target_filepath)
        ))

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

        # 生成内存 ZIP 文件
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            for record in records:
                if record.target_filepath and os.path.exists(record.target_filepath):
                    # 将文件添加到 ZIP 中
                    zip_file.write(
                        record.target_filepath,
                        os.path.basename(record.target_filepath)
                    )

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
        """OpenAI接口检测[^6]"""
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

        total_size = sum(record.size for record in records_to_delete)

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


class TranslateRandDeleteAllResource(Resource):
    def delete(self):
        """删除临时用户所有记录[^4]"""
        rand_user_id = request.json.get('rand_user_id')
        if not rand_user_id:
            return APIResponse.error('需要临时用户ID', 400)

        Translate.query.filter_by(
            rand_user_id=rand_user_id,
            deleted_flag='N'
        ).delete()
        db.session.commit()
        return APIResponse.success(message="删除成功")


class TranslateRandDeleteResource(Resource):
    def delete(self, id):
        """删除临时用户单条记录[^5]"""
        rand_user_id = request.json.get('rand_user_id')
        translate = Translate.query.filter_by(
            id=id,
            rand_user_id=rand_user_id
        ).first_or_404()

        db.session.delete(translate)
        db.session.commit()
        return APIResponse.success(message="删除成功")


class TranslateRandDownloadResource(Resource):
    def get(self):
        """下载临时用户翻译文件[^6]"""
        rand_user_id = request.args.get('rand_user_id')
        records = Translate.query.filter_by(
            rand_user_id=rand_user_id,
            status='done'
        ).all()

        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            for record in records:
                if os.path.exists(record.target_filepath):
                    zip_file.write(
                        record.target_filepath,
                        os.path.basename(record.target_filepath)
                    )

        zip_buffer.seek(0)
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"temp_translations_{datetime.now().strftime('%Y%m%d')}.zip"
        )


class Doc2xCheckResource(Resource):
    def post(self):
        """检查Doc2x接口[^7]"""
        secret_key = request.json.get('doc2x_secret_key')
        # 模拟验证逻辑，实际需对接Doc2x服务
        if secret_key == "valid_key_123":  # 示例验证
            return APIResponse.success(message="接口正常")
        return APIResponse.error("无效密钥", 400)
