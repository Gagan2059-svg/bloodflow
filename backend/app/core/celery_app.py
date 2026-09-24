import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "bloodflow_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks.forecasting_tasks", "app.tasks.anomaly_tasks"]
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    # Fail fast when no broker is available — prevents HTTP handlers from blocking
    broker_connection_timeout=2,          # seconds to wait for initial connection
    broker_connection_max_retries=1,      # only retry once
    broker_connection_retry_on_startup=False,
)
