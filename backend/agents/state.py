"""
Estado compartilhado entre agentes no grafo LangGraph
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List


@dataclass
class AgentState:
    """
    Estado compartilhado entre todos os agentes no grafo LangGraph.
    Cada agente pode ler e modificar campos relevantes.
    """
    
    # Entrada
    input_text: str = ""
    input_file_path: Optional[str] = None
    input_file_type: Optional[str] = None  # pdf, docx, mp3, mp4
    
    # Classificação e roteamento
    intent: Optional[str] = None  # timeline, graph, transcription, write, all
    document_type: Optional[str] = None  # peticao_inicial, contestacao, sentenca, etc.
    
    # Resultados dos agentes especialistas
    timeline: Optional[Dict[str, Any]] = None  # Resultado do TimelineAgent
    graph: Optional[Dict[str, Any]] = None  # Resultado do GraphAgent
    transcription: Optional[Dict[str, Any]] = None  # Resultado do TranscriptionAgent
    output: Optional[str] = None  # Resultado do WriterAgent ou resultado final
    
    # Documentos de referência (para WriterAgent)
    reference_documents: List[Dict[str, Any]] = field(default_factory=list)
    instructions: Optional[str] = None
    
    # Metadados
    metadata: Dict[str, Any] = field(default_factory=dict)
    numero_processo: Optional[str] = None
    
    # Controle de fluxo
    current_agent: Optional[str] = None
    completed_agents: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    def add_error(self, error: str):
        """Adiciona um erro ao estado"""
        self.errors.append(error)
    
    def mark_agent_complete(self, agent_name: str):
        """Marca um agente como completo"""
        if agent_name not in self.completed_agents:
            self.completed_agents.append(agent_name)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte o estado para dicionário"""
        return {
            "input_text": self.input_text,
            "input_file_path": self.input_file_path,
            "input_file_type": self.input_file_type,
            "intent": self.intent,
            "document_type": self.document_type,
            "timeline": self.timeline,
            "graph": self.graph,
            "transcription": self.transcription,
            "output": self.output,
            "reference_documents_count": len(self.reference_documents),
            "instructions": self.instructions,
            "metadata": self.metadata,
            "numero_processo": self.numero_processo,
            "current_agent": self.current_agent,
            "completed_agents": self.completed_agents,
            "errors": self.errors,
        }

