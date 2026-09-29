import re


_GATILHOS_SAVE = [
    "minha namorada",
    "meu namorado",
    "minha mãe",
    "meu pai",
    "minha irmã",
    "meu irmão",
    "meu amigo",
    "minha amiga",
    r"aniversário d[ao]",
    r"data de nascimento d[ao]",
    r"nasceu em",
    r"nasceu no dia",
    "salvar que",
    "salva que",
    "salve que",
    "anota no cérebro",
    "anote no cérebro",
    "guarda no cérebro",
    "guarde no cérebro",
    "salvar no cérebro",
    "salve no cérebro",
    "lembre-se que",
    "não esqueça que",
]

_GATILHOS_READ = [
    r"quando [eé] o anivers[aá]rio",
    r"qual [eé] o anivers[aá]rio",
    r"o que (?:voc[eê]\s*|vc\s*)sabe sobre",
    r"o que sabe sobre",
    r"me fala sobre",
    r"me fal[ea] sobre",
    r"me conta sobre",
    r"quem [eé] ([A-Za-zÀ-ú\s]+)",
    r"ler nota d[ao]",
    r"ler nota sobre",
    r"quando eu nasci",
    r"qual[ \w]*meu anivers[aá]rio",
    r"qual[ \w]*minha data de nascimento",
    r"o que (?:voc[eê]\s*|vc\s*)tem guardado sobre",
    r"o que (?:voc[eê]\s*|vc\s*)anotou sobre",
]


def detectar(comando: str) -> tuple | None:
    c = comando.lower().strip()

    # Filtros de salvamento baseados em regex (para capturar os mais óbvios rapidamente)
    for padrao in _GATILHOS_READ:
        if re.search(padrao, c):
            m = re.search(padrao, c)
            alvo = m.group(1) if m and m.lastindex else c
            return ("CEREBRO_READ", alvo, 0.91)

    for padrao in _GATILHOS_SAVE:
        if re.search(padrao, c):
            return ("CEREBRO_SAVE", comando, 0.93)
            
    # LLM fallback: o `chat_intent.py` (ou `memoria.py`) pegariam, mas queremos que 
    # se o cara disser "a malu gosta de café" num tom declarativo, a gente jogue pro cérebro.
    # Por segurança de velocidade, vamos capturar sentenças declarativas fortes que citem 'meu', 'minha'
    if ("meu " in c or "minha " in c or " se chama " in c or "me chamo " in c) and len(c.split()) > 2:
        # Se for pergunta (?), ignora pro SAVE
        if "?" not in c:
            return ("CEREBRO_SAVE", comando, 0.94)

    return None
