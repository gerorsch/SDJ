"""
Agente Redator - Gera minutas/sentenças baseadas em perfil (Juiz/Advogado)
"""

import os
from typing import Optional
from .base import BaseAgent
from .state import AgentState
from services.llm import gerar_sentenca_llm


class WriterAgent(BaseAgent):
    """
    Agente Redator que gera minutas e sentenças baseadas no perfil do usuário
    (Juiz ou Advogado) e nos documentos de referência fornecidos.
    """
    
    def __init__(self):
        super().__init__(
            name="writer",
            description="Gera minutas e sentenças baseadas em perfil e referências"
        )
        self.default_profile = os.getenv("DEFAULT_USER_PROFILE", "juiz")
    
    async def process(self, state: AgentState) -> AgentState:
        """
        Processa a geração da sentença/minuta usando o LLM.
        """
        # Valida se há relatório
        if not state.input_text:
            state.add_error("Relatório não fornecido para geração de sentença")
            return state
        
        # Prepara documentos de referência
        docs = state.reference_documents or []
        
        # Se não há documentos de referência, tenta buscar na base
        if not docs and state.input_text:
            try:
                from services.retrieval_rerank import recuperar_documentos_similares
                docs = recuperar_documentos_similares(
                    state.input_text,
                    top_k=10,
                    rerank_top_k=5
                )
                state.reference_documents = docs
            except Exception as e:
                state.add_error(f"Erro ao buscar documentos de referência: {str(e)}")
        
        if not docs:
            state.add_error("Nenhum documento de referência disponível")
            return state
        
        # Gera a sentença usando o serviço LLM existente
        try:
            sentenca = await gerar_sentenca_llm(
                relatorio=state.input_text,
                docs=docs,
                instrucoes_usuario=state.instructions or "",
            )
            
            state.output = sentenca
            state.metadata["profile"] = self.default_profile
            state.metadata["reference_docs_count"] = len(docs)
            
        except Exception as e:
            error_msg = f"Erro na geração da sentença: {str(e)}"
            state.add_error(error_msg)
        
        return state
    
    def validate(self, state: AgentState) -> bool:
        """Valida se há relatório para processar"""
        return bool(state.input_text)

