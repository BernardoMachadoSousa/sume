def detectar(comando: str) -> tuple | None:
    if "meu nome é" in comando:
        nome = comando.split("é")[-1].strip()
        return ("MEMORY_SAVE", nome, 1.0)
    if "me chamo" in comando:
        nome = comando.split("chamo")[-1].strip()
        return ("MEMORY_SAVE", nome, 1.0)
    if "meu nome" in comando or "quem sou eu" in comando:
        return ("MEMORY_READ", "", 1.0)
    return None