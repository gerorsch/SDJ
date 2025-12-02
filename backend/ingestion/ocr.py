"""
OCR Processor - Wrapper para OCR de PDFs escaneados
"""

import os
from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class OCRProcessor:
    """
    Processador OCR para extrair texto de PDFs escaneados (imagens).
    Integra com pytesseract e pdf2image.
    """
    
    def __init__(self):
        self.tesseract_cmd = os.getenv("TESSERACT_CMD", None)
        self.enabled = os.getenv("OCR_ENABLED", "true").lower() == "true"
        
        if self.tesseract_cmd:
            try:
                import pytesseract
                pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
            except ImportError:
                print("⚠️ pytesseract não instalado. OCR desabilitado.")
                self.enabled = False
    
    def extract_text_from_pdf(self, pdf_path: str, lang: str = "por") -> Dict[str, Any]:
        """
        Extrai texto de um PDF usando OCR.
        
        Args:
            pdf_path: Caminho do arquivo PDF
            lang: Idioma para OCR (padrão: português)
            
        Returns:
            Dicionário com 'text' (texto extraído) e 'metadata'
        """
        if not self.enabled:
            return {
                "text": "",
                "metadata": {
                    "status": "disabled",
                    "message": "OCR está desabilitado"
                }
            }
        
        try:
            from pdf2image import convert_from_path
            import pytesseract
            
            # Converte PDF para imagens
            images = convert_from_path(pdf_path)
            
            # Extrai texto de cada página
            texts = []
            for i, image in enumerate(images):
                page_text = pytesseract.image_to_string(image, lang=lang)
                texts.append(page_text)
            
            full_text = "\n\n".join(texts)
            
            return {
                "text": full_text,
                "metadata": {
                    "status": "success",
                    "pages": len(images),
                    "language": lang,
                    "total_chars": len(full_text)
                }
            }
            
        except ImportError:
            return {
                "text": "",
                "metadata": {
                    "status": "error",
                    "message": "Dependências OCR não instaladas (pdf2image, pytesseract)"
                }
            }
        except Exception as e:
            return {
                "text": "",
                "metadata": {
                    "status": "error",
                    "message": str(e)
                }
            }
    
    def extract_text_from_image(self, image_path: str, lang: str = "por") -> Dict[str, Any]:
        """
        Extrai texto de uma imagem usando OCR.
        
        Args:
            image_path: Caminho do arquivo de imagem
            lang: Idioma para OCR
            
        Returns:
            Dicionário com 'text' e 'metadata'
        """
        if not self.enabled:
            return {
                "text": "",
                "metadata": {"status": "disabled"}
            }
        
        try:
            import pytesseract
            from PIL import Image
            
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, lang=lang)
            
            return {
                "text": text,
                "metadata": {
                    "status": "success",
                    "language": lang,
                    "total_chars": len(text)
                }
            }
            
        except Exception as e:
            return {
                "text": "",
                "metadata": {
                    "status": "error",
                    "message": str(e)
                }
            }
    
    def is_pdf_scanned(self, pdf_path: str) -> bool:
        """
        Verifica se um PDF é escaneado (imagem) ou tem texto extraível.
        
        Args:
            pdf_path: Caminho do PDF
            
        Returns:
            True se parece ser escaneado, False caso contrário
        """
        try:
            from pypdf import PdfReader
            
            reader = PdfReader(pdf_path)
            text_content = ""
            
            # Tenta extrair texto das primeiras 3 páginas
            for i, page in enumerate(reader.pages[:3]):
                text_content += page.extract_text()
            
            # Se há muito pouco texto (< 100 caracteres), provavelmente é escaneado
            return len(text_content.strip()) < 100
            
        except Exception:
            # Em caso de erro, assume que precisa OCR
            return True

