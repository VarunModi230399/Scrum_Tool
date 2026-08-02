from celery import Celery

from src.platform.config import get_settings

settings = get_settings()

celery_app = Celery(
    "scrum_tool",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[],  # task modules are registered here as modules add them
)

celery_app.conf.update(task_serializer="json", result_serializer="json", accept_content=["json"])
