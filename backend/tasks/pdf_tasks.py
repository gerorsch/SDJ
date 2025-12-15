"""
Tasks Celery para processamento de PDFs e geração de sentenças
"""
import os
import uuid
import json
from pathlib import Path as FSPath
from typing import List, Optional, Dict, Any
from celery import Task
from celery.utils.log import get_task_logger

from .celery_app import celery_app
from .models import ProcessarPDFResult, GerarSentencaResult, TaskStatus
from preprocessing.process_report_pipeline import Config, generate as gerar_relatorio
from services.retrieval_rerank import recuperar_documentos_similares as semantic_search_rerank
from services.llm import gerar_sentenca_llm
from services.docx_utils import salvar_sentenca_como_docx, salvar_docs_referencia
from services.docx_parser import parse_docx_bytes
from utils import (
    extrair_numero_processo,
    gerar_nome_arquivo_sentenca,
    gerar_nome_arquivo_referencias,
    decodificar_unicode,
    limpar_arquivo_temporario,
)

logger = get_task_logger(__name__)


class CallbackTask(Task):
    """Task com callback de progresso"""
    
    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f'Task {task_id} succeeded: {retval}')
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f'Task {task_id} failed: {exc}')


@celery_app.task(
    bind=True,
    base=CallbackTask,
    name='tasks.processar_pdf',
    max_retries=3,
    default_retry_delay=60
)
def processar_pdf_task(self, pdf_data: bytes, filename: str) -> Dict[str, Any]:
    """
    Processa um PDF e extrai o relatório do processo
    
    Args:
        pdf_data: Bytes do arquivo PDF
        filename: Nome do arquivo original
        
    Returns:
        Dict com relatorio e numero_processo
    """
    tmp_id = uuid.uuid4().hex
    tmp_path = f"/tmp/{tmp_id}.pdf"
    
    try:
        # Atualiza status para PROCESSING
        self.update_state(
            state=TaskStatus.PROCESSING,
            meta={'progress': 'Salvando arquivo PDF...'}
        )
        
        # Salva arquivo temporário
        with open(tmp_path, "wb") as f:
            f.write(pdf_data)
        
        self.update_state(
            state=TaskStatus.PROCESSING,
            meta={'progress': 'Processando PDF e extraindo texto...'}
        )
        
        # Processa o PDF
        cfg = Config()
        
        def on_progress(msg: str):
            """Callback de progresso"""
            self.update_state(
                state=TaskStatus.PROCESSING,
                meta={'progress': msg}
            )
        
        texto = gerar_relatorio(FSPath(tmp_path), cfg, on_progress=on_progress)
        
        # Extrai número do processo se presente
        numero_processo = extrair_numero_processo(texto)
        
        resultado = ProcessarPDFResult(
            relatorio=texto,
            numero_processo=numero_processo
        )
        
        return resultado.dict()
    
    except Exception as exc:
        logger.error(f"Erro no processamento do PDF: {exc}", exc_info=True)
        # Retry automático
        raise self.retry(exc=exc, countdown=60)
    
    finally:
        # Limpa arquivo temporário
        limpar_arquivo_temporario(tmp_path)


@celery_app.task(
    bind=True,
    base=CallbackTask,
    name='tasks.buscar_documentos',
    max_retries=2,
    default_retry_delay=30
)
def buscar_documentos_task(
    self,
    relatorio: str,
    top_k: int = 10,
    rerank_top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Busca documentos similares usando busca semântica
    
    Args:
        relatorio: Texto do relatório
        top_k: Número de documentos iniciais
        rerank_top_k: Número de documentos após rerank
        
    Returns:
        Lista de documentos encontrados
    """
    try:
        self.update_state(
            state=TaskStatus.PROCESSING,
            meta={'progress': 'Buscando documentos similares...'}
        )
        
        docs = semantic_search_rerank(
            relatorio,
            top_k=top_k,
            rerank_top_k=rerank_top_k
        )
        
        return docs
    
    except Exception as exc:
        logger.error(f"Erro na busca de documentos: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(
    bind=True,
    base=CallbackTask,
    name='tasks.gerar_sentenca',
    max_retries=3,
    default_retry_delay=60
)
def gerar_sentenca_task(
    self,
    relatorio: str,
    instrucoes_usuario: Optional[str] = None,
    numero_processo: Optional[str] = None,
    top_k: int = 10,
    rerank_top_k: int = 5,
    arquivos_referencia_data: Optional[List[Dict[str, Any]]] = None,
    buscar_na_base: bool = False
) -> Dict[str, Any]:
    """
    Gera uma sentença completa baseada no relatório
    
    Args:
        relatorio: Texto do relatório
        instrucoes_usuario: Instruções adicionais do usuário
        numero_processo: Número do processo
        top_k: Número de documentos iniciais
        rerank_top_k: Número de documentos após rerank
        arquivos_referencia_data: Lista de dicts com 'filename' e 'data' (bytes)
        buscar_na_base: Se deve buscar na base de dados
        
    Returns:
        Dict com sentenca, sentenca_url, referencias_url, etc.
    """
    try:
        self.update_state(
            state=TaskStatus.PROCESSING,
            meta={'progress': 'Preparando documentos de referência...'}
        )
        
        # 1) Monta lista inicial com arquivos enviados, se houver
        docs: List[dict] = []
        
        if arquivos_referencia_data:
            for ref_data in arquivos_referencia_data:
                filename = ref_data.get('filename', '')
                data = ref_data.get('data')
                
                if not filename.lower().endswith('.docx'):
                    raise ValueError(f"Arquivo {filename} deve ser DOCX")
                
                sec = parse_docx_bytes(data)
                sec["id"] = filename or uuid.uuid4().hex
                docs.append(sec)
            
            # Se marcado, também busca na base
            if buscar_na_base:
                self.update_state(
                    state=TaskStatus.PROCESSING,
                    meta={'progress': 'Buscando documentos na base de dados...'}
                )
                extra = semantic_search_rerank(
                    relatorio, top_k=top_k, rerank_top_k=rerank_top_k
                )
                docs.extend(extra)
        else:
            # Sem arquivos enviados, busca obrigatória
            self.update_state(
                state=TaskStatus.PROCESSING,
                meta={'progress': 'Buscando documentos similares...'}
            )
            docs = semantic_search_rerank(
                relatorio, top_k=top_k, rerank_top_k=rerank_top_k
            )
            if not docs:
                raise ValueError("Nenhum documento semelhante encontrado")
        
        # 2) Geração via LLM
        self.update_state(
            state=TaskStatus.PROCESSING,
            meta={'progress': 'Gerando sentença com LLM...'}
        )
        
        # Importar função async e executar em loop
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        def on_progress(msg: str):
            """Callback de progresso"""
            self.update_state(
                state=TaskStatus.PROCESSING,
                meta={'progress': msg}
            )
        
        sentenca = loop.run_until_complete(
            gerar_sentenca_llm(
                relatorio=relatorio,
                docs=docs,
                instrucoes_usuario=instrucoes_usuario,
                on_progress=on_progress,
            )
        )
        
        # 3) Gera nomes de arquivo baseados no número do processo
        nome_base_sentenca = gerar_nome_arquivo_sentenca(numero_processo)
        nome_base_referencias = gerar_nome_arquivo_referencias(numero_processo)
        
        sent_id = f"{nome_base_sentenca}_{uuid.uuid4().hex[:8]}"
        refs_id = f"{nome_base_referencias}_{uuid.uuid4().hex[:8]}"
        
        sent_path = f"/tmp/{sent_id}.docx"
        refs_path = f"/tmp/{refs_id}.zip"
        
        # 4) Salvar .docx e ZIP de referências
        self.update_state(
            state=TaskStatus.PROCESSING,
            meta={'progress': 'Salvando sentença e referências...'}
        )
        
        sentenca_limpa = decodificar_unicode(sentenca)
        
        salvar_sentenca_como_docx(
            relatorio=relatorio,
            fundamentacao_dispositivo=sentenca_limpa,
            arquivo_path=sent_path,
            numero_processo=numero_processo
        )
        salvar_docs_referencia(docs, refs_path)
        
        # 5) Montar resultado
        resultado = GerarSentencaResult(
            sentenca=sentenca_limpa,
            sentenca_url=f"/download/sentenca/{sent_id}.docx",
            referencias_url=f"/download/referencias/{refs_id}.zip",
            numero_processo=numero_processo,
            documentos=[
                {
                    "id": d.get("id", ""),
                    "relatorio": d.get("relatorio", ""),
                    "fundamentacao": d.get("fundamentacao", ""),
                    "dispositivo": d.get("dispositivo", ""),
                    "score": d.get("score", 0.0),
                    "rerank_score": d.get("rerank_score", 0.0),
                }
                for d in docs
            ]
        )
        
        return resultado.dict()
    
    except Exception as exc:
        logger.error(f"Erro na geração da sentença: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=60)

