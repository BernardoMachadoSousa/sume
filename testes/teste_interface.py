"""
Teste da interface Desktop (Etapa 4).

Sem microfone e sem rede: importa o main.py e confere o contrato da API
pywebview (métodos que a interface chama), a marcação da última intenção
e os hooks de histórico/memória/confiança nos arquivos da interface.

Execute: python testes/teste_interface.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.console import configurar_console

configurar_console()  # antes de qualquer print, senão o emoji derruba o script

ORIGEM = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

erros = []
TOTAL = 0


def checar(descricao, condicao, detalhe=""):
    global TOTAL
    TOTAL += 1
    if condicao:
        print(f"  \u2713 {descricao}")
    else:
        erros.append(descricao)
        print(f"  \u2717 {descricao}  {detalhe}")


# tem que rodar da raiz do projeto, senão 'dados/memoria.db' não resolve
os.chdir(ORIGEM)

import main
import core.nexus_core as nexus_core
import modulos.memoria as memoria

api = main.NexusAPI()

# ── 1. A API expõe os métodos que a interface chama ──
for nome in ("processar_comando", "processar_comando_info", "ouvir_comando",
             "ver_memorias", "ultima_intencao", "minimizar", "fechar"):
    checar(f"NexusAPI.{nome} existe e é chamável",
           callable(getattr(api, nome, None)))

# ── 2. ver_memorias devolve o formato que o JS espera ──
memorias = api.ver_memorias()
checar("ver_memorias devolve lista", isinstance(memorias, list))
checar("itens têm camada/chave/valor",
       all(set(item) >= {"camada", "chave", "valor"} for item in memorias))
checar("camadas são válidas",
       all(item["camada"] in memoria.CAMADAS for item in memorias))

# ── 3. ultima_intencao devolve o dicionário esperado ──
info = api.ultima_intencao()
checar("ultima_intencao tem intent e confianca",
       isinstance(info, dict) and "intent" in info and "confianca" in info)

nexus_core._marcar_intencao("GET_TIME", "", 0.92)
ui = nexus_core.ultima_intencao()
checar("marcar_intencao registra intent/alvo/confianca",
       ui["intent"] == "GET_TIME" and ui["confianca"] == 0.92)
checar("ultima_intencao devolve cópia (isolado)",
       nexus_core.ultima_intencao() is not ui)

# ── 4. processar() registra a intenção de verdade, sem rede nem disco ──
resposta = nexus_core.processar("que horas são?")
ui = nexus_core.ultima_intencao()
checar("'que horas são?' vira GET_TIME", ui["intent"] == "GET_TIME",
       f"obteve {ui.get('intent')}")
checar("confiança do GET_TIME é número >= 0.5",
       isinstance(ui["confianca"], (int, float)) and ui["confianca"] >= 0.5,
       str(ui))

# ── 5. Classificação de erro (para o estado de erro com contexto) ──
from modulos.ia_conversacional import FALHA_OLLAMA

checar("FALHA_OLLAMA é marcada como erro",
       main.NexusAPI._mensagem_de_erro(FALHA_OLLAMA))
checar("'ocorreu um erro ao processar' é erro",
       main.NexusAPI._mensagem_de_erro(
           "Desculpe, ocorreu um erro ao processar seu comando."))
checar("resposta normal não é erro",
       not main.NexusAPI._mensagem_de_erro("São 14h32."))
checar("resposta vazia não é erro",
       not main.NexusAPI._mensagem_de_erro(""))

# ── 6. Os arquivos da interface têm os hooks esperados ──
html = open(os.path.join(ORIGEM, "interface", "index.html"),
            encoding="utf-8").read()
js = open(os.path.join(ORIGEM, "interface", "assets", "script.js"),
          encoding="utf-8").read()
css = open(os.path.join(ORIGEM, "interface", "assets", "style.css"),
           encoding="utf-8").read()

for id_ in ("history", "memory-panel", "memory-list", "confidence"):
    checar(f"index.html tem id='{id_}'", f'id="{id_}"' in html)

for fn in ("renderizarHistorico", "atualizarPainelMemoria",
           "atualizarConfianca", "processar_comando_info"):
    checar(f"script.js usa {fn}", fn in js)

checar("widget mostra só as últimas 3 mensagens",
       "historico.slice(-3)" in js)
checar("showResposta foi removido (responsa some dali)",
       "showResposta" not in js)

for cls in ("memory-panel", "main-col", "history", "msg.sume.erro"):
    checar(f"style.css tem regra para '{cls}'", cls in css)

print("=" * 68)
if erros:
    print(f"\u2717 {len(erros)} FALHA(S) de {TOTAL} checagens:")
    for e in erros:
        print(f"   - {e}")
    sys.exit(1)
else:
    print(f"\u2713 TODOS OS {TOTAL} TESTES PASSARAM!")
print("=" * 68)