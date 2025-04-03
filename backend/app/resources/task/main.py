import threading
import time
from datetime import datetime
import os
import traceback
from flask import current_app
from app.extensions import db
from app.models.comparison import Comparison
from app.models.prompt import Prompt
from app.models.translate import Translate
from app.translate import word, excel, powerpoint, pdf, txt, csv_handle, md, to_translate


def main_wrapper(task_id, config, origin_path):
    """
    翻译任务核心逻辑（支持多参数）[^4]
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
            # 设置OpenAI API

        # 初始化翻译配置
        _init_translate_config(task)
        to_translate.init_openai(config['api_url'], config['api_key'])
        # 获取文件扩展名
        extension = os.path.splitext(origin_path)[1].lower()
        print('文件扩展名',extension,origin_path)
        # 调用文件处理器
        handler_map = {
            ('.docx', '.doc'): word,
            ('.xlsx', '.xls'): excel,
            ('.pptx', '.ppt'): powerpoint,
            ('.pdf',): pdf,
            ('.txt',): txt,
            ('.csv',): csv_handle,
            ('.md',): md
        }

        # 查找匹配的处理器
        for ext_group, handler in handler_map.items():
            if extension in ext_group:
                # if extension == '.pdf':
                #     status = handler(config, origin_path)  # 传递 origin_path
                # else:
                #     status = handler.start(config)  # 传递翻译配置
                status = handler.start(
                    # origin_path=origin_path,
                    # target_path=target_path,
                    trans=config  # 传递翻译配置
                )
                print('config配置项', config)
                return status

        current_app.logger.error(f"不支持的文件类型: {extension}")
        return False

    except Exception as e:
        current_app.logger.error(f"翻译任务执行异常: {str(e)}", exc_info=True)
        return False


    # return gptpdf.start(config)
    # if pdf.is_scanned_pdf(origin_path):
    #     return gptpdf.start(config)
    # else:
    #     # 这里均使用gptpdf实现
    #     return gptpdf.start(config)
    return pdf.start(config)
def _init_translate_config(trans):
    """
    初始化翻译配置[^5]
    :param trans: 翻译任务对象
    """
    # 设置OpenAI API
    if trans.api_url and trans.api_key:
        set_openai_config(trans.api_url, trans.api_key)

    # 加载术语对照表
    if trans.comparison_id:
        comparison = get_comparison(trans.comparison_id)
        trans.prompt = f"{comparison}\n{trans.prompt}"

    # 加载提示词模板
    if trans.prompt_id:
        prompt = get_prompt(trans.prompt_id)
        trans.prompt = prompt


def set_openai_config(api_url, api_key):
    """
    设置OpenAI API配置[^6]
    """
    import openai
    openai.api_base = api_url
    openai.api_key = api_key


def get_comparison(comparison_id):
    """
    加载术语对照表
    :param comparison_id: 术语对照表ID
    :return: 术语对照表内容
    """
    comparison = db.session.query(Comparison).filter_by(id=comparison_id).first()
    if comparison and comparison.content:
        return comparison.content.replace(',', ':').replace(';', '\n')
    return ""


def get_prompt(prompt_id):
    """
    加载提示词模板
    :param prompt_id: 提示词模板ID
    :return: 提示词内容
    """
    prompt = db.session.query(Prompt).filter_by(id=prompt_id).first()
    if prompt and prompt.content:
        return prompt.content
    return ""
