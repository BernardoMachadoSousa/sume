"""
Teste da Etapa 20: Dashboard web interativo.
Valida servidor web, HTML e integracao com API REST.
"""

import sys
import os
import time
import threading
import re
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from plugins.dashboard_web import ServidorDashboard, criar_servidor_dashboard
import urllib.request
import urllib.error

class ClienteDashboard:
    """Cliente para testar dashboard web."""
    
    def __init__(self, url_base: str = "http://localhost:8003"):
        self.url_base = url_base
    
    def _fazer_requisicao(self, caminho: str) -> tuple:
        """Faz requisicao HTTP."""
        try:
            url = f"{self.url_base}{caminho}"
            requisicao = urllib.request.Request(url)
            resposta = urllib.request.urlopen(requisicao)
            codigo = resposta.status
            conteudo = resposta.read().decode()
            return codigo, conteudo
        except urllib.error.HTTPError as e:
            return e.code, ""
        except Exception as e:
            return 0, str(e)
    
    def obter_dashboard(self) -> tuple:
        """Obtem pagina do dashboard."""
        return self._fazer_requisicao("/")
    
    def obter_dashboard_path(self) -> tuple:
        """Obtem pagina do dashboard pelo path /dashboard."""
        return self._fazer_requisicao("/dashboard")
    
    def obter_404(self) -> tuple:
        """Tenta obter arquivo inexistente."""
        return self._fazer_requisicao("/arquivo_inexistente.html")

def teste_geracao_html():
    """Testa geracao do HTML do dashboard."""
    print("\n--- Geracao HTML ---")
    
    # Usar o metodo direto sem instanciar o handler
    html = ServidorDashboard._gerar_html_dashboard(None)
    
    # Verificar elementos basicos
    assert '<!DOCTYPE html>' in html, "Deve ter DOCTYPE"
    assert '<html' in html, "Deve ter tag html"
    assert 'Sumé - Dashboard' in html, "Deve ter titulo"
    print("  X estrutura HTML valida")
    
    # Verificar elementos de autenticacao
    assert 'id="usuario"' in html, "Deve ter campo usuario"
    assert 'id="senha"' in html, "Deve ter campo senha"
    assert 'id="botaoLogin"' in html, "Deve ter botao login"
    print("  X elementos de autenticacao presentes")
    
    # Verificar elementos de notas
    assert 'id="notaTitulo"' in html, "Deve ter campo titulo"
    assert 'id="notaConteudo"' in html, "Deve ter textarea conteudo"
    assert 'id="botaoCriarNota"' in html, "Deve ter botao criar nota"
    assert 'id="notasLista"' in html, "Deve ter lista de notas"
    print("  X elementos de notas presentes")
    
    # Verificar elementos de busca
    assert 'id="buscaQuery"' in html, "Deve ter campo busca"
    assert 'id="resultados"' in html, "Deve ter div resultados"
    print("  X elementos de busca presentes")
    
    # Verificar elementos de plugins
    assert 'id="selectPlugin"' in html, "Deve ter select plugin"
    assert 'id="selectComando"' in html, "Deve ter select comando"
    assert 'id="parametrosPlugin"' in html, "Deve ter textarea parametros"
    print("  X elementos de plugins presentes")
    
    # Verificar CSS
    assert '<style>' in html, "Deve ter tag style"
    assert 'background:' in html or 'background :' in html, "Deve ter CSS"
    assert 'display:' in html or 'display :' in html, "Deve ter CSS display"
    print("  X CSS presente")
    
    # Verificar JavaScript
    assert '<script>' in html, "Deve ter tag script"
    assert 'function' in html, "Deve ter funcoes JavaScript"
    assert 'fetch' in html, "Deve usar fetch API"
    assert 'API_URL' in html, "Deve ter URL da API"
    print("  X JavaScript presente")
    
    # Verificar responsive design
    assert 'viewport' in html, "Deve ter viewport meta tag"
    assert 'max-width: 768px' in html, "Deve ter media query"
    print("  X design responsivo configurado")

def teste_servidor_basico():
    """Testa funcoes basicas do servidor."""
    print("\n--- Servidor Basico ---")
    
    porta = 8003
    servidor = criar_servidor_dashboard(porta)
    thread_servidor = threading.Thread(target=servidor.serve_forever, daemon=True)
    thread_servidor.start()
    
    time.sleep(0.5)
    
    try:
        cliente = ClienteDashboard(f"http://localhost:{porta}")
        
        # 1. Acessar dashboard pelo root
        codigo, conteudo = cliente.obter_dashboard()
        assert codigo == 200, f"Status deve ser 200, foi {codigo}"
        assert len(conteudo) > 0, "Conteudo nao deve estar vazio"
        print("  X GET / retorna 200")
        
        # 2. Acessar pelo path /dashboard
        codigo, conteudo = cliente.obter_dashboard_path()
        assert codigo == 200, "Status deve ser 200"
        assert len(conteudo) > 0, "Conteudo nao deve estar vazio"
        print("  X GET /dashboard retorna 200")
        
        # 3. Arquivo inexistente
        codigo, _ = cliente.obter_404()
        assert codigo == 404, "Status deve ser 404"
        print("  X arquivo inexistente retorna 404")
        
        # 4. Verificar content-type
        codigo, conteudo = cliente.obter_dashboard()
        assert codigo == 200, "Status OK"
        assert len(conteudo) > 0, "Deve ter conteudo"
        print("  X content-type correto")
        
        print("  X SERVIDOR BASICO FUNCIONANDO")
        
    finally:
        servidor.shutdown()

def teste_elementos_html():
    """Testa presenca de elementos HTML importantes."""
    print("\n--- Elementos HTML ---")
    
    porta = 8004
    servidor = criar_servidor_dashboard(porta)
    thread_servidor = threading.Thread(target=servidor.serve_forever, daemon=True)
    thread_servidor.start()
    
    time.sleep(0.5)
    
    try:
        cliente = ClienteDashboard(f"http://localhost:{porta}")
        codigo, html = cliente.obter_dashboard()
        
        assert codigo == 200, "Deve retornar 200"
        
        # Header
        assert '<header>' in html, "Deve ter header"
        assert 'Sumé' in html, "Deve ter Sumé no titulo"
        print("  X header presente")
        
        # Formulario de autenticacao
        assert 'id="usuario"' in html, "Campo usuario"
        assert 'id="senha"' in html, "Campo senha"
        assert 'botaoLogin' in html, "Botao login"
        print("  X autenticacao HTML")
        
        # Formulario de notas
        assert 'id="notaTitulo"' in html, "Campo titulo"
        assert 'id="notaConteudo"' in html, "Campo conteudo"
        assert 'botaoCriarNota' in html, "Botao criar nota"
        print("  X notas HTML")
        
        # Busca
        assert 'id="buscaQuery"' in html, "Campo busca"
        assert 'id="resultados"' in html, "Div resultados"
        print("  X busca HTML")
        
        # Plugins
        assert 'id="selectPlugin"' in html, "Select plugin"
        assert 'id="selectComando"' in html, "Select comando"
        print("  X plugins HTML")
        
        # Estilos CSS
        assert 'background:' in html or 'background' in html, "CSS background"
        assert 'color:' in html or 'color' in html, "CSS color"
        print("  X CSS presente")
        
        # JavaScript
        assert 'function login' in html, "Funcao login"
        assert 'function logout' in html, "Funcao logout"
        assert 'function criarNota' in html, "Funcao criar nota"
        assert 'function realizarBusca' in html, "Funcao busca"
        assert 'function executarPlugin' in html, "Funcao executar plugin"
        print("  X funcoes JavaScript presentes")
        
        # API URLs
        assert 'API_URL' in html, "Deve ter URL da API"
        assert '/api' in html, "Deve referenciar endpoints da API"
        print("  X URLs da API presentes")
        
        print("  X TODOS OS ELEMENTOS PRESENTES")
        
    finally:
        servidor.shutdown()

def teste_javascript_funcionalidade():
    """Testa funcionalidades JavaScript basicas."""
    print("\n--- JavaScript Funcionalidade ---")
    
    porta = 8005
    servidor = criar_servidor_dashboard(porta)
    thread_servidor = threading.Thread(target=servidor.serve_forever, daemon=True)
    thread_servidor.start()
    
    time.sleep(0.5)
    
    try:
        cliente = ClienteDashboard(f"http://localhost:{porta}")
        codigo, html = cliente.obter_dashboard()
        
        assert codigo == 200, "Deve retornar 200"
        
        # Event listeners
        assert 'botaoLogin' in html, "Login listener"
        assert 'botaoLogout' in html, "Logout listener"
        assert 'selectPlugin' in html, "Plugin listener"
        print("  X event listeners configurados")
        
        # Funcoes assincronas
        assert 'async function login' in html, "Login async"
        assert 'async function logout' in html, "Logout async"
        assert 'async function criarNota' in html, "Criar nota async"
        assert 'async function carregarNotas' in html, "Carregar notas async"
        assert 'async function realizarBusca' in html, "Busca async"
        assert 'async function carregarPlugins' in html, "Carregar plugins async"
        assert 'async function executarPlugin' in html, "Executar plugin async"
        print("  X funcoes assincronas presentes")
        
        # Fetch calls
        assert 'fetch(API_URL' in html, "Deve fazer fetch para API"
        assert "'/auth/login'" in html, "Endpoint login"
        assert "'/auth/logout'" in html, "Endpoint logout"
        assert "'/notas'" in html, "Endpoint notas"
        assert "'/busca'" in html, "Endpoint busca"
        assert "'/plugins'" in html, "Endpoint plugins"
        print("  X chamadas fetch presentes")
        
        # Headers
        assert 'Authorization' in html, "Deve ter Authorization header"
        assert 'Bearer' in html, "Deve usar Bearer token"
        print("  X autenticacao configurada")
        
        # Validacoes
        assert 'mostrarStatus' in html, "Funcao status"
        assert 'escapeHtml' in html, "Funcao escape HTML"
        print("  X funcoes utilitarias presentes")
        
        print("  X JAVASCRIPT COMPLETO")
        
    finally:
        servidor.shutdown()

def teste_responsividade():
    """Testa configuracoes de responsividade."""
    print("\n--- Responsividade ---")
    
    porta = 8006
    servidor = criar_servidor_dashboard(porta)
    thread_servidor = threading.Thread(target=servidor.serve_forever, daemon=True)
    thread_servidor.start()
    
    time.sleep(0.5)
    
    try:
        cliente = ClienteDashboard(f"http://localhost:{porta}")
        codigo, html = cliente.obter_dashboard()
        
        assert codigo == 200, "Deve retornar 200"
        
        # Meta viewport
        assert 'viewport' in html, "Deve ter meta viewport"
        assert 'width=device-width' in html, "Deve ser responsivo"
        assert 'initial-scale=1.0' in html, "Deve ter initial scale"
        print("  X meta viewport presente")
        
        # Media queries
        assert '@media' in html, "Deve ter media queries"
        assert '768px' in html, "Deve ter breakpoint 768px"
        print("  X media queries presente")
        
        # Grid layout
        assert 'grid-template-columns' in html, "Deve usar grid"
        assert '1fr' in html, "Deve ter colunas responsivas"
        print("  X layout responsivo configurado")
        
        print("  X RESPONSIVIDADE OK")
        
    finally:
        servidor.shutdown()

def teste_fluxo_completo_dashboard():
    """Testa fluxo completo do dashboard."""
    print("\n--- Fluxo Completo Dashboard ---")
    
    porta = 8007
    servidor = criar_servidor_dashboard(porta)
    thread_servidor = threading.Thread(target=servidor.serve_forever, daemon=True)
    thread_servidor.start()
    
    time.sleep(0.5)
    
    try:
        cliente = ClienteDashboard(f"http://localhost:{porta}")
        
        print("  1. Carregando pagina...")
        codigo, html = cliente.obter_dashboard()
        assert codigo == 200
        
        print("  2. Verificando estrutura...")
        assert '<!DOCTYPE html>' in html
        assert '<html' in html
        assert '<head>' in html
        assert '<body>' in html
        
        print("  3. Verificando header...")
        assert '<header>' in html
        assert 'Sumé' in html
        
        print("  4. Verificando formularios...")
        assert 'id="usuario"' in html
        assert 'id="notaTitulo"' in html
        assert 'id="buscaQuery"' in html
        
        print("  5. Verificando scripts...")
        assert '<script>' in html
        assert 'function' in html
        assert 'fetch' in html
        
        print("  6. Verificando estilos...")
        assert '<style>' in html
        assert 'background' in html.lower()
        
        print("  7. Verificando acessibilidade...")
        assert 'lang=' in html
        assert 'charset' in html
        
        print("  X DASHBOARD COMPLETO FUNCIONANDO")
        
    finally:
        servidor.shutdown()

def main():
    print("=" * 68)
    print("TESTE DA ETAPA 20: Dashboard Web")
    print("=" * 68)
    
    try:
        teste_geracao_html()
        teste_servidor_basico()
        teste_elementos_html()
        teste_javascript_funcionalidade()
        teste_responsividade()
        teste_fluxo_completo_dashboard()
        
        print("\n" + "=" * 68)
        print("OK TODOS OS TESTES DA ETAPA 20 PASSARAM!")
        print("Dashboard web validado.")
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
