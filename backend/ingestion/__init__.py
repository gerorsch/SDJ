"""
Módulo de Ingestão e Triagem - Camada de processamento inicial
"""

from .classifier import DocumentClassifier
from .splitter import IntelligentSplitter
from .ocr import OCRProcessor

__all__ = [
    "DocumentClassifier",
    "IntelligentSplitter",
    "OCRProcessor",
]

