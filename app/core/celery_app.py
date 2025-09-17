from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Crear instancia de Celery
celery_app = Celery("sales_management")

# Configuración
celery_app.conf.update(
    broker_url=settings.redis_url,
    result_backend=settings.redis_url,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Asuncion",  # Zona horaria de Paraguay
    enable_utc=True,
    
    # Configuración del scheduler
    beat_schedule={
        "check-tourism-expiry": {
            "task": "app.services.notification_service.check_tourism_expiry_task",
            "schedule": crontab(hour=8, minute=0),  # Todos los días a las 8:00 AM
        },
    },
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.services"])

# Import all models to ensure SQLAlchemy registry is populated
from app import models  # noqa - This registers all models

# Explicitly import tasks to ensure they're registered
from app.services import notification_service  # noqa