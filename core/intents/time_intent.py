def detectar(comando: str) -> tuple | None:
    if "hora" in comando:
        return ("GET_TIME", "", 0.9)
    _data = ("data" in comando or "dia" in comando or "hoje" in comando
             or "semana" in comando or "mês" in comando)
    if _data and "hora" not in comando:
        return ("GET_DATE", "", 0.9)
    return None