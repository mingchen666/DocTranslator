# utils/translate_utils.py
from typing import List
import subprocess
from pathlib import Path
import zipfile
from io import BytesIO
from datetime import datetime

class TranslateUtils:
    @staticmethod
    def execute_python_script(script_path: str, args: List[str], timeout: int = 120):
        """执行Python脚本并处理超时[^1]"""
        try:
            result = subprocess.run(
                ['python3', script_path] + args,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.stdout.strip(), None
        except subprocess.TimeoutExpired:
            return None, '操作超时'
        except Exception as e:
            return None, str(e)

    @staticmethod
    def generate_zip(files: List[tuple]) -> BytesIO:
        """生成内存ZIP文件流[^2]"""
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_path, arcname in files:
                zip_file.write(file_path, arcname)
        zip_buffer.seek(0)
        return zip_buffer

    @staticmethod
    def get_preset_settings() -> dict:
        """获取预设配置[^5]"""
        return {
            'models': ['gpt-3.5-turbo', 'gpt-4'],
            'default_model': 'gpt-3.5-turbo',
            'max_threads': 10,
            'prompt_template': '将以下内容翻译为{target_lang}'
        }
