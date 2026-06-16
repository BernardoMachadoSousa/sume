"""
Módulo de IA Conversacional do Sumé.
Usa Ollama com Phi-3 Mini para conversas offline e ilimitadas.
"""

import ollama

# Configuração
MODELO = "phi3:mini"
CONTEXTO_SISTEMA = """Você é o Sumé, um assistente virtual pessoal inspirado no Jarvis.
Características:
- Fala português brasileiro
- Respostas curtas e diretas (1-3 frases)
- Tom amigável mas profissional
- Chama o usuário pelo nome quando souber
- Usa emojis ocasionalmente
- Não inventa informações, admite quando não sabe algo"""

# Histórico de conversa (últimas mensagens para contexto)
historico = []


def conversar(mensagem, nome_usuario=None):
    """
    Envia mensagem para o Phi-3 Mini e retorna a resposta.
    
    Args:
        mensagem: texto da pergunta do usuário
        nome_usuario: nome do usuário (opcional, se conhecido)
    
    Returns:
        resposta: texto da resposta da IA
    """
    global historico
    
    # Prepara o prompt com contexto
    prompt_sistema = CONTEXTO_SISTEMA
    if nome_usuario:
        prompt_sistema += f"\nO usuário se chama {nome_usuario}."
    
    # Monta mensagens para o Ollama
    mensagens = [{"role": "system", "content": prompt_sistema}]
    
    # Adiciona histórico recente (últimas 6 mensagens)
    for msg in historico[-6:]:
        mensagens.append(msg)
    
    # Adiciona mensagem atual
    mensagens.append({"role": "user", "content": mensagem})
    
    try:
        resposta = ollama.chat(
            model=MODELO,
            messages=mensagens,
        )
        
        texto_resposta = resposta["message"]["content"].strip()
        
        # Salva no histórico
        historico.append({"role": "user", "content": mensagem})
        historico.append({"role": "assistant", "content": texto_resposta})
        
        # Mantém histórico limitado
        if len(historico) > 20:
            historico = historico[-20:]
        
        return texto_resposta
        
    except Exception as e:
        print(f"[IA] Erro no Ollama: {e}")
        return "Desculpe, não consegui processar isso agora. O Ollama está rodando?"


def limpar_historico():
    """Limpa o histórico de conversa."""
    global historico
    historico = []
    return "Histórico limpo!"


# Teste rápido
if __name__ == "__main__":
    resposta = conversar("Olá! Quem é você e o que pode fazer?")
    print(f"Sumé: {resposta}")