import requests
import re
from core.router import registrar
from modulos.ia_conversacional import conversar
from utils.logger import info as log_info
from utils.resultado import Resultado

def limpar_busca(comando: str) -> str:
    """Tira as palavras de ação para pesquisar apenas o núcleo."""
    remover = ["pesquise na internet", "busque na internet", "procure na web", "sobre", "pesquise", "pesquisar"]
    for r in remover:
        comando = comando.replace(r, "")
    return comando.strip()

def buscar_duckduckgo(query: str) -> str:
    url = "https://html.duckduckgo.com/html/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    data = {"q": query}
    try:
        r = requests.post(url, headers=headers, data=data, timeout=10)
        matches = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', r.text, flags=re.IGNORECASE | re.DOTALL)
        
        snippets = []
        for match in matches:
            # Limpa tags HTML
            clean_text = re.sub(r'<[^>]+>', '', match)
            # Des-escapsa entidades comuns
            clean_text = clean_text.replace('&#39;', "'").replace('&quot;', '"').replace('&amp;', '&')
            snippets.append(clean_text)
            if len(snippets) >= 4:
                break
                
        if not snippets:
            return ""
            
        return "\n".join(snippets)
    except Exception as e:
        log_info("websearch", f"Erro na rede: {e}")
        return ""

@registrar("WEB_SEARCH")
def handle_websearch(alvo: str, comando_original: str) -> Resultado:
        chave_de_pesquisa = limpar_busca(comando_original)
        
        if not chave_de_pesquisa:
            chave_de_pesquisa = comando_original # se limpou tudo, vai tudo
            
        log_info("websearch", f"Procurando na internet por: {chave_de_pesquisa}")
        
        # Faz o Scraping
        contexto_web = buscar_duckduckgo(chave_de_pesquisa)
        
        if not contexto_web:
            return Resultado(True, "Desculpe, tive um problema de comunicação com os motores de busca e não pude encontrar isso na internet agora.")
        
        # Alimenta a IA com as verdades em tempo real e colhe a síntese
        prompt = f"Baseado nas seguintes informações extraídas agora da internet (Motor de busca), responda de forma CURTA a dúvida do usuário.\n\n=== RESULTADOS DA WEB ===\n{contexto_web}\n==================\n\nComando do usuário: '{comando_original}'"
        
        resposta_ia = conversar(prompt)
        
        return Resultado(True, resposta_ia)
