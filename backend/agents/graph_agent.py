"""
Agente Visual - Mapeia entidades e relações usando NetworkX + LLM
"""

import os
import json
import re
from typing import Dict, Any, List
import networkx as nx
from .base import BaseAgent
from .state import AgentState
from dotenv import load_dotenv
import anthropic

load_dotenv()


class GraphAgent(BaseAgent):
    """
    Agente Visual que mapeia entidades (pessoas, organizações, conceitos)
    e suas relações, criando um grafo de conhecimento.
    """
    
    def __init__(self):
        super().__init__(
            name="graph",
            description="Mapeia entidades e relações em grafo de conhecimento"
        )
        self.llm_model = os.getenv("GRAPH_MODEL", "claude-sonnet-4-20250514")
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    async def process(self, state: AgentState) -> AgentState:
        """
        Processa o texto e extrai entidades e relações.
        """
        if not state.input_text:
            state.add_error("Texto de entrada não fornecido para grafo")
            return state
        
        try:
            graph_data = await self._extract_entities_and_relations(state.input_text)
            state.graph = graph_data
            state.metadata["graph_nodes_count"] = len(graph_data.get("nodes", []))
            state.metadata["graph_edges_count"] = len(graph_data.get("edges", []))
        except Exception as e:
            error_msg = f"Erro na extração de grafo: {str(e)}"
            state.add_error(error_msg)
        
        return state
    
    async def _extract_entities_and_relations(self, text: str) -> Dict[str, Any]:
        """
        Extrai entidades e relações usando LLM e cria grafo NetworkX.
        """
        prompt = f"""Analise o seguinte texto jurídico e identifique:
1. Entidades (pessoas, organizações, conceitos jurídicos)
2. Relações entre essas entidades

Texto:
{text[:8000]}

Retorne um JSON com a seguinte estrutura:
{{
    "nodes": [
        {{
            "id": "id_unico",
            "label": "Nome da entidade",
            "type": "pessoa|organizacao|conceito|documento|processo",
            "properties": {{}}
        }}
    ],
    "edges": [
        {{
            "source": "id_origem",
            "target": "id_destino",
            "label": "tipo_de_relacao",
            "weight": 1.0
        }}
    ]
}}

Tipos de relações comuns: "processa", "representa", "requer", "decide", "apela", "contesta", etc."""

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
                graph_json = json.loads(json_match.group())
                
                # Valida e cria grafo NetworkX
                G = self._create_networkx_graph(graph_json)
                graph_json["networkx_serialized"] = self._serialize_graph(G)
                
                return graph_json
            else:
                # Fallback: extração básica
                return self._extract_entities_fallback(text)
                
        except Exception as e:
            # Fallback em caso de erro
            return self._extract_entities_fallback(text)
    
    def _create_networkx_graph(self, graph_data: Dict[str, Any]) -> nx.DiGraph:
        """
        Cria um grafo NetworkX a partir dos dados extraídos.
        """
        G = nx.DiGraph()
        
        # Adiciona nós
        for node in graph_data.get("nodes", []):
            G.add_node(
                node.get("id", ""),
                label=node.get("label", ""),
                type=node.get("type", "outro"),
                **node.get("properties", {})
            )
        
        # Adiciona arestas
        for edge in graph_data.get("edges", []):
            G.add_edge(
                edge.get("source", ""),
                edge.get("target", ""),
                label=edge.get("label", ""),
                weight=edge.get("weight", 1.0)
            )
        
        return G
    
    def _serialize_graph(self, G: nx.DiGraph) -> Dict[str, Any]:
        """
        Serializa o grafo NetworkX para formato JSON.
        """
        return {
            "nodes": [
                {
                    "id": node,
                    **G.nodes[node]
                }
                for node in G.nodes()
            ],
            "edges": [
                {
                    "source": u,
                    "target": v,
                    **G.edges[u, v]
                }
                for u, v in G.edges()
            ]
        }
    
    def _extract_entities_fallback(self, text: str) -> Dict[str, Any]:
        """
        Método fallback para extrair entidades básicas usando regex.
        """
        nodes = []
        edges = []
        
        # Padrões básicos para entidades
        # Nomes próprios (maiúsculas seguidas de minúsculas)
        name_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b'
        names = re.findall(name_pattern, text)
        
        # Organizações (com palavras-chave)
        org_keywords = ["tribunal", "vara", "juízo", "empresa", "ltda", "s/a"]
        orgs = []
        for keyword in org_keywords:
            pattern = rf'\b[A-Z][a-z]*\s+{keyword}\b'
            orgs.extend(re.findall(pattern, text, re.IGNORECASE))
        
        # Cria nós
        node_id = 0
        seen = set()
        
        for name in names[:20]:  # Limita a 20 nomes
            if name not in seen and len(name) > 3:
                seen.add(name)
                nodes.append({
                    "id": f"node_{node_id}",
                    "label": name,
                    "type": "pessoa",
                    "properties": {}
                })
                node_id += 1
        
        for org in orgs[:10]:  # Limita a 10 organizações
            if org not in seen:
                seen.add(org)
                nodes.append({
                    "id": f"node_{node_id}",
                    "label": org,
                    "type": "organizacao",
                    "properties": {}
                })
                node_id += 1
        
        # Cria grafo básico
        G = self._create_networkx_graph({"nodes": nodes, "edges": edges})
        
        return {
            "nodes": nodes,
            "edges": edges,
            "networkx_serialized": self._serialize_graph(G)
        }
    
    def validate(self, state: AgentState) -> bool:
        """Valida se há texto para processar"""
        return bool(state.input_text)

