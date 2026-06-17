"""
Módulo de memória do Sumé.
Armazena dados em SQLite (robusto, sem JSON).
"""

import sqlite3
import os

DB = "dados/memoria.db"

def _conectar():
    os.makedirs("dados", exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.execute("CREATE TABLE IF NOT EXISTS memoria (chave TEXT PRIMARY KEY, valor TEXT)")
    conn.commit()
    return conn

def guardar(chave: str, valor: str):
    with _conectar() as conn:
        conn.execute("INSERT OR REPLACE INTO memoria (chave, valor) VALUES (?, ?)", (chave, valor))

def lembrar(chave: str) -> str | None:
    with _conectar() as conn:
        cursor = conn.execute("SELECT valor FROM memoria WHERE chave = ?", (chave,))
        row = cursor.fetchone()
        return row[0] if row else None

def carregar() -> dict:
    with _conectar() as conn:
        rows = conn.execute("SELECT chave, valor FROM memoria").fetchall()
        return dict(rows)

def processar_memoria(comando: str) -> str | None:
    comando = comando.lower().strip()

    if "meu nome é" in comando:
        nome = comando.split("é")[-1].strip()
        guardar("nome", nome)
        return f"Prazer, {nome}! Vou me lembrar disso."

    if "me chamo" in comando:
        nome = comando.split("chamo")[-1].strip()
        guardar("nome", nome)
        return f"Prazer, {nome}! Vou me lembrar disso."

    if "meu nome" in comando or "quem sou eu" in comando:
        nome = lembrar("nome")
        if nome:
            return f"Seu nome é {nome}."
        return "Ainda não sei seu nome. Me diga: 'meu nome é...'"

    return None


# Migração única: copia dados do JSON antigo para SQLite
def _migrar_json():
    json_path = "dados/memorias.json"
    if os.path.exists(json_path):
        import json
        with open(json_path, "r", encoding="utf-8") as f:
            dados = json.load(f)
        for chave, valor in dados.items():
            guardar(chave, valor)
        os.rename(json_path, json_path + ".backup")
        print("[Memoria] Dados migrados do JSON para SQLite.")

# Executa migração ao importar
_migrar_json()