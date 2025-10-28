"""
Celery application instance for distributed task queue

Features:
- Background data collection
- Model training tasks
- Scheduled analysis
- Report generation
"""
import os
from celery import Celery
from celery.schedules import crontab

# Redis URL from environment
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/1')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2')

# Create Celery app
celery_app = Celery(
    'sigma_analyst',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=['backend.tasks.tasks']  # Auto-discover tasks
)

# Celery configuration
celery_app.conf.update(
    # Timezone
    timezone='UTC',
    enable_utc=True,

    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3000,  # 50 minutes soft limit

    # Result backend
    result_expires=3600,  # Results expire after 1 hour
    result_backend_transport_options={
        'master_name': 'mymaster',
    },

    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,

    # Beat schedule (periodic tasks)
    beat_schedule={
        # Example: collect data every 15 minutes
        'collect-market-data': {
            'task': 'backend.tasks.tasks.collect_market_data',
            'schedule': crontab(minute='*/15'),  # Every 15 minutes
            'options': {'expires': 600}
        },

        # Example: daily analysis at 00:00 UTC
        'daily-analysis': {
            'task': 'backend.tasks.tasks.run_daily_analysis',
            'schedule': crontab(hour=0, minute=0),  # Daily at midnight
            'options': {'expires': 3600}
        },
    },
)

# Optional: Task routes (advanced)
celery_app.conf.task_routes = {
    'backend.tasks.tasks.collect_*': {'queue': 'data_collection'},
    'backend.tasks.tasks.train_*': {'queue': 'model_training'},
    'backend.tasks.tasks.run_*': {'queue': 'analysis'},
}

if __name__ == '__main__':
    celery_app.start()
