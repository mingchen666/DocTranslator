from datetime import datetime
from app import db


class Translate(db.Model):
    """ 文件翻译任务表 """
    __tablename__ = 'translate'
    __table_args__ = (
        db.CheckConstraint(
            "target_storage_backend IN ('local', 'oss')",
            name='ck_translate_target_storage_backend',
        ),
    )
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    translate_no = db.Column(db.String(32))
    uuid = db.Column(db.String(64))
    customer_id = db.Column(db.Integer, default=0)
    rand_user_id = db.Column(db.String(64))
    origin_filename = db.Column(db.String(520), nullable=False)
    origin_filepath = db.Column(db.String(520), nullable=False)
    target_filepath = db.Column(db.String(520), nullable=False)
    status = db.Column(db.Enum('none', 'process', 'done', 'failed'), default='none')
    start_at = db.Column(db.DateTime)
    end_at = db.Column(db.DateTime)
    deleted_flag = db.Column(db.Enum('N', 'Y'), default='N')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    origin_filesize = db.Column(db.BigInteger, default=0)
    target_filesize = db.Column(db.BigInteger, default=0)
    target_storage_backend = db.Column(
        db.String(16), nullable=False, default='local', server_default='local'
    )
    target_storage_key = db.Column(db.String(1024), nullable=True)
    lang = db.Column(db.String(32), default='')
    model = db.Column(db.String(64), default='')
    prompt = db.Column(db.String(1024), default='')
    api_url = db.Column(db.String(255), default='')
    api_key = db.Column(db.String(255), default='')
    threads = db.Column(db.Integer, default=10)
    failed_reason = db.Column(db.Text)
    failed_count = db.Column(db.Integer, default=0)
    word_count = db.Column(db.Integer, default=0)
    backup_model = db.Column(db.String(64), default='')
    md5 = db.Column(db.String(32))
    type = db.Column(db.String(64), default='')
    origin_lang = db.Column(db.String(32))
    process = db.Column(db.Float(5, 2), default=0.00)
    doc2x_flag = db.Column(db.Enum('N', 'Y'), default='N')
    doc2x_secret_key = db.Column(db.String(32))
    prompt_id = db.Column(db.BigInteger, default=0)
    comparison_id = db.Column(db.BigInteger, default=0)
    size = db.Column(db.BigInteger, default=0)  # 文件大小 字节
    server = db.Column(db.String(32), default='openai')
    app_id = db.Column(db.String(64), default='')
    app_key = db.Column(db.String(64), default='')
    batch_id = db.Column(db.String(36), index=True)
    batch_relative_path = db.Column(db.String(520))

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
