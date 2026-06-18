"""
Teste rápido do Sumé — verifica se tudo está funcionando.
Execute: python testes/teste_rapido.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modulos.memoria import guardar, lembrar, carregar
from modulos.automacoes import _abrir, _fechar, CATALOGO
from utils.voz import falar
import sqlite3

print("=" * 50)
print("TESTE RÁPIDO DO SUMÉ")
print("=" * 50)

erros = []

def testar(nome, func):
    try:
        func()
        print(f"✅ {nome}")
    except Exception as e:
        print(f"❌ {nome} -> {e}")
        erros.append((nome, str(e)))

# Memória
def t1():
    guardar("teste_tmp", "ok")
    assert lembrar("teste_tmp") == "ok", "Não lembrou"

def t2():
    dados = carregar()
    assert isinstance(dados, dict), "Carregar não retornou dict"

# Catálogo
def t3():
    assert len(CATALOGO) > 5, "Catálogo vazio ou pequeno"

def t4():
    assert "steam" in CATALOGO or "discord" in CATALOGO, "Programas comuns não encontrados"

# Banco de dados
def t5():
    assert os.path.exists("dados/memoria.db"), "memoria.db não encontrado"

# Logs
def t6():
    assert os.path.exists("dados/sume.log"), "sume.log não encontrado"

# Catálogo
def t7():
    assert os.path.exists("dados/catalogo_programas.json"), "catalogo_programas.json não encontrado"

# Execução
testar("Memória: guardar/lembrar", t1)
testar("Memória: carregar()", t2)
testar("Catálogo: tem programas", t3)
testar("Catálogo: Steam ou Discord", t4)
testar("Banco: memoria.db existe", t5)
testar("Logs: sume.log existe", t6)
testar("Catálogo: arquivo existe", t7)

print("=" * 50)
if erros:
    print(f"❌ {len(erros)} FALHA(S):")
    for nome, erro in erros:
        print(f"   - {nome}: {erro}")
else:
    print("✅ TODOS OS TESTES PASSARAM!")
print("=" * 50)