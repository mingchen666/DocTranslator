import os
from datetime import datetime
from threading import Thread
from flask import current_app
from app.models.translate import Translate
from app.extensions import db
from .main import main_wrapper
from ...models.comparison import Comparison
from ...models.prompt import Prompt
import pytz

# 时间修复
class TranslateEngine:
    def __init__(self, task_id):
        self.task_id = task_id
        self.app = current_app._get_current_object()  # 获取真实app对象

    def execute(self):
        """启动翻译任务入口"""
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
                db.session.remove()  # 清理线程局部session

    def _execute_core(self, task):
        """执行核心翻译逻辑"""
        try:
            # 初始化翻译配置
            self._init_translate_config(task)

            # 构建符合要求的 trans 字典
            trans_config = self._build_trans_config(task)

            # 调用 main_wrapper 执行翻译
            return main_wrapper(task_id=task.id, config=trans_config,origin_path=task.origin_filepath)
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
        task.start_at = datetime.now(pytz.timezone(self.app.config['TIMEZONE']))  # 使用配置的时区
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
            'file_path': task.origin_filepath,  # 原始文件绝对路径
            'target_file': task.target_filepath,  # 目标文件绝对路径
            'api_url': task.api_url,
            'api_key': task.api_key,  # 新增API密钥字段
            # 机器翻译相关
            'app_id':task.app_id,
            'app_key': task.app_key,
            'type': task.type,
            'lang': task.lang,
            'server': task.server,
            'run_complete': True,  # 默认设为True
            'prompt': task.prompt,
            'model': task.model,
            'backup_model': task.backup_model,
            'comparison_id': task.comparison_id,
            'prompt_id': task.prompt_id,
            'extension': os.path.splitext(task.origin_filepath)[1]  # 动态获取文件扩展名
        }

        # 加载术语对照表
        if task.comparison_id and task.comparison_id != 0:
            comparison = self.get_comparison(task.comparison_id)
            config['prompt'] = f"""
                术语对照表如下:
                {comparison}
                ---------------------
                {config['prompt']}
                """


        return config

    def _init_translate_config(self, task):
        """初始化翻译配置"""
        if task.api_url and task.api_key:
            import openai
            openai.api_base = task.api_url
            openai.api_key = task.api_key

    def _complete_task(self, success):
        """更新任务状态"""
        try:
            task = db.session.query(Translate).get(self.task_id)
            if task:
                task.status = 'done' if success else 'failed'
                task.end_at = datetime.now(pytz.timezone(self.app.config['TIMEZONE']))  # 使用配置的时区
                task.process = 100.00 if success else 0.00
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            self.app.logger.error(f"状态更新失败: {str(e)}", exc_info=True)


    def get_comparison(self,comparison_id):
        """
        加载术语对照表
        :param comparison_id: 术语对照表ID
        :return: 术语对照表内容
        """
        comparison = db.session.query(Comparison).filter_by(id=comparison_id).first()
        if comparison and comparison.content:
            return comparison.content.replace(',', ':').replace(';', '\n')
        return


    def get_prompt(self,prompt_id):
        """
        加载提示词模板
        :param prompt_id: 提示词模板ID
        :return: 提示词内容
        """
        prompt = db.session.query(Prompt).filter_by(id=prompt_id).first()
        if prompt and prompt.content:
            return prompt.content
        return

