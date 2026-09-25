def detectar(comando: str) -> tuple | None:
    if "pasta" in comando:
        alvo = comando.replace("abrir", "").replace("abra", "").replace("abre", "").replace("pasta", "").strip()
        if alvo:
            return ("OPEN_FOLDER", alvo, 0.75)
    return None