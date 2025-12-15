import os
import random
import time
import math
import asyncio
from typing import Callable, Optional, List, Dict, Any
from openai import OpenAI
from anthropic import Anthropic

# Providers
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").strip().lower()  # 'openai' | 'anthropic'
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-5").strip()
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "128000"))
desired = LLM_MAX_TOKENS
_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if LLM_PROVIDER == "openai" else None
_anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY")) if LLM_PROVIDER == "anthropic" else None

if LLM_PROVIDER == "openai":
    try:
        from openai import OpenAI  # SDK v1
        _openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    except Exception as e:
        raise RuntimeError(f"Falha ao inicializar OpenAI client: {e}")
elif LLM_PROVIDER == "anthropic":
    try:
        from anthropic import Anthropic
        _anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    except Exception as e:
        raise RuntimeError(f"Falha ao inicializar Anthropic client: {e}")
else:
    raise ValueError(f"LLM_PROVIDER inválido: {LLM_PROVIDER}")

def _approx_tokens(txt: str) -> int:
    # heurística: ~4 chars por token (ajuste se quiser)
    return max(1, math.ceil(len(txt) / 4))

def _context_window_from_env(model: str) -> int:
    # permite override específico por modelo, ex.: LLM_CONTEXT_WINDOW_GPT_5=128000
    model_key = model.upper().replace("-", "_").replace(".", "_")
    return int(os.getenv(f"LLM_CONTEXT_WINDOW_{model_key}", os.getenv("LLM_CONTEXT_WINDOW", "32000")))

def _length_param_name(model: str) -> str:
    # modelos de raciocínio → max_completion_tokens; demais → max_tokens
    m = model.lower()
    return "max_completion_tokens" if m.startswith(("gpt-5", "o1", "o3", "o4-mini")) else "max_tokens"

def _cap_limit_tokens(model: str, messages, desired: int) -> int:
    ctx_window = _context_window_from_env(model)
    in_tokens = sum(_approx_tokens(m.get("content", "")) for m in messages)
    safety = int(os.getenv("LLM_SAFETY_TOKENS", "512"))
    available = ctx_window - in_tokens - safety
    # evita negativo e limita ao desejado
    return max(1, min(desired, max(1, available)))


# ===================== Grounding / Prompt =====================
SYSTEM_PROMPT_SENTENCA = """
Você é um juiz que redige sentenças **apenas** com base no CONTEXTO fornecido.
Regras (obrigatórias):
0) Inicie a sentença com o texto "É o que havia a relatar. Relatado o feito, DECIDO."
1) Use exclusivamente informações do bloco CONTEXTO.
2) Não cite lei/jurisprudência/precedente que não esteja no CONTEXTO.
3) Linguagem técnica jurídica brasileira; nada de analogias criativas ou suposições.
4) **Siga rigorosamente a ESTRUTURA DA SENTENÇA abaixo, mas sem citar os títulos.**
5) ** Não refira aos documentos de referência, como em "conforme ilustra a jurisprudência colacionada nos **documentos de referência**". Atue como se estivesse lido os documentos de referência e incorporado seu conhecimento. Cite diretamente apenas lei e jurisprudência encontradas nos documentos de referência, e não os textos próprios do documento.
6) **Exceção às regras 1–2:** o BLOCO DE CONCLUSÃO OBRIGATÓRIA deve ser reproduzido **exatamente** como fornecido ao final, **mesmo que não esteja no CONTEXTO**.
7) Antes de finalizar, verifique que cada asserção feita está explicitamente suportada pelo CONTEXTO.
""" 

def _safe_pick(d: Dict[str, Any], keys: List[str], default: str = "") -> str:
    for k in keys:
        v = d.get(k)
        if isinstance(v, str) and v.strip():
            return v
    return default

def _trim_text(s: str, max_chars: int) -> str:
    if len(s) <= max_chars:
        return s
    return s[: max_chars - 3] + "..."

def build_context(exemplos: List[Dict[str, Any]], *, max_docs: int = 5, max_chars_per_doc: int = 10000) -> str:
    if not exemplos:
        return "(nenhum documento fornecido)"

    blocos = []
    for i, doc in enumerate(exemplos[:max_docs]):
        titulo = _safe_pick(doc, ["titulo", "title", "nome"], default=f"Documento {i+1}")
        # 👇 juntar relatorio, fundamentacao, dispositivo
        conteudo = ""
        for k in ["conteudo", "content", "texto", "trecho", "body", "relatorio", "fundamentacao", "dispositivo"]:
            v = doc.get(k)
            if isinstance(v, str) and v.strip():
                conteudo += v.strip() + "\n\n"
        conteudo = _trim_text(conteudo.strip(), max_chars_per_doc) if conteudo else "[sem conteúdo]"
        blocos.append(f"Documento {i+1}: {titulo}\n---\n{conteudo}\n")

    return "\n\n".join(blocos)

def _montar_mensagens_sentenca(relatorio: str, contexto: str, instrucoes_usuario: Optional[str]) -> List[Dict[str, str]]:
    relatorio = (relatorio or "").strip()
    contexto = (contexto or "").strip()
    instr = (instrucoes_usuario or "").strip()
    instr_block = f"INSTRUÇÕES ADICIONAIS DO USUÁRIO:\n{instr}\n\n" if instr else ""

    user_msg = f"""
TAREFA: Gerar sentença (fundamentação + dispositivo) **estritamente** baseada no CONTEXTO.

NOVO RELATÓRIO:
{relatorio}

{instr_block}
=== CONTEXTO (única fonte de verdade) ===

{contexto}
=== FIM DO CONTEXTO ===

## ESTRUTURA DA SENTENÇA

### 0. JULGAMENTO ANTECIPADO
- Verifique no RELATÓRIO se houve produção de provas, como audiência de instrução e julgamento, perícia técnica, etc. Caso as partes não tenham produzido provas, anuncie o julgamento antecipado previsto no art. 355, conforme o CONTEXTO.

### 1. QUESTÕES PRELIMINARES
- Analise o processo e identifique se há, na CONTESTAÇÃO questões PRELIMINARES suscitadas (exemplo: inépcia da inicial, impugnação ao valor da causa, falta de interesse de agir, prescrição, etc.).
- Se houver preliminares, desenvolva a fundamentação para cada uma delas separadamente.
- Se não houver preliminares, escreva a frase "Ausentes questões preliminares, passo ao mérito." e siga para o mérito.

### 2. MÉRITO
- Inicie afirmando claramente o(s) fato(s) que constitui(em) a causa de pedir do autor.
- Em seguida, apresente o principal argumento do réu em sua defesa.
- Desenvolva a fundamentação com base nos documentos de referência, analisando:
  - Os fatos comprovados nos autos
  - As provas produzidas
  - A legislação aplicável
  - A jurisprudência pertinente
  - A doutrina relevante

#### REGRAS IMPORTANTES PARA A FUNDAMENTAÇÃO:
- As citações de lei, doutrina ou jurisprudência devem ser reproduzidas **EXATAMENTE** como constam nos documentos de referência, sem alterações.
- A argumentação deve ser coerente, lógica e completa.
- Utilize linguagem técnica-jurídica apropriada.
- Analise todos os pedidos formulados na inicial.

### 3. DISPOSITIVO
- Elabore o dispositivo da sentença, decidindo sobre todos os pedidos.
- Fixe os honorários advocatícios conforme critérios do art. 85 do CPC.

### 4. CONCLUSÃO OBRIGATÓRIA
Após o dispositivo e a condenação em honorários, encerre a sentença com **EXATAMENTE** o seguinte texto, **sem nenhuma alteração**:

"Opostos embargos de declaração com efeito modificativo, intime-se a parte embargada para, querendo, manifestar-se no prazo de 05 (cinco) dias. (art. 1.023, § 2º, do CPC/2015), e decorrido o prazo, com ou sem manifestação, voltem conclusos.

Na hipótese de interposição de recurso de apelação, intime-se a parte apelada para apresentar contrarrazões (art. 1010, §1º, do CPC/2015). Havendo alegação – em sede de contrarrazões - de questões resolvidas na fase de conhecimento as quais não comportaram agravo de instrumento, intime-se a parte adversa (recorrente) para, em 15 (quinze) dias, manifestar-se a respeito delas (art. 1.009, §§ 1º e 2º, do CPC/2015). Havendo interposição de apelação adesiva, intime-se a parte apelante para contrarrazões, no prazo de 15 (quinze) dias (art. 1010, §2º, do CPC/2015). Em seguida, com ou sem resposta, sigam os autos ao e. Tribunal de Justiça do Estado de Pernambuco, com os cumprimentos deste Juízo (art. 1010, §3º, do CPC/2015).

Após o trânsito em julgado, nada mais sendo requerido, arquivem-se os autos, com as cautelas de estilo, independentemente de nova determinação.

Comunicações processuais necessárias.

Cumpra-se.
Recife-PE, data da assinatura digital.

Maria Betânia Martins da Hora

Juíza de Direito"

## INSTRUÇÕES FINAIS
- Leia atentamente o relatório e todos os documentos de referência antes de iniciar a redação.
- **Siga rigorosamente a estrutura indicada acima.**
- Certifique-se de que o texto final está coeso, coerente e tecnicamente preciso.
- **Não omita** nenhum dos elementos obrigatórios da sentença.
- As citações de leis, doutrina e jurisprudência devem ser exatamente iguais às dos documentos de referência.
"""
    return [
        {"role": "system", "content": SYSTEM_PROMPT_SENTENCA},
        {"role": "user", "content": user_msg},
    ]


# ===================== Chamada às APIs =====================

def _extract_text_from_response(content: Any) -> str:
    """Extrai texto de respostas do Anthropic (content blocks)."""
    try:
        parts = []
        for block in content or []:
            # Estrutura comum: {"type": "text", "text": "..."}
            t = block.get("text") if isinstance(block, dict) else None
            if isinstance(t, str) and t:
                parts.append(t)
        return "".join(parts)
    except Exception:
        return ""


def _call_llm(*, messages: List[Dict[str, str]], on_progress: Optional[Callable[[str], None]] = None) -> str:
    max_retries = 5
    base_delay = 1
    param_name = _length_param_name(LLM_MODEL)
    limit = _cap_limit_tokens(LLM_MODEL, messages, LLM_MAX_TOKENS)
    
    for attempt in range(max_retries):
        try:
            if on_progress:
                on_progress(f"🤖 Consultando {LLM_PROVIDER.capitalize()} ({LLM_MODEL})... (Tentativa {attempt+1})")

            if LLM_PROVIDER == "openai":
           
                kwargs = {
                    "model": LLM_MODEL,
                    "messages": messages,
                    param_name: limit,           
                }

                # gpt-5 não aceita temperature ≠ 1
                if not LLM_MODEL.startswith("gpt-5"):
                    kwargs["temperature"] = LLM_TEMPERATURE

                seed_env = os.getenv("LLM_SEED")
                if seed_env and seed_env.isdigit():
                    kwargs["seed"] = int(seed_env)

                resp = _openai.chat.completions.create(**kwargs)
                return (resp.choices[0].message.content or "").strip()

            else:  # anthropic
                resp = _anthropic.messages.create(
                    model=LLM_MODEL,
                    max_tokens=LLM_MAX_TOKENS,
                    temperature=LLM_TEMPERATURE,
                    messages=messages,
                )
                # extrai texto dos blocks:
                text = "".join([b.get("text","") for b in getattr(resp, "content", []) if isinstance(b, dict)])
                return (text or "").strip()

        except Exception as e:
            # backoff simples para erros transitórios
            transient = ["529", "overloaded", "500", "503", "rate_limit", "timeout"]
            if any(t in str(e).lower() for t in transient) and attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                if on_progress: on_progress(f"⏳ API indisponível. Tentando de novo em {delay:.2f}s...")
                time.sleep(delay)
            else:
                if on_progress: on_progress(f"❌ Erro na chamada da API {LLM_PROVIDER}: {e}")
                return f"Erro na chamada da API {LLM_PROVIDER}: {e}"
    return "Erro: A chamada da API falhou após múltiplas tentativas."

# ===================== Função principal =====================

async def gerar_sentenca_llm(
    *,
    relatorio: str,
    exemplos: Optional[List[Dict[str, Any]]] = None,
    docs: Optional[List[Dict[str, Any]]] = None,   # <- retrocompatível com main.py
    instrucoes_usuario: Optional[str] = None,
    on_progress: Optional[Callable[[str], None]] = None,
) -> str:
    if exemplos is None and docs is not None:
        exemplos = docs

    if on_progress: on_progress("📚 Preparando CONTEXTO...")
    contexto = build_context(exemplos or [])

    if on_progress: on_progress("✍️ Montando mensagens...")
    messages = _montar_mensagens_sentenca(relatorio, contexto, instrucoes_usuario)

    if on_progress: on_progress("🎯 Gerando sentença...")

    # roda a chamada bloqueante em thread, já que o endpoint é async
    loop = asyncio.get_running_loop()
    resultado = await loop.run_in_executor(None, lambda: _call_llm(messages=messages, on_progress=on_progress))

    if on_progress: on_progress("✅ Sentença gerada com sucesso!")
    return resultado


__all__ = [
    "gerar_sentenca_llm",
    "build_context",
]
