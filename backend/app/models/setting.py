from datetime import datetime

from app import db


class Setting(db.Model):
    """ 系统配置表 """
    __tablename__ = 'setting'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    alias = db.Column(db.String(64))  # 配置字段别名
    value = db.Column(db.Text)        # 配置字段值
    serialized = db.Column(db.Boolean, default=False)  # 是否序列化
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 创建时间
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)  # 更新时间
    deleted_flag = db.Column(db.Enum('N', 'Y'), default='N')  # 删除标记
    group = db.Column(db.String(32))  # 分组

    def to_dict(self):
        return {
            'id': self.id,
            'alias': self.alias,
            'value': self.value,
            'serialized': self.serialized,
            'group': self.group
        }
