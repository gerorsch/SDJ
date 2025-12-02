"""
Agente Cronologista - Extrai datas e fatos do relatório
"""

import os
import json
import re
from typing import Dict, Any, List
from .base import BaseAgent
from .state import AgentState
from dotenv import load_dotenv
import anthropic

load_dotenv()


class TimelineAgent(BaseAgent):
    """
    Agente Cronologista que extrai datas, eventos e fatos relevantes
    do relatório, criando uma timeline estruturada.
    """
    
    def __init__(self):
        super().__init__(
            name="timeline",
            description="Extrai datas, eventos e fatos para criar timeline"
        )
        self.llm_model = os.getenv("TIMELINE_MODEL", "claude-sonnet-4-20250514")
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    async def process(self, state: AgentState) -> AgentState:
        """
        Processa o texto e extrai timeline de datas e fatos.
        """
        if not state.input_text:
            state.add_error("Texto de entrada não fornecido para timeline")
            return state
        
        try:
            timeline_data = await self._extract_timeline(state.input_text)
            state.timeline = timeline_data
            state.metadata["timeline_events_count"] = len(timeline_data.get("events", []))
        except Exception as e:
            error_msg = f"Erro na extração de timeline: {str(e)}"
            state.add_error(error_msg)
        
        return state
    
    async def _extract_timeline(self, text: str) -> Dict[str, Any]:
        """
        Extrai timeline usando LLM para identificar datas e eventos.
        """
        prompt = f"""Analise o seguinte texto jurídico e extraia todas as datas, eventos e fatos relevantes, organizando-os em ordem cronológica.

Texto:
{text[:8000]}  # Limita o tamanho para evitar exceder tokens

Retorne um JSON com a seguinte estrutura:
{{
    "events": [
        {{
            "date": "DD/MM/YYYY ou descrição da data",
            "description": "Descrição do evento/fato",
            "type": "peticao|contestacao|decisao|sentenca|audiencia|outro",
            "relevance": "alta|media|baixa"
        }}
    ],
    "key_dates": ["lista de datas importantes"],
    "summary": "Resumo cronológico dos principais eventos"
}}

Seja preciso e extraia apenas informações claramente mencionadas no texto."""

        try:
            response = self.client.messages.create(
                model=self.llm_model,
                max_tokens=2048,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Extrai o texto da resposta
            content = response.content
            if isinstance(content, list):
                text_response = "".join([block.text for block in content if hasattr(block, 'text')])
            else:
                text_response = str(content)
            
            # Tenta extrair JSON da resposta
            json_match = re.search(r'\{.*\}', text_response, re.DOTALL)
            if json_match:
                timeline_json = json.loads(json_match.group())
                return timeline_json
            else:
                # Fallback: cria estrutura básica
                return {
                    "events": self._extract_dates_fallback(text),
                    "key_dates": [],
                    "summary": "Timeline extraída automaticamente"
                }
                
        except Exception as e:
            # Fallback em caso de erro
            return {
                "events": self._extract_dates_fallback(text),
                "key_dates": [],
                "summary": f"Timeline extraída com fallback (erro: {str(e)})"
            }
    
    def _extract_dates_fallback(self, text: str) -> List[Dict[str, Any]]:
        """
        Método fallback para extrair datas usando regex quando o LLM falha.
        """
        events = []
        
        # Padrões de data comuns em documentos jurídicos
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',  # DD/MM/YYYY
            r'\d{1,2}-\d{1,2}-\d{4}',  # DD-MM-YYYY
            r'\d{4}-\d{2}-\d{2}',      # YYYY-MM-DD
        ]
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                date_str = match.group()
                # Tenta pegar contexto ao redor da data
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 100)
                context = text[start:end]
                
                events.append({
                    "date": date_str,
                    "description": context.strip()[:200],
                    "type": "outro",
                    "relevance": "media"
                })
        
        # Remove duplicatas
        seen = set()
        unique_events = []
        for event in events:
            key = (event["date"], event["description"][:50])
            if key not in seen:
                seen.add(key)
                unique_events.append(event)
        
        return unique_events[:20]  # Limita a 20 eventos
    
    def validate(self, state: AgentState) -> bool:
        """Valida se há texto para processar"""
        return bool(state.input_text)

