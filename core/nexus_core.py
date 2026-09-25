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

# Chat não entra na lista: é o fallback explícito quando nada mais serve
# (ver _interpretar_comando), não mais um detector que "sempre bate".
INTENTS = [
    detect_exit,
    detect_time,
    detect_memory,
    detect_folder,
    detect_open,
    detect_close,
]

# Abaixo desse valor, nenhum candidato é confiável o bastante: cai pro chat.
LIMIAR_CONFIANCA_MINIMA = 0.5

# Se os dois melhores candidatos são ações diferentes e a diferença de
# confiança entre eles é menor que isso, não dá pra decidir sozinho -
# é ambiguidade real, não escolha arbitrária de ordem de lista.
LIMIAR_AMBIGUIDADE = 0.15

# Descrição em linguagem natural de cada ação, usada só pra montar a
# pergunta de esclarecimento quando há ambiguidade.
_DESCRICAO_ACAO = {
    "OPEN_APP": "abrir um aplicativo",
    "OPEN_FOLDER": "abrir uma pasta",
    "CLOSE_APP": "fechar um aplicativo",
    "GET_TIME": "saber as horas",
    "MEMORY_SAVE": "salvar seu nome",
    "MEMORY_READ": "lembrar seu nome",
    "EXIT": "encerrar o Sumé",
}


def _interpretar_comando(comando: str) -> tuple:
    """
    Roda TODOS os detectores (não para no primeiro que bater), escolhe o de
    maior confiança. Se o melhor for fraco demais, cai no chat. Se os dois
    melhores forem ações diferentes e muito próximos em confiança, devolve
    ambiguidade em vez de chutar um dos dois.
    """
    candidatos = [r for r in (detector(comando) for detector in INTENTS) if r]

    if not candidatos:
        return ("CHAT", comando, 1.0)

    candidatos.sort(key=lambda c: c[2], reverse=True)
    melhor = candidatos[0]

    if melhor[2] < LIMIAR_CONFIANCA_MINIMA:
        return ("CHAT", comando, 1.0)

    if len(candidatos) > 1:
        segundo = candidatos[1]
        if melhor[0] != segundo[0] and (melhor[2] - segundo[2]) <= LIMIAR_AMBIGUIDADE:
            return ("AMBIGUOUS", candidatos[:3], melhor[2])

    return melhor


def _pergunta_ambiguidade(candidatos: list) -> str:
    """Monta a pergunta de esclarecimento a partir dos candidatos ambíguos."""
    descricoes = []
    for acao, _alvo, _conf in candidatos:
        desc = _DESCRICAO_ACAO.get(acao, acao)
        if desc not in descricoes:
            descricoes.append(desc)
    if len(descricoes) == 1:
        # Mesma ação com alvos diferentes (ex.: dois nomes parecidos) - caso
        # raro hoje, mas a função fica pronta pra isso.
        return "Não entendi direito o que você quer dizer. Pode reformular?"
    opcoes = " ou ".join(descricoes)
    return f"Não tenho certeza se você quer {opcoes}. Pode ser mais específico?"


def processar(comando: str) -> str:
    inicio = time.time()
    comando = comando.lower().strip()

    resposta_memoria = processar_memoria(comando)
    if resposta_memoria:
        log_resultado(True, resposta_memoria, (time.time() - inicio) * 1000)
        return resposta_memoria

    acao, alvo, confianca = _interpretar_comando(comando)

    if acao == "AMBIGUOUS":
        candidatos = alvo  # lista de (acao, alvo, confianca) - ver _interpretar_comando
        log_intent("AMBIGUOUS", str([c[0] for c in candidatos]), confianca)
        resposta = _pergunta_ambiguidade(candidatos)
        log_resultado(True, resposta, (time.time() - inicio) * 1000)
        return resposta

    log_intent(acao, alvo, confianca)

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