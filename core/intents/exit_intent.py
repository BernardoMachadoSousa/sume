def detectar(comando: str) -> tuple | None:
    if any(p in comando for p in ["tchau", "sair", "desligar"]):
        return ("EXIT", "", 1.0)
    return None