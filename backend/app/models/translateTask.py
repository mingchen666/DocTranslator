from datetime import datetime

from app import db


class TranslateTask(db.Model):
    """ 翻译任务表 """
    __tablename__ = 'translate'

    id = db.Column(db.Integer, primary_key=True)
    # 基础信息
    translate_no = db.Column(db.String(32))  # 任务编号
    uuid = db.Column(db.String(64))  # 对外暴露的UUID
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), default=0)
    rand_user_id = db.Column(db.String(64))  # 随机用户ID（未登录用户）

    # 文件信息
    origin_filename = db.Column(db.String(520), nullable=False)
    origin_filepath = db.Column(db.String(520), nullable=False)
    target_filepath = db.Column(db.String(520), nullable=False)
    origin_filesize = db.Column(db.BigInteger, default=0)  # 字节
    target_filesize = db.Column(db.BigInteger, default=0)  # 字节
    md5 = db.Column(db.String(32))  # 文件校验值

    # 翻译设置
    origin_lang = db.Column(db.String(32))  # 源语言
    lang = db.Column(db.String(32))  # 目标语言
    model = db.Column(db.String(64), default='')  # 主用模型
    backup_model = db.Column(db.String(64), default='')  # 备用模型
    prompt_id = db.Column(db.BigInteger, default=0)  # 提示词ID [^7]
    comparison_id = db.Column(db.BigInteger, default=0)  # 对照表ID [^7]
    type = db.Column(db.String(64))  # 译文形式（双语/单语等）

    # 任务状态
    status = db.Column(
        db.Enum('none', 'process', 'done', 'failed'),
        default='none'
    )
    process = db.Column(db.Float(5, 2), default=0.00)  # 进度百分比
    start_at = db.Column(db.DateTime)  # 开始时间
    end_at = db.Column(db.DateTime)  # 结束时间
    failed_reason = db.Column(db.Text)  # 失败原因
    failed_count = db.Column(db.Integer, default=0)  # 失败次数

    # 系统字段
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    deleted_flag = db.Column(db.Enum('N', 'Y'), default='N')

    # 文档转换相关
    doc2x_flag = db.Column(db.Enum('N', 'Y'), default='N')
    doc2x_secret_key = db.Column(db.String(32))  # 转换秘钥