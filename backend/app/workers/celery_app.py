from celery import Celery

from app.core.config import get_settings

settings = get_settings()
celery_app = Celery(
    "rag_visual_optimizer",
    broker=str(settings.redis_url),
    backend=str(settings.redis_url),
)
celery_app.conf.task_routes = {"app.workers.tasks.*": {"queue": "rag-jobs"}}

