"""
Diagnóstico da captura de áudio com microfone de verdade.

Os testes de `testes/teste_vad.py` usam áudio sintético, o que valida a
decisão do VAD mas não a gravação. Este script fecha a lacuna: ele grava do
microfone real, mostra o que o VAD decidiu frame a frame e salva o WAV para
você ouvir exatamente o que foi capturado.

Requer: microfone funcionando e permissão de gravação no Windows.
Execute: python testes/diagnostico_pipeline.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import wave

import numpy as np
import sounddevice as sd

from utils import config, voz_vad
from utils.escuta import _detectar_dispositivo, _resample_para_whisper, TAXA

max_seg = float(config.get("tempo_escuta_max") or 15)
silencios = float(config.get("silencios_para_parar") or 1.2)

dispositivo, taxa_nativa = _detectar_dispositivo()
print(f"Dispositivo {dispositivo} a {taxa_nativa}Hz")
print(f"Máximo {max_seg:.0f}s, para após {silencios:.1f}s de silêncio\n")

detector = voz_vad.DetectorVoz(taxa_nativa)
por_frame = detector.amostras_por_frame
max_amostras = int(max_seg * taxa_nativa)
piso_para_parar = detector.janela_seg + silencios

audio_gravado = []
decisoes = []
total = 0

with sd.InputStream(
    device=dispositivo,
    samplerate=taxa_nativa,
    channels=1,
    dtype="float32",
    latency="high",
) as stream:
    stream.start()
    print("falando ao microfone...\n")
    while total < max_amostras:
        frame, overflow = stream.read(por_frame)
        if overflow:
            print("  [AVISO: buffer overflow, frame descartado]")

        amostra = frame.reshape(-1)
        audio_gravado.append(amostra)
        decisoes.append(detector.processar_frame(amostra))
        total += por_frame

        if detector.fala_ativa:
            continue
        if total >= piso_para_parar and detector.silencio_seguido_seg >= silencios:
            print(f"  [parou: {detector.silencio_seguido_seg:.1f}s de silêncio aos "
                  f"{total / taxa_nativa:.1f}s]")
            break
    stream.stop()

if total >= max_amostras:
    print(f"  [parou: tempo máximo aos {total / taxa_nativa:.1f}s]")

audio_bruto = np.concatenate(audio_gravado) if audio_gravado else np.zeros(0, dtype=np.float32)
dec = np.array(decisoes, dtype=bool)

print(f"\nCapturado: {len(audio_bruto)} amostras ({len(audio_bruto) / taxa_nativa:.2f}s)")
print(f"Decidido:   {dec.sum()} frames de fala ({dec.sum() * 0.03:.2f}s) em {len(dec)} frames")
print(f"tem_fala:  {voz_vad.tem_fala(audio_bruto, taxa_nativa)}")
print(f"rezSamples: {len(_resample_para_whisper(audio_bruto, taxa_nativa))} a {TAXA}Hz")

rms, zcr, planura = voz_vad.medir(audio_bruto, taxa_nativa)
if rms.size:
    cv = float(rms.std() / rms.mean()) if rms.mean() > 0 else 0.0
    print(f"\nrms: media={rms.mean():.5f} min={rms.min():.5f} max={rms.max():.5f} cv={cv:.3f}")
    print(f"zcr: media={zcr.mean():.3f} min={zcr.min():.3f} max={zcr.max():.3f} "
          f"(janela {voz_vad.ZCR_MIN}-{voz_vad.ZCR_MAX})")
    print(f"planura: media={planura.mean():.3f} min={planura.min():.3f} "
          f"max={planura.max():.3f} (max {voz_vad.FLATNESS_MAX})")
    print(f"separacao topo/piso: "
          f"{float(np.percentile(rms, 95)) / max(voz_vad.PISO_ABSOLUTO, float(np.percentile(rms, 15))):.2f} "
          f"(minimo {voz_vad.SEPARACAO_MINIMA})")

print("\nVAD por frame (1 = fala, . = não):")
print("".join("1" if d else "." for d in dec))
print(f"{len(dec)} frames = {len(dec) * 0.03:.2f}s\n")


def salvar_wav(caminho, audio, taxa):
    audio_int16 = (np.clip(audio, -1, 1) * 32767).astype(np.int16)
    with wave.open(caminho, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(int(taxa))
        wf.writeframes(audio_int16.tobytes())


salvar_wav("diag_bruto.wav", audio_bruto, taxa_nativa)
print("Salvo: diag_bruto.wav (audio bruto, taxa nativa)")

salvar_wav("diag_cortado.wav", voz_vad.cortar_silencio(audio_bruto, taxa_nativa), taxa_nativa)
print("Salvo: diag_cortado.wav (so o que o VAD marcou como fala)")

salvar_wav("diag_resample.wav", _resample_para_whisper(audio_bruto, taxa_nativa), TAXA)
print(f"Salvo: diag_resample.wav (apos resample para {TAXA}Hz, o que vai pro Whisper)")
