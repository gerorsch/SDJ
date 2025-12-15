# Frontend SDJ - Next.js + TypeScript

Frontend do Sistema Distribuído Jurídico desenvolvido em **Next.js 14** com **TypeScript**.

## 🚀 Tecnologias

- **Next.js 14**: Framework React com SSR
- **TypeScript**: Tipagem estática
- **React 18**: Biblioteca UI
- **Axios**: Cliente HTTP
- **File Saver**: Download de arquivos

## 📁 Estrutura

```
frontend-next/
├── app/
│   ├── layout.tsx          # Layout principal
│   ├── page.tsx            # Página inicial
│   └── globals.css         # Estilos globais
├── components/
│   ├── Sidebar.tsx         # Barra lateral
│   ├── FileUpload.tsx      # Upload de PDF
│   ├── ReportViewer.tsx    # Visualização de relatório
│   ├── SentenceGenerator.tsx # Geração de sentença
│   └── SentenceViewer.tsx # Visualização de sentença
├── Dockerfile              # Container Docker
├── package.json            # Dependências
└── tsconfig.json          # Configuração TypeScript
```

## 🏃 Executar Localmente

```bash
# Instalar dependências
npm install

# Executar em desenvolvimento
npm run dev

# Acessar
# http://localhost:3000
```

## 🐳 Executar com Docker

```bash
# Build e start
docker compose up -d frontend

# Acessar
# http://localhost:3000
```

## 🔧 Variáveis de Ambiente

```bash
NEXT_PUBLIC_API_URL=http://localhost:8010
```

## 📝 Funcionalidades

- ✅ Upload de PDF
- ✅ Extração de relatório
- ✅ Visualização de relatório
- ✅ Download de relatório
- ✅ Geração de sentença
- ✅ Visualização de sentença
- ✅ Download de sentença
- ✅ Status do sistema
- ✅ Interface responsiva

## 🎨 Componentes Principais

### FileUpload
Componente para upload de arquivos PDF com validação e feedback visual.

### ReportViewer
Exibe o relatório extraído com opções de visualização e download.

### SentenceGenerator
Formulário para configurar parâmetros e gerar sentença.

### SentenceViewer
Exibe a sentença gerada com opções de download.

### Sidebar
Barra lateral com instruções e status do sistema.

## 🔄 Comunicação com Backend

O frontend se comunica com o backend FastAPI através de:

- `POST /processar` - Processa PDF
- `POST /gerar-sentenca` - Gera sentença
- `GET /health` - Health check

## 📦 Build para Produção

```bash
npm run build
npm start
```

---

**Módulo**: Frontend (Next.js + TypeScript) - Módulo 1 do Sistema Distribuído

