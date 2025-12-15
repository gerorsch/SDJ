"""
Módulo de tasks Celery para processamento assíncrono
"""
from .celery_app import celery_app
from .pdf_tasks import processar_pdf_task, gerar_sentenca_task, buscar_documentos_task

__all__ = [
    'celery_app',
    'processar_pdf_task',
    'gerar_sentenca_task',
    'buscar_documentos_task',
]

