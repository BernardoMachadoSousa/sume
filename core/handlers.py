"""
Handlers de cada ação de intenção do Sumé.
Cada função trata uma ação específica e devolve um Resultado (ou None,
se não conseguiu tratar - nesse caso o nexus_core cai no fallback de conversa).
"""
from datetime import datetime
from core.router import registrar
from modulos.automacoes import executar
from modulos.memoria import processar_memoria
from utils.resultado import Resultado


@registrar("OPEN_FOLDER")
def _abrir_pasta(alvo: str, comando: str):
    if not alvo:
        return None
    resposta = executar(f"pasta {alvo}")
    if not resposta:
        return None  # preserva comportamento antigo: cai no fallback de chat
    return Resultado(True, resposta)


@registrar("OPEN_APP")
def _abrir_app(alvo: str, comando: str):
    if not alvo:
        return None
    resposta = executar(f"abrir {alvo}")
    if not resposta:
        return None
    return Resultado(True, resposta)


@registrar("CLOSE_APP")
def _fechar_app(alvo: str, comando: str):
    if not alvo:
        return None
    resposta = executar(f"fechar {alvo}")
    if not resposta:
        return None
    return Resultado(True, resposta)


@registrar("GET_TIME")
def _get_time(alvo: str, comando: str):
    resposta = f"São {datetime.now().strftime('%H:%M')}."
    return Resultado(True, resposta)


@registrar("MEMORY_SAVE")
def _memory_save(alvo: str, comando: str):
    if not alvo:
        return None
    resposta = processar_memoria(f"meu nome é {alvo}")
    return Resultado(True, resposta)


@registrar("MEMORY_READ")
def _memory_read(alvo: str, comando: str):
    resposta = processar_memoria("qual é o meu nome")
    return Resultado(True, resposta)


@registrar("EXIT")
def _exit(alvo: str, comando: str):
    return Resultado(True, "desligar")
