import pyttsx3
import sounddevice as sd
import numpy as np

# Teste de fala
engine = pyttsx3.init()
engine.say("Nexus online. Sistema funcionando.")
engine.runAndWait()

# Teste de escuta - grava 3 segundos
print("Diga algo...")
gravacao = sd.rec(int(3 * 44100), samplerate=44100, channels=1)
sd.wait()
print("Gravação concluída. Processando...")

# Por enquanto só confirma que capturou áudio
volume = np.abs(gravacao).mean()
if volume > 0.01:
    print(f"Áudio capturado! Volume médio: {volume:.4f}")
else:
    print("Nenhum áudio detectado. Verifique o microfone.")