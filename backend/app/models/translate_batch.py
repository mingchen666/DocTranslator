from datetime import datetime

from app.extensions import db


class TranslateBatch(db.Model):
    __tablename__ = 'translate_batch'

    id = db.Column(db.String(36), primary_key=True)
    customer_id = db.Column(db.Integer, nullable=False, index=True)
    source_type = db.Column(db.Enum('files', 'zip'), nullable=False)
    origin_filename = db.Column(db.String(520))
    status = db.Column(
        db.Enum('pending', 'process', 'done', 'partial', 'failed'),
        nullable=False,
        default='pending',
    )
    total_count = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    finished_at = db.Column(db.DateTime)
