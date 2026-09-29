import os
import glob
from core.router import registrar
from modulos.ia_conversacional import conversar
from utils.logger import info as log_info
from utils.resultado import Resultado
from utils import config as cfg


def buscar_notas_obsidian(query: str) -> str:
    """Busca o termo diretamente nos arquivos Markdown do Vault."""
    vault_path = cfg.get("caminho_obsidian")
    if not vault_path or not os.path.exists(vault_path):
        return "Não consegui encontrar sua pasta do Obsidian na configuração."
    
    arquivos_md = glob.glob(os.path.join(vault_path, "**", "*.md"), recursive=True)
    resultados = []
    
    # Extrai palavras chave vazadas da query. Ex: "pesquise no obsidian sobre python" -> "python"
    termos = query.lower().replace("pesquise no obsidian", "").replace("nas minhas notas", "").replace("sobre", "").replace("o que eu escrevi", "").strip().split()
    
    if not termos:
        termos = [""] # Busca vazia não acha nada específico
        
    for caminho in arquivos_md:
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                conteudo = f.read().lower()
                nome_arq = os.path.basename(caminho).replace(".md", "")
                
                # Se o nome do arquivo bater ou o conteúdo bater forte com os termos
                score = 0
                for t in termos:
                    if len(t) > 2 and t in nome_arq.lower():
                        score += 5
                    if len(t) > 3 and t in conteudo:
                        score += 1
                        
                if score > 0:
                    resultados.append((score, nome_arq, conteudo[:1000])) # Pegamos os 1000 primeiros chars para não estourar contexto
        except Exception:
            pass

    if not resultados:
        return f"Eu procurei, mas não encontrei nada mencionando isso nas suas anotações."
        
    # Ordena pelos com maior score
    resultados.sort(key=lambda x: x[0], reverse=True)
    
    # Monta um super-contexto com os 2 melhores arquivos
    texto_contexto = "Aqui estão trechos das suas anotações:\n"
    for r in resultados[:2]:
        texto_contexto += f"\n[Nota: {r[1]}]\n{r[2]}...\n"
        
    return texto_contexto

@registrar("OBSIDIAN_SEARCH")
def handle_obsidian(alvo: str, comando_original: str) -> Resultado:
        log_info("obsidian_plugin", f"Buscando notas para: {comando_original}")
        
        contexto_extraido = buscar_notas_obsidian(comando_original)
        
        if "Não consegui encontrar" in contexto_extraido or "não encontrei nada" in contexto_extraido:
            return Resultado(True, contexto_extraido)
        
        # Pede para a IA ler as notas e responder baseada nelas
        prompt = f"Baseado ÚNICA E EXCLUSIVAMENTE nas anotações a seguir, responda de forma curta ao que o usuário pediu.\n\n{contexto_extraido}\n\nPedido do usuário: '{comando_original}'"
        
        resposta_ia = conversar(prompt)
        
        return Resultado(True, resposta_ia)
