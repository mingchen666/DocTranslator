import os
import logging
import shutil
import asyncio
import datetime
from pathlib import Path

# 修复导入路径
from babeldoc.format.pdf import high_level
from babeldoc.translator.translator import OpenAITranslator
from babeldoc.docvision.table_detection.rapidocr import RapidOCRModel
from babeldoc.format.pdf.translation_config import TranslationConfig, WatermarkOutputMode

from . import common, db, to_translate
from babeldoc.docvision.doclayout import DocLayoutModel

logger = logging.getLogger(__name__)


def clean_output_filename(original_path: Path, output_dir: str) -> Path:
    """清理babeldoc生成的多余后缀"""
    stem = original_path.stem.split('.')[0]
    new_path = Path(output_dir) / f"{stem}{original_path.suffix}"

    # 支持所有可能的输出文件名变体
    possible_suffixes = [
        '.dual', '.mono',
        '.no_watermark.en.dual', '.no_watermark.en.mono',
        '.en.dual', '.en.mono',
        '.no_watermark.zh.mono', '.no_watermark.zh.dual',
        '.zh.dual', '.zh.mono',
        '.no_watermark.zh.mono',
        '.no_watermark.en.mono',
        'no_watermark.ko.mono',
        'no_watermark.ru.mono',
        'no_watermark.es.mono',
        'no_watermark.pt.mono',
        'no_watermark.fr.mono',
        'no_watermark.it.mono',
        'no_watermark.de.mono',
        'no_watermark.ar.mono',
        'no_watermark.ja.mono'
    ]

    for suffix in possible_suffixes:
        temp_path = Path(output_dir) / f"{stem}{suffix}{original_path.suffix}"
        if temp_path.exists():
            shutil.move(temp_path, new_path)
            logger.info(f"重命名文件: {temp_path} -> {new_path}")
            break

    return new_path if new_path.exists() else None


async def async_translate_pdf(trans):
    """异步PDF翻译核心函数"""
    try:
        start_time = datetime.datetime.now()
        original_path = Path(trans['file_path'])

        logger.info(f"开始翻译PDF: {original_path}")

        # 初始化翻译库
        high_level.init()

        # 转换语言代码
        target_lang = common.convert_language_name_to_code(trans['lang'])
        logger.info(f"目标语言: {target_lang}")

        # 初始化文档布局模型
        doc_layout_model = DocLayoutModel.load_onnx()
        logger.info("文档布局模型加载完成")

        # 初始化表格模型（根据参数决定是否启用）
        table_model = RapidOCRModel() if trans.get('translate_table', False) else None
        if table_model:
            logger.info("表格识别模型已启用")

        # 创建翻译器实例
        translator = OpenAITranslator(
            lang_in="auto",
            lang_out=target_lang,
            model=trans.get('model', 'gpt-4o-mini'),  # 使用更常见的默认模型
            api_key=trans['api_key'],
            base_url=trans.get('api_url', 'https://api.openai.com/v1'),
            ignore_cache=False,
        )
        logger.info(f"翻译器初始化完成，模型: {trans.get('model', 'gpt-4o-mini')}")

        # 完整翻译配置 - 修复参数名和类型
        config = TranslationConfig(
            input_file=str(original_path),
            output_dir=str(trans['target_path_dir']),
            translator=translator,
            lang_in="auto",
            lang_out=target_lang,
            doc_layout_model=doc_layout_model,
            watermark_output_mode=WatermarkOutputMode.NoWatermark,
            min_text_length=5,
            pages=None,
            qps=3,
            table_model=table_model,
            no_dual=True,  # 只生成单语PDF
            no_mono=False,  # 生成单语PDF
            split_short_lines=True,
            skip_clean=True,
            skip_scanned_detection=True,  # 先跳过扫描检测以提高性能
            debug=trans.get('debug', False),
            # 确保这些参数存在
            formular_font_pattern=trans.get('formular_font_pattern'),
            formular_char_pattern=trans.get('formular_char_pattern'),
            dual_translate_first=trans.get('dual_translate_first', False),
            disable_rich_text_translate=trans.get('disable_rich_text_translate', False),
            enhance_compatibility=trans.get('enhance_compatibility', False),
            use_alternating_pages_dual=trans.get('use_alternating_pages_dual', False),
            report_interval=0.1,
            custom_system_prompt=trans.get('custom_system_prompt'),
            working_dir=trans.get('working_dir'),
            auto_extract_glossary=trans.get('auto_extract_glossary', False),
            auto_enable_ocr_workaround=trans.get('auto_enable_ocr_workaround', False),
            only_include_translated_page=trans.get('only_include_translated_page', False),
            save_auto_extracted_glossary=trans.get('save_auto_extracted_glossary', False),
            enable_graphic_element_process=not trans.get('disable_graphic_element_process', False),
            merge_alternating_line_numbers=trans.get('merge_alternating_line_numbers', True),
            skip_translation=trans.get('skip_translation', False),
            skip_form_render=trans.get('skip_form_render', False),
            skip_curve_render=trans.get('skip_curve_render', False),
            only_parse_generate_pdf=trans.get('only_parse_generate_pdf', False),
            pool_max_workers=trans.get('pool_max_workers'),
            term_pool_max_workers=trans.get('term_pool_max_workers'),
        )

        logger.info("开始执行PDF翻译...")

        # 执行翻译 - 修复事件处理逻辑
        async for event in high_level.async_translate(config):
            logger.debug(f"收到事件: {event}")

            if event["type"] == "progress_update":  # 修复事件类型
                progress = event.get("overall_progress", 0)
                db.execute(
                    "UPDATE translate SET process=%s WHERE id=%s",
                    int(progress),
                    trans['id']
                )
                logger.info(f"翻译进度: {progress}%")

            elif event["type"] == "finish":
                logger.info("翻译完成")
                # 处理输出文件名
                final_path = clean_output_filename(original_path, trans['target_path_dir'])

                # 更新数据库记录
                if final_path and final_path.exists():
                    db.execute(
                        "UPDATE translate SET target_file=%s WHERE id=%s",
                        str(final_path),
                        trans['id']
                    )
                    logger.info(f"输出文件: {final_path}")

                # 计算token使用量
                spend_time = (datetime.datetime.now() - start_time).total_seconds()

                # 触发完成回调
                to_translate.complete(
                    trans,
                    text_count=1,  # PDF按文件计数
                    spend_time=spend_time
                )
                return True

            elif event["type"] == "error":
                error_msg = event.get("error", "未知错误")
                logger.error(f"翻译过程中出现错误: {error_msg}")
                db.execute(
                    "UPDATE translate SET status='failed', failed_reason=%s WHERE id=%s",
                    str(error_msg), trans['id']
                )
                return False

    except Exception as e:
        logger.error(f"PDF翻译失败: {str(e)}", exc_info=True)
        db.execute(
            "UPDATE translate SET status='failed', failed_reason=%s WHERE id=%s",
            str(e), trans['id']
        )
        return False


def translate_pdf(trans):
    """同步入口"""
    # 检查是否已经在事件循环中
    try:
        loop = asyncio.get_running_loop()
        # 如果在事件循环中，使用 run_coroutine_threadsafe
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, async_translate_pdf(trans))
            return future.result()
    except RuntimeError:
        # 没有事件循环，直接运行
        return asyncio.run(async_translate_pdf(trans))


def start(trans):
    """启动PDF翻译（与TXT翻译保持相同接口）"""
    try:
        # 参数检查
        original_path = Path(trans['file_path'])
        if not original_path.exists():
            raise FileNotFoundError(f"文件不存在: {trans['file_path']}")

        if not original_path.suffix.lower().endswith('.pdf'):
            raise ValueError(f"文件不是PDF格式: {trans['file_path']}")

        # 初始化任务状态
        db.execute(
            "UPDATE translate SET status='process', process=0, start_at=NOW() WHERE id=%s",
            trans['id']
        )

        # 确保输出目录存在
        os.makedirs(trans['target_path_dir'], exist_ok=True)

        # 执行翻译
        success = translate_pdf(trans)

        if not success:
            raise RuntimeError("PDF翻译过程失败")

        return True

    except Exception as e:
        logger.error(f"PDF任务初始化失败: {str(e)}")
        db.execute(
            "UPDATE translate SET status='failed', failed_reason=%s WHERE id=%s",
            str(e), trans['id']
        )
        return False
