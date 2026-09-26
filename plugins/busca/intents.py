"""
Intents do plugin de busca.
Define os padrões de voz que ativam as funções de busca.
"""

INTENTS = {
    "BUSCAR_NOTAS": [
        r"(?:buscar|procurar|pesquisar)(?: em)?(?: minhas? )?anotaç(?:ões|oes)",
        r"(?:o que|quando|onde|como)(?: você sabe| é| está)(?: em)?(?: minhas? )?anotaç(?:ões|oes)",
        r"(?:lembrar|recordar)(?: de| o que)(?: você anotou| eu disse)"
    ],
    
    "BUSCAR_ARQUIVOS": [
        r"(?:buscar|procurar|pesquisar|localizar)(?: um| o| a| os| as)?(?: arquivo| documento| imagem| foto| vídeo| programa)?(?:\s+.*?)(?: no| no meu| na minha| no computador| no pc)",
        r"(?:onde está| onde fica| localizar)(?: o| a| os| as)?(?: arquivo| documento| imagem| foto| vídeo| programa)(?:\s+.*?)",
        r"(?:encontrar| achar)(?: o| a| os| as)?(?: arquivo| documento| imagem| foto| vídeo| programa)(?:\s+.*?)"
    ]
}