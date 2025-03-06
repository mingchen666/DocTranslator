# 后台管理用户模型 (对应user表)
from datetime import datetime

from app import db


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    password = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    deleted_flag = db.Column(db.Enum('N', 'Y'), default='N')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    