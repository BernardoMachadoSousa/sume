"""
Módulo de reconhecimento de voz do Sumé.
Whisper local + VAD (detecção de silêncio).
"""

import sounddevice as sd
import numpy as np
import whisper
import threading
from utils.logger import erro as log_erro, info as log_info

MODELO = "small"
TAXA = 16000  # taxa exigida pelo Whisper
SILENCIO_LIMIAR = 0.02
DURACAO_GRAVACAO = 5  # segundos - simples e fixo, evita o ruído do streaming em pedaços

_modelo = None
_lock = threading.Lock()
_dispositivo_cache = None  # (index, samplerate_nativa), detectado uma vez e reaproveitado


def _detectar_dispositivo():
    """
    Encontra um dispositivo de entrada que realmente abre um stream.
    No Windows, o dispositivo MME padrão pode estar com driver quebrado
    mesmo aparecendo como "default" - por isso testamos WASAPI/DirectSound
    antes de cair no padrão do sistema.
    """
    global _dispositivo_cache
    if _dispositivo_cache is not None:
        return _dispositivo_cache

    hostapis = sd.query_hostapis()
    ordem_preferida = ["Windows WASAPI", "Windows DirectSound", "MME"]

    candidatos = []
    for idx, dev in enumerate(sd.query_devices()):
        if dev["max_input_channels"] > 0:
            nome_api = hostapis[dev["hostapi"]]["name"]
            prioridade = ordem_preferida.index(nome_api) if nome_api in ordem_preferida else len(ordem_preferida)
            candidatos.append((prioridade, idx, dev))
    candidatos.sort(key=lambda c: c[0])

    for _, idx, dev in candidatos:
        taxa = int(dev["default_samplerate"])
        try:
            stream = sd.InputStream(device=idx, samplerate=taxa, channels=1, dtype="float32")
            stream.start()
            stream.stop()
            stream.close()
            log_info("escuta", f"Dispositivo de áudio selecionado: '{dev['name']}' ({taxa}Hz)")
            _dispositivo_cache = (idx, taxa)
            return _dispositivo_cache
        except Exception as e:
            log_erro("escuta", f"Dispositivo '{dev['name']}' falhou ao abrir: {e}")
            continue

    raise RuntimeError("Nenhum dispositivo de entrada de áudio funcional foi encontrado.")


def _resample_para_whisper(audio: np.ndarray, taxa_origem: int) -> np.ndarray:
    """Converte a taxa de amostragem gravada para os 16000Hz que o Whisper exige."""
    if taxa_origem == TAXA:
        return audio
    n_amostras_destino = int(len(audio) * TAXA / taxa_origem)
    x_origem = np.linspace(0, 1, len(audio))
    x_destino = np.linspace(0, 1, n_amostras_destino)
    return np.interp(x_destino, x_origem, audio).astype(np.float32)


def _carregar_modelo():
    global _modelo
    if _modelo is None:
        print("[ESCUTA] Carregando Whisper...")
        _modelo = whisper.load_model(MODELO)
        print("[ESCUTA] Whisper pronto.")
    return _modelo


def _tem_audio(audio_chunk, limiar):
    return np.max(np.abs(audio_chunk)) > limiar


def _cortar_silencio(audio: np.ndarray, limiar: float, taxa: int, margem_inicio_seg: float = 0.6, margem_fim_seg: float = 0.3) -> np.ndarray:
    """
    Remove silêncio do início/fim do áudio já gravado.
    O Whisper tende a alucinar (repetir frases, gerar texto aleatório) quando
    recebe áudio com muito silêncio de sobra - cortar isso reduz bastante o problema.
    Margem do início é maior porque consoantes iniciais (ex: "Qu") têm amplitude
    baixa e podem ficar abaixo do limiar, cortando o começo da palavra.
    """
    acima_limiar = np.abs(audio) > limiar
    indices = np.nonzero(acima_limiar)[0]
    if len(indices) == 0:
        return audio[:0]  # nada de fala detectada
    inicio = max(0, indices[0] - int(margem_inicio_seg * taxa))
    fim = min(len(audio), indices[-1] + int(margem_fim_seg * taxa))
    return audio[inicio:fim]


def ouvir() -> str:
    modelo = _carregar_modelo()
    
    with _lock:
        try:
            dispositivo, taxa_nativa = _detectar_dispositivo()
            
            print("Ouvindo... (fale algo)")
            
            audio = sd.rec(
                int(DURACAO_GRAVACAO * taxa_nativa),
                samplerate=taxa_nativa,
                channels=1,
                dtype="float32",
                device=dispositivo,
            )
            sd.wait()
            audio = audio.flatten()
            
            if not _tem_audio(audio, SILENCIO_LIMIAR):
                return ""
            
            audio = _cortar_silencio(audio, SILENCIO_LIMIAR, taxa_nativa)
            if len(audio) < int(0.3 * taxa_nativa):  # muito curto pra ser fala de verdade
                return ""
            
            audio = _resample_para_whisper(audio, taxa_nativa)
            resultado = modelo.transcribe(audio, language="pt", fp16=False, verbose=False)
            texto = resultado["text"].strip()
            
            if texto:
                print(f"Você (Whisper): {texto}")
            return texto
            
        except Exception as e:
            log_erro("escuta", f"Falha ao capturar/transcrever áudio: {e}")
            print(f"[ESCUTA] Erro: {e}")
            return ""
    