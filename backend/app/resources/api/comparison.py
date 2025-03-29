# resources/comparison.py

import zipfile
from io import BytesIO
import pandas as pd
import pytz
from flask import request, current_app, send_file
from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models import Customer
from app.models.comparison import Comparison, ComparisonFav
from app.utils.response import APIResponse
from sqlalchemy import func
from datetime import datetime


class MyComparisonListResource(Resource):
    @jwt_required()
    def get(self):
        """获取我的术语表列表[^1]"""
        # 直接查询所有数据（不解析查询参数）
        query = Comparison.query.filter_by(customer_id=get_jwt_identity())
        comparisons = [self._format_comparison(comparison) for comparison in query.all()]

        # 返回结果
        return APIResponse.success({
            'data': comparisons,
            'total': len(comparisons)
        })

    def _format_comparison(self, comparison):
        """格式化术语表数据"""
        # 解析 content 字段
        content_list = []
        if comparison.content:
            for item in comparison.content.split('; '):
                if ':' in item:
                    origin, target = item.split(':', 1)
                    content_list.append({
                        'origin': origin.strip(),
                        'target': target.strip()
                    })

        # 返回格式化后的数据
        return {
            'id': comparison.id,
            'title': comparison.title,
            'origin_lang': comparison.origin_lang,
            'target_lang': comparison.target_lang,
            'share_flag': comparison.share_flag,
            'added_count': comparison.added_count,
            'content': content_list,  # 返回解析后的数组
            'customer_id': comparison.customer_id,
            'created_at': comparison.created_at.strftime(
                '%Y-%m-%d %H:%M') if comparison.created_at else None,  # 格式化时间
            'updated_at': comparison.updated_at.strftime(
                '%Y-%m-%d %H:%M') if comparison.updated_at else None,  # 格式化时间
            'deleted_flag': comparison.deleted_flag
        }


# 获取共享术语表列表
class SharedComparisonListResource(Resource):
    @jwt_required()
    def get(self):
        """获取共享术语表列表[^3]"""
        # 从查询字符串中解析参数
        parser = reqparse.RequestParser()
        parser.add_argument('page', type=int, default=1, location='args')  # 分页参数
        parser.add_argument('limit', type=int, default=10, location='args')  # 分页参数
        parser.add_argument('order', type=str, default='latest', location='args')  # 排序参数
        args = parser.parse_args()

        # 查询共享的术语表，并关联 Customer 表获取用户 email
        query = db.session.query(
            Comparison,
            func.count(ComparisonFav.id).label('fav_count'),  # 动态计算收藏量
            Customer.email.label('customer_email')  # 获取用户的 email
        ).outerjoin(
            ComparisonFav, Comparison.id == ComparisonFav.comparison_id
        ).outerjoin(
            Customer, Comparison.customer_id == Customer.id  # 通过 customer_id 关联 Customer
        ).filter(
            Comparison.share_flag == 'Y',
            Comparison.deleted_flag == 'N'
        ).group_by(
            Comparison.id
        )

        # 根据 order 参数排序
        if args['order'] == 'latest':
            query = query.order_by(Comparison.created_at.desc())  # 按最新发表排序
        elif args['order'] == 'added':
            query = query.order_by(Comparison.added_count.desc())  # 按添加量排序
        elif args['order'] == 'fav':
            query = query.order_by(func.count(ComparisonFav.id).desc())  # 按收藏量排序

        # 分页查询
        pagination = query.paginate(page=args['page'], per_page=args['limit'], error_out=False)
        comparisons = [{
            'id': comparison.id,
            'title': comparison.title,
            'origin_lang': comparison.origin_lang,
            'target_lang': comparison.target_lang,
            'content': self.parse_content(comparison.content),  # 解析 content 字段为数组
            'email': customer_email if customer_email else '匿名用户',  # 返回用户 email
            'added_count': comparison.added_count,
            'created_at': comparison.created_at.strftime('%Y-%m-%d %H:%M'),  # 格式化时间
            'faved': self.check_faved(comparison.id),  # 检查是否被当前用户收藏
            'fav_count': fav_count  # 添加收藏量
        } for comparison, fav_count, customer_email in pagination.items]

        # 返回结果
        return APIResponse.success({
            'data': comparisons,
            'total': pagination.total,
            'current_page': pagination.page,
            'per_page': pagination.per_page
        })

    def parse_content(self, content_str):
        """将 content 字符串解析为数组格式"""
        content_list = []
        if content_str:
            for item in content_str.split('; '):
                if ':' in item:
                    origin, target = item.split(':', 1)  # 分割为 origin 和 target
                    content_list.append({
                        'origin': origin.strip(),
                        'target': target.strip()
                    })
        return content_list

    def check_faved(self, comparison_id):
        """检查当前用户是否收藏了该术语表"""
        # 假设当前用户的 ID 存储在 JWT 中
        user_id = get_jwt_identity()
        if user_id:
            fav = ComparisonFav.query.filter_by(
                comparison_id=comparison_id,
                customer_id=user_id
            ).first()
            return 1 if fav else 0
        return 0



# 编辑术语列表
class EditComparisonResource(Resource):
    @jwt_required()
    def post(self, id):
        """编辑术语表"""
        comparison = Comparison.query.filter_by(
            id=id,
            customer_id=get_jwt_identity()
        ).first_or_404()

        data = request.form
        if 'title' in data:
            comparison.title = data['title']
        if 'origin_lang' in data:
            comparison.origin_lang = data['origin_lang']
        if 'target_lang' in data:
            comparison.target_lang = data['target_lang']
        if 'share_flag' in data:
            comparison.share_flag = data['share_flag']
        if 'added_count' in data:
            try:
                comparison.added_count = int(data['added_count'])
            except ValueError:
                return APIResponse.error("无效的 added_count 格式", 400)

        # 更新 content
        content_list = []
        for key, value in data.items():
            if key.startswith('content[') and '][origin]' in key:
                # 提取索引
                index = key.split('[')[1].split(']')[0]
                origin = value
                target = data.get(f'content[{index}][target]', '')
                content_list.append(f"{origin}: {target}")

        # 将 content_list 转换为字符串
        content_str = '; '.join(content_list)
        comparison.content = content_str

        # 获取应用配置中的时区
        timezone_str = current_app.config['TIMEZONE']
        timezone = pytz.timezone(timezone_str)

        # 更新 updated_at 字段
        comparison.updated_at = datetime.now(timezone)

        db.session.commit()
        return APIResponse.success(message='术语表更新成功')


# 更新术语表共享状态
class ShareComparisonResource(Resource):
    @jwt_required()
    def post(self, id):
        """修改共享状态[^4]"""
        comparison = Comparison.query.filter_by(
            id=id,
            customer_id=get_jwt_identity()
        ).first_or_404()

        data = request.form
        if 'share_flag' not in data or data['share_flag'] not in ['Y', 'N']:
            return APIResponse.error('share_flag 参数无效', 400)

        comparison.share_flag = data['share_flag']
        db.session.commit()
        return APIResponse.success(message='共享状态已更新')


# 复制到我的术语库
class CopyComparisonResource(Resource):
    @jwt_required()
    def post(self, id):
        """复制到我的术语库[^5]"""
        comparison = Comparison.query.filter_by(
            id=id,
            share_flag='Y'
        ).first_or_404()

        new_comparison = Comparison(
            title=f"{comparison.title} (副本)",
            content=comparison.content,
            origin_lang=comparison.origin_lang,
            target_lang=comparison.target_lang,
            customer_id=get_jwt_identity(),
            share_flag='N'
        )
        db.session.add(new_comparison)
        db.session.commit()
        return APIResponse.success({
            'new_id': new_comparison.id
        })


# 收藏/取消收藏
class FavoriteComparisonResource(Resource):
    @jwt_required()
    def post(self, id):
        """收藏/取消收藏[^6]"""
        comparison = Comparison.query.filter_by(id=id).first_or_404()
        customer_id = get_jwt_identity()

        favorite = ComparisonFav.query.filter_by(
            comparison_id=id,
            customer_id=customer_id
        ).first()

        if favorite:
            db.session.delete(favorite)
            message = '已取消收藏'
        else:
            new_favorite = ComparisonFav(
                comparison_id=id,
                customer_id=customer_id
            )
            db.session.add(new_favorite)
            message = '已收藏'

        db.session.commit()
        return APIResponse.success(message=message)


# 创建新术语表
class CreateComparisonResource(Resource):
    @jwt_required()
    def post(self):
        """创建新术语表[^1]"""
        data = request.form
        required_fields = ['title', 'share_flag', 'origin_lang', 'target_lang']
        if not all(field in data for field in required_fields):
            return APIResponse.error('缺少必要参数', 400)

        # 解析 content 参数
        content_list = []
        for key, value in data.items():
            if key.startswith('content[') and '][origin]' in key:
                # 提取索引
                index = key.split('[')[1].split(']')[0]
                origin = value
                target = data.get(f'content[{index}][target]', '')
                content_list.append(f"{origin}: {target}")

        # 将 content_list 转换为字符串
        content_str = '; '.join(content_list)

        # 获取应用配置中的时区
        timezone_str = current_app.config['TIMEZONE']
        timezone = pytz.timezone(timezone_str)
        # 获取当前时间
        current_time = datetime.now(timezone)

        # 创建术语表
        comparison = Comparison(
            title=data['title'],
            origin_lang=data['origin_lang'],
            target_lang=data['target_lang'],
            content=content_str,  # 插入转换后的 content 字符串
            customer_id=get_jwt_identity(),
            share_flag=data.get('share_flag', 'N'),
            created_at=current_time,  # 显式赋值
            updated_at=current_time  # 显式赋值
        )
        db.session.add(comparison)
        db.session.commit()
        return APIResponse.success({
            'id': comparison.id
        })


# 删除术语表
class DeleteComparisonResource(Resource):
    @jwt_required()
    def delete(self, id):
        """删除术语表[^2]"""
        comparison = Comparison.query.filter_by(
            id=id,
            customer_id=get_jwt_identity()
        ).first_or_404()

        db.session.delete(comparison)
        db.session.commit()
        return APIResponse.success(message='删除成功')


# 下载模板文件
class DownloadTemplateResource(Resource):
    def get(self):
        """下载模板文件[^3]"""
        from flask import send_file
        from io import BytesIO
        import pandas as pd

        # 创建模板文件
        df = pd.DataFrame(columns=['源术语', '目标术语'])
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        output.seek(0)

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='术语表模板.xlsx'
        )


# 导入术语表
class ImportComparisonResource(Resource):
    @jwt_required()
    def post(self):
        """
        导入 Excel 文件
        """
        # 检查是否上传了文件
        if 'file' not in request.files:
            return APIResponse.error('未选择文件', 400)
        file = request.files['file']

        try:
            # 读取 Excel 文件
            import pandas as pd
            df = pd.read_excel(file)

            # 检查文件是否包含所需的列
            if not {'源术语', '目标术语'}.issubset(df.columns):
                return APIResponse.error('文件格式不符合模板要求', 406)
            # 解析 Excel 文件内容
            content = ';'.join(
                [f"{row['源术语']}: {row['目标术语']}" for _, row in df.iterrows()])  # 按 ': ' 分隔
            # 创建术语表
            comparison = Comparison(
                title='导入的术语表',
                origin_lang='未知',
                target_lang='未知',
                content=content,  # 使用改进后的格式
                customer_id=get_jwt_identity(),
                share_flag='N'
            )
            db.session.add(comparison)
            db.session.commit()

            # 返回成功响应
            return APIResponse.success({
                'id': comparison.id
            })
        except Exception as e:
            # 捕获并返回错误信息
            return APIResponse.error(f"文件导入失败：{str(e)}", 500)


# 导出单个术语表
class ExportComparisonResource(Resource):
    @jwt_required()
    def get(self, id):
        """
        导出单个术语表
        """
        # 获取当前用户 ID
        current_user_id = get_jwt_identity()

        # 查询术语表
        comparison = Comparison.query.get_or_404(id)

        # 检查术语表是否共享或属于当前用户
        if comparison.share_flag != 'Y' and comparison.user_id != current_user_id:
            return {'message': '术语表未共享或无权限访问', 'code': 403}, 403

        # 解析术语内容
        terms = [term.split(': ') for term in comparison.content.split(';')]  # 按 ': ' 分割
        df = pd.DataFrame(terms, columns=['源术语', '目标术语'])

        # 创建 Excel 文件
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        output.seek(0)

        # 返回文件下载响应
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'{comparison.title}.xlsx'
        )




# 批量导出所有术语表
class ExportAllComparisonsResource(Resource):
    @jwt_required()
    def get(self):
        """
        批量导出所有术语表
        """
        # 获取当前用户 ID
        current_user_id = get_jwt_identity()

        # 查询当前用户的所有术语表
        comparisons = Comparison.query.filter_by(customer_id=current_user_id).all()

        # 创建 ZIP 文件
        memory_file = BytesIO()
        with zipfile.ZipFile(memory_file, 'w') as zf:
            for comparison in comparisons:
                # 解析术语内容
                terms = [term.split(': ') for term in comparison.content.split(';')]  # 按 ': ' 分割
                df = pd.DataFrame(terms, columns=['源术语', '目标术语'])

                # 创建 Excel 文件
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False)
                output.seek(0)

                # 将 Excel 文件添加到 ZIP 中
                zf.writestr(f"{comparison.title}.xlsx", output.getvalue())

        memory_file.seek(0)

        # 返回 ZIP 文件下载响应
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'术语表_{datetime.now().strftime("%Y%m%d")}.zip'
        )
