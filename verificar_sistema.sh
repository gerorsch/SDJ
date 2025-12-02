#!/bin/bash

# Script de Verificação do Sistema Distribuído
# Verifica se todos os módulos estão funcionando corretamente

echo "=========================================="
echo "  Verificação do Sistema Distribuído"
echo "  SDJ - 02/12/2024"
echo "=========================================="
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Contador de sucessos e falhas
SUCCESS=0
FAIL=0

# Função para testar endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo -n "Testando $name... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    
    if [ "$response" == "$expected_status" ]; then
        echo -e "${GREEN}✓ OK${NC} (Status: $response)"
        ((SUCCESS++))
        return 0
    else
        echo -e "${RED}✗ FALHOU${NC} (Status: $response, esperado: $expected_status)"
        ((FAIL++))
        return 1
    fi
}

# Função para verificar container
check_container() {
    local name=$1
    
    echo -n "Verificando container $name... "
    
    if docker ps --format '{{.Names}}' | grep -q "^${name}$"; then
        echo -e "${GREEN}✓ RODANDO${NC}"
        ((SUCCESS++))
        return 0
    else
        echo -e "${RED}✗ PARADO${NC}"
        ((FAIL++))
        return 1
    fi
}

echo "1. Verificando Containers Docker"
echo "--------------------------------"
check_container "rag_postgres"
check_container "rag_elasticsearch"
check_container "rag_api"
check_container "rag_app"
check_container "rag_proxy"
echo ""

echo "2. Verificando Comunicação entre Módulos"
echo "----------------------------------------"

# Backend Health Check
test_endpoint "Backend API (Health)" "http://localhost:8010/health"

# Elasticsearch Health Check
test_endpoint "Elasticsearch" "http://localhost:9200/_cluster/health"

# Frontend (Streamlit)
test_endpoint "Frontend (Streamlit)" "http://localhost:8501" 200

# Nginx
test_endpoint "Nginx (Proxy)" "http://localhost:80" 200

echo ""

echo "3. Verificando Variáveis de Ambiente"
echo "--------------------------------------"
if [ -f ".env" ]; then
    echo -e "${GREEN}✓ Arquivo .env encontrado${NC}"
    ((SUCCESS++))
    
    # Verifica se tem pelo menos uma chave de API
    if grep -q "OPENAI_API_KEY\|ANTHROPIC_API_KEY" .env; then
        echo -e "${GREEN}✓ Chave de API configurada${NC}"
        ((SUCCESS++))
    else
        echo -e "${YELLOW}⚠ Nenhuma chave de API encontrada no .env${NC}"
        ((FAIL++))
    fi
else
    echo -e "${RED}✗ Arquivo .env não encontrado${NC}"
    ((FAIL++))
fi
echo ""

echo "4. Resumo"
echo "--------"
echo -e "Sucessos: ${GREEN}$SUCCESS${NC}"
echo -e "Falhas: ${RED}$FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ Sistema está funcionando corretamente!${NC}"
    exit 0
else
    echo -e "${RED}✗ Alguns componentes não estão funcionando. Verifique os logs:${NC}"
    echo "   docker-compose logs"
    exit 1
fi

