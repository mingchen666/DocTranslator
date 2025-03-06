from app import db


class Migration(db.Model):
    """ 数据库迁移记录表 """
    __tablename__ = 'migrations'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    migration = db.Column(db.String(255), nullable=False)          # 迁移文件名
    batch = db.Column(db.Integer, nullable=False)                  # 迁移批次号