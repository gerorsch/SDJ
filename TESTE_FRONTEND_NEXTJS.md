# Teste do Frontend Next.js + TypeScript

## 🚀 Iniciar o Sistema

```bash
cd SDJ
docker compose up -d
```

## ✅ Verificar Status

```bash
# Verificar se o frontend está rodando
docker compose ps frontend

# Ver logs do frontend
docker compose logs -f frontend
```

## 🌐 Acessar o Frontend

- **URL Local**: http://localhost:3000
- **URL via Nginx**: http://localhost (porta 80)

## 🧪 Testes Manuais

### 1. Teste de Carregamento
- Acesse http://localhost:3000
- Verifique se a página carrega corretamente
- Verifique se o status do sistema aparece na sidebar

### 2. Teste de Upload de PDF
- Clique em "Clique para selecionar um PDF"
- Selecione um arquivo PDF
- Clique em "🔍 Extrair Relatório"
- Aguarde o processamento
- Verifique se o relatório é exibido

### 3. Teste de Geração de Sentença
- Após extrair o relatório
- Preencha os campos opcionais (instruções, referências)
- Configure Top K e Rerank Top K
- Clique em "⚖️ Gerar Sentença"
- Aguarde o processamento
- Verifique se a sentença é exibida

### 4. Teste de Download
- Após gerar relatório ou sentença
- Clique em "📥 Baixar"
- Verifique se o arquivo é baixado

## 🔍 Verificar Comunicação com Backend

```bash
# Testar health check
curl http://localhost:8010/health

# Verificar se o frontend consegue acessar a API
# (verificar logs do frontend)
docker compose logs frontend | grep -i "api\|error"
```

## 🐛 Troubleshooting

### Frontend não inicia
```bash
# Rebuild do container
docker compose build frontend
docker compose up -d frontend

# Ver logs detalhados
docker compose logs frontend
```

### Erro de conexão com API
- Verifique se o backend está rodando: `docker compose ps fastapi`
- Verifique a variável `NEXT_PUBLIC_API_URL` no docker-compose.yml
- Teste a API diretamente: `curl http://localhost:8010/health`

### Erro de build
```bash
# Limpar cache e rebuild
docker compose down
docker compose build --no-cache frontend
docker compose up -d
```

## 📊 Checklist de Funcionalidades

- [ ] Página inicial carrega
- [ ] Status do sistema aparece
- [ ] Upload de PDF funciona
- [ ] Extração de relatório funciona
- [ ] Visualização de relatório funciona
- [ ] Download de relatório funciona
- [ ] Geração de sentença funciona
- [ ] Visualização de sentença funciona
- [ ] Download de sentença funciona
- [ ] Sidebar com instruções aparece
- [ ] Comunicação com backend funciona

## 🎯 Linguagens Utilizadas

✅ **Python**: Backend (FastAPI)  
✅ **TypeScript**: Frontend (Next.js)

**Requisito atendido**: Sistema usa pelo menos 2 linguagens diferentes!

---

**Data**: 02/12/2024  
**Versão**: 1.0

