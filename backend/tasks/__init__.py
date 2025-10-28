"""
Celery tasks module for background processing
"""
from .celery_app import celery_app

__all__ = ['celery_app']
