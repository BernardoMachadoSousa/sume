def detectar(comando: str) -> tuple:
    c = comando.lower().strip()
    
    gatilhos = [
        "pesquise na internet",
        "busque na internet",
        "procure na web",
        "pesquise no google",
        "na internet sobre",
        "pesquisar sobre",
        "saiba sobre",
        "descubra quem é",
        "descubra o que é",
        "quanto tá o dólar",
        "quanto está o dólar"
    ]
    
    for g in gatilhos:
        if g in c or c.startswith("pesquise"):
            return ("WEB_SEARCH", comando, 0.9)
            
    return None
