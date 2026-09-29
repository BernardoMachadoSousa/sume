"""
Recall do Sumé — as três camadas de memória (T1/T2/T3).

Mapeamento para o modelo de 3 camadas (referência: r/hermesagent):

    T1  memória quente (hot)   — sempre injetada no prompt. Fatos de alta
                                  importância + preferências + camada
                                  'permanente' do SQLite. Custo: latência zero.
    T2  memória do vault (living files) — as notas .md do Obsidian. Entra no
                                  prompt apenas sob demanda, quando a consulta
                                  casa com o conteúdo (grafo de relações).
    T3  logs de evento (event logs) — diário diário + histórico. Nunca entra no
                                  prompt; é fonte para reanálise e promoted facts.

O objetivo é manter o prompt pequeno (só o que importa agora) e levar o resto
do segundo cérebro para dentro da conversa só quando necessário.
"""

import re
from typing import Any

from modulos import vault
from modulos.memoria import carregar, PERMANENTE
from utils.nome_utils import normalizar_nome

# Limite de relações T1 injetadas por padrão no prompt
LIMITE_QUENTE = 8


# ── T1: contexto quente ───────────────────────────────────────────────────────

def _peso_quente(rel: dict) -> float:
    """Score de urgência para entrarem no contexto quente."""
    try:
        importancia = float(rel.get("importancia", 0) or 0)
    except (TypeError, ValueError):
        importancia = 0.0
    try:
        usos = int(rel.get("usos", 0) or 0)
    except (TypeError, ValueError):
        usos = 0

    # Importância domina; 'usos' só desempata levemente (uso frequente sobe um pouco)
    return importancia + min(usos, 10) * 0.01


def contexto_quente(limite: int = LIMITE_QUENTE) -> str:
    """
    Monta o contexto T1: preferências e fatos de maior importância do grafo,
    mais a memória 'permanente' do SQLite.
    Retorna string pronta para injeção no system prompt (vazia se não houver nada).

    O `limite` é o teto de LINHAS do contexto, dividido em duas metades:
    metade para as memórias permanentes (preferências declaradas) e metade para
    as relações de maior importance score do vault. O teto é sempre global,
    senão um usuário com muitas preferências empurraria todo o grafo para fora
    do prompt sem limite.
    """
    if limite <= 0:
        return ""

    metade = max(1, limite // 2)
    linhas: list[str] = []

    # 1. Preferências declaradas (alta utilidade conversacional, baixo custo)
    prefs = carregar(PERMANENTE) or {}
    for _chave, valor in prefs.items():
        linhas.append(f"- {valor}")
    del linhas[metade:]

    # 2. Relações de maior importância do vault (T1 derivado do T2)
    candidatos: list[tuple[float, str]] = []
    try:
        notas = vault.listar()
    except Exception:
        notas = []

    for nota in notas:
        titulo = nota.get("titulo", "")
        for rel in nota.get("relacoes") or []:
            if not isinstance(rel, dict):
                continue
            if rel.get("status") == "historico":
                continue
            alvo = rel.get("alvo", "")
            tipo = rel.get("tipo", "")
            if not tipo:
                continue
            texto = f"- {tipo}: {alvo} (sobre {titulo})"
            candidatos.append((_peso_quente(rel), texto))

    candidatos.sort(key=lambda x: x[0], reverse=True)
    restantes = max(0, limite - len(linhas))
    for _, texto in candidatos[:restantes]:
        linhas.append(texto)

    if not linhas:
        return ""
    return "\n".join(linhas)


# ── T2: recuperação sob demanda ───────────────────────────────────────────────

def _termos(consulta: str) -> set[str]:
    """Extrai termos de busca normalizados de uma pergunta em linguagem natural."""
    limpo = re.sub(r"\[|\]", " ", consulta or "")
    palavras = re.findall(r"\w+", limpo.lower(), flags=re.UNICODE)
    # Stopwords pt-BR + en comuns
    stop = {
        "a", "o", "as", "os", "um", "uma", "uns", "umas", "de", "do", "da", "dos", "das",
        "em", "no", "na", "nos", "nas", "por", "para", "pra", "pro", "com", "sem", "sob",
        "sobre", "que", "quem", "qual", "quais", "eu", "meu", "minha", "me", "você", "voce",
        "the", "a", "an", "of", "is", "and", "to", "for", "my",
    }
    return {normalizar_nome(p) for p in palavras if len(p) > 2 and p not in stop}


def _casou(termos: set[str], texto_norm: str) -> bool:
    """True se algum termo da consulta aparece como palavra inteira no texto."""
    if not texto_norm:
        return False
    palavras = set(texto_norm.split())
    return any(t in palavras or t in texto_norm for t in termos)


def recuperar(consulta: str, limite: int = 5, contar_uso: bool = True) -> list[dict]:
    """
    Recupera do vault (T2) as relações que casam com a consulta.
    Usa interseção de termos normalizados (case/acento-insensitive via
    normalizar_nome) e pontua por importance score e por centralidade da
    entidade citada na consulta.
    """
    termos = _termos(consulta)
    if not termos:
        return []

    resultados: list[dict] = []
    try:
        notas = vault.listar()
    except Exception:
        return []

    for nota in notas:
        titulo = nota.get("titulo", "")
        tit_norm = normalizar_nome(titulo)
        corpo = nota.get("corpo", "") or ""
        corpo_norm = normalizar_nome(corpo)

        # Bônus quando a consulta cita a própria entidade: o usuário perguntou
        # "do que a Malu gosta?" — a nota Malu é a resposta, mesmo que a nota
        # do usuário também contenha um [[wikilink]] para ela.
        citada = 1.0 if tit_norm and tit_norm in termos else 0.0

        # Match no corpo da nota
        if _casou(termos, corpo_norm):
            resultados.append({
                "titulo": titulo,
                "tipo": "nota",
                "alvo": "",
                "texto": (corpo[:200] + "...") if len(corpo) > 200 else corpo,
                "score": 0.6 + citada * 0.6,
            })

        # Match nas relações
        for rel in nota.get("relacoes") or []:
            if not isinstance(rel, dict):
                continue
            tipo_norm = normalizar_nome(str(rel.get("tipo", "")))
            alvo_norm = normalizar_nome(str(rel.get("alvo", "")))
            if _casou(termos, tipo_norm) or _casou(termos, alvo_norm):
                try:
                    imp = float(rel.get("importancia", 0) or 0)
                except (TypeError, ValueError):
                    imp = 0.0
                resultados.append({
                    "titulo": titulo,
                    "tipo": rel.get("tipo", ""),
                    "alvo": rel.get("alvo", ""),
                    "texto": f"{rel.get('tipo', '')}: {rel.get('alvo', '')}",
                    "categoria": rel.get("categoria", "geral"),
                    "importancia": imp,
                    # Base alta (é um fato estruturado, não só menção) + bônus
                    "score": 0.8 + imp * 0.4 + citada * 0.4,
                })

    # Dedup: mesma entidade/tipo/alvo
    vistos: set[tuple] = set()
    unicos: list[dict] = []
    for r in sorted(resultados, key=lambda x: x["score"], reverse=True):
        chave = (normalizar_nome(r["titulo"]), normalizar_nome(r.get("tipo", "")),
                 normalizar_nome(r.get("alvo", "")))
        if chave in vistos:
            continue
        vistos.add(chave)
        unicos.append(r)

    finais = unicos[:limite]

    # Incrementa contador de uso nas relações recuperadas (reforço de saliência)
    if contar_uso and finais:
        _incrementar_usos(finais)

    return finais


def _incrementar_usos(resultados: list[dict]) -> None:
    """
    Incrementa o campo 'usos' nas notas onde houve match, escrevendo de volta
    no frontmatter. Best-effort: falha ao gravar não deve quebrar a resposta.
    """
    # Agrupa por título para minimizar escritas
    por_titulo: dict[str, int] = {}
    for r in resultados:
        if r.get("tipo") == "nota":
            # Nota inteira usada — não incrementar todas as rels
            continue
        t = r.get("titulo", "")
        por_titulo[t] = por_titulo.get(t, 0) + 1

    for titulo in por_titulo:
        try:
            raw = vault._ler_raw(titulo)
            if raw is None:
                continue
            partes = raw.split("---", 2)
            frontmatter = partes[1] if len(partes) >= 3 else ""
            corpo = partes[2].strip() if len(partes) >= 3 else raw.strip()
            relacoes = vault._frontmatter_objeto(frontmatter, "relacoes") if frontmatter else []
            if not relacoes:
                continue
            mudou = False
            for rel in relacoes:
                if isinstance(rel, dict):
                    try:
                        rel["usos"] = int(rel.get("usos", 0) or 0) + 1
                        mudou = True
                    except (TypeError, ValueError):
                        pass
            if mudou:
                vault.salvar(titulo, corpo, relacoes=relacoes)
        except Exception:
            # best-effort: não propaga erro
            continue


# ── Orquestração ──────────────────────────────────────────────────────────────

def montar_prompt_completo(consulta: str) -> dict:
    """
    Monta as três camadas para uma consulta específica.
    Retorna {t1, t2} — t1 sempre presente, t2 só quando há match.
    t3 (logs) não entra no prompt; é capturado separadamente por recall.
    """
    return {
        "t1": contexto_quente(),
        "t2": recuperar(consulta, contar_uso=True),
    }
