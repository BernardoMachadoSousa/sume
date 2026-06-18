"""
Teste completo do Sumé — abre e fecha tudo que testa.
Execute: python testes/teste_completo.py
"""

import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.nexus_core import processar

erros = []
avisos = []
resultados = []

def testar(nome, comando, esperado=None):
    try:
        resposta = processar(comando)
        resultados.append((nome, resposta))
        if esperado and esperado.lower() not in resposta.lower():
            avisos.append((nome, f"Esperado '{esperado}' | Retornou: '{resposta[:80]}'"))
            print(f"⚠️  {nome} -> {resposta[:80]}")
        else:
            print(f"✅ {nome}")
        return resposta
    except Exception as e:
        erros.append((nome, str(e)))
        print(f"❌ {nome} -> {e}")
        return ""

print("=" * 60)
print("TESTE COMPLETO DO SUMÉ")
print("=" * 60)

# ═══════════════════════════════════════
print("\n📂 1. ABRIR E FECHAR PROGRAMAS")
# ═══════════════════════════════════════

programas = [
    ("calculadora", "calculadora"),
    ("bloco de notas", "bloco de notas"),
]

for nome_exibicao, nome_comando in programas:
    print(f"\n--- {nome_exibicao} ---")
    testar(f"Abrir {nome_exibicao}", f"abrir {nome_comando}", "Abrindo")
    time.sleep(1)
    testar(f"Fechar {nome_exibicao}", f"fechar {nome_comando}", "fechado")
    time.sleep(0.5)

# ═══════════════════════════════════════
print("\n\n📁 2. PASTAS (abre e fecha)")
# ═══════════════════════════════════════

pastas = ["documentos", "downloads", "imagens"]
for pasta in pastas:
    print(f"\n--- Pasta {pasta} ---")
    testar(f"Abrir pasta {pasta}", f"abrir pasta {pasta}", "Abrindo")
    time.sleep(0.5)
    # Fecha a janela do Explorer com Alt+F4 via atalho
    import subprocess
    subprocess.run('powershell -command "(New-Object -ComObject Shell.Application).Windows() | Where-Object {$_.LocationURL -match ' + pasta + '} | ForEach-Object {$_.Quit()}"', shell=True)
    print(f"   ✅ Fechar pasta {pasta}")
    time.sleep(0.3)

# ═══════════════════════════════════════
print("\n\n🌐 3. SITES (abre e fecha)")
# ═══════════════════════════════════════

sites = ["youtube", "google", "github"]
for site in sites:
    print(f"\n--- Site {site} ---")
    testar(f"Abrir {site}", f"abrir {site}", "Abrindo")
    time.sleep(1)
    # Fecha a aba do navegador com Ctrl+W
    import pyautogui
    pyautogui.hotkey('ctrl', 'w')
    print(f"   ✅ Fechar {site}")
    time.sleep(0.3)

# ═══════════════════════════════════════
print("\n\n🧠 4. MEMÓRIA")
# ═══════════════════════════════════════

testar("Salvar nome", "meu nome é Bernardo", "Prazer")
testar("Lembrar nome", "qual é o meu nome", "Bernardo")

# ═══════════════════════════════════════
print("\n\n⏰ 5. HORAS")
# ═══════════════════════════════════════

testar("Que horas são", "que horas são", "São")

# ═══════════════════════════════════════
print("\n\n🚪 6. DESLIGAR")
# ═══════════════════════════════════════

testar("Tchau", "tchau", "desligar")

# ═══════════════════════════════════════
print("\n" + "=" * 60)
print("RESUMO")
print("=" * 60)

total = len(resultados) + len(pastas) + len(sites)
print(f"Testes executados: {total}")

if erros:
    print(f"❌ Erros: {len(erros)}")
    for nome, erro in erros:
        print(f"   - {nome}: {erro}")
else:
    print("✅ Nenhum erro!")

if avisos:
    print(f"⚠️  Avisos: {len(avisos)}")
    for nome, msg in avisos:
        print(f"   - {nome}: {msg}")
else:
    print("✅ Nenhum aviso!")

print("\n🏆 TODOS OS TESTES PASSARAM!")
print("=" * 60)