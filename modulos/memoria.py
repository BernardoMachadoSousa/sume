"""
Módulo de memória do Sumé.
Armazena dados em SQLite.
Apenas salva e recupera — não interpreta comandos.

Três camadas, com prazo de validade:
  sessao     some quando o processo termina, não vai para o disco
  curta      dura alguns dias, some sozinha
  permanente não expira

O que é privacy-sensitive fica na camada curta ou na permanente, nunca na
sessão, e nada disso vai para um modelo remoto sem autorização explícita.
"""

import sqlite3
import os
import time
from datetime import datetime, timedelta

from utils.logger import erro as log_erro

DB = "dados/memoria.db"

SESSAO = "sessao"
CURTA = "curta"
PERMANENTE = "permanente"
CAMADAS = (SESSAO, CURTA, PERMANENTE)

# dias até a expiração, por camada
TTL = {SESSAO: 0, CURTA: 7, PERMANENTE: None}

_sessao: dict[str, tuple[str, float | None]] = {}


def _conectar():
    os.makedirs("dados", exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS memoria ("
        "chave TEXT PRIMARY KEY, valor TEXT, camada TEXT, expira_em REAL)"
    )
    # Quem já tinha o banco no formato antigo (só chave/valor) precisa das
    # colunas novas: CREATE TABLE IF NOT EXISTS não adiciona coluna nenhuma.
    # Sem isto, todo INSERT passa a estourar "no such column: camada".
    existentes = {linha[1] for linha in conn.execute("PRAGMA table_info(memoria)")}
    if "camada" not in existentes:
        conn.execute(
            "ALTER TABLE memoria ADD COLUMN camada TEXT NOT NULL DEFAULT 'permanente'"
        )
    if "expira_em" not in existentes:
        conn.execute("ALTER TABLE memoria ADD COLUMN expira_em REAL")
    conn.commit()
    return conn


def _purgar(conn):
    """Remove do disco o que já venceu o TTL."""
    agora = time.time()
    conn.execute(
        "DELETE FROM memoria WHERE expira_em IS NOT NULL AND expira_em < ?", (agora,)
    )


def guardar(chave: str, valor: str, camada: str = PERMANENTE):
    """
    Salva um valor. `camada` decide onde ele vive e se expira.
    Na sessão o valor não toca o disco.
    """
    if camada not in CAMADAS:
        camada = PERMANENTE
    ttl = TTL[camada]
    expira = (time.time() + ttl * 86400) if ttl else None
    try:
        if camada == SESSAO:
            _sessao[chave] = (valor, expira)
            return
        with _conectar() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO memoria (chave, valor, camada, expira_em)"
                " VALUES (?, ?, ?, ?)",
                (chave, valor, camada, expira),
            )
    except Exception as e:
        log_erro("memoria", str(e))


def lembrar(chave: str) -> str | None:
    """Busca um valor em qualquer camada, da mais volátil para a fixa."""
    if chave in _sessao:
        valor, expira = _sessao[chave]
        if expira is not None and time.time() > expira:
            del _sessao[chave]
            return None
        return valor
    try:
        with _conectar() as conn:
            _purgar(conn)
            conn.commit()
            row = conn.execute(
                "SELECT valor FROM memoria WHERE chave = ?", (chave,)
            ).fetchone()
            return row[0] if row else None
    except Exception as e:
        log_erro("memoria", str(e))
        return None


def carregar(camada: str | None = None) -> dict:
    """Devolve tudo, ou só uma camada. Vencidos já vêm filtrados."""
    resultado = {}
    if camada in (None, SESSAO):
        agora = time.time()
        for chave, (valor, expira) in list(_sessao.items()):
            if expira is not None and agora > expira:
                del _sessao[chave]
            else:
                resultado[chave] = valor
    if camada in (None, CURTA, PERMANENTE):
        try:
            with _conectar() as conn:
                _purgar(conn)
                conn.commit()
                if camada:
                    rows = conn.execute(
                        "SELECT chave, valor FROM memoria WHERE camada = ?", (camada,)
                    ).fetchall()
                else:
                    rows = conn.execute("SELECT chave, valor FROM memoria").fetchall()
                resultado.update(dict(rows))
        except Exception as e:
            log_erro("memoria", str(e))
    return resultado


def esquecer(chave: str) -> bool:
    """Apaga a chave de todas as camadas."""
    removido = _sessao.pop(chave, None) is not None
    try:
        with _conectar() as conn:
            cur = conn.execute("DELETE FROM memoria WHERE chave = ?", (chave,))
            removido = removido or cur.rowcount > 0
            conn.commit()
        return removido
    except Exception as e:
        log_erro("memoria", str(e))
        return removido


def limpar_sessao():
    """Encerra a camada de sessão."""
    _sessao.clear()


def expira_em(chave: str) -> datetime | None:
    """Quando essa chave vence, se vencer."""
    if chave in _sessao:
        valor, expira = _sessao[chave]
        return datetime.fromtimestamp(expira) if expira else None
    try:
        with _conectar() as conn:
            row = conn.execute(
                "SELECT expira_em FROM memoria WHERE chave = ?", (chave,)
            ).fetchone()
            if row and row[0]:
                return datetime.fromtimestamp(row[0])
    except Exception as e:
        log_erro("memoria", str(e))
    return None


def guardar_nome(nome: str) -> str:
    guardar("nome_usuario", nome, PERMANENTE)
    return f"Prazer, {nome}! Vou me lembrar disso."

def obter_nome() -> str | None:
    return lembrar("nome_usuario")


def _camada_do_comando(comando: str) -> str:
    """Deduza a camada a partir de palavras como 'por Some dias'."""
    if "nesta sessão" in comando or "por enquanto" in comando:
        return SESSAO
    for dias, camada in (("uma hora", CURTA), ("hoje", CURTA), ("amanhã", CURTA),
                         ("semana", CURTA), ("alguns dias", CURTA)):
        if dias in comando:
            return camada
    if any(p in comando for p in ("sempre", "permanente", "para sempre", "definitivo")):
        return PERMANENTE
    return CURTA


def _extrair_nome(texto: str, marcador: str) -> str:
    """Pega o nome preservando a capitalização original."""
    i = texto.lower().find(marcador)
    if i < 0:
        return texto.split(marcador)[-1].strip()
    return texto[i + len(marcador):].strip(" .?!\n\t")


def processar_memoria(comando: str) -> str | None:
    """
    Interpreta frases de memória. Devolve None quando o comando não é
    sobre memória, para o roteador seguir o fluxo normal.
    """
    original = comando
    comando = comando.lower().strip()

    # O nome é dado próprio: extrai do texto original, antes do lower(),
    # senão "meu nome é Bernardo" seria guardado como "bernardo".
    if "meu nome é" in comando:
        nome = _extrair_nome(original, "meu nome é")
        return guardar_nome(nome)

    if "me chamo" in comando:
        nome = _extrair_nome(original, "me chamo")
        return guardar_nome(nome)

    if "meu nome" in comando or "quem sou eu" in comando:
        nome = obter_nome()
        if nome:
            return f"Seu nome é {nome}."
        return "Ainda não sei seu nome. Me diga: 'meu nome é...'"

    if "esqueça" in comando or "esquece" in comando or "apague" in comando:
        return _processar_esquecer(original)

    if any(p in comando for p in ("anote", "anota", "guarde", "guarda",
                                  "lembre-se", "lembra que", "salve")):
        return _processar_anotar(original)

    if any(p in comando for p in ("o que você sabe", "o que voce sabe",
                                  "quais memórias", "quais memorias",
                                  "mostre memórias", "mostre memorias",
                                  "minhas memórias", "minhas memorias")):
        return _processar_listar()

    if any(p in comando for p in ("no vault", "no obsidian", "anote no vault",
                                  "guarde no vault", "crie uma nota")):
        return _processar_vault(original)

    return None


def _processar_anotar(comando: str) -> str:
    """'anote que X' grava na camada deduzida do próprio comando."""
    for marcador in ("anote que ", "anota que ", "guarde que ", "lembre-se que ",
                     "lembra que ", "salve que "):
        if marcador in comando.lower():
            conteudo = comando.lower().split(marcador, 1)[1].strip(" .?!")
            if not conteudo:
                return "Me diz o que eu devo anotar."
            camada = _camada_do_comando(comando.lower())
            chave = conteudo[:60]
            guardar(chave, conteudo, camada)
            rotulo = {
                SESSAO: "Só nesta sessão",
                CURTA: "Guardei por alguns dias",
                PERMANENTE: "Guardei para sempre",
            }[camada]
            return f"{rotulo}: {conteudo}"
    return None


def _processar_esquecer(comando: str) -> str | None:
    """'esqueça que X' apaga a memória correspondente."""
    for marcador in ("esqueça que ", "esquece que ", "apague que "):
        if marcador in comando.lower():
            trecho = comando.lower().split(marcador, 1)[1].strip(" .?!")
            if not trecho:
                return "Me diz o que devo esquecer."
            alvo = trecho[:60]
            if esquecer(alvo):
                return f"Esqueci: {trecho}"
            return f"Não tinha nada guardado sobre {trecho}."
    return None


def _processar_listar() -> str:
    """Mostra o que está guardado, por camada."""
    partes = []
    for camada, titulo in ((SESSAO, "nesta sessão"),
                           (CURTA, "por alguns dias"),
                           (PERMANENTE, "para sempre")):
        itens = carregar(camada)
        if itens:
            partes.append(f"{titulo}: " + ", ".join(f"{k} = {v}" for k, v in itens.items()))
    if not partes:
        return "Ainda não guardei nada sobre você."
    return " | ".join(partes)


def _processar_vault(comando: str) -> str:
    """'anote no vault que X' cria uma nota em Markdown."""
    from modulos import vault

    for marcador in ("anote no vault que ", "anota no vault que ",
                     "guarde no vault que ", "crie uma nota que "):
        if marcador in comando.lower():
            corpo = comando.lower().split(marcador, 1)[1].strip(" .?!")
            if not corpo:
                return "Me diz o que devo escrever na nota."
            titulo = corpo.split()[0].strip(",.").capitalize() + " - " + " ".join(
                corpo.split()[1:4]
            ).strip(",.")
            caminho = vault.salvar(titulo, corpo)
            if caminho:
                return f"Anotei no vault: {caminho}"
            return "Não consegui escrever a nota no vault."
    return "Use assim: anote no vault que ..."

def _migrar_json():
    json_path = "dados/memorias.json"
    if os.path.exists(json_path):
        try:
            import json
            with open(json_path, "r", encoding="utf-8") as f:
                dados = json.load(f)
            for chave, valor in dados.items():
                guardar(chave, valor)
            os.replace(json_path, json_path + ".backup")
            print("[Memoria] Dados migrados do JSON para SQLite.")
        except Exception as e:
            log_erro("memoria", f"Migração: {e}")

_migrar_json()