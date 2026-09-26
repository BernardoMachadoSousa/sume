"""
Teste do VAD de voz (ETAPA 3).
Não depende de microfone nem de Ollama - todo o áudio é sintético.
Execute: python testes/teste_vad.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contextlib import contextmanager

from utils.console import configurar_console
configurar_console()  # antes de qualquer print, senão o emoji derruba o script

import numpy as np

import utils.voz_vad as vad
from utils.voz_vad import DetectorVoz, classificar, tem_fala, cortar_silencio, indice_corte_silencio

erros = []
TAXA = 16000
GERADOR = np.random.default_rng(42)  # semente fixa: o teste é reprodutível


# --- Sinais sintéticos ------------------------------------------------------
# Os limiares do VAD (CV_MINIMO, ZCR_MIN/MAX, FLATNESS_MAX) foram calibrados
# contra estes mesmos geradores. Ao mexer num limiar, rode este arquivo: ele
# imprime as medidas de cada caso, então dá para ver o que saiu do lugar.

def silencio(seg, nivel=0.0):
    """Silêncio digital ou chiado de quarto."""
    n = int(TAXA * seg)
    if nivel <= 0:
        return np.zeros(n, dtype=np.float32)
    return (GERADOR.standard_normal(n) * nivel).astype(np.float32)


def voz(seg, f0=120.0, harmônicos=40, amplitude=0.15, fricacao=0.12, silabas=True, taxa=TAXA):
    """
    Voz sintética: f0 com harmônicas em inclinação 1/k, amplitude modulada por
    um envelope de sílabas (~4Hz) e uma camada de fricação. É a modulação que
    dá ao sinal a variação de energia que separa voz de ruído contínuo.
    """
    n = int(taxa * seg)
    t = np.arange(n) / taxa
    sinal = np.zeros(n, dtype=np.float64)
    for k in range(1, harmônicos + 1):
        sinal += np.sin(2 * np.pi * f0 * k * t) / k
    envelope = 0.5 * (1 + np.sin(2 * np.pi * 4.0 * t)) if silabas else np.ones(n)
    sinal = sinal * envelope * amplitude
    ar = GERADOR.standard_normal(n)
    ar = ar - np.convolve(ar, np.ones(5) / 5, mode="same")  # realça agudos
    return (sinal + ar * (amplitude * fricacao)).astype(np.float32)


def zumbido(seg, hz=60.0, amplitude=0.08):
    """Ruído de fonte/transformador: quase não troca de sinal."""
    n = int(TAXA * seg)
    t = np.arange(n) / TAXA
    return (amplitude * np.sin(2 * np.pi * hz * t)).astype(np.float32)


def ventilador(seg, janela=20, amplitude=0.05):
    """Cooler de CPU: ruído passa-baixa, liso, energia constante."""
    n = int(TAXA * seg)
    bruto = GERADOR.standard_normal(n)
    filtrado = np.convolve(bruto, np.ones(janela) / janela, mode="same")
    filtrado = filtrado / (np.max(np.abs(filtrado)) + 1e-9)
    return (filtrado * amplitude).astype(np.float32)


def chiado(seg, amplitude=0.05):
    """Chiado de alta frequência: broadband, troca de sinal toda amostra."""
    return (GERADOR.standard_normal(int(TAXA * seg)) * amplitude).astype(np.float32)


def estalo(seg, duracao_seg=0.01, amplitude=0.9):
    """Estalo único e alto - o caso que enganava o limiar global de pico."""
    sinal = silencio(seg)
    inicio = int(TAXA * 0.5)
    sinal[inicio:inicio + int(TAXA * duracao_seg)] = amplitude
    return sinal


# --- Helpers ----------------------------------------------------------------

def checar(nome, condicao, detalhe=""):
    if condicao:
        print(f"✅ {nome}")
    else:
        print(f"❌ {nome}")
        if detalhe:
            print(f"   {detalhe}")
        erros.append(nome)


def medida(audio):
    """rms médio, coeficiente de variação, piso e topo - só para diagnóstico."""
    rms, zcr, planura = vad.medir(audio, TAXA)
    cv = float(rms.std() / rms.mean()) if rms.mean() > 0 else 0.0
    piso = max(vad.PISO_ABSOLUTO, float(np.percentile(rms, vad.PERCENTIL_PISO))) if rms.size else 0.0
    topo = float(np.percentile(rms, vad.PERCENTIL_TOPO)) if rms.size else 0.0
    return rms.mean(), cv, piso, topo, topo / piso if piso > 0 else 0.0


def como_mock(decisoes, funcao, *args, **kwargs):
    """Roda `funcao` com a decisão do VAD trocada por uma pré-definida."""
    original = vad.classificar

    def falso(audio, taxa, agressividade=1):
        return decisoes

    vad.classificar = falso
    try:
        return funcao(*args, **kwargs)
    finally:
        vad.classificar = original


print("=" * 68)
print("TESTE: VAD de voz (frames de 30ms)")
print(f"frame={vad.tamanho_frame(TAXA)} amostras  CV_MINIMO={vad.CV_MINIMO}  "
      f"ZCR={vad.ZCR_MIN}-{vad.ZCR_MAX}  FLATNESS_MAX={vad.FLATNESS_MAX}")
print("=" * 68)

# ---------------------------------------------------------------------------
# 1. Ruído não é fala
# ---------------------------------------------------------------------------
print("\n--- 1. o que NÃO é fala ---")
for nome, sinal in [
    ("silêncio digital", silencio(2.0)),
    ("chiado de quarto (-46dB)", chiado(2.0, 0.002)),
    ("chiado forte (0.02)", chiado(2.0, 0.02)),
    ("chiado branco (0.05)", chiado(2.0, 0.05)),
    ("zumbido 60Hz", zumbido(2.0, 60, 0.08)),
    ("zumbido 50Hz alto", zumbido(2.0, 50, 0.20)),
    ("ventilador (j=5)", ventilador(2.0, 5)),
    ("ventilador (j=20)", ventilador(2.0, 20)),
    ("ventilador (j=100)", ventilador(2.0, 100)),
    ("estalo único", estalo(2.0)),
]:
    rms, cv, piso, topo, sep = medida(sinal)
    checar(f"{nome} -> sem fala", not tem_fala(sinal, TAXA),
           f"rms={rms:.5f} cv={cv:.3f} sep={sep:.2f}")

# ---------------------------------------------------------------------------
# 2. Fala é fala
# ---------------------------------------------------------------------------
print("\n--- 2. o que É fala ---")
for nome, sinal in [
    ("voz normal", voz(1.2)),
    ("voz só harmônica", voz(1.2, fricacao=0.0)),
    ("voz com fricação forte", voz(1.2, fricacao=0.25)),
    ("voz aguda (f0=210)", voz(1.2, f0=210.0)),
    ("voz fraca (amp=0.03)", voz(1.2, amplitude=0.03)),
]:
    rms, cv, piso, topo, sep = medida(sinal)
    checar(f"{nome} -> tem fala", tem_fala(sinal, TAXA),
           f"rms={rms:.5f} cv={cv:.3f} sep={sep:.2f}")

# ---------------------------------------------------------------------------
# 3. Ruído de fundo não pode apagar a fala
#    Este é o ponto central da Etapa 3: o método antigo comparava o pico do
#    áudio com 0.02 fixo, então dependia do volume da casa.
# ---------------------------------------------------------------------------
print("\n--- 3. voz sobre ruído ---")
for nome, sinal in [
    ("ventilador + voz", ventilador(1.2, 20) + voz(1.2)),
    ("zumbido + voz", zumbido(1.2, 60, 0.08) + voz(1.2)),
    ("chiado 0.02 + voz", chiado(1.2, 0.02) + voz(1.2)),
]:
    rms, cv, piso, topo, sep = medida(sinal)
    checar(f"{nome} -> tem fala", tem_fala(sinal, TAXA),
           f"rms={rms:.5f} cv={cv:.3f} sep={sep:.2f}")

# O VAD é relativo: a mesma voz, agora com o ruído bem mais alto, continua
# achada. O teste antigo usava ruído 2.3x mais forte que a voz, e aí o VAD
# acertava em não achar - ninguém ouve fala 2.5dB abaixo do chiado.
sala_cheia = chiado(1.2, 0.03) + voz(1.2)
rms_voz = float(np.sqrt(np.mean(np.square(voz(1.2)))))
rms_sala = float(np.sqrt(np.mean(np.square(chiado(1.2, 0.03)))))
checar(f"voz sob ruído de sala ({20*np.log10(rms_voz/rms_sala):.0f}dB de SNR) -> tem fala",
       tem_fala(sala_cheia, TAXA),
       f"voz={rms_voz:.4f} ruido={rms_sala:.4f}")

# ---------------------------------------------------------------------------
# 4. O corte pega a fala, não o barulho
# ---------------------------------------------------------------------------
print("\n--- 4. o corte isola a fala ---")
inicio_verdadeiro = 1.0
duracao_fala = 1.2
montado = np.concatenate([
    ventilador(1.0, 20),                      # 1.0s de ventilador
    voz(duracao_fala),                        # 1.2s de fala
    ventilador(1.0, 20),                      # 1.0s de ventilador
])
cortado = cortar_silencio(montado, TAXA)
tamanho = vad.tamanho_frame(TAXA)
esperado = int(duracao_fala * TAXA)
# A histerese estende a fala até 0.30s para dentro do silêncio em cada ponta
# antes de declarar o fim, e aí ainda vêm as margens de 0.6s e 0.3s. O teto
# é fala + 2x(0.30+0.30) + margens + uma frame de arredondamento.
teto = esperado + int(2 * (vad.SILENCIO_MAX_CONSECUTIVOS * vad.FRAME_MS / 1000.0) * TAXA) \
    + int((0.6 + 0.3) * TAXA) + tamanho
checar("corte tem o tamanho da fala + histerese + margens",
       esperado <= len(cortado) <= teto,
       f"fala={esperado}, teto={teto}, corte={len(cortado)}")
checar("corte não devolve a gravação inteira", len(cortado) < len(montado))
checar("corte não é vazio", len(cortado) > 0)
rms_antes = float(np.sqrt(np.mean(np.square(montado))))
rms_depois = float(np.sqrt(np.mean(np.square(cortado))))
checar("corte reduz a energia média (tirou silêncio)", rms_depois > rms_antes,
       f"antes={rms_antes:.5f} depois={rms_depois:.5f}")

# ---------------------------------------------------------------------------
# 5. Histerese: a pausa entre palavras não corta a frase
# ---------------------------------------------------------------------------
print("\n--- 5. histerese ---")
# A pausa entre palavras fica em 0.2-0.3s. A histerese tem de atravessá-la, ou
# a frase sai picotada e nenhuma parte conta como fala.
pausa_curta = int(0.2 * 1000 / vad.FRAME_MS)
pausa = np.concatenate([voz(0.5), silencio(0.2), voz(0.5)])
checar("pausa de 0.2s não pica a frase",
       len(vad._intervalos_fala(classificar(pausa, TAXA))) == 1,
       f"pausa={pausa_curta} frames, "
       f"trechos={len(vad._intervalos_fala(classificar(pausa, TAXA)))}")

# Pausa longa (0.6s) é fim de turno mesmo, e aí sim tem de separar.
longa = np.concatenate([voz(0.5), silencio(0.6), voz(0.5)])
checar("pausa de 0.6s separa os trechos",
       len(vad._intervalos_fala(classificar(longa, TAXA))) == 2,
       f"trechos={len(vad._intervalos_fala(classificar(longa, TAXA)))}")

# Um frame perdido no meio da fala não pode abrir um buraco: é o que a
# tolerância a pausas compra.
com_buraco = voz(1.0)
F = vad.tamanho_frame(TAXA)
interrompido = np.concatenate([
    com_buraco[:10 * F], silencio(0.06), com_buraco[11 * F:]
])
checar("frame perdido não abre buraco",
       len(vad._intervalos_fala(classificar(interrompido, TAXA))) == 1,
       f"trechos={len(vad._intervalos_fala(classificar(interrompido, TAXA)))}")

# ---------------------------------------------------------------------------
# 6. A matemática do corte com a decisão do VAD mockada
#    É este bloco que o documento afirmava existir.
# ---------------------------------------------------------------------------
print("\n--- 6. corte com decisão de VAD mockada ---")

total_frames = int(5.0 * 1000 / vad.FRAME_MS)
# A fala começa no frame 5, e não no 0, por dois motivos: a margem da frente
# (0.6s) precisa de silêncio à esquerda para cair dentro, e a parada
# antecipada com 0.3s pedidos dispararia logo no começo se o mock devolvesse
# silêncio no início.
fala_inicio = 5
fala_fim = 54
decisoes = np.zeros(total_frames, dtype=bool)
decisoes[fala_inicio:fala_fim + 1] = True

# Áudio com marcador: 0.5 na região de fala, 0.0 no silêncio. Dá para conferir
# se o corte preservou a fala e se as margens caíram no silêncio.
marcado = np.zeros(total_frames * tamanho, dtype=np.float32)
marcado[fala_inicio * tamanho : (fala_fim + 1) * tamanho] = 0.5

margem_ini, margem_fim = 0.6, 0.3
esperado_ini = max(0, fala_inicio * tamanho - int(margem_ini * TAXA))
esperado_fim = min(len(marcado), (fala_fim + 1) * tamanho + int(margem_fim * TAXA))

corte = como_mock(decisoes, cortar_silencio, marcado, TAXA, margem_ini, margem_fim)
checar("comprimento = fala + margens exatas", len(corte) == esperado_fim - esperado_ini,
       f"esperado {esperado_fim - esperado_ini}, obtido {len(corte)}")
checar("a fala dentro do corte sobreviveu", corte.size and float(corte.max()) == 0.5)
checar("a margem da frente caiu no silêncio", corte.size and float(corte[0]) == 0.0)
checar("a margem de trás caiu no silêncio", corte.size and float(corte[-1]) == 0.0)

# Sem fala nenhuma: tem de devolver vazio, não o áudio.
vazio = como_mock(np.zeros(total_frames, dtype=bool), cortar_silencio, marcado, TAXA)
checar("sem fala nenhuma -> corte vazio", len(vazio) == 0)

# Fala no fim inteiro: a margem de trás não pode estourar o áudio.
cheio = np.ones(total_frames, dtype=bool)
corte_cheio = como_mock(cheio, cortar_silencio, marcado, TAXA)
checar("fala ocupando tudo não gera corte maior que o áudio",
       0 < len(corte_cheio) <= len(marcado))

# ---------------------------------------------------------------------------
# 7. Parada antecipada no silêncio
# ---------------------------------------------------------------------------
print("\n--- 7. índice de corte no silêncio ---")

# O índice aponta para o COMEÇO do silêncio final, não para o momento em que
# o pedido foi cumprido. Por isso subir o tempo pedido não muda o índice: ele
# só decide se o corte acontece ou não.
idx = como_mock(decisoes, indice_corte_silencio, marcado, TAXA, 0.3)
checar("corte começa no primeiro frame após a fala",
       idx == (fala_fim + 1) * tamanho, f"esperado {(fala_fim + 1) * tamanho}, obtido {idx}")
idx_mais = como_mock(decisoes, indice_corte_silencio, marcado, TAXA, 0.4)
checar("o índice é o começo do silêncio, não o ponto de disparo",
       idx_mais == idx, f"0.3s->{idx}  0.4s->{idx_mais}")

# Silêncio que nunca chega ao tempo pedido: não corta.
idx_curto = como_mock(decisoes, indice_corte_silencio, marcado, TAXA, 5.0)
checar("silêncio menor que o pedido -> sem corte", idx_curto is None)

# Fala até o fim: sem silêncio depois, não corta.
idx_sem_fim = como_mock(cheio, indice_corte_silencio, marcado, TAXA, 0.3)
checar("fala até o fim -> sem corte", idx_sem_fim is None)

# Valor zero desliga a funcionalidade (não corta no primeiro frame).
checar("silencios_para_parar=0 -> sem corte",
       como_mock(decisoes, indice_corte_silencio, marcado, TAXA, 0.0) is None)

# ---------------------------------------------------------------------------
# 8. DetectorVoz incremental bate com o caminho offline
# ---------------------------------------------------------------------------
print("\n--- 8. DetectorVoz durante a captura ---")
det = DetectorVoz(TAXA)
frames = [
    ventilador(1.0, 20),
    voz(1.2),
    ventilador(1.0, 20),
]
total_amostras = sum(len(a) for a in frames)
capturado = np.concatenate(frames)

visto_fala = False
for pos in range(0, total_amostras - tamanho, tamanho):
    if det.processar_frame(capturado[pos:pos + tamanho]):
        visto_fala = True
checar("DetectorVoz vê a fala durante a captura", visto_fala)
checar("DetectorVoz reporta silêncio sustentado no fim",
       det.silencio_seguido_seg > 0.3, f"silêncio medido {det.silencio_seguido_seg:.2f}s")

# O final do buffer é ventilador, então o detector tem de estar em silêncio.
checar("DetectorVoz termina em silêncio", not det.fala_ativa)
det.reset()
checar("reset limpa o estado", not det.fala_ativa and det.silencio_seguido_seg == 0)

# Entrada inválida tem de dar erro claro, não exceção genérica. A
# agressividade é validada no construtor, e não só na hora de decidir.
for ruim, em_que in [((TAXA, 99), "agressividade inválida"), ((0, 1), "taxa inválida")]:
    try:
        DetectorVoz(*ruim)
        checar(f"{em_que} levanta erro", False, "não levantou nada")
    except ValueError:
        checar(f"{em_que} levanta erro", True)
for ok in (0, 1, 2, 3):
    DetectorVoz(TAXA, ok)
    checar(f"agressividade {ok} é aceita", True)

# ---------------------------------------------------------------------------
# 9. Limitações conhecidas (documentadas, não bugs)
# ---------------------------------------------------------------------------
print("\n--- 9. limitações conhecidas ---")
# Um tom contínuo sem variação é estacionário, e estacionário o VAD trata
# como ruído. Voz real sempre varia com as pausas entre sílabas, então isto
# não afeta fala de verdade.
tom = voz(1.2, silabas=False)
checar("tom contínuo sem sílabas -> tratado como ruído (limitação conhecida)",
       not tem_fala(tom, TAXA))

# Buffer mais curto que um frame não pode quebrar.
checar("áudio menor que um frame -> sem fala", not tem_fala(np.zeros(10, dtype=np.float32), TAXA))
checar("áudio vazio -> sem fala", not tem_fala(np.array([], dtype=np.float32), TAXA))
checar("corte de áudio vazio não quebra", len(cortar_silencio(np.array([], dtype=np.float32), TAXA)) == 0)

# ---------------------------------------------------------------------------
# 10. Entradas com outro formato de áudio
# ---------------------------------------------------------------------------
print("\n--- 10. formatos de entrada ---")
# O sounddevice entrega (n, 1); o VAD tem de aceitar.
plano = voz(1.2)
coluna = plano.reshape(-1, 1)
checar("áudio (n,1) do sounddevice é aceito", tem_fala(coluna, TAXA))
checar("mesmo áudio em 1D dá o mesmo resultado",
       np.array_equal(classificar(plano, TAXA), classificar(coluna, TAXA)))
# 48kHz é o outro samplerate comum em notebook. O VAD tem de se adaptar
# porque o frame precisa continuar valendo 30ms, e não 480 amostras.
taxa48 = 48000
voz48 = voz(1.2, taxa=taxa48)
checar("funciona a 48kHz", tem_fala(voz48, taxa48))
checar("frame de 30ms escala com a taxa",
       vad.tamanho_frame(48000) == 3 * vad.tamanho_frame(16000),
       f"16k={vad.tamanho_frame(16000)} 48k={vad.tamanho_frame(48000)}")

# Invariante da agressividade: permissiva (0) tem de detectar pelo menos
# tantos frames quanto a estrita (3). Não testa um caso específico, testa a
# ordem entre os níveis, que é a garantia que importa.
borda = voz(1.2, amplitude=0.03) + chiado(1.2, 0.05)
detectado = [int(classificar(borda, TAXA, n).sum()) for n in (0, 1, 2, 3)]
checar("agressividade 0 é a mais permissiva",
       detectado == sorted(detectado, reverse=True),
       f"frames detectados por nível 0..3: {detectado}")
try:
    classificar(borda, TAXA, 9)
    checar("agressividade 9 é rejeitada", False, "não levantou nada")
except ValueError:
    checar("agressividade 9 é rejeitada", True)

# ---------------------------------------------------------------------------
# 11. O loop de captura de utils/escuta.py
#     As seções 1-10 provam que o VAD decide certo. Esta prova que a captura
#     usa essa decisão para parar no momento certo, sem depender de microfone.
# ---------------------------------------------------------------------------
print("\n--- 11. loop de captura (stream falso) ---")

from utils import escuta  # noqa: E402  (vem depois do console; é lento)


class StreamFalso:
    """Faz as vezes do sd.InputStream servindo um áudio combinado."""

    def __init__(self, sinal, por_frame, overflow=False):
        self._sinal = sinal
        self._por_frame = por_frame
        self._pos = 0
        self._overflow = overflow
        self.iniciado = False
        self.parado = False

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def start(self):
        self.iniciado = True

    def stop(self):
        self.parado = True

    def read(self, n):
        bloco = self._sinal[self._pos:self._pos + n]
        self._pos += n
        if len(bloco) < n:
            # microfone de verdade devolve silêncio quando não tem nada
            bloco = np.pad(bloco, (0, n - len(bloco)))
        return bloco.reshape(-1, 1).astype(np.float32), self._overflow


@contextmanager
def microfone_falso(sinal, taxa, overflow=False):
    """Troca o sounddevice por um stream controlado durante o bloco."""
    real = escuta.sd
    por_frame = vad.tamanho_frame(taxa)
    criado = {}

    class SdFalso:
        @staticmethod
        def InputStream(**kwargs):
            criado["stream"] = StreamFalso(sinal, por_frame, overflow)
            return criado["stream"]

    escuta.sd = SdFalso
    try:
        yield criado
    finally:
        escuta.sd = real


def captura(sinal, max_seg, silencios, taxa=TAXA, overflow=False):
    with microfone_falso(sinal, taxa, overflow) as criado:
        audio = escuta._capturar(0, taxa, max_seg, silencios)
    return audio, criado.get("stream")


FRAME_SEG = vad.FRAME_MS / 1000.0
MAX = 4.0
SIL = 0.5
PISO = vad.JANELA_DETECCAO_SEG + SIL

# Fala e depois silêncio: tem de parar no piso, não esperar o tempo máximo.
audio, stream = captura(np.concatenate([voz(1.2), ventilador(3.0, 20)]), MAX, SIL)
dur = len(audio) / TAXA
checar("fala seguida de silêncio para no piso (janela + silencios)",
       PISO - FRAME_SEG <= dur <= PISO + FRAME_SEG,
       f"esperado ~{PISO:.2f}s, parou em {dur:.2f}s")
checar("parou antes do tempo máximo", dur < MAX - 0.1, f"parou em {dur:.2f}s")
checar("o áudio capturado contém a fala", tem_fala(audio, TAXA))
checar("o stream foi aberto e fechado", stream.iniciado and stream.parado)

# Fala sem parar: tem de ir até o tempo máximo.
audio, _ = captura(voz(3.9), MAX, SIL)
dur = len(audio) / TAXA
checar("fala contínua vai até o tempo máximo", abs(dur - MAX) < 0.05,
       f"esperado {MAX}s, gravou {dur:.2f}s")

# Ninguém falando: não pode segurar o microfone por 15s à toa.
audio, _ = captura(ventilador(3.0, 20), MAX, SIL)
dur = len(audio) / TAXA
checar("sem fala nenhuma também para no piso", abs(dur - PISO) < 0.05,
       f"esperado {PISO:.2f}s, gravou {dur:.2f}s")
checar("e o VAD diz que não tem fala", not tem_fala(audio, TAXA))

# O piso existe para o caso em que o usuário ainda não começou a falar: sem
# ele, o VAD contaria o preenchimento da própria janela como silêncio e
# encerraria a captura antes de o usuário abrir a boca.
with microfone_falso(silencio(0.4), TAXA):
    audio = escuta._capturar(0, TAXA, MAX, 0.1)
dur = len(audio) / TAXA
checar("captura não encerra antes da janela encher",
       dur >= vad.JANELA_DETECCAO_SEG,
       f"parou em {dur:.2f}s com a janela em {vad.JANELA_DETECCAO_SEG:.1f}s")

# Buffer overflow tem de ser registrado, não engolido em silêncio.
with microfone_falso(voz(1.0), TAXA, overflow=True):
    escuta._capturar(0, TAXA, 1.5, 5.0)
checar("buffer overflow não trava a captura", True)

print("=" * 68)
if erros:
    print(f"❌ {len(erros)} FALHA(S):")
    for e in erros:
        print(f"   - {e}")
    sys.exit(1)
else:
    print("✅ TODOS OS TESTES PASSARAM!")
print("=" * 68)
