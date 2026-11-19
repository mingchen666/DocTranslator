# resources/admin/setting.py
import os
import shutil
import json
from flask import request, current_app
from flask_restful import Resource

from app import db
from app.models import Setting
from app.utils.auth_tools import admin_required
from app.utils.file_security import safe_storage_path
from app.utils.response import APIResponse
from app.utils.site_domain import (
    DOMAIN_MODE_AUTO,
    DOMAIN_MODE_MANUAL,
    DOMAIN_MODES,
    DomainValidationError,
    get_site_domain_config,
    normalize_project_domain,
    save_site_domain_config,
    site_config_payload,
)
from app.utils.validators import validate_id_list


class AdminSettingNoticeResource(Resource):
    @admin_required
    def get(self):
        """获取通知设置"""
        setting = Setting.query.filter_by(alias='notice_setting').first()
        if not setting:
            return APIResponse.success(data={'users': []})
        return APIResponse.success(data={'users': json.loads(setting.value)})

    @admin_required
    def post(self):
        """更新通知设置"""
        data = request.json
        users = validate_id_list(data.get('users'))

        setting = Setting.query.filter_by(alias='notice_setting').first()
        if not setting:
            setting = Setting(alias='notice_setting')

        setting.value = json.dumps(users)
        setting.serialized = True
        db.session.add(setting)
        db.session.commit()
        return APIResponse.success(message='通知设置已更新')


class AdminSettingApiResource(Resource):
    @admin_required
    def get(self):
        """获取API配置"""
        settings = Setting.query.filter(Setting.group == 'api_setting').all()
        data = {
            'api_url': settings[0].value,
            'api_key': settings[1].value,
            'models': settings[2].value,
            'default_model': settings[3].value,
            'default_backup': settings[4].value
        }
        return APIResponse.success(data=data)

    @admin_required
    def post(self):
        """更新API配置"""
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
    @admin_required
    def get(self):
        """获取其他设置"""
        settings = Setting.query.filter(Setting.group == 'other_setting').all()
        data = {
            'prompt': settings[0].value,
            'threads': int(settings[1].value),
            'email_limit': settings[2].value
        }
        return APIResponse.success(data=data)


class AdminEditSettingOtherResource(Resource):
    @admin_required
    def post(self):
        """更新其他设置"""
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
    @admin_required
    def get(self):
        """获取站点设置（版本 + 项目域名）"""
        version_setting = Setting.query.filter_by(alias='version').first()
        data = {
            'version': version_setting.value if version_setting else 'community',
        }
        data.update(site_config_payload())
        return APIResponse.success(data=data)

    @admin_required
    def post(self):
        """更新站点版本与项目域名配置。

        兼容旧客户端：只传 version 时仍然只更新版本，不会创建域名配置行，
        升级站点因此保持原有行为。
        """
        data = request.get_json(silent=True) or {}
        if not data:
            return APIResponse.error('缺少必要参数', 400)

        version = data.get('version')
        if version is not None and version not in ['business', 'community']:
            return APIResponse.error('版本号无效', 400)

        domain_mode = data.get('domain_mode')
        if domain_mode is not None and domain_mode not in DOMAIN_MODES:
            return APIResponse.error('域名模式无效', 400)

        current = get_site_domain_config()
        target_mode = domain_mode if domain_mode is not None else current['domain_mode']
        domain_value = data.get('domain', current['domain'])
        domain_value = '' if domain_value is None else str(domain_value).strip()

        if target_mode == DOMAIN_MODE_MANUAL:
            try:
                domain_value = normalize_project_domain(domain_value)
            except DomainValidationError as exc:
                return APIResponse.error(str(exc), 400)
        elif target_mode == DOMAIN_MODE_AUTO and domain_value:
            # 自动模式下保留用户填写的备用地址，但仍然校验格式。
            try:
                domain_value = normalize_project_domain(domain_value)
            except DomainValidationError as exc:
                return APIResponse.error(str(exc), 400)

        try:
            if version is not None:
                version_setting = Setting.query.filter_by(alias='version').first()
                if version_setting is None:
                    version_setting = Setting(alias='version', group='site_setting')
                version_setting.value = version
                version_setting.group = 'site_setting'
                db.session.add(version_setting)

            if domain_mode is not None or data.get('domain') is not None:
                save_site_domain_config(
                    domain_mode=domain_mode,
                    domain=domain_value,
                )
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        if version is None:
            version_setting = Setting.query.filter_by(alias='version').first()
            version = version_setting.value if version_setting else 'community'

        payload = {'version': version}
        payload.update(site_config_payload())
        return APIResponse.success(data=payload, message='站点设置已更新')


# ----系统存储设置-----
# 获取系统路径存储文件列表
class SystemStorageResource(Resource):
    @admin_required
    def get(self):
        """获取文件列表"""
        try:
            base_dir = os.path.dirname(current_app.root_path)
            storage_path = os.path.join(base_dir, 'storage')

            if not os.path.exists(storage_path):
                return APIResponse.not_found("storage目录不存在")

            result = {}

            for category in os.listdir(storage_path):
                category_path = os.path.join(storage_path, category)
                if not os.path.isdir(category_path):
                    continue

                category_data = {"size": 0, "dates": {}}

                for date_dir in os.listdir(category_path):
                    date_path = os.path.join(category_path, date_dir)
                    if not os.path.isdir(date_path):
                        continue

                    date_data = {"size": 0, "files": []}

                    # 保持系统原生路径格式
                    for root, _, files in os.walk(date_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            try:
                                size = os.path.getsize(file_path)
                                date_data["files"].append({
                                    "path": file_path,  # 关键点：保持原生路径
                                    "size": size,
                                    "name": file
                                })
                                date_data["size"] += size
                            except OSError:
                                continue

                    category_data["size"] += date_data["size"]
                    category_data["dates"][date_dir] = date_data

                result[category] = category_data

            return APIResponse.success(data=result)

        except Exception as e:
            current_app.logger.error(f"获取文件列表失败: {str(e)}")
            return APIResponse.error("获取文件列表失败")

    @admin_required
    def delete(self):
        """删除（自动清理空目录）"""
        try:
            req = request.get_json()
            target = req.get("target")
            delete_type = req.get("type")

            if not target or not delete_type:
                return APIResponse.error("缺少必要参数")

            base_dir = os.path.dirname(current_app.root_path)
            storage_path = os.path.join(base_dir, 'storage')
            try:
                target_path = safe_storage_path(storage_path, *target.split('/'))
            except ValueError:
                return APIResponse.error("非法路径")

            # 执行删除
            if delete_type == "file":
                if not os.path.exists(target_path):
                    return APIResponse.not_found("文件不存在")

                # 删除文件
                os.remove(target_path)
                self._clean_empty_dirs(target_path)  # 自动清理空目录

            elif delete_type == "date":
                if not os.path.exists(target_path):
                    return APIResponse.not_found("日期目录不存在")
                shutil.rmtree(target_path)  # 删除整个日期目录

            elif delete_type == "category":
                if not os.path.exists(target_path):
                    return APIResponse.not_found("分类目录不存在")
                shutil.rmtree(target_path)  # 删除整个分类目录

            else:
                return APIResponse.error("无效操作类型")

            return APIResponse.success(message="删除成功")

        except PermissionError:
            return APIResponse.error("权限不足")
        except Exception as e:
            current_app.logger.error(f"删除失败: {str(e)}")
            return APIResponse.error("删除操作失败")

    def _clean_empty_dirs(self, file_path):
        """递归清理空目录"""
        current_dir = os.path.dirname(file_path)
        storage_root = os.path.join(os.path.dirname(current_app.root_path), 'storage')

        # 从文件所在目录向上清理，直到storage根目录
        while len(current_dir) > len(storage_root):
            try:
                if not os.listdir(current_dir):  # 如果是空目录
                    os.rmdir(current_dir)
                    current_dir = os.path.dirname(current_dir)  # 继续检查上级目录
                else:
                    break
            except OSError:
                break
