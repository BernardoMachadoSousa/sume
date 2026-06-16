"""
Módulo de síntese de voz do Sumé.
Usa Edge TTS (Microsoft) para voz natural em português.
Fallback para pyttsx3 offline se Edge TTS falhar.
"""

import asyncio
import tempfile
import os
import threading
import edge_tts
import pyttsx3

# Configuração
VOZ_PRINCIPAL = "pt-BR-AntonioNeural"
VELOCIDADE = "+10%"  # velocidade da fala (opções: "-20%", "+0%", "+10%", "+20%")

# Engine offline (fallback)
_engine_offline = None


def _get_engine_offline():
    """Retorna engine pyttsx3 como fallback."""
    global _engine_offline
    if _engine_offline is None:
        _engine_offline = pyttsx3.init()
    return _engine_offline


def _tocar_audio(caminho_audio):
    """Toca o arquivo de áudio usando o player padrão do Windows."""
    os.system(f'start /min "" "{caminho_audio}"')


def _falar_offline(texto):
    """Fallback com pyttsx3 (robótico)."""
    engine = _get_engine_offline()
    engine.say(texto)
    engine.runAndWait()


async def _gerar_audio_edge(texto, caminho_saida):
    """Gera arquivo de áudio com Edge TTS."""
    comunicador = edge_tts.Communicate(
        text=texto,
        voice=VOZ_PRINCIPAL,
        rate=VELOCIDADE,
    )
    await comunicador.save(caminho_saida)


def falar(texto):
    """
    Fala o texto usando Edge TTS (natural).
    Se falhar, usa pyttsx3 como fallback (robótico).
    """
    if not texto or not texto.strip():
        return

    texto = texto.strip()

    try:
        # Cria arquivo temporário
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            caminho_audio = tmp.name

        # Gera áudio com Edge TTS
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_gerar_audio_edge(texto, caminho_audio))

        # Toca o áudio
        _tocar_audio(caminho_audio)

        # Agenda limpeza do arquivo após alguns segundos
        def _limpar():
            try:
                import time
                time.sleep(5)
                os.unlink(caminho_audio)
            except:
                pass

        threading.Thread(target=_limpar, daemon=True).start()

    except Exception as e:
        print(f"[Voz] Edge TTS falhou: {e}, usando fallback offline")
        try:
            _falar_offline(texto)
        except:
            pass


# Teste rápido
if __name__ == "__main__":
    falar("Olá, eu sou o Sumé. Minha voz está mais natural agora.")