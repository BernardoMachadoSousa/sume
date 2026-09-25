def detectar(comando: str) -> tuple | None:
    for prefixo in ["abrir ", "abre ", "abra "]:
        if comando.startswith(prefixo):
            alvo = comando[len(prefixo):].strip()
            if alvo:
                # "abrir pasta X" também casa com folder_intent (OPEN_FOLDER)
                # com confiança parecida - de propósito, pra virar ambiguidade
                # real em vez de decidir por acaso pela ordem da lista.
                return ("OPEN_APP", alvo, 0.75)
    return None