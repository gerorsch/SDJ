"""
Agente de Audiência - Transcrição e Diarização (WhisperX)
"""

import os
from typing import Dict, Any
from .base import BaseAgent
from .state import AgentState
from dotenv import load_dotenv

load_dotenv()


class TranscriptionAgent(BaseAgent):
    """
    Agente de Audiência que realiza transcrição e diarização de arquivos de áudio.
    Por enquanto, estrutura base com placeholder para futura integração com WhisperX.
    """
    
    def __init__(self):
        super().__init__(
            name="transcription",
            description="Transcreve e diariza arquivos de áudio (MP3, MP4)"
        )
        self.whisperx_enabled = os.getenv("WHISPERX_ENABLED", "false").lower() == "true"
    
    async def process(self, state: AgentState) -> AgentState:
        """
        Processa transcrição e diarização do arquivo de áudio.
        Por enquanto, retorna estrutura placeholder.
        """
        if not state.input_file_path:
            state.add_error("Arquivo de áudio não fornecido para transcrição")
            return state
        
        if state.input_file_type not in ["mp3", "mp4"]:
            state.add_error(f"Tipo de arquivo não suportado para transcrição: {state.input_file_type}")
            return state
        
        try:
            if self.whisperx_enabled:
                transcription_data = await self._transcribe_with_whisperx(state.input_file_path)
            else:
                # Placeholder para quando WhisperX não estiver configurado
                transcription_data = {
                    "transcription": f"[Placeholder] Transcrição do arquivo {state.input_file_path}",
                    "diarization": [],
                    "segments": [],
                    "status": "placeholder",
                    "note": "WhisperX não está habilitado. Configure WHISPERX_ENABLED=true para usar transcrição real."
                }
            
            state.transcription = transcription_data
            state.metadata["transcription_status"] = transcription_data.get("status", "unknown")
            
        except Exception as e:
            error_msg = f"Erro na transcrição: {str(e)}"
            state.add_error(error_msg)
        
        return state
    
    async def _transcribe_with_whisperx(self, file_path: str) -> Dict[str, Any]:
        """
        Realiza transcrição usando WhisperX.
        Por enquanto, retorna placeholder. Implementação futura.
        """
        # TODO: Implementar integração com WhisperX
        # Exemplo de estrutura esperada:
        return {
            "transcription": "[Transcrição completa do áudio]",
            "diarization": [
                {
                    "speaker": "SPEAKER_00",
                    "start": 0.0,
                    "end": 5.2,
                    "text": "Texto falado pelo speaker"
                }
            ],
            "segments": [],
            "status": "completed",
            "language": "pt-BR",
            "duration": 0.0
        }
    
    def validate(self, state: AgentState) -> bool:
        """Valida se há arquivo de áudio para processar"""
        return bool(state.input_file_path and state.input_file_type in ["mp3", "mp4"])

