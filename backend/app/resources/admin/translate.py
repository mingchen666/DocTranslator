# resources/admin/to_translate.py
import os
import tempfile
import zipfile
from datetime import datetime
from flask import current_app, request, make_response, send_file
from flask_restful import Resource, reqparse
from app import db
from app.models import Customer
from app.models.translate import Translate
from app.utils.auth_tools import admin_required
from app.utils.response import APIResponse
from app.utils.validators import (
    validate_id_list
)
from app.result_storage import (
    delete_result,
    result_exists,
    send_result_file,
    write_result_to_zip,
)


# 获取翻译记录列表
class AdminTranslateListResource(Resource):
    @admin_required
    def get(self):
        """获取翻译记录列表"""
        # 获取查询参数
        parser = reqparse.RequestParser()
        parser.add_argument('page', type=int, default=1, location='args')  # 页码，默认为 1
        parser.add_argument('limit', type=int, default=100, location='args')  # 每页数量，默认为 100
        parser.add_argument('status', type=str, location='args')  # 状态，可选
        parser.add_argument('keyword', type=str, location='args')  # 搜索关键字，可选
        args = parser.parse_args()

        # 构建查询条件
        query = Translate.query.filter_by()

        # 检查状态过滤条件
        if args['status']:
            valid_statuses = {'none', 'process', 'done', 'failed'}
            if args['status'] not in valid_statuses:
                return APIResponse.error(f"Invalid status value: {args['status']}"), 400
            query = query.filter_by(status=args['status'])
        # 检查关键字过滤条件
        if args['keyword']:
            # 模糊匹配 origin_filename 或 customer_email
            query = query.join(Customer, Translate.customer_id == Customer.id).filter(
                (Translate.origin_filename.ilike(f"%{args['keyword']}%")) |
                (Customer.email.ilike(f"%{args['keyword']}%"))
            )
        # 执行分页查询
        pagination = query.paginate(page=args['page'], per_page=args['limit'], error_out=False)

        # 处理每条记录
        data = []
        for t in pagination.items:
            # 计算花费时间（基于 start_at 和 end_at）
            if t.start_at and t.end_at:
                spend_time = t.end_at - t.start_at
                spend_time_minutes = int(spend_time.total_seconds() // 60)
                spend_time_seconds = int(spend_time.total_seconds() % 60)
                spend_time_str = f"{spend_time_minutes}分{spend_time_seconds}秒"
            else:
                spend_time_str = "--"

            # 获取用户邮箱（通过 Customer 模型关联查询）
            customer = Customer.query.get(t.customer_id)
            customer_email = customer.email if customer else "--"
            customer_no = customer.customer_no if customer.customer_no else t.customer_id
            # 格式化时间字段
            start_at_str = t.start_at.strftime('%Y-%m-%d %H:%M:%S') if t.start_at else "--"
            end_at_str = t.end_at.strftime('%Y-%m-%d %H:%M:%S') if t.end_at else "--"

            # 构建返回数据
            data.append({
                'id': t.id,
                'customer_no': customer_no,
                'customer_id': t.customer_id,  # 所属用户 ID
                'customer_email': customer_email,  # 用户邮箱
                'origin_filename': t.origin_filename,
                'status': t.status,
                'process': float(t.process) if t.process is not None else None,  # 转换为 float
                'start_at': start_at_str,  # 开始时间
                'end_at': end_at_str,  # 完成时间
                'spend_time': spend_time_str,  # 完成用时
                'lang': t.lang,
                'target_filepath': t.target_filepath,
            'deleted_flag':t.deleted_flag
            })

        # 返回响应数据
        return APIResponse.success({
            'data': data,
            'total': pagination.total,
            'current_page': pagination.page
        })


# 批量下载多个翻译文件
class AdminTranslateDownloadBatchResource(Resource):
    @admin_required
    def post(self):
        """批量下载多个翻译结果文件（管理员接口）"""
        try:
            # 解析请求体中的 ids 参数
            data = request.get_json()
            if not data or 'ids' not in data:
                return {"message": "缺少 ids 参数"}, 400

            ids = data['ids']
            if not isinstance(ids, list):
                return {"message": "ids 必须是数组"}, 400

            # 查询指定的翻译记录
            records = Translate.query.filter(
                Translate.id.in_(ids),  # 过滤指定 ID
                Translate.deleted_flag == 'N'  # 只下载未删除的记录
            ).all()

            zip_buffer = tempfile.SpooledTemporaryFile(
                max_size=16 * 1024 * 1024, mode='w+b'
            )
            with zipfile.ZipFile(
                zip_buffer, 'w', zipfile.ZIP_DEFLATED
            ) as zip_file:
                for record in records:
                    if record.status != 'done':
                        continue
                    if not result_exists(record):
                        raise FileNotFoundError(
                            f'翻译结果不存在，任务ID={record.id}'
                        )
                    write_result_to_zip(
                        zip_file,
                        record,
                        os.path.basename(
                            record.origin_filename or record.target_filepath
                        ),
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
        except Exception as e:
            if 'zip_buffer' in locals():
                zip_buffer.close()
            return {"message": "批量下载时读取结果文件失败"}, 502


# 下载单个翻译文件
class AdminTranslateDownloadResource(Resource):
    @admin_required
    def get(self, id):
        """通过 ID 下载单个翻译结果文件[^5]"""
        # 查询翻译记录
        translate = Translate.query.filter_by(
            id=id,
            # customer_id=get_jwt_identity()
        ).first_or_404()

        # 确保文件存在
        try:
            exists = result_exists(translate)
        except Exception as exc:
            current_app.logger.error(
                '管理员读取翻译结果状态失败，任务ID=%s，错误类型=%s',
                translate.id,
                type(exc).__name__,
            )
            return APIResponse.error('文件读取失败', 502)
        if not exists:
            return APIResponse.error('文件不存在', 404)

        # 返回文件
        try:
            response = make_response(send_result_file(
                translate,
                os.path.basename(
                    translate.origin_filename or translate.target_filepath
                ),
            ))
        except Exception as exc:
            current_app.logger.error(
                '管理员读取翻译结果失败，任务ID=%s，错误类型=%s',
                translate.id,
                type(exc).__name__,
            )
            return APIResponse.error('文件读取失败', 502)

        # 禁用缓存
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'

        return response


# 删除单个翻译记录
class AdminTranslateDeteleResource(Resource):
    @admin_required
    def delete(self, id):
        """删除单个翻译记录[^2]"""
        try:
            record = Translate.query.get_or_404(id)
            delete_result(record)
            if record.customer_id:
                customer = db.session.get(Customer, record.customer_id)
                if customer:
                    customer.storage = max(
                        0, customer.storage - (record.size or 0)
                    )
            db.session.delete(record)
            db.session.commit()
            return APIResponse.success(message='记录删除成功')
        except Exception as e:
            db.session.rollback()
            return APIResponse.error('删除失败', 500)


class AdminTranslateBatchDeleteResource(Resource):
    @admin_required
    def post(self):
        """批量删除翻译记录[^3]"""
        try:
            ids = validate_id_list(request.json.get('ids'))
            if len(ids) > 100:
                return APIResponse.error('单次最多删除100条记录', 400)

            records = Translate.query.filter(Translate.id.in_(ids)).all()
            if len(records) != len(set(ids)):
                return APIResponse.error('部分翻译记录不存在', 404)
            quota_by_customer = {}
            for record in records:
                delete_result(record)
                if record.customer_id:
                    quota_by_customer[record.customer_id] = (
                        quota_by_customer.get(record.customer_id, 0)
                        + (record.size or 0)
                    )
                db.session.delete(record)
            for customer_id, released_size in quota_by_customer.items():
                customer = db.session.get(Customer, customer_id)
                if customer:
                    customer.storage = max(
                        0, customer.storage - released_size
                    )
            db.session.commit()
            return APIResponse.success(message=f'成功删除{len(records)}条记录')
        except APIResponse as e:
            return e
        except Exception as e:
            db.session.rollback()
            return APIResponse.error('批量删除失败', 500)


class AdminTranslateRestartResource(Resource):
    @admin_required
    def post(self, id):
        """重启翻译任务[^4]"""
        try:
            record = Translate.query.get_or_404(id)
            if record.status not in ['failed', 'done']:
                return APIResponse.error('当前状态无法重启', 400)

            record.status = 'none'
            record.start_at = None
            record.end_at = None
            record.failed_reason = None
            db.session.commit()
            return APIResponse.success(message='任务已重启')
        except Exception as e:
            db.session.rollback()
            return APIResponse.error('重启失败', 500)


class AdminTranslateStatisticsResource(Resource):
    @admin_required
    def get(self):
        """获取翻译统计信息[^5]"""
        try:
            total = Translate.query.count()
            done_count = Translate.query.filter_by(status='done').count()
            processing_count = Translate.query.filter_by(status='process').count()
            failed_count = Translate.query.filter_by(status='failed').count()

            return APIResponse.success({
                'total': total,
                'done_count': done_count,
                'processing_count': processing_count,
                'failed_count': failed_count
            })
        except Exception as e:
            return APIResponse.error('获取统计信息失败', 500)
