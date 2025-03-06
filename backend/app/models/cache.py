from app import db


class Cache(db.Model):
    """ 缓存表 """
    __tablename__ = 'cache'
    key = db.Column(db.String(255), primary_key=True)
    value = db.Column(db.Text, nullable=False)  # 存储序列化后的缓存值 [^1]
    expiration = db.Column(db.Integer, nullable=False)  # 过期时间（Unix时间戳）

class CacheLock(db.Model):
    """ 缓存锁表 """
    __tablename__ = 'cache_locks'
    key = db.Column(db.String(255), primary_key=True)
    owner = db.Column(db.String(255), nullable=False)  # 锁持有者标识
    expiration = db.Column(db.Integer, nullable=False)  # 锁过期时间