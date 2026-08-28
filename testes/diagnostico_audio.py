"""
Script de diagnóstico: grava 3 segundos usando o mesmo pipeline do Sumé
e salva em WAV para você ouvir o que está sendo capturado de verdade.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import wave
import numpy as np
from utils.escuta import _detectar_dispositivo, _resample_para_whisper
import sounddevice as sd

dispositivo, taxa_nativa = _detectar_dispositivo()
print(f"Gravando 3 segundos do dispositivo (taxa nativa {taxa_nativa}Hz)...")
print("FALE ALGO AGORA:")

audio = sd.rec(int(3 * taxa_nativa), samplerate=taxa_nativa, channels=1, dtype="float32", device=dispositivo)
sd.wait()
audio = audio.flatten()

pico = float(np.max(np.abs(audio)))
rms = float(np.sqrt(np.mean(audio**2)))
print(f"Pico de amplitude: {pico:.4f} | RMS: {rms:.4f}")

# Salva o áudio cru (na taxa nativa) para você ouvir exatamente o que foi capturado
audio_int16 = (audio * 32767).astype(np.int16)
with wave.open("diagnostico.wav", "wb") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(taxa_nativa)
    wf.writeframes(audio_int16.tobytes())

print("Salvo em diagnostico.wav — abra e ouça o que foi gravado.")
