# Arquitetura do Sistema - SDJ

## Diagrama de Arquitetura

```
                    ┌─────────────────────────────────────┐
                    │         USUÁRIO FINAL               │
                    └──────────────┬──────────────────────┘
                                   │
                                   │ HTTP/HTTPS
                                   ▼
                    ┌─────────────────────────────────────┐
                    │    MÓDULO 1: FRONTEND (Streamlit)    │
                    │    Container: streamlit              │
                    │    Porta: 8501                       │
                    │    Tecnologia: Python + Streamlit    │
                    └──────────────┬──────────────────────┘
                                   │
                                   │ HTTP REST API
                                   │ (API_URL)
                                   ▼
                    ┌─────────────────────────────────────┐
                    │    MÓDULO 5: NGINX (Proxy)          │
                    │    Container: nginx                  │
                    │    Porta: 80                        │
                    │    Função: Load Balancing            │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
    ┌───────────────────────────┐   ┌───────────────────────────┐
    │  MÓDULO 2: BACKEND API    │   │  MÓDULO 3: ELASTICSEARCH  │
    │  Container: fastapi        │◄──┤  Container: elasticsearch  │
    │  Porta: 8001 (interna)     │   │  Porta: 9200              │
    │  Tecnologia: FastAPI       │   │  Função: Busca Semântica  │
    └──────────────┬────────────┘   │  (RAG)                     │
                   │                └───────────────────────────┘
                   │
                   │ SQL
                   ▼
    ┌───────────────────────────┐
    │  MÓDULO 4: POSTGRESQL     │
    │  Container: postgres       │
    │  Porta: 5432               │
    │  Função: Dados Estruturados│
    └───────────────────────────┘
```

## Detalhamento dos Módulos

### Módulo 1: Frontend (Streamlit)

**Arquivo**: `frontend/streamlit_app.py`

**Responsabilidades**:
- Interface gráfica para upload de PDFs
- Exibição de relatórios extraídos
- Configuração de parâmetros de geração
- Visualização e download de sentenças geradas

**Comunicação**:
- **Envia**: Requisições HTTP para Backend API
- **Recebe**: Respostas JSON com dados processados

**Tecnologias**:
- Python 3.9+
- Streamlit
- Requests (para chamadas HTTP)

---

### Módulo 2: Backend API (FastAPI)

**Arquivo**: `backend/main.py`

**Responsabilidades**:
- Processamento de PDFs (extração de texto)
- Extração de relatórios de processos
- Busca semântica de sentenças similares (via Elasticsearch)
- Geração de sentenças usando LLM (Claude/OpenAI)
- Gerenciamento de arquivos temporários

**Endpoints Principais**:
- `POST /processar` - Processa PDF e extrai relatório
- `POST /gerar-sentenca` - Gera sentença baseada em relatório
- `GET /health` - Health check do serviço

**Comunicação**:
- **Recebe**: Requisições HTTP do Frontend
- **Envia**: Requisições para Elasticsearch (busca)
- **Envia**: Requisições para LLM APIs (Claude/OpenAI)
- **Envia**: Queries SQL para PostgreSQL

**Tecnologias**:
- Python 3.9+
- FastAPI
- Elasticsearch client
- Anthropic/OpenAI SDKs

---

### Módulo 3: Elasticsearch (RAG)

**Container**: `elasticsearch`

**Responsabilidades**:
- Armazenamento de sentenças indexadas
- Busca semântica por similaridade (KNN)
- Reranking de resultados

**Comunicação**:
- **Recebe**: Queries de busca do Backend
- **Retorna**: Lista de documentos similares

**Tecnologias**:
- Elasticsearch 8.15.1
- Vector Search (KNN)

---

### Módulo 4: PostgreSQL

**Container**: `postgres`

**Responsabilidades**:
- Armazenamento de metadados
- Dados estruturados do sistema

**Comunicação**:
- **Recebe**: Queries SQL do Backend
- **Retorna**: Dados estruturados

**Tecnologias**:
- PostgreSQL 13

---

### Módulo 5: Nginx (Proxy Reverso)

**Container**: `nginx`

**Responsabilidades**:
- Roteamento de requisições
- Load balancing (futuro)
- SSL/TLS termination (futuro)

**Comunicação**:
- **Recebe**: Requisições HTTP do Frontend
- **Roteia**: Para Backend ou Frontend conforme necessário

**Tecnologias**:
- Nginx

---

## Fluxo de Dados Detalhado

### Fluxo 1: Processamento de PDF

```
1. Usuário → Frontend: Upload de PDF
2. Frontend → Backend: POST /processar (multipart/form-data)
3. Backend: Processa PDF (extrai texto)
4. Backend → Elasticsearch: Indexa texto (opcional)
5. Backend → Frontend: Retorna relatório extraído (JSON)
6. Frontend: Exibe relatório na interface
```

### Fluxo 2: Geração de Sentença

```
1. Usuário → Frontend: Configura parâmetros e clica "Gerar Sentença"
2. Frontend → Backend: POST /gerar-sentenca (relatório + parâmetros)
3. Backend → Elasticsearch: Busca sentenças similares (RAG)
4. Elasticsearch → Backend: Retorna top-K sentenças similares
5. Backend → LLM API (Claude/OpenAI): Gera sentença baseada em contexto
6. LLM API → Backend: Retorna sentença gerada
7. Backend → Frontend: Retorna sentença completa (JSON)
8. Frontend: Exibe sentença e permite download
```

## Protocolos de Comunicação

| Módulo Origem | Módulo Destino | Protocolo | Porta |
|---------------|----------------|-----------|-------|
| Frontend | Backend | HTTP/REST | 8001 |
| Backend | Elasticsearch | HTTP/REST | 9200 |
| Backend | PostgreSQL | SQL/TCP | 5432 |
| Frontend | Nginx | HTTP | 80 |
| Nginx | Backend | HTTP | 8001 |

## Dependências entre Módulos

```
Frontend depende de:
  - Backend (API_URL)
  - Elasticsearch (para status, opcional)

Backend depende de:
  - Elasticsearch (ELASTICSEARCH_HOST)
  - PostgreSQL (POSTGRES_HOST)
  - LLM APIs (OPENAI_API_KEY / ANTHROPIC_API_KEY)

Nginx depende de:
  - Frontend (upstream)
  - Backend (upstream)
```

## Escalabilidade

O sistema foi projetado para ser escalável:

- **Frontend**: Pode ter múltiplas instâncias atrás do Nginx
- **Backend**: Pode ter múltiplas instâncias (load balancing via Nginx)
- **Elasticsearch**: Suporta cluster (configuração futura)
- **PostgreSQL**: Pode ter réplicas (configuração futura)

## Segurança

- CORS configurado no Backend
- Variáveis de ambiente para credenciais
- Isolamento de containers via Docker network
- Autenticação no Frontend (auth_tjpe.py)

---

**Documento criado para**: Entrega 02/12 - Protótipo e Comunicação entre Componentes

