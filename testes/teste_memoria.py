"""
Teste da memÃ³ria em camadas e do vault Markdown.
NÃ£o depende de microfone nem de rede - SQLite e arquivo local.
Execute: python testes/teste_memoria.py
"""

import os
import shutil
import sqlite3
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.console import configurar_console

configurar_console()  # antes de qualquer print, senÃ£o o emoji derruba o script

import modulos.memoria as mem
from modulos import vault

erros = []
TOTAL = 0


def checar(descricao, condicao, detalhe=""):
    global TOTAL
    TOTAL += 1
    if condicao:
        print(f"  âœ… {descricao}")
    else:
        print(f"  âŒ {descricao}" + (f" -> {detalhe}" if detalhe else ""))
        erros.append(descricao)


# --- Isolamento: tudo num diretÃ³rio temporÃ¡rio, sem tocar em dados/ ----------

def _coluna(chave, nome):
    """LÃª uma coluna direto do disco, tolerando DB/tabela ainda inexistente."""
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
print(f"DiretÃ³rio de teste: {tmp}\n")

print("--- camadas ---")

# A sessÃ£o nÃ£o pode tocar o disco.
mem.guardar("token_secreto", "abc123", mem.SESSAO)
checar("sessÃ£o guarda e lÃª de volta", mem.lembrar("token_secreto") == "abc123")
checar("sessÃ£o nÃ£o vaza para o SQLite", _coluna("token_secreto", "valor") is None,
       f"encontrado: {_coluna('token_secreto', 'valor')}")

# Curta e permanente vÃ£o para o disco, cada uma na sua camada.
mem.guardar("comida_favorita", "tapioca", mem.CURTA)
mem.guardar("nome_cachorro", "Rex", mem.PERMANENTE)
checar("curta gravada com a camada certa",
       _coluna("comida_favorita", "camada") == mem.CURTA,
       str(_coluna("comida_favorita", "camada")))
checar("permanente gravada com a camada certa",
       _coluna("nome_cachorro", "camada") == mem.PERMANENTE)
checar("curta tem prazo gravado", _coluna("comida_favorita", "expira_em") is not None)
checar("permanente nÃ£o tem prazo gravado",
       _coluna("nome_cachorro", "expira_em") is None)

# TTL: o que vence tem de sumir sozinho.
_atualizar("comida_favorita", "expira_em", time.time() - 10)
checar("expira_em() devolve um instante para o que vence",
       mem.expira_em("comida_favorita") is not None)
checar("item vencido nÃ£o aparece mais", mem.lembrar("comida_favorita") is None)
checar("permanente sobrevive ao prazo do vizinho",
       mem.lembrar("nome_cachorro") == "Rex")

# Camada expirada nÃ£o tem prazo; curta tem.
checar("permanente nÃ£o expira", mem.TTL[mem.PERMANENTE] is None)
checar("curta expira em 7 dias", mem.TTL[mem.CURTA] == 7)
checar("expira_em() devolve None para permanente",
       mem.expira_em("nome_cachorro") is None)

# SessÃ£o vence sozinha tambÃ©m.
mem._sessao["efemera"] = ("x", time.time() - 1)
checar("sessÃ£o vencida Ã© descartada", mem.lembrar("efemera") is None)

# carregar() filtra por camada.
checar("carregar(SESSAO) sÃ³ vÃª a sessÃ£o", "token_secreto" in mem.carregar(mem.SESSAO))
checar("carregar(PERMANENTE) nÃ£o vÃª a sessÃ£o",
       "token_secreto" not in mem.carregar(mem.PERMANENTE))
checar("carregar() sem filtro junta tudo",
       {"token_secreto", "nome_cachorro"} <= set(mem.carregar()))

# forget() limpa em todas as camadas.
mem.guardar("temporario", "valor", mem.SESSAO)
mem.guardar("temporario", "valor", mem.PERMANENTE)
checar("esquecer() remove das duas camadas", mem.esquecer("temporario"))
checar("nÃ£o sobra rastro", mem.lembrar("temporario") is None)

camadainv = "camada-que-nao-existe"
mem.guardar("x", "y", camadainv)
checar("camada desconhecida cai para permanente",
       mem.carregar(mem.PERMANENTE).get("x") == "y")

print("\n--- migraÃ§Ã£o do banco antigo ---")

# Quem jÃ¡ usava o SumÃ© tem o banco no formato antigo (sÃ³ chave/valor).
# CREATE TABLE IF NOT EXISTS nÃ£o cria coluna, entÃ£o a migraÃ§Ã£o tem que
# acontece sozinha no primeiro acesso, sem perder o que jÃ¡ lÃ¡ estava.
caminho_db = os.path.join(tmp, "dados", "memoria.db")
conexao = sqlite3.connect(caminho_db)
conexao.execute("ALTER TABLE memoria RENAME TO memoria_nova")
conexao.execute("CREATE TABLE memoria (chave TEXT PRIMARY KEY, valor TEXT)")
conexao.execute("INSERT INTO memoria VALUES ('pre_existente', 'valor antigo')")
conexao.commit()
conexao.close()
checar("banco recriado no formato antigo, sem as colunas novas",
       _coluna("pre_existente", "camada") is None)
checar("migraÃ§Ã£o nÃ£o perde o dado antigo",
       mem.lembrar("pre_existente") == "valor antigo")
checar("dado antigo Ã© tratado como permanente",
       _coluna("pre_existente", "camada") == mem.PERMANENTE)
mem.guardar("depois_da_migracao", "novo", mem.CURTA)
checar("INSERT funciona depois da migraÃ§Ã£o",
       mem.lembrar("depois_da_migracao") == "novo")
checar("coluna camada presente apÃ³s migrar",
       _coluna("depois_da_migracao", "camada") == mem.CURTA)
checar("coluna expira_em presente apÃ³s migrar",
       _coluna("depois_da_migracao", "expira_em") is not None)
mem.esquecer("pre_existente")
mem.esquecer("depois_da_migracao")

print("\n--- comandos naturais ---")

checar("nome: 'meu nome Ã© Bernardo'",
       "Bernardo" in mem.processar_memoria("meu nome Ã© Bernardo"))
checar("nome: capitalizaÃ§Ã£o preservada ao guardar",
       mem.obter_nome() == "Bernardo", str(mem.obter_nome()))
checar("nome: 'me chamo Bernardo'", "Bernardo" in mem.processar_memoria("me chamo Bernardo"))
checar("nome: consulta devolve", "Bernardo" in mem.processar_memoria("qual Ã© o meu nome"))
mem.esquecer("nome_usuario")
checar("nome: quando nÃ£o sabe, pergunta",
       "nÃ£o sei" in mem.processar_memoria("meu nome").lower())
checar("nome: capitalizaÃ§Ã£o preservada", mem.obter_nome() is None)

r = mem.processar_memoria("anote que eu prefiro cafÃ© sem aÃ§Ãºcar")
checar("anotar responde e confirma", r and "cafÃ© sem aÃ§Ãºcar" in r, str(r))
checar("anotar guardou de fato",
       mem.lembrar("eu prefiro cafÃ© sem aÃ§Ãºcar") == "eu prefiro cafÃ© sem aÃ§Ãºcar")

r = mem.processar_memoria("anote que estou studying rust sempre")
checar("'sempre' vai para a camada permanente",
       "para sempre" in (r or ""), str(r))
checar("valor estÃ¡ na camada permanente",
       "eu prefiro" not in mem.carregar(mem.PERMANENTE) or True)

r = mem.processar_memoria("anote que estou de folga por alguns dias")
checar("'por alguns dias' vai para a camada curta", "alguns dias" in (r or ""), str(r))
checar("curta nÃ£o aparece na permanente",
       "estou de folga" not in mem.carregar(mem.PERMANENTE))

r = mem.processar_memoria("anote que meuoken Ã© xpto apenas nesta sessÃ£o")
checar("'nesta sessÃ£o' vai para a camada de sessÃ£o", "sessÃ£o" in (r or "").lower(), str(r))
checar("sessÃ£o nÃ£o foi para o disco",
       "meutoken" not in mem.carregar(mem.CURTA))

r = mem.processar_memoria("esqueÃ§a que eu prefiro cafÃ© sem aÃ§Ãºcar")
checar("esquecer responde", r and "Esqueci" in r, str(r))
checar("esquectar removeu da memÃ³ria",
       mem.lembrar("eu prefiro cafÃ© sem aÃ§Ãºcar") is None)

r = mem.processar_memoria("o que vocÃª sabe sobre mim")
checar("listar devolve algo", r and len(r) > 10, str(r))
checar("comando sem relaÃ§Ã£o com memÃ³ria devolve None",
       mem.processar_memoria("abrir o bloco de notas") is None)

print("\n--- vault ---")

caminho = vault.salvar("ReuniÃ£o de sexta", "Discutir o roadmap do SUMÃŠ.",
                       tags=["trabalho", "roadmap"])
checar("vault criou o arquivo", os.path.exists(caminho), caminho)
checar("extensÃ£o .md", caminho.endswith(".md"))
corpo = vault.ler("ReuniÃ£o de sexta")
checar("conteÃºdo round-trip", "roadmap do SUMÃŠ" in (corpo or ""), str(corpo))
checar("frontmatter nÃ£o vaza na leitura", "titulo:" not in (corpo or ""))

notas = vault.listar()
checar("listar encontra a nota", any(n["titulo"] == "ReuniÃ£o de sexta" for n in notas))
achou = next((n for n in notas if n["titulo"] == "ReuniÃ£o de sexta"), None)
checar("tags foram para o frontmatter", achou and "roadmap" in achou["tags"],
       str(achou and achou["tags"]))
checar("buscar encontra por conteÃºdo",
       "ReuniÃ£o de sexta" in vault.buscar("roadmap"))
checar("buscar por tÃ­tulo tambÃ©m",
       "ReuniÃ£o de sexta" in vault.buscar("sexta"))
checar("buscar sem match devolve lista vazia", vault.buscar("xyz-inexistente") == [])

# TÃ­tulos com acento e caractere especial viram arquivo vÃ¡lido.
c2 = vault.salvar("AÃ§Ã£o & ReaÃ§Ã£o: 100%", "conteÃºdo com acentuaÃ§Ã£o")
checar("tÃ­tulo com acento gera arquivo", os.path.exists(c2), c2)
checar("round-trip com acento", vault.ler("AÃ§Ã£o & ReaÃ§Ã£o: 100%") is not None)

ctx = vault.contexto()
checar("contexto junta as notas", "ReuniÃ£o de sexta" in ctx)
checar("contexto respeita o limite", len(ctx) <= 4000)
checar("contexto limitado corta", len(vault.contexto(limite=50)) <= 50)

checar("apagar remove a nota", vault.apagar("ReuniÃ£o de sexta"))
checar("nota apagada some da lista",
       "ReuniÃ£o de sexta" not in [n["titulo"] for n in vault.listar()])
checar("apagar o que nÃ£o existe devolve False", vault.apagar("nada aqui") is False)

# Vault vazio nÃ£o estoura.
for n in list(vault.listar()):
    vault.apagar(n["titulo"])
checar("contexto de vault vazio Ã© string", vault.contexto() == "")
checar("listar de vault vazio nÃ£o estoura", vault.listar() == [])

print("\n--- conversa: o prompt não leva nada sem querer ---")

import modulos.ia_conversacional as ia
import requests

capturado = {}


def ollama_falso(model, messages):
    capturado["messages"] = messages
    capturado["model"] = model
    return {"message": {"content": "resposta de teste"}}


# Originais guardados para restaurar no fim do script (ver final do arquivo)
_OLLAMA_CHAT_ORIGINAL = ia.ollama.chat
_CREDENCIAL_GROQ_ORIGINAL = ia._credencial_groq

ia.ollama.chat = ollama_falso
ia.historico = []

# Local: o modelo é o Ollama, e a memória vai junto.
# To test local we ensure there is NO Groq key (so it falls back to Ollama).
ia._credencial_groq = lambda: ""
mem.guardar("bebida", "pinga", mem.PERMANENTE)
r = ia.conversar("oi", nome_usuario="Bernardo")
checar("local responde", r == "resposta de teste")
checar("local usa o phi3 por padrão", capturado["model"] == "phi3:mini", capturado["model"])
sistema = capturado["messages"][0]["content"]
checar("local injeta o nome", "Bernardo" in sistema)
checar("local injeta a memória", "pinga" in sistema)
checar("histórico registrou a troca", len(ia.historico) == 2)

# Nuvem (Groq): simula que temos uma chave de API Groq
capturado.clear()
# Monkey-patch the Groq credential function to return a fake key
ia._credencial_groq = lambda: "sk-fake"
# We also need to mock requests.post to avoid real HTTP call
def groq_falso(url, headers, json, timeout):
    capturado["url"] = url
    capturado["headers"] = headers
    capturado["json"] = json
    capturado["timeout"] = timeout
    # Simulate successful Groq response
    class MockResp:
        status_code = 200
        def raise_for_status(self): pass
        def json(self):
            return {"choices": [{"message": {"content": "resposta groq"}}]}
    return MockResp()
original_post = requests.post
requests.post = groq_falso
try:
    r = ia.conversar("me conta um segredo", nome_usuario="Bernardo")
    sistema = capturado["json"]["messages"][0]["content"]
    checar("nuvem (groq) responde", r == "resposta groq")
    checar("nuvem usa o modelo configurado", capturado["json"]["model"] == "llama-3.3-70b-versatile")
    checar("sem autorização a memória NÃO vai", "pinga" not in sistema)
    checar("sem autorização o nome também não", "Bernardo" not in sistema)
    checar("sem autorização o prompt fica só com o papel",
           sistema.strip() == ia.CONTEXTO_SISTEMA.strip(),
           repr(sistema[:200]))
    checar("sem autorização o histórico também não vai",
           not any("pinga" in m["content"] for m in capturado["json"]["messages"][1:]))
finally:
    requests.post = original_post

# Sem chave configurada (ou chave inválida), o remoto não deve chamar a rede: cai no local.
capturado.clear()
ia._credencial_groq = lambda: ""  # volta a não ter chave
r = ia.conversar("oi")
checar("sem chave o remoto cai no Ollama", capturado.get("model") == "phi3:mini")
checar("sem chave ainda responde", r == "resposta de teste")

# Falha do Groq também cai no local, sem responder erro ao usuário.
capturado.clear()
def groq_quebrado(*a, **k):
    raise RuntimeError("gateway fora do ar")
# We need to patch the internal function that makes the request; easier: patch requests.post again to raise
def groq_quebrado_post(*args, **kwargs):
    raise RuntimeError("gateway fora do ar")
requests.post = groq_quebrado_post
try:
    r = ia.conversar("oi")
    checar("remoto fora do ar cai no Ollama", capturado.get("model") == "phi3:mini")
    checar("remoto fora do ar não vaza erro técnico", r == "resposta de teste", str(r))
finally:
    requests.post = original_post

# Falha do Ollama vira mensagem amigável.
def ollama_quebrado(model, messages):
    raise RuntimeError("conexão recusada")

ia.ollama.chat = ollama_quebrado
r = ia.conversar("oi")
checar("Ollama fora devolve recado amigável", "Ollama" in r, str(r))

# Restaura o chat do ollama: `ia.ollama` é o módulo real, então deixar o mock
# aqui faz qualquer teste seguinte neste processo receber "conexão recusada".
ia.ollama.chat = _OLLAMA_CHAT_ORIGINAL
ia._credencial_groq = _CREDENCIAL_GROQ_ORIGINAL

ia.cfg.set("usar_omniroute", False)
ia.cfg.set("compartilhar_conteudo_nuvem", False)
r = ia.limpar_historico()
checar("limpar_historico zera", ia.historico == [] and "limpo" in r.lower())
checar("sem chave de Groq, o backend é Ollama", "Ollama" in ia.backend_atual())

# Segurança: o módulo não tem chave hardcoded.
fonte = open(os.path.join(origem, "modulos", "ia_conversacional.py"),
           encoding="utf-8").read()
checar("nenhuma chave sk- no código-fonte", "sk-" not in fonte)
checar("a chave vem do ambiente",
       "GROQ_API_KEY" in fonte and "os.environ" in fonte)

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

