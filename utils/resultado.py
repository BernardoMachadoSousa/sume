class Resultado:
    def __init__(self, sucesso: bool, mensagem: str, dados: dict = None):
        self.sucesso = sucesso
        self.mensagem = mensagem
        self.dados = dados or {}