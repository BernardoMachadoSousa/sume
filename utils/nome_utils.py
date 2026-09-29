"""
Utilitários para normalização e comparação de nomes de entidades.
Usado para identificar quando grafias diferentes apontam para a mesma pessoa,
lugar ou conceito, permitindo deduplicação no vault do Obsidian.
"""

import unicodedata
import re
import difflib

def normalizar_nome(nome: str) -> str:
    """
    Converte qualquer grafia de nome em uma forma canônica para comparação.
    - minúsculas
    - remove acentos
    - espaços, hífens, underscores viram o mesmo token
    - remove pontuação
    - opcionalmente remove artigos/preposições comuns (deixamos desativado por enquanto
      para evitar falsos negativos em nomes como "João dos Santos").
    Ex: 'Bernardo-João', 'bernardo joao', 'Bernardo João' => 'bernardo joao'
    """
    if not nome:
        return ""
    # Lowercase + strip
    nome = nome.strip().lower()
    # Remove acentos (combining marks)
    nome = ''.join(c for c in unicodedata.normalize('NFD', nome)
                  if unicodedata.category(c) != 'Mn')
    # Substitui separadores por espaço simples
    nome = re.sub(r'[\s_-]+', ' ', nome)
    # Remove pontuação
    nome = re.sub(r'[^\w\s]', '', nome)
    # Remove artigos/preposições comuns em português (opcional, pode ser perigoso)
    # Comentado para evitar fusão indevida de nomes distintos.
    # artigos = r'\b(o|a|os|as|de|do|da|dos|das|e|y|em|no|na|nos|nas)\b'
    # nome = re.sub(artigos, '', nome)
    # Colapsa espaços e trim
    nome = re.sub(r'\s+', ' ', nome).strip()
    return nome

def nomes_sao_equivalentes(n1: str, n2: str) -> bool:
    """
    Retorna True se os dois nomes, após normalização, apontarem para a mesma entidade.
    """
    return normalizar_nome(n1) == normalizar_nome(n2)

VARIANTES_EU = {"eu", "mim", "meu", "minha", "me", "usuario", "usuário", "eu mesmo"}

LIMIAR_FUSAO = 0.85
LIMIAR_DUVIDA = 0.70


def calcular_similaridade(n1: str, n2: str) -> float:
    """Similaridade de sequência entre dois nomes normalizados (0.0 a 1.0)."""
    norm1 = normalizar_nome(n1)
    norm2 = normalizar_nome(n2)
    if not norm1 or not norm2:
        return 0.0
    return difflib.SequenceMatcher(None, norm1, norm2).ratio()


def calcular_similaridade_tokens(alvo: str, candidato: str) -> float:
    """
    Cobertura de tokens: fração das palavras do candidato que existem no alvo.
    'Maria' contra 'Maria Luiza' = 1.0; 'Silva' contra 'Roberta Silva' = 1.0.
    """
    alvo_tokens = set(normalizar_nome(alvo).split())
    cand_tokens = set(normalizar_nome(candidato).split())
    if not alvo_tokens or not cand_tokens:
        return 0.0
    return len(alvo_tokens.intersection(cand_tokens)) / len(cand_tokens)


def score_entidade(query: str, alvo: str) -> float:
    """
    Score combinado para decidir se query e alvo são a mesma entidade.
    Combina string inteira, typos token a token e primeiro-nome de nome composto.
    """
    qn = normalizar_nome(query)
    an = normalizar_nome(alvo)
    if not qn or not an:
        return 0.0
    if qn == an:
        return 1.0

    cheio = difflib.SequenceMatcher(None, qn, an).ratio()
    q_tokens = qn.split()
    a_tokens = an.split()
    melhor = cheio

    primeiro = difflib.SequenceMatcher(None, q_tokens[0], a_tokens[0]).ratio()

    if len(q_tokens) == len(a_tokens):
        alinhado = sum(
            difflib.SequenceMatcher(None, qt, at).ratio()
            for qt, at in zip(q_tokens, a_tokens)
        ) / len(q_tokens)
        return max(melhor, alinhado)

    # Um token só casa com o primeiro nome (evita Silva -> Roberta Silva)
    if len(q_tokens) == 1 or len(a_tokens) == 1:
        return max(melhor, primeiro)

    n = min(len(q_tokens), len(a_tokens))
    alinhado = sum(
        difflib.SequenceMatcher(None, q_tokens[i], a_tokens[i]).ratio()
        for i in range(n)
    ) / n
    return max(melhor, primeiro, alinhado)


def e_pronome_usuario(nome: str) -> bool:
    return normalizar_nome(nome) in VARIANTES_EU


def resolver_ancora_identidade(nome: str, nome_usuario: str = "Bernardo Jonas") -> bool:
    """True se o nome for pronome do dono ou um typo/variante do nome do usuário."""
    if e_pronome_usuario(nome):
        return True
    if not nome_usuario:
        return False
    return score_entidade(nome, nome_usuario) >= LIMIAR_FUSAO

def gerar_apelidos_possiveis(nome_completo: str) -> list[str]:
    """
    Dado um nome completo, gera apelidos prováveis (primeiro nome, diminutivos comuns).
    Usado para preencher o campo `aliases:`.
    """
    nome = nome_completo.strip()
    if not nome:
        return []
    partes = nome.split()
    if len(partes) == 1:
        return [partes[0]]
    primeiro = partes[0]
    # Por enquanto, apenas o primeiro nome como apelido provável.
    # Pode ser expandido com uma lista de diminutivos comuns (Ber, Dudu, etc.) se necessário.
    return [primeiro]