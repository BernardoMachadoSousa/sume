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

ROOT = "dados/vault"
LIMITE_CONTEXTO = 4000


def _caminho(titulo: str) -> str:
    """Converte o título num nome de arquivo seguro."""
    base = unicodedata.normalize("NFKD", titulo)
    base = base.encode("ascii", "ignore").decode("ascii").lower()
    base = re.sub(r"[^\w\s-]", "", base).strip()
    base = re.sub(r"[\s_]+", "-", base)
    base = re.sub(r"-{2,}", "-", base).strip("-")
    return os.path.join(ROOT, f"{base or 'nota'}.md")


def salvar(titulo: str, corpo: str, tags=None, links=None) -> str:
    """Cria ou sobrescreve uma nota e devolve o caminho do arquivo."""
    try:
        os.makedirs(ROOT, exist_ok=True)
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
        linhas += ["---", "", corpo.strip(), ""]

        with open(caminho, "w", encoding="utf-8") as f:
            f.write("\n".join(linhas))
        return caminho
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
        if not os.path.isdir(ROOT):
            return []
        notas = []
        for nome in sorted(os.listdir(ROOT)):
            if not nome.endswith(".md"):
                continue
            caminho = os.path.join(ROOT, nome)
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
