def detectar(comando: str) -> tuple | None:
    if "hora" in comando:
        return ("GET_TIME", "", 1.0)
    return None