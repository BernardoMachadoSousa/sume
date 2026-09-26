from .intents import detectar

intents = [detectar]

DESCRICAO_ACAO = {
    "SYSTEM_MEDIA": "controlar o som e as mídias do computador"
}

from . import handlers