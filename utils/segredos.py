"""
Detecção de segredos em texto livre.

Objetivo: impedir que credenciais e dados financeiros entrem no grafo
do cérebro (que é sincronizado para o Obsidian em texto plano).

Abordagem: heurística determinística e conservadora — só sinaliza quando
há um marcador semântico forte ("minha senha é ...") ou formato típico
(chave de API, cartão, CPF, JWT). Falso positivo é aceitável porque
o custo é apenas pedir confirmação ao usuário; falso negativo grava
um segredo em texto plano.
"""

import re
from typing import Optional

# Padrões de formato (independentes de contexto)
_PADROES_FORMATO: list[tuple[str, str]] = [
    # Chaves de API conhecidas pelos prefixos
    (r"\bsk-[A-Za-z0-9]{16,}\b", "token/chave de API da OpenAI"),
    (r"\bsk-ant-[A-Za-z0-9\-_]{16,}\b", "chave da Anthropic"),
    (r"\bghp_[A-Za-z0-9]{20,}\b", "token do GitHub"),
    (r"\bgithub_pat_[A-Za-z0-9_]{20,}\b", "token do GitHub"),
    (r"\bAKIA[0-9A-Z]{16}\b", "chave de acesso AWS"),
    (r"\bAIza[0-9A-Za-z\-_]{30,}\b", "chave da Google Cloud"),
    (r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b", "token do Slack"),
    (r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{5,}\b", "token JWT"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "chave privada"),
    # CPF / CNPJ
    (r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b", "CPF"),
    (r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b", "CNPJ"),
    # Cartão de crédito (com ou sem separadores)
    (r"\b(?:\d[ -]?){13,19}\b", "número de cartão"),
    # Senha em URL
    (r"\b[a-z][a-z0-9+.\-]*://[^\s/@:]+:[^\s/@]+@", "senha em URL (credencial)"),
]

# Marcadores semânticos: exigem um valor associado para reduzir falsos positivos
_PADROES_CONTEXTUAIS: list[tuple[str, str]] = [
    (r"\b(?:minha|meco)\s+(?:senha|palavra[\s\-]?passe|pin|senha)\s*(?:é|e|:)\s*\S+",
     "senha"),
    (r"\b(?:senha|palavra[\s\-]?passe|password)\s*(?:é|e|:)\s*\S+", "senha"),
    (r"\b(?:api[\s\-]?key|chave\s+de\s+api|api[\s\-]?secret|token)\s*(?:é|e|:)\s*\S+",
     "chave/token de API"),
    (r"\b(?:senha|senhas?)\s+(?:do|da|no|na)\s+\w+\s*(?:é|e|:)\s*\S+", "senha"),
]

_PADROES_COMPILED_FORMATO = [(re.compile(p, re.IGNORECASE), r) for p, r in _PADROES_FORMATO]
_PADROES_COMPILED_CTX = [(re.compile(p, re.IGNORECASE), r) for p, r in _PADROES_CONTEXTUAIS]

# Falso positivo conhecido: datas e números comuns que casam com o padrão de cartão.
_RE_CURTO_OU_DATA = re.compile(r"^\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}$")


def detectar_segredo(texto: Optional[str]) -> Optional[str]:
    """
    Retorna uma descrição do segredo encontrado, ou None se o texto for limpo.

    Args:
        texto: texto livre a inspecionar.

    Returns:
        str describing the secret type, or None.
    """
    if not texto or not isinstance(texto, str):
        return None

    # Padrões de contexto têm prioridade: são os mais confiáveis
    for regex, rotulo in _PADROES_COMPILED_CTX:
        if regex.search(texto):
            return rotulo

    for regex, rotulo in _PADROES_COMPILED_FORMATO:
        achado = regex.search(texto)
        if not achado:
            continue
        # Descarta datas/valores curtos que casaram com o padrão de cartão
        if rotulo == "número de cartão":
            trecho = achado.group(0).strip()
            if _RE_CURTO_OU_DATA.match(trecho) or len(re.sub(r"\D", "", trecho)) < 13:
                continue
        return rotulo

    return None


def texto_contem_segredo(texto: Optional[str]) -> bool:
    """Conveniência booleana sobre detectar_segredo."""
    return detectar_segredo(texto) is not None
