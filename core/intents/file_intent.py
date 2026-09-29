def detectar(comando: str) -> tuple | None:
    prefixos = (
        "abrir o arquivo ",
        "abre o arquivo ",
        "abra o arquivo ",
        "abrir arquivo ",
        "abre arquivo ",
        "abra arquivo ",
        "abrir o documento ",
        "abre o documento ",
        "abra o documento ",
        "abrir documento ",
        "abre documento ",
        "abra documento ",
        "abrir o pdf ",
        "abre o pdf ",
        "abra o pdf ",
        "abrir pdf ",
    )
    for prefixo in prefixos:
        if comando.startswith(prefixo):
            alvo = comando[len(prefixo):].strip()
            if alvo:
                return ("OPEN_FILE", alvo, 0.92)
    return None
