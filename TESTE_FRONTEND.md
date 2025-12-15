# Guia de Teste do Frontend - SDJ

## 🚀 Como Acessar o Frontend

### 1. Acesso via Navegador

Abra o navegador e acesse:

```
http://localhost:8501
```

Ou via Nginx (se configurado):

```
http://localhost:80
```

---

## ✅ Verificações Básicas

### Teste 1: Interface Carrega

1. Abra http://localhost:8501
2. Você deve ver a interface do Streamlit com:
   - Título: "⚖️ Justino — Assessor Digital"
   - Seção 1: "Extração do Relatório"
   - Seção 2: "Geração da Sentença"
   - Barra lateral com instruções

### Teste 2: Verificar Status do Sistema

Na barra lateral, deve aparecer:
- **🟢 Sistema Online** (se o backend estiver funcionando)

---

## 🧪 Testes Funcionais

### Teste 1: Upload de PDF

1. Na seção "1. Extração do Relatório"
2. Clique em "📎 Envie um processo em PDF"
3. Selecione um arquivo PDF
4. Clique em "🔍 Extrair Relatório"
5. **Resultado esperado**: 
   - Barra de progresso aparece
   - Relatório é extraído e exibido
   - Botão de download aparece

### Teste 2: Visualização do Relatório

Após extrair o relatório:

1. Expanda "📄 Visualizar Relatório Extraído"
2. **Resultado esperado**:
   - Texto do relatório é exibido
   - Número do processo é identificado (se presente)
   - Tamanho do relatório é mostrado

### Teste 3: Download do Relatório

1. Após extrair o relatório
2. Clique em "📥 Baixar Relatório (.docx)"
3. **Resultado esperado**:
   - Arquivo DOCX é baixado
   - Nome do arquivo contém número do processo (se identificado)

### Teste 4: Geração de Sentença

1. Após extrair o relatório
2. Na seção "2. Geração da Sentença"
3. Configure:
   - **Instruções Adicionais** (opcional): "Enfatizar danos morais"
   - **Top K**: 10
   - **Rerank Top K**: 5
4. Clique em "⚖️ Gerar Sentença"
5. **Resultado esperado**:
   - Barra de progresso aparece
   - Sentença é gerada e exibida
   - Botões de download aparecem

### Teste 5: Download da Sentença

1. Após gerar a sentença
2. Clique em "📥 Baixar Sentença (.docx)"
3. **Resultado esperado**:
   - Arquivo DOCX é baixado
   - Nome do arquivo contém número do processo

### Teste 6: Download de Referências

1. Após gerar a sentença
2. Clique em "📥 Baixar Referências (.zip)"
3. **Resultado esperado**:
   - Arquivo ZIP é baixado
   - Contém documentos de referência usados

---

## 🔍 Testes de Comunicação Frontend → Backend

### Teste 1: Verificar Requisições HTTP

Abra o **Console do Navegador** (F12 → Console) e observe:

1. Ao fazer upload de PDF, deve aparecer requisições para:
   - `http://localhost:8010/processar` ou
   - `http://localhost:8010/stream/processar`

2. Ao gerar sentença, deve aparecer requisições para:
   - `http://localhost:8010/gerar-sentenca` ou
   - `http://localhost:8010/stream/gerar-sentenca`

### Teste 2: Verificar Respostas da API

No Console do Navegador (F12 → Network):

1. Filtre por "XHR" ou "Fetch"
2. Faça uma ação (upload ou gerar sentença)
3. Clique na requisição
4. Verifique:
   - **Status**: 200 (sucesso)
   - **Response**: JSON com dados esperados

### Teste 3: Verificar Erros

Se algo falhar:

1. Abra o Console (F12 → Console)
2. Procure por erros em vermelho
3. Verifique a aba Network para requisições com status de erro

---

## 🐛 Troubleshooting do Frontend

### Problema: Interface não carrega

```bash
# Verificar se o container está rodando
docker compose ps streamlit

# Verificar logs
docker compose logs streamlit

# Reiniciar
docker compose restart streamlit
```

### Problema: Erro ao fazer upload

1. Verifique se o backend está funcionando:
   ```bash
   curl http://localhost:8010/health
   ```

2. Verifique os logs do backend:
   ```bash
   docker compose logs fastapi | tail -20
   ```

3. Verifique os logs do frontend:
   ```bash
   docker compose logs streamlit | tail -20
   ```

### Problema: Sentença não é gerada

1. Verifique se há chaves de API configuradas:
   ```bash
   docker compose exec streamlit env | grep API_KEY
   ```

2. Verifique se o Elasticsearch está funcionando:
   ```bash
   curl http://localhost:9200/_cluster/health
   ```

3. Verifique os logs do backend durante a geração:
   ```bash
   docker compose logs -f fastapi
   ```

### Problema: Timeout nas requisições

1. Aumente o timeout no código (se necessário)
2. Verifique se o backend está processando:
   ```bash
   docker compose logs fastapi | grep -i "process\|error"
   ```

---

## 📊 Testes Automatizados (via Terminal)

### Teste 1: Verificar se a página carrega

```bash
curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost:8501
```

**Esperado**: `Status: 200`

### Teste 2: Verificar conteúdo HTML

```bash
curl -s http://localhost:8501 | grep -i "justino\|assessor" | head -5
```

**Esperado**: Deve encontrar o título da aplicação

### Teste 3: Verificar variável de ambiente API_URL

```bash
docker compose exec streamlit env | grep API_URL
```

**Esperado**: `API_URL=http://fastapi:8001`

---

## 🎯 Checklist de Testes do Frontend

- [ ] Interface carrega em http://localhost:8501
- [ ] Barra lateral mostra "Sistema Online"
- [ ] Upload de PDF funciona
- [ ] Relatório é extraído e exibido
- [ ] Download do relatório funciona
- [ ] Geração de sentença funciona
- [ ] Sentença é exibida corretamente
- [ ] Download da sentença funciona
- [ ] Download de referências funciona
- [ ] Requisições HTTP aparecem no console do navegador
- [ ] Não há erros no console do navegador
- [ ] Mensagens de erro são exibidas adequadamente (se houver)

---

## 🎬 Para a Apresentação

### O que mostrar:

1. **Interface Gráfica**:
   - Mostrar a tela inicial
   - Mostrar as duas seções principais
   - Mostrar a barra lateral com instruções

2. **Fluxo Completo**:
   - Upload de PDF
   - Extração de relatório
   - Geração de sentença
   - Download dos resultados

3. **Comunicação**:
   - Abrir Console do Navegador (F12)
   - Mostrar requisições HTTP sendo feitas
   - Mostrar respostas da API

4. **Código**:
   - Mostrar `frontend/streamlit_app.py`
   - Destacar como faz requisições HTTP
   - Mostrar como exibe resultados

---

## 📝 Notas Importantes

- O frontend usa **Streamlit**, que recarrega automaticamente ao salvar arquivos
- As requisições são feitas para `API_URL` (configurado via variável de ambiente)
- O frontend se comunica com o backend via **HTTP REST API**
- Erros são exibidos na interface e também podem ser vistos no console do navegador

---

**Última Atualização**: 02/12/2024

