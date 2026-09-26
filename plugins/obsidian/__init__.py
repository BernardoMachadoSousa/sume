from .intents import detectar

intents = [detectar]

DESCRICAO_ACAO = {
    "OBSIDIAN_SEARCH": "pesquisar nas suas anotações do Obsidian"
}

# Inicializa o registro de handlers deste plugin
from . import handlers
