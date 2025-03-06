from datetime import datetime

from app import db


class TranslateLog(db.Model):
    """ 翻译日志表 """
    __tablename__ = 'translate_logs'

    id = db.Column(db.BigInteger, primary_key=True)
    md5_key = db.Column(db.String(100), nullable=False, unique=True)  # 原文MD5
    source = db.Column(db.Text, nullable=False)  # 原文内容
    content = db.Column(db.Text)  # 译文内容
    target_lang = db.Column(db.String(32), default='zh')
    model = db.Column(db.String(255), nullable=False)  # 使用的翻译模型
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 上下文参数
    prompt = db.Column(db.String(1024), default='')  # 实际使用的提示语
    api_url = db.Column(db.String(255), default='')  # 接口地址
    api_key = db.Column(db.String(255), default='')  # 接口密钥
    word_count = db.Column(db.Integer, default=0)  # 字数统计
    backup_model = db.Column(db.String(64), default='')  # 备用模型


