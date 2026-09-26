"""
API REST para integracao externa com Sumé.
Fornece endpoints para busca, notas, vault e plugins.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import hashlib
import hmac
import secrets
import time
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import base64

class AutenticadorJWT:
    """Gerenciador de tokens JWT simples."""
    
    def __init__(self, chave_secreta: str):
        self.chave_secreta = chave_secreta.encode()
        self.tokens_validos = {}
    
    def gerar_token(self, usuario_id: str, expiracao_horas: int = 24) -> str:
        """Gera token JWT para usuario."""
        agora = time.time()
        expira_em = agora + (expiracao_horas * 3600)
        
        payload = {
            "usuario_id": usuario_id,
            "iat": agora,
            "exp": expira_em
        }
        
        payload_json = json.dumps(payload, separators=(',', ':'))
        payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode().rstrip('=')
        
        header = {"typ": "JWT", "alg": "HS256"}
        header_json = json.dumps(header, separators=(',', ':'))
        header_b64 = base64.urlsafe_b64encode(header_json.encode()).decode().rstrip('=')
        
        assinatura = hmac.new(
            self.chave_secreta,
            f"{header_b64}.{payload_b64}".encode(),
            hashlib.sha256
        ).digest()
        assinatura_b64 = base64.urlsafe_b64encode(assinatura).decode().rstrip('=')
        
        token = f"{header_b64}.{payload_b64}.{assinatura_b64}"
        
        self.tokens_validos[token] = {
            "usuario_id": usuario_id,
            "expira_em": expira_em
        }
        
        return token
    
    def validar_token(self, token: str) -> Tuple[bool, Optional[str]]:
        """Valida token e retorna (valido, usuario_id)."""
        try:
            if token not in self.tokens_validos:
                return False, None
            
            info = self.tokens_validos[token]
            if time.time() > info["expira_em"]:
                del self.tokens_validos[token]
                return False, None
            
            return True, info["usuario_id"]
        except:
            return False, None
    
    def revogar_token(self, token: str):
        """Revoga token (logout)."""
        if token in self.tokens_validos:
            del self.tokens_validos[token]

class GerenciadorSessoes:
    """Gerencia sessoes de usuarios."""
    
    def __init__(self):
        self.sessoes = {}
        self.usuarios = {
            "demo": {
                "senha_hash": hashlib.sha256("demo123".encode()).hexdigest(),
                "nome": "Usuario Demo"
            }
        }
    
    def autenticar(self, usuario: str, senha: str) -> bool:
        """Autentica usuario."""
        if usuario not in self.usuarios:
            return False
        
        senha_hash = hashlib.sha256(senha.encode()).hexdigest()
        return self.usuarios[usuario]["senha_hash"] == senha_hash
    
    def criar_sessao(self, usuario: str) -> str:
        """Cria sessao para usuario."""
        sessao_id = secrets.token_urlsafe(32)
        self.sessoes[sessao_id] = {
            "usuario": usuario,
            "criada_em": datetime.now().isoformat(),
            "ultima_atividade": datetime.now().isoformat()
        }
        return sessao_id
    
    def obter_sessao(self, sessao_id: str) -> Optional[Dict]:
        """Obtem informacoes da sessao."""
        return self.sessoes.get(sessao_id)
    
    def encerrar_sessao(self, sessao_id: str):
        """Encerra sessao."""
        if sessao_id in self.sessoes:
            del self.sessoes[sessao_id]

class ManipuladorAPIREST(BaseHTTPRequestHandler):
    """Manipulador de requisicoes HTTP para API REST."""
    
    autenticador = None
    gerenciador_sessoes = None
    dados_mock = {}
    
    def log_message(self, format, *args):
        """Suprime logs padrao do servidor."""
        pass
    
    def _enviar_resposta(self, codigo: int, dados: Any):
        """Envia resposta JSON."""
        self.send_response(codigo)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        resposta = json.dumps(dados, ensure_ascii=False)
        self.wfile.write(resposta.encode())
    
    def _enviar_erro(self, codigo: int, mensagem: str):
        """Envia erro JSON."""
        self._enviar_resposta(codigo, {"erro": mensagem})
    
    def _extrair_token(self) -> Optional[str]:
        """Extrai token Bearer do header."""
        auth = self.headers.get('Authorization', '')
        if auth.startswith('Bearer '):
            return auth[7:]
        return None
    
    def _validar_autenticacao(self) -> Tuple[bool, Optional[str]]:
        """Valida autenticacao do token."""
        token = self._extrair_token()
        if not token:
            return False, None
        
        valido, usuario_id = self.autenticador.validar_token(token)
        return valido, usuario_id
    
    def _ler_corpo(self) -> Dict:
        """Le e parseia corpo JSON da requisicao."""
        try:
            tamanho = int(self.headers.get('Content-Length', 0))
            corpo = self.rfile.read(tamanho).decode()
            return json.loads(corpo) if corpo else {}
        except:
            return {}
    
    def do_OPTIONS(self):
        """Responde para requisicoes OPTIONS (CORS)."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def do_POST(self):
        """Manipula requisicoes POST."""
        caminho = urlparse(self.path).path
        
        if caminho == '/api/auth/login':
            self._handle_login()
        elif caminho == '/api/auth/logout':
            self._handle_logout()
        elif caminho == '/api/notas':
            self._handle_criar_nota()
        elif caminho == '/api/busca':
            self._handle_busca()
        elif caminho == '/api/plugins/executar':
            self._handle_executar_plugin()
        else:
            self._enviar_erro(404, "Endpoint nao encontrado")
    
    def do_GET(self):
        """Manipula requisicoes GET."""
        caminho = urlparse(self.path).path
        
        if caminho == '/api/status':
            self._handle_status()
        elif caminho == '/api/notas':
            self._handle_listar_notas()
        elif caminho == '/api/plugins':
            self._handle_listar_plugins()
        elif caminho == '/api/autenticacao/validar':
            self._handle_validar_token()
        else:
            self._enviar_erro(404, "Endpoint nao encontrado")
    
    def do_PUT(self):
        """Manipula requisicoes PUT."""
        caminho = urlparse(self.path).path
        
        if caminho.startswith('/api/notas/'):
            self._handle_atualizar_nota()
        else:
            self._enviar_erro(404, "Endpoint nao encontrado")
    
    def do_DELETE(self):
        """Manipula requisicoes DELETE."""
        caminho = urlparse(self.path).path
        
        if caminho.startswith('/api/notas/'):
            self._handle_deletar_nota()
        else:
            self._enviar_erro(404, "Endpoint nao encontrado")
    
    def _handle_status(self):
        """GET /api/status - Retorna status do servidor."""
        self._enviar_resposta(200, {
            "status": "ok",
            "versao": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "usuarios_ativos": len(self.gerenciador_sessoes.sessoes)
        })
    
    def _handle_login(self):
        """POST /api/auth/login - Autentica usuario."""
        corpo = self._ler_corpo()
        usuario = corpo.get("usuario")
        senha = corpo.get("senha")
        
        if not usuario or not senha:
            self._enviar_erro(400, "Usuario e senha obrigatorios")
            return
        
        if not self.gerenciador_sessoes.autenticar(usuario, senha):
            self._enviar_erro(401, "Usuario ou senha invalidos")
            return
        
        token = self.autenticador.gerar_token(usuario)
        self._enviar_resposta(200, {
            "sucesso": True,
            "token": token,
            "expira_em": 86400
        })
    
    def _handle_logout(self):
        """POST /api/auth/logout - Finaliza sessao."""
        valido, usuario_id = self._validar_autenticacao()
        if not valido:
            self._enviar_erro(401, "Token invalido")
            return
        
        token = self._extrair_token()
        self.autenticador.revogar_token(token)
        self._enviar_resposta(200, {"sucesso": True})
    
    def _handle_validar_token(self):
        """GET /api/autenticacao/validar - Valida token."""
        valido, usuario_id = self._validar_autenticacao()
        if not valido:
            self._enviar_erro(401, "Token invalido ou expirado")
            return
        
        self._enviar_resposta(200, {
            "valido": True,
            "usuario_id": usuario_id
        })
    
    def _handle_criar_nota(self):
        """POST /api/notas - Cria nova nota."""
        valido, usuario_id = self._validar_autenticacao()
        if not valido:
            self._enviar_erro(401, "Nao autenticado")
            return
        
        corpo = self._ler_corpo()
        titulo = corpo.get("titulo", "Sem titulo")
        conteudo = corpo.get("conteudo", "")
        
        nota_id = hashlib.md5(f"{usuario_id}{titulo}{time.time()}".encode()).hexdigest()[:12]
        
        if usuario_id not in self.dados_mock:
            self.dados_mock[usuario_id] = {"notas": []}
        
        nota = {
            "id": nota_id,
            "titulo": titulo,
            "conteudo": conteudo,
            "criada_em": datetime.now().isoformat(),
            "usuario_id": usuario_id
        }
        
        self.dados_mock[usuario_id]["notas"].append(nota)
        
        self._enviar_resposta(201, {
            "sucesso": True,
            "nota_id": nota_id,
            "nota": nota
        })
    
    def _handle_listar_notas(self):
        """GET /api/notas - Lista notas do usuario."""
        valido, usuario_id = self._validar_autenticacao()
        if not valido:
            self._enviar_erro(401, "Nao autenticado")
            return
        
        notas = self.dados_mock.get(usuario_id, {}).get("notas", [])
        self._enviar_resposta(200, {
            "total": len(notas),
            "notas": notas
        })
    
    def _handle_atualizar_nota(self):
        """PUT /api/notas/{id} - Atualiza nota."""
        valido, usuario_id = self._validar_autenticacao()
        if not valido:
            self._enviar_erro(401, "Nao autenticado")
            return
        
        nota_id = self.path.split('/')[-1]
        corpo = self._ler_corpo()
        
        if usuario_id not in self.dados_mock:
            self._enviar_erro(404, "Nota nao encontrada")
            return
        
        notas = self.dados_mock[usuario_id]["notas"]
        for nota in notas:
            if nota["id"] == nota_id:
                nota["titulo"] = corpo.get("titulo", nota["titulo"])
                nota["conteudo"] = corpo.get("conteudo", nota["conteudo"])
                nota["atualizada_em"] = datetime.now().isoformat()
                self._enviar_resposta(200, {"sucesso": True, "nota": nota})
                return
        
        self._enviar_erro(404, "Nota nao encontrada")
    
    def _handle_deletar_nota(self):
        """DELETE /api/notas/{id} - Deleta nota."""
        valido, usuario_id = self._validar_autenticacao()
        if not valido:
            self._enviar_erro(401, "Nao autenticado")
            return
        
        nota_id = self.path.split('/')[-1]
        
        if usuario_id not in self.dados_mock:
            self._enviar_erro(404, "Nota nao encontrada")
            return
        
        notas = self.dados_mock[usuario_id]["notas"]
        for i, nota in enumerate(notas):
            if nota["id"] == nota_id:
                notas.pop(i)
                self._enviar_resposta(200, {"sucesso": True})
                return
        
        self._enviar_erro(404, "Nota nao encontrada")
    
    def _handle_busca(self):
        """POST /api/busca - Realiza busca."""
        valido, usuario_id = self._validar_autenticacao()
        if not valido:
            self._enviar_erro(401, "Nao autenticado")
            return
        
        corpo = self._ler_corpo()
        query = corpo.get("query", "")
        
        if usuario_id not in self.dados_mock:
            self._enviar_resposta(200, {"resultados": []})
            return
        
        notas = self.dados_mock[usuario_id]["notas"]
        resultados = [
            n for n in notas
            if query.lower() in n["titulo"].lower() or query.lower() in n["conteudo"].lower()
        ]
        
        self._enviar_resposta(200, {
            "query": query,
            "total": len(resultados),
            "resultados": resultados
        })
    
    def _handle_listar_plugins(self):
        """GET /api/plugins - Lista plugins disponiveis."""
        valido, usuario_id = self._validar_autenticacao()
        if not valido:
            self._enviar_erro(401, "Nao autenticado")
            return
        
        self._enviar_resposta(200, {
            "plugins": [
                {"nome": "processador", "versao": "1.0.0", "ativado": True},
                {"nome": "analise", "versao": "1.0.0", "ativado": True}
            ]
        })
    
    def _handle_executar_plugin(self):
        """POST /api/plugins/executar - Executa plugin."""
        valido, usuario_id = self._validar_autenticacao()
        if not valido:
            self._enviar_erro(401, "Nao autenticado")
            return
        
        corpo = self._ler_corpo()
        plugin = corpo.get("plugin", "")
        comando = corpo.get("comando", "")
        parametros = corpo.get("parametros", {})
        
        if plugin == "processador" and comando == "processar_texto":
            texto = parametros.get("texto", "")
            resultado = {
                "comprimento": len(texto),
                "palavras": len(texto.split())
            }
            self._enviar_resposta(200, {"sucesso": True, "resultado": resultado})
        elif plugin == "analise" and comando == "analisar_sentimento":
            texto = parametros.get("texto", "")
            positivo = len([p for p in ["bom", "otimo"] if p in texto.lower()])
            sentimento = "positivo" if positivo > 0 else "neutro"
            self._enviar_resposta(200, {"sucesso": True, "resultado": {"sentimento": sentimento}})
        else:
            self._enviar_erro(400, "Plugin ou comando invalido")

def criar_servidor_rest(porta: int = 8000, chave_secreta: str = None) -> HTTPServer:
    """Cria servidor REST."""
    if chave_secreta is None:
        chave_secreta = secrets.token_urlsafe(32)
    
    ManipuladorAPIREST.autenticador = AutenticadorJWT(chave_secreta)
    ManipuladorAPIREST.gerenciador_sessoes = GerenciadorSessoes()
    
    servidor = HTTPServer(('localhost', porta), ManipuladorAPIREST)
    return servidor

def iniciar_servidor(porta: int = 8000, chave_secreta: str = None):
    """Inicia servidor REST."""
    servidor = criar_servidor_rest(porta, chave_secreta)
    print(f"Servidor REST iniciado em http://localhost:{porta}")
    print("Pressione Ctrl+C para interromper")
    
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor finalizado")
        servidor.shutdown()
