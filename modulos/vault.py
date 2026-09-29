"""
Vault de conhecimento do Sumé.

Notas em Markdown dentro de dados/vault/, no formato do Obsidian: dá para
abrir a pasta em qualquer editor, versionar em git ou sincronizar à mão.

O vault é só leitura por padrão no prompt. Ele só entra no contexto quando
o chamador pedir explicitamente, porque normalmente é o que o usuário não
quer mandando para um modelo remoto.
"""

import os
import re
import unicodedata
from datetime import datetime

from utils.logger import erro as log_erro
from utils import config as cfg
from utils.nome_utils import normalizar_nome

LIMITE_CONTEXTO = 4000
ROOT = None

def _pasta_vault() -> str:
    """Retorna o caminho atual do vault baseado no config (ou ROOT se sobrescrito)."""
    if ROOT:
        os.makedirs(ROOT, exist_ok=True)
        return ROOT
    caminho = cfg.get("caminho_obsidian")
    if not caminho:
        caminho = "dados/vault"
    os.makedirs(caminho, exist_ok=True)
    return caminho


# Index cache: maps normalized name to (canonical_title, caminho)
_INDICE = None
_INDICE_VALIDO = False


def _construir_indice():
    """Reconstrói o índice de nomes normalizados para (título canônico, caminho)."""
    global _INDICE, _INDICE_VALIDO
    indice = {}
    pasta = _pasta_vault()
    if not os.path.isdir(pasta):
        _INDICE = {}
        _INDICE_VALIDO = True
        return
    for nome in os.listdir(pasta):
        if not nome.endswith(".md"):
            continue
        caminho = os.path.join(pasta, nome)
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                texto = f.read()
        except Exception:
            continue
        # Extract title and aliases from frontmatter
        titulo = None
        aliases = []
        partes = texto.split("---", 2)
        if len(partes) >= 2:
            frontmatter = partes[1]
            for linha in frontmatter.splitlines():
                if linha.startswith("titulo:"):
                    titulo = linha.split(":", 1)[1].strip()
                elif linha.startswith("aliases:"):
                    # Parse list like: aliases: [item1, item2]
                    import ast
                    try:
                        aliases_str = linha.split(":", 1)[1].strip()
                        if aliases_str.startswith("[") and aliases_str.endswith("]"):
                            aliases = ast.literal_eval(aliases_str)
                            if not isinstance(aliases, list):
                                aliases = []
                        else:
                            aliases = []
                    except Exception:
                        aliases = []
        if titulo is None:
            # Fallback: filename without extension
            titulo = nome[:-3].replace("-", " ")
        # Normalize title and each alias
        for nome_variante in [titulo] + aliases:
            norm = normalizar_nome(nome_variante)
            if norm and norm not in indice:
                # Prefer the longer title as canonical? For now, first wins.
                indice[norm] = (titulo, caminho)
    _INDICE = indice
    _INDICE_VALIDO = True


def resolver_entidade(nome: str) -> str | None:
    """
    Dado um nome (como extraído pelo LLM ou dito pelo usuário), retorna o
    título canônico da nota que já existe para esse nome, ou None se for nova.
    Passos:
      1. Normaliza o nome de entrada.
      2. Procura no índice por correspondência exata (normalizado).
      3. Se não encontrar, tenta correspondência por "começa com" (prefixo)
         onde o candidato normalizado começa com o nome normalizado e é maior.
         Entre todos tais candidatos, escolhe o que tiver o título mais longo
         (mais específico). Se nenhum candidato, retorna None.
    """
    global _INDICE_VALIDO
    if not _INDICE_VALIDO:
        _construir_indice()
    norm = normalizar_nome(nome)
    if not norm:
        return None
    # Exact match
    if norm in _INDICE:
        return _INDICE[norm][0]  # canonical title
    # Prefix match: find all entries where the normalized canonical starts with norm
    candidates = []
    for n, (titulo, _) in _INDICE.items():
        if n.startswith(norm) and len(n) > len(norm):
            candidates.append((titulo, n))
    if not candidates:
        return None
    # Choose the candidate with the longest title (most specific)
    # In case of tie, choose the one with longest normalized string? We'll just pick first after sorting by length descending.
    candidates.sort(key=lambda x: len(x[0]), reverse=True)
    return candidates[0][0]


def obter_ou_criar_nota(titulo: str, corpo_inicial: str = "", tags=None, links=None, aliases=None) -> str:
    """
    Usa resolver_entidade(titulo); se existir, apenas atualiza (append ou mescla fatos);
    senão, cria nova.
    Returns the path of the note.
    """
    existente = resolver_entidade(titulo)
    if existente:
        # Note exists; we could append or just return the path.
        # For now, we just return the path (caller can decide to append).
        # But we also want to merge aliases if provided.
        if aliases is not None:
            # Add any new aliases
            nota_atual = _ler_raw(existente) or ""
            # Extract current aliases from frontmatter
            aliases_atuais = []
            partes = nota_atual.split("---", 2)
            if len(partes) >= 2:
                frontmatter = partes[1]
                for linha in frontmatter.splitlines():
                    if linha.startswith("aliases:"):
                        try:
                            import ast
                            aliases_str = linha.split(":", 1)[1].strip()
                            if aliases_str.startswith("[") and aliases_str.endswith("]"):
                                aliases_atuais = ast.literal_eval(aliases_str)
                                if not isinstance(aliases_atuais, list):
                                    aliases_atuais = []
                        except Exception:
                            aliases_atuais = []
            # Combine
            todas = list(set(aliases_atuais + [str(a).strip() for a in aliases if str(a).strip()]))
            # Update the note with merged aliases (preserving existing content)
            corpo = partes[2].strip() if len(partes) >= 3 else nota_atual.strip()
            # Read tags and links to not lose them
            if tags is None:
                tags = []
            if links is None:
                links = []
            if len(partes) >= 2:
                for linha in frontmatter.splitlines():
                    if linha.startswith("tags:") and not tags:
                        try:
                            t_str = linha.split(":", 1)[1].strip().strip("[]")
                            tags = [t.strip() for t in t_str.split(",") if t.strip()]
                        except Exception: pass
                    elif linha.startswith("links:") and not links:
                        try:
                            l_str = linha.split(":", 1)[1].strip().strip("[]")
                            links = [lk.strip() for lk in l_str.split(",") if lk.strip()]
                        except Exception: pass
            salvar(existente, corpo, tags=tags, links=links, aliases=todas)
        return _caminho(existente)
    else:
        # Create new note
        return salvar(titulo, corpo_inicial, tags=tags, links=links, aliases=aliases)


def _ler_raw(titulo: str) -> str | None:
    """Lê o conteúdo completo do arquivo (frontmatter + corpo), ou None se não existir."""
    try:
        caminho = _caminho(titulo)
        if not os.path.exists(caminho):
            return None
        with open(caminho, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        log_erro("vault", str(e))
        return None


def adicionar_alias(titulo_canonico: str, alias: str) -> bool:
    """
    Se o alias não estiver já na lista `aliases:` da nota, o acrescenta
    (evitando duplicatas) e salva a nota novamente.
    Returns True if the note was updated, False otherwise.
    """
    # Ensure the note exists
    existente = resolver_entidade(titulo_canonico)
    if not existente:
        return False
    nota_atual = _ler_raw(existente) or ""
    # Extract current aliases
    aliases_atuais = []
    partes = nota_atual.split("---", 2)
    if len(partes) >= 2:
        frontmatter = partes[1]
        for linha in frontmatter.splitlines():
            if linha.startswith("aliases:"):
                try:
                    import ast
                    aliases_str = linha.split(":", 1)[1].strip()
                    if aliases_str.startswith("[") and aliases_str.endswith("]"):
                        aliases_atuais = ast.literal_eval(aliases_str)
                        if not isinstance(aliases_atuais, list):
                            aliases_atuais = []
                except Exception:
                    aliases_atuais = []
    # Check if alias already present (normalized)
    alias_norm = normalizar_nome(alias)
    ja_existe = any(normalizar_nome(a) == alias_norm for a in aliases_atuais)
    if ja_existe:
        return False
    # Add alias
    novas_aliases = aliases_atuais + [alias]
    # Preserve existing content (body)
    corpo = partes[2].strip() if len(partes) >= 3 else nota_atual.strip()
    # Read tags and links to not lose them
    tags_atuais = []
    links_atuais = []
    if len(partes) >= 2:
        for linha in frontmatter.splitlines():
            if linha.startswith("tags:"):
                try:
                    t_str = linha.split(":", 1)[1].strip().strip("[]")
                    tags_atuais = [t.strip() for t in t_str.split(",") if t.strip()]
                except Exception: pass
            elif linha.startswith("links:"):
                try:
                    l_str = linha.split(":", 1)[1].strip().strip("[]")
                    links_atuais = [lk.strip() for lk in l_str.split(",") if lk.strip()]
                except Exception: pass
    salvar(existente, corpo, tags=tags_atuais, links=links_atuais, aliases=novas_aliases)
    return True

def _caminho(titulo: str) -> str:
    """Converte o título num nome de arquivo seguro."""
    base = unicodedata.normalize("NFKD", titulo)
    base = base.encode("ascii", "ignore").decode("ascii").lower()
    base = re.sub(r"[^\w\s-]", "", base).strip()
    base = re.sub(r"[\s_]+", "-", base)
    base = re.sub(r"-{2,}", "-", base).strip("-")
    return os.path.join(_pasta_vault(), f"{base or 'nota'}.md")


def salvar(titulo: str, corpo: str, tags=None, links=None, aliases=None) -> str:
    """Cria ou sobrescreve uma nota e devolve o caminho do arquivo."""
    try:
        caminho = _caminho(titulo)
        etiquetas = [t.lstrip("#") for t in (tags or []) if str(t).strip()]
        linhas = [
            "---",
            f"titulo: {titulo}",
            f"atualizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ]
        if etiquetas:
            linhas.append("tags: [" + ", ".join(etiquetas) + "]")
        if links:
            linhas.append("links: [" + ", ".join(str(l) for l in links) + "]")
        if aliases is not None:
            # Ensure aliases is a list of strings
            aliases_lista = [str(a).strip() for a in aliases if str(a).strip()]
            if aliases_lista:
                linhas.append("aliases: [" + ", ".join(aliases_lista) + "]")
        linhas += ["---", "", corpo.strip(), ""]

        with open(caminho, "w", encoding="utf-8") as f:
            f.write("\n".join(linhas))
        # Invalidate index cache because we added/changed a note
        global _INDICE, _INDICE_VALIDO
        _INDICE = None
        _INDICE_VALIDO = False
        return caminho
    except Exception as e:
        log_erro("vault", str(e))
        return ""


def append_to_note(titulo: str, texto: str) -> str:
    """Append texto to an existing note, creating it if necessary.
    Returns the path of the note.
    """
    try:
        existente = ler(titulo) or ""
        # Avoid adding extra newline if existing is empty
        if existente:
            combined = existente + "\n" + texto
        else:
            combined = texto
        return salvar(titulo, combined)
    except Exception as e:
        log_erro("vault", str(e))
        return ""


def ler(titulo: str) -> str | None:
    """Lê o corpo de uma nota, sem o frontmatter."""
    try:
        caminho = _caminho(titulo)
        if not os.path.exists(caminho):
            return None
        with open(caminho, "r", encoding="utf-8") as f:
            texto = f.read()
        partes = texto.split("---", 2)
        return partes[2].strip() if len(partes) == 3 else texto.strip()
    except Exception as e:
        log_erro("vault", str(e))
        return None


def listar() -> list[dict]:
    """Lista as notas do vault com título, tags e caminho."""
    try:
        pasta = _pasta_vault()
        if not os.path.isdir(pasta):
            return []
        notas = []
        for nome in sorted(os.listdir(pasta)):
            if not nome.endswith(".md"):
                continue
            caminho = os.path.join(pasta, nome)
            with open(caminho, "r", encoding="utf-8") as f:
                texto = f.read()
            titulo = nome[:-3].replace("-", " ")
            etiquetas = []
            for linha in texto.splitlines():
                if linha.startswith("titulo:"):
                    titulo = linha.split(":", 1)[1].strip()
                elif linha.startswith("tags:"):
                    etiquetas = [
                        t.strip() for t in
                        linha.split(":", 1)[1].strip().strip("[]").split(",")
                        if t.strip()
                    ]
            notas.append({
                "titulo": titulo,
                "tags": etiquetas,
                "caminho": caminho,
            })
        return notas
    except Exception as e:
        log_erro("vault", str(e))
        return []


def buscar(termo: str) -> list[str]:
    """Devolve os títulos das notas que contêm o termo."""
    alvo = termo.lower()
    achados = []
    for nota in listar():
        corpo = ler(nota["titulo"]) or ""
        if alvo in nota["titulo"].lower() or alvo in corpo.lower():
            achados.append(nota["titulo"])
    return achados


def apagar(titulo: str) -> bool:
    """Remove uma nota do vault."""
    try:
        caminho = _caminho(titulo)
        if os.path.exists(caminho):
            os.remove(caminho)
            return True
        return False
    except Exception as e:
        log_erro("vault", str(e))
        return False


def contexto(limite=LIMITE_CONTEXTO) -> str:
    """
    Concatena as notas num texto para o prompt.

    Só chame quando o envio estiver autorizado: quando o modelo é remoto,
    o conteúdo do vault costuma ser justamente o que não deve sair da máquina.
    """
    try:
        pedacos = []
        for nota in listar():
            corpo = ler(nota["titulo"])
            if corpo:
                cabecalho = f"## {nota['titulo']}"
                if nota["tags"]:
                    cabecalho += "  (" + ", ".join(f"#{t}" for t in nota["tags"]) + ")"
                pedacos.append(f"{cabecalho}\n{corpo}")
        texto = "\n\n".join(pedacos)
        return texto[:limite]
    except Exception as e:
        log_erro("vault", str(e))
        return ""