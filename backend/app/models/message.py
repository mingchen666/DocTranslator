# models/message.py
from datetime import datetime
from app.extensions import db


class Message(db.Model):
    __tablename__ = 'message'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)  # 关联客户 [^1]
    content = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum('unread', 'read'), default='unread')  # 消息状态 [^2]
    msg_type = db.Column(db.String(50))  # 消息类型（系统通知/业务提醒等）
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    deleted_flag = db.Column(db.CHAR(1), default='N', nullable=False)  # 保持删除标记一致性 [^3]

    @classmethod
    def get_user_messages(cls, customer_id):
        """获取用户有效消息列表 [^2]"""
        return cls.query.filter_by(
            customer_id=customer_id,
            deleted_flag='N'
        ).order_by(cls.created_at.desc()).all()

    @classmethod
    def mark_as_read(cls, message_id):
        """标记消息为已读"""
        message = cls.query.get(message_id)
        if message:
            message.status = 'read'
            db.session.commit()

