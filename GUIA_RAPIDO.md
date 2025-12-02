# Guia Rápido - Execução do Sistema

## 🚀 Início Rápido

### 1. Configuração Inicial

```bash
# Clone o repositório (se ainda não tiver)
cd SDJ

# Crie o arquivo .env (copie de .env.example se existir)
# Configure as variáveis:
# - OPENAI_API_KEY ou ANTHROPIC_API_KEY
# - Outras variáveis conforme necessário
```

### 2. Iniciar o Sistema

```bash
# Inicia todos os módulos em background
docker-compose up -d

# Aguarde alguns segundos para os serviços iniciarem
# Verifique os logs:
docker-compose logs -f
```

### 3. Acessar a Interface

Abra o navegador em: **http://localhost:8501**

---

## ✅ Verificação Rápida

### Verificar se todos os módulos estão rodando:

```bash
docker-compose ps
```

Você deve ver 5 containers:
- `rag_postgres` (PostgreSQL)
- `rag_elasticsearch` (Elasticsearch)
- `rag_api` (FastAPI Backend)
- `rag_app` (Streamlit Frontend)
- `rag_proxy` (Nginx)

### Testar Comunicação entre Módulos:

```bash
# 1. Teste Backend
curl http://localhost:8010/health

# 2. Teste Elasticsearch
curl http://localhost:9200/_cluster/health

# 3. Teste Frontend (abra no navegador)
# http://localhost:8501
```

---

## 📋 Fluxo de Uso Básico

1. **Acesse a Interface**: http://localhost:8501
2. **Faça Login** (se autenticação estiver habilitada)
3. **Upload de PDF**: 
   - Clique em "Envie um processo em PDF"
   - Selecione um arquivo PDF
   - Clique em "Extrair Relatório"
4. **Aguarde Processamento**: O sistema extrairá o relatório
5. **Gere Sentença**:
   - Configure parâmetros (Top K, Rerank Top K)
   - Adicione instruções opcionais
   - Clique em "Gerar Sentença"
6. **Baixe Resultados**: 
   - Sentença em DOCX
   - Referências em ZIP

---

## 🔧 Comandos Úteis

### Parar o Sistema

```bash
docker-compose down
```

### Reiniciar um Módulo Específico

```bash
# Reiniciar apenas o backend
docker-compose restart fastapi

# Reiniciar apenas o frontend
docker-compose restart streamlit
```

### Ver Logs de um Módulo

```bash
# Logs do backend
docker-compose logs -f fastapi

# Logs do frontend
docker-compose logs -f streamlit

# Logs de todos
docker-compose logs -f
```

### Reconstruir Containers (após mudanças no código)

```bash
# Reconstruir e reiniciar
docker-compose up -d --build
```

### Limpar Tudo (volumes e containers)

```bash
# CUIDADO: Remove todos os dados
docker-compose down -v
```

---

## 🐛 Solução de Problemas

### Problema: Containers não iniciam

```bash
# Verifique os logs
docker-compose logs

# Verifique se as portas estão livres
netstat -tulpn | grep -E '8501|8010|9200|5432|80'
```

### Problema: Backend não responde

```bash
# Verifique se o container está rodando
docker ps | grep rag_api

# Verifique os logs
docker-compose logs fastapi

# Teste o health check
curl http://localhost:8010/health
```

### Problema: Elasticsearch não inicia

```bash
# Elasticsearch precisa de memória suficiente
# Verifique se há pelo menos 2GB disponíveis

# Verifique os logs
docker-compose logs elasticsearch

# Tente aumentar a memória no docker-compose.yml
# ES_JAVA_OPTS=-Xms512m -Xmx1g
```

### Problema: Frontend não carrega

```bash
# Verifique se o container está rodando
docker ps | grep rag_app

# Verifique os logs
docker-compose logs streamlit

# Verifique se a variável API_URL está correta
docker-compose exec streamlit env | grep API_URL
```

---

## 📊 Monitoramento

### Status dos Serviços

```bash
# Status geral
docker-compose ps

# Uso de recursos
docker stats
```

### Health Checks

```bash
# Backend
curl http://localhost:8010/health

# Elasticsearch
curl http://localhost:9200/_cluster/health

# PostgreSQL (requer cliente psql)
docker-compose exec postgres pg_isready -U rag_user
```

---

## 🔐 Segurança

- Nunca commite o arquivo `.env` no Git
- Use variáveis de ambiente para credenciais
- Configure CORS adequadamente em produção
- Use HTTPS em produção (configure no Nginx)

---

## 📝 Próximos Passos

Após verificar que tudo está funcionando:

1. Teste o fluxo completo (upload → processamento → geração)
2. Verifique a comunicação entre módulos
3. Prepare a documentação para apresentação
4. Grave o vídeo demonstrando o sistema

---

**Última Atualização**: 02/12/2024

