from .intents import detectar

intents = [detectar]

DESCRICAO_ACAO = {
    "WEB_SEARCH": "pesquisar informações em tempo real na Internet"
}

from . import handlers
