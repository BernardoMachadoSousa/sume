"""
Módulo de reconhecimento de voz do Sumé.
Whisper local + VAD por frames (utils/voz_vad.py).
"""

import sounddevice as sd
import numpy as np
import whisper
import threading
from utils import config
from utils import voz_vad
from utils.logger import erro as log_erro, info as log_info

MODELO = "small"
TAXA = 16000  # taxa exigida pelo Whisper

# Fala mais curta que vale a pena mandar pro Whisper. Abaixo disso foi um
# toque, uma batida na mesa ou o barulho de alguém ajeitando a cadeira.
MIN_FALA_SEG = 0.3

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


def _capturar(
    dispositivo: int,
    taxa: int,
    max_seg: float,
    silencios_para_parar: float,
    agressividade: int = 1,
) -> np.ndarray:
    """
    Grava até dar tempo máximo, ou até vir `silencios_para_parar` de silêncio
    depois que o silêncio já tem início.

    A parada antecipada só vale depois de `janela_seg + silencios_para_parar`:
    o DetectorVoz precisa da janela inteira para ter uma opinião, e sem esse
    piso ele contaria o preenchimento da própria janela como silêncio e
    devolveria vazio antes de o usuário começar a falar.
    """
    detector = voz_vad.DetectorVoz(taxa, agressividade)
    por_frame = detector.amostras_por_frame
    max_amostras = int(max_seg * taxa)
    piso_para_parar = detector.janela_seg + silencios_para_parar

    blocos = []
    total = 0
    descartes = 0

    with sd.InputStream(
        device=dispositivo,
        samplerate=taxa,
        channels=1,
        dtype="float32",
        latency="high",
    ) as stream:
        stream.start()
        while total < max_amostras:
            frame, overflow = stream.read(por_frame)
            if overflow:
                # O VAD trabalha por frames de 30ms; perder um significa
                # perder a ordem do áudio, e melhor saber disso no log do
                # que descobrir depois num corte estranho.
                descartes += 1
                log_erro("escuta", f"buffer overflow: frame descartado #{descartes}")
            amostra = frame.reshape(-1)
            blocos.append(amostra)
            total += por_frame

            if detector.processar_frame(amostra):
                continue  # falando, nada a decidir
            # `total` conta amostras e `piso_para_parar` conta segundos.
            if total / taxa >= piso_para_parar and detector.silencio_seguido_seg >= silencios_para_parar:
                break
        stream.stop()

    if descartes:
        log_erro("escuta", f"{descartes} frame(s) perdidos no total")

    if not blocos:
        return np.zeros(0, dtype=np.float32)

    audio = np.concatenate(blocos)
    voz_vad.resumir(audio, taxa, agressividade)
    return audio


def ouvir() -> str:
    modelo = _carregar_modelo()

    max_seg = float(config.get("tempo_escuta_max") or 15)
    silencios = float(config.get("silencios_para_parar") or 1.2)

    with _lock:
        try:
            dispositivo, taxa_nativa = _detectar_dispositivo()

            print(
                f"Ouvindo... (até {max_seg:.0f}s, para {silencios:.1f}s de silêncio)"
            )

            audio = _capturar(
                dispositivo,
                taxa_nativa,
                max_seg,
                silencios,
            )

            if not voz_vad.tem_fala(audio, taxa_nativa):
                print("Nada de fala detectado.")
                return ""

            # Cortar o silêncio de sobra antes do Whisper: ele alucina
            # (repete frase, inventa texto) quando recebe silêncio demais.
            audio = voz_vad.cortar_silencio(audio, taxa_nativa)

            if len(audio) < int(MIN_FALA_SEG * taxa_nativa):
                print("Fala curta demais para transcrever.")
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
    