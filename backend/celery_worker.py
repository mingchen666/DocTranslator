"""Celery worker import target.

Run ordinary documents with queue ``translation.default`` and PDF documents
with queue ``translation.pdf``. Use separate worker processes to keep the
default concurrency at two and PDF concurrency at one.
"""

from app.celery_app import celery

__all__ = ['celery']
