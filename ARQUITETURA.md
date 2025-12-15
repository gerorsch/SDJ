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
                    │    MÓDULO 1: FRONTEND (Next.js)     │
                    │    Container: frontend               │
                    │    Porta: 3000                       │
                    │    Tecnologia: Next.js + TypeScript  │
                    └──────────────┬──────────────────────┘
                                   │
                                   │ HTTP REST API
                                   │ (API_URL)
                                   ▼
                    ┌─────────────────────────────────────┐
                    │    MÓDULO 6: NGINX (Proxy)          │
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
                   │ AMQP (RabbitMQ)
                   ▼
    ┌───────────────────────────┐
    │  MÓDULO 7: RABBITMQ       │
    │  Container: rabbitmq       │
    │  Porta: 5672 (AMQP)         │
    │  Porta: 15672 (Management) │
    │  Função: Message Broker     │
    └──────────────┬────────────┘
                   │
                   │ Consome tarefas
                   ▼
    ┌───────────────────────────┐
    │  MÓDULO 8: CELERY WORKER  │
    │  Container: celery_worker  │
    │  Tecnologia: Celery         │
    │  Função: Processamento       │
    │         Assíncrono           │
    └──────────────┬────────────┘
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

### Módulo 1: Frontend (Next.js + TypeScript)

**Arquivo**: `frontend-next/app/page.tsx`

**Responsabilidades**:
- Interface gráfica para upload de PDFs
- Exibição de relatórios extraídos
- Configuração de parâmetros de geração
- Visualização e download de sentenças geradas

**Tecnologias**:
- Next.js 14 (Framework React)
- TypeScript (Tipagem estática)
- React 18 (Biblioteca UI)
- Axios (Cliente HTTP)

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
- `POST /processar` - Processa PDF e extrai relatório (síncrono - compatibilidade)
- `POST /queue/processar` - Enfileira processamento de PDF (assíncrono)
- `POST /gerar-sentenca` - Gera sentença baseada em relatório (síncrono - compatibilidade)
- `POST /queue/gerar-sentenca` - Enfileira geração de sentença (assíncrono)
- `GET /tasks/{task_id}/status` - Verifica status de uma tarefa
- `GET /tasks/{task_id}/result` - Obtém resultado de uma tarefa concluída
- `GET /health` - Health check do serviço

**Comunicação**:
- **Recebe**: Requisições HTTP do Frontend
- **Envia**: Tarefas para RabbitMQ (filas)
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

### Módulo 7: RabbitMQ (Message Broker)

**Container**: `rabbitmq`

**Responsabilidades**:
- Gerenciamento de filas de mensagens
- Distribuição de tarefas para workers
- Persistência de mensagens
- Interface de gerenciamento (Management UI)

**Comunicação**:
- **Recebe**: Tarefas do Backend API (via AMQP)
- **Distribui**: Tarefas para Celery Workers
- **Retorna**: Status e resultados de tarefas

**Tecnologias**:
- RabbitMQ 3-management-alpine
- AMQP Protocol
- Management Plugin

**Acesso**:
- AMQP: Porta 5672
- Management UI: http://localhost:15672 (guest/guest)

---

### Módulo 8: Celery Worker

**Container**: `celery_worker`

**Responsabilidades**:
- Processamento assíncrono de tarefas pesadas
- Processamento de PDFs
- Geração de sentenças
- Busca semântica de documentos

**Tasks Principais**:
- `processar_pdf_task`: Processa PDF e extrai relatório
- `gerar_sentenca_task`: Gera sentença baseada em relatório
- `buscar_documentos_task`: Busca documentos similares

**Comunicação**:
- **Consome**: Tarefas do RabbitMQ
- **Envia**: Requisições para Elasticsearch
- **Envia**: Requisições para LLM APIs
- **Retorna**: Resultados via RabbitMQ

**Tecnologias**:
- Celery 5.3+
- Python 3.9+
- Mesmas dependências do Backend

**Configuração**:
- Concurrency: 2 workers simultâneos
- Retry: 3 tentativas automáticas
- Timeout: 30 minutos por tarefa

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

### Fluxo 1: Processamento de PDF (Assíncrono com Fila)

```
1. Usuário → Frontend: Upload de PDF
2. Frontend → Backend: POST /queue/processar (multipart/form-data)
3. Backend → RabbitMQ: Enfileira tarefa processar_pdf_task
4. Backend → Frontend: Retorna task_id (202 Accepted)
5. Frontend: Inicia polling do status (GET /tasks/{task_id}/status)
6. Celery Worker: Consome tarefa do RabbitMQ
7. Celery Worker: Processa PDF (extrai texto)
8. Celery Worker → RabbitMQ: Retorna resultado
9. Frontend (polling): Detecta status COMPLETED
10. Frontend → Backend: GET /tasks/{task_id}/result
11. Backend → Frontend: Retorna relatório extraído (JSON)
12. Frontend: Exibe relatório na interface
```

### Fluxo 2: Geração de Sentença (Assíncrono com Fila)

```
1. Usuário → Frontend: Configura parâmetros e clica "Gerar Sentença"
2. Frontend → Backend: POST /queue/gerar-sentenca
3. Backend → RabbitMQ: Enfileira tarefa gerar_sentenca_task
4. Backend → Frontend: Retorna task_id (202 Accepted)
5. Frontend: Inicia polling do status (GET /tasks/{task_id}/status)
6. Celery Worker: Consome tarefa do RabbitMQ
7. Celery Worker → Elasticsearch: Busca documentos similares
8. Celery Worker → LLM API: Gera sentença
9. Celery Worker: Salva arquivos (.docx e .zip)
10. Celery Worker → RabbitMQ: Retorna resultado
11. Frontend (polling): Detecta status COMPLETED
12. Frontend → Backend: GET /tasks/{task_id}/result
13. Backend → Frontend: Retorna sentença gerada (JSON)
14. Frontend: Exibe sentença e permite download
```
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

