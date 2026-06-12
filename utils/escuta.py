import sounddevice as sd
import numpy as np
import vosk
import speech_recognition as sr
import json
import os
import io
import wave

# ========== VOSK (offline) ==========
modelo_path = os.path.join(os.path.dirname(__file__), "..", "modelo_voz")
vosk_disponivel = os.path.exists(modelo_path)

if vosk_disponivel:
    modelo = vosk.Model(modelo_path)
    reconhecedor = vosk.KaldiRecognizer(modelo, 44100)
    print("[ESCUTA] Vosk carregado (offline)")
else:
    modelo = None
    reconhecedor = None
    print("[ESCUTA] Vosk não encontrado. Usando apenas Google Speech.")

# ========== GOOGLE SPEECH (online) ==========
r = sr.Recognizer()

def ouvir_vosk(gravacao) -> str:
    reconhecedor.Reset()
    dados = gravacao.tobytes()
    reconhecedor.AcceptWaveform(dados)
    resultado = json.loads(reconhecedor.FinalResult())
    texto = resultado.get("text", "").strip()
    if texto:
        return texto.lower()

    parcial = json.loads(reconhecedor.PartialResult())
    texto = parcial.get("partial", "").strip()
    return texto.lower() if texto else ""

def ouvir_google(gravacao) -> str:
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(44100)
        wf.writeframes(gravacao.tobytes())
    buffer.seek(0)

    with sr.AudioFile(buffer) as source:
        audio = r.record(source)

    try:
        texto = r.recognize_google(audio, language='pt-BR')
        return texto.lower()
    except:
        return ""

def ouvir() -> str:
    print("Ouvindo...")
    gravacao = sd.rec(int(3 * 44100), samplerate=44100, channels=1, dtype='int16')
    sd.wait()

    # Verifica volume
    volume = np.abs(gravacao).mean()
    if volume < 50:
        return ""

    # Tenta Vosk primeiro (offline, rápido)
    if vosk_disponivel:
        texto = ouvir_vosk(gravacao)
        if texto:
            print("Você (Vosk):", texto)
            return texto

    # Fallback: Google Speech (online, mais flexível)
    texto = ouvir_google(gravacao)
    if texto:
        print("Você (Google):", texto)
        return texto

    print("Não entendi.")
    return ""