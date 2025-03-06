# tasks/translate.py
import subprocess

from flask import current_app

from app import db
from app.models.translate import Translate


def start_translate_task(task_id):
    """启动翻译子进程[^2]"""
    translate = Translate.query.get(task_id)
    if not translate:
        return False

    try:
        # 构建命令参数
        storage_path = current_app.config['UPLOAD_FOLDER']
        cmd = [
            'python3',
            'translate/main.py',
            translate.uuid,
            storage_path
        ]

        # 启动子进程
        subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # 更新任务状态
        translate.status = 'process'
        db.session.commit()
        return True

    except Exception as e:
        translate.status = 'failed'
        translate.failed_reason = str(e)
        db.session.commit()
        return False
