from .intents import detectar

intents = [detectar]

DESCRICAO_ACAO = {
    "GET_WEATHER": "verificar o clima e a previsão do tempo"
}

from . import handlers