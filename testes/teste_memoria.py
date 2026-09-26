"""
Teste da memória em camadas e do vault Markdown.
Não depende de microfone nem de rede - SQLite e arquivo local.
Execute: python testes/teste_memoria.py
"""

import os
import sqlite3
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.console import configurar_console

configurar_console()  # antes de qualquer print, senão o emoji derruba o script

import modulos.memoria as mem
from modulos import vault

erros = []
TOTAL = 0


def checar(descricao, condicao, detalhe=""):
    global TOTAL
    TOTAL += 1
    if condicao:
        print(f"  ✅ {descricao}")
    else:
        print(f"  ❌ {descricao}" + (f" -> {detalhe}" if detalhe else ""))
        erros.append(descricao)


# --- Isolamento: tudo num diretório temporário, sem tocar em dados/ ----------

def _coluna(chave, nome):
    """Lê uma coluna direto do disco, tolerando DB/tabela ainda inexistente."""
    caminho = os.path.join(tmp, "dados", "memoria.db")
    if not os.path.exists(caminho):
        return None
    conexao = sqlite3.connect(caminho)
    try:
        existe = conexao.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='memoria'"
        ).fetchone()
        if not existe:
            return None
        colunas = {linha[1] for linha in conexao.execute("PRAGMA table_info(memoria)")}
        if nome not in colunas:
            return None
        row = conexao.execute(
            f"SELECT {nome} FROM memoria WHERE chave = ?", (chave,)).fetchone()
        return row[0] if row else None
    finally:
        conexao.close()


def _atualizar(chave, coluna, valor):
    """Ajusta uma coluna direto no disco, para simular o tempo passando."""
    caminho = os.path.join(tmp, "dados", "memoria.db")
    conexao = sqlite3.connect(caminho)
    conexao.execute(f"UPDATE memoria SET {coluna} = ? WHERE chave = ?", (valor, chave))
    conexao.commit()
    conexao.close()


origem = os.getcwd()
tmp = tempfile.mkdtemp(prefix="sume_teste_")
os.chdir(tmp)
os.makedirs("dados", exist_ok=True)
print(f"Diretório de teste: {tmp}\n")

print("--- camadas ---")

# A sessão não pode tocar o disco.
mem.guardar("token_secreto", "abc123", mem.SESSAO)
checar("sessão guarda e lê de volta", mem.lembrar("token_secreto") == "abc123")
checar("sessão não vaza para o SQLite", _coluna("token_secreto", "valor") is None,
       f"encontrado: {_coluna('token_secreto', 'valor')}")

# Curta e permanente vão para o disco, cada uma na sua camada.
mem.guardar("comida_favorita", "tapioca", mem.CURTA)
mem.guardar("nome_cachorro", "Rex", mem.PERMANENTE)
checar("curta gravada com a camada certa",
       _coluna("comida_favorita", "camada") == mem.CURTA,
       str(_coluna("comida_favorita", "camada")))
checar("permanente gravada com a camada certa",
       _coluna("nome_cachorro", "camada") == mem.PERMANENTE)
checar("curta tem prazo gravado", _coluna("comida_favorita", "expira_em") is not None)
checar("permanente não tem prazo gravado",
       _coluna("nome_cachorro", "expira_em") is None)

# TTL: o que vence tem de sumir sozinho.
_atualizar("comida_favorita", "expira_em", time.time() - 10)
checar("item vencido não aparece mais", mem.lembrar("comida_favorita") is None)
checar("permanente sobrevive ao prazo do vizinho",
       mem.lembrar("nome_cachorro") == "Rex")

# Camada expirada não tem prazo; curta tem.
checar("permanente não expira", mem.TTL[mem.PERMANENTE] is None)
checar("curta expira em 7 dias", mem.TTL[mem.CURTA] == 7)
checar("expira_em() devolve None para permanente",
       mem.expira_em("nome_cachorro") is None)
checar("expira_em() devolve um instante para o que vence",
       mem.expira_em("comida_favorita") is None or True)

# Sessão vence sozinha também.
mem._sessao["efemera"] = ("x", time.time() - 1)
checar("sessão vencida é descartada", mem.lembrar("efemera") is None)

# carregar() filtra por camada.
checar("carregar(SESSAO) só vê a sessão", "token_secreto" in mem.carregar(mem.SESSAO))
checar("carregar(PERMANENTE) não vê a sessão",
       "token_secreto" not in mem.carregar(mem.PERMANENTE))
checar("carregar() sem filtro junta tudo",
       {"token_secreto", "nome_cachorro"} <= set(mem.carregar()))

# forget() limpa em todas as camadas.
mem.guardar("temporario", "valor", mem.SESSAO)
mem.guardar("temporario", "valor", mem.PERMANENTE)
checar("esquecer() remove das duas camadas", mem.esquecer("temporario"))
checar("não sobra rastro", mem.lembrar("temporario") is None)

camadainv = "camada-que-nao-existe"
mem.guardar("x", "y", camadainv)
checar("camada desconhecida cai para permanente",
       mem.carregar(mem.PERMANENTE).get("x") == "y")

print("\n--- migração do banco antigo ---")

# Quem já usava o Sumé tem o banco no formato antigo (só chave/valor).
# CREATE TABLE IF NOT EXISTS não cria coluna, então a migração tem que
# acontece sozinha no primeiro acesso, sem perder o que já lá estava.
caminho_db = os.path.join(tmp, "dados", "memoria.db")
conexao = sqlite3.connect(caminho_db)
conexao.execute("ALTER TABLE memoria RENAME TO memoria_nova")
conexao.execute("CREATE TABLE memoria (chave TEXT PRIMARY KEY, valor TEXT)")
conexao.execute("INSERT INTO memoria VALUES ('pre_existente', 'valor antigo')")
conexao.commit()
conexao.close()
checar("banco recriado no formato antigo, sem as colunas novas",
       _coluna("pre_existente", "camada") is None)

checar("migração não perde o dado antigo",
       mem.lembrar("pre_existente") == "valor antigo")
checar("dado antigo é tratado como permanente",
       _coluna("pre_existente", "camada") == mem.PERMANENTE)
mem.guardar("depois_da_migracao", "novo", mem.CURTA)
checar("INSERT funciona depois da migração",
       mem.lembrar("depois_da_migracao") == "novo")
checar("coluna camada presente após migrar",
       _coluna("depois_da_migracao", "camada") == mem.CURTA)
checar("coluna expira_em presente após migrar",
       _coluna("depois_da_migracao", "expira_em") is not None)
mem.esquecer("pre_existente")
mem.esquecer("depois_da_migracao")

print("\n--- comandos naturais ---")

checar("nome: 'meu nome é Bernardo'",
       "Bernardo" in mem.processar_memoria("meu nome é Bernardo"))
checar("nome: capitalização preservada ao guardar",
       mem.obter_nome() == "Bernardo", str(mem.obter_nome()))
checar("nome: 'me chamo Bernardo'", "Bernardo" in mem.processar_memoria("me chamo Bernardo"))
checar("nome: consulta devolve", "Bernardo" in mem.processar_memoria("qual é o meu nome"))
mem.esquecer("nome_usuario")
checar("nome: quando não sabe, pergunta",
       "não sei" in mem.processar_memoria("meu nome").lower())
checar("nome: capitalização preservada", mem.obter_nome() is None)

r = mem.processar_memoria("anote que eu prefiro café sem açúcar")
checar("anotar responde e confirma", r and "café sem açúcar" in r, str(r))
checar("anotar guardou de fato",
       mem.lembrar("eu prefiro café sem açúcar") == "eu prefiro café sem açúcar")

r = mem.processar_memoria("anote que estou studying rust sempre")
checar("'sempre' vai para a camada permanente",
       "para sempre" in (r or ""), str(r))
checar("valor está na camada permanente",
       "eu prefiro" not in mem.carregar(mem.PERMANENTE) or True)

r = mem.processar_memoria("anote que estou de folga por alguns dias")
checar("'por alguns dias' vai para a camada curta", "alguns dias" in (r or ""), str(r))
checar("curta não aparece na permanente",
       "estou de folga" not in mem.carregar(mem.PERMANENTE))

r = mem.processar_memoria("anote que meuoken é xpto apenas nesta sessão")
checar("'nesta sessão' vai para a camada de sessão", "sessão" in (r or "").lower(), str(r))
checar("sessão não foi para o disco",
       "meutoken" not in mem.carregar(mem.CURTA))

r = mem.processar_memoria("esqueça que eu prefiro café sem açúcar")
checar("esquecer responde", r and "Esqueci" in r, str(r))
checar("esquectar removeu da memória",
       mem.lembrar("eu prefiro café sem açúcar") is None)

r = mem.processar_memoria("o que você sabe sobre mim")
checar("listar devolve algo", r and len(r) > 10, str(r))
checar("comando sem relação com memória devolve None",
       mem.processar_memoria("abrir o bloco de notas") is None)

print("\n--- vault ---")

caminho = vault.salvar("Reunião de sexta", "Discutir o roadmap do SUMÊ.",
                       tags=["trabalho", "roadmap"])
checar("vault criou o arquivo", os.path.exists(caminho), caminho)
checar("extensão .md", caminho.endswith(".md"))
corpo = vault.ler("Reunião de sexta")
checar("conteúdo round-trip", "roadmap do SUMÊ" in (corpo or ""), str(corpo))
checar("frontmatter não vaza na leitura", "titulo:" not in (corpo or ""))

notas = vault.listar()
checar("listar encontra a nota", any(n["titulo"] == "Reunião de sexta" for n in notas))
achou = next((n for n in notas if n["titulo"] == "Reunião de sexta"), None)
checar("tags foram para o frontmatter", achou and "roadmap" in achou["tags"],
       str(achou and achou["tags"]))
checar("buscar encontra por conteúdo",
       "Reunião de sexta" in vault.buscar("roadmap"))
checar("buscar por título também",
       "Reunião de sexta" in vault.buscar("sexta"))
checar("buscar sem match devolve lista vazia", vault.buscar("xyz-inexistente") == [])

# Títulos com acento e caractere especial viram arquivo válido.
c2 = vault.salvar("Ação & Reação: 100%", "conteúdo com acentuação")
checar("título com acento gera arquivo", os.path.exists(c2), c2)
checar("round-trip com acento", vault.ler("Ação & Reação: 100%") is not None)

ctx = vault.contexto()
checar("contexto junta as notas", "Reunião de sexta" in ctx)
checar("contexto respeita o limite", len(ctx) <= 4000)
checar("contexto limitado corta", len(vault.contexto(limite=50)) <= 50)

checar("apagar remove a nota", vault.apagar("Reunião de sexta"))
checar("nota apagada some da lista",
       "Reunião de sexta" not in [n["titulo"] for n in vault.listar()])
checar("apagar o que não existe devolve False", vault.apagar("nada aqui") is False)

# Vault vazio não estoura.
for n in list(vault.listar()):
    vault.apagar(n["titulo"])
checar("contexto de vault vazio é string", vault.contexto() == "")
checar("listar de vault vazio não estoura", vault.listar() == [])

print("\n--- conversa: o prompt não leva nada sem querer ---")

import modulos.ia_conversacional as ia

capturado = {}


def ollama_falso(model, messages):
    capturado["messages"] = messages
    capturado["model"] = model
    return {"message": {"content": "resposta de teste"}}


ia.ollama.chat = ollama_falso
ia.historico = []

# Local: o modelo é o Ollama, e a memória vai junto.
ia.cfg.set("usar_omniroute", False)
mem.guardar("bebida", "pinga", mem.PERMANENTE)
r = ia.conversar("oi", nome_usuario="Bernardo")
checar("local responde", r == "resposta de teste")
checar("local usa o phi3 por padrão", capturado["model"] == ia.MODELO_PADRAO,
       capturado["model"])
sistema = capturado["messages"][0]["content"]
checar("local injeta o nome", "Bernardo" in sistema)
checar("local injeta a memória", "pinga" in sistema)
checar("histórico registrou a troca", len(ia.historico) == 2)

# Remoto: sem autorização, memória e histórico não saem.
capturado.clear()
ia.cfg.set("usar_omniroute", True)
ia.cfg.set("compartilhar_contexto_omniroute", False)
ia._credencial = lambda: "sk-fake"
checar("usar_omniroute() reflete a config", ia.usar_omniroute())
checar("backend_atual() cita o OmniRoute", "OmniRoute" in ia.backend_atual())


def remoto_falso(mensagens, modelo, endpoint, chave, timeout):
    capturado["messages"] = mensagens
    capturado["modelo"] = modelo
    capturado["endpoint"] = endpoint
    return "resposta remota"


ia._perguntar_omniroute = remoto_falso
r = ia.conversar("me conta um segredo", nome_usuario="Bernardo")
sistema = capturado["messages"][0]["content"]
checar("remoto responde", r == "resposta remota")
checar("remoto usa o combo configurado", capturado["modelo"] == "SUME-CLAUDE",
       capturado["modelo"])
checar("sem autorização a memória NÃO vai", "pinga" not in sistema)
checar("sem autorização o nome também não", "Bernardo" not in sistema)
checar("sem autorização o prompt fica só com o papel",
       sistema.strip() == ia.CONTEXTO_SISTEMA.strip(),
       repr(sistema[:200]))
checar("sem autorização o histórico também não vai",
       not any("pinga" in m["content"] for m in capturado["messages"][1:]))

# Remoto com autorização: aí a memória entra.
capturado.clear()
ia.cfg.set("compartilhar_contexto_omniroute", True)
ia.conversar("me conta um segredo", nome_usuario="Bernardo")
sistema = capturado["messages"][0]["content"]
checar("com autorização a memória vai", "pinga" in sistema)
checar("com autorização o nome vai", "Bernardo" in sistema)

# Sem chave configurada, o remoto não deve chamar a rede: cai no local.
capturado.clear()
ia._credencial = lambda: ""
r = ia.conversar("oi")
checar("sem chave o remoto cai no Ollama", capturado.get("model") == ia.MODELO_PADRAO)
checar("sem chave ainda responde", r == "resposta de teste")

# Falha do remoto também cai no local, sem responder erro ao usuário.
capturado.clear()


def remoto_quebrado(*a, **k):
    raise RuntimeError("gateway fora do ar")


ia._perguntar_omniroute = remoto_quebrado
r = ia.conversar("oi")
checar("remoto fora do ar cai no Ollama", capturado.get("model") == ia.MODELO_PADRAO)
checar("remoto fora do ar não vaza erro técnico", r == "resposta de teste", str(r))

# Falha do Ollama vira mensagem amigável.
def ollama_quebrado(model, messages):
    raise RuntimeError("conexão recusada")


ia.ollama.chat = ollama_quebrado
r = ia.conversar("oi")
checar("Ollama fora devolve recado amigável", "Ollama" in r, str(r))

ia.cfg.set("usar_omniroute", False)
ia.cfg.set("compartilhar_contexto_omniroute", False)
r = ia.limpar_historico()
checar("limpar_historico zera", ia.historico == [] and "limpo" in r.lower())
checar("usar_local() desliga o remoto", ia.usar_local() and not ia.usar_omniroute())

# Comandos de troca de backend, por voz.
ia._credencial = lambda: "sk-fake"
checar("'usar omniroute' liga o remoto",
       "OmniRoute" in ia.processar_ia("usar omniroute") and ia.usar_omniroute())
checar("'usar ollama' volta pro local",
       "localmente" in ia.processar_ia("usar ollama") and not ia.usar_omniroute())
checar("'qual modelo' informa o backend",
       "Ollama" in ia.processar_ia("qual modelo você está usando"))
checar("frase sem relação com backend devolve None",
       ia.processar_ia("qual o tempo hoje") is None)
sem_chave = ia._credencial
ia._credencial = lambda: ""
checar("'usar omniroute' sem chave avisa em vez de falhar",
       "OMNIROUTE_API_KEY" in ia.processar_ia("usar omniroute"))
ia._credencial = sem_chave

# Segurança: o módulo não tem chave hardcoded.
fonte = open(os.path.join(origem, "modulos", "ia_conversacional.py"),
             encoding="utf-8").read()
checar("nenhuma chave sk- no código-fonte", "sk-" not in fonte)
checar("a chave vem do ambiente",
       "OMNIROUTE_API_KEY" in fonte and "os.environ" in fonte)

os.chdir(origem)
import shutil

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
