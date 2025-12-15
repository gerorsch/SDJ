# Migração do Frontend: Streamlit → Next.js + TypeScript

## 📋 Resumo da Mudança

O frontend foi migrado de **Python/Streamlit** para **Next.js + TypeScript** para atender ao requisito do projeto de usar **pelo menos 2 linguagens diferentes**.

## 🎯 Motivação

- ✅ **Requisito do Projeto**: Sistema distribuído deve usar pelo menos 2 linguagens diferentes
- ✅ **Linguagens Utilizadas**:
  - **Python**: Backend (FastAPI)
  - **TypeScript**: Frontend (Next.js)
- ✅ **Tecnologias Modernas**: Next.js oferece melhor performance e experiência de desenvolvimento

## 📁 Estrutura Antiga vs Nova

### Antiga (Streamlit)
```
frontend/
├── streamlit_app.py
├── auth_tjpe.py
├── requirements.txt
└── Dockerfile
```

### Nova (Next.js + TypeScript)
```
frontend-next/
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   └── globals.css
├── components/
│   ├── Sidebar.tsx
│   ├── FileUpload.tsx
│   ├── ReportViewer.tsx
│   ├── SentenceGenerator.tsx
│   └── SentenceViewer.tsx
├── package.json
├── tsconfig.json
├── next.config.js
└── Dockerfile
```

## 🔄 Funcionalidades Mantidas

Todas as funcionalidades do frontend Streamlit foram preservadas:

- ✅ Upload de PDF
- ✅ Extração de relatório
- ✅ Visualização de relatório
- ✅ Download de relatório
- ✅ Geração de sentença
- ✅ Visualização de sentença
- ✅ Download de sentença
- ✅ Status do sistema
- ✅ Barra lateral com instruções

## 🚀 Como Usar

### Desenvolvimento Local

```bash
cd frontend-next
npm install
npm run dev
# Acessar: http://localhost:3000
```

### Docker

```bash
# Build e start
docker compose up -d frontend

# Acessar
# http://localhost:3000
```

## 🔧 Configurações Atualizadas

### docker-compose.yml
- Serviço `streamlit` → `frontend`
- Porta `8501` → `3000`
- Container `rag_app` → `sdj_frontend`

### nginx.conf
- Upstream `streamlit_backend` → `frontend_nextjs`
- Rotas atualizadas para Next.js
- WebSocket configurado para HMR

## 📝 Notas Importantes

1. **Autenticação**: A autenticação do Streamlit (`auth_tjpe.py`) não foi migrada inicialmente. Pode ser implementada posteriormente se necessário.

2. **Compatibilidade**: O backend FastAPI permanece inalterado. A comunicação via HTTP REST API continua funcionando normalmente.

3. **Variáveis de Ambiente**: 
   - `NEXT_PUBLIC_API_URL`: URL do backend FastAPI
   - Padrão: `http://localhost:8010`

## ✅ Benefícios da Migração

- ✅ **Múltiplas Linguagens**: Atende requisito do projeto (Python + TypeScript)
- ✅ **Performance**: Next.js oferece melhor performance com SSR/SSG
- ✅ **Tipagem**: TypeScript adiciona segurança de tipos
- ✅ **Modernidade**: Stack moderna e amplamente utilizada
- ✅ **Manutenibilidade**: Código mais organizado e escalável

## 🔄 Próximos Passos (Opcional)

- [ ] Implementar autenticação no frontend Next.js
- [ ] Adicionar testes unitários e de integração
- [ ] Melhorar tratamento de erros
- [ ] Adicionar loading states mais sofisticados
- [ ] Implementar cache de requisições

---

**Data da Migração**: 02/12/2024  
**Versão**: 1.0

