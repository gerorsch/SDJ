"""
Agente Orquestrador - Recebe intenção e delega para agentes especialistas
"""

from typing import Literal
from .base import BaseAgent
from .state import AgentState


class OrchestratorAgent(BaseAgent):
    """
    Agente Orquestrador que recebe a intenção do usuário e delega
    para os agentes especialistas apropriados.
    """
    
    def __init__(self):
        super().__init__(
            name="orchestrator",
            description="Orquestra o fluxo de trabalho entre agentes especialistas"
        )
    
    async def process(self, state: AgentState) -> AgentState:
        """
        Processa a intenção e determina qual agente deve ser executado.
        Se a intenção não estiver definida, tenta inferir do contexto.
        """
        # Se não há intenção definida, tenta inferir
        if not state.intent:
            state.intent = self._infer_intent(state)
        
        # Atualiza metadados
        state.metadata["intent"] = state.intent
        
        return state
    
    def _infer_intent(self, state: AgentState) -> str:
        """
        Infere a intenção baseado no contexto do estado.
        Por padrão, retorna "all" para processar tudo.
        """
        # Se há arquivo de áudio, intenção é transcrição
        if state.input_file_type in ["mp3", "mp4"]:
            return "transcription"
        
        # Se há instruções e documentos de referência, intenção é escrita
        if state.instructions and state.reference_documents:
            return "write"
        
        # Por padrão, processa tudo
        return "all"
    
    def route(self, state: AgentState) -> Literal["timeline", "graph", "transcription", "writer", "all", "end"]:
        """
        Função de roteamento condicional para LangGraph.
        Determina qual agente deve ser executado após o orquestrador.
        """
        intent = state.intent or "all"
        
        if intent == "timeline":
            return "timeline"
        elif intent == "graph":
            return "graph"
        elif intent == "transcription":
            return "transcription"
        elif intent == "write":
            return "writer"
        elif intent == "all":
            # Quando "all", começa com timeline
            return "timeline"
        else:
            return "end"
    
    def route_after_timeline(self, state: AgentState) -> Literal["graph", "writer", "end"]:
        """
        Roteamento após o agente timeline.
        Se a intenção é "all", continua para graph, senão vai para writer ou end.
        """
        intent = state.intent or "all"
        
        if intent == "all":
            # Se timeline foi completado, vai para graph
            if "timeline" in state.completed_agents:
                return "graph"
            else:
                return "end"
        elif intent == "write":
            return "writer"
        else:
            return "end"
    
    def route_after_graph(self, state: AgentState) -> Literal["writer", "end"]:
        """
        Roteamento após o agente graph.
        Se a intenção é "all" ou "write", vai para writer, senão termina.
        """
        intent = state.intent or "all"
        
        if intent in ["all", "write"]:
            return "writer"
        else:
            return "end"
    
    def route_after_transcription(self, state: AgentState) -> Literal["writer", "end"]:
        """
        Roteamento após o agente transcription.
        Se há instruções, vai para writer, senão termina.
        """
        if state.instructions:
            return "writer"
        else:
            return "end"
    
    def validate(self, state: AgentState) -> bool:
        """Valida se há input para processar"""
        return bool(state.input_text or state.input_file_path)

