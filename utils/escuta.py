"""
Módulo de reconhecimento de voz do Sumé.
Whisper local + VAD (detecção de silêncio).
"""

import sounddevice as sd
import numpy as np
import whisper
import threading
import time

MODELO = "small"
TAXA = 16000
SILENCIO_LIMIAR = 0.02
SILENCIO_SEGUNDOS = 1.2
MAX_SEGUNDOS = 15

_modelo = None
_lock = threading.Lock()


def _carregar_modelo():
    global _modelo
    if _modelo is None:
        print("[ESCUTA] Carregando Whisper...")
        _modelo = whisper.load_model(MODELO)
        print("[ESCUTA] Whisper pronto.")
    return _modelo


def _tem_audio(audio_chunk, limiar):
    return np.max(np.abs(audio_chunk)) > limiar


def ouvir() -> str:
    modelo = _carregar_modelo()
    
    with _lock:
        try:
            print("Ouvindo... (fale algo)")
            
            audio_gravado = []
            silencio_inicio = None
            falando = False
            
            stream = sd.InputStream(samplerate=TAXA, channels=1, dtype="float32")
            stream.start()
            
            while True:
                chunk, _ = stream.read(int(TAXA * 0.25))
                audio_gravado.append(chunk.flatten())
                
                if _tem_audio(chunk, SILENCIO_LIMIAR):
                    falando = True
                    silencio_inicio = None
                elif falando:
                    if silencio_inicio is None:
                        silencio_inicio = time.time()
                    elif time.time() - silencio_inicio > SILENCIO_SEGUNDOS:
                        break
                
                if len(audio_gravado) * 0.25 > MAX_SEGUNDOS:
                    break
            
            stream.stop()
            stream.close()
            
            if not falando:
                return ""
            
            audio = np.concatenate(audio_gravado)
            resultado = modelo.transcribe(audio, language="pt", fp16=False, verbose=False)
            texto = resultado["text"].strip()
            
            if texto:
                print(f"Você (Whisper): {texto}")
            return texto
            
        except Exception as e:
            print(f"[ESCUTA] Erro: {e}")
            return ""