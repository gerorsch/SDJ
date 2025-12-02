# Arquitetura Multi-Agente - SDJ

Este módulo implementa a arquitetura multi-agente proposta no documento de planejamento do projeto SDJ, utilizando LangGraph para orquestração.

## Visão Geral

A arquitetura multi-agente é composta por:

1. **Agente Orquestrador**: Recebe a intenção do usuário e delega para agentes especialistas
2. **Agente Cronologista (Timeline)**: Extrai datas, eventos e fatos do relatório
3. **Agente Visual (Graph)**: Mapeia entidades e relações em grafo de conhecimento
4. **Agente de Audiência (Transcription)**: Transcreve e diariza arquivos de áudio
5. **Agente Redator (Writer)**: Gera minutas e sentenças baseadas em perfil e referências

## Estrutura

```
agents/
├── __init__.py          # Exporta todos os agentes
├── base.py              # Classe base BaseAgent
├── state.py             # AgentState - estado compartilhado
├── graph.py             # Grafo LangGraph de orquestração
├── orchestrator.py      # Agente Orquestrador
├── timeline_agent.py    # Agente Cronologista
├── graph_agent.py       # Agente Visual
├── transcription_agent.py # Agente de Audiência
└── writer_agent.py      # Agente Redator
```

## Fluxo de Execução

```
[Entrada] → [Orquestrador] → [Agente Especialista] → [Agregação] → [Saída]
```

1. **Entrada**: Texto ou arquivo é recebido
2. **Orquestrador**: Classifica intenção e roteia para agente apropriado
3. **Agente Especialista**: Processa a tarefa específica
4. **Agregação**: Resultados são combinados (quando necessário)
5. **Saída**: Resultado final é retornado

## Uso Básico

### Processamento Completo via API

```python
POST /agents/process
{
    "text": "Texto do relatório...",
    "intent": "all",  # ou "timeline", "graph", "write", etc.
    "instructions": "Instruções opcionais",
    "numero_processo": "0000000-00.0000.0.00.0000"
}
```

### Uso Programático

```python
from agents.state import AgentState
from agents.graph import run_agent_graph

# Cria estado inicial
state = AgentState()
state.input_text = "Texto do relatório..."
state.intent = "all"

# Executa o grafo
final_state = await run_agent_graph(state)

# Acessa resultados
print(final_state.timeline)
print(final_state.graph)
print(final_state.output)
```

## Agentes Especialistas

### Agente Orquestrador

Responsável por:
- Receber a intenção do usuário
- Classificar o tipo de documento (se necessário)
- Rotear para o agente especialista apropriado
- Coordenar o fluxo de trabalho

**Intenções suportadas**:
- `timeline`: Apenas extração de timeline
- `graph`: Apenas extração de grafo
- `transcription`: Apenas transcrição
- `write`: Apenas geração de sentença
- `all`: Processa tudo (timeline → graph → write)

### Agente Cronologista (Timeline)

Extrai datas, eventos e fatos do relatório, criando uma timeline estruturada.

**Input**: Texto do relatório
**Output**: JSON com eventos, datas-chave e resumo cronológico

```json
{
    "events": [
        {
            "date": "01/01/2024",
            "description": "Petição inicial protocolada",
            "type": "peticao",
            "relevance": "alta"
        }
    ],
    "key_dates": ["01/01/2024", "15/02/2024"],
    "summary": "Resumo cronológico..."
}
```

### Agente Visual (Graph)

Mapeia entidades (pessoas, organizações, conceitos) e suas relações.

**Input**: Texto do relatório
**Output**: Grafo de conhecimento (NetworkX + JSON)

```json
{
    "nodes": [
        {"id": "node_1", "label": "João Silva", "type": "pessoa"}
    ],
    "edges": [
        {"source": "node_1", "target": "node_2", "label": "processa"}
    ],
    "networkx_serialized": {...}
}
```

### Agente de Audiência (Transcription)

Transcreve e diariza arquivos de áudio (MP3, MP4).

**Input**: Arquivo de áudio
**Output**: Transcrição + diarização

**Nota**: Atualmente em modo placeholder. Configure `WHISPERX_ENABLED=true` para usar transcrição real.

### Agente Redator (Writer)

Gera minutas e sentenças baseadas em perfil (Juiz/Advogado) e documentos de referência.

**Input**: Relatório + documentos de referência + instruções
**Output**: Sentença/minuta formatada

## Estado Compartilhado (AgentState)

O `AgentState` é o estado compartilhado entre todos os agentes:

```python
@dataclass
class AgentState:
    input_text: str                    # Texto de entrada
    input_file_path: Optional[str]     # Caminho do arquivo
    intent: Optional[str]              # Intenção do usuário
    timeline: Optional[dict]           # Resultado do TimelineAgent
    graph: Optional[dict]               # Resultado do GraphAgent
    transcription: Optional[dict]       # Resultado do TranscriptionAgent
    output: Optional[str]               # Resultado final
    reference_documents: List[dict]    # Documentos de referência
    metadata: dict                     # Metadados
    completed_agents: List[str]         # Agentes completados
    errors: List[str]                  # Erros ocorridos
```

## Configuração

Variáveis de ambiente relevantes:

```bash
# Modelos LLM
TIMELINE_MODEL=claude-sonnet-4-20250514
GRAPH_MODEL=claude-sonnet-4-20250514
DEFAULT_USER_PROFILE=juiz

# Transcrição
WHISPERX_ENABLED=false

# Classificação
BERT_CLASSIFIER_MODEL=neuralmind/bert-base-portuguese-cased
```

## Endpoints API

### POST /agents/process
Processa texto/arquivo usando a arquitetura multi-agente completa.

### POST /agents/timeline
Extrai timeline usando apenas o Agente Cronologista.

### POST /agents/graph
Extrai grafo usando apenas o Agente Visual.

### POST /agents/classify
Classifica o tipo de documento usando Classificador BERT.

## Compatibilidade

A arquitetura multi-agente é uma camada adicional sobre o sistema existente. Todos os endpoints originais (`/processar`, `/gerar-sentenca`) continuam funcionando normalmente.

## Próximos Passos

1. Fine-tuning do modelo BERT para classificação de documentos jurídicos
2. Integração completa com WhisperX para transcrição
3. Implementação de Vector DB (Qdrant) para substituir Elasticsearch
4. Adição de mais agentes especialistas conforme necessário

## Exemplos

Veja `tests/test_agents.py` para exemplos de uso e testes.

