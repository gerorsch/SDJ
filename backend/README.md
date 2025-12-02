# Backend API - Módulo 2

## Visão Geral

Backend FastAPI responsável por processar documentos jurídicos, extrair relatórios e gerar sentenças utilizando Inteligência Artificial.

## Endpoints Principais

### Health Check

```http
GET /health
```

Retorna status do serviço.

**Resposta**:
```json
{
  "status": "healthy",
  "environment": "development",
  "allowed_origins": 6
}
```

---

### Processar PDF

```http
POST /processar
Content-Type: multipart/form-data
```

Processa um PDF e extrai o relatório do processo.

**Parâmetros**:
- `pdf`: Arquivo PDF (multipart/form-data)

**Resposta**:
```json
{
  "relatorio": "Texto do relatório extraído...",
  "numero_processo": "0000000-00.2024.8.17.0001"
}
```

**Exemplo de uso**:
```python
import requests

with open("processo.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8010/processar",
        files={"pdf": f}
    )
    result = response.json()
    print(result["relatorio"])
```

---

### Gerar Sentença

```http
POST /gerar-sentenca
Content-Type: multipart/form-data
```

Gera uma sentença completa baseada no relatório e documentos de referência.

**Parâmetros**:
- `relatorio` (form): Texto do relatório
- `instrucoes_usuario` (form, opcional): Instruções adicionais
- `numero_processo` (form, opcional): Número do processo
- `top_k` (form, default: 10): Número de documentos similares
- `rerank_top_k` (form, default: 5): Número de documentos após rerank
- `arquivos_referencia` (file, opcional): Arquivos DOCX de referência
- `buscar_na_base` (form, default: false): Se deve buscar na base Elasticsearch

**Resposta**:
```json
{
  "documentos": [
    {
      "id": "doc1",
      "relatorio": "...",
      "fundamentacao": "...",
      "dispositivo": "...",
      "score": 0.95,
      "rerank_score": 0.98
    }
  ],
  "sentenca": "Texto da sentença gerada...",
  "sentenca_url": "/download/sentenca/xxx.docx",
  "referencias_url": "/download/referencias/xxx.zip",
  "numero_processo": "0000000-00.2024.8.17.0001"
}
```

**Exemplo de uso**:
```python
import requests

data = {
    "relatorio": "Texto do relatório...",
    "instrucoes_usuario": "Enfatizar danos morais",
    "top_k": "10",
    "rerank_top_k": "5",
    "buscar_na_base": "true"
}

response = requests.post(
    "http://localhost:8010/gerar-sentenca",
    data=data
)
result = response.json()
print(result["sentenca"])
```

---

### Download de Arquivos

```http
GET /download/sentenca/{file_id}.docx
GET /download/referencias/{file_id}.zip
```

Baixa arquivos gerados (sentença ou referências).

---

## Estrutura do Código

```
backend/
├── main.py                    # API principal (FastAPI)
├── services/
│   ├── llm.py                # Integração com LLM (Claude/OpenAI)
│   ├── retrieval_rerank.py   # Busca semântica + rerank
│   ├── docx_parser.py         # Parser de documentos DOCX
│   └── docx_utils.py          # Utilitários para DOCX
├── preprocessing/
│   ├── process_report_pipeline.py  # Pipeline de processamento
│   └── sentence_indexing_rag.py    # Indexação no Elasticsearch
└── database/
    ├── elasticsearch.py       # Cliente Elasticsearch
    └── postgres.py            # Cliente PostgreSQL
```

## Variáveis de Ambiente

```bash
# APIs de LLM
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Banco de Dados
ELASTICSEARCH_HOST=http://elasticsearch:9200
POSTGRES_HOST=postgres
POSTGRES_DB=rag_database
POSTGRES_USER=rag_user
POSTGRES_PASSWORD=rag_password

# Ambiente
ENVIRONMENT=development
```

## Comunicação com Outros Módulos

### Elasticsearch

O backend se comunica com Elasticsearch para:
- Buscar sentenças similares (RAG)
- Indexar novos documentos

**Exemplo**:
```python
from services.retrieval_rerank import recuperar_documentos_similares

docs = recuperar_documentos_similares(
    query="Texto do relatório",
    top_k=10,
    rerank_top_k=5
)
```

### PostgreSQL

O backend pode usar PostgreSQL para:
- Armazenar metadados
- Histórico de processamentos

## Testes

```bash
# Teste de health check
curl http://localhost:8010/health

# Teste de processamento (requer arquivo PDF)
curl -X POST http://localhost:8010/processar \
  -F "pdf=@processo.pdf"
```

## Logs

Os logs são exibidos no console do container. Para ver:

```bash
docker-compose logs -f fastapi
```

---

**Módulo**: Backend API (Módulo 2 do Sistema Distribuído)

