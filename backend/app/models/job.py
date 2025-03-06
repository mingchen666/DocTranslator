from datetime import datetime

from app import db


class FailedJob(db.Model):
    """ 失败任务记录表 """
    __tablename__ = 'failed_jobs'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    uuid = db.Column(db.String(255), unique=True)                   # 任务UUID
    connection = db.Column(db.Text, nullable=False)                 # 连接信息
    queue = db.Column(db.Text, nullable=False)                      # 队列名称
    payload = db.Column(db.Text, nullable=False)                    # 任务负载数据
    exception = db.Column(db.Text, nullable=False)                  # 异常信息
    failed_at = db.Column(db.DateTime, default=datetime.utcnow)     # 失败时间\


class JobBatch(db.Model):
    """ 任务批次记录表 """
    __tablename__ = 'job_batches'
    id = db.Column(db.String(255), primary_key=True)  # 批次ID（UUID）
    name = db.Column(db.String(255), nullable=False)  # 批次名称
    total_jobs = db.Column(db.Integer, nullable=False)  # 总任务数
    pending_jobs = db.Column(db.Integer, nullable=False)  # 待处理数
    failed_jobs = db.Column(db.Integer, nullable=False)  # 失败任务数
    failed_job_ids = db.Column(db.Text, nullable=False)  # 失败任务ID列表（JSON）
    options = db.Column(db.Text)  # 任务选项配置
    cancelled_at = db.Column(db.Integer)  # 取消时间戳
    created_at = db.Column(db.Integer, nullable=False)  # 创建时间戳
    finished_at = db.Column(db.Integer)  # 完成时间戳

class Job(db.Model):
    """ 队列任务表 """
    __tablename__ = 'jobs'
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    queue = db.Column(db.String(255), nullable=False)              # 队列名称
    payload = db.Column(db.Text, nullable=False)                   # 任务数据（JSON）
    attempts = db.Column(db.SmallInteger, nullable=False)          # 尝试次数
    reserved_at = db.Column(db.Integer)                            # 预留时间戳
    available_at = db.Column(db.Integer, nullable=False)           # 可用时间戳
    created_at = db.Column(db.Integer, nullable=False)             # 创建时间戳


