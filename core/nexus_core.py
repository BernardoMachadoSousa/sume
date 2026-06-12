from modulos.memoria import processar_memoria
from modulos.memoria import carregar as carregar_memorias
from modulos.automacoes import executar
from modulos.ia_conversacional import perguntar_ia

def processar(comando: str) -> str:
    comando = comando.lower().strip()

    # Memória
    resposta_memoria = processar_memoria(comando)
    if resposta_memoria:
        return resposta_memoria

    # Se é um programa conhecido sem "abrir", adiciona
    programas = ["calculadora", "notas", "bloco de notas", "cmd", "terminal",
                 "word", "excel", "powerpoint", "paint", "chrome", "navegador",
                 "youtube", "google", "github", "gmail", "netflix", "spotify"]
    for p in programas:
        if p in comando and "abrir" not in comando and "fechar" not in comando:
            comando = "abrir " + comando
            break

    # Automações
    resposta_auto = executar(comando)
    if resposta_auto:
        return resposta_auto

    # Horas
    if "horas" in comando or "hora" in comando:
        from datetime import datetime
        hora = datetime.now().strftime("%H:%M")
        return f"São {hora}."

    # Nome do assistente
    if "seu nome" in comando or "quem é você" in comando:
        return "Meu nome é Nexus, seu assistente pessoal."

    # Agradecimento
    if "obrigado" in comando or "valeu" in comando:
        return "Por nada, estou aqui para ajudar."

    # Sair
    if "tchau" in comando or "sair" in comando or "desligar" in comando:
        return "desligar"

    # IA Conversacional (fallback para qualquer outra coisa)
    contexto = ""
    memorias = carregar_memorias()
    if memorias:
        contexto = "\n".join([f"{k}: {v}" for k, v in memorias.items()])

    return perguntar_ia(comando, contexto)