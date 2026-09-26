"""
Módulo de IA Conversacional do Sumé.

Híbrido: Ollama local (padrão) ou OmniRoute (opt-in).

Privacidade: por padrão nada sai da máquina. Só há envio para o OmniRoute
— que é um gateway remoto — quando `usar_omniroute` está ligado, e mesmo
aí o histórico/memória só é incluído com `compartilhar_contexto_omniroute`.
"""

import os

import ollama
import requests

from utils import config as cfg
from utils.logger import erro as log_erro
from utils.logger import info as log_info

# Configuração

MODELO_PADRAO = "phi3:mini"
ENDPOINT_PADRAO = "http://localhost:20128/v1"
CHAVE_PADRAO = ""
HISTORICO_MAXIMO = 20
MENSAGENS_NO_HISTORICO = 6
TIMEOUT_PADRAO = 120
FALHA_OLLAMA = (
    "Desculpe, não consegui processar isso agora. O Ollama está rodando?"
)

CONTEXTO_SISTEMA = """Você é o Sumé, um assistente virtual pessoal inspirado no Jarvis.
Características:
- Fala português brasileiro
- Respostas curtas e diretas (1-3 frases)
- Tom amigável mas profissional
- Chama o usuário pelo nome quando souber
- Usa emojis ocasionalmente
- Não inventa informações, admite quando não sabe algo"""

# Histórico de conversa (últimas mensagens para contexto)
historico = []


def _credencial() -> str:
    """Chave do OmniRoute: ambiente primeiro, config como reserva."""
    return (
        os.environ.get("OMNIROUTE_API_KEY")
        or cfg.get("chave_omniroute")
        or CHAVE_PADRAO
    )


def _contexto_extra(nome_usuario, incluir_memoria) -> str:
    """
    Monta o complemento do prompt de sistema, se houver.

    Quando `incluir_memoria` é falso, volta vazio: nem o nome nem o que
    sabemos do usuário vão para um modelo remoto sem autorização. Nome é
    dado pessoal, então entra na mesma regra do resto.
    """
    if not incluir_memoria:
        return ""
    partes = []
    if nome_usuario:
        partes.append(f"O usuário se chama {nome_usuario}.")
    from modulos.memoria import carregar

    memorias = {
        k: v for k, v in (carregar() or {}).items()
        if k != "nome_usuario" and v
    }
    if memorias:
        linhas = "\n".join(f"- {k}: {v}" for k, v in list(memorias.items())[:10])
        partes.append(f"O que você sabe sobre o usuário:\n{linhas}")
    return ("\n" + "\n".join(partes)) if partes else ""


def _montar_mensagens(nome_usuario, extras=""):
    """Prepara a lista de mensagens para qualquer um dos backends."""
    mensagens = [{"role": "system", "content": CONTEXTO_SISTEMA + extras}]
    for msg in historico[-MENSAGENS_NO_HISTORICO:]:
        mensagens.append(msg)
    return mensagens


def _registrar(usuario: str, assistente: str):
    """Guarda a troca e mantém o histórico limitado."""
    historico.append({"role": "user", "content": usuario})
    historico.append({"role": "assistant", "content": assistente})
    if len(historico) > HISTORICO_MAXIMO:
        del historico[:-HISTORICO_MAXIMO]


def _perguntar_ollama(mensagens, modelo):
    """Chama o Ollama local."""
    resposta = ollama.chat(model=modelo, messages=mensagens)
    return resposta["message"]["content"].strip()


def _perguntar_omniroute(mensagens, modelo, endpoint, chave, timeout):
    """Chama o OmniRoute pela API compatível com OpenAI."""
    r = requests.post(
        f"{endpoint.rstrip('/')}/chat/completions",
        headers={
            "Authorization": f"Bearer {chave}",
            "Content-Type": "application/json",
        },
        json={
            "model": modelo,
            "messages": mensagens,
            "stream": False,
        },
        timeout=timeout,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


def usar_omniroute() -> bool:
    """Diz se o gateway remoto está habilitado."""
    return bool(cfg.get("usar_omniroute"))


def _responder_omniroute(mensagem, nome_usuario):
    """Backend remoto, com queda para o Ollama se algo falhar."""
    modelo = cfg.get("modelo_omniroute") or "SUME-CLAUDE"
    endpoint = cfg.get("endpoint_omniroute") or ENDPOINT_PADRAO
    chave = _credencial()
    timeout = cfg.get("timeout_omniroute") or TIMEOUT_PADRAO
    incluir = bool(cfg.get("compartilhar_contexto_omniroute"))

    if not chave:
        log_erro("ia", "OmniRoute ligado mas sem OMNIROUTE_API_KEY")
        return _responder_ollama(mensagem, nome_usuario, avisar=True)

    extras = _contexto_extra(nome_usuario, incluir)
    mensagens = _montar_mensagens(nome_usuario, extras)
    mensagens.append({"role": "user", "content": mensagem})

    try:
        texto = _perguntar_omniroute(mensagens, modelo, endpoint, chave, timeout)
        log_info("ia", f"OmniRoute/{modelo} respondeu")
        _registrar(mensagem, texto)
        return texto
    except Exception as e:
        log_erro("ia", f"OmniRoute falhou, usando Ollama: {e}")
        return _responder_ollama(mensagem, nome_usuario, avisar=True)


def _responder_ollama(mensagem, nome_usuario, avisar=False):
    """Backend local, que é o padrão e nunca sai da máquina."""
    modelo = cfg.get("modelo_ia") or MODELO_PADRAO
    if modelo == "phi3":
        modelo = MODELO_PADRAO

    extras = _contexto_extra(nome_usuario, True)
    mensagens = _montar_mensagens(nome_usuario, extras)
    mensagens.append({"role": "user", "content": mensagem})

    try:
        texto = _perguntar_ollama(mensagens, modelo)
        _registrar(mensagem, texto)
        return texto
    except Exception as e:
        log_erro("ia", f"Ollama falhou: {e}")
        return FALHA_OLLAMA


def conversar(mensagem, nome_usuario=None):
    """
    Envia a mensagem ao backend configurado e retorna a resposta.

    Args:
        mensagem: texto da pergunta do usuário
        nome_usuario: nome do usuário (opcional, se conhecido)

    Returns:
        resposta: texto da resposta da IA
    """
    if usar_omniroute():
        return _responder_omniroute(mensagem, nome_usuario)
    return _responder_ollama(mensagem, nome_usuario)


def usar_local():
    """Volta para o Ollama local."""
    cfg.set("usar_omniroute", False)
    return "Sumé passou a responder localmente, com o Ollama."


def usar_remoto():
    """Liga o OmniRoute, se houver credencial configurada."""
    if not _credencial():
        return (
            "Para usar o OmniRoute eu preciso da chave. "
            "Defina OMNIROUTE_API_KEY no ambiente."
        )
    cfg.set("usar_omniroute", True)
    modelo = cfg.get("modelo_omniroute") or "SUME-CLAUDE"
    return f"Sumé passou a responder pelo OmniRoute, usando {modelo}."


def backend_atual() -> str:
    """Nome do backend em uso, para mostrar ao usuário."""
    if usar_omniroute():
        return f"OmniRoute/{cfg.get('modelo_omniroute') or 'SUME-CLAUDE'}"
    modelo = cfg.get("modelo_ia") or MODELO_PADRAO
    return f"Ollama/{modelo}"


def processar_ia(comando: str) -> str | None:
    """
    Treata as frases que trocam o backend. Devolve None quando o comando
    não é sobre isso, para o fluxo seguir normal.
    """
    c = (comando or "").lower().strip()

    if any(p in c for p in ("usar omniroute", "usar o omniroute",
                            "ligar o omniroute", "passar pro omniroute",
                            "passar para o omniroute", "conectar no omniroute")):
        return usar_remoto()

    if any(p in c for p in ("usar ollama", "usar localmente", "responder local",
                            "desligar o omniroute", "voltar pro local",
                            "sem gateway", "modo offline")):
        return usar_local()

    if any(p in c for p in ("qual modelo", "que modelo", "qual ia",
                            "quem esta respondendo", "quem está respondendo",
                            "qual backend")):
        return f"Agora eu respondo com {backend_atual()}."

    return None


def limpar_historico():
    """Limpa o histórico de conversa."""
    global historico
    historico = []
    return "Histórico limpo!"


# Teste rápido
if __name__ == "__main__":
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.console import configurar_console

    configurar_console()  # a resposta do LLM costuma vir com emoji

    print(f"backend: {backend_atual()}")
    resposta = conversar("Olá! Quem é você e o que pode fazer?")
    print(f"Sumé: {resposta}")
