"""
Teste do sistema de confiança e ambiguidade (ETAPA 2).
Não depende de microfone nem de Ollama - só testa a lógica de decisão.
Execute: python testes/teste_confianca.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.nexus_core import _interpretar_comando, LIMIAR_CONFIANCA_MINIMA, LIMIAR_AMBIGUIDADE

erros = []


def testar(nome, comando, esperado_acao, checar_alvo=None):
    acao, alvo, confianca = _interpretar_comando(comando)
    if acao != esperado_acao:
        print(f"❌ {nome}")
        print(f"   comando: '{comando}'")
        print(f"   esperado ação={esperado_acao}, obtido ação={acao} (confiança={confianca})")
        erros.append(nome)
        return
    if checar_alvo is not None and alvo != checar_alvo:
        print(f"❌ {nome} (alvo errado: esperado '{checar_alvo}', obtido '{alvo}')")
        erros.append(nome)
        return
    print(f"✅ {nome}  -> {acao} (confiança={confianca})")


print("=" * 60)
print("TESTE: sistema de confiança e ambiguidade")
print(f"LIMIAR_CONFIANCA_MINIMA={LIMIAR_CONFIANCA_MINIMA}  LIMIAR_AMBIGUIDADE={LIMIAR_AMBIGUIDADE}")
print("=" * 60)

# --- Casos claros: uma intenção domina, sem ambiguidade ---
testar("Hora - sinal claro", "que horas são", "GET_TIME")
testar("Tchau - sinal forte", "tchau sumé", "EXIT")
testar("Abrir app - sem 'pasta' no alvo", "abrir discord", "OPEN_APP", checar_alvo="discord")
testar("Fechar app", "fechar navegador", "CLOSE_APP", checar_alvo="navegador")
testar("Memória - salvar nome (padrão forte)", "meu nome é bernardo", "MEMORY_SAVE", checar_alvo="bernardo")
testar("Memória - perguntar nome (padrão forte)", "quem sou eu", "MEMORY_READ")

# --- Caso de ambiguidade real: "abrir pasta X" bate em OPEN_APP e OPEN_FOLDER ---
# Antes desta etapa, quem decidia era a ordem da lista (folder_intent vinha
# primeiro), escondendo a ambiguidade. Agora isso precisa aparecer como tal.
testar("Ambiguidade real: abrir pasta X", "abrir pasta downloads", "AMBIGUOUS")

# --- Caso de confiança fraca: deve cair pro chat, não executar ação chutada ---
testar("Sinal fraco isolado ('sair', confiança 0.6 > limiar mas sem conflito) executa EXIT",
       "preciso sair mais cedo hoje", "EXIT")
testar("Nenhum padrão bate -> chat", "me conta uma curiosidade sobre o brasil", "CHAT")

# --- Comando vazio / irrelevante ---
testar("Comando sem nenhuma palavra-chave -> chat", "bom dia", "CHAT")

print("=" * 60)
if erros:
    print(f"❌ {len(erros)} FALHA(S): {erros}")
    sys.exit(1)
else:
    print("✅ TODOS OS TESTES PASSARAM!")
print("=" * 60)
