from app import db


class Users(db.Model):
    """ Laravel兼容用户表 """
    __tablename__ = 'users'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)               # 用户名
    email = db.Column(db.String(255), unique=True, nullable=False) # 邮箱（唯一）
    email_verified_at = db.Column(db.DateTime)                     # 邮箱验证时间
    password = db.Column(db.String(255), nullable=False)           # 密码
    remember_token = db.Column(db.String(100))                     # 记住令牌
    created_at = db.Column(db.DateTime)                            # 创建时间
    updated_at = db.Column(db.DateTime)                            # 更新时间
