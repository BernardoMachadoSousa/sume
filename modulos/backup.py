"""
Backup e restauração do cérebro do Sumé.

O "cérebro" tem duas fontes de verdade:
  1. dados/memoria.db  — memória por camadas (sessão/curta/permanente)
  2. o vault .md        — grafo de entidades em texto plano (Obsidian)

Ambas são irrecuperáveis se perdidas, então o backup é feito pelo
`sqlite3.Connection.backup()` (cópia online consistente, sem travar o banco)
e por cópia do arquivo .db já fechado, além de um ZIP do vault.

Padrão: um backup por dia em dados/backups/; retenção das últimas N cópias.
"""

import os
import shutil
import sqlite3
import zipfile
from datetime import datetime
from typing import Any

from utils.logger import info as log_info, erro as log_erro

BACKUP_DIR = os.path.join("dados", "backups")
# Quantos backups manter por sufixo (.db / .zip)
RETENCAO = 10


def _caminho_db() -> str:
    """
    Caminho do banco, lido do módulo a cada chamada.

    Não dá para fazer `from modulos.memoria import DB`: o valor seria
    congelado no import e qualquer reconfiguração do caminho (ou teste com
    path temporário) passaria a apontar para o banco errado.
    """
    from modulos import memoria
    return memoria.DB


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _pasta(diretorio: str | None = None) -> str:
    destino = diretorio or BACKUP_DIR
    os.makedirs(destino, exist_ok=True)
    return destino


def _purgar_antigos(diretorio: str, sufixo: str = ".db", manter: int = RETENCAO) -> int:
    """Mantém apenas as `manter` cópias mais recentes com o sufixo dado."""
    arquivos = sorted(
        (os.path.join(diretorio, f) for f in os.listdir(diretorio) if f.endswith(sufixo)),
        key=os.path.getmtime,
        reverse=True,
    )
    removidos = 0
    for antigo in arquivos[manter:]:
        try:
            os.remove(antigo)
            removidos += 1
        except OSError:
            pass
    return removidos


# ── backup ────────────────────────────────────────────────────────────────────

def backup_memoria(destino: str | None = None) -> str:
    """
    Copia o banco de memória de forma consistente.
    Usa a API de backup do SQLite (não copia o arquivo com o banco aberto,
    o que pode capturar estado inconsistente).
    """
    pasta = _pasta(destino)
    origem = os.path.abspath(_caminho_db())
    if not os.path.exists(origem):
        log_erro("backup", f"banco não encontrado: {origem}")
        return ""

    alvo = os.path.join(pasta, f"memoria_{_timestamp()}.db")
    try:
        src = sqlite3.connect(origem)
        try:
            dst = sqlite3.connect(alvo)
            try:
                src.backup(dst)
            finally:
                dst.close()
        finally:
            src.close()
    except sqlite3.Error as e:
        log_erro("backup", f"falha ao copiar banco: {e}")
        if os.path.exists(alvo):
            os.remove(alvo)
        return ""

    _purgar_antigos(pasta, ".db")
    log_info("backup", f"banco salvo em {alvo}")
    return alvo


def backup_vault(destino: str | None = None) -> str:
    """
    Compacta o vault inteiro em um ZIP.
    O vault é texto puro, então um ZIP por cópia é barato e versionável.
    """
    from modulos import vault

    raiz = vault._pasta_vault()
    if not os.path.isdir(raiz):
        log_erro("backup", f"vault não encontrado: {raiz}")
        return ""

    pasta = _pasta(destino)
    alvo = os.path.join(pasta, f"vault_{_timestamp()}.zip")
    try:
        with zipfile.ZipFile(alvo, "w", zipfile.ZIP_DEFLATED) as z:
            for diretorio, _subpastas, arquivos in os.walk(raiz):
                for nome in arquivos:
                    if not nome.endswith(".md"):
                        continue
                    completo = os.path.join(diretorio, nome)
                    # caminho relativo à raiz do vault, para preservar a hierarquia
                    relativo = os.path.relpath(completo, raiz)
                    z.write(completo, relativo)
    except (OSError, zipfile.BadZipFile) as e:
        log_erro("backup", f"falha ao compactar vault: {e}")
        if os.path.exists(alvo):
            os.remove(alvo)
        return ""

    _purgar_antigos(pasta, ".zip")
    log_info("backup", f"vault salvo em {alvo}")
    return alvo


def backup_completo(destino: str | None = None) -> dict[str, str]:
    """Faz o backup das duas fontes e devolve os caminhos gerados."""
    return {"memoria": backup_memoria(destino), "vault": backup_vault(destino)}


def listar_backups(destino: str | None = None) -> list[dict[str, Any]]:
    """Lista os backups disponíveis, do mais novo para o mais antigo."""
    pasta = destino or BACKUP_DIR
    if not os.path.isdir(pasta):
        return []

    itens: list[dict[str, Any]] = []
    for nome in os.listdir(pasta):
        completo = os.path.join(pasta, nome)
        if not os.path.isfile(completo):
            continue
        if not (nome.endswith(".db") or nome.endswith(".zip")):
            continue
        itens.append({
            "arquivo": nome,
            "caminho": completo,
            "tipo": "memoria" if nome.endswith(".db") else "vault",
            "bytes": os.path.getsize(completo),
            "quando": datetime.fromtimestamp(os.path.getmtime(completo)).strftime("%Y-%m-%d %H:%M"),
        })

    itens.sort(key=lambda x: x["quando"], reverse=True)
    return itens


# ── restauração ───────────────────────────────────────────────────────────────

def restaurar_memoria(caminho: str) -> str:
    """
    Restaura o banco de memória a partir de um arquivo .db de backup.
    Guarda o banco atual em .bak antes de sobrescrever (permite voltar atrás).
    """
    origem = os.path.abspath(caminho)
    if not os.path.exists(origem):
        return "Não encontrei esse arquivo de backup."

    atual = os.path.abspath(_caminho_db())
    if os.path.exists(atual):
        try:
            shutil.copy2(atual, atual + ".bak")
        except OSError as e:
            log_erro("backup", f"não consegui preservar o banco atual: {e}")
            return f"Falha ao preservar o banco atual: {e}"

    try:
        shutil.copy2(origem, atual)
    except OSError as e:
        log_erro("backup", f"falha ao restaurar banco: {e}")
        return f"Falha ao restaurar: {e}"

    log_info("backup", f"banco restaurado de {origem}")
    return f"Memória restaurada de {os.path.basename(origem)}."


def _arquivar_vault(raiz: str) -> str:
    """
    Move as notas atuais do vault para uma pasta irmã chamada
    ".vault-anterior-<timestamp>".

    A pasta tem que ser IRMÃ da raiz, nunca filha: mover um diretório para
    dentro de si mesmo é erro no shutil. Também não pode ser dentro da raiz,
    senão o próximo walk do vault indexaria o backup como se fosse conteúdo.
    """
    marca = _timestamp()
    destino = os.path.join(os.path.dirname(os.path.abspath(raiz)),
                           f".vault-anterior-{marca}")
    contador = 1
    while os.path.exists(destino):
        destino = os.path.join(os.path.dirname(os.path.abspath(raiz)),
                               f".vault-anterior-{marca}-{contador}")
        contador += 1
    shutil.move(raiz, destino)
    os.makedirs(raiz, exist_ok=True)
    return destino


def restaurar_vault(caminho: str) -> str:
    """
    Restaura o vault de um ZIP de backup.
    Não sobrescreve nada silenciosamente: as notas existentes são movidas
    para uma pasta .vault-anterior-<timestamp>/ e o ZIP é extraído por cima.
    """
    origem = os.path.abspath(caminho)
    if not os.path.exists(origem):
        return "Não encontrei esse arquivo de backup."

    from modulos import vault

    raiz = vault._pasta_vault()
    os.makedirs(raiz, exist_ok=True)

    arquivo = ""
    if os.listdir(raiz):
        try:
            arquivo = _arquivar_vault(raiz)
        except OSError as e:
            log_erro("backup", f"falha ao arquivar vault atual: {e}")
            return f"Falha ao arquivar o vault atual: {e}"

    try:
        with zipfile.ZipFile(origem, "r") as z:
            z.extractall(raiz)
    except (OSError, zipfile.BadZipFile) as e:
        log_erro("backup", f"zip inválido: {e}")
        return f"Esse backup não é um ZIP válido: {e}"

    log_info("backup", f"vault restaurado de {origem}")
    msg = f"Vault restaurado de {os.path.basename(origem)}."
    if arquivo:
        msg += f" Suas notas anteriores ficaram em {os.path.basename(arquivo)}."
    return msg


def restaurar(arquivo: str) -> str:
    """Despacha a restauração pelo tipo do arquivo (.db ou .zip)."""
    if arquivo.lower().endswith(".db"):
        return restaurar_memoria(arquivo)
    if arquivo.lower().endswith(".zip"):
        return restaurar_vault(arquivo)
    return "Só restauro backups .db (memória) ou .zip (vault)."
