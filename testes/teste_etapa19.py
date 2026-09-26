"""
Teste da Etapa 19: API REST para integracao externa.
Valida autenticacao, endpoints e respostas.
"""

import sys
import os
import json
import time
import threading
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from plugins.api_rest import (
    AutenticadorJWT, GerenciadorSessoes, ManipuladorAPIREST,
    criar_servidor_rest
)
import urllib.request
import urllib.error

class ClienteAPIREST:
    """Cliente para testar API REST."""
    
    def __init__(self, url_base: str = "http://localhost:8001"):
        self.url_base = url_base
        self.token = None
    
    def _fazer_requisicao(self, metodo: str, endpoint: str, dados: dict = None, token: str = None) -> tuple:
        """Faz requisicao HTTP."""
        url = f"{self.url_base}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if token:
            headers["Authorization"] = f"Bearer {token}"
        elif self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        corpo = None
        if dados:
            corpo = json.dumps(dados).encode()
        
        try:
            requisicao = urllib.request.Request(url, data=corpo, headers=headers, method=metodo)
            resposta = urllib.request.urlopen(requisicao)
            codigo = resposta.status
            dados_resposta = json.loads(resposta.read().decode())
            return codigo, dados_resposta
        except urllib.error.HTTPError as e:
            codigo = e.code
            try:
                dados_resposta = json.loads(e.read().decode())
            except:
                dados_resposta = {"erro": str(e)}
            return codigo, dados_resposta
        except Exception as e:
            return 0, {"erro": str(e)}
    
    def login(self, usuario: str, senha: str) -> bool:
        """Faz login."""
        codigo, resposta = self._fazer_requisicao("POST", "/api/auth/login", {
            "usuario": usuario,
            "senha": senha
        })
        
        if codigo == 200:
            self.token = resposta.get("token")
            return True
        return False
    
    def logout(self) -> bool:
        """Faz logout."""
        codigo, _ = self._fazer_requisicao("POST", "/api/auth/logout")
        self.token = None
        return codigo == 200
    
    def validar_token(self) -> bool:
        """Valida token."""
        codigo, _ = self._fazer_requisicao("GET", "/api/autenticacao/validar")
        return codigo == 200
    
    def status(self) -> tuple:
        """Obtem status do servidor."""
        return self._fazer_requisicao("GET", "/api/status")
    
    def criar_nota(self, titulo: str, conteudo: str) -> tuple:
        """Cria nota."""
        return self._fazer_requisicao("POST", "/api/notas", {
            "titulo": titulo,
            "conteudo": conteudo
        })
    
    def listar_notas(self) -> tuple:
        """Lista notas."""
        return self._fazer_requisicao("GET", "/api/notas")
    
    def atualizar_nota(self, nota_id: str, titulo: str, conteudo: str) -> tuple:
        """Atualiza nota."""
        return self._fazer_requisicao("PUT", f"/api/notas/{nota_id}", {
            "titulo": titulo,
            "conteudo": conteudo
        })
    
    def deletar_nota(self, nota_id: str) -> tuple:
        """Deleta nota."""
        return self._fazer_requisicao("DELETE", f"/api/notas/{nota_id}")
    
    def buscar(self, query: str) -> tuple:
        """Realiza busca."""
        return self._fazer_requisicao("POST", "/api/busca", {
            "query": query
        })
    
    def listar_plugins(self) -> tuple:
        """Lista plugins."""
        return self._fazer_requisicao("GET", "/api/plugins")
    
    def executar_plugin(self, plugin: str, comando: str, parametros: dict = None) -> tuple:
        """Executa plugin."""
        return self._fazer_requisicao("POST", "/api/plugins/executar", {
            "plugin": plugin,
            "comando": comando,
            "parametros": parametros or {}
        })

def teste_autenticador_jwt():
    """Testa autenticador JWT."""
    print("\n--- Autenticador JWT ---")
    
    autenticador = AutenticadorJWT("chave_secreta_teste")
    
    # Gerar token
    token = autenticador.gerar_token("usuario1")
    assert token, "Token deve ser gerado"
    assert len(token) > 0, "Token nao deve estar vazio"
    print("  X token gerado")
    
    # Validar token
    valido, usuario = autenticador.validar_token(token)
    assert valido, "Token deve ser valido"
    assert usuario == "usuario1", "Usuario deve corresponder"
    print("  X token validado corretamente")
    
    # Token invalido
    valido, usuario = autenticador.validar_token("token_invalido")
    assert not valido, "Token invalido deve ser rejeitado"
    print("  X token invalido rejeitado")
    
    # Revogar token
    autenticador.revogar_token(token)
    valido, _ = autenticador.validar_token(token)
    assert not valido, "Token revogado nao deve ser valido"
    print("  X token revogado com sucesso")

def teste_gerenciador_sessoes():
    """Testa gerenciador de sessoes."""
    print("\n--- Gerenciador Sessoes ---")
    
    gerenciador = GerenciadorSessoes()
    
    # Autenticar
    assert gerenciador.autenticar("demo", "demo123"), "Deve autenticar usuario valido"
    print("  X usuario autenticado")
    
    # Senha errada
    assert not gerenciador.autenticar("demo", "senha_errada"), "Senha errada deve falhar"
    print("  X senha errada rejeitada")
    
    # Criar sessao
    sessao_id = gerenciador.criar_sessao("demo")
    assert sessao_id, "Sessao deve ser criada"
    print("  X sessao criada")
    
    # Obter sessao
    sessao = gerenciador.obter_sessao(sessao_id)
    assert sessao is not None, "Sessao deve existir"
    assert sessao["usuario"] == "demo", "Usuario deve corresponder"
    print("  X sessao obtida corretamente")
    
    # Encerrar sessao
    gerenciador.encerrar_sessao(sessao_id)
    sessao = gerenciador.obter_sessao(sessao_id)
    assert sessao is None, "Sessao deve ser encerrada"
    print("  X sessao encerrada")

def teste_servidor_rest():
    """Testa servidor REST completo."""
    print("\n--- Servidor REST ---")
    
    porta = 8001
    servidor = criar_servidor_rest(porta)
    
    # Iniciar servidor em thread
    thread_servidor = threading.Thread(target=servidor.serve_forever, daemon=True)
    thread_servidor.start()
    
    time.sleep(0.5)  # Aguardar inicializacao
    
    try:
        cliente = ClienteAPIREST(f"http://localhost:{porta}")
        
        # 1. Status sem autenticacao
        codigo, resposta = cliente.status()
        assert codigo == 200, "Status deve ser acessivel"
        assert resposta["status"] == "ok", "Status deve retornar ok"
        print("  X status acessivel")
        
        # 2. Tentar acessar recurso protegido sem token
        codigo, _ = cliente.listar_notas()
        assert codigo == 401, "Deve rejeitar sem token"
        print("  X recurso protegido sem token")
        
        # 3. Login
        assert cliente.login("demo", "demo123"), "Login deve funcionar"
        print("  X login funciona")
        
        # 4. Validar token
        assert cliente.validar_token(), "Token deve ser valido"
        print("  X token validado")
        
        # 5. Criar nota
        codigo, resposta = cliente.criar_nota("Python", "Linguagem excelente")
        assert codigo == 201, "Deve criar nota"
        nota_id = resposta["nota_id"]
        print("  X nota criada")
        
        # 6. Listar notas
        codigo, resposta = cliente.listar_notas()
        assert codigo == 200, "Deve listar notas"
        assert resposta["total"] == 1, "Deve ter 1 nota"
        print("  X notas listadas")
        
        # 7. Atualizar nota
        codigo, resposta = cliente.atualizar_nota(nota_id, "Python 3", "Conteudo atualizado")
        assert codigo == 200, "Deve atualizar nota"
        print("  X nota atualizada")
        
        # 8. Buscar
        codigo, resposta = cliente.buscar("Python")
        assert codigo == 200, "Deve realizar busca"
        assert resposta["total"] == 1, "Deve encontrar 1 resultado"
        print("  X busca funciona")
        
        # 9. Listar plugins
        codigo, resposta = cliente.listar_plugins()
        assert codigo == 200, "Deve listar plugins"
        assert len(resposta["plugins"]) > 0, "Deve ter plugins"
        print("  X plugins listados")
        
        # 10. Executar plugin
        codigo, resposta = cliente.executar_plugin("processador", "processar_texto", {
            "texto": "Hello World"
        })
        assert codigo == 200, "Deve executar plugin"
        assert resposta["resultado"]["comprimento"] == 11, "Deve processar texto"
        print("  X plugin executado")
        
        # 11. Deletar nota
        codigo, _ = cliente.deletar_nota(nota_id)
        assert codigo == 200, "Deve deletar nota"
        print("  X nota deletada")
        
        # 12. Logout
        assert cliente.logout(), "Logout deve funcionar"
        assert not cliente.validar_token(), "Token deve ser invalido apos logout"
        print("  X logout funciona")
        
        print("  X SERVIDOR REST COMPLETO FUNCIONANDO")
        
    finally:
        servidor.shutdown()

def teste_fluxo_completo_api():
    """Testa fluxo completo da API."""
    print("\n--- Fluxo Completo API ---")
    
    porta = 8002
    servidor = criar_servidor_rest(porta)
    thread_servidor = threading.Thread(target=servidor.serve_forever, daemon=True)
    thread_servidor.start()
    
    time.sleep(0.5)
    
    try:
        cliente = ClienteAPIREST(f"http://localhost:{porta}")
        
        print("  1. Autenticando...")
        assert cliente.login("demo", "demo123")
        
        print("  2. Criando notas...")
        _, r1 = cliente.criar_nota("Python Tips", "Dicas de Python")
        id1 = r1["nota_id"]
        _, r2 = cliente.criar_nota("JavaScript", "Guia completo")
        id2 = r2["nota_id"]
        
        print("  3. Listando notas...")
        _, resposta = cliente.listar_notas()
        assert resposta["total"] == 2
        
        print("  4. Buscando...")
        _, resposta = cliente.buscar("Python")
        assert resposta["total"] == 1
        
        print("  5. Executando plugin...")
        _, resposta = cliente.executar_plugin("analise", "analisar_sentimento", {
            "texto": "Python eh otimo"
        })
        assert resposta["resultado"]["sentimento"] == "positivo"
        
        print("  6. Atualizando nota...")
        cliente.atualizar_nota(id1, "Python Tips v2", "Dicas atualizadas")
        
        print("  7. Deletando nota...")
        cliente.deletar_nota(id2)
        
        _, resposta = cliente.listar_notas()
        assert resposta["total"] == 1
        
        print("  8. Logout...")
        assert cliente.logout()
        
        print("  X FLUXO COMPLETO FUNCIONANDO")
        
    finally:
        servidor.shutdown()

def main():
    print("=" * 68)
    print("TESTE DA ETAPA 19: API REST")
    print("=" * 68)
    
    try:
        teste_autenticador_jwt()
        teste_gerenciador_sessoes()
        teste_servidor_rest()
        teste_fluxo_completo_api()
        
        print("\n" + "=" * 68)
        print("OK TODOS OS TESTES DA ETAPA 19 PASSARAM!")
        print("API REST validada.")
        print("=" * 68)
        return 0
        
    except AssertionError as e:
        print(f"\nERRO: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\nERRO INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
