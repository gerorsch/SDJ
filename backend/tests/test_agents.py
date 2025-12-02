"""
Testes básicos para a arquitetura multi-agente
"""

import pytest
import asyncio
from agents.state import AgentState
from agents.timeline_agent import TimelineAgent
from agents.graph_agent import GraphAgent
from agents.writer_agent import WriterAgent
from agents.orchestrator import OrchestratorAgent
from ingestion.classifier import DocumentClassifier


# Texto de exemplo para testes
SAMPLE_REPORT = """
PROCESSO Nº 0000000-00.2024.8.17.0001

RELATÓRIO

Em 15 de janeiro de 2024, foi protocolada a petição inicial na qual o autor 
requer indenização por danos morais e materiais.

Em 20 de fevereiro de 2024, foi apresentada a contestação pelo réu, negando 
os fatos narrados pelo autor.

Em 10 de março de 2024, foi realizada audiência de conciliação, sem acordo.

Em 25 de março de 2024, foi proferida sentença julgando procedente o pedido 
do autor, condenando o réu ao pagamento de indenização.

FUNDAMENTAÇÃO

Com base nos documentos dos autos e na legislação aplicável, verifica-se que 
os fatos narrados pelo autor são verdadeiros e configuram dano moral e material.

DISPOSITIVO

JULGO PROCEDENTE o pedido do autor, condenando o réu ao pagamento de 
indenização por danos morais no valor de R$ 10.000,00 e danos materiais no 
valor de R$ 5.000,00.
"""


@pytest.mark.asyncio
async def test_timeline_agent():
    """Testa o Agente Cronologista"""
    agent = TimelineAgent()
    state = AgentState()
    state.input_text = SAMPLE_REPORT
    
    state = await agent.execute(state)
    
    assert state.timeline is not None
    assert "events" in state.timeline
    assert len(state.timeline["events"]) > 0
    assert state.errors == []


@pytest.mark.asyncio
async def test_graph_agent():
    """Testa o Agente Visual"""
    agent = GraphAgent()
    state = AgentState()
    state.input_text = SAMPLE_REPORT
    
    state = await agent.execute(state)
    
    assert state.graph is not None
    assert "nodes" in state.graph
    assert "edges" in state.graph
    assert state.errors == []


@pytest.mark.asyncio
async def test_orchestrator_agent():
    """Testa o Agente Orquestrador"""
    agent = OrchestratorAgent()
    state = AgentState()
    state.input_text = SAMPLE_REPORT
    state.intent = "timeline"
    
    state = await agent.execute(state)
    
    assert state.intent == "timeline"
    assert state.metadata.get("intent") == "timeline"
    assert state.errors == []


def test_document_classifier():
    """Testa o Classificador de Documentos"""
    classifier = DocumentClassifier()
    
    # Testa classificação de sentença
    result = classifier.classify(SAMPLE_REPORT)
    
    assert "class" in result
    assert "confidence" in result
    assert "method" in result
    assert result["class"] in ["peticao_inicial", "contestacao", "sentenca", "despacho", "outros"]


@pytest.mark.asyncio
async def test_agent_state_serialization():
    """Testa serialização do estado"""
    state = AgentState()
    state.input_text = "Teste"
    state.intent = "timeline"
    
    state_dict = state.to_dict()
    
    assert state_dict["input_text"] == "Teste"
    assert state_dict["intent"] == "timeline"
    assert "completed_agents" in state_dict
    assert "errors" in state_dict


@pytest.mark.asyncio
async def test_agent_error_handling():
    """Testa tratamento de erros nos agentes"""
    agent = TimelineAgent()
    state = AgentState()
    # Estado sem input_text deve gerar erro
    
    state = await agent.execute(state)
    
    # O agente deve adicionar erro ao estado
    assert len(state.errors) > 0 or state.timeline is None


def test_orchestrator_intent_inference():
    """Testa inferência de intenção pelo orquestrador"""
    agent = OrchestratorAgent()
    
    # Testa inferência para arquivo de áudio
    state = AgentState()
    state.input_file_type = "mp3"
    state.intent = None
    
    inferred = agent._infer_intent(state)
    assert inferred == "transcription"
    
    # Testa inferência padrão
    state = AgentState()
    state.input_text = "Texto qualquer"
    state.intent = None
    
    inferred = agent._infer_intent(state)
    assert inferred == "all"


if __name__ == "__main__":
    # Executa testes básicos
    print("Executando testes básicos...")
    
    # Teste síncrono
    classifier = DocumentClassifier()
    result = classifier.classify(SAMPLE_REPORT)
    print(f"✓ Classificação: {result['class']} (confiança: {result['confidence']:.2f})")
    
    # Teste assíncrono
    async def run_async_tests():
        agent = TimelineAgent()
        state = AgentState()
        state.input_text = SAMPLE_REPORT
        state = await agent.execute(state)
        print(f"✓ Timeline extraído: {len(state.timeline.get('events', []))} eventos")
    
    asyncio.run(run_async_tests())
    print("✓ Testes básicos concluídos!")

