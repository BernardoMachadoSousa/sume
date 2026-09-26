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


@registrar("GET_DATE")
def _get_date(alvo: str, comando: str):
    import locale
    agora = datetime.now()
    dias = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
            "sexta-feira", "sábado", "domingo"]
    meses = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
             "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
    dia_semana = dias[agora.weekday()]
    mes = meses[agora.month - 1]
    resposta = f"Hoje é {dia_semana}, {agora.day} de {mes} de {agora.year}."
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


@registrar("REMINDER_SET")
def _reminder_set(alvo: str, comando: str):
    from modulos.lembretes import criar
    return Resultado(True, criar(alvo or comando))


@registrar("REMINDER_LIST")
def _reminder_list(alvo: str, comando: str):
    from modulos.lembretes import listar
    return Resultado(True, listar())


@registrar("REMINDER_CANCEL")
def _reminder_cancel(alvo: str, comando: str):
    from modulos.lembretes import cancelar
    return Resultado(True, cancelar(alvo))


@registrar("EXIT")
def _exit(alvo: str, comando: str):
    return Resultado(True, "desligar")
