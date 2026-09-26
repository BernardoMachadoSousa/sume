"""
Intents do plugin de busca.
Define os padrões de voz que ativam as funções de busca.
"""

INTENTS = {
    "BUSCAR_NOTAS": [
        r"buscar.*notas",
        r"buscar.*anotacoes",
        r"procurar.*notas",
        r"pesquisar.*notas",
        r"lembrar.*anotado"
    ],
    
    "BUSCAR_ARQUIVOS": [
        r"buscar.*arquivo",
        r"buscar.*documento",
        r"procurar.*arquivo",
        r"onde.*arquivo",
        r"localizar.*arquivo"
    ]
}