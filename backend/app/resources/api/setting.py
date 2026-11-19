# resources/system.py
from flask import current_app, jsonify, make_response
from flask_restful import Resource

from app.utils.response import APIResponse
from app.utils.site_domain import site_config_payload


class SystemVersionResource(Resource):
    def get(self):
        """获取系统版本信息[^1]"""
        return APIResponse.success({
            'version': current_app.config['SYSTEM_VERSION'],
            'message': 'success'
        })


class SystemSettingsResource(Resource):
    def get(self):
        """获取全量系统配置[^2]"""
        return APIResponse.success({
            'site_setting': {
                'version': current_app.config['SYSTEM_VERSION'],
                'site_name': current_app.config['SITE_NAME']
            },
            'api_setting': {
                'api_url': current_app.config['API_URL'],
                'models': current_app.config['TRANSLATE_MODELS']
            },
            'message': 'success'
        })


class SiteConfigResource(Resource):
    """公开的站点域名配置，供前台/管理端启动时读取。"""

    def get(self):
        payload, status = APIResponse.success(site_config_payload())
        response = make_response(jsonify(payload), status)
        # 配置随时可能被管理员修改，不能让浏览器/代理缓存旧值。
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        return response
