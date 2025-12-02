"""
Grafo LangGraph para orquestração de agentes
"""

from typing import Literal, TypedDict, Optional
from langgraph.graph import StateGraph, END
from .state import AgentState
from .orchestrator import OrchestratorAgent
from .timeline_agent import TimelineAgent
from .graph_agent import GraphAgent
from .transcription_agent import TranscriptionAgent
from .writer_agent import WriterAgent


class GraphState(TypedDict, total=False):
    """Wrapper TypedDict para compatibilidade com LangGraph"""
    input_text: str
    input_file_path: Optional[str]
    input_file_type: Optional[str]
    intent: Optional[str]
    document_type: Optional[str]
    timeline: Optional[dict]
    graph: Optional[dict]
    transcription: Optional[dict]
    output: Optional[str]
    reference_documents: list
    instructions: Optional[str]
    metadata: dict
    numero_processo: Optional[str]
    current_agent: Optional[str]
    completed_agents: list
    errors: list


def create_agent_graph() -> StateGraph:
    """
    Cria e retorna o grafo LangGraph com todos os agentes.
    
    Returns:
        StateGraph configurado com todos os nós e arestas
    """
    # Inicializa os agentes
    orchestrator = OrchestratorAgent()
    timeline_agent = TimelineAgent()
    graph_agent = GraphAgent()
    transcription_agent = TranscriptionAgent()
    writer_agent = WriterAgent()
    
    # Cria o grafo
    workflow = StateGraph(GraphState)
    
    # Define o ponto de entrada
    workflow.set_entry_point("orchestrator")
    
    # Wrapper para converter AgentState para dict antes de passar para LangGraph
    async def orchestrator_wrapper(state_dict: dict):
        state = _convert_graph_state_to_agent_state(state_dict)
        result = await orchestrator.execute(state)
        return _convert_state_to_graph_state(result)
    
    async def timeline_wrapper(state_dict: dict):
        state = _convert_graph_state_to_agent_state(state_dict)
        result = await timeline_agent.execute(state)
        return _convert_state_to_graph_state(result)
    
    async def graph_wrapper(state_dict: dict):
        state = _convert_graph_state_to_agent_state(state_dict)
        result = await graph_agent.execute(state)
        return _convert_state_to_graph_state(result)
    
    async def transcription_wrapper(state_dict: dict):
        state = _convert_graph_state_to_agent_state(state_dict)
        result = await transcription_agent.execute(state)
        return _convert_state_to_graph_state(result)
    
    async def writer_wrapper(state_dict: dict):
        state = _convert_graph_state_to_agent_state(state_dict)
        result = await writer_agent.execute(state)
        return _convert_state_to_graph_state(result)
    
    def route_wrapper(state_dict: dict):
        state = _convert_graph_state_to_agent_state(state_dict)
        return orchestrator.route(state)
    
    def route_after_timeline_wrapper(state_dict: dict):
        state = _convert_graph_state_to_agent_state(state_dict)
        return orchestrator.route_after_timeline(state)
    
    def route_after_graph_wrapper(state_dict: dict):
        state = _convert_graph_state_to_agent_state(state_dict)
        return orchestrator.route_after_graph(state)
    
    def route_after_transcription_wrapper(state_dict: dict):
        state = _convert_graph_state_to_agent_state(state_dict)
        return orchestrator.route_after_transcription(state)
    
    # Adiciona nós (agentes)
    workflow.add_node("orchestrator", orchestrator_wrapper)
    workflow.add_node("timeline", timeline_wrapper)
    workflow.add_node("graph", graph_wrapper)
    workflow.add_node("transcription", transcription_wrapper)
    workflow.add_node("writer", writer_wrapper)
    
    # Adiciona arestas condicionais do orquestrador
    workflow.add_conditional_edges(
        "orchestrator",
        route_wrapper,
        {
            "timeline": "timeline",
            "graph": "graph",
            "transcription": "transcription",
            "writer": "writer",
            "all": "timeline",  # Começa com timeline quando "all"
            "end": END,
        }
    )
    
    # Após timeline, pode ir para graph ou writer ou end
    workflow.add_conditional_edges(
        "timeline",
        route_after_timeline_wrapper,
        {
            "graph": "graph",
            "writer": "writer",
            "end": END,
        }
    )
    
    # Após graph, pode ir para writer ou end
    workflow.add_conditional_edges(
        "graph",
        route_after_graph_wrapper,
        {
            "writer": "writer",
            "end": END,
        }
    )
    
    # Após transcription, vai para writer ou end
    workflow.add_conditional_edges(
        "transcription",
        route_after_transcription_wrapper,
        {
            "writer": "writer",
            "end": END,
        }
    )
    
    # Writer sempre termina
    workflow.add_edge("writer", END)
    
    return workflow.compile()


# Instância global do grafo (lazy initialization)
_agent_graph = None


def get_agent_graph() -> StateGraph:
    """
    Retorna a instância do grafo de agentes (singleton).
    
    Returns:
        StateGraph compilado
    """
    global _agent_graph
    if _agent_graph is None:
        _agent_graph = create_agent_graph()
    return _agent_graph


def _convert_state_to_graph_state(state: AgentState) -> dict:
    """Converte AgentState para dicionário compatível com GraphState"""
    return {
        "input_text": state.input_text,
        "input_file_path": state.input_file_path,
        "input_file_type": state.input_file_type,
        "intent": state.intent,
        "document_type": state.document_type,
        "timeline": state.timeline,
        "graph": state.graph,
        "transcription": state.transcription,
        "output": state.output,
        "reference_documents": state.reference_documents,
        "instructions": state.instructions,
        "metadata": state.metadata,
        "numero_processo": state.numero_processo,
        "current_agent": state.current_agent,
        "completed_agents": state.completed_agents,
        "errors": state.errors,
    }


def _convert_graph_state_to_agent_state(graph_state: dict) -> AgentState:
    """Converte dicionário (GraphState) para AgentState"""
    state = AgentState()
    state.input_text = graph_state.get("input_text", "")
    state.input_file_path = graph_state.get("input_file_path")
    state.input_file_type = graph_state.get("input_file_type")
    state.intent = graph_state.get("intent")
    state.document_type = graph_state.get("document_type")
    state.timeline = graph_state.get("timeline")
    state.graph = graph_state.get("graph")
    state.transcription = graph_state.get("transcription")
    state.output = graph_state.get("output")
    state.reference_documents = graph_state.get("reference_documents", [])
    state.instructions = graph_state.get("instructions")
    state.metadata = graph_state.get("metadata", {})
    state.numero_processo = graph_state.get("numero_processo")
    state.current_agent = graph_state.get("current_agent")
    state.completed_agents = graph_state.get("completed_agents", [])
    state.errors = graph_state.get("errors", [])
    return state


async def run_agent_graph(initial_state: AgentState) -> AgentState:
    """
    Executa o grafo de agentes com o estado inicial fornecido.
    
    Args:
        initial_state: Estado inicial do processamento
        
    Returns:
        Estado final após processamento por todos os agentes
    """
    graph = get_agent_graph()
    graph_state = _convert_state_to_graph_state(initial_state)
    
    # Executa o grafo
    final_graph_state = await graph.ainvoke(graph_state)
    
    # Converte de volta para AgentState
    return _convert_graph_state_to_agent_state(final_graph_state)

