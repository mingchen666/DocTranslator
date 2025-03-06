import logging
import os
import datetime
from typing import Optional, Dict, Tuple, List

from app.translate import to_translate
from .pdf_parse import parse_pdf  # 假设原始PDF处理模块位于当前目录的gptpdf.py中

def start(trans: Dict) -> bool:
    """
    PDF翻译任务启动方法
    参数结构示例：
    trans = {
        'id': 任务ID,
        'file_path': 源文件路径,
        'target_file': 目标文件路径,
        'api_key': OpenAI API密钥,
        'base_url': API基础地址,
        'model': 模型名称,
        'output_dir': 输出目录,
        'verbose': 是否保留中间文件,
        'temperature': 温度参数,
        'max_tokens': 最大token数,
        'top_p': top_p参数,
        'frequency_penalty': 频率惩罚参数,
        'run_complete': 是否调用完成回调,
        # ...其他参数
    }
    """
    try:
        # 初始化输出目录
        output_dir = trans.get('output_dir', './temp_pdf')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 记录任务开始时间
        start_time = datetime.datetime.now()

        # 调用 parse_pdf 处理PDF
        content, image_paths = parse_pdf(
            pdf_path=trans['file_path'],
            output_dir=output_dir,
            prompt=None,  # 使用默认提示词
            api_key=trans['api_key'],
            base_url=trans['base_url']+'/v1',
            model=trans['model'],
            verbose=trans.get('verbose', False),
            gpt_worker=int(trans.get('threads', 1)),  # 默认使用 1 个线程
            temperature=trans.get('temperature', 0.5),
            max_tokens=trans.get('max_tokens', 1000),
            top_p=trans.get('top_p', 0.9),
            frequency_penalty=trans.get('frequency_penalty', 1)
        )

        # 保存最终结果
        save_final_result(content, trans['target_file'])

        # 清理临时文件
        if not trans.get('verbose', False):
            cleanup_temp_files(output_dir, image_paths)

        # 计算耗时
        end_time = datetime.datetime.now()
        spend_time = (end_time - start_time).total_seconds()

        # 任务完成处理
        if trans.get('run_complete'):
            to_translate.complete(trans, len(content), spend_time)

        return True

    except Exception as e:
        error_msg = f"PDF处理失败: {str(e)}"
        to_translate.error(trans['id'], error_msg)
        return False

def save_final_result(content: str, target_path: str) -> None:
    """保存最终结果"""
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(content)
    logging.info(f"结果已保存至：{target_path}")

def cleanup_temp_files(output_dir: str, image_paths: List[str]) -> None:
    """清理临时文件"""
    for path in image_paths:
        if os.path.exists(path):
            os.remove(path)
    if os.path.exists(output_dir):
        os.rmdir(output_dir)



