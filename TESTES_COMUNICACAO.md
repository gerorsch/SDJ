# Guia de Testes de Comunicação - SDJ

Este documento descreve como testar a comunicação entre os módulos do sistema distribuído SDJ.

## 📋 Pré-requisitos

Certifique-se de que todos os containers estão rodando:

```bash
cd SDJ
docker compose ps
```

Todos os containers devem estar com status `Up` e `healthy` (quando aplicável).

---

## 🧪 Testes de Comunicação

### 1. Teste: Frontend → Backend

**Objetivo**: Verificar se o Frontend consegue se comunicar com o Backend.

#### Teste 1.1: Health Check do Backend

```bash
curl http://localhost:8010/health
```

**Resposta esperada**:
```json
{
  "status": "healthy",
  "environment": "development",
  "allowed_origins": 6
}
```

#### Teste 1.2: Via Navegador

1. Abra o navegador em: http://localhost:8501
2. A interface do Streamlit deve carregar
3. O Frontend faz requisições HTTP para o Backend automaticamente

#### Teste 1.3: Verificar Logs de Comunicação

```bash
# Logs do Frontend (mostra requisições HTTP)
docker compose logs streamlit | grep -i "http\|api\|request"

# Logs do Backend (mostra requisições recebidas)
docker compose logs fastapi | grep -i "request\|POST\|GET"
```

---

### 2. Teste: Backend → Elasticsearch

**Objetivo**: Verificar se o Backend consegue buscar documentos no Elasticsearch.

#### Teste 2.1: Health Check do Elasticsearch

```bash
curl http://localhost:9200/_cluster/health
```

**Resposta esperada**:
```json
{
  "cluster_name": "docker-cluster",
  "status": "green",
  "number_of_nodes": 1,
  ...
}
```

#### Teste 2.2: Teste de Busca (via Backend)

```bash
# Teste de busca semântica (requer relatório de teste)
curl -X POST http://localhost:8010/gerar-sentenca \
  -F "relatorio=Teste de comunicação entre Backend e Elasticsearch" \
  -F "top_k=5" \
  -F "rerank_top_k=3" \
  -F "buscar_na_base=true"
```

#### Teste 2.3: Verificar Comunicação Interna

```bash
# Verificar se o Backend consegue acessar Elasticsearch pela rede Docker
docker compose exec fastapi python3 -c "
import requests
try:
    r = requests.get('http://elasticsearch:9200/_cluster/health', timeout=5)
    print(f'Status: {r.status_code}')
    print(f'Resposta: {r.json()}')
except Exception as e:
    print(f'Erro: {e}')
"
```

---

### 3. Teste: Backend → PostgreSQL

**Objetivo**: Verificar se o Backend consegue se conectar ao PostgreSQL.

#### Teste 3.1: Verificar PostgreSQL está acessível

```bash
# Teste de conexão (do host)
docker compose exec postgres pg_isready -U rag_user
```

**Resposta esperada**: `postgres:5432 - accepting connections`

#### Teste 3.2: Teste de Conexão via Backend

```bash
# Verificar logs do Backend para erros de conexão PostgreSQL
docker compose logs fastapi | grep -i "postgres\|database\|connection"
```

#### Teste 3.3: Teste Manual de Conexão

```bash
# Conectar ao PostgreSQL via container
docker compose exec postgres psql -U rag_user -d rag_database -c "SELECT version();"
```

---

### 4. Teste: Frontend → Nginx → Backend

**Objetivo**: Verificar o fluxo completo através do proxy reverso.

#### Teste 4.1: Acesso via Nginx

```bash
# Teste via Nginx (porta 80)
curl http://localhost:80/health
```

**Nota**: Isso depende da configuração do `nginx.conf`. Se não estiver configurado, pode retornar 404.

#### Teste 4.2: Acesso Direto ao Backend (bypass Nginx)

```bash
# Teste direto (porta 8010)
curl http://localhost:8010/health
```

---

### 5. Teste Completo: Fluxo End-to-End

**Objetivo**: Testar o fluxo completo de processamento.

#### Teste 5.1: Processar PDF

```bash
# Criar um arquivo de teste (ou usar um PDF real)
curl -X POST http://localhost:8010/processar \
  -F "pdf=@/caminho/para/seu/arquivo.pdf"
```

#### Teste 5.2: Gerar Sentença

```bash
# Primeiro, processe um PDF para obter o relatório
# Depois, gere a sentença:
curl -X POST http://localhost:8010/gerar-sentenca \
  -F "relatorio=Texto do relatório aqui..." \
  -F "top_k=10" \
  -F "rerank_top_k=5" \
  -F "buscar_na_base=true"
```

---

## 🔧 Script Automatizado de Testes

Execute o script de verificação:

```bash
cd SDJ
./verificar_sistema.sh
```

Este script testa:
- ✅ Status dos containers
- ✅ Health checks de todos os serviços
- ✅ Comunicação básica entre módulos

---

## 📊 Verificação de Rede Docker

### Verificar Rede Interna

```bash
# Listar redes
docker network ls

# Inspecionar a rede do projeto
docker network inspect sdj_network
```

Isso mostra todos os containers conectados e seus IPs internos.

### Testar Comunicação entre Containers

```bash
# Do Backend para Elasticsearch
docker compose exec fastapi ping -c 2 elasticsearch

# Do Backend para PostgreSQL
docker compose exec fastapi ping -c 2 postgres

# Do Frontend para Backend
docker compose exec streamlit ping -c 2 fastapi
```

---

## 🐛 Troubleshooting

### Problema: Backend não responde

```bash
# Verificar logs
docker compose logs fastapi

# Verificar se está rodando
docker compose ps fastapi

# Reiniciar
docker compose restart fastapi
```

### Problema: Elasticsearch não acessível

```bash
# Verificar logs
docker compose logs elasticsearch

# Verificar saúde
curl http://localhost:9200/_cluster/health

# Verificar se o índice existe
curl http://localhost:9200/_cat/indices
```

### Problema: Frontend não carrega

```bash
# Verificar logs
docker compose logs streamlit

# Verificar variável API_URL
docker compose exec streamlit env | grep API_URL

# Deve mostrar: API_URL=http://fastapi:8001
```

### Problema: Comunicação entre containers falha

```bash
# Verificar se estão na mesma rede
docker network inspect sdj_network | grep -A 5 "Containers"

# Testar ping entre containers
docker compose exec fastapi ping elasticsearch
```

---

## 📝 Checklist de Testes

- [ ] Todos os containers estão rodando
- [ ] Backend responde em `/health`
- [ ] Elasticsearch está `green`
- [ ] PostgreSQL aceita conexões
- [ ] Frontend carrega em http://localhost:8501
- [ ] Frontend consegue fazer requisições ao Backend
- [ ] Backend consegue buscar no Elasticsearch
- [ ] Backend consegue conectar ao PostgreSQL
- [ ] Fluxo completo funciona (upload → processamento → geração)

---

## 🎯 Testes para Apresentação

Para a apresentação do projeto, demonstre:

1. **Teste de Health Checks**:
   ```bash
   curl http://localhost:8010/health
   curl http://localhost:9200/_cluster/health
   ```

2. **Teste de Interface Gráfica**:
   - Abrir http://localhost:8501
   - Mostrar que a interface carrega

3. **Teste de Comunicação**:
   - Mostrar logs do Backend recebendo requisições
   - Mostrar que o Backend busca no Elasticsearch

4. **Teste de Rede Docker**:
   ```bash
   docker network inspect sdj_network
   ```

---

**Última Atualização**: 02/12/2024

