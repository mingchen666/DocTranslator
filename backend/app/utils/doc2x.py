import os

import requests
import time
from flask import current_app


class Doc2XService:
    BASE_URL = "https://v2.doc2x.noedgeai.com/api/v2"

    @staticmethod
    def _make_request(api_key, method, endpoint, data=None, files=None):
        """统一请求方法"""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        } if method != "upload" else {
            "Authorization": f"Bearer {api_key}"
        }

        url = f"{Doc2XService.BASE_URL}/{endpoint}"
        try:
            if method == "upload":
                response = requests.post(url, headers=headers, data=files)
            else:
                response = requests.request(
                    method.lower(),
                    url,
                    headers=headers,
                    json=data if data else None
                )

            result = response.json()
            if result.get("code") != "success":
                raise Exception(result.get("msg", "API 请求失败"))
            return result["data"]
        except Exception as e:
            current_app.logger.error(f"doc2x 请求失败: {str(e)}")
            raise

    @staticmethod
    def start_task(api_key: str, file_path: str) -> str:
        """阶段1: 启动任务 (parse/pdf)"""
        with open(file_path, 'rb') as f:
            return Doc2XService._make_request(
                api_key,
                "upload",
                "parse/pdf",
                files=f
            )["uid"]

    @staticmethod
    def check_parse_status(api_key: str, uid: str) -> dict:
        """检查解析状态"""
        data = Doc2XService._make_request(
            api_key,
            "GET",
            f"parse/status?uid={uid}"
        )

        # 确保包含所有doc2x可能返回的状态
        if "status" not in data:
            raise Exception("无效的API响应：缺少status字段")

        return {
            "status": data["status"],  # processing/success/failed
            "progress": data.get("progress", 0),
            "detail": data.get("detail", "")
        }

    @staticmethod
    def trigger_export(api_key: str, uid: str, filename: str) -> bool:
        """触发导出（返回是否成功触发）"""
        data = {
            "uid": uid,
            "to": "docx",  # 导出为Word文档
            "formula_mode": "normal",
            "filename": f"{filename}.docx"  # 确保扩展名正确
        }
        result = Doc2XService._make_request(
            api_key,
            "POST",
            "convert/parse",
            data=data
        )
        return result.get("status") == "processing"

    @staticmethod
    def download_file(url: str, save_path: str) -> bool:
        """下载文件并验证完整性"""
        try:
            # 创建临时文件
            temp_path = f"{save_path}.tmp"

            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(temp_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)

            # 验证文件大小
            if os.path.getsize(temp_path) == 0:
                raise Exception("下载文件为空")

            # 重命名为正式文件
            os.rename(temp_path, save_path)
            return True

        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            current_app.logger.error(f"文件下载失败: {str(e)}")
            raise

    @staticmethod
    def check_export_status(api_key: str, uid: str, timeout=300) -> str:
        """阶段4: 轮询导出结果 (convert/parse/result)"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            data = Doc2XService._make_request(
                api_key,
                "GET",
                f"convert/parse/result?uid={uid}"
            )
            if data["status"] == "success":
                return data["url"]
            elif data["status"] == "failed":
                raise Exception("导出任务失败")
            time.sleep(2)  # 合理轮询间隔
        raise TimeoutError("导出结果等待超时")
