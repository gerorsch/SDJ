"""
Classe base para todos os agentes especialistas
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from .state import AgentState


class BaseAgent(ABC):
    """
    Classe base abstrata para todos os agentes especialistas.
    Define a interface comum que todos os agentes devem implementar.
    """
    
    def __init__(self, name: str, description: str = ""):
        """
        Inicializa o agente base.
        
        Args:
            name: Nome único do agente
            description: Descrição do propósito do agente
        """
        self.name = name
        self.description = description
    
    @abstractmethod
    async def process(self, state: AgentState) -> AgentState:
        """
        Processa o estado e retorna o estado modificado.
        
        Args:
            state: Estado atual do grafo
            
        Returns:
            Estado modificado com os resultados do processamento
        """
        pass
    
    def validate(self, state: AgentState) -> bool:
        """
        Valida se o estado tem os dados necessários para processamento.
        
        Args:
            state: Estado a ser validado
            
        Returns:
            True se válido, False caso contrário
        """
        return True
    
    def get_state(self) -> Dict[str, Any]:
        """
        Retorna informações sobre o estado do agente.
        
        Returns:
            Dicionário com informações do agente
        """
        return {
            "name": self.name,
            "description": self.description,
            "status": "ready"
        }
    
    def _prepare_state(self, state: AgentState) -> AgentState:
        """
        Prepara o estado antes do processamento.
        Marca o agente atual no estado.
        """
        state.current_agent = self.name
        return state
    
    def _finalize_state(self, state: AgentState) -> AgentState:
        """
        Finaliza o estado após o processamento.
        Marca o agente como completo.
        """
        state.mark_agent_complete(self.name)
        state.current_agent = None
        return state
    
    async def execute(self, state: AgentState) -> AgentState:
        """
        Método principal de execução que coordena validação, processamento e finalização.
        
        Args:
            state: Estado atual
            
        Returns:
            Estado modificado
        """
        if not self.validate(state):
            state.add_error(f"Validação falhou para agente {self.name}")
            return state
        
        try:
            state = self._prepare_state(state)
            state = await self.process(state)
            state = self._finalize_state(state)
        except Exception as e:
            error_msg = f"Erro no agente {self.name}: {str(e)}"
            state.add_error(error_msg)
            state.current_agent = None
        
        return state

