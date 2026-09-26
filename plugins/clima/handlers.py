import requests
from core.router import registrar
from modulos.ia_conversacional import conversar
from utils.logger import info as log_info
from utils.resultado import Resultado

def extrair_local(comando: str) -> str:
    """Tenta puxar a cidade do comando. Ex: 'como está o tempo em São Paulo'"""
    # heurística simples pra extrair tudo depois de "em"
    if " em " in comando:
        partes = comando.split(" em ", 1)
        if len(partes) > 1:
            return partes[1].strip().replace("?", "")
    return ""

def buscar_clima(local: str) -> str:
    """Busca dados de clima no wttr.in formatados em JSON/Texto limpo"""
    url_base = "https://wttr.in/"
    # Se nao passar local, a API tenta inferir pelo IP, o que é ótimo para o assistente da maquina!
    local_limpo = local.replace(" ", "+") if local else ""
    # Formato 3: Exibe de forma curta textual (Location: Temp, Condition) - Perfeito pro LLM ler sem formatar JSON gigante.
    url = f"{url_base}{local_limpo}?format=3"
    
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return r.text.strip()
        return "Serviço de clima indisponível."
    except Exception:
        return "Serviço de clima indisponível (Erro de Rede)."

@registrar("GET_WEATHER")
def handle_weather(alvo: str, comando_original: str) -> Resultado:
        c = comando_original.lower()
        log_info("clima_plugin", f"Verificando clima: {c}")
        
        cidade = extrair_local(c)
        
        # 1. Puxa os dados brutos de Clima textual
        clima_info = buscar_clima(cidade)
        
        if "indisponível" in clima_info:
             return Resultado(True, "Desculpe, não consegui entrar em contato com o satélite climático agora.")
          
        # 2. Pede para a IA interpretar e dizer no estilo dela
        prompt = f"O usuário perguntou sobre o clima ('{comando_original}'). O satélite retornou o seguinte dado meteorológico exato: '{clima_info}'. Mude os símbolos pra palavras se necessário e diga de forma simpática, curta e carismática pro usuário."
        
        resposta_ia = conversar(prompt)
        return Resultado(True, resposta_ia)
