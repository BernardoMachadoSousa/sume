"""
Servidor web para dashboard interativo do Sumé.
Interface moderna para gerenciar notas, buscar e executar plugins.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import os
import mimetypes
import json
from typing import Optional

class ServidorDashboard(BaseHTTPRequestHandler):
    """Servidor web para dashboard."""
    
    diretorio_static = None
    
    def log_message(self, format, *args):
        """Suprime logs padrao."""
        pass
    
    def do_GET(self):
        """Manipula requisicoes GET."""
        caminho = urlparse(self.path).path
        
        if caminho == '/' or caminho == '/dashboard':
            self._servir_html_dashboard()
        elif caminho == '/style.css':
            self._servir_arquivo_static('style.css', 'text/css')
        elif caminho == '/app.js':
            self._servir_arquivo_static('app.js', 'application/javascript')
        else:
            self._enviar_erro_404()
    
    def _enviar_resposta(self, codigo: int, conteudo: str, tipo_conteudo: str = 'text/html'):
        """Envia resposta HTTP."""
        self.send_response(codigo)
        self.send_header('Content-type', tipo_conteudo)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.end_headers()
        self.wfile.write(conteudo.encode() if isinstance(conteudo, str) else conteudo)
    
    def _enviar_erro_404(self):
        """Envia erro 404."""
        self._enviar_resposta(404, '<h1>404 - Arquivo nao encontrado</h1>')
    
    def _servir_arquivo_static(self, nome_arquivo: str, tipo_conteudo: str):
        """Serve arquivo estatico."""
        if self.diretorio_static and os.path.exists(os.path.join(self.diretorio_static, nome_arquivo)):
            with open(os.path.join(self.diretorio_static, nome_arquivo), 'r', encoding='utf-8') as f:
                self._enviar_resposta(200, f.read(), tipo_conteudo)
        else:
            self._enviar_erro_404()
    
    def _servir_html_dashboard(self):
        """Serve HTML do dashboard."""
        html = self._gerar_html_dashboard()
        self._enviar_resposta(200, html, 'text/html')
    
    def _gerar_html_dashboard(self) -> str:
        """Gera HTML do dashboard."""
        return '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sumé - Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        h1 { color: #667eea; }
        
        .auth-section {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        
        input[type="text"],
        input[type="password"],
        textarea,
        select {
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-family: inherit;
            font-size: 14px;
        }
        
        button {
            padding: 10px 20px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.3s;
        }
        
        button:hover { background: #5568d3; }
        button:disabled { background: #ccc; cursor: not-allowed; }
        
        .main {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        
        .card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .card h2 { color: #667eea; margin-bottom: 15px; }
        
        .form-group {
            margin-bottom: 15px;
        }
        
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: 500;
        }
        
        .notas-lista {
            max-height: 400px;
            overflow-y: auto;
        }
        
        .nota-item {
            padding: 10px;
            background: #f5f5f5;
            border-left: 4px solid #667eea;
            margin-bottom: 10px;
            border-radius: 4px;
            cursor: pointer;
            transition: background 0.2s;
        }
        
        .nota-item:hover { background: #e8e8e8; }
        
        .nota-titulo { font-weight: bold; color: #667eea; }
        .nota-preview { font-size: 12px; color: #666; margin-top: 5px; }
        .nota-data { font-size: 11px; color: #999; margin-top: 3px; }
        
        .busca-section {
            margin-bottom: 20px;
        }
        
        .resultados {
            max-height: 300px;
            overflow-y: auto;
        }
        
        .resultado-item {
            padding: 10px;
            background: #f0f4ff;
            border-radius: 4px;
            margin-bottom: 8px;
        }
        
        .plugins-lista {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }
        
        .plugin-card {
            background: #f5f5f5;
            padding: 12px;
            border-radius: 4px;
            border: 1px solid #ddd;
        }
        
        .plugin-nome { font-weight: bold; color: #667eea; }
        .plugin-versao { font-size: 12px; color: #999; }
        .plugin-status {
            display: inline-block;
            padding: 3px 8px;
            background: #4caf50;
            color: white;
            border-radius: 3px;
            font-size: 11px;
            margin-top: 5px;
        }
        
        .status-message {
            padding: 10px;
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
            border-radius: 4px;
            margin-bottom: 10px;
            display: none;
        }
        
        .status-message.show { display: block; }
        .status-message.error { background: #ffebee; border-left-color: #f44336; }
        .status-message.success { background: #e8f5e9; border-left-color: #4caf50; }
        
        @media (max-width: 768px) {
            .main { grid-template-columns: 1fr; }
            header { flex-direction: column; gap: 10px; }
            .auth-section { flex-wrap: wrap; }
        }
        
        .hidden { display: none; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📝 Sumé - Dashboard</h1>
            <div class="auth-section">
                <input type="text" id="usuario" placeholder="Usuario" value="demo">
                <input type="password" id="senha" placeholder="Senha" value="demo123">
                <button id="botaoLogin">Login</button>
                <button id="botaoLogout" class="hidden">Logout</button>
                <span id="usuarioLogado" class="hidden"></span>
            </div>
        </header>
        
        <div class="main">
            <!-- Painel de Notas -->
            <div class="card">
                <h2>📔 Notas</h2>
                <div id="statusNotas" class="status-message"></div>
                
                <div class="form-group">
                    <label for="notaTitulo">Titulo:</label>
                    <input type="text" id="notaTitulo" placeholder="Titulo da nota">
                </div>
                
                <div class="form-group">
                    <label for="notaConteudo">Conteudo:</label>
                    <textarea id="notaConteudo" placeholder="Conteudo da nota" rows="4"></textarea>
                </div>
                
                <button id="botaoCriarNota" onclick="criarNota()">Criar Nota</button>
                
                <h3 style="margin-top: 20px; color: #666;">Suas Notas:</h3>
                <div id="notasLista" class="notas-lista"></div>
            </div>
            
            <!-- Painel de Busca e Plugins -->
            <div class="card">
                <h2>🔍 Busca e Ferramentas</h2>
                <div id="statusBusca" class="status-message"></div>
                
                <div class="busca-section">
                    <div class="form-group">
                        <label for="buscaQuery">Buscar em notas:</label>
                        <input type="text" id="buscaQuery" placeholder="Digite para buscar...">
                    </div>
                    <button onclick="realizarBusca()">Buscar</button>
                </div>
                
                <div id="resultados" class="resultados"></div>
                
                <h3 style="margin-top: 20px; color: #666;">Plugins Disponiveis:</h3>
                <div id="pluginsLista" class="plugins-lista"></div>
                
                <div style="margin-top: 20px;">
                    <h4>Executar Plugin:</h4>
                    <div class="form-group">
                        <select id="selectPlugin">
                            <option value="">Selecione um plugin</option>
                            <option value="processador">Processador de Texto</option>
                            <option value="analise">Analise de Sentimento</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <select id="selectComando">
                            <option value="">Selecione um comando</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <textarea id="parametrosPlugin" placeholder="Parametros (JSON)" rows="3"></textarea>
                    </div>
                    <button onclick="executarPlugin()">Executar</button>
                </div>
                
                <div id="statusPlugin" class="status-message" style="margin-top: 10px;"></div>
            </div>
        </div>
    </div>
    
    <script>
        const API_URL = 'http://localhost:8000/api';
        let token = null;
        
        // Event listeners
        document.getElementById('botaoLogin').onclick = login;
        document.getElementById('botaoLogout').onclick = logout;
        document.getElementById('selectPlugin').onchange = atualizarComandos;
        document.getElementById('buscaQuery').onkeyup = (e) => {
            if (e.key === 'Enter') realizarBusca();
        };
        
        async function login() {
            const usuario = document.getElementById('usuario').value;
            const senha = document.getElementById('senha').value;
            
            try {
                const resposta = await fetch(API_URL + '/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ usuario, senha })
                });
                
                const dados = await resposta.json();
                if (resposta.ok) {
                    token = dados.token;
                    document.getElementById('botaoLogin').classList.add('hidden');
                    document.getElementById('botaoLogout').classList.remove('hidden');
                    document.getElementById('usuarioLogado').textContent = usuario;
                    document.getElementById('usuarioLogado').classList.remove('hidden');
                    mostrarStatus('statusNotas', 'Login realizado com sucesso!', 'success');
                    carregarNotas();
                    carregarPlugins();
                } else {
                    mostrarStatus('statusNotas', dados.erro || 'Erro no login', 'error');
                }
            } catch (erro) {
                mostrarStatus('statusNotas', 'Erro ao conectar com servidor', 'error');
            }
        }
        
        async function logout() {
            try {
                await fetch(API_URL + '/auth/logout', {
                    method: 'POST',
                    headers: { 'Authorization': 'Bearer ' + token }
                });
            } catch (e) {}
            
            token = null;
            document.getElementById('botaoLogin').classList.remove('hidden');
            document.getElementById('botaoLogout').classList.add('hidden');
            document.getElementById('usuarioLogado').classList.add('hidden');
            document.getElementById('notasLista').innerHTML = '';
            mostrarStatus('statusNotas', 'Logout realizado', 'success');
        }
        
        async function criarNota() {
            if (!token) {
                mostrarStatus('statusNotas', 'Faca login primeiro', 'error');
                return;
            }
            
            const titulo = document.getElementById('notaTitulo').value;
            const conteudo = document.getElementById('notaConteudo').value;
            
            if (!titulo || !conteudo) {
                mostrarStatus('statusNotas', 'Preencha titulo e conteudo', 'error');
                return;
            }
            
            try {
                const resposta = await fetch(API_URL + '/notas', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + token
                    },
                    body: JSON.stringify({ titulo, conteudo })
                });
                
                if (resposta.ok) {
                    document.getElementById('notaTitulo').value = '';
                    document.getElementById('notaConteudo').value = '';
                    mostrarStatus('statusNotas', 'Nota criada com sucesso!', 'success');
                    carregarNotas();
                } else {
                    mostrarStatus('statusNotas', 'Erro ao criar nota', 'error');
                }
            } catch (erro) {
                mostrarStatus('statusNotas', 'Erro ao conectar', 'error');
            }
        }
        
        async function carregarNotas() {
            if (!token) return;
            
            try {
                const resposta = await fetch(API_URL + '/notas', {
                    headers: { 'Authorization': 'Bearer ' + token }
                });
                
                const dados = await resposta.json();
                const lista = document.getElementById('notasLista');
                
                if (dados.notas && dados.notas.length > 0) {
                    lista.innerHTML = dados.notas.map(nota => `
                        <div class="nota-item">
                            <div class="nota-titulo">${escapeHtml(nota.titulo)}</div>
                            <div class="nota-preview">${escapeHtml(nota.conteudo.substring(0, 50))}...</div>
                            <div class="nota-data">${new Date(nota.criada_em).toLocaleDateString('pt-BR')}</div>
                        </div>
                    `).join('');
                } else {
                    lista.innerHTML = '<p style="color: #999;">Nenhuma nota ainda</p>';
                }
            } catch (erro) {
                console.error('Erro ao carregar notas', erro);
            }
        }
        
        async function realizarBusca() {
            if (!token) {
                mostrarStatus('statusBusca', 'Faca login primeiro', 'error');
                return;
            }
            
            const query = document.getElementById('buscaQuery').value;
            if (!query) {
                mostrarStatus('statusBusca', 'Digite algo para buscar', 'error');
                return;
            }
            
            try {
                const resposta = await fetch(API_URL + '/busca', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + token
                    },
                    body: JSON.stringify({ query })
                });
                
                const dados = await resposta.json();
                const resultados = document.getElementById('resultados');
                
                if (dados.resultados && dados.resultados.length > 0) {
                    resultados.innerHTML = dados.resultados.map(r => `
                        <div class="resultado-item">
                            <strong>${escapeHtml(r.titulo)}</strong>
                            <p>${escapeHtml(r.conteudo)}</p>
                        </div>
                    `).join('');
                    mostrarStatus('statusBusca', 'Encontrados ' + dados.total + ' resultados', 'success');
                } else {
                    resultados.innerHTML = '<p style="color: #999;">Nenhum resultado encontrado</p>';
                    mostrarStatus('statusBusca', 'Nenhum resultado encontrado', 'error');
                }
            } catch (erro) {
                mostrarStatus('statusBusca', 'Erro ao buscar', 'error');
            }
        }
        
        async function carregarPlugins() {
            if (!token) return;
            
            try {
                const resposta = await fetch(API_URL + '/plugins', {
                    headers: { 'Authorization': 'Bearer ' + token }
                });
                
                const dados = await resposta.json();
                const lista = document.getElementById('pluginsLista');
                
                if (dados.plugins && dados.plugins.length > 0) {
                    lista.innerHTML = dados.plugins.map(plugin => `
                        <div class="plugin-card">
                            <div class="plugin-nome">${plugin.nome}</div>
                            <div class="plugin-versao">v${plugin.versao}</div>
                            <div class="plugin-status">${plugin.ativado ? 'Ativo' : 'Inativo'}</div>
                        </div>
                    `).join('');
                } else {
                    lista.innerHTML = '<p style="color: #999;">Nenhum plugin disponivel</p>';
                }
            } catch (erro) {
                console.error('Erro ao carregar plugins', erro);
            }
        }
        
        function atualizarComandos() {
            const plugin = document.getElementById('selectPlugin').value;
            const comandos = {
                'processador': ['processar_texto', 'extrair_palavras'],
                'analise': ['analisar_sentimento', 'contar_entidades']
            };
            
            const selectComando = document.getElementById('selectComando');
            selectComando.innerHTML = '<option value="">Selecione um comando</option>';
            
            if (plugin in comandos) {
                comandos[plugin].forEach(cmd => {
                    const option = document.createElement('option');
                    option.value = cmd;
                    option.textContent = cmd.replace(/_/g, ' ');
                    selectComando.appendChild(option);
                });
            }
        }
        
        async function executarPlugin() {
            if (!token) {
                mostrarStatus('statusPlugin', 'Faca login primeiro', 'error');
                return;
            }
            
            const plugin = document.getElementById('selectPlugin').value;
            const comando = document.getElementById('selectComando').value;
            
            if (!plugin || !comando) {
                mostrarStatus('statusPlugin', 'Selecione plugin e comando', 'error');
                return;
            }
            
            try {
                let parametros = {};
                const parametrosStr = document.getElementById('parametrosPlugin').value;
                
                if (parametrosStr) {
                    parametros = JSON.parse(parametrosStr);
                }
                
                const resposta = await fetch(API_URL + '/plugins/executar', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + token
                    },
                    body: JSON.stringify({ plugin, comando, parametros })
                });
                
                const dados = await resposta.json();
                
                if (resposta.ok) {
                    mostrarStatus('statusPlugin', 'Resultado: ' + JSON.stringify(dados.resultado), 'success');
                } else {
                    mostrarStatus('statusPlugin', 'Erro ao executar plugin', 'error');
                }
            } catch (erro) {
                mostrarStatus('statusPlugin', 'Erro: ' + erro.message, 'error');
            }
        }
        
        function mostrarStatus(elementoId, mensagem, tipo) {
            const el = document.getElementById(elementoId);
            el.textContent = mensagem;
            el.className = 'status-message show ' + tipo;
            
            if (tipo === 'success') {
                setTimeout(() => el.classList.remove('show'), 3000);
            }
        }
        
        function escapeHtml(texto) {
            const map = {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#039;'
            };
            return texto.replace(/[&<>"']/g, m => map[m]);
        }
    </script>
</body>
</html>'''

def criar_servidor_dashboard(porta: int = 8080):
    """Cria servidor do dashboard."""
    servidor = HTTPServer(('localhost', porta), ServidorDashboard)
    return servidor

def iniciar_dashboard(porta: int = 8080):
    """Inicia dashboard."""
    servidor = criar_servidor_dashboard(porta)
    print(f"Dashboard iniciado em http://localhost:{porta}")
    print("Pressione Ctrl+C para interromper")
    
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard finalizado")
        servidor.shutdown()
