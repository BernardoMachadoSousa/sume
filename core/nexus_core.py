"""
Nexus Core - Cérebro do Sumé.
Usa IA local (Phi-3) para interpretar intenções e rotear comandos.
"""

from modulos.memoria import processar_memoria
from modulos.memoria import carregar as carregar_memorias
from modulos.automacoes import executar
from modulos.ia_conversacional import conversar


def _interpretar_comando(comando: str) -> tuple:
    """Interpreta o comando: regras diretas primeiro, IA conversacional como fallback."""
    
    # Desligar
    if any(p in comando for p in ["tchau", "sair", "desligar"]):
        return "desligar", ""

    # Horas
    if "hora" in comando:
        return "horas", ""

    # Nome
    if "meu nome é" in comando:
        nome = comando.replace("meu nome é", "").strip()
        return "nome", nome
    if "qual é o meu nome" in comando or "qual o meu nome" in comando:
        return "nome", ""

    # Abrir (comando começa com abrir/abre/abra)
    for prefixo in ["abrir ", "abre ", "abra "]:
        if comando.startswith(prefixo):
            alvo = comando[len(prefixo):].strip()
            if alvo:
                return "abrir", alvo

    # Fechar (comando começa com fechar/fecha/feche)
    for prefixo in ["fechar ", "fecha ", "feche "]:
        if comando.startswith(prefixo):
            alvo = comando[len(prefixo):].strip()
            if alvo:
                return "fechar", alvo

    # Se chegou aqui, é conversa — não tenta interpretar como abrir/fechar
    return "conversa", comando


def processar(comando: str) -> str:
    """Processa um comando de voz ou texto e retorna a resposta."""
    comando = comando.lower().strip()

    # 1. Memória (nome do usuário)
    resposta_memoria = processar_memoria(comando)
    if resposta_memoria:
        return resposta_memoria

    # 2. IA interpreta a intenção
    acao, alvo = _interpretar_comando(comando)
    print(f"[Nexus] Intenção: {acao} -> {alvo}")

    # 3. Roteia conforme a ação
    if acao == "abrir" and alvo:
        resposta = executar(f"abrir {alvo}")
        if resposta:
            return resposta

    elif acao == "fechar" and alvo:
        resposta = executar(f"fechar {alvo}")
        if resposta:
            return resposta

    elif acao == "horas":
        from datetime import datetime
        return f"São {datetime.now().strftime('%H:%M')}."

    elif acao == "nome" and alvo:
        return processar_memoria(f"meu nome é {alvo}")

    elif acao == "nome":
        return processar_memoria("qual é o meu nome")

    elif acao == "desligar":
        return "desligar"


    # 4. Fallback final: IA conversacional
    memorias = carregar_memorias()
    nome = memorias.get("nome_usuario") if memorias else None
    return conversar(comando, nome_usuario=nome)