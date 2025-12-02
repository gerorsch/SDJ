"""
Cliente Qdrant - Preparação para substituir Elasticsearch no futuro
"""

import os
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv

load_dotenv()


class QdrantClient:
    """
    Cliente Qdrant para Vector Database.
    Por enquanto, estrutura base com placeholder.
    """
    
    def __init__(self):
        self.host = os.getenv("QDRANT_HOST", "localhost")
        self.port = int(os.getenv("QDRANT_PORT", "6333"))
        self.collection_name = os.getenv("QDRANT_COLLECTION", "jurisprudentia")
        self.enabled = os.getenv("QDRANT_ENABLED", "false").lower() == "true"
        self.client = None
        
        if self.enabled:
            try:
                from qdrant_client import QdrantClient as QdrantClientLib
                self.client = QdrantClientLib(host=self.host, port=self.port)
            except ImportError:
                print("⚠️ qdrant-client não instalado. Qdrant desabilitado.")
                self.enabled = False
    
    def create_collection(self, vector_size: int = 1536) -> bool:
        """
        Cria uma coleção no Qdrant.
        
        Args:
            vector_size: Tamanho dos vetores (dimensões)
            
        Returns:
            True se criado com sucesso
        """
        if not self.enabled or not self.client:
            return False
        
        try:
            from qdrant_client.models import Distance, VectorParams
            
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
            return True
        except Exception as e:
            print(f"⚠️ Erro ao criar coleção Qdrant: {e}")
            return False
    
    def upsert(self, points: List[Dict[str, Any]]) -> bool:
        """
        Insere ou atualiza pontos na coleção.
        
        Args:
            points: Lista de pontos com id, vector e payload
            
        Returns:
            True se inserido com sucesso
        """
        if not self.enabled or not self.client:
            return False
        
        try:
            from qdrant_client.models import PointStruct
            
            points_struct = [
                PointStruct(
                    id=point["id"],
                    vector=point["vector"],
                    payload=point.get("payload", {})
                )
                for point in points
            ]
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=points_struct
            )
            return True
        except Exception as e:
            print(f"⚠️ Erro ao inserir pontos no Qdrant: {e}")
            return False
    
    def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filter: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca vetores similares.
        
        Args:
            query_vector: Vetor de consulta
            top_k: Número de resultados
            filter: Filtros opcionais
            
        Returns:
            Lista de resultados
        """
        if not self.enabled or not self.client:
            return []
        
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                query_filter=filter
            )
            
            return [
                {
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload
                }
                for result in results
            ]
        except Exception as e:
            print(f"⚠️ Erro na busca Qdrant: {e}")
            return []
    
    def is_available(self) -> bool:
        """Verifica se Qdrant está disponível"""
        return self.enabled and self.client is not None


# Instância global (lazy initialization)
_qdrant_client = None


def get_qdrant_client() -> QdrantClient:
    """
    Retorna a instância do cliente Qdrant (singleton).
    
    Returns:
        QdrantClient
    """
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClient()
    return _qdrant_client

