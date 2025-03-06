from datetime import datetime

from app import db


class SendCode(db.Model):
    """ 验证码发送记录表 """
    __tablename__ = 'send_code'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer)
    send_type = db.Column(db.String(20), nullable=False)  # 添加字段# 关联用户ID（可为空）
    send_type = db.Column(db.Integer, nullable=False)               # 发送类型（1=邮件改密）[^4]
    send_to = db.Column(db.String(100), nullable=False)             # 接收地址（邮箱/手机）
    code = db.Column(db.String(6), nullable=False)                  # 验证码（6位）
    created_at = db.Column(db.DateTime)                             # 创建时间
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)   # 更新时间