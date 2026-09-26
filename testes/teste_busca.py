"""
Teste do plugin de busca (notas e arquivos).
Não depende de rede - usa arquivos locais e mocks onde necessário.
Execute: python testes/teste_busca.py
"""

import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.console import configurar_console
configurar_console()

from utils import config as cfg
from modulos import vault
from plugins.busca import notas, arquivos

erros = []
TOTAL = 0


def checar(descricao, condicao, detalhe=""):
    global TOTAL
    TOTAL += 1
    if condicao:
        print(f"  ✓ {descricao}")
    else:
        print(f"  ✗ {descricao}" + (f" -> {detalhe}" if detalhe else ""))
        erros.append(descricao)


origem = os.getcwd()
tmp = tempfile.mkdtemp(prefix="sume_teste_busca_")
os.chdir(tmp)

print(f"Diretório de teste: {tmp}\n")

print("--- busca em notas ---")

os.makedirs("dados/vault", exist_ok=True)
os.makedirs("dados", exist_ok=True)

vault.salvar("nota de python", "def hello():\n    print('olá mundo')\n\nesta é uma nota sobre python")
vault.salvar("receita de café", "ingredientes:\n- café\n- água quente\n\nprepare o café com cuidado")
vault.salvar("lista de compras", "leite\npão\ncafé\novos\nbatata")

resultados = notas.buscar("café")
checar("busca por 'café' encontra notas", len(resultados) > 0, f"encontrou {len(resultados)}")
checar("resultados têm campo 'titulo'", all("titulo" in r for r in resultados))
checar("resultados têm campo 'trecho'", all("trecho" in r for r in resultados))
checar("resultados têm campo 'caminho'", all("caminho" in r for r in resultados))
checar("busca encontrou 'receita de café'", any("café" in r.get("titulo", "").lower() for r in resultados))

resultados = notas.buscar("python")
checar("busca por 'python' encontra a nota", len(resultados) > 0)
checar("nota de python está nos resultados", any("python" in r.get("titulo", "").lower() for r in resultados))

resultados = notas.buscar("xyz_nao_existe")
checar("busca sem match retorna lista vazia", len(resultados) == 0)

resultados = notas.buscar("")
checar("busca vazia retorna lista vazia", len(resultados) == 0)

print("\n--- busca em arquivos ---")

docs_path = os.path.join(tmp, "Documentos")
downloads_path = os.path.join(tmp, "Downloads")

os.makedirs(docs_path, exist_ok=True)
os.makedirs(downloads_path, exist_ok=True)

with open(os.path.join(docs_path, "relatorio.txt"), "w", encoding="utf-8") as f:
    f.write("Relatório de vendas 2026\nTotal: 50000\nDespesas: 10000")

with open(os.path.join(downloads_path, "lista.md"), "w", encoding="utf-8") as f:
    f.write("# Minha lista\n\n- item 1\n- item 2\n- café na segunda")

with open(os.path.join(docs_path, "dados.json"), "w", encoding="utf-8") as f:
    f.write('{"nome": "João", "café": "sim"}')

cfg.set("pastas_busca", [docs_path, downloads_path])
cfg.set("extensoes_busca", [".txt", ".md", ".json"])

resultados = arquivos.buscar("café")
checar("busca por 'café' em arquivos encontra resultados", len(resultados) > 0, f"encontrou {len(resultados)}")
checar("resultados têm campo 'nome'", all("nome" in r for r in resultados))
checar("resultados têm campo 'caminho'", all("caminho" in r for r in resultados))
checar("resultados têm campo 'trecho'", all("trecho" in r for r in resultados))

resultados = arquivos.buscar("vendas")
checar("busca por 'vendas' encontra relatorio.txt", any("relatorio" in r.get("nome", "").lower() for r in resultados))

resultados = arquivos.buscar("xyz_arquivo_inexistente")
checar("busca sem match em arquivos retorna lista vazia", len(resultados) == 0)

resultados = arquivos.buscar("")
checar("busca vazia em arquivos retorna lista vazia", len(resultados) == 0)

print("\n--- ranker e relevância ---")

vault.salvar("computador novo", "comprei um computador novo de 15 polegadas")
vault.salvar("mouse de computador", "o mouse do computador quebrou")

resultados = notas.buscar("computador")
checar("ranker classifica múltiplos resultados", len(resultados) > 1)
checar("resultados têm campo 'score'", all("score" in r for r in resultados))
checar("primeiro resultado tem maior score", resultados[0].get("score", 0) >= resultados[-1].get("score", 0))

print("\n--- integração com handlers ---")

from core.handlers import _buscar_notas, _buscar_arquivos

resultado = _buscar_notas("café", "buscar café")
checar("handler buscar_notas retorna Resultado", resultado is not None)
checar("handler retorna sucesso", resultado.sucesso if resultado else False)

resultado = _buscar_arquivos("vendas", "buscar vendas")
checar("handler buscar_arquivos retorna Resultado", resultado is not None)
checar("handler retorna sucesso", resultado.sucesso if resultado else False)

resultado = _buscar_notas("", "")
checar("handler trata busca vazia", resultado is not None)
checar("handler retorna erro para busca vazia", not resultado.sucesso if resultado else False)

os.chdir(origem)
shutil.rmtree(tmp, ignore_errors=True)

print("=" * 68)
if erros:
    print(f"❌ {len(erros)} FALHA(S) de {TOTAL} checagens:")
    for e in erros:
        print(f"   - {e}")
    sys.exit(1)
else:
    print(f"✅ TODOS OS {TOTAL} TESTES PASSARAM!")
print("=" * 68)
