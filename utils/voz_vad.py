"""
Detector de atividade de voz (VAD) do Sumé.

Substitui o corte de silêncio por limiar de amplitude global.

O método antigo comparava o pico do áudio inteiro contra 0.02. Isso não tem
relação com o barulho da casa: acima de 0.02 pode estar tanto o dedo batendo
na mesa quanto uma frase inteira, e um único estalo já estourava o corte.

Aqui o áudio é fatiado em frames de 30ms e cada frame recebe três medidas
baratas:

  - energia (RMS)          -> "tem coisa acontecendo?"
  - taxa de mudança de sinal (ZCR) -> descarta zumbido de fonte (50/60Hz)
  - planura espectral      -> descarta chiado broadband

A decisão de quais frames são fala é estatística, feita sobre a gravação
inteira, e não frame a frame isolado. O motivo é concreto: cada medida sozinha
se confunde com alguma coisa.RMS não distingue ventilador de frase fraca; a
planura não distingue ventilador de voz, porque um cooler de CPU é
passa-baixa e liso demais para parecer ruído; o ZCR não distingue quase nada
além de zumbido. Só a comparação entre os frames resolve, porque fala varia
enquanto (pausas entre sílabas) e ruído contínuo é estacionário.

Implementação em numpy puro, sem dependência externa. webrtcvad foi avaliado e
descartado: não publica wheel para cp314 e a venv do projeto é Python 3.14.6.
"""

from collections import deque

import numpy as np

from utils.logger import info as log_info

FRAME_MS = 30

# Multiplicador do piso de ruído, por nível de agressividade. Maior exige
# mais energia acima do ruído: menos falsos positivos, ao custo de poder
# descartar fala baixa ou distante.
AGRESSIVIDADE = {0: 2.2, 1: 3.0, 2: 4.0, 3: 5.5}

# Abaixo disso é silêncio digital, e o ruído não consegue ser medido.
PISO_ABSOLUTO = 1e-4

# Percentis usados para achar o piso de ruído e o topo da fala. O piso sai de
# um percentil baixo (o quarto silencioso da gravação) e o topo de um alto (a
# parte mais alta da frase).
PERCENTIL_PISO = 15
PERCENTIL_TOPO = 95

# Se o topo não for pelo menos este múltiplo do piso, a gravação não tem
# separação entre silêncio e fala: ou é quase tudo fala, ou é quase tudo
# ruído. Nesse caso o limiar deixa de servir e o desempate é outro.
SEPARACAO_MINIMA = 2.5

# Coeficiente de variação dos frames de energia. Fala tem pausa entre sílabas,
# então a energia sobe e desce: o coeficiente é alto. Um ruído contínuo
# (ventilador, zumbido) mantém a energia praticamente constante, e o
# coeficiente fica perto de zero. É isso que separa "gravação vazia" de
# "gravação com frase", quando não dá para usar o limiar.
# Medido: ventilador em 0.06-0.24, voz em 0.44-0.66. Corte em 0.30 fica com
# ~20% de folga para o lado do ruído e ~45% para o lado da voz.
CV_MINIMO = 0.30

# ZCR (zero-crossing rate) de fala medido em 0.015-0.28. Abaixo disso é zumbido
# de fonte/transformador, que quase não troca de sinal; acima disso é chiado.
ZCR_MIN = 0.010
ZCR_MAX = 0.35

# Planura espectral (média geométrica / aritmética dos coeficientes): perto de
# 0 o sinal é tonal, perto de 1 é ruído broadband. Pega o chiado, que é a
# única coisa que energia relativa e ZCR deixam passar.
# Medido: chiado branco e chiado de quarto em 0.49-0.64, voz em 0.007-0.47.
FLATNESS_MAX = 0.45

# Histerese: quantos frames seguidos de fala abrem a janela e quantos de
# silêncio fecham.
#
# Abrir exige 3 frames (90ms) para não abrir num estalo. Fechar é o outro
# lado da moeda e o número mais delicado: os vales do envelope de sílabas
# criam buracos de 4-5 frames (120-150ms) no meio da frase, e a pausa natural
# entre palavras chega a 200-300ms. Com 2 frames de tolerância a frase saía
# picotada em 6 trechos, e nenhum dos trechos contava como fala. Por isso
# fechar exige 0.30s de silêncio contínuo, bem acima da maior pausa
# esperada dentro de uma frase.
# Isso não atrasa o fim da captura: quem decide quando parar é
# `indice_corte_silencio`, com o `silencios_para_parar` de 1.2s do config.
FALA_MIN_CONSECUTIVOS = 3
SILENCIO_MAX_CONSECUTIVOS = 10

# Fala mínima para `tem_fala` aceitar a gravação. Abaixo disso foi ruído ou
# um toque, não uma frase.
MIN_FALA_SEG = 0.12

# Janela que o DetectorVoz carrega para decidir sobre o momento presente.
JANELA_DETECCAO_SEG = 2.0


def tamanho_frame(taxa: int) -> int:
    """Amostras por frame de 30ms, para a taxa de amostragem informada."""
    return max(1, int(round(int(taxa) * FRAME_MS / 1000.0)))


def _planura(espectro: np.ndarray) -> float:
    """Planura espectral de um espectro de potência já calculado."""
    total = float(np.sum(espectro))
    if espectro.size == 0 or total <= 0.0:
        return 1.0
    p = espectro / total
    if not np.all(p > 0):
        return 1.0
    return float(np.exp(np.mean(np.log(p))) / np.mean(p))


def _metricas(frame: np.ndarray) -> tuple:
    """RMS, ZCR e planura de um frame. Vetorizado, sem laço."""
    x = np.asarray(frame, dtype=np.float32).ravel()

    if x.size == 0:
        return PISO_ABSOLUTO, 0.0, 1.0

    rms = float(np.sqrt(np.mean(np.square(x))))

    if x.size < 2:
        return rms, 0.0, 1.0

    # np.signbit devolve bool, então diff conta as trocas de sinal de uma vez.
    zcr = float(np.count_nonzero(np.diff(np.signbit(x)))) / (x.size - 1)

    # Parseval: a energia é a soma dos quadrados dos coeficientes. Somar os
    # módulos e elevar ao quadrado daria um denominador sem sentido e a
    # planura sairia ~480x menor.
    espectro = np.abs(np.fft.rfft(x))[1:] ** 2  # fora o bin DC
    return rms, zcr, _planura(espectro)


def medir(audio: np.ndarray, taxa: int) -> tuple:
    """
    Calcula (rms, zcr, planura) de cada frame completo do áudio.

    O último frame parcial é ignorado: meio frame carrega menos informação que
    os outros e só faria a borda do corte ficar irregular.
    """
    x = np.asarray(audio, dtype=np.float32).ravel()
    tamanho = tamanho_frame(taxa)
    n_frames = len(x) // tamanho

    rms = np.zeros(n_frames, dtype=np.float64)
    zcr = np.zeros(n_frames, dtype=np.float64)
    planura = np.zeros(n_frames, dtype=np.float64)

    for i in range(n_frames):
        rms[i], zcr[i], planura[i] = _metricas(x[i * tamanho : (i + 1) * tamanho])

    return rms, zcr, planura


def decidir(rms, zcr, planura, agressividade: int = 1) -> np.ndarray:
    """
    Decide fala/não-fala por frame a partir das métricas já medidas.

    O caminho normal é: achar o piso de ruído da própria gravação, exigir
    energia acima dele e aplicar os filtros de forma de sinal e planura. O
    caminho especial é quando não há separação entre silêncio e fala, aí a
    estacionariedade é que decide.
    """
    rms = np.asarray(rms, dtype=np.float64)
    zcr = np.asarray(zcr, dtype=np.float64)
    planura = np.asarray(planura, dtype=np.float64)

    if agressividade not in AGRESSIVIDADE:
        raise ValueError(
            f"agressividade inválida: {agressividade} (use {list(AGRESSIVIDADE)})"
        )
    if not rms.size:
        return np.zeros(0, dtype=bool)

    # Zumbido e chiado entram aqui, independente do resto.
    tonal = (zcr >= ZCR_MIN) & (zcr <= ZCR_MAX) & (planura <= FLATNESS_MAX)

    limite_piso = max(PISO_ABSOLUTO, float(np.percentile(rms, PERCENTIL_PISO)))
    limite_topo = float(np.percentile(rms, PERCENTIL_TOPO))

    if limite_topo < limite_piso * SEPARACAO_MINIMA:
        # Sem separação entre silêncio e fala. A gravação é estacionária
        # (ventilador, zumbido) ou é fala do começo ao fim. Voz varia de
        # energia com as pausas entre sílabas; ruído contínuo não varia.
        coeficiente = float(rms.std() / rms.mean()) if rms.mean() > 0 else 0.0
        if coeficiente < CV_MINIMO:
            return np.zeros(rms.size, dtype=bool)
        return tonal

    return (rms >= limite_piso * AGRESSIVIDADE[agressividade]) & tonal


def _suavizar(decisoes: np.ndarray) -> np.ndarray:
    """Histerese: exige fala sustentada para abrir e silêncio para fechar."""
    if not decisoes.size:
        return decisoes

    suavizado = np.zeros(decisoes.size, dtype=bool)
    ativa = False
    fala_seguidos = 0
    silencio_seguidos = 0

    for i, bruto in enumerate(decisoes):
        if bruto:
            fala_seguidos += 1
            silencio_seguidos = 0
        else:
            silencio_seguidos += 1
            fala_seguidos = 0

        if not ativa:
            if fala_seguidos >= FALA_MIN_CONSECUTIVOS:
                ativa = True
        else:
            if silencio_seguidos >= SILENCIO_MAX_CONSECUTIVOS:
                ativa = False

        suavizado[i] = ativa

    return suavizado


def classificar(audio: np.ndarray, taxa: int, agressividade: int = 1) -> np.ndarray:
    """Devolve um bool por frame completo dizendo se o frame é fala."""
    rms, zcr, planura = medir(audio, taxa)
    return _suavizar(decidir(rms, zcr, planura, agressividade))


def _intervalos_fala(decisoes: np.ndarray) -> list:
    """Agrupa os frames de fala em pacotes (início, fim) inclusivos."""
    pacotes = []
    inicio = None
    for i, fala in enumerate(decisoes):
        if fala and inicio is None:
            inicio = i
        elif not fala and inicio is not None:
            pacotes.append((inicio, i - 1))
            inicio = None
    if inicio is not None:
        pacotes.append((inicio, len(decisoes) - 1))
    return pacotes


def tem_fala(audio: np.ndarray, taxa: int, agressividade: int = 1) -> bool:
    """Diz se a gravação tem fala suficiente para valer a transcrição."""
    decisoes = classificar(audio, taxa, agressividade)
    if not decisoes.size:
        return False

    pacotes = _intervalos_fala(decisoes)
    if not pacotes:
        return False

    # A maior sequência de fala precisa passar do piso, senão um estalo único
    # já passaria como frase.
    maior = max(fim - ini + 1 for ini, fim in pacotes)
    return maior * FRAME_MS / 1000.0 >= MIN_FALA_SEG


def cortar_silencio(
    audio: np.ndarray,
    taxa: int,
    margem_inicio_seg: float = 0.6,
    margem_fim_seg: float = 0.3,
    agressividade: int = 1,
) -> np.ndarray:
    """
    Corta o silêncio de antes e de depois da fala, mantendo uma margem.

    A margem do início é maior de propósito: consoante inicial ("Qu", "Tr") tem
    energia baixa e pode ser o primeiro frame a cair, então cortar seco perde o
    começo da primeira palavra.
    """
    x = np.asarray(audio, dtype=np.float32).ravel()
    pacotes = _intervalos_fala(classificar(x, taxa, agressividade))

    if not pacotes:
        return x[:0]

    tamanho = tamanho_frame(taxa)
    primeiro = pacotes[0][0] * tamanho
    ultimo = (pacotes[-1][1] + 1) * tamanho

    inicio = max(0, primeiro - int(margem_inicio_seg * taxa))
    fim = min(len(x), ultimo + int(margem_fim_seg * taxa))
    return x[inicio:fim]


def indice_corte_silencio(
    audio: np.ndarray,
    taxa: int,
    silencios_para_parar: float,
    agressividade: int = 1,
):
    """
    Índice da amostra onde começa um silêncio já sustentado, ou None.

    É o que permite parar a gravação quando a pessoa termina de falar, em vez
    de esperar o tempo fixo no fim. O silêncio contado é o que vem depois do
    último frame de fala, e a suavização evita que a pausa natural entre
    palavras dispare o corte.
    """
    if silencios_para_parar <= 0:
        return None

    decisoes = classificar(audio, taxa, agressividade)
    if not decisoes.size:
        return None

    necessarios = int(silencios_para_parar / (FRAME_MS / 1000.0))
    if necessarios <= 0 or decisoes.size < necessarios:
        return None

    silencio = 0
    for i, fala in enumerate(decisoes):
        if fala:
            silencio = 0
            continue
        silencio += 1
        if silencio >= necessarios:
            # Recua até o último frame de fala: o corte não pode engolir a
            # última palavra, só o silêncio que vem depois dela.
            return (i - silencio + 1) * tamanho_frame(taxa)
    return None


class DetectorVoz:
    """
    VAD para uso durante a captura: alimenta frame a frame e pergunta se o
    momento presente é fala.

    A janela é reprocessada do zero a cada frame em vez de acumular estado
    frame a frame. É o mesmo algoritmo de `decidir`, então o comportamento
    durante a gravação é idêntico ao de `cortar_silencio` depois dela. O custo
    é um FFT por frame dentro da janela de 2s (~66 frames), o que é
    irrelevante para áudio em tempo real.
    """

    def __init__(self, taxa: int, agressividade: int = 1, janela_seg: float = JANELA_DETECCAO_SEG):
        if taxa <= 0:
            raise ValueError(f"taxa de amostragem inválida: {taxa}")
        if agressividade not in AGRESSIVIDADE:
            # Validar aqui e não em `decidir` de propósito: erro no
            # construtor aparece na hora de montar o detector, e não no meio
            # da captura quando o primeiro frame chega.
            raise ValueError(
                f"agressividade inválida: {agressividade} (use {list(AGRESSIVIDADE)})"
            )
        self.taxa = int(taxa)
        self.agressividade = agressividade
        self.amostras_por_frame = tamanho_frame(self.taxa)
        self._capacidade = max(1, int(janela_seg / (FRAME_MS / 1000.0)))
        self._janela = deque(maxlen=self._capacidade)
        self._decisoes = deque(maxlen=self._capacidade)
        self._fala_ativa = False
        self._silencio_seguidos = 0

    @property
    def janela_seg(self) -> float:
        """Quanto de áudio o detector precisa antes de ter uma opinião."""
        return self._capacidade * FRAME_MS / 1000.0

    @property
    def fala_ativa(self) -> bool:
        return self._fala_ativa

    @property
    def silencio_seguido_seg(self) -> float:
        """Silêncio contínuo já medido no fim da janela, em segundos."""
        return self._silencio_seguidos * FRAME_MS / 1000.0

    def reset(self):
        self._janela.clear()
        self._decisoes.clear()
        self._fala_ativa = False
        self._silencio_seguidos = 0

    def _reavaliar(self):
        rms = np.fromiter((m[0] for m in self._janela), dtype=np.float64, count=len(self._janela))
        zcr = np.fromiter((m[1] for m in self._janela), dtype=np.float64, count=len(self._janela))
        plan = np.fromiter((m[2] for m in self._janela), dtype=np.float64, count=len(self._janela))
        novas = _suavizar(decidir(rms, zcr, plan, self.agressividade))
        self._decisoes = deque(novas.tolist(), maxlen=self._capacidade)

    def processar_frame(self, frame: np.ndarray) -> bool:
        """Acrescenta um frame e devolve se o momento presente é fala."""
        self._janela.append(_metricas(frame))
        self._reavaliar()
        self._fala_ativa = bool(self._decisoes[-1]) if self._decisoes else False

        if self._fala_ativa:
            self._silencio_seguidos = 0
        else:
            self._silencio_seguidos += 1

        return self._fala_ativa


def resumir(audio: np.ndarray, taxa: int, agressividade: int = 1) -> str:
    """Log de uma linha com o que o VAD decidiu. Ajuda a depurar no campo."""
    decisoes = classificar(audio, taxa, agressividade)
    pacotes = _intervalos_fala(decisoes)
    total = decisoes.size * FRAME_MS / 1000.0

    if not pacotes:
        log_info("vad", f"nenhuma fala em {total:.2f}s ({decisoes.size} frames)")
        return ""

    fala = sum(fim - ini + 1 for ini, fim in pacotes) * FRAME_MS / 1000.0
    log_info(
        "vad",
        f"fala {fala:.2f}s em {total:.2f}s, {len(pacotes)} trecho(s)",
    )
    return f"{len(pacotes)}"
