# resources/admin/setting.py
from flask import request
from flask_restful import Resource

from app import db
from app.models import Setting
from app.utils.response import APIResponse
from app.utils.validators import validate_id_list


class AdminSettingNoticeResource(Resource):
    def get(self):
        """获取通知设置[^1]"""
        setting = Setting.query.filter_by(alias='notice_setting').first()
        if not setting:
            return APIResponse.success(data={'users': []})
        return APIResponse.success(data={'users': eval(setting.value)})

    def post(self):
        """更新通知设置[^1]"""
        data = request.json
        users = validate_id_list(data.get('users'))

        setting = Setting.query.filter_by(alias='notice_setting').first()
        if not setting:
            setting = Setting(alias='notice_setting')

        setting.value = str(users)
        setting.serialized = True
        db.session.add(setting)
        db.session.commit()
        return APIResponse.success(message='通知设置已更新')


class AdminSettingApiResource(Resource):
    def get(self):
        """获取API配置[^2]"""
        settings = Setting.query.filter(Setting.group == 'api_setting').all()
        data = {
            'api_url': settings[0].value,
            'api_key': settings[1].value,
            'models': settings[2].value,
            'default_model': settings[3].value,
            'default_backup': settings[4].value
        }
        return APIResponse.success(data=data)

    def post(self):
        """更新API配置[^2]"""
        data = request.json
        required_fields = ['api_url', 'api_key', 'models', 'default_model', 'default_backup']
        if not all(field in data for field in required_fields):
            return APIResponse.error('缺少必要参数', 400)

        for alias, value in data.items():
            setting = Setting.query.filter_by(alias=alias).first()
            if not setting:
                setting = Setting(alias=alias, group='api_setting')
            setting.value = value
            db.session.add(setting)
        db.session.commit()
        return APIResponse.success(message='API配置已更新')


class AdminInfoSettingOtherResource(Resource):
    def get(self):
        """获取其他设置[^3]"""
        settings = Setting.query.filter(Setting.group == 'other_setting').all()
        data = {
            'prompt': settings[0].value,
            'threads': int(settings[1].value),
            'email_limit': settings[2].value
        }
        return APIResponse.success(data=data)



class AdminEditSettingOtherResource(Resource):
    def post(self):
        """更新其他设置[^3]"""
        data = request.json
        required_fields = ['prompt', 'threads']
        if not all(field in data for field in required_fields):
            return APIResponse.error('缺少必要参数', 400)

        for alias, value in data.items():
            setting = Setting.query.filter_by(alias=alias).first()
            if not setting:
                setting = Setting(alias=alias, group='other_setting')
            setting.value = value
            db.session.add(setting)
        db.session.commit()
        return APIResponse.success(message='其他设置已更新')

class AdminSettingSiteResource(Resource):
    def get(self):
        """获取站点设置[^4]"""
        setting = Setting.query.filter_by(alias='version').first()
        if not setting:
            return APIResponse.success(data={'version': 'community'})
        return APIResponse.success(data={'version': setting.value})

    def post(self):
        """更新站点版本[^4]"""
        version = request.json.get('version')
        if not version or version not in ['business', 'community']:
            return APIResponse.error('版本号无效', 400)

        setting = Setting.query.filter_by(alias='version').first()
        if not setting:
            setting = Setting(alias='version', group='site_setting')
        setting.value = version
        db.session.add(setting)
        db.session.commit()
        return APIResponse.success(message='站点版本已更新')

