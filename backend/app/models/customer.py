from datetime import datetime
from decimal import Decimal

from werkzeug.security import generate_password_hash, check_password_hash

from app import db


class Customer(db.Model):
    """ 前台用户表 """
    __tablename__ = 'customer'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_no = db.Column(db.String(32))  # 用户编号
    phone = db.Column(db.String(11))  # 手机号（长度11）
    name = db.Column(db.String(255))  # 用户名
    password = db.Column(db.String(64), nullable=False)  # 密码（SHA256长度）
    email = db.Column(db.String(255), nullable=False)  # 邮箱
    level = db.Column(db.Enum('common', 'vip'), default='common')  # 会员等级
    status = db.Column(db.Enum('enabled', 'disabled'), default='enabled')  # 账户状态
    deleted_flag = db.Column(db.Enum('N', 'Y'), default='N')  # 删除标记
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 创建时间
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)  # 更新时间
    storage = db.Column(db.BigInteger, default=0)  # 存储空间（字节）

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password, password)

    def to_dict(self):
        """将模型实例转换为字典，处理所有需要序列化的字段"""
        return {
            'id': self.id,
            'name': self.name,
            'customer_no': self.customer_no,
            'email': self.email,
            'status': 'enabled' if self.deleted_flag == 'N'and self.status == 'enabled' else 'disabled',
            'level': self.level,
            'storage': int(self.storage),
            # 处理 Decimal
            'created_at': self.created_at.isoformat() if self.created_at else None,  # 注册时间
            'updated_at': self.updated_at.isoformat() if self.updated_at else None  # 更新时间
        }
