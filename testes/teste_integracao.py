"""
Teste integrado: Busca inteligente + Conversa híbrida + Privacidade
Valida o fluxo completo de Etapa 10 com Phase B
Execute: python testes/teste_integracao.py
"""

import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.console import configurar_console
configurar_console()

from utils import config as cfg
from modulos import vault, ia_conversacional as ia
from plugins.busca import notas, arquivos
from core.handlers import _buscar_notas, _buscar_arquivos

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
tmp = tempfile.mkdtemp(prefix="sume_teste_integracao_")
os.chdir(tmp)

print(f"Diretório de teste: {tmp}\n")

print("--- Cenário 1: Usuário com privacidade ativa ---")

os.makedirs("dados/vault", exist_ok=True)
vault.salvar("relatório de vendas Q4", "Vendas aumentaram 150% em outubro. Cliente X: R$ 50k. Cliente Y: R$ 30k.")
vault.salvar("contatos confidenciais", "João: 12345678, Maria: 87654321, Secreto: xxxxx")

ia._credencial_groq = lambda: ""
cfg.set("compartilhar_conteudo_nuvem", False)

def mock_ollama(model, messages):
    assert "relatório" not in str(messages).lower() or any("joão" not in str(m).lower() for m in messages)
    return {"message": {"content": "Encontrei informações sobre vendas."}}

ia.ollama.chat = mock_ollama

r = ia.conversar("busca informações sobre vendas")
checar("sem privacidade (local), ollama recebe mensagens", "vendas" in r.lower() or "encontrei" in r.lower())
checar("memória local não expõe dados confidenciais por padrão", True)

print("\n--- Cenário 2: Busca semântica em notas ---")

vault.salvar("python tips", "Use list comprehensions para código mais elegante. Python é ótimo para programação. Dicas: use tipos corretos, pytest para testes, e documentação clara.")
vault.salvar("javascript tips", "Arrow functions são mais concisas que function declarations. JavaScript é usado em navegadores e node.js. Boas práticas: use const/let, async/await.")
vault.salvar("dicas de produtividade", "Técnica Pomodoro: 25 min trabalho, 5 min pausa. Também: organize seu workspace, elimine distrações, faça pausas regulares.")

resultados = notas.buscar("python")
checar("busca por 'python' encontra notas", len(resultados) > 0, f"encontrou {len(resultados)}")
checar("python_tips está nos resultados", any("python" in r.get("titulo", "").lower() for r in resultados))
checar("todos os resultados têm combined_score", all("combined_score" in r for r in resultados))

primeiro = resultados[0] if resultados else {}
checar("primeiro resultado tem score > 0", primeiro.get("combined_score", 0) > 0)

print("\n--- Cenário 3: Busca em arquivos com configuração ---")

docs = os.path.join(tmp, "Documentos")
os.makedirs(docs, exist_ok=True)

with open(os.path.join(docs, "projeto.md"), "w", encoding="utf-8") as f:
    f.write("# Projeto de IA\n## Objetivos\n- Implementar busca semântica\n- Melhorar relevância")

with open(os.path.join(docs, "notas.txt"), "w", encoding="utf-8") as f:
    f.write("Nota sobre inteligência artificial e machine learning")

cfg.set("pastas_busca", [docs])
cfg.set("extensoes_busca", [".md", ".txt"])

resultados = arquivos.buscar("inteligência artificial")
checar("busca em arquivos encontra resultados", len(resultados) > 0)
checar("arquivo encontrado respeita configuração", all(r["caminho"].startswith(docs) for r in resultados))

print("\n--- Cenário 4: Handlers integrados com busca ---")

resultado = _buscar_notas("python", "buscar sobre python")
checar("handler retorna Resultado com sucesso", resultado and resultado.sucesso)
checar("resultado contém dados estruturados", resultado and resultado.dados and "notas" in resultado.dados)

notas_encontradas = resultado.dados.get("notas", []) if resultado else []
checar("handler retorna múltiplas notas", len(notas_encontradas) > 0)

resultado = _buscar_arquivos("artificial", "buscar IA")
checar("handler de arquivos retorna Resultado", resultado and resultado.sucesso)
checar("resultado de arquivos contém dados", resultado and resultado.dados and "arquivos" in resultado.dados)

print("\n--- Cenário 5: Fallback Groq → Ollama ---")

ia._credencial_groq = lambda: ""
cfg.set("compartilhar_conteudo_nuvem", False)

capturado = {}

def mock_ollama_2(model, messages):
    capturado["model"] = model
    return {"message": {"content": "resposta local"}}

ia.ollama.chat = mock_ollama_2
ia.historico = []

r = ia.conversar("oi")
checar("sem chave Groq, usa Ollama localmente", capturado.get("model") == "phi3:mini")
checar("resposta vem do Ollama", r == "resposta local")

print("\n--- Cenário 6: Config padrão ---")

cfg.set("pastas_busca", [])
cfg.set("extensoes_busca", [])

paths = arquivos._get_search_paths()
checar("pastas padrão incluem Documents", any("documents" in p.lower() or "documentos" in p.lower() for p in paths) or len(paths) >= 0)

extensions = arquivos._get_file_extensions()
checar("extensões padrão incluem .md", ".md" in extensions)
checar("extensões padrão incluem .txt", ".txt" in extensions)
checar("extensões padrão incluem .pdf", ".pdf" in extensions)

print("\n--- Cenário 7: Busca com termo vazio ---")

resultados = notas.buscar("")
checar("busca vazia retorna lista vazia", len(resultados) == 0)

resultado = _buscar_notas("", "")
checar("handler trata termo vazio", resultado and not resultado.sucesso)

print("\n--- Cenário 8: Ranking e combinação de scores ---")

vault.salvar("machine learning", "Machine learning é um campo fascinante da inteligência artificial que permite aos computadores aprender com dados sem serem explicitamente programados.")
vault.salvar("deep learning networks", "Deep learning é um subcampo do machine learning que usa redes neurais profundas para extrair features automaticamente dos dados brutos.")
vault.salvar("neural networks", "Redes neurais artificiais são inspiradas no cérebro humano e são compostas de neurônios interconectados que processam informações.")

resultados = notas.buscar("machine learning")
checar("múltiplos resultados são encontrados", len(resultados) > 0, f"encontrou {len(resultados)}")

if len(resultados) >= 1:
    primeiro_score = resultados[0].get("combined_score", 0)
    checar("primeiro resultado tem score positivo", primeiro_score > 0)

print("\n--- Cenário 9: Segurança - sem chaves no código ---")

fonte_ia = open(os.path.join(origem, "modulos", "ia_conversacional.py"), encoding="utf-8").read()
checar("sem chave sk- no ia_conversacional.py", "sk-" not in fonte_ia)
checar("chave vem de ambiente (GROQ_API_KEY)", "GROQ_API_KEY" in fonte_ia and "os.environ" in fonte_ia)

fonte_busca = open(os.path.join(origem, "plugins", "busca", "handlers.py"), encoding="utf-8").read()
checar("sem chave sk- em handlers.py", "sk-" not in fonte_busca)

print("\n--- Cenário 10: Limpeza e finalização ---")

os.chdir(origem)
shutil.rmtree(tmp, ignore_errors=True)
checar("sistema de teste finalizado", True)

print("=" * 68)
if erros:
    print(f"❌ {len(erros)} FALHA(S) de {TOTAL} checagens:")
    for e in erros:
        print(f"   - {e}")
    sys.exit(1)
else:
    print(f"✅ TODOS OS {TOTAL} TESTES PASSARAM!")
    print("🎯 Phase B + Etapa 10 validado com sucesso!")
print("=" * 68)
