"""
Utilitários para normalização e comparação de nomes de entidades.
Usado para identificar quando grafias diferentes apontam para a mesma pessoa,
lugar ou conceito, permitindo deduplicação no vault do Obsidian.
"""

import unicodedata
import re

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