def detectar(comando: str) -> tuple | None:
    for prefixo in ["fechar ", "fecha ", "feche "]:
        if comando.startswith(prefixo):
            alvo = comando[len(prefixo):].strip()
            if alvo:
                return ("CLOSE_APP", alvo, 1.0)
    return None