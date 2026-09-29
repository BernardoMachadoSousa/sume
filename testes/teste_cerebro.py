"""
Testes do sistema Cérebro — grafo de conhecimento pessoal no vault.
"""

import os
import sys
import shutil
import tempfile
import unittest

# Garante que o root do projeto está no path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)


# ── Fixtures: redireciona o vault para pasta temporária ──────────────────────

VAULT_TMP = None

def setUpModule():
    global VAULT_TMP
    VAULT_TMP = tempfile.mkdtemp(prefix="sume_cerebro_test_")
    import modulos.vault as v
    v.ROOT = VAULT_TMP
    import modulos.cerebro as c
    c.vault.ROOT = VAULT_TMP

def tearDownModule():
    if VAULT_TMP and os.path.exists(VAULT_TMP):
        shutil.rmtree(VAULT_TMP)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _set_usuario(nome: str):
    from modulos.memoria import guardar, PERMANENTE
    guardar("nome_usuario", nome, PERMANENTE)


def _ler_nota(titulo: str) -> str:
    import modulos.vault as v
    return v.ler(titulo) or ""


# ── Testes de Intent ─────────────────────────────────────────────────────────

class TestCerebroIntent(unittest.TestCase):

    def _det(self, cmd):
        from core.intents.cerebro_intent import detectar
        return detectar(cmd)

    def test_namorada_detecta_save(self):
        r = self._det("minha namorada é Malu")
        self.assertIsNotNone(r)
        self.assertEqual(r[0], "CEREBRO_SAVE")

    def test_aniversario_detecta_save(self):
        r = self._det("o aniversário da Malu é 12 de outubro")
        self.assertIsNotNone(r)
        self.assertEqual(r[0], "CEREBRO_SAVE")

    def test_mae_detecta_save(self):
        r = self._det("minha mãe é Cristina")
        self.assertIsNotNone(r)
        self.assertEqual(r[0], "CEREBRO_SAVE")

    def test_ler_sobre_detecta_read(self):
        r = self._det("o que você sabe sobre Malu?")
        self.assertIsNotNone(r)
        self.assertEqual(r[0], "CEREBRO_READ")

    def test_quem_e_detecta_read(self):
        r = self._det("quem é Malu?")
        self.assertIsNotNone(r)
        self.assertEqual(r[0], "CEREBRO_READ")

    def test_quando_aniversario_detecta_read(self):
        r = self._det("quando é o aniversário da Malu?")
        self.assertIsNotNone(r)
        self.assertEqual(r[0], "CEREBRO_READ")

    def test_comando_irrelevante_retorna_none(self):
        r = self._det("abra o chrome")
        self.assertIsNone(r)

    def test_confianca_save_alta(self):
        r = self._det("minha namorada é Malu")
        self.assertGreaterEqual(r[2], 0.9)

    def test_confianca_read_alta(self):
        r = self._det("quem é Malu?")
        self.assertGreaterEqual(r[2], 0.9)


# ── Testes do módulo cerebro.py ──────────────────────────────────────────────

class TestCerebroSalvarFato(unittest.TestCase):

    def setUp(self):
        _set_usuario("Bernardo")

    def test_namorada_cria_nota_entidade(self):
        from modulos.cerebro import salvar_fato
        salvar_fato("minha namorada é Malu")
        corpo = _ler_nota("Malu")
        self.assertIn("namorada", corpo.lower())

    def test_namorada_link_bidireccional(self):
        from modulos.cerebro import salvar_fato
        salvar_fato("minha namorada é Malu")
        nota_user = _ler_nota("Bernardo")
        self.assertIn("Malu", nota_user)

    def test_aniversario_salvo_na_nota(self):
        from modulos.cerebro import salvar_fato
        salvar_fato("o aniversário da Malu é 12 de outubro")
        corpo = _ler_nota("Malu")
        self.assertIn("aniversário", corpo.lower())
        self.assertIn("12 de outubro", corpo.lower())

    def test_nota_usuario_criada_automaticamente(self):
        from modulos.cerebro import _garantir_nota_usuario
        _garantir_nota_usuario()
        corpo = _ler_nota("Bernardo")
        self.assertTrue(len(corpo) > 0)

    def test_mae_cria_nota(self):
        from modulos.cerebro import salvar_fato
        msg = salvar_fato("minha mãe é Cristina")
        self.assertIn("Cristina", msg)
        corpo = _ler_nota("Cristina")
        self.assertIn("mãe", corpo.lower())

    def test_retorno_confirma_entidade(self):
        from modulos.cerebro import salvar_fato
        msg = salvar_fato("minha namorada é Malu")
        self.assertIn("Malu", msg)

    def test_fato_livre_sobre_entidade(self):
        from modulos.cerebro import salvar_fato_sobre
        salvar_fato_sobre("Malu", "gosta de café")
        corpo = _ler_nota("Malu")
        self.assertIn("gosta de café", corpo)

    def test_ler_fatos_existente(self):
        from modulos.cerebro import salvar_fato, ler_fatos
        salvar_fato("minha namorada é Malu")
        resultado = ler_fatos("Malu")
        self.assertIn("Malu", resultado)

    def test_ler_fatos_inexistente(self):
        from modulos.cerebro import ler_fatos
        resultado = ler_fatos("PessoaInexistente123")
        self.assertIn("Não tenho", resultado)

    def test_acumula_fatos_na_mesma_nota(self):
        from modulos.cerebro import salvar_fato, salvar_fato_sobre
        salvar_fato("minha namorada é Malu")
        salvar_fato("o aniversário da Malu é 12 de outubro")
        salvar_fato_sobre("Malu", "estuda medicina")
        corpo = _ler_nota("Malu")
        self.assertIn("namorada", corpo.lower())
        self.assertIn("12 de outubro", corpo.lower())
        self.assertIn("estuda medicina", corpo)


# ── Teste end-to-end via nexus_core ──────────────────────────────────────────

class TestCerebroNexus(unittest.TestCase):

    def setUp(self):
        _set_usuario("Bernardo")

    def test_nexus_salva_namorada(self):
        from core.nexus_core import processar
        resp = processar("minha namorada é Malu")
        self.assertIn("Malu", resp)

    def test_nexus_le_fatos(self):
        from core.nexus_core import processar
        processar("minha namorada é Malu")
        resp = processar("o que você sabe sobre Malu?")
        self.assertIn("Malu", resp)


if __name__ == "__main__":
    unittest.main(verbosity=2)
