from app import db
from datetime import datetime

class Announcement(db.Model):
    __tablename__ = 'announcement'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)  # 公告内容
    duration = db.Column(db.Integer, default=5)  # 显示时长(秒)
    is_active = db.Column(db.Boolean, default=True)  # 是否启用
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    deleted_flag = db.Column(db.String(1), default='N')  # 软删除标记 