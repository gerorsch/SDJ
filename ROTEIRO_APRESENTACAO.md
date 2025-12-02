# Roteiro para Apresentação do Vídeo

## 📹 Roteiro para Gravação do Vídeo

**Duração sugerida**: 10-15 minutos

---

## 1. Introdução (1-2 min)

### O que falar:
- "Este é o projeto SDJ, um sistema distribuído desenvolvido para a disciplina de Sistemas Distribuídos"
- "O sistema processa documentos jurídicos e gera sentenças automaticamente usando Inteligência Artificial"

### O que mostrar:
- Tela inicial do projeto
- README.md aberto

---

## 2. Arquitetura do Sistema (2-3 min)

### O que falar:
- "O sistema é composto por 5 módulos distribuídos, cada um rodando em um container Docker independente"
- "Cada módulo é um processo separado que se comunica com os outros via rede"

### O que mostrar:
- Arquivo `ARQUITETURA.md` ou diagrama
- Arquivo `docker-compose.yml`
- Explicar cada módulo:
  1. **Frontend (Streamlit)** - Interface gráfica
  2. **Backend (FastAPI)** - Processamento e API
  3. **Elasticsearch** - Busca semântica
  4. **PostgreSQL** - Banco de dados
  5. **Nginx** - Proxy reverso

### Código a mostrar:
```yaml
# docker-compose.yml - Mostrar os 5 serviços
```

---

## 3. Demonstração da Interface Gráfica (2-3 min)

### O que falar:
- "A interface gráfica permite que o usuário acesse todas as funcionalidades do sistema"
- "Vou demonstrar o fluxo completo de uso"

### O que mostrar:
1. Abrir http://localhost:8501 no navegador
2. Mostrar a interface do Streamlit
3. Fazer upload de um PDF de teste
4. Clicar em "Extrair Relatório"
5. Mostrar o relatório extraído
6. Configurar parâmetros e gerar sentença
7. Mostrar a sentença gerada

### Código a mostrar:
- `frontend/streamlit_app.py` - Mostrar estrutura básica

---

## 4. Comunicação entre Componentes (2-3 min)

### O que falar:
- "Vou demonstrar como os módulos se comunicam"
- "O frontend faz requisições HTTP para o backend"
- "O backend se comunica com o Elasticsearch para buscar documentos similares"

### O que mostrar:

#### 4.1. Frontend → Backend
```bash
# Mostrar no terminal
curl http://localhost:8010/health
```

Mostrar no código:
- `frontend/streamlit_app.py` - Linha onde faz requisição HTTP
- `backend/main.py` - Endpoint `/health`

#### 4.2. Backend → Elasticsearch
```bash
# Mostrar no terminal
curl http://localhost:9200/_cluster/health
```

Mostrar no código:
- `backend/services/retrieval_rerank.py` - Como busca no Elasticsearch

#### 4.3. Executar script de verificação
```bash
./verificar_sistema.sh
```

---

## 5. Código Fonte - Módulos Principais (3-4 min)

### O que falar:
- "Vou mostrar os principais arquivos de código de cada módulo"

### O que mostrar:

#### 5.1. Backend (FastAPI)
- Arquivo: `backend/main.py`
- Mostrar:
  - Endpoints principais (`/processar`, `/gerar-sentenca`)
  - Como recebe requisições HTTP
  - Como se comunica com Elasticsearch

```python
# Mostrar exemplo de endpoint
@app.post("/processar")
async def processar_pdf(pdf: UploadFile = File(...)):
    # Processa PDF
    # Retorna relatório
```

#### 5.2. Frontend (Streamlit)
- Arquivo: `frontend/streamlit_app.py`
- Mostrar:
  - Como faz upload de arquivo
  - Como chama a API do backend
  - Como exibe resultados

```python
# Mostrar exemplo de chamada HTTP
response = requests.post(f"{API_URL}/processar", files=files)
```

#### 5.3. Elasticsearch
- Arquivo: `backend/services/retrieval_rerank.py`
- Mostrar:
  - Como busca documentos similares
  - Como usa embeddings para busca semântica

---

## 6. Distribuição e Containers (1-2 min)

### O que falar:
- "Todos os módulos rodam em containers Docker isolados"
- "Cada container é um processo independente"

### O que mostrar:
```bash
# Mostrar containers rodando
docker-compose ps

# Mostrar logs de um módulo
docker-compose logs fastapi
```

### Código a mostrar:
- `docker-compose.yml` - Mostrar configuração dos containers
- Explicar rede Docker (`network: network`)

---

## 7. Repositório Git (1 min)

### O que falar:
- "O código está versionado no Git desde o início do projeto"
- "Todo o histórico de commits está disponível"

### O que mostrar:
- Abrir repositório Git (GitHub/GitLab)
- Mostrar histórico de commits
- Mostrar estrutura de pastas

---

## 8. Conclusão (1 min)

### O que falar:
- "O sistema atende todos os requisitos do projeto:"
  - ✅ Sistema distribuído com 5 módulos
  - ✅ Interface gráfica completa
  - ✅ Comunicação via rede entre módulos
  - ✅ Containerização com Docker
  - ✅ Repositório Git com histórico

### O que mostrar:
- Resumo visual dos módulos
- Diagrama de arquitetura final

---

## 📝 Checklist Antes de Gravar

- [ ] Todos os containers estão rodando (`docker-compose ps`)
- [ ] Sistema está funcionando (`./verificar_sistema.sh`)
- [ ] Tem um PDF de teste para demonstrar
- [ ] Código está organizado e comentado
- [ ] README.md está atualizado
- [ ] Repositório Git está atualizado

---

## 🎬 Dicas para Gravação

1. **Use uma ferramenta de gravação de tela** (OBS, ShareX, etc.)
2. **Fale claramente** e em ritmo moderado
3. **Mostre o código** enquanto explica
4. **Demonstre o funcionamento** em tempo real
5. **Use zoom** para destacar partes importantes do código
6. **Edite o vídeo** para remover pausas longas

---

## 📋 Pontos a Destacar

### Complexidade:
- Sistema com múltiplos módulos
- Integração com APIs externas (LLM)
- Busca semântica (RAG)

### Corretude:
- Todos os módulos funcionando
- Comunicação entre componentes testada
- Tratamento de erros implementado

### Completude:
- Interface gráfica completa
- Todos os endpoints funcionando
- Documentação completa

### Criatividade:
- Uso de IA para geração de sentenças
- Busca semântica para encontrar referências
- Arquitetura modular e escalável

---

**Boa sorte com a apresentação! 🚀**

