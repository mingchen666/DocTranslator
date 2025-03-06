import os
import threading
from threading import Thread
from flask import current_app
from app.models.translate import Translate
from app.extensions import db
from .main import main_wrapper
from ...models.comparison import Comparison
from ...models.prompt import Prompt




class TranslateEngine99:
    def __init__(self, task_id):
        self.task_id = task_id
        self.app = current_app._get_current_object()  # 获取真实app对象

    def execute(self):
        """启动翻译任务入口"""
        try:
            # 主线程预处理
            with self.app.app_context():
                task = self._prepare_task()

            # 启动异步线程（传递真实app对象）
            thr = threading.Thread(
                target=self._async_wrapper,
                args=(self.app, self.task_id)
            )
            thr.start()
            return True
        except Exception as e:
            self.app.logger.error(f"任务初始化失败: {str(e)}", exc_info=True)
            return False

    def _async_wrapper(self, app, task_id):
        """异步执行包装器"""
        with app.app_context():
            try:
                # 每个线程独立获取任务对象
                task = db.session.query(Translate).get(task_id)
                self._async_execute(task)
            except Exception as e:
                app.logger.error(f"任务执行异常: {str(e)}", exc_info=True)
                self._complete_task(False)
            finally:
                db.session.remove()  # 关键：清理线程会话

    def _async_execute(self, task):
        """执行核心翻译逻辑"""
        try:
            # 初始化配置（使用线程内session）
            config = self._build_config(task)

            # 调用翻译核心
            success = main_wrapper(
                task=task,
                origin_path=task.origin_filepath,
                target_path=task.target_filepath,
                config=config
            )
            self._complete_task(success)
        except Exception as e:
            current_app.logger.error(f"翻译执行失败: {str(e)}", exc_info=True)
            self._complete_task(False)

    def _build_config(self, task):
        """构建线程安全配置"""
        return {
            'lang': task.lang,
            'model': task.model,
            'type': task.type,
            'prompt': self._load_prompt(task),
            'threads': task.threads,
            'api_url': task.api_url,
            'api_key': task.api_key,
            'comparison': self._load_comparison(task.comparison_id)
        }

    def _load_prompt(self, task):
        """加载提示词（线程安全）"""
        if task.prompt_id:
            prompt = db.session.query(Prompt).get(task.prompt_id)
            return prompt.content if prompt else ""
        return task.prompt

    def _load_comparison(self, comparison_id):
        """加载术语对照表（线程安全）"""
        if not comparison_id:
            return ""
        comparison = db.session.query(Comparison).get(comparison_id)
        return comparison.content.replace(',', ':').replace(';', '\n') if comparison else ""

    def _prepare_task(self):
        """任务预处理"""
        task = db.session.query(Translate).get(self.task_id)
        if not task:
            raise ValueError(f"任务 {self.task_id} 不存在")

        if not os.path.exists(task.origin_filepath):
            raise FileNotFoundError(f"文件不存在: {task.origin_filepath}")

        task.status = 'process'
        task.start_at = db.func.now()
        db.session.commit()
        return task

    def _complete_task(self, success):
        """完成处理"""
        try:
            task = db.session.query(Translate).get(self.task_id)
            task.status = 'done' if success else 'failed'
            task.end_at = db.func.now()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            self.app.logger.error(f"状态更新失败: {str(e)}", exc_info=True)




class TranslateEngine666:
    def __init__(self, task_id):
        self.task_id = task_id
        self.app = current_app._get_current_object()  # 获取真实app对象

    def _build_trans_config(self, task):
            """构建符合文件处理器要求的trans字典"""
            return {
                'id': task.id,  # 任务ID
                'threads': task.threads,
                'file_path': task.origin_filepath,  # 原始文件绝对路径
                'target_file': task.target_filepath,  # 目标文件绝对路径
                'api_url': task.api_url,
                'api_key': task.api_key,  # 新增API密钥字段
                'type': task.type,
                'lang': task.lang,
                'run_complete': True,  # 默认设为True
                # 以下是可能需要添加的额外字段
                'prompt': task.prompt,
                'model': task.model,
                'backup_model': task.backup_model,
                'comparison_id': task.comparison_id,
                'prompt_id': task.prompt_id,
                'extension':'.docx'
            }

    def execute(self):
        """启动任务入口"""
        try:
            # 在主线程上下文中准备任务
            with self.app.app_context():
                task = self._prepare_task()

            # 启动线程时传递真实app对象和任务ID
            thr = Thread(
                target=self._async_wrapper,
                args=(self.app, self.task_id)
            )
            thr.start()
            return True
        except Exception as e:
            self.app.logger.error(f"任务初始化失败: {str(e)}", exc_info=True)
            return False

    def _async_wrapper(self, app, task_id):
        """异步执行包装器"""
        with app.app_context():
            from app.extensions import db  # 确保在每个线程中导入
            try:
                # 使用新会话获取任务对象
                task = db.session.query(Translate).get(task_id)
                if not task:
                    app.logger.error(f"任务 {task_id} 不存在")
                    return

                # 执行核心逻辑
                success = self._execute_core(task)
                self._complete_task(success)
            except Exception as e:
                app.logger.error(f"任务执行异常: {str(e)}", exc_info=True)
                self._complete_task(False)
            finally:
                db.session.remove()  # 重要！清理线程局部session

    def _execute_core(self, task):
        """执行核心翻译逻辑"""
        try:
            # 初始化翻译配置
            self._init_translate_config(task)

            # 选择处理器
            handler = self._get_file_handler(task.origin_filepath)
            if not handler:
                current_app.logger.error(f"不支持的文件类型: {task.origin_filepath}")
                return False

            # 构建符合要求的trans字典
            trans_config = self._build_trans_config(task)

            # 调用处理器
            return handler.start(trans=trans_config)  # 正确传递参数
        except Exception as e:
            current_app.logger.error(f"翻译执行失败: {str(e)}", exc_info=True)
            return False

    def _prepare_task(self):
        """准备翻译任务"""
        task = Translate.query.get(self.task_id)
        if not task:
            raise ValueError(f"任务 {self.task_id} 不存在")

        # 验证文件存在性
        if not os.path.exists(task.origin_filepath):
            raise FileNotFoundError(f"原始文件不存在: {task.origin_filepath}")

        # 更新任务状态
        task.status = 'process'
        task.start_at = db.func.now()
        db.session.commit()
        return task

    def _init_translate_config(self, task):
        """初始化翻译配置"""
        if task.api_url and task.api_key:
            import openai
            openai.api_base = task.api_url
            openai.api_key = task.api_key

        # 加载术语对照表
        if task.comparison_id:
            from app.models import Comparison
            comparison = db.session.query(Comparison).get(task.comparison_id)
            if comparison:
                task.prompt = f"术语对照表:\n{comparison.content.replace(',', ':')}\n{task.prompt}"

        # 加载提示词模板
        if task.prompt_id:
            from app.models import Prompt
            prompt = db.session.query(Prompt).get(task.prompt_id)
            if prompt:
                task.prompt = prompt.content

    def _get_file_handler(self, file_path):
        from app.translate import (
            word, excel, powerpoint, pdf,
            gptpdf, txt, csv_handle, md
        )

        try:
            current_app.logger.debug(f"正在解析文件路径: {file_path}")
            # 标准化路径（处理不同OS的斜杠和大小写）
            normalized_path = os.path.normpath(file_path).lower()
            current_app.logger.debug(f"标准化路径: {normalized_path}")

            ext = os.path.splitext(normalized_path)[1]
            # 获取标准化后的扩展名
            # ext = os.path.splitext(file_path)[1].lower()
            current_app.logger.debug(f"提取的扩展名: {ext}")

            # 处理器映射表
            handler_map = {
                '.docx': word,
                '.doc': word,
                '.xlsx': excel,
                '.xls': excel,
                '.pptx': powerpoint,
                '.ppt': powerpoint,
                '.pdf': pdf,#if not pdf.is_scanned_pdf(file_path) else gptpdf,
                '.txt': txt,
                '.csv': csv_handle,
                '.md': md
            }

            current_app.logger.debug(f"当前处理器映射表: {handler_map}")

            # 匹配处理器
            handler = handler_map.get(ext)
            if not handler:
                current_app.logger.error(f"未找到匹配的处理器，扩展名: {ext}")
                return None

            current_app.logger.info(f"成功匹配处理器: {handler.__name__}")
            return handler

        except Exception as e:
            current_app.logger.error(f"获取文件处理器失败: {str(e)}", exc_info=True)
            return None

    def _build_config(self, task):
        """构建配置字典"""
        return {
            'lang': task.lang,
            'model': task.model,
            'type': task.type,
            'prompt': task.prompt,
            'threads': task.threads,
            'api_url': task.api_url,
            'api_key': task.api_key,
            'origin_lang': task.origin_lang,
            'backup_model': task.backup_model,
            'doc2x_flag': task.doc2x_flag,
            'doc2x_secret_key': task.doc2x_secret_key,
            'comparison_id': task.comparison_id,
            'word_count': task.word_count,
            'prompt_id': task.prompt_id,
            'rand_user_id': task.rand_user_id,
            'origin_filesize': task.origin_filesize,
            'origin_filename': task.origin_filename,
            'target_filesize': task.target_filesize,
            'target_filename': task.target_filename,
            'target_filepath': task.target_filepath,
            'origin_filepath': task.origin_filepath,
        }

    def _complete_task(self, success):
        """更新任务状态"""
        from app.extensions import db
        try:
            with self.app.app_context():
                task = db.session.query(Translate).get(self.task_id)
                if task:
                    task.status = 'done' if success else 'failed'
                    task.end_at = db.func.now()
                    db.session.commit()
        except Exception as e:
            db.session.rollback()
            self.app.logger.error(f"状态更新失败: {str(e)}", exc_info=True)




class TranslateEngine9999:
    def __init__(self, task_id):
        self.task_id = task_id
        self.app = current_app._get_current_object()  # 获取真实app对象

    def _build_trans_config(self, task):
        """构建符合文件处理器要求的 trans 字典[^1]"""
        return {
            'id': task.id,  # 任务ID
            'threads': task.threads,
            'file_path': task.origin_filepath,  # 原始文件绝对路径
            'target_file': task.target_filepath,  # 目标文件绝对路径
            'api_url': task.api_url,
            'api_key': task.api_key,  # 新增API密钥字段
            'type': task.type,
            'lang': task.lang,
            'run_complete': True,  # 默认设为True
            # 以下是可能需要添加的额外字段
            'prompt': task.prompt,
            'model': task.model,
            'backup_model': task.backup_model,
            'comparison_id': task.comparison_id,
            'prompt_id': task.prompt_id,
            'extension': os.path.splitext(task.origin_filepath)[1]  # 动态获取文件扩展名
        }

    def execute(self):
        """启动任务入口[^2]"""
        try:
            # 在主线程上下文中准备任务
            with self.app.app_context():
                task = self._prepare_task()

            # 启动线程时传递真实app对象和任务ID
            thr = Thread(
                target=self._async_wrapper,
                args=(self.app, self.task_id)
            )
            thr.start()
            return True
        except Exception as e:
            self.app.logger.error(f"任务初始化失败: {str(e)}", exc_info=True)
            return False

    def _async_wrapper(self, app, task_id):
        """异步执行包装器[^3]"""
        with app.app_context():
            from app.extensions import db  # 确保在每个线程中导入
            try:
                # 使用新会话获取任务对象
                task = db.session.query(Translate).get(task_id)
                if not task:
                    app.logger.error(f"任务 {task_id} 不存在")
                    return

                # 执行核心逻辑
                success = self._execute_core(task)
                self._complete_task(success)
            except Exception as e:
                app.logger.error(f"任务执行异常: {str(e)}", exc_info=True)
                self._complete_task(False)
            finally:
                db.session.remove()  # 重要！清理线程局部session

    def _execute_core(self, task):
        """执行核心翻译逻辑[^4]"""
        try:
            # 初始化翻译配置
            self._init_translate_config(task)

            # 构建符合要求的 trans 字典
            trans_config = self._build_trans_config(task)

            # 调用 main_wrapper 执行翻译
            return main_wrapper(task_id=task.id, origin_path=task.origin_filepath,config=trans_config)
        except Exception as e:
            current_app.logger.error(f"翻译执行失败: {str(e)}", exc_info=True)
            return False

    def _prepare_task(self):
        """准备翻译任务[^5]"""
        task = Translate.query.get(self.task_id)
        if not task:
            raise ValueError(f"任务 {self.task_id} 不存在")

        # 验证文件存在性
        if not os.path.exists(task.origin_filepath):
            raise FileNotFoundError(f"原始文件不存在: {task.origin_filepath}")

        # 更新任务状态
        task.status = 'process'
        task.start_at = db.func.now()
        db.session.commit()
        return task

    def _init_translate_config(self, task):
        """初始化翻译配置[^6]"""
        if task.api_url and task.api_key:
            import openai
            openai.api_base = task.api_url
            openai.api_key = task.api_key

        # 加载术语对照表
        if task.comparison_id:
            from app.models import Comparison
            comparison = db.session.query(Comparison).get(task.comparison_id)
            if comparison:
                task.prompt = f"术语对照表:\n{comparison.content.replace(',', ':')}\n{task.prompt}"

        # 加载提示词模板
        if task.prompt_id:
            from app.models import Prompt
            prompt = db.session.query(Prompt).get(task.prompt_id)
            if prompt:
                task.prompt = prompt.content

    def _get_file_handler(self, file_path):
        """获取文件处理器[^7]"""
        from app.translate import (
            word, excel, powerpoint, pdf,
            gptpdf, txt, csv_handle, md
        )

        try:
            current_app.logger.debug(f"正在解析文件路径: {file_path}")
            # 标准化路径（处理不同OS的斜杠和大小写）
            normalized_path = os.path.normpath(file_path).lower()
            current_app.logger.debug(f"标准化路径: {normalized_path}")

            ext = os.path.splitext(normalized_path)[1]
            current_app.logger.debug(f"提取的扩展名: {ext}")

            # 处理器映射表
            handler_map = {
                '.docx': word,
                '.doc': word,
                '.xlsx': excel,
                '.xls': excel,
                '.pptx': powerpoint,
                '.ppt': powerpoint,
                '.pdf': pdf,  # if not pdf.is_scanned_pdf(file_path) else gptpdf,
                '.txt': txt,
                '.csv': csv_handle,
                '.md': md
            }

            current_app.logger.debug(f"当前处理器映射表: {handler_map}")

            # 匹配处理器
            handler = handler_map.get(ext)
            if not handler:
                current_app.logger.error(f"未找到匹配的处理器，扩展名: {ext}")
                return None

            current_app.logger.info(f"成功匹配处理器: {handler.__name__}")
            return handler

        except Exception as e:
            current_app.logger.error(f"获取文件处理器失败: {str(e)}", exc_info=True)
            return None

    def _complete_task(self, success):
        """更新任务状态[^8]"""
        from app.extensions import db
        try:
            with self.app.app_context():
                task = db.session.query(Translate).get(self.task_id)
                if task:
                    task.status = 'done' if success else 'failed'
                    task.end_at = db.func.now()
                    task.process = 100.00 if success else 0.00
                    db.session.commit()
        except Exception as e:
            db.session.rollback()
            self.app.logger.error(f"状态更新失败: {str(e)}", exc_info=True)


class TranslateEngine:
    def __init__(self, task_id):
        self.task_id = task_id
        self.app = current_app._get_current_object()  # 获取真实app对象

    def _build_trans_config(self, task):
        """构建符合文件处理器要求的 trans 字典[^1]"""
        config = {
            'id': task.id,  # 任务ID
            'target_lang': task.lang,
            # 'origin_lang': task.origin_lang,
            'uuid':task.uuid,
            'target_path_dir':os.path.dirname(task.target_filepath),
            'threads': task.threads,
            'file_path': task.origin_filepath,  # 原始文件绝对路径
            'target_file': task.target_filepath,  # 目标文件绝对路径
            'api_url': task.api_url,
            'api_key': task.api_key,  # 新增API密钥字段
            'type': task.type,
            'lang': task.lang,
            'run_complete': True,  # 默认设为True
            # 以下是可能需要添加的额外字段
            'prompt': task.prompt,
            'model': task.model,
            'backup_model': task.backup_model,
            'comparison_id': task.comparison_id,
            'prompt_id': task.prompt_id,
            'extension': os.path.splitext(task.origin_filepath)[1]  # 动态获取文件扩展名
        }

        # 加载术语表
        if task.comparison_id:
            comparison = db.session.query(Comparison).get(task.comparison_id)
            if comparison:
                config['comparison'] = comparison.content.replace(',', ':').replace(';', '\n')

        # 加载提示语模板
        if task.prompt_id:
            prompt = db.session.query(Prompt).get(task.prompt_id)
            if prompt:
                config['prompt'] = prompt.content

        return config

    def execute(self):
        """启动任务入口[^2]"""
        try:
            # 在主线程上下文中准备任务
            with self.app.app_context():
                task = self._prepare_task()

            # 启动线程时传递真实app对象和任务ID
            thr = Thread(
                target=self._async_wrapper,
                args=(self.app, self.task_id)
            )
            thr.start()
            return True
        except Exception as e:
            self.app.logger.error(f"任务初始化失败: {str(e)}", exc_info=True)
            return False

    def _async_wrapper(self, app, task_id):
        """异步执行包装器[^3]"""
        with app.app_context():
            from app.extensions import db  # 确保在每个线程中导入
            try:
                # 使用新会话获取任务对象
                task = db.session.query(Translate).get(task_id)
                if not task:
                    app.logger.error(f"任务 {task_id} 不存在")
                    return

                # 执行核心逻辑
                success = self._execute_core(task)
                self._complete_task(success)
            except Exception as e:
                app.logger.error(f"任务执行异常: {str(e)}", exc_info=True)
                self._complete_task(False)
            finally:
                db.session.remove()  # 重要！清理线程局部session

    def _execute_core(self, task):
        """执行核心翻译逻辑[^4]"""
        try:
            # 初始化翻译配置
            self._init_translate_config(task)

            # 构建符合要求的 trans 字典
            trans_config = self._build_trans_config(task)

            # 调用 main_wrapper 执行翻译
            return main_wrapper(task_id=task.id, origin_path=task.origin_filepath, config=trans_config)
        except Exception as e:
            current_app.logger.error(f"翻译执行失败: {str(e)}", exc_info=True)
            return False

    def _prepare_task(self):
        """准备翻译任务[^5]"""
        task = Translate.query.get(self.task_id)
        if not task:
            raise ValueError(f"任务 {self.task_id} 不存在")

        # 验证文件存在性
        if not os.path.exists(task.origin_filepath):
            raise FileNotFoundError(f"原始文件不存在: {task.origin_filepath}")

        # 更新任务状态
        task.status = 'process'
        task.start_at = db.func.now()
        db.session.commit()
        return task

    def _init_translate_config(self, task):
        """初始化翻译配置[^6]"""
        if task.api_url and task.api_key:
            import openai
            openai.api_base = task.api_url
            openai.api_key = task.api_key

    def _complete_task(self, success):
        """更新任务状态[^7]"""
        from app.extensions import db
        try:
            with self.app.app_context():
                task = db.session.query(Translate).get(self.task_id)
                if task:
                    task.status = 'done' if success else 'failed'
                    task.end_at = db.func.now()
                    task.process = 100.00 if success else 0.00
                    db.session.commit()
        except Exception as e:
            db.session.rollback()
            self.app.logger.error(f"状态更新失败: {str(e)}", exc_info=True)
