"""
Nexus Core - Cérebro do Sumé.
Usa IA local (Phi-3) para interpretar intenções e rotear comandos.
"""

import time
from modulos.memoria import processar_memoria
from modulos.memoria import carregar as carregar_memorias
from modulos.automacoes import executar
from modulos.ia_conversacional import conversar
from utils.logger import intent as log_intent, resultado as log_resultado, erro as log_erro
from utils.resultado import Resultado


def _interpretar_comando(comando: str) -> tuple:
    if any(p in comando for p in ["tchau", "sair", "desligar"]):
        return "desligar", ""

    if "hora" in comando:
        return "horas", ""

    if "meu nome é" in comando:
        nome = comando.replace("meu nome é", "").strip()
        return "nome", nome
    if "qual é o meu nome" in comando or "qual o meu nome" in comando:
        return "nome", ""

    if "pasta" in comando:
        alvo = comando.replace("abrir", "").replace("abra", "").replace("abre", "").replace("pasta", "").strip()
        if alvo:
            return "pasta", alvo

    for prefixo in ["abrir ", "abre ", "abra "]:
        if comando.startswith(prefixo):
            alvo = comando[len(prefixo):].strip()
            if alvo:
                return "abrir", alvo

    for prefixo in ["fechar ", "fecha ", "feche "]:
        if comando.startswith(prefixo):
            alvo = comando[len(prefixo):].strip()
            if alvo:
                return "fechar", alvo

    return "conversa", comando


def processar(comando: str) -> str:
    inicio = time.time()
    comando = comando.lower().strip()

    resposta_memoria = processar_memoria(comando)
    if resposta_memoria:
        log_resultado(True, resposta_memoria, (time.time() - inicio) * 1000)
        return resposta_memoria

    acao, alvo = _interpretar_comando(comando)
    log_intent(acao, alvo)

    if acao == "pasta" and alvo:
        resposta = executar(f"pasta {alvo}")
        if resposta:
            log_resultado(True, resposta, (time.time() - inicio) * 1000)
            return resposta

    if acao == "abrir" and alvo:
        resposta = executar(f"abrir {alvo}")
        if resposta:
            log_resultado(True, resposta, (time.time() - inicio) * 1000)
            return resposta

    elif acao == "fechar" and alvo:
        resposta = executar(f"fechar {alvo}")
        if resposta:
            log_resultado(True, resposta, (time.time() - inicio) * 1000)
            return resposta

    elif acao == "horas":
        from datetime import datetime
        resposta = f"São {datetime.now().strftime('%H:%M')}."
        log_resultado(True, resposta, (time.time() - inicio) * 1000)
        return resposta

    elif acao == "nome" and alvo:
        resposta = processar_memoria(f"meu nome é {alvo}")
        log_resultado(True, resposta, (time.time() - inicio) * 1000)
        return resposta

    elif acao == "nome":
        resposta = processar_memoria("qual é o meu nome")
        log_resultado(True, resposta, (time.time() - inicio) * 1000)
        return resposta

    elif acao == "desligar":
        log_resultado(True, "desligar", (time.time() - inicio) * 1000)
        return "desligar"

    try:
        memorias = carregar_memorias()
        nome = memorias.get("nome_usuario") if memorias else None
        resposta = conversar(comando, nome_usuario=nome)
        log_resultado(True, resposta, (time.time() - inicio) * 1000)
        return resposta
    except Exception as e:
        log_erro("nexus_core", str(e))
        return "Desculpe, ocorreu um erro ao processar seu comando."