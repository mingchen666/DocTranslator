import hashlib
import json
import uuid
from datetime import datetime

from app.extensions import db


class McpApiKey(db.Model):
    __tablename__ = 'mcp_api_key'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    key_hash = db.Column(db.String(64), nullable=False, unique=True)
    key_prefix = db.Column(db.String(12), nullable=False)
    name = db.Column(db.String(100))
    customer_id = db.Column(db.Integer, nullable=False)
    scope = db.Column(db.Enum('user', 'admin'), default='user')
    config = db.Column(db.JSON, nullable=False)
    status = db.Column(db.Enum('active', 'revoked'), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used_at = db.Column(db.DateTime)
    deleted_flag = db.Column(db.Enum('N', 'Y'), default='N')

    DEFAULT_CONFIG = {
        'api_url': '',
        'api_key': '',
        'model': '',
        'type': 'trans_all_only_inherit',
        'prompt_id': 0,
        'backup_model': '',
        'threads': 5,
        'lang': '中文',
        'comparison_id': None,
        'doc2x_flag': 'N',
        'doc2x_secret_key': '',
    }

    @staticmethod
    def generate_key():
        raw = f"dtk_{uuid.uuid4().hex}"
        key_hash = hashlib.sha256(raw.encode()).hexdigest()
        key_prefix = raw[:12]
        return raw, key_hash, key_prefix

    @staticmethod
    def hash_key(raw_key):
        return hashlib.sha256(raw_key.encode()).hexdigest()

    def get_config(self):
        base = dict(self.DEFAULT_CONFIG)
        if self.config:
            base.update(self.config)
        return base

    def to_dict(self, include_config=False):
        d = {
            # 'id': self.id,
            'key_prefix': self.key_prefix,
            'name': self.name,
            'scope': self.scope,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None,
            'last_used_at': self.last_used_at.strftime('%Y-%m-%d %H:%M') if self.last_used_at else None,
        }
        if include_config:
            d['config'] = self.get_config()
        return d
