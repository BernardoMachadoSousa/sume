import json
import os

ARQUIVO = "dados/memorias.json"

def carregar() -> dict:
    if os.path.exists(ARQUIVO):
        with open(ARQUIVO, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def salvar(dados: dict):
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

def guardar(chave: str, valor: str):
    dados = carregar()
    dados[chave] = valor
    salvar(dados)

def lembrar(chave: str) -> str:
    dados = carregar()
    return dados.get(chave, None)

def processar_memoria(comando: str) -> str | None:
    # Guardar nome
    if "meu nome é" in comando:
        nome = comando.split("é")[-1].strip()
        guardar("nome", nome)
        return f"Prazer, {nome}! Vou me lembrar disso."

    if "me chamo" in comando:
        nome = comando.split("chamo")[-1].strip()
        guardar("nome", nome)
        return f"Prazer, {nome}! Vou me lembrar disso."

    # Perguntar nome
    if "meu nome" in comando or "quem sou eu" in comando:
        nome = lembrar("nome")
        if nome:
            return f"Seu nome é {nome}."
        return "Ainda não sei seu nome. Me diga: 'meu nome é...'"

    return None