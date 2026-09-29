"""
Gerenciador de arquivos do Sumé (Etapa 6).
Abre arquivos encontrados nas pastas de busca configuradas.
"""

import os
from datetime import datetime

from plugins.busca.arquivos import buscar_por_nome, _get_search_paths
from plugins.seguranca import validar_caminho_arquivo
from utils.logger import erro as log_erro, info as log_info

EXTENSOES_BLOQUEADAS = {
    ".exe", ".bat", ".cmd", ".ps1", ".msi", ".scr", ".com", ".vbs", ".lnk",
}

_abrir_caminho = os.startfile


def _raizes_permitidas() -> list[str]:
    home = os.path.abspath(os.path.expanduser("~"))
    raizes = [home]
    for pasta in _get_search_paths():
        abs_pasta = os.path.abspath(pasta)
        if abs_pasta not in raizes:
            raizes.append(abs_pasta)
    return raizes


def _esta_dentro(caminho: str, raiz: str) -> bool:
    c = os.path.normcase(os.path.abspath(caminho))
    r = os.path.normcase(os.path.abspath(raiz))
    return c == r or c.startswith(r + os.sep)


def caminho_seguro(caminho: str) -> bool:
    if not caminho or not validar_caminho_arquivo(caminho):
        return False
    abs_c = os.path.abspath(caminho)
    if not os.path.isfile(abs_c):
        return False
    _, ext = os.path.splitext(abs_c)
    if ext.lower() in EXTENSOES_BLOQUEADAS:
        return False
    return any(_esta_dentro(abs_c, raiz) for raiz in _raizes_permitidas())


def _anotar_abertura(nome: str) -> None:
    try:
        from modulos.diario import anotar_no_diario
        agora = datetime.now().strftime("%H:%M")
        anotar_no_diario(f"- {agora} abri o arquivo {nome}\n")
    except Exception as e:
        log_erro("arquivos", f"falha ao anotar no diario: {e}")


def abrir(nome: str) -> str:
    if not nome or not nome.strip():
        return "Qual arquivo você quer abrir?"

    candidatos = buscar_por_nome(nome.strip())
    if not candidatos:
        return f"Não encontrei o arquivo '{nome}'."

    melhores = [c for c in candidatos if c["score"] >= 0.9]
    if len(melhores) == 1:
        escolhido = melhores[0]
    elif len(candidatos) == 1:
        escolhido = candidatos[0]
    else:
        lista = ", ".join(c["nome"] for c in candidatos[:5])
        return f"Encontrei vários: {lista}. Qual você quer abrir?"

    caminho = escolhido["caminho"]
    if not caminho_seguro(caminho):
        log_erro("arquivos", f"caminho bloqueado: {caminho}")
        return "Não posso abrir esse arquivo."

    try:
        _abrir_caminho(caminho)
    except Exception as e:
        log_erro("arquivos", f"erro ao abrir {caminho}: {e}")
        return f"Erro ao abrir {escolhido['nome']}."

    log_info("arquivos", f"aberto: {caminho}")
    _anotar_abertura(escolhido["nome"])
    return f"Abrindo {escolhido['nome']}."
