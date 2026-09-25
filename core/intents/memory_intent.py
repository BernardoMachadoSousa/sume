def detectar(comando: str) -> tuple | None:
    if "meu nome é" in comando:
        nome = comando.split("é")[-1].strip()
        return ("MEMORY_SAVE", nome, 0.95)
    if "me chamo" in comando:
        nome = comando.split("chamo")[-1].strip()
        return ("MEMORY_SAVE", nome, 0.95)
    if "quem sou eu" in comando:
        return ("MEMORY_READ", "", 0.85)
    if "meu nome" in comando:
        return ("MEMORY_READ", "", 0.75)
    return None