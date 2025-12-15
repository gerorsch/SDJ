"""
Configuração da aplicação Celery
"""
from celery import Celery
from .config import CeleryConfig

# Criar instância do Celery
celery_app = Celery(
    'sdj_tasks',
    broker=CeleryConfig.BROKER_URL,
    backend=CeleryConfig.RESULT_BACKEND,
)

# Aplicar configurações
celery_app.conf.update(
    task_serializer=CeleryConfig.TASK_SERIALIZER,
    result_serializer=CeleryConfig.RESULT_SERIALIZER,
    accept_content=CeleryConfig.ACCEPT_CONTENT,
    timezone=CeleryConfig.TIMEZONE,
    enable_utc=CeleryConfig.ENABLE_UTC,
    task_acks_late=CeleryConfig.TASK_ACKS_LATE,
    task_reject_on_worker_lost=CeleryConfig.TASK_REJECT_ON_WORKER_LOST,
    task_time_limit=CeleryConfig.TASK_TIME_LIMIT,
    task_soft_time_limit=CeleryConfig.TASK_SOFT_TIME_LIMIT,
    task_max_retries=CeleryConfig.TASK_MAX_RETRIES,
    task_default_retry_delay=CeleryConfig.TASK_DEFAULT_RETRY_DELAY,
    worker_prefetch_multiplier=CeleryConfig.WORKER_PREFETCH_MULTIPLIER,
    worker_max_tasks_per_child=CeleryConfig.WORKER_MAX_TASKS_PER_CHILD,
    result_expires=CeleryConfig.RESULT_EXPIRES,
)

# Auto-discover tasks
celery_app.autodiscover_tasks(['tasks'])

