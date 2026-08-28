"""
Nexus Core - Cérebro do Sumé.
Usa sistema de intenções modulares para interpretar e rotear comandos.
"""

import time
from modulos.memoria import processar_memoria
from modulos.memoria import carregar as carregar_memorias
from modulos.ia_conversacional import conversar
from utils.logger import intent as log_intent, resultado as log_resultado, erro as log_erro
from core.router import rotear
import core.handlers  # registra os handlers no router (import por efeito colateral)

# Sistema de intenções
from core.intents.open_intent import detectar as detect_open
from core.intents.close_intent import detectar as detect_close
from core.intents.time_intent import detectar as detect_time
from core.intents.memory_intent import detectar as detect_memory
from core.intents.exit_intent import detectar as detect_exit
from core.intents.folder_intent import detectar as detect_folder
from core.intents.chat_intent import detectar as detect_chat

INTENTS = [
    detect_exit,
    detect_time,
    detect_memory,
    detect_folder,
    detect_open,
    detect_close,
    detect_chat,  # último, fallback
]


def _interpretar_comando(comando: str) -> tuple:
    """Percorre os detectores de intenção em ordem. O último (chat) sempre retorna."""
    for detector in INTENTS:
        resultado = detector(comando)
        if resultado:
            return resultado
    return ("CHAT", comando, 1.0)


def processar(comando: str) -> str:
    inicio = time.time()
    comando = comando.lower().strip()

    resposta_memoria = processar_memoria(comando)
    if resposta_memoria:
        log_resultado(True, resposta_memoria, (time.time() - inicio) * 1000)
        return resposta_memoria

    acao, alvo, confianca = _interpretar_comando(comando)
    log_intent(acao, alvo)

    resultado = rotear(acao, alvo, comando)
    if resultado is not None:
        log_resultado(resultado.sucesso, resultado.mensagem, (time.time() - inicio) * 1000)
        return resultado.mensagem

    try:
        memorias = carregar_memorias()
        nome = memorias.get("nome_usuario") if memorias else None
        resposta = conversar(comando, nome_usuario=nome)
        log_resultado(True, resposta, (time.time() - inicio) * 1000)
        return resposta
    except Exception as e:
        log_erro("nexus_core", str(e))
        return "Desculpe, ocorreu um erro ao processar seu comando."