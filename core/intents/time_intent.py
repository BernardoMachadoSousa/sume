def detectar(comando: str) -> tuple | None:
    if "hora" in comando:
        return ("GET_TIME", "", 0.9)
    return None