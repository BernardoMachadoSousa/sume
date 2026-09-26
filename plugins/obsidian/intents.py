def detectar(comando: str) -> tuple:
    c = comando.lower().strip()
    
    gatilhos = [
        "obsidian",
        "nas minhas notas",
        "na minha nota",
        "no meu cofre",
        "nas anotações",
        "nas minhas anotações",
        "o que eu escrevi sobre",
        "pesquise no obsidian"
    ]
    
    for g in gatilhos:
        if g in c:
            # Tenta extrair o assunto. Simplificadamente, o comando todo vai.
            # O processamento da IA filtrará o que precisa buscar.
            return ("OBSIDIAN_SEARCH", comando, 0.9)
            
    return None
