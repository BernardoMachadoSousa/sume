"""
Módulo de IA Conversacional do Sumé.

Nuvem: Groq API (Padrão, super-rápida, grátis) ou Gemini (Grátis)
Fallback: Ollama local (se sem internet)
"""

import os
import requests
import ollama
import threading
from utils import config as cfg
from utils.logger import erro as log_erro
from utils.logger import info as log_info

# Configuração Padrão Nova API: Groq Cloud (API Gratuita Ultra Rápida)
MODELO_NUVEM_PADRAO = "llama-3.3-70b-versatile"
URL_GROQ = "https://api.groq.com/openai/v1/chat/completions"

HISTORICO_MAXIMO = 20
MENSAGENS_NO_HISTORICO = 6
TIMEOUT_PADRAO = 15
FALHA_CONEXAO = "Desculpe, deu branco aqui na comunicação de rede."

CONTEXTO_SISTEMA = """Você é o Sumé, um assistente virtual pessoal inspirado no Jarvis.
Características:
- Fala português brasileiro
- Respostas CURTAS e DIRETAS (1 a 3 frases máximo)
- Tom amigável, ligeiramente formal e inteligente
- Chama o usuário pelo nome quando souber
- NÃO inventa informações. Se não souber, diga.
Importante: O usuário falará com você SOMENTE VIA VOZ. Não envie listas imensas de markdown, evite ler código gigantesco. Seja breve."""

historico = []
_historico_lock = threading.Lock()

def _credencial_groq() -> str:
    """Verifica variável GROQ_API_KEY no Windows."""
    return os.environ.get("GROQ_API_KEY") or cfg.get("groq_api_key") or ""

def _contexto_extra(nome_usuario, incluir_memoria) -> str:
    if not incluir_memoria:
        return ""
    partes = []
    if nome_usuario:
        partes.append(f"O usuário se chama {nome_usuario}.")
    
    from modulos.memoria import carregar
    memorias = {k: v for k, v in (carregar() or {}).items() if k != "nome_usuario" and v}
    
    if memorias:
        linhas = "\n".join(f"- {k}: {v}" for k, v in list(memorias.items())[:10])
        partes.append(f"O que você já sabe definitivamente sobre o usuário:\n{linhas}")
    return ("\n" + "\n".join(partes)) if partes else ""

def _montar_mensagens(nome_usuario, extras=""):
    mensagens = [{"role": "system", "content": CONTEXTO_SISTEMA + extras}]
    with _historico_lock:
        for msg in historico[-MENSAGENS_NO_HISTORICO:]:
            mensagens.append(msg)
    return mensagens

def _registrar(usuario: str, assistente: str):
    with _historico_lock:
        historico.append({"role": "user", "content": usuario})
        historico.append({"role": "assistant", "content": assistente})
        if len(historico) > HISTORICO_MAXIMO:
            del historico[:-HISTORICO_MAXIMO]

def _responder_groq(mensagem, nome_usuario):
    """Bate no servidor Ultra-rápido da Groq Llama 3 70B."""
    chave = _credencial_groq()
    if not chave:
        return _responder_ollama(mensagem, nome_usuario)
    
    compartilhar = cfg.get("compartilhar_conteudo_nuvem", False)
    extras = _contexto_extra(nome_usuario, compartilhar)
    mensagens = _montar_mensagens(nome_usuario, extras)
    mensagens.append({"role": "user", "content": mensagem})

    try:
        r = requests.post(
            URL_GROQ,
            headers={
                "Authorization": f"Bearer {chave}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODELO_NUVEM_PADRAO,
                "messages": mensagens,
                "temperature": 0.6,
                "max_tokens": 1024
            },
            timeout=TIMEOUT_PADRAO
        )
        r.raise_for_status()
        texto = r.json()["choices"][0]["message"]["content"].strip()
        _registrar(mensagem, texto)
        log_info("ia", "Groq Llama 3 respondeu")
        return texto
    except Exception as e:
        log_erro("ia", f"Groq Falhou: {e}")
        return _responder_ollama(mensagem, nome_usuario)

def _responder_ollama(mensagem, nome_usuario):
    import ollama
    extras = _contexto_extra(nome_usuario, True)
    mensagens = _montar_mensagens(nome_usuario, extras)
    mensagens.append({"role": "user", "content": mensagem})
    try:
        resposta = ollama.chat(model="phi3:mini", messages=mensagens)
        texto = resposta["message"]["content"].strip()
        _registrar(mensagem, texto)
        return texto
    except Exception:
        return FALHA_CONEXAO

def conversar(mensagem, nome_usuario=None):
    return _responder_groq(mensagem, nome_usuario)

def backend_atual() -> str:
    if _credencial_groq():
        return f"Groq Cloud ({MODELO_NUVEM_PADRAO})"
    return "Ollama (phi3:mini local)"

def limpar_historico():
    global historico
    with _historico_lock:
        historico = []
    return "Memória curta redefinida."
