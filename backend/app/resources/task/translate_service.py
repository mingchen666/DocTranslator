import logging
import os
from datetime import datetime
from flask import current_app
from sqlalchemy import or_
from app.models.translate import Translate
from app.extensions import db
from ...models.comparison import Comparison
from ...models.prompt import Prompt
import pytz


class TranslateEngine:
    def __init__(self, task_id):
        self.task_id = task_id
        self.app = current_app._get_current_object()  # 获取真实app对象

    def execute(self):
        """Persist the task for execution by the dedicated worker."""
        try:
            with self.app.app_context():
                from app.task_queue import enqueue_translation
                return enqueue_translation(self.task_id)
        except Exception as e:
            self.app.logger.error(f"任务入队失败: {str(e)}", exc_info=True)
            try:
                with self.app.app_context():
                    self._complete_task(False, f"任务入队失败: {e}")
            except Exception:
                self.app.logger.error("记录任务入队失败状态时出错", exc_info=True)
            return False

    def run(self):
        """Execute one queued task synchronously inside a worker thread."""
        with self.app.app_context():
            try:
                task = self._prepare_task()
                success = self._execute_core(task)
                return self._complete_task(success)
            except Exception as e:
                self.app.logger.error(f"任务执行异常: {str(e)}", exc_info=True)
                self._complete_task(False, str(e))
                return False
            finally:
                db.session.remove()

    def _execute_core(self, task):
        """执行核心翻译逻辑"""
        try:
            from .main import main_wrapper

            # 构建符合要求的 trans 字典
            trans_config = self._build_trans_config(task)

            # 调用 main_wrapper 执行翻译
            return main_wrapper(task_id=task.id, config=trans_config,
                                origin_path=task.origin_filepath)
        except Exception as e:
            current_app.logger.error(f"翻译执行失败: {str(e)}", exc_info=True)
            raise

    def _prepare_task(self):
        """准备翻译任务"""
        task = db.session.get(Translate, self.task_id)
        if not task:
            raise ValueError(f"任务 {self.task_id} 不存在")

        # 验证文件存在性
        if not os.path.exists(task.origin_filepath):
            raise FileNotFoundError(f"原始文件不存在: {task.origin_filepath}")

        # 更新任务状态
        task.status = 'process'
        task.process = 0.00
        task.start_at = datetime.now(pytz.timezone(self.app.config['TIMEZONE']))  # 使用配置的时区
        task.end_at = None
        task.failed_reason = None
        db.session.commit()
        return task

    def _build_trans_config(self, task):
        """构建符合文件处理器要求的 trans 字典"""
        config = {
            'id': task.id,  # 任务ID
            'target_lang': task.lang,
            'uuid': task.uuid,
            'target_path_dir': os.path.dirname(task.target_filepath),
            'threads': task.threads,
            'file_path': task.origin_filepath,
            'target_file': task.target_filepath,
            'api_url': task.api_url,
            'api_key': task.api_key,
            # 机器翻译相关
            'app_id': task.app_id,
            'app_key': task.app_key,
            'type': task.type,
            'lang': task.lang,
            'server': task.server,
            'run_complete': True,
            'model': task.model,
            'backup_model': task.backup_model,
            'comparison_id': task.comparison_id,
            'prompt_id': task.prompt_id,
            'prompt': self._get_final_prompt(task),
            'terms_dict': (
                self._get_matched_terms(task)
                if task.server != 'baidu' and task.comparison_id
                else None
            ),
            'use_baidu_terms': self._should_use_baidu_terms(task),
            'extension': os.path.splitext(task.origin_filepath)[1]

        }

        return config

    def _get_final_prompt(self, task):
        """
        获取最终的prompt
        优先使用prompt_id对应的模板，其次使用task.prompt
        """
        # 如果有prompt_id，查询数据库
        if task.prompt_id and task.prompt_id != 0:
            prompt_obj = db.session.query(Prompt).filter(
                Prompt.id == task.prompt_id,
                Prompt.deleted_flag == 'N',
                or_(
                    Prompt.customer_id == task.customer_id,
                    Prompt.share_flag == 'Y',
                ),
            ).first()
            if not prompt_obj or not prompt_obj.content:
                raise ValueError(f"提示词模板 {task.prompt_id} 不存在或无权使用")

            logging.info(f"[任务{task.id}] 使用提示词模板ID: {task.prompt_id}")
            return prompt_obj.content

        # 使用任务中的prompt
        prompt = task.prompt or "请将以下文本翻译成{target_lang}，保持原文的格式和风格："

        logging.info(f"[任务{task.id}] 使用任务自带prompt")
        return prompt

    def _get_matched_terms(self, task):
        """
        获取术语库内容（用于AI翻译动态匹配）
        返回解析后的术语对列表
        """
        if not task.comparison_id or task.comparison_id == 0:
            logging.info(f"[任务{task.id}] 未设置术语库ID")
            return None

        logging.info(f"[任务{task.id}] 开始查询术语库ID: {task.comparison_id}")

        comparison = db.session.query(Comparison).filter(
            Comparison.id == task.comparison_id,
            Comparison.deleted_flag == 'N',
            or_(
                Comparison.customer_id == task.customer_id,
                Comparison.share_flag == 'Y',
            ),
        ).first()

        if not comparison:
            raise ValueError(f"术语库 {task.comparison_id} 不存在或无权使用")

        if not comparison.content or comparison.content.strip() == '':
            raise ValueError(f"术语库 {task.comparison_id} 内容为空")

        logging.info(
            f"[任务{task.id}] 找到术语库: {comparison.title}, 内容长度: {len(comparison.content)}")

        # 解析术语库内容
        terms_content = comparison.content.strip()
        term_pairs = []

        # 支持多种分隔符
        separator = ';'
        if ';' not in terms_content:
            if '\n' in terms_content:
                separator = '\n'
            elif '|' in terms_content:
                separator = '|'

        for term_pair in terms_content.split(separator):
            term_pair = term_pair.strip()
            if not term_pair:
                continue

            # 支持多种格式：逗号、制表符、冒号
            if ',' in term_pair:
                parts = term_pair.split(',', 1)
            elif '\t' in term_pair:
                parts = term_pair.split('\t', 1)
            elif ':' in term_pair:
                parts = term_pair.split(':', 1)
            else:
                continue

            source_term = parts[0].strip()
            target_term = parts[1].strip()

            if source_term and target_term:
                term_pairs.append({
                    'source': source_term,
                    'target': target_term
                })

        if not term_pairs:
            raise ValueError(f"术语库 {task.comparison_id} 没有可用术语")

        logging.info(f"[任务{task.id}] 成功解析术语库，共 {len(term_pairs)} 个术语对")
        return term_pairs

    def _should_use_baidu_terms(self, task):
        """
        判断百度翻译是否启用术语库
        """
        if task.server != 'baidu':
            return False

        # 百度翻译：comparison_id=1表示启用术语库
        return task.comparison_id == 1

    def _complete_task(self, success, failure_reason=None):
        """更新任务状态"""
        try:
            # Lower-level handlers use a separate SQL connection for progress
            # and failure updates. Refresh before deciding the final state so
            # a recorded failure cannot be overwritten by a late success.
            db.session.expire_all()
            task = db.session.get(Translate, self.task_id)
            if task:
                if success and task.status != 'failed':
                    if not task.target_filepath or not os.path.isfile(task.target_filepath):
                        success = False
                        failure_reason = failure_reason or '翻译未生成目标文件'

                if success:
                    from app.result_storage import commit_completed_result

                    try:
                        commit_completed_result(
                            task,
                            datetime.now(pytz.timezone(
                                self.app.config['TIMEZONE']
                            )),
                        )
                        return True
                    except Exception as exc:
                        db.session.rollback()
                        self.app.logger.error(
                            '翻译结果持久化失败，任务ID=%s，错误类型=%s',
                            self.task_id,
                            type(exc).__name__,
                        )
                        task = db.session.get(Translate, self.task_id)
                        success = False
                        failure_reason = (
                            '翻译结果持久化失败，请检查结果存储配置和网络'
                        )

                if not success:
                    task.status = 'failed'
                    task.process = 0.00
                    if not task.failed_reason:
                        task.failed_reason = str(
                            failure_reason or '翻译任务失败'
                        )[:500]
                    task.end_at = datetime.now(
                        pytz.timezone(self.app.config['TIMEZONE'])
                    )
                    db.session.commit()
                    return False
            return False
        except Exception as e:
            db.session.rollback()
            self.app.logger.error(
                '状态更新失败，任务ID=%s，错误类型=%s',
                self.task_id,
                type(e).__name__,
            )
            return False


