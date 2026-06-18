def detectar(comando: str) -> tuple | None:
    for prefixo in ["abrir ", "abre ", "abra "]:
        if comando.startswith(prefixo):
            alvo = comando[len(prefixo):].strip()
            if alvo:
                return ("OPEN_APP", alvo, 1.0)
    return None