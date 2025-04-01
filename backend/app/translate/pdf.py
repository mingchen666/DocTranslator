import os
import logging
import shutil
import asyncio
import datetime
from pathlib import Path
from . import common, db, to_translate
import babeldoc.high_level
from babeldoc.document_il.translator.translator import OpenAITranslator
from babeldoc.docvision.doclayout import DocLayoutModel
from babeldoc.translation_config import TranslationConfig, WatermarkOutputMode

logger = logging.getLogger(__name__)


def clean_output_filename(original_path: Path, output_dir: str) -> Path:
    """清理babeldoc生成的多余后缀"""
    stem = original_path.stem.split('.')[0]
    new_path = Path(output_dir) / f"{stem}{original_path.suffix}"

    for suffix in [
        '.dual', '.mono',
        '.no_watermark.en.dual', '.no_watermark.en.mono',
        '.en.dual', '.en.mono',
        '.no_watermark.zh.mono', '.no_watermark.zh.dual',
        '.zh.dual', '.zh.mono',
        *[f'.no_watermark.{lang}.mono' for lang in ['ja', 'fr', 'de', 'es']],
        *[f'.no_watermark.{lang}.dual' for lang in ['ja', 'fr', 'de', 'es']],
        *[f'.{lang}.mono' for lang in ['ja', 'fr', 'de', 'es']],
        *[f'.{lang}.dual' for lang in ['ja', 'fr', 'de', 'es']]
    ]:
        temp_path = Path(output_dir) / f"{stem}{suffix}{original_path.suffix}"
        if temp_path.exists():
            shutil.move(temp_path, new_path)
            break

    return new_path if new_path.exists() else None


async def async_translate_pdf(trans):
    """异步PDF翻译核心函数"""
    try:
        start_time = datetime.datetime.now()
        original_path = Path(trans['file_path'])

        # 初始化翻译库
        babeldoc.high_level.init()

        # 转换语言代码
        target_lang = common.convert_language_name_to_code(trans['lang'])

        # 初始化文档布局模型
        doc_layout_model = DocLayoutModel.load_onnx()

        # 创建翻译器实例
        translator = OpenAITranslator(
            lang_in="auto",
            lang_out=target_lang,
            model=trans.get('model', 'gpt-4'),
            api_key=trans['api_key'],
            base_url=trans.get('api_url', 'https://api.openai.com/v1'),
            ignore_cache=False
        )

        # 完整翻译配置
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
            no_dual=True,  # 是否生成双语PDF
            no_mono=False,  # 是否生成单语PDF
        )

        # 执行翻译
        async for event in babeldoc.high_level.async_translate(config):
            if event["type"] == "progress":
                db.execute(
                    "UPDATE translate SET process=%s WHERE id=%s",
                    int(event["progress"] * 100),
                    trans['id']
                )
            elif event["type"] == "finish":
                # 处理输出文件名
                final_path = clean_output_filename(original_path, trans['target_path_dir'])

                # 更新数据库记录
                if final_path:
                    db.execute(
                        "UPDATE translate SET target_file=%s WHERE id=%s",
                        str(final_path),
                        trans['id']
                    )

                # 计算token使用量
                token_count = getattr(translator, 'token_count', 0)
                prompt_tokens = getattr(translator, 'prompt_token_count', 0)
                completion_tokens = getattr(translator, 'completion_token_count', 0)

                # 触发完成回调
                spend_time = (datetime.datetime.now() - start_time).total_seconds()
                to_translate.complete(
                    trans,
                    text_count=1,  # PDF按文件计数
                    spend_time=spend_time
                )
                return True

    except Exception as e:
        logger.error(f"PDF翻译失败: {str(e)}", exc_info=True)
        db.execute(
            "UPDATE translate SET status='failed', failed_reason=%s WHERE id=%s",
            str(e), trans['id']
        )
        return False


def translate_pdf(trans):
    """同步入口"""
    return asyncio.run(async_translate_pdf(trans))


def start(trans):
    """启动PDF翻译（与TXT翻译保持相同接口）"""
    try:
        # 参数检查
        original_path = Path(trans['file_path'])
        if not original_path.exists():
            raise FileNotFoundError(f"文件不存在: {trans['file_path']}")

        # 初始化任务状态
        db.execute(
            "UPDATE translate SET status='processing', process=0, start_at=NOW() WHERE id=%s",
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
