"""
Plugin de busca para o Sumé.
Fornece capacidades de busca semântica nas notas e busca inteligente no computador.
"""

import re
from .intents import INTENTS

def _detectar_busca(comando: str) -> tuple:
    """
    Detecta se o comando corresponde a um intent de busca.
    Retorna (acao, alvo, confianca) ou None se não há match.
    """
    comando_lower = comando.lower().strip()
    
    for acao, padroes in INTENTS.items():
        for padrao in padroes:
            if re.search(padrao, comando_lower):
                alvo = comando_lower
                confianca = 0.85
                return (acao, alvo, confianca)
    
    return None

intents = [_detectar_busca]

DESCRICAO_ACAO = {
    "BUSCAR_NOTAS": "buscar nas minhas anotacoes",
    "BUSCAR_ARQUIVOS": "buscar arquivos no computador"
}