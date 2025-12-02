"""
Classificador BERT para classificar tipo de documento jurídico
"""

import os
from typing import Dict, Optional
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from dotenv import load_dotenv

load_dotenv()


class DocumentClassifier:
    """
    Classificador BERT para identificar o tipo de documento jurídico.
    Classes: peticao_inicial, contestacao, sentenca, despacho, outros
    """
    
    def __init__(self):
        self.model_name = os.getenv(
            "BERT_CLASSIFIER_MODEL",
            "neuralmind/bert-base-portuguese-cased"
        )
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = None
        self.model = None
        self.classes = [
            "peticao_inicial",
            "contestacao",
            "sentenca",
            "despacho",
            "outros"
        ]
        self._load_model()
    
    def _load_model(self):
        """Carrega o modelo BERT (lazy loading)"""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            # Por enquanto, usa modelo genérico. Em produção, usar modelo fine-tuned
            # self.model = AutoModelForSequenceClassification.from_pretrained(
            #     self.model_name,
            #     num_labels=len(self.classes)
            # )
            # self.model.to(self.device)
            # self.model.eval()
            self.model = None  # Placeholder até ter modelo fine-tuned
        except Exception as e:
            print(f"⚠️ Erro ao carregar modelo BERT: {e}")
            print("⚠️ Usando classificação por palavras-chave como fallback")
            self.model = None
    
    def classify(self, text: str) -> Dict[str, any]:
        """
        Classifica o tipo de documento baseado no texto.
        
        Args:
            text: Texto do documento a ser classificado
            
        Returns:
            Dicionário com 'class' (tipo) e 'confidence' (confiança)
        """
        if not text or len(text.strip()) < 50:
            return {
                "class": "outros",
                "confidence": 0.5,
                "method": "fallback_short_text"
            }
        
        # Se modelo não está carregado, usa classificação por palavras-chave
        if self.model is None:
            return self._classify_by_keywords(text)
        
        # TODO: Implementar classificação com BERT quando modelo estiver disponível
        # Por enquanto, usa fallback
        return self._classify_by_keywords(text)
    
    def _classify_by_keywords(self, text: str) -> Dict[str, any]:
        """
        Classificação por palavras-chave (fallback quando BERT não está disponível).
        """
        text_lower = text.lower()
        
        # Palavras-chave para cada classe
        keywords = {
            "peticao_inicial": [
                "petição inicial", "peticao inicial", "requer", "requerente",
                "vem respeitosamente", "vem à presença", "pelos motivos expostos"
            ],
            "contestacao": [
                "contestação", "contestacao", "contesta", "defesa",
                "vem apresentar contestação", "nega os fatos"
            ],
            "sentenca": [
                "sentença", "sentenca", "julgo", "julgo procedente",
                "julgo improcedente", "resolvo o mérito", "dispositivo"
            ],
            "despacho": [
                "despacho", "determino", "intimo", "determina-se",
                "determino a", "intimo-se"
            ]
        }
        
        scores = {}
        for doc_type, kw_list in keywords.items():
            score = sum(1 for kw in kw_list if kw in text_lower)
            scores[doc_type] = score
        
        # Determina a classe com maior score
        if max(scores.values()) > 0:
            best_class = max(scores, key=scores.get)
            confidence = min(0.95, 0.5 + (scores[best_class] * 0.1))
        else:
            best_class = "outros"
            confidence = 0.5
        
        return {
            "class": best_class,
            "confidence": confidence,
            "method": "keyword_based",
            "scores": scores
        }
    
    def classify_batch(self, texts: list[str]) -> list[Dict[str, any]]:
        """
        Classifica múltiplos textos.
        
        Args:
            texts: Lista de textos a classificar
            
        Returns:
            Lista de resultados de classificação
        """
        return [self.classify(text) for text in texts]

