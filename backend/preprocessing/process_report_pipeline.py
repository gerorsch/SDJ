from __future__ import annotations

import argparse
import os
import re
import sys
import textwrap
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from types import SimpleNamespace
import hashlib
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from dotenv import load_dotenv
load_dotenv()

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseLanguageModel
import anthropic
from pypdf.errors import PdfReadError
from pypdf import PdfReader
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image


# ───────────────────────────────────────── config ──────────────────────────
@dataclass
class Config:
    summary_model: str = os.getenv("SUMMARY_MODEL", "gpt-4o-mini")
    report_model:  str = os.getenv("REPORT_MODEL",  "gpt-5")
    temperature:   float = float(os.getenv("TEMPERATURE", 0.2))
    max_tokens:    int = int(os.getenv("MAX_TOKENS", 4096))
    fallback_chars:int = int(os.getenv("FALLBACK_CHARS", 10000))
    verbose:       bool  = os.getenv("VERBOSE", "false").lower() in ("1","true","yes","t")

def log(msg: str, cfg: Config):
    if cfg.verbose:
        print(msg, file=sys.stderr)
        
# --- NOVO: FUNÇÃO DE TAREFA PARA OCR PARALELO ---
# Esta função precisa ser de "nível superior" para funcionar com ProcessPoolExecutor
def ocr_page_task(task_args: Tuple[bytes, int, str]) -> Tuple[int, str]:
    """
    Executa OCR em uma única página de um PDF.
    Retorna uma tupla com (numero_da_pagina, texto_extraido).
    """
    pdf_bytes, page_number, lang = task_args
    try:
        pil_images = convert_from_bytes(
            pdf_bytes,
            dpi=300,
            first_page=page_number,
            last_page=page_number
        )
        if pil_images:
            text = pytesseract.image_to_string(pil_images[0], lang=lang)
            return (page_number, text)
    except Exception as e:
        print(f"Erro no OCR da página {page_number}: {e}", file=sys.stderr)
    
    return (page_number, "")

# --- NOVO: FUNÇÃO PARA EXTRAIR TEXTO COM OCR PARALELO ---
def extract_text_from_pdf(pdf_path: Path, cfg: Config, on_progress: Optional[Callable[[str], None]] = None) -> List[SimpleNamespace]:
    """
    Carrega o texto de um PDF, aplicando OCR em paralelo nas páginas que forem imagens.
    """
    pages_content = []
    pages_to_ocr = []
    
    try:
        reader = PdfReader(str(pdf_path), strict=False)
        num_pages = len(reader.pages)
        if on_progress: on_progress(f"📄 PDF com {num_pages} páginas detectado. Lendo texto...")

        # Fase 1: Extrai texto direto e identifica páginas para OCR
        for i, page in enumerate(reader.pages):
            try:
                text = page.extract_text() or ""
                if len(text.strip()) < 100:
                    pages_to_ocr.append(i + 1)
                    pages_content.append(SimpleNamespace(page_content=None, metadata={'page': i})) # Placeholder
                else:
                    pages_content.append(SimpleNamespace(page_content=text, metadata={'page': i}))
            except Exception:
                log(f"   – erro extraindo texto da página {i+1}, marcando para OCR.", cfg)
                pages_to_ocr.append(i + 1)
                pages_content.append(SimpleNamespace(page_content=None, metadata={'page': i})) # Placeholder

    except Exception as e:
        log(f"⚠️ Leitura do PDF falhou: {e}. O documento pode estar corrompido.", cfg)
        raise

    # Fase 2: Executa OCR em paralelo, se necessário
    if pages_to_ocr:
        if on_progress: on_progress(f"⚙️ Executando OCR em {len(pages_to_ocr)} páginas em paralelo...")
        pdf_bytes = pdf_path.read_bytes()
        tasks = [(pdf_bytes, page_num, 'por') for page_num in pages_to_ocr]

        with ProcessPoolExecutor() as executor:
            results = executor.map(ocr_page_task, tasks)
            
            for page_num, ocr_text in results:
                # O índice na lista é page_num - 1
                pages_content[page_num - 1].page_content = ocr_text

    # Garante que nenhum conteúdo de página seja None
    for page in pages_content:
        if page.page_content is None:
            page.page_content = ""

    return pages_content

# ────────────────────────────── detectar peça ─────────────────────────────
PIECE_KWS: Dict[str, list[str]] = {
    "peticao_inicial": ["petição inicial", "peticao inicial"],
    "contestacao":     ["contestação", "contestacao"],
    "decisao":         ["decisão", "decisao"],
    "despacho":        ["despacho"],
    "sentenca":        ["sentença", "sentenca"],
    "replica":         ["réplica", "replica"],
}

def classify_page(txt: str) -> str:
    low = txt.lower()
    for lab, kws in PIECE_KWS.items():
        if any(kw in low for kw in kws):
            return lab
    return "outros"

def extract_process_number(first_page_text: str) -> Optional[str]:
    """
    Extrai o número do processo da primeira página do PDF
    """
    if not first_page_text:
        return None
    
    # Padrões de número de processo (ordem de prioridade)
    patterns = [
        # Formato CNJ padrão: 0000000-00.0000.0.00.0000
        r'\b\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}\b',
        
        # Formato CNJ com mais dígitos: 0000000000-00.0000.0.00.0000
        r'\b\d{10}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}\b',
        
        # Formato antigo: 0000.00.000000-0
        r'\b\d{4}\.\d{2}\.\d{6}-\d{1}\b',
        
        # Padrões com texto: "Número: 0000000-00.0000.0.00.0000"
        r'(?:número|processo|autos)(?:\s*:?\s*|\s+n[º°]?\.?\s*)(\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4})',
        
        # Padrões com texto mais genéricos
        r'(?:processo|autos)(?:\s+n[º°]?\.?\s*|\s+)(\d+[-\.\d]+)',
        
        # Padrão específico do PJe: "Processo Eletrônico nº ..."
        r'processo\s+eletr[ôo]nico\s+n[º°]?\s*(\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4})',
    ]
    
    text_lower = first_page_text.lower()
    
    for i, pattern in enumerate(patterns):
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        if matches:
            # Para padrões com grupo de captura, pega o grupo
            if i >= 3:  # Padrões com grupos de captura
                number = matches[0] if isinstance(matches[0], str) else matches[0]
            else:  # Padrões diretos
                number = matches[0]
            
            # Validação adicional para formato CNJ
            if re.match(r'\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}', number):
                return number
            elif re.match(r'\d{10}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}', number):
                return number
            elif len(number) > 10:  # Outros formatos longos
                return number
    
    return None


def extract_id_from_text(text: str) -> Optional[str]:
    """
    Procura padrões de ID no rodapé:
     - “ID 12345” ou “ID: 12345”
     - “Num. 12345” ou “Núm. 12345”
    """
    patterns = [
        r"\bID\s*[:\-]?\s*(\d+)\b",
        r"(?:Num\.|Núm\.)\s*(\d+)"
    ]
    for pat in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            return m.group(1)
    return None


def group_pages(pages: List, cfg: Config) -> tuple[Dict[str, List[str]], Optional[str]]:
    """
    Agrupa páginas por tipo de peça e extrai número do processo da primeira página
    """
    groups: Dict[str, List[str]] = {}
    cur: Optional[str] = None
    buf: List[str] = []
    process_number = None
    # mapa de label -> ID capturado do rodapé
    section_id_map: Dict[str,str] = {}
    
    for i, p in enumerate(pages):
        # Extrai número do processo da primeira página
        if i == 0:
            process_number = extract_process_number(p.page_content)
            if process_number:
                log(f"📋 Número do processo identificado: {process_number}", cfg)
            else:
                log("⚠️ Número do processo não encontrado na primeira página", cfg)
        
        lab = classify_page(p.page_content)
        if lab != cur:
            if buf:
                groups.setdefault(cur or "outros", []).append("\n".join(buf))
                buf = []
                # novo bloco: captura ID no início da seção
            page_id = extract_id_from_text(p.page_content)
            if page_id:
                section_id_map[lab] = page_id
            cur = lab
            log(f"→ nova peça '{lab}' na página {i+1}", cfg)
        buf.append(p.page_content)
    
    if buf:
        groups.setdefault(cur or "outros", []).append("\n".join(buf))
    
    return groups, process_number, section_id_map

# ─────────────────────────────── prompts ──────────────────────────────────
SUMMARY_PT = PromptTemplate(
    template=textwrap.dedent("""
        Leia o texto e liste **cada ato processual relevante** já no formato:
        – frase concisa (ID 123456789).
        Não inclua títulos como "Petição Inicial".
        Texto:
        {texto}
    """),
    input_variables=["texto"],
)

# Prompt modificado para incluir número do processo
INSTRUCOES_COM_PROCESSO = textwrap.dedent("""
    TAREFA
    Elabore um relatório analítico e detalhado do processo judicial fornecido, com base nos documentos constantes dos autos. Utilize estilo direto, informando de maneira objetiva o conteúdo de cada ato processual relevante, com a respectiva identificação por ID.

    NÚMERO DO PROCESSO
    O processo tem o número: {numero_processo}

    INSTRUÇÕES ESPECÍFICAS
    - Inicie o relatório com "Processo nº {numero_processo}"
    - Não inclua os títulos formais das peças (ex: "Petição Inicial", "Despacho", "Decisão", etc.).
    - Cada parágrafo gerado deve terminar com “(ID <número>)”;
    - Use exatamente o número que aparece no rodapé.
    - Identifique os atos com uma frase introdutória direta e o número do ID entre parênteses, como nos exemplos abaixo:
      - Foi concedida a justiça gratuita e deferida a tutela de urgência (ID ___).
      - Réplica apresentada (ID ___).
    - Ao tratar de manifestações das partes (petições), explique brevemente seu conteúdo jurídico.
    - Na contestação, redija um parágrafo mais desenvolvido, contendo:
      - Os principais fatos narrados;
      - Os fundamentos jurídicos alegados;
      - O pedido final;
      - E se foram juntados documentos e procurações.
    - A Réplica deve ser indicada apenas com a frase: "Réplica no ID ___.", sem síntese adicional.
    - Inclua todas as petições, exceto as de habilitação de advogado.
    - Ignore todas as certidões, exceto:
      - Certidões de citação positiva;
      - Certidões de decurso de prazo (ex: "decorrido o prazo sem manifestação").

    MODELO DE FORMATAÇÃO DO RELATÓRIO
    Processo nº {numero_processo}
    
    Vistos, etc.
    NOME DO AUTOR, qualificado na inicial, por intermédio de advogado legalmente habilitado por instrumento de mandado, propôs AÇÃO EM ITÁLICO contra NOME DO RÉU, também qualificado, com o objetivo de sintetizar o pedido da ação em minúsculas.
    A parte autora alegou que [...] (ID: ___).
    Foi deferida a gratuidade judiciária (ID: ___).
    Tutela de urgência concedida [...] (ID: ___).
    Contestação apresentada (ID: ___), na qual a parte ré [...]
    Réplica no ID ___.
    Manifestação da parte autora [...] (ID ___).
    Decurso de prazo certificado (ID ___).
    [Outros atos relevantes, em sequência cronológica].
""")

INSTRUCOES_SEM_PROCESSO = textwrap.dedent("""
    TAREFA
    Elabore um relatório analítico e detalhado do processo judicial fornecido, com base nos documentos constantes dos autos. Utilize estilo direto, informando de maneira objetiva o conteúdo de cada ato processual relevante, com a respectiva identificação por ID.

    INSTRUÇÕES ESPECÍFICAS
    - Não inclua os títulos formais das peças (ex: "Petição Inicial", "Despacho", "Decisão", etc.).
    - Cada parágrafo gerado deve terminar com “(ID <número>)”;
    - Use exatamente o número que aparece no rodapé.
    - Identifique os atos com uma frase introdutória direta e o número do ID entre parênteses, como nos exemplos abaixo:
      - Foi concedida a justiça gratuita e deferida a tutela de urgência (ID ___).
      - Réplica apresentada (ID ___).
    - Ao tratar de manifestações das partes (petições), explique brevemente seu conteúdo jurídico.
    - Na contestação, redija um parágrafo mais desenvolvido, contendo:
      - Os principais fatos narrados;
      - Os fundamentos jurídicos alegados;
      - O pedido final;
      - E se foram juntados documentos e procurações.
    - A Réplica deve ser indicada apenas com a frase: "Réplica no ID ___.", sem síntese adicional.
    - Inclua todas as petições, exceto as de habilitação de advogado.
    - Ignore todas as certidões, exceto:
      - Certidões de citação positiva;
      - Certidões de decurso de prazo (ex: "decorrido o prazo sem manifestação").

    MODELO DE FORMATAÇÃO DO RELATÓRIO
    Vistos, etc.
    NOME DO AUTOR, qualificado na inicial, por intermédio de advogado legalmente habilitado por instrumento de mandado, propôs AÇÃO EM ITÁLICO contra NOME DO RÉU, também qualificado, com o objetivo de sintetizar o pedido da ação em minúsculas.
    A parte autora alegou que [...] (ID: ___).
    Foi deferida a gratuidade judiciária (ID: ___).
    Tutela de urgência concedida [...] (ID: ___).
    Contestação apresentada (ID: ___), na qual a parte ré [...]
    Réplica no ID ___.
    Manifestação da parte autora [...] (ID ___).
    Decurso de prazo certificado (ID ___).
    [Outros atos relevantes, em sequência cronológica].
""")

REPORT_PT = PromptTemplate(
    template="""{instr}

CONTEÚDO DOS AUTOS:
{linhas_atos}

RELATÓRIO:""",
    input_variables=["instr", "linhas_atos"],
)

# ─────────────────────────── wrapper Claude CORRIGIDO ─────────────────────────────
class AnthropicClaudeWrapper:
    def __init__(self, model: str, max_tokens: int = 4096, temperature: float = 0.2):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = model

        self.max_tokens = max_tokens
        self.temperature = temperature

    def _extract_text_from_response(self, response_content) -> str:
        """
        Extrai o texto da resposta do Claude de forma segura.
        A API do Anthropic retorna response.content como uma lista de TextBlocks.
        """
        if not response_content:
            return ""
        
        if isinstance(response_content, str):
            # Se já é string, retorna diretamente
            return response_content
        
        if isinstance(response_content, list):
            # Se é lista de TextBlocks, extrai o texto de cada um
            text_parts = []
            for block in response_content:
                if hasattr(block, 'text'):
                    # Objeto TextBlock com atributo text
                    text_parts.append(block.text)
                elif isinstance(block, dict) and 'text' in block:
                    # Dicionário com chave text
                    text_parts.append(block['text'])
                elif isinstance(block, str):
                    # String direta
                    text_parts.append(block)
                else:
                    # Fallback: converte para string
                    text_parts.append(str(block))
            
            return ''.join(text_parts)
        
        # Fallback final: converte para string
        return str(response_content)

    def invoke(self, input_data: dict) -> str:
        user_msg = input_data.get("prompt") or (
            input_data["instr"]
            + "\n\nCONTEÚDO DOS AUTOS:\n"
            + input_data["linhas_atos"]
            + "\n\nRELATÓRIO:"
        )
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{"role": "user", "content": user_msg}],
            )
            
            # CORREÇÃO: Extrai o texto corretamente da resposta do Claude
            text = self._extract_text_from_response(response.content)
            return text.strip()
            
        except Exception as e:
            print(f"Erro na chamada da API Anthropic: {e}", file=sys.stderr)
            return f"Erro na geração de conteúdo: {str(e)}"

# ───────────────────────── funções LLM CORRIGIDAS ────────────────────────────────────

def get_llm(model_name: str, cfg: Config) -> BaseLanguageModel:
    """
    Seleciona dinamicamente o cliente LLM (OpenAI ou Anthropic)
    com base no nome do modelo.
    """
    if model_name.startswith("gpt"):
        log(f"Usando modelo OpenAI: {model_name}", cfg)
        try:
            return ChatOpenAI(
                model=model_name,
                temperature=cfg.temperature,
                max_tokens=cfg.max_tokens,
                api_key=os.getenv("OPENAI_API_KEY") # Passando a chave explicitamente
            )
        except Exception as e:
            log(f"Falha ao inicializar ChatOpenAI para o modelo '{model_name}': {e}", cfg)
            # Se falhar (ex: chave inválida), cai no fallback
            pass

    elif model_name.startswith("claude"):
        log(f"Usando modelo Anthropic: {model_name}", cfg)
        return AnthropicClaudeWrapper(
            model=model_name,
            max_tokens=cfg.max_tokens,
            temperature=cfg.temperature
        )

    # Fallback para um modelo padrão se o nome não for reconhecido OU se a inicialização falhar
    log(f"⚠️ Modelo '{model_name}' não encontrado ou falhou ao inicializar. Usando fallback gpt-4o-mini.", cfg)
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens,
        api_key=os.getenv("OPENAI_API_KEY")
    )


def _extract_text_safely(response) -> str:
    """
    Função auxiliar para extrair texto de respostas de LLM de forma segura.
    Funciona tanto para responses do Claude quanto do OpenAI.
    """
    if not response:
        return ""
    
    # Se tem atributo content
    if hasattr(response, "content"):
        content = response.content
        
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            # Lista de TextBlocks (Claude)
            text_parts = []
            for block in content:
                if hasattr(block, 'text'):
                    text_parts.append(block.text)
                elif isinstance(block, dict) and 'text' in block:
                    text_parts.append(block['text'])
                elif isinstance(block, str):
                    text_parts.append(block)
                else:
                    text_parts.append(str(block))
            return ''.join(text_parts)
        else:
            return str(content)
    
    # Se é string direta
    if isinstance(response, str):
        return response
    
    # Fallback final
    return str(response)

# def get_llm(model: str, cfg: Config):
#     use_claude = os.getenv("USE_CLAUDE_FOR_REPORT", "false").lower() in ("1", "true", "yes", "t")
#     if use_claude and model.startswith("claude"):
#         return AnthropicClaudeWrapper(model=model, max_tokens=cfg.max_tokens, temperature=cfg.temperature)
#     else:
#         return ChatOpenAI(model_name=model, temperature=cfg.temperature, max_tokens=cfg.max_tokens)

def summarize(text: str, llm: BaseLanguageModel, cfg: Config) -> str:
    try:
        resp = (SUMMARY_PT | llm).invoke({"texto": text})
        content = _extract_text_safely(resp)
        return content.strip()
    except Exception as e:
        print(f"Erro na função summarize: {e}", file=sys.stderr)
        return f"Documento processado com {len(text)} caracteres."


from typing import Any

def build_report(atos: str, process_number: Optional[str], cfg: Config) -> str:
    try:
        llm = get_llm(cfg.report_model, cfg)

        instructions = (
            INSTRUCOES_COM_PROCESSO.format(numero_processo=process_number)
            if process_number else INSTRUCOES_SEM_PROCESSO
        )
        formatted_prompt = REPORT_PT.format(instr=instructions, linhas_atos=atos)

        # Se for o wrapper do Claude, ele quer {"prompt": ...}; caso contrário, passe string
        if isinstance(llm, AnthropicClaudeWrapper):
            resp = llm.invoke({"prompt": formatted_prompt})
        else:
            # ChatOpenAI (LangChain): aceita string diretamente
            resp = llm.invoke(formatted_prompt)

        content = _extract_text_safely(resp)

        if process_number and not content.strip().startswith(f"Processo nº {process_number}"):
            content = f"Processo nº {process_number}\n\n{content.strip()}"

        return content.strip()

    except Exception as e:
        print(f"Erro na função build_report: {e}", file=sys.stderr)
        if process_number:
            return (f"Processo nº {process_number}\n\n"
                    f"Relatório: Processo analisado com base nos atos processuais fornecidos.\n\n{atos}")
        return f"Relatório: Processo analisado com base nos atos processuais fornecidos.\n\n{atos}"

def clean_textblock_artifacts(text: str) -> str:
    """
    Remove resíduos de TextBlock que possam aparecer no texto final.
    """
    if not text:
        return ""
    
    # Remove padrões como "TextBlock(citations=None, text="
    text = re.sub(r'TextBlock\([^)]*\)', '', text)
    
    # Remove padrões como "[TextBlock(citations=None, text="...")]"
    text = re.sub(r'\[TextBlock\([^]]*\)\]', '', text)
    
    # Remove "citations=None, text=" e variações
    text = re.sub(r'citations=None,\s*text=', '', text)
    text = re.sub(r'citations=[^,]*,\s*text=', '', text)
    text = re.sub(r"type='text'", '', text)
    
    # Remove aspas extras no início/fim
    text = text.strip('"\'')
    
    # Remove quebras de linha excessivas
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()

# ───────────────────────── geração principal ──────────────────────────────

# def generate(
#     pdf: Path,
#     cfg: Config,
#     on_progress: Optional[Callable[[str], None]] = None
# ) -> str:
#     # Esta linha agora seleciona dinamicamente o provedor para o resumo
#     summary_llm = get_llm(cfg.summary_model, cfg)
    
#     # (O resto da função continua exatamente o mesmo)
#     digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
#     cache_path = Path(f"/tmp/report_{digest}.txt")
#     if cache_path.exists():
#         log("♻️  Usando relatório em cache", cfg)
#         if on_progress: on_progress("♻️ Usando relatório em cache...")
#         return cache_path.read_text(encoding="utf-8")
#     try:
#         pages = extract_text_from_pdf(pdf, cfg, on_progress)
#         groups, process_number, section_id_map = group_pages(pages, cfg)
#         if process_number and on_progress: on_progress(f"📋 Processo nº {process_number} identificado")
#         chunks_para_resumir: List[Tuple[str, str]] = []
#         for label, blocos in groups.items():
#             texto_secao = "\n".join(blocos)
#             if len(texto_secao) > cfg.fallback_chars:
#                 parts = [texto_secao[i : i + cfg.fallback_chars] for i in range(0, len(texto_secao), cfg.fallback_chars)]
#             else:
#                 parts = [texto_secao]
#             for pi, part in enumerate(parts, start=1):
#                 chunks_para_resumir.append((label, part))
#         if on_progress: on_progress(f"🧠 Resumindo {len(chunks_para_resumir)} partes do processo em paralelo...")
#         def _job(label_text: Tuple[str,str]) -> str:
#             label, texto = label_text
#             resumo = summarize(texto, summary_llm, cfg)
#             id_real = section_id_map.get(label)
#             if id_real: resumo = resumo.rstrip(".") + f" (ID {id_real})."
#             return clean_textblock_artifacts(resumo)
#         linhas: List[str] = []
#         with ThreadPoolExecutor(max_workers=8) as pool:
#             futures = { pool.submit(_job, lt): lt for lt in chunks_para_resumir }
#             for fut in as_completed(futures):
#                 linhas.append(fut.result())
#         atos = "\n".join(linhas)
#         if on_progress: on_progress("⚙️ Construindo relatório final...")
#         report = build_report(atos, process_number, cfg)
#         report_limpo = clean_textblock_artifacts(report)
#         cache_path.write_text(report_limpo, encoding="utf-8")
#         if on_progress: on_progress("✅ Relatório pronto!")
#         return report_limpo
#     except Exception as e:
#         error_msg = f"Erro na geração do relatório: {str(e)}"
#         print(error_msg, file=sys.stderr)
#         if on_progress: on_progress(f"❌ {error_msg}")
#         return f"Erro no processamento: {str(e)}"

def generate(
    pdf: Path,
    cfg: Config,
    on_progress: Optional[Callable[[str], None]] = None
) -> str:
    summary_llm = get_llm(cfg.summary_model, cfg)
    
    # ── CACHE (sem alterações) ──
    digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
    cache_path = Path(f"/tmp/report_{digest}.txt")
    if cache_path.exists():
        log("♻️  Usando relatório em cache", cfg)
        if on_progress: on_progress("♻️ Usando relatório em cache...")
        return cache_path.read_text(encoding="utf-8")
        
    try:
        # 1) NOVO: Extrai texto do PDF com OCR paralelo para páginas de imagem
        pages = extract_text_from_pdf(pdf, cfg, on_progress)

        # 2) Agrupa por peça e extrai número do processo (sem alterações)
        groups, process_number, section_id_map = group_pages(pages, cfg)
        
        if process_number and on_progress:
            on_progress(f"📋 Processo nº {process_number} identificado")

        # 3) Prepara os chunks para o resumo (sem alterações)
        chunks_para_resumir: List[Tuple[str, str]] = []
        for label, blocos in groups.items():
            # ... (lógica de divisão de chunks grandes continua a mesma) ...
            texto_secao = "\n".join(blocos)
            if len(texto_secao) > cfg.fallback_chars:
                parts = [texto_secao[i : i + cfg.fallback_chars] for i in range(0, len(texto_secao), cfg.fallback_chars)]
            else:
                parts = [texto_secao]
            for pi, part in enumerate(parts, start=1):
                chunks_para_resumir.append((label, part))
        
        if on_progress: on_progress(f"🧠 Resumindo {len(chunks_para_resumir)} partes do processo em paralelo...")

        # 4) Paraleliza chamadas de resumo com ThreadPoolExecutor (sem alterações)
        def _job(label_text: Tuple[str,str]) -> str:
            label, texto = label_text
            resumo = summarize(texto, summary_llm, cfg)
            id_real = section_id_map.get(label)
            if id_real: resumo = resumo.rstrip(".") + f" (ID {id_real})."
            return clean_textblock_artifacts(resumo)

        linhas: List[str] = []
        with ThreadPoolExecutor(max_workers=8) as pool: # Aumentado para 8 workers
            futures = { pool.submit(_job, lt): lt for lt in chunks_para_resumir }
            for fut in as_completed(futures):
                linhas.append(fut.result())

        atos = "\n".join(linhas)

        # 5) Construção do relatório final (sem alterações)
        if on_progress: on_progress("⚙️ Construindo relatório final...")
        report = build_report(atos, process_number, cfg)
        report_limpo = clean_textblock_artifacts(report)
        cache_path.write_text(report_limpo, encoding="utf-8")
        
        if on_progress: on_progress("✅ Relatório pronto!")
        return report_limpo
        
    except Exception as e:
        error_msg = f"Erro na geração do relatório: {str(e)}"
        print(error_msg, file=sys.stderr)
        if on_progress: on_progress(f"❌ {error_msg}")
        return f"Erro no processamento: {str(e)}"
# ───────────────────────────── CLI ────────────────────────────────────────
if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Relatório analítico peça-aware (dual-model com suporte ao Claude)"
    )
    ap.add_argument("pdf", type=Path)
    ap.add_argument("-o", "--output", type=Path)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    cfg = Config(verbose=not args.quiet)
    rel = generate(args.pdf, cfg)

    if args.output:
        args.output.write_text(rel, encoding="utf-8")
        log(f"Relatório salvo em {args.output}", cfg)
    else:
        print(rel)