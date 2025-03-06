from app import db


class PasswordResetToken(db.Model):
    """ 密码重置令牌表 """
    __tablename__ = 'password_reset_tokens'
    email = db.Column(db.String(255), primary_key=True)            # 用户邮箱（主键）
    token = db.Column(db.String(255), nullable=False)              # 重置令牌
    created_at = db.Column(db.DateTime)                            # 令牌创建时间