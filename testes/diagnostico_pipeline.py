import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import wave
import time
import numpy as np
import sounddevice as sd
from utils.escuta import _detectar_dispositivo, _resample_para_whisper, _tem_audio, _calibrar_limiar, SILENCIO_SEGUNDOS, MAX_SEGUNDOS, TAXA

dispositivo, taxa_nativa = _detectar_dispositivo()
stream = sd.InputStream(device=dispositivo, samplerate=taxa_nativa, channels=1, dtype="float32", latency="high")
stream.start()

limiar = _calibrar_limiar(stream, taxa_nativa)
print(f"Limiar calibrado: {limiar:.5f}")
print("Ouvindo... (fale algo)")

audio_gravado = []
silencio_inicio = None
falando = False

while True:
    chunk, overflow = stream.read(int(taxa_nativa * 0.25))
    if overflow:
        print("  [AVISO: buffer overflow neste chunk]")
    audio_gravado.append(chunk.flatten())

    nivel = float(np.max(np.abs(chunk)))
    if _tem_audio(chunk, limiar):
        if not falando:
            print(f"  [detectou fala, nivel={nivel:.5f}]")
        falando = True
        silencio_inicio = None
    elif falando:
        if silencio_inicio is None:
            silencio_inicio = time.time()
        elif time.time() - silencio_inicio > SILENCIO_SEGUNDOS:
            print("  [silêncio suficiente, parando]")
            break

    if len(audio_gravado) * 0.25 > MAX_SEGUNDOS:
        print("  [tempo máximo atingido]")
        break

stream.stop()
stream.close()

audio_bruto = np.concatenate(audio_gravado)
print(f"Total capturado: {len(audio_bruto)} amostras ({len(audio_bruto)/taxa_nativa:.2f}s) a {taxa_nativa}Hz")
print(f"Falando detectado: {falando}")

def salvar_wav(caminho, audio, taxa):
    audio_int16 = (np.clip(audio, -1, 1) * 32767).astype(np.int16)
    with wave.open(caminho, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(int(taxa))
        wf.writeframes(audio_int16.tobytes())

salvar_wav("diag_bruto.wav", audio_bruto, taxa_nativa)
print("Salvo: diag_bruto.wav (áudio bruto, taxa nativa)")

audio_resample = _resample_para_whisper(audio_bruto, taxa_nativa)
print(f"Após resample: {len(audio_resample)} amostras a {TAXA}Hz")
salvar_wav("diag_resample.wav", audio_resample, TAXA)
print("Salvo: diag_resample.wav (após resample para 16kHz, o que vai pro Whisper)")
