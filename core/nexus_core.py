"""
Nexus Core - Cérebro do Sumé.
Usa sistema de intenções modulares para interpretar e rotear comandos.
Auto-descobre plugins na pasta plugins/
"""

import time
import os
import sys
import importlib
from modulos.memoria import processar_memoria
from modulos.memoria import carregar as carregar_memorias
from modulos.ia_conversacional import conversar
from utils.logger import intent as log_intent, resultado as log_resultado, erro as log_erro
from core.router import rotear

_INTENTS_DINAMICOS = []
_DESCRICAO_ACAO = {} 

def carregar_intencoes_automaticamente():
    global _INTENTS_DINAMICOS, _DESCRICAO_ACAO
    _INTENTS_DINAMICOS = []
    
    # 1. Carrega os do core/intents/
    pasta_intents = os.path.join(os.path.dirname(__file__), "intents")
    if os.path.exists(pasta_intents):
        for arquivo in os.listdir(pasta_intents):
            if arquivo.endswith(".py") and not arquivo.startswith("__"):
                nome_modulo = f"core.intents.{arquivo[:-3]}"
                try:
                    modulo = importlib.import_module(nome_modulo)
                    if hasattr(modulo, "detectar"):
                        _INTENTS_DINAMICOS.append(modulo.detectar)
                except Exception as e:
                    log_erro("nexus_core_loader", f"Falha ao carregar intent nativo {arquivo}: {e}")

    # 2. Carrega da pasta plugins/
    raiz_projeto = os.path.dirname(os.path.dirname(__file__))
    pasta_plugins = os.path.join(raiz_projeto, "plugins")
    if not os.path.exists(pasta_plugins):
        os.makedirs(pasta_plugins, exist_ok=True)
    
    sys.path.insert(0, raiz_projeto)
    for folder in os.listdir(pasta_plugins):
        caminho_plugin = os.path.join(pasta_plugins, folder)
        if os.path.isdir(caminho_plugin) and not folder.startswith("__"):
            init_file = os.path.join(caminho_plugin, "__init__.py")
            if os.path.exists(init_file):
                try:
                    modulo = importlib.import_module(f"plugins.{folder}")
                    if hasattr(modulo, "intents"):
                        for detector in modulo.intents:
                            _INTENTS_DINAMICOS.append(detector)
                    
                    if hasattr(modulo, "DESCRICAO_ACAO"):
                        _DESCRICAO_ACAO.update(modulo.DESCRICAO_ACAO)
                        
                    log_intent("PLUGIN_LOAD", f"Plugin [{folder}] carregado com sucesso.", 1.0)
                except Exception as e:
                    log_erro("nexus_core_loader", f"Falha ao carregar plugin {folder}: {e}")

# Executa na hora do boot do script
carregar_intencoes_automaticamente()
import core.handlers  # Registra os handlers base

# Removido limite mínimo rigido de confiança para permitir que intents baseados em LLM sejam perdoados.
LIMIAR_CONFIANCA_MINIMA = 0.4 
LIMIAR_AMBIGUIDADE = 0.15

_ultima_intencao = {"intent": None, "alvo": "", "confianca": None}

def _marcar_intencao(acao, alvo="", confianca=None):
    _ultima_intencao.update(intent=acao, alvo=str(alvo), confianca=confianca)

def ultima_intencao() -> dict:
    return dict(_ultima_intencao)

def _interpretar_comando(comando: str) -> tuple:
    candidatos = [r for r in (detector(comando) for detector in _INTENTS_DINAMICOS) if r]

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
    descricoes = []
    base_desc = {
        "OPEN_APP": "abrir um aplicativo",
        "OPEN_FOLDER": "abrir uma pasta",
        "CLOSE_APP": "fechar um aplicativo",
        "GET_TIME": "saber as horas",
        "GET_DATE": "saber a data",
        "MEMORY_SAVE": "salvar dados na memória",
        "MEMORY_READ": "resgatar algo da memória",
        "EXIT": "encerrar o Sumé",
        "REMINDER_SET": "criar um lembrete",
        "REMINDER_LIST": "ver nossos lembretes",
        "REMINDER_CANCEL": "cancelar um lembrete"
    }
    base_desc.update(_DESCRICAO_ACAO) # Une as descricoes dos plugins
    
    for acao, _alvo, _conf in candidatos:
        desc = base_desc.get(acao, acao)
        if desc not in descricoes:
            descricoes.append(desc)
    
    if len(descricoes) == 1:
        return "Não entendi direito o que você quer dizer. Pode reformular?"
    opcoes = " ou ".join(descricoes)
    return f"Não tenho certeza se você quer {opcoes}. Pode ser mais específico?"

def processar(comando: str) -> str:
    inicio = time.time()
    comando = comando.lower().strip()

    resposta_memoria = processar_memoria(comando)
    if resposta_memoria:
        _marcar_intencao("MEMORIA")
        log_resultado(True, resposta_memoria, (time.time() - inicio) * 1000)
        return resposta_memoria

    acao, alvo, confianca = _interpretar_comando(comando)

    if acao == "AMBIGUOUS":
        candidatos = alvo  
        _marcar_intencao("AMBIGUOUS", " ou ".join(c[0] for c in candidatos), confianca)
        log_intent("AMBIGUOUS", str([c[0] for c in candidatos]), confianca)
        resposta = _pergunta_ambiguidade(candidatos)
        log_resultado(True, resposta, (time.time() - inicio) * 1000)
        return resposta

    if acao == "CHAT":
        _marcar_intencao("CHAT", comando)
    else:
        _marcar_intencao(acao, alvo, confianca)
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