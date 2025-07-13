from datetime import datetime

from app import db


class Translate(db.Model):
    """ 文件翻译任务表 """
    __tablename__ = 'translate'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    translate_no = db.Column(db.String(32))                         # 任务编号
    uuid = db.Column(db.String(64))                                 # 任务UUID
    customer_id = db.Column(db.Integer, default=0)                  # 关联用户ID
    rand_user_id = db.Column(db.String(64))                         # 随机用户ID（新增字段）[^3]
    origin_filename = db.Column(db.String(520), nullable=False)     # 原始文件名（带路径）
    origin_filepath = db.Column(db.String(520), nullable=False)     # 原始文件存储路径
    target_filepath = db.Column(db.String(520), nullable=False)     # 目标文件路径
    status = db.Column(db.Enum('none', 'process', 'done', 'failed'), default='none') # 任务状态
    start_at = db.Column(db.DateTime)                               # 开始时间
    end_at = db.Column(db.DateTime)                                 # 完成时间
    deleted_flag = db.Column(db.Enum('N', 'Y'), default='N')        # 删除标记
    created_at = db.Column(db.DateTime, default=datetime.utcnow)    # 创建时间
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)   # 更新时间
    origin_filesize = db.Column(db.BigInteger, default=0)           # 原始文件大小（字节）
    target_filesize = db.Column(db.BigInteger, default=0)           # 目标文件大小
    lang = db.Column(db.String(32), default='')                     # 目标语言
    model = db.Column(db.String(64), default='')                    # 使用模型
    prompt = db.Column(db.String(1024), default='')                 # 提示语内容
    api_url = db.Column(db.String(255), default='')                 # API地址
    api_key = db.Column(db.String(255), default='')                 # API密钥
    threads = db.Column(db.Integer, default=10)                     # 线程数
    failed_reason = db.Column(db.Text)                              # 失败原因
    failed_count = db.Column(db.Integer, default=0)                 # 失败次数
    word_count = db.Column(db.Integer, default=0)                   # 字数统计
    backup_model = db.Column(db.String(64), default='')             # 备用模型
    md5 = db.Column(db.String(32))                                  # 文件MD5
    type = db.Column(db.String(64), default='')                     # 译文类型
    origin_lang = db.Column(db.String(32))                          # 原始语言（新增字段）
    process = db.Column(db.Float(5, 2), default=0.00)               # 进度百分比
    doc2x_flag = db.Column(db.Enum('N', 'Y'), default='N')          # 文档转换标记
    doc2x_secret_key = db.Column(db.String(32))                     # 转换密钥
    prompt_id = db.Column(db.BigInteger, default=0)                 # 提示词ID
    comparison_id = db.Column(db.BigInteger, default=0)             # 对照表ID
    size = db.Column(db.BigInteger, default=0) # 文件大小 字节
    server= db.Column(db.String(32), default='openai')
    app_id = db.Column(db.String(64), default='')
    app_key = db.Column(db.String(64), default='')
    def to_dict(self):
        return {
            'id': self.id,
            'origin_filename': self.origin_filename,
            'status': self.status,
            'lang': self.lang,
            'process': float(self.process) if self.process is not None else None,
            'created_at': self.created_at.isoformat(),
            'customer_id': self.customer_id,
            'word_count': self.word_count,
            'server': self.server,
        }