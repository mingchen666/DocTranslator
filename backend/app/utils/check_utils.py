# utils/ai_utils.py
import openai
from io import BytesIO
import fitz  # PyMuPDF
import logging


class AIChecker:
    @staticmethod
    def check_openai_connection(api_url: str, api_key: str, model: str, timeout: int = 10):
        """OpenAI连通性测试[^1]"""
        try:
            openai.api_key = api_key
            openai.base_url = api_url

            # 使用更轻量的列表模型接口测试
            response = openai.models.list(timeout=timeout)
            return any(m.id == model for m in response.data), None
        except Exception as e:
            logging.error(f"OpenAI连接测试失败: {str(e)}")
            return False, str(e)

    @staticmethod
    def check_pdf_scanned(file_stream: BytesIO):
        """PDF扫描件检测[^2]"""
        try:
            file_stream.seek(0)
            doc = fitz.open(stream=file_stream.read(), filetype="pdf")
            pages_to_check = min(5, len(doc))

            for page_num in range(pages_to_check):
                page = doc[page_num]
                if page.get_text().strip():  # 发现可编辑文本
                    return False
                if page.get_images():  # 发现图像
                    return True
            return False
        except Exception as e:
            logging.error(f"PDF检测失败: {str(e)}")
            raise
