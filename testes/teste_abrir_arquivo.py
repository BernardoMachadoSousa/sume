#!/usr/bin/env python3
"""
Teste da funcionalidade de abrir arquivo por voz (Etapa 6, parte 1).
Não depende de rede - usa arquivos locais e mocks onde necessário.
Execute: python testes/teste_abrir_arquivo.py
"""

import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.console import configurar_console
configurar_console()

from utils import config as cfg
from core.intents.file_intent import detectar as detectar_file_intent
from modulos.arquivos import abrir, caminho_seguro
from plugins.busca.arquivos import buscar_por_nome
from utils.resultado import Resultado

erros = []
TOTAL = 0

def checar(descricao, condicao, detalhe=""):
    global TOTAL
    TOTAL += 1
    if condicao:
        print(f"  ✓ {descricao}")
    else:
        print(f"  ❌ {descricao}")
        if detalhe:
            print(f"      {detalhe}")
        erros.append(f"{descricao}: {detalhe}")

def limpar_diretorio(diretorio):
    if os.path.exists(diretorio):
        shutil.rmtree(diretorio)
    os.makedirs(diretorio)

def setup_pastas_teste():
    tmp = tempfile.mkdtemp(prefix="sume_teste_")
    docs_path = os.path.join(tmp, "Documentos")
    downloads_path = os.path.join(tmp, "Downloads")
    os.makedirs(docs_path, exist_ok=True)
    os.makedirs(downloads_path, exist_ok=True)
    cfg.set("pastas_busca", [docs_path, downloads_path])
    cfg.set("extensoes_busca", [".txt", ".md", ".pdf", ".docx"])
    return tmp, docs_path, downloads_path

def test_intent_detectar():
    print("\n--- intent: detectar comandos de abertura de arquivo ---")
    casos = [
        ("abrir arquivo notas.txt", ("OPEN_FILE", "notas.txt", 0.92)),
        ("abre o documento relatorio.pdf", ("OPEN_FILE", "relatorio.pdf", 0.92)),
        ("abra arquivo imagem.png", ("OPEN_FILE", "imagem.png", 0.92)),
        ("abrir o arquivo dados.csv", ("OPEN_FILE", "dados.csv", 0.92)),
    ]
    for comando, esperado in casos:
        res = detectar_file_intent(comando)
        checar(f"detectar '{comando}'", res == esperado, f"esperado {esperado}, obtido {res}")

def test_intent_nao_confunde():
    print("\n--- intent: não confundir com outros comandos ---")
    nao_devem = [
        ("abrir bloco de notas", "OPEN_APP"),
        ("abrir pasta downloads", "OPEN_FOLDER"),
        ("fechar arquivo", None),
        ("abrir", None),
        ("abrir o", None),
    ]
    for comando, nao_esperado_intent in nao_devem:
        res = detectar_file_intent(comando)
        if nao_esperado_intent is None:
            cond = (res is None)
            detalhe = f"esperado None, obtido {res}"
        else:
            # pass if None or intent different
            cond = (res is None or res[0] != nao_esperado_intent)
            detalhe = f"esperado intent != {nao_esperado_intent}, obtido {res}"
        checar(f"nao detectar '{comando}' como file intent", cond, detalhe)

def test_busca_por_nome():
    print("\n--- busca por nome em arquivos de teste ---")
    tmp, docs_path, _ = setup_pastas_teste()
    try:
        with open(os.path.join(docs_path, "notas.txt"), "w", encoding="utf-8") as f:
            f.write("conteúdo de teste")
        with open(os.path.join(docs_path, "Relatorio.TXT"), "w", encoding="utf-8") as f:
            f.write("relatório em maiúsculas")
        with open(os.path.join(docs_path, "outro.md"), "w", encoding="utf-8") as f:
            f.write("# markdown")

        cfg.set("pastas_busca", [docs_path])
        cfg.set("extensoes_busca", [".txt", ".md"])

        resultados = buscar_por_nome("notas")
        checar("busca por 'notas' encontra notas.txt", len(resultados) > 0 and resultados[0]["nome"] == "notas.txt")
        checar("score máximo para nome exato", resultados[0]["score"] == 1.0 if resultados else False)

        resultados = buscar_por_nome("relatorio")
        checar("busca case-insensitive por 'relatorio' encontra Relatorio.TXT", len(resultados) > 0 and resultados[0]["nome"] == "Relatorio.TXT")

        resultados = buscar_por_nome("inexistente")
        checar("busca por nome inexistente retorna lista vazia", len(resultados) == 0)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def test_caminho_seguro():
    print("\n--- validação de caminho seguro ---")
    tmp, docs_path, downloads_path = setup_pastas_teste()
    try:
        txt_path = os.path.join(docs_path, "seguro.txt")
        with open(txt_path, "w") as f:
            f.write("test")
        cfg.set("pastas_busca", [docs_path, downloads_path])

        chevar = caminho_seguro(txt_path)
        checar("caminho dentro das pastas de busca é seguro", chevar, f"obtido {chevar}")

        invalidos = [
            ("../../../etc/passwd", "path traversal"),
            (os.path.join(docs_path, "subdir", "..", "seguro.txt"), "tentativa de .. dentro"),
            ("/tmp/outsider.txt", "fora do home"),
        ]
        for caminho, motivo in invalidos:
            checar(f"caminho inválido ({motivo}) bloqueado", not caminho_seguro(caminho), f"obtido {caminho_seguro(caminho)}")

        cfg.set("pastas_busca", ["/pasta/inexistente"])
        checar("caminho seguro retorna False quando pastas_busca vazias/inexistentes", not caminho_seguro(txt_path))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def test_abrir_arquivo():
    print("\n--- abertura de arquivo (sem abrir de verdade) ---")
    tmp, docs_path, _ = setup_pastas_teste()
    try:
        nome = "plano.md"
        caminho = os.path.join(docs_path, nome)
        with open(caminho, "w", encoding="utf-8") as f:
            f.write("# plano mestre")
        cfg.set("pastas_busca", [docs_path])
        cfg.set("extensoes_busca", [".md"])

        resposta = abrir(nome)
        checar("abrir arquivo existente retorna sucesso", isinstance(resposta, str) and "Abrindo" in resposta and nome in resposta)

        resposta = abrir("arquivo_que_nao_existe.xyz")
        checar("abrir arquivo inexistente retorna mensagem de erro", isinstance(resposta, str) and "Não encontrei" in resposta)

        resposta = abrir("")
        checar("abrir com string vazia pede nome do arquivo", isinstance(resposta, str) and "Qual arquivo" in resposta)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def test_integracao_handler():
    print("\n--- integração com handler via router ---")
    tmp, docs_path, _ = setup_pastas_teste()
    try:
        nome = "tarefa.txt"
        caminho = os.path.join(docs_path, nome)
        with open(caminho, "w", encoding="utf-8") as f:
            f.write("tarefa a fazer")
        cfg.set("pastas_busca", [docs_path])
        cfg.set("extensoes_busca", [".txt"])

        from core.handlers import _abrir_arquivo
        from utils.resultado import Resultado

        res = _abrir_arquivo(nome, f"abrir arquivo {nome}")
        checar("handler OPEN_FILE retorna Resultado", isinstance(res, Resultado))
        checar("handler retorna sucesso", res is not None and res.sucesso)
        checar("mensagem de sucesso contém nome do arquivo", nome in res.mensagem if res and res.mensagem else False)

        res_vazio = _abrir_arquivo("", "abrir arquivo ")
        checar("handler retorna None para alvo vazio", res_vazio is None)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def test_integracao_nexus():
    print("\n--- integração via Nexus Core (end-to-end mock) ---")
    tmp, docs_path, _ = setup_pastas_teste()
    try:
        nome = "orçamento.xlsx"
        caminho = os.path.join(docs_path, nome)
        with open(caminho, "w") as f:
            f.write("dados")
        cfg.set("pastas_busca", [docs_path])
        cfg.set("extensoes_busca", [".xlsx"])

        # Simulamos o fluxo: comando → intent → handler → resposta
        comando = f"abrir arquivo {nome}"
        from core.nexus_core import _interpretar_comando
        acao, alvo, conf = _interpretar_comando(comando)
        print(f"DEBUG: acao={acao}, alvo={alvo!r}, conf={conf}, tipo alvo={type(alvo)}")
        checar("nexus interpreta como OPEN_FILE", acao == "OPEN_FILE" and alvo == nome and conf > 0.9)

        from core.handlers import _abrir_arquivo
        res = _abrir_arquivo(alvo, comando)
        checar("handler processa corretamente", isinstance(res, Resultado) and res.sucesso)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

if __name__ == "__main__":
    print("=" * 68)
    print("TESTE DE ABRIR ARQUIVO POR VOZ (Etapa 6, parte 1)")
    print("=" * 68)

    try:
        test_intent_detectar()
        test_intent_nao_confunde()
        test_busca_por_nome()
        test_caminho_seguro()
        test_abrir_arquivo()
        test_integracao_handler()
        test_integracao_nexus()
    except Exception as e:
        print(f"Erro inesperado durante os testes: {e}")
        import traceback
        traceback.print_exc()

    print("=" * 68)
    if erros:
        print(f"❌ {len(erros)} FALHA(S) de {TOTAL} checagens:")
        for e in erros:
            print(f"   - {e}")
        sys.exit(1)
    else:
        print(f"✅ TODOS OS {TOTAL} TESTES PASSARAM!")
    print("=" * 68)