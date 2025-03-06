from app import db


class Session(db.Model):
    """ 用户会话表 """
    __tablename__ = 'sessions'
    id = db.Column(db.String(255), primary_key=True)               # 会话ID
    user_id = db.Column(db.BigInteger)                             # 关联用户ID
    ip_address = db.Column(db.String(45))                          # 客户端IP
    user_agent = db.Column(db.Text)                                # 用户代理
    payload = db.Column(db.Text, nullable=False)                   # 会话数据
    last_activity = db.Column(db.Integer, nullable=False)          # 最后活动时间戳