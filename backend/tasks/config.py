"""
Configurações do Celery
"""
import os
from typing import Optional

class CeleryConfig:
    """Configurações centralizadas do Celery"""
    
    # Broker (RabbitMQ)
    BROKER_URL: str = os.getenv(
        'CELERY_BROKER_URL',
        os.getenv('RABBITMQ_URL', 'amqp://guest:guest@localhost:5672//')
    )
    
    # Result Backend
    RESULT_BACKEND: str = os.getenv('CELERY_RESULT_BACKEND', 'rpc://')
    
    # Serialização
    TASK_SERIALIZER: str = 'json'
    RESULT_SERIALIZER: str = 'json'
    ACCEPT_CONTENT: list = ['json']
    
    # Timezone
    TIMEZONE: str = 'America/Recife'
    ENABLE_UTC: bool = True
    
    # Task Execution
    TASK_ACKS_LATE: bool = True  # Confirma após conclusão
    TASK_REJECT_ON_WORKER_LOST: bool = True
    TASK_TIME_LIMIT: int = 30 * 60  # 30 minutos
    TASK_SOFT_TIME_LIMIT: int = 25 * 60  # 25 minutos
    
    # Retry
    TASK_MAX_RETRIES: int = 3
    TASK_DEFAULT_RETRY_DELAY: int = 60  # 1 minuto
    
    # Worker
    WORKER_PREFETCH_MULTIPLIER: int = 1
    WORKER_MAX_TASKS_PER_CHILD: int = 1000
    
    # Result Expiration
    RESULT_EXPIRES: int = 24 * 60 * 60  # 24 horas

