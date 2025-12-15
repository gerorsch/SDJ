"""
Modelos Pydantic para status e resultados de tarefas
"""
from enum import Enum
from typing import Optional, Any, Dict
from pydantic import BaseModel
from datetime import datetime


class TaskStatus(str, Enum):
    """Status de uma tarefa"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRY = "RETRY"


class TaskResult(BaseModel):
    """Resultado de uma tarefa"""
    task_id: str
    status: TaskStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    progress: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ProcessarPDFResult(BaseModel):
    """Resultado do processamento de PDF"""
    relatorio: str
    numero_processo: Optional[str] = None


class GerarSentencaResult(BaseModel):
    """Resultado da geração de sentença"""
    sentenca: str
    sentenca_url: str
    referencias_url: str
    numero_processo: Optional[str] = None
    documentos: list = []

