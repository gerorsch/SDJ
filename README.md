# Sistema Distribuído - SDJ

**Projeto para Sistemas Distribuídos - 2ª V.A.**  
**Data de Entrega: 12/12/2025**

## 📋 Visão Geral

Sistema distribuído para processamento de documentos jurídicos, extração de relatórios e geração automática de sentenças utilizando Inteligência Artificial.

## 🏗️ Arquitetura do Sistema

O sistema é composto por **5 módulos distribuídos** (processos independentes):

### Módulos do Sistema

1. **Frontend (Streamlit)** - Interface Gráfica
   - Container: `streamlit`
   - Porta: `8501`
   - Responsabilidade: Interface gráfica para usuários acessarem todas as funcionalidades
   - Tecnologia: Python + Streamlit

2. **Backend API (FastAPI)** - Processamento de Documentos
   - Container: `fastapi`
   - Porta: `8010` (externa) / `8001` (interna)
   - Responsabilidade: Processa PDFs, extrai relatórios, gera sentenças via LLM
   - Tecnologia: Python + FastAPI
   - Endpoints principais:
     - `POST /processar` - Extrai relatório de PDF
     - `POST /gerar-sentenca` - Gera sentença baseada em relatório e referências
     - `GET /health` - Health check

3. **Elasticsearch** - Motor de Busca Semântica (RAG)
   - Container: `elasticsearch`
   - Porta: `9200`
   - Responsabilidade: Armazena e busca sentenças similares para referência
   - Tecnologia: Elasticsearch 8.15.1

4. **PostgreSQL** - Banco de Dados
   - Container: `postgres`
   - Porta: `5432`
   - Responsabilidade: Armazena metadados e dados estruturados
   - Tecnologia: PostgreSQL 13

5. **Nginx** - Proxy Reverso
   - Container: `nginx`
   - Porta: `80`
   - Responsabilidade: Roteamento e balanceamento de requisições
   - Tecnologia: Nginx

## 🔄 Comunicação entre Componentes

```
┌─────────────┐
│   Usuário   │
└──────┬───────┘
       │
       ▼
┌─────────────────┐
│  Frontend       │  (Streamlit - Porta 8501)
│  Interface GUI  │
└──────┬──────────┘
       │ HTTP
       ▼
┌─────────────────┐
│  Nginx          │  (Proxy Reverso - Porta 80)
│  Load Balancer  │
└──────┬──────────┘
       │
       ├──────────────┐
       │              │
       ▼              ▼
┌─────────────┐  ┌──────────────┐
│  Backend    │  │ Elasticsearch │
│  FastAPI    │◄─┤ (RAG Search)  │
│  (Porta     │  │ (Porta 9200)  │
│   8001)     │  └──────────────┘
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ PostgreSQL  │
│ (Porta 5432)│
└─────────────┘
```

### Fluxo de Dados

1. **Upload de PDF**: Usuário faz upload via Frontend → Frontend envia para Backend
2. **Processamento**: Backend processa PDF → Extrai texto → Salva no Elasticsearch
3. **Geração de Sentença**: 
   - Backend busca sentenças similares no Elasticsearch (RAG)
   - Backend chama LLM (Claude/OpenAI) para gerar sentença
   - Backend retorna resultado para Frontend
4. **Exibição**: Frontend exibe sentença gerada e permite download

## 🚀 Como Executar

### Pré-requisitos

- Docker e Docker Compose instalados
- Arquivo `.env` configurado com:
  - `OPENAI_API_KEY` ou `ANTHROPIC_API_KEY`
  - Outras variáveis de ambiente necessárias

### Executar o Sistema

```bash
# 1. Clone o repositório (se ainda não tiver)
git clone <url-do-repositorio>
cd SDJ

# 2. Configure o arquivo .env
cp .env.example .env
# Edite .env com suas chaves de API

# 3. Inicie todos os módulos
docker-compose up -d

# 4. Acesse a interface gráfica
# Abra o navegador em: http://localhost:8501
```

### Verificar Status dos Módulos

```bash
# Ver logs de todos os módulos
docker-compose logs -f

# Ver status dos containers
docker-compose ps

# Verificar saúde do backend
curl http://localhost:8010/health

# Verificar Elasticsearch
curl http://localhost:9200/_cluster/health
```

### Parar o Sistema

```bash
docker-compose down
```

## 📁 Estrutura do Projeto

```
jurisprudentia/
├── backend/              # Módulo Backend (FastAPI)
│   ├── main.py          # API principal
│   ├── services/        # Serviços (LLM, RAG, etc.)
│   ├── preprocessing/   # Processamento de PDFs
│   └── Dockerfile
├── frontend/             # Módulo Frontend (Streamlit)
│   ├── streamlit_app.py # Interface gráfica
│   └── Dockerfile
├── docker-compose.yml    # Orquestração dos módulos
├── nginx.conf           # Configuração do proxy
└── README.md            # Este arquivo
```

## 🧪 Testes de Comunicação

### Teste 1: Frontend → Backend

```bash
# Teste de health check
curl http://localhost:8010/health
```

### Teste 2: Backend → Elasticsearch

```bash
# Verificar se Elasticsearch está respondendo
curl http://localhost:9200/_cluster/health
```

### Teste 3: Fluxo Completo

1. Acesse http://localhost:8501
2. Faça upload de um PDF de processo
3. Clique em "Extrair Relatório"
4. Configure parâmetros e clique em "Gerar Sentença"
5. Verifique se a sentença foi gerada com sucesso

## 📊 Tecnologias Utilizadas

- **Python 3.9+**: Linguagem principal
- **FastAPI**: Framework para API REST
- **Streamlit**: Framework para interface gráfica
- **Elasticsearch**: Motor de busca semântica
- **PostgreSQL**: Banco de dados relacional
- **Docker**: Containerização
- **Docker Compose**: Orquestração de containers
- **Nginx**: Proxy reverso
- **Claude/OpenAI**: Modelos de linguagem para geração de sentenças

## ✅ Requisitos do Projeto Atendidos

- ✅ **Sistema Distribuído**: 5 módulos (processos) independentes
- ✅ **Interface Gráfica**: Streamlit permite acesso a todas as funcionalidades
- ✅ **Comunicação via Rede**: Módulos comunicam via HTTP/REST
- ✅ **Containerização**: Todos os módulos rodam em containers Docker
- ✅ **Repositório Git**: Código versionado (obrigatório desde primeira semana)

## 📝 Notas para Apresentação

### Pontos a Destacar no Vídeo:

1. **Arquitetura**: Mostrar os 5 módulos e como se comunicam
2. **Funcionalidades**: 
   - Upload e processamento de PDF
   - Extração de relatório
   - Geração automática de sentença
3. **Distribuição**: Mostrar que cada módulo é um processo/container independente
4. **Comunicação**: Demonstrar fluxo de dados entre módulos
5. **Código**: Mostrar estrutura do projeto e principais arquivos

## 🔧 Desenvolvimento

### Adicionar Novo Endpoint no Backend

1. Edite `backend/main.py`
2. Adicione a rota FastAPI
3. Reinicie o container: `docker-compose restart fastapi`

### Modificar Frontend

1. Edite `frontend/streamlit_app.py`
2. O Streamlit recarrega automaticamente (hot reload)

## 📞 Contato

Para dúvidas sobre o projeto, consulte o repositório Git ou entre em contato com a equipe.

---

**Versão**: 1.0  
**Última Atualização**: 02/12/2024
