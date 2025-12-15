"""
Funções utilitárias compartilhadas
"""
import os
import re
from typing import Optional
from datetime import datetime


def decodificar_unicode(texto: str) -> str:
    """
    Decodifica caracteres unicode e limpa o texto da sentença
    """
    if not texto:
        return texto
    
    try:
        # 1. Tenta decodificar unicode
        texto_limpo = texto.encode('latin-1').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        texto_limpo = texto
    
    # 2. Normaliza quebras de linha
    texto_limpo = texto_limpo.replace('\\n', '\n')
    texto_limpo = texto_limpo.replace('\\r', '')
    texto_limpo = texto_limpo.replace('\r\n', '\n')
    texto_limpo = texto_limpo.replace('\r', '\n')
    
    # 3. Remove quebras excessivas mas preserva formatação de parágrafos
    texto_limpo = re.sub(r'\n{3,}', '\n\n', texto_limpo)
    
    # 4. Remove espaços em branco no final das linhas
    linhas = [linha.rstrip() for linha in texto_limpo.split('\n')]
    texto_limpo = '\n'.join(linhas)
    
    return texto_limpo.strip()


def extrair_numero_processo(texto: str) -> Optional[str]:
    """
    Extrai o número do processo do texto do relatório.
    Prioriza o formato CNJ padrão que aparece no cabeçalho do PJe.
    """
    # Processa primeiro as primeiras linhas onde geralmente está o número no PJe
    linhas_iniciais = '\n'.join(texto.split('\n')[:20])  # Primeiras 20 linhas
    
    # Padrões em ordem de prioridade (formato CNJ primeiro)
    padroes = [
        # 1. Formato CNJ padrão do PJe: 0000000-00.0000.0.00.0000
        r'\b\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}\b',
        
        # 2. Formato CNJ com zeros à esquerda: 0000000000-00.0000.0.00.0000  
        r'\b\d{10}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}\b',
        
        # 3. Com texto "Número:" (comum no PJe)
        r'(?:número|n[º°])\s*:?\s*(\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4})',
        
        # 4. Formato antigo
        r'\b\d{4}\.\d{2}\.\d{6}-\d{1}\b',
        
        # 5. Outros padrões com texto
        r'(?:processo|autos)(?:\s+n[º°]?\.?\s*|\s*:?\s*)(\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4})',
    ]
    
    # Primeiro procura nas linhas iniciais
    for i, padrao in enumerate(padroes):
        matches = re.findall(padrao, linhas_iniciais, re.IGNORECASE)
        if matches:
            numero = matches[0] if isinstance(matches[0], str) else matches[0]
            # Valida se é formato CNJ válido
            if re.match(r'\d{7,10}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}', numero):
                return numero
    
    # Se não encontrar nas primeiras linhas, procura no texto completo
    for i, padrao in enumerate(padroes):
        matches = re.findall(padrao, texto, re.IGNORECASE)
        if matches:
            numero = matches[0] if isinstance(matches[0], str) else matches[0]
            if re.match(r'\d{7,10}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}', numero):
                return numero
    
    return None


def gerar_nome_arquivo_sentenca(numero_processo: Optional[str] = None) -> str:
    """
    Gera um nome de arquivo inteligente para a sentença
    """
    if numero_processo:
        # Remove caracteres especiais do número do processo
        numero_limpo = numero_processo.replace('-', '').replace('.', '').replace('/', '')
        return f"sentenca_{numero_limpo}_{datetime.now().strftime('%Y%m%d')}"
    else:
        return f"sentenca_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def gerar_nome_arquivo_referencias(numero_processo: Optional[str] = None) -> str:
    """
    Gera um nome de arquivo inteligente para as referências
    """
    if numero_processo:
        numero_limpo = numero_processo.replace('-', '').replace('.', '').replace('/', '')
        return f"referencias_{numero_limpo}"
    else:
        return f"referencias_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def limpar_arquivo_temporario(path: str) -> None:
    """
    Remove arquivo temporário com tratamento de erro
    """
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        print(f"⚠️ Erro ao remover arquivo temporário {path}: {e}")

