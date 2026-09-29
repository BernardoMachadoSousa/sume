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
from utils.nome_utils import (
    normalizar_nome,
    score_entidade,
    e_pronome_usuario,
    resolver_ancora_identidade,
    LIMIAR_FUSAO,
    LIMIAR_DUVIDA,
)

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
        titulo = None
        aliases = []
        partes = texto.split("---", 2)
        if len(partes) >= 2:
            frontmatter = partes[1]
            for linha in frontmatter.splitlines():
                if linha.startswith("titulo:"):
                    titulo = linha.split(":", 1)[1].strip()
                    break
            aliases = _frontmatter_campo(frontmatter, "aliases")
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


def _titulos_unicos_indice() -> list[str]:
    if not _INDICE:
        return []
    vistos = []
    for titulo, _ in _INDICE.values():
        if titulo not in vistos:
            vistos.append(titulo)
    return vistos


def _melhor_candidato(nome: str) -> tuple[str, float] | None:
    melhor_titulo = None
    melhor_score = 0.0
    for titulo in _titulos_unicos_indice():
        s = score_entidade(nome, titulo)
        if s > melhor_score or (s == melhor_score and melhor_titulo and len(titulo) > len(melhor_titulo)):
            melhor_score = s
            melhor_titulo = titulo
    if melhor_titulo is None:
        return None
    return melhor_titulo, melhor_score


def resolver_entidade(nome: str, nome_usuario: str | None = None) -> str | None:
    """
    Devolve o título canônico de uma nota que já existe, ou None.
    Nunca devolve um título sem arquivo correspondente.
    """
    global _INDICE_VALIDO
    if not _INDICE_VALIDO:
        _construir_indice()

    norm = normalizar_nome(nome)
    if not norm:
        return None

    if nome_usuario and resolver_ancora_identidade(nome, nome_usuario):
        norm_usuario = normalizar_nome(nome_usuario)
        if _INDICE and norm_usuario in _INDICE:
            return _INDICE[norm_usuario][0]
        hit = _melhor_candidato(nome_usuario)
        if hit and hit[1] >= LIMIAR_FUSAO:
            return hit[0]
        if e_pronome_usuario(nome):
            return None

    if _INDICE and norm in _INDICE:
        return _INDICE[norm][0]

    hit = _melhor_candidato(nome)
    if hit and hit[1] >= LIMIAR_FUSAO:
        return hit[0]
    return None


def _frontmatter_campo(frontmatter: str, chave: str) -> list[str]:
    for linha in frontmatter.splitlines():
        if linha.startswith(chave + ":"):
            try:
                bruto = linha.split(":", 1)[1].strip()
                if bruto.startswith("[") and bruto.endswith("]"):
                    inner = bruto[1:-1].strip()
                    if not inner:
                        return []
                    return [p.strip().strip("'\"") for p in inner.split(",") if p.strip()]
                return [t.strip().strip("'\"") for t in bruto.strip("[]").split(",") if t.strip()]
            except Exception:
                return []
    return []


def _frontmatter_objeto(frontmatter: str, chave: str) -> list[dict]:
    """Lê chaves que são JSON-like arrays de objetos (propriedades, relacoes)."""
    for linha in frontmatter.splitlines():
        if linha.startswith(chave + ":"):
            try:
                bruto = linha.split(":", 1)[1].strip()
                if not bruto.startswith("[") or not bruto.endswith("]"):
                    return []
                import ast
                arr = ast.literal_eval(bruto)
                if isinstance(arr, list):
                    return arr
            except Exception:
                return []
    return []


def obter_ou_criar_nota(titulo: str, corpo_inicial: str = "", tags=None, links=None, aliases=None, nome_usuario: str | None = None, tipo_entidade=None, propriedades=None, relacoes=None) -> str:
    """
    Resolve o título para uma nota existente (incluindo typos) ou cria uma nova.
    Se o nome for um typo de nota existente, grava o typo em aliases.
    Na zona de dúvida (70–85%), cria nota nova com tag revisar_entidade.
    Suporta criação/atualização de propriedades e relações estruturadas.
    """
    existente = resolver_entidade(titulo, nome_usuario=nome_usuario)
    caminho_existente = _caminho(existente) if existente else ""
    if existente and os.path.exists(caminho_existente):
        nota_atual = _ler_raw(existente) or ""
        partes = nota_atual.split("---", 2)
        frontmatter = partes[1] if len(partes) >= 2 else ""
        
        # Extrair campos existentes
        aliases_atuais = _frontmatter_campo(frontmatter, "aliases")
        tags_atuais = tags if tags else _frontmatter_campo(frontmatter, "tags")
        links_atuais = links if links else _frontmatter_campo(frontmatter, "links")
        
        # Extrair propriedades e relações existentes
        propriedades_atuais = _frontmatter_objeto(frontmatter, "propriedades")
        relacoes_atuais = _frontmatter_objeto(frontmatter, "relacoes")
        
        # Atualizar aliases
        todas = list(aliases_atuais)
        for a in (aliases or []):
            if str(a).strip() and str(a).strip() not in todas:
                todas.append(str(a).strip())
        if normalizar_nome(titulo) != normalizar_nome(existente) and titulo not in todas:
            todas.append(titulo)
        
        # Atualizar corpo
        corpo = partes[2].strip() if len(partes) >= 3 else (nota_atual.strip() or corpo_inicial)
        if corpo_inicial and corpo_inicial.strip() and corpo_inicial.strip() not in corpo:
            corpo = (corpo + "\n" + corpo_inicial.strip()).strip() if corpo else corpo_inicial.strip()
        
        # Salvar atualizando todas as propriedades
        salvar(existente, corpo, 
                tags=tags_atuais, 
                links=links_atuais, 
                aliases=todas,
                tipo_entidade=tipo_entidade,
                propriedades=propriedades or propriedades_atuais,
                relacoes=relacoes or relacoes_atuais)
        return _caminho(existente)

    tags = list(tags or [])
    hit = _melhor_candidato(titulo)
    if hit and LIMIAR_DUVIDA <= hit[1] < LIMIAR_FUSAO:
        tit_canon, _ = hit
        if "revisar_entidade" not in tags:
            tags.append("revisar_entidade")
        corpo_inicial = (
            (corpo_inicial or "")
            + f"\n\n> [!WARNING] Alerta de Identidade\n"
            + f"> O Sumé detectou que esta nota pode ser um erro de digitação para a entidade: [[{tit_canon}]].\n"
        )
    return salvar(titulo, corpo_inicial, tags=tags, links=links, aliases=aliases,
                  tipo_entidade=tipo_entidade, propriedades=propriedades, relacoes=relacoes)


def _ler_raw(titulo: str) -> str | None:
    """Lê o conteúdo completo do arquivo (frontmatter + corpo), ou None se não existir."""
    try:
        canon = resolver_entidade(titulo) or titulo
        caminho = _caminho(canon)
        if not os.path.exists(caminho):
            caminho = _caminho(titulo)
        if not os.path.exists(caminho):
            return None
        with open(caminho, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        log_erro("vault", str(e))
        return None


def _extrair_relacoes_frentematter(frontmatter: str) -> list[dict]:
    """Extrai lista de relações do frontmatter."""
    return _frontmatter_objeto(frontmatter, "relacoes")


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
    partes = nota_atual.split("---", 2)
    frontmatter = partes[1] if len(partes) >= 2 else ""
    aliases_atuais = _frontmatter_campo(frontmatter, "aliases")
    alias_norm = normalizar_nome(alias)
    if any(normalizar_nome(a) == alias_norm for a in aliases_atuais):
        return False
    novas_aliases = aliases_atuais + [alias]
    corpo = partes[2].strip() if len(partes) >= 3 else nota_atual.strip()
    tags_atuais = _frontmatter_campo(frontmatter, "tags")
    links_atuais = _frontmatter_campo(frontmatter, "links")
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


def salvar(titulo: str, corpo: str, tags=None, links=None, aliases=None, tipo_entidade=None, propriedades=None, relacoes=None) -> str:
    """Cria ou sobrescreve uma nota e devolve o caminho do arquivo."""
    try:
        caminho = _caminho(titulo)
        bruto = ""
        if os.path.exists(caminho):
            with open(caminho, "r", encoding="utf-8") as f:
                bruto = f.read()
        partes_exist = bruto.split("---", 2) if bruto else []
        fm_exist = partes_exist[1] if len(partes_exist) >= 2 else ""
        if tags is None:
            tags = _frontmatter_campo(fm_exist, "tags")
        if links is None:
            links = _frontmatter_campo(fm_exist, "links")
        if aliases is None:
            aliases = _frontmatter_campo(fm_exist, "aliases")
        etiquetas = [t.lstrip("#") for t in (tags or []) if str(t).strip()]
        aliases_lista = [str(a).strip() for a in (aliases or []) if str(a).strip()]
        
        # Format properties as YAML-like dict (simplified)
        propriedades_str = ""
        if propriedades:
            if isinstance(propriedades, dict):
                props_items = list(propriedades.items())
            elif isinstance(propriedades, list):
                props_items = []
                for item in propriedades:
                    if isinstance(item, dict):
                        props_items.extend(item.items())
                    elif isinstance(item, (list, tuple)) and len(item) == 2:
                        props_items.append((str(item[0]), item[1]))
            else:
                props_items = []
            props_list = []
            for k, v in props_items:
                kk = str(k)
                if isinstance(v, str):
                    vv = f'"{v.replace(chr(34), chr(39))}"'
                elif isinstance(v, bool):
                    vv = str(v)
                elif isinstance(v, (int, float)):
                    vv = str(v)
                else:
                    vv = f'"{v}"'
                props_list.append(f'"{kk}": {vv}')
            propriedades_str = "{" + ", ".join(props_list) + "}"
        
        # Format relations as list of dicts
        relacoes_str = ""
        if relacoes:
            rel_list = []
            for rel in relacoes:
                if isinstance(rel, dict):
                    rel_items = []
                    for k, v in rel.items():
                        kk = str(k)
                        if isinstance(v, str):
                            vv = f'"{v.replace(chr(34), chr(39))}"'
                        elif isinstance(v, bool):
                            vv = str(v)  # True/False (round-trip com literal_eval)
                        elif isinstance(v, (int, float)):
                            vv = str(v)
                        else:
                            vv = f'"{v}"'
                        rel_items.append(f'"{kk}": {vv}')
                    rel_list.append("{" + ", ".join(rel_items) + "}")
            relacoes_str = "[" + ", ".join(rel_list) + "]"
        
        linhas = [
            "---",
            f"titulo: {titulo}",
        ]
        if tipo_entidade:
            linhas.append(f"tipo_entidade: {tipo_entidade}")
        if propriedades_str:
            linhas.append(f"propriedades: {propriedades_str}")
        if relacoes_str:
            linhas.append(f"relacoes: {relacoes_str}")
        linhas.append(f"atualizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if etiquetas:
            linhas.append("tags: [" + ", ".join(etiquetas) + "]")
        if links:
            linhas.append("links: [" + ", ".join(str(l) for l in links) + "]")
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
    """Lê o corpo de uma nota, sem o frontmatter. Resolve typos para a nota canônica."""
    try:
        texto = _ler_raw(titulo)
        if texto is None:
            return None
        partes = texto.split("---", 2)
        return partes[2].strip() if len(partes) == 3 else texto.strip()
    except Exception as e:
        log_erro("vault", str(e))
        return None


def listar() -> list[dict]:
    """Lista as notas do vault com título, tags, tipo_entidade, propriedades, relações, corpo e caminho."""
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
            tipo_entidade = None
            propriedades = []
            relacoes = []
            frontmatter = ""
            corpo = texto
            if texto.startswith("---"):
                partes = texto.split("---", 2)
                if len(partes) >= 2:
                    frontmatter = partes[1]
                    # corpo = o que vem depois do segundo "---"
                    if len(partes) >= 3:
                        corpo = partes[2].strip()
            for linha in frontmatter.splitlines():
                if linha.startswith("titulo:"):
                    titulo = linha.split(":", 1)[1].strip()
                elif linha.startswith("tags:"):
                    etiquetas = [
                        t.strip() for t in
                        linha.split(":", 1)[1].strip().strip("[]").split(",")
                        if t.strip()
                    ]
                elif linha.startswith("tipo_entidade:"):
                    tipo_entidade = linha.split(":", 1)[1].strip()
            if frontmatter:
                propriedades = _frontmatter_objeto(frontmatter, "propriedades")
                relacoes = _frontmatter_objeto(frontmatter, "relacoes")
            notas.append({
                "titulo": titulo,
                "tags": etiquetas,
                "tipo_entidade": tipo_entidade,
                "propriedades": propriedades,
                "relacoes": relacoes,
                "corpo": corpo,
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


def obter_relacoes(titulo: str) -> list[dict]:
    """Retorna as relações estruturadas de uma nota, ou lista vazia se não existir."""
    try:
        texto = _ler_raw(titulo)
        if not texto:
            return []
        partes = texto.split("---", 2)
        if len(partes) < 2:
            return []
        return _frontmatter_objeto(partes[1], "relacoes")
    except Exception as e:
        log_erro("vault", str(e))
        return []


def obter_propriedades(titulo: str) -> list[dict]:
    """Retorna as propriedades estruturadas de uma nota, ou lista vazia se não existir."""
    try:
        texto = _ler_raw(titulo)
        if not texto:
            return []
        partes = texto.split("---", 2)
        if len(partes) < 2:
            return []
        return _frontmatter_objeto(partes[1], "propriedades")
    except Exception as e:
        log_erro("vault", str(e))
        return []


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