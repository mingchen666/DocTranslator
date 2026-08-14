import os
from importlib import import_module

from flask import current_app
from app.models.translate import Translate
from app.translate import to_translate


HANDLER_BY_EXTENSION = {
    '.docx': 'word',
    '.xlsx': 'excel',
    '.pptx': 'powerpoint',
    '.pdf': 'pdf',
    '.txt': 'txt',
    '.csv': 'csv_handle',
    '.md': 'md',
    '.html': 'html',
    '.htm': 'html',
}


def get_handler(extension):
    module_name = HANDLER_BY_EXTENSION.get(extension.lower())
    if module_name is None:
        return None
    return import_module(f'app.translate.{module_name}')


def main_wrapper(task_id, config, origin_path):
    """
    翻译任务核心逻辑
    :param task_id: 任务ID
    :param origin_path: 原始文件绝对路径
    :param target_path: 目标文件绝对路径
    :param config: 翻译配置字典
    :return: 是否成功
    """
    try:
        # 获取任务对象
        task = Translate.query.get(task_id)
        if not task:
            current_app.logger.error(f"任务 {task_id} 不存在")
            return False

        # 获取文件扩展名
        extension = os.path.splitext(origin_path)[1].lower()
        handler = get_handler(extension)
        if handler is None:
            current_app.logger.error(f"不支持的文件类型: {extension}")
            return False

        if config.get('server', 'openai') == 'baidu' and extension == '.pdf':
            current_app.logger.error('百度翻译暂不支持PDF文件')
            return False

        if config.get('server', 'openai') != 'baidu' and extension != '.pdf':
            config['_openai_client'] = to_translate.create_openai_client(
                config.get('api_url'), config.get('api_key')
            )

        return handler.start(trans=config)

    except Exception as e:
        current_app.logger.error(f"翻译任务执行异常: {str(e)}", exc_info=True)
        return False


def pdf_handler(config, origin_path):
    pass
    # return gptpdf.start(config)
    # if pdf.is_scanned_pdf(origin_path):
    #     return gptpdf.start(config)
    # else:
    #     # 这里均使用gptpdf实现
    #     return gptpdf.start(config)
    #     # return pdf.start(config)

