"""
Splitter Inteligente que preserva contexto jurídico
"""

from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document


class IntelligentSplitter:
    """
    Splitter inteligente que preserva a estrutura jurídica dos documentos,
    mantendo contexto entre chunks relacionados.
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: List[str] = None
    ):
        """
        Inicializa o splitter.
        
        Args:
            chunk_size: Tamanho máximo do chunk em caracteres
            chunk_overlap: Sobreposição entre chunks
            separators: Separadores customizados (padrão: jurídicos)
        """
        if separators is None:
            # Separadores específicos para documentos jurídicos
            separators = [
                "\n\n\n",  # Quebras de seção
                "\n\n",    # Parágrafos
                "\n",      # Linhas
                ". ",      # Frases
                " ",       # Palavras
                ""         # Caracteres
            ]
        
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators,
            length_function=len,
        )
    
    def split_text(self, text: str) -> List[str]:
        """
        Divide o texto em chunks preservando contexto.
        
        Args:
            text: Texto a ser dividido
            
        Returns:
            Lista de chunks de texto
        """
        return self.splitter.split_text(text)
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Divide uma lista de documentos em chunks.
        
        Args:
            documents: Lista de documentos LangChain
            
        Returns:
            Lista de documentos divididos
        """
        return self.splitter.split_documents(documents)
    
    def split_by_sections(self, text: str) -> List[Dict[str, str]]:
        """
        Divide o texto preservando seções jurídicas (Relatório, Fundamentação, Dispositivo).
        
        Args:
            text: Texto do documento
            
        Returns:
            Lista de dicionários com 'section' e 'content'
        """
        sections = []
        current_section = "outros"
        current_content = []
        
        # Padrões de seções jurídicas
        section_patterns = {
            "relatorio": [
                "relatório", "relatorio", "relato", "dos fatos",
                "narrativa", "histórico"
            ],
            "fundamentacao": [
                "fundamentação", "fundamentacao", "fundamento",
                "do direito", "análise", "considerações"
            ],
            "dispositivo": [
                "dispositivo", "decido", "julgo", "resolvo",
                "determino", "condeno", "absolvo"
            ]
        }
        
        lines = text.split("\n")
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Verifica se a linha indica início de nova seção
            for section_name, keywords in section_patterns.items():
                if any(kw in line_lower for kw in keywords) and len(line) < 200:
                    # Salva seção anterior
                    if current_content:
                        sections.append({
                            "section": current_section,
                            "content": "\n".join(current_content)
                        })
                    # Inicia nova seção
                    current_section = section_name
                    current_content = [line]
                    break
            else:
                # Continua acumulando conteúdo da seção atual
                current_content.append(line)
        
        # Adiciona última seção
        if current_content:
            sections.append({
                "section": current_section,
                "content": "\n".join(current_content)
            })
        
        return sections
    
    def split_preserving_structure(self, text: str) -> List[Dict[str, any]]:
        """
        Divide o texto preservando estrutura e metadados.
        
        Args:
            text: Texto a ser dividido
            
        Returns:
            Lista de dicionários com 'text', 'section', 'chunk_index'
        """
        # Primeiro, tenta dividir por seções
        sections = self.split_by_sections(text)
        
        chunks = []
        chunk_index = 0
        
        for section_data in sections:
            section_name = section_data["section"]
            section_text = section_data["content"]
            
            # Divide cada seção em chunks menores
            section_chunks = self.split_text(section_text)
            
            for chunk_text in section_chunks:
                chunks.append({
                    "text": chunk_text,
                    "section": section_name,
                    "chunk_index": chunk_index,
                    "metadata": {
                        "section": section_name,
                        "chunk_size": len(chunk_text)
                    }
                })
                chunk_index += 1
        
        return chunks

