"""
Testes das camadas de memória: proveniência, segredos, recall e backup.

Cobre os upgrades adicionados a partir da pesquisa dos projetos
de agentes pessoais (3 camadas T1/T2/T3, categorias, importance scoring,
proveniência, recusa de segredos e backup/restore).
"""

import os
import sys
import shutil
import sqlite3
import tempfile
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)


# ── Fixtures: vault e banco temporários ───────────────────────────────────────

VAULT_TMP = None
DB_TMP = None
DB_ORIGINAL = None


def setUpModule():
    global VAULT_TMP, DB_TMP, DB_ORIGINAL
    VAULT_TMP = tempfile.mkdtemp(prefix="sume_recall_test_")
    DB_TMP = tempfile.mkdtemp(prefix="sume_recall_db_")

    import modulos.vault as v
    v.ROOT = VAULT_TMP
    import modulos.cerebro as c
    c.vault.ROOT = VAULT_TMP

    import modulos.memoria as m
    DB_ORIGINAL = m.DB
    m.DB = os.path.join(DB_TMP, "memoria.db")


def tearDownModule():
    import modulos.memoria as m
    if DB_ORIGINAL:
        m.DB = DB_ORIGINAL
    for pasta in (VAULT_TMP, DB_TMP):
        if pasta and os.path.exists(pasta):
            shutil.rmtree(pasta)


def _set_usuario(nome: str):
    from modulos.memoria import guardar, PERMANENTE
    guardar("nome_usuario", nome, PERMANENTE)


def _caminho(titulo: str) -> str:
    import modulos.vault as v
    return os.path.join(VAULT_TMP, f"{titulo.lower()}.md")


# ── Segredos: recusa de armazenar credenciais ─────────────────────────────────

class TestDeteccaoSegredos(unittest.TestCase):

    def test_detecta_senha_contextual(self):
        from utils.segredos import detectar_segredo
        self.assertIsNotNone(detectar_segredo("minha senha é 123456"))

    def test_detecta_chave_openai(self):
        from utils.segredos import detectar_segredo
        self.assertIsNotNone(detectar_segredo("token sk-abcdefghijklmnop1234"))

    def test_detecta_cpf(self):
        from utils.segredos import detectar_segredo
        self.assertIsNotNone(detectar_segredo("meu cpf é 123.456.789-00"))

    def test_detecta_cartao(self):
        from utils.segredos import detectar_segredo
        self.assertIsNotNone(detectar_segredo("cartão 4111 1111 1111 1111"))

    def test_detecta_senha_em_url(self):
        from utils.segredos import detectar_segredo
        self.assertIsNotNone(detectar_segredo("git clone https://joao:abc123@github.com/x/y"))

    def test_nao_detecta_texto_inocente(self):
        from utils.segredos import detectar_segredo
        for texto in [
            "minha namorada é Malu",
            "gosto de café",
            "nasci em 12/10/2004",
            "trabalho na empresa X desde 2020",
            "o código é 12345",
        ]:
            with self.subTest(texto=texto):
                self.assertIsNone(detectar_segredo(texto))

    def test_texto_vazio_nao_quebra(self):
        from utils.segredos import detectar_segredo, texto_contem_segredo
        self.assertIsNone(detectar_segredo(""))
        self.assertIsNone(detectar_segredo(None))
        self.assertFalse(texto_contem_segredo(None))


class TestRecusaSegredosNoCerebro(unittest.TestCase):

    def setUp(self):
        _set_usuario("Bernardo")

    def test_salvar_fato_recusa_senha(self):
        from modulos.cerebro import salvar_fato
        msg = salvar_fato("minha senha do banco é hunter2")
        self.assertIn("Não vou guardar", msg)
        # E nada foi gravado no vault
        for nome in os.listdir(VAULT_TMP):
            caminho = os.path.join(VAULT_TMP, nome)
            if os.path.isfile(caminho):
                with open(caminho, "r", encoding="utf-8") as f:
                    self.assertNotIn("hunter2", f.read())

    def test_salvar_fato_sobre_recusa_chave_api(self):
        from modulos.cerebro import salvar_fato_sobre
        salvar_fato_sobre("Credenciais", "minha api key é sk-abcdefghijklmnop9999")
        self.assertFalse(os.path.exists(_caminho("Credenciais")))

    def test_memoria_recusa_segredo(self):
        from modulos.memoria import processar_memoria, lembrar
        resposta = processar_memoria("anote que minha senha é 123456")
        self.assertIn("Não vou guardar", resposta)
        self.assertIsNone(lembrar("minha senha é 123456"))

    def test_memoria_ainda_aceita_texto_normal(self):
        from modulos.memoria import processar_memoria
        resposta = processar_memoria("anote que gosto de azul")
        self.assertIn("Guardei", resposta)


# ── Categorias, importância e proveniência ────────────────────────────────────

class TestCategorizacao(unittest.TestCase):

    def test_categorias_basicas(self):
        from modulos.cerebro import _categorizar_fato
        self.assertEqual(_categorizar_fato("nome: Bernardo"), "nome")
        self.assertEqual(_categorizar_fato("aniversário: 12 de outubro"), "aniversario")
        self.assertEqual(_categorizar_fato("mora em: Salvador"), "moradia")
        self.assertEqual(_categorizar_fato("namorada de: [[Malu]]"), "relacao")
        self.assertEqual(_categorizar_fato("gosta de: café"), "preferencia")
        self.assertEqual(_categorizar_fato("texto qualquer"), "geral")

    def test_importancia_ordenada_por_categoria(self):
        from modulos.cerebro import _importancia_fato
        nome = _importancia_fato("nome", 0.9)
        relacao = _importancia_fato("relacao", 0.9)
        geral = _importancia_fato("geral", 0.9)
        self.assertGreater(nome, relacao)
        self.assertGreater(relacao, geral)
        self.assertTrue(0.0 <= geral <= 1.0)

    def test_importancia_sobe_com_confianca(self):
        from modulos.cerebro import _importancia_fato
        baixa = _importancia_fato("moradia", 0.2)
        alta = _importancia_fato("moradia", 0.95)
        self.assertGreater(alta, baixa)

    def test_importancia_limitada_a_um(self):
        from modulos.cerebro import _importancia_fato
        self.assertLessEqual(_importancia_fato("nome", 5.0), 1.0)
        self.assertGreaterEqual(_importancia_fato("nome", -3.0), 0.0)


class TestProvenienciaNasRelacoes(unittest.TestCase):

    def setUp(self):
        _set_usuario("Bernardo")
        import modulos.vault as v
        v.obter_ou_criar_nota("Malu")

    def _relacoes(self, titulo):
        import modulos.vault as v
        return v.obter_relacoes(titulo) or []

    def test_relacao_tem_campos_de_proveniencia(self):
        from modulos.cerebro import _adicionar_fato
        _adicionar_fato("Malu", "pessoa", "mora em: [[Salvador]]",
                        links_extras=["Salvador"], confianca=0.9, fonte="conversa")
        rels = self._relacoes("Malu")
        alvo = [r for r in rels if r.get("alvo") == "Salvador"]
        self.assertTrue(alvo, f"relação não encontrada: {rels}")
        rel = alvo[0]
        for campo in ("categoria", "importancia", "confianca", "fonte", "usos"):
            self.assertIn(campo, rel, f"campo ausente: {campo}")
        self.assertEqual(rel["fonte"], "conversa")
        self.assertEqual(rel["confianca"], 0.9)
        self.assertEqual(rel["usos"], 0)

    def test_round_trip_preserva_campos(self):
        """Relação salva e relida do disco mantém todos os metadados."""
        from modulos.cerebro import _adicionar_fato
        from modulos import vault

        _adicionar_fato("Malu", "pessoa", "trabalha em: [[Hospital]]",
                        links_extras=["Hospital"], confianca=0.8, fonte="conversa")
        # Releitura a partir do arquivo, não de cache em memória
        with open(_caminho("Malu"), "r", encoding="utf-8") as f:
            bruto = f.read()
        partes = bruto.split("---", 2)
        rels = vault._frontmatter_objeto(partes[1], "relacoes")
        alvo = [r for r in rels if r.get("alvo") == "Hospital"]
        self.assertTrue(alvo, f"round-trip perdeu a relação: {rels}")
        self.assertEqual(alvo[0]["categoria"], "trabalho")
        self.assertEqual(alvo[0]["confianca"], 0.8)
        self.assertEqual(alvo[0]["fonte"], "conversa")

    def test_uso_preservado_entre_salvadas(self):
        from modulos.cerebro import _adicionar_fato
        import modulos.vault as v

        _adicionar_fato("Malu", "pessoa", "gosta de: [[Café]]",
                        links_extras=["Café"], confianca=0.9)
        # Simula um recall anterior
        rels = v.obter_relacoes("Malu") or []
        for rel in rels:
            if rel.get("alvo") == "Café":
                rel["usos"] = 3
        v.salvar("Malu", v.ler("Malu") or "", relacoes=rels)

        # Novo fato na mesma nota não pode zerar o contador
        _adicionar_fato("Malu", "pessoa", "estuda: [[Medicina]]",
                        links_extras=["Medicina"], confianca=0.9)
        rels = [r for r in (v.obter_relacoes("Malu") or []) if r.get("alvo") == "Café"]
        self.assertTrue(rels)
        self.assertEqual(rels[0]["usos"], 3)


# ── Recall: T1 (quente) e T2 (sob demanda) ───────────────────────────────────

class TestRecall(unittest.TestCase):

    def setUp(self):
        _set_usuario("Bernardo")
        from modulos.cerebro import _adicionar_fato
        import modulos.vault as v
        v.obter_ou_criar_nota("Malu")
        _adicionar_fato("Malu", "pessoa", "gosta de: [[Café]]",
                        links_extras=["Café"], confianca=0.9)
        _adicionar_fato("Malu", "pessoa", "mora em: [[Salvador]]",
                        links_extras=["Salvador"], confianca=0.9)

    def test_contexto_quente_traz_relacoes(self):
        from modulos import recall
        t1 = recall.contexto_quente()
        self.assertIn("gosta", t1.lower() + " ".join([t1]))
        self.assertTrue(t1.strip(), "contexto quente veio vazio")

    def test_contexto_quente_respeita_limite(self):
        from modulos import recall
        self.assertLessEqual(len(recall.contexto_quente(limite=1).splitlines()), 1)

    def test_recuperar_encontra_por_termo(self):
        from modulos import recall
        achados = recall.recuperar("onde a Malu mora?", contar_uso=False)
        self.assertTrue(achados, "não recuperou nada")
        alvos = [a.get("alvo", "") for a in achados]
        self.assertTrue(any("Salvador" in str(a) for a in alvos + [str(x) for x in achados]))

    def test_recuperar_ignora_termos_vazios(self):
        from modulos import recall
        self.assertEqual(recall.recuperar("", contar_uso=False), [])
        self.assertEqual(recall.recuperar("a o de", contar_uso=False), [])

    def test_recuperar_incrementa_usos(self):
        from modulos import recall
        import modulos.vault as v
        recall.recuperar("Malu Salvador", contar_uso=True)
        rels = [r for r in (v.obter_relacoes("Malu") or []) if r.get("alvo") == "Salvador"]
        self.assertTrue(rels)
        self.assertGreaterEqual(rels[0].get("usos", 0), 1)

    def test_montar_prompt_tem_t1_e_t2(self):
        from modulos import recall
        contexto = recall.montar_prompt_completo("o que a Malu gosta?")
        self.assertIn("t1", contexto)
        self.assertIn("t2", contexto)


# ── Recall injetado no prompt (com a trava de privacidade) ───────────────────

class TestRecallNoPrompt(unittest.TestCase):

    def setUp(self):
        _set_usuario("Bernardo")
        from modulos.cerebro import _adicionar_fato
        import modulos.vault as v
        v.obter_ou_criar_nota("Malu")
        _adicionar_fato("Malu", "pessoa", "gosta de: [[Café]]",
                        links_extras=["Café"], confianca=0.9)

    def test_contexto_local_inclui_segundo_cerebro(self):
        from modulos import ia_conversacional as ia
        extras = ia._contexto_extra("Bernardo", True, consulta="o que a Malu gosta?")
        self.assertIn("segundo cérebro", extras)
        self.assertIn("gosta", extras.lower())

    def test_contexto_remoto_NAO_inclui_memoria_sem_autorizacao(self):
        """Trava de privacidade: sem autorização, o prompt fica limpo."""
        from modulos import ia_conversacional as ia
        extras = ia._contexto_extra("Bernardo", False, consulta="o que a Malu gosta?")
        self.assertEqual(extras, "")
        self.assertNotIn("Café", extras)

    def test_recall_quebrado_nao_derruba_a_conversa(self):
        """Recall é reforço: se falhar, a conversa continua sem ele."""
        from modulos import ia_conversacional as ia
        from modulos import recall

        original = recall.contexto_quente
        recall.contexto_quente = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("vault fora"))
        try:
            extras = ia._contexto_extra("Bernardo", True, consulta="o que a Malu gosta?")
        finally:
            recall.contexto_quente = original
        # O nome continua presente: a falha é isolada
        self.assertIn("Bernardo", extras)


# ── Backup e restauração ─────────────────────────────────────────────────────

class TestBackup(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="sume_backup_test_")
        _set_usuario("Bernardo")

    def tearDown(self):
        if os.path.exists(self.dir):
            shutil.rmtree(self.dir)

    def test_backup_memoria_cria_arquivo(self):
        from modulos import backup
        caminho = backup.backup_memoria(self.dir)
        self.assertTrue(caminho.endswith(".db"))
        self.assertTrue(os.path.exists(caminho))
        # O backup tem que ser um SQLite legível
        conn = sqlite3.connect(caminho)
        try:
            self.assertIsNotNone(conn.execute("SELECT name FROM sqlite_master").fetchone())
        finally:
            conn.close()

    def test_backup_vault_cria_zip_com_notas(self):
        from modulos import backup
        from modulos.vault import obter_ou_criar_nota
        import zipfile

        obter_ou_criar_nota("Nota Para Backup")
        caminho = backup.backup_vault(self.dir)
        self.assertTrue(caminho.endswith(".zip"))
        with zipfile.ZipFile(caminho) as z:
            nomes = z.namelist()
        # O vault grava o arquivo com o título normalizado em kebab-case
        self.assertTrue(any(n.endswith("nota-para-backup.md") for n in nomes), nomes)

    def test_restaura_memoria(self):
        from modulos import backup
        from modulos.memoria import guardar, lembrar, esquecer

        # A chave precisa existir ANTES do backup, senão o restore não a recupera
        guardar("chave_recall", "valor_recall")
        caminho = backup.backup_memoria(self.dir)

        esquecer("chave_recall")
        self.assertIsNone(lembrar("chave_recall"))

        msg = backup.restaurar_memoria(caminho)
        self.assertIn("restaurada", msg.lower())
        self.assertEqual(lembrar("chave_recall"), "valor_recall")

    def test_restaura_vault_preservando_arquivo_anterior(self):
        from modulos import backup
        from modulos.vault import obter_ou_criar_nota

        caminho = backup.backup_vault(self.dir)
        obter_ou_criar_nota("Nota criada depois do backup")

        msg = backup.restaurar_vault(caminho)
        self.assertIn("restaurado", msg.lower())
        # Nota posterior ao backup não deve sobreviver, e o antigo fica arquivado
        self.assertFalse(os.path.exists(_caminho("Nota criada depois do backup")))
        import modulos.vault as v
        raiz = v._pasta_vault()
        pai = os.path.dirname(os.path.abspath(raiz))
        arquivados = [d for d in os.listdir(pai) if d.startswith(".vault-anterior-")]
        self.assertTrue(arquivados, "vault anterior não foi arquivado")

    def test_restaura_arquivo_inexistente(self):
        from modulos import backup
        self.assertIn("Não encontrei", backup.restaurar_memoria(
            os.path.join(self.dir, "nao_existe.db")))

    def test_restaura_extensao_invalida(self):
        from modulos import backup
        self.assertIn("Só restauro", backup.restaurar("coisa.txt"))

    def test_listar_backups_ordena_por_data(self):
        from modulos import backup
        backup.backup_memoria(self.dir)
        backup.backup_vault(self.dir)
        itens = backup.listar_backups(self.dir)
        self.assertGreaterEqual(len(itens), 2)
        tipos = {i["tipo"] for i in itens}
        self.assertEqual(tipos, {"memoria", "vault"})
        self.assertEqual([i["quando"] for i in itens],
                         sorted([i["quando"] for i in itens], reverse=True))

    def test_retencao_limita_quantidade(self):
        from modulos import backup
        for _ in range(backup.RETENCAO + 3):
            backup.backup_memoria(self.dir)
        gerados = [f for f in os.listdir(self.dir) if f.endswith(".db")]
        self.assertLessEqual(len(gerados), backup.RETENCAO)


if __name__ == "__main__":
    unittest.main(verbosity=2)
