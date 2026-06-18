"""
Módulo de memória do Sumé.
Armazena dados em SQLite.
Apenas salva e recupera — não interpreta comandos.
"""

import sqlite3
import os
from utils.logger import erro as log_erro

DB = "dados/memoria.db"

def _conectar():
    os.makedirs("dados", exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.execute("CREATE TABLE IF NOT EXISTS memoria (chave TEXT PRIMARY KEY, valor TEXT)")
    conn.commit()
    return conn

def guardar(chave: str, valor: str):
    try:
        with _conectar() as conn:
            conn.execute("INSERT OR REPLACE INTO memoria (chave, valor) VALUES (?, ?)", (chave, valor))
    except Exception as e:
        log_erro("memoria", str(e))

def lembrar(chave: str) -> str | None:
    try:
        with _conectar() as conn:
            cursor = conn.execute("SELECT valor FROM memoria WHERE chave = ?", (chave,))
            row = cursor.fetchone()
            return row[0] if row else None
    except Exception as e:
        log_erro("memoria", str(e))
        return None

def carregar() -> dict:
    try:
        with _conectar() as conn:
            rows = conn.execute("SELECT chave, valor FROM memoria").fetchall()
            return dict(rows)
    except Exception as e:
        log_erro("memoria", str(e))
        return {}

def guardar_nome(nome: str) -> str:
    guardar("nome_usuario", nome)
    return f"Prazer, {nome}! Vou me lembrar disso."

def obter_nome() -> str | None:
    return lembrar("nome_usuario")

def processar_memoria(comando: str) -> str | None:
    comando = comando.lower().strip()

    if "meu nome é" in comando:
        nome = comando.split("é")[-1].strip()
        return guardar_nome(nome)

    if "me chamo" in comando:
        nome = comando.split("chamo")[-1].strip()
        return guardar_nome(nome)

    if "meu nome" in comando or "quem sou eu" in comando:
        nome = obter_nome()
        if nome:
            return f"Seu nome é {nome}."
        return "Ainda não sei seu nome. Me diga: 'meu nome é...'"

    return None

def _migrar_json():
    json_path = "dados/memorias.json"
    if os.path.exists(json_path):
        try:
            import json
            with open(json_path, "r", encoding="utf-8") as f:
                dados = json.load(f)
            for chave, valor in dados.items():
                guardar(chave, valor)
            os.rename(json_path, json_path + ".backup")
            print("[Memoria] Dados migrados do JSON para SQLite.")
        except Exception as e:
            log_erro("memoria", f"Migração: {e}")

_migrar_json()