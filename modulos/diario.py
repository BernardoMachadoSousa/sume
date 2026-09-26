"""
Diário do Sumé - Notas diárias automáticas no formato Markdown.

Cada dia recebe seu próprio arquivo no vault (YYYY-MM-DD.md) para registro
de eventos, aprendizados rápidos e anotacoes do dia.
"""

import os
from datetime import date
from modulos.vault import salvar, ler, listar, apagar
from utils.logger import info as log_info, erro as log_erro

DIARIO_PREFIX = "diario_"  # Prefixo opcional para evitar colisões com notas manuais


def _hoje_str() -> str:
    """Retorna a data atual no formato YYYY-MM-DD."""
    return date.today().isoformat()


def garantir_diario_hoje() -> str:
    """
    Garante que existe uma nota de diario para hoje e retorna seu caminho.
    Cria a nota vazia se necessário.
    """
    hoje_str = _hoje_str()
    titulo = f"{DIARIO_PREFIX}{hoje_str}"
    
    # Verifica se já existe
    existente = ler(titulo)
    if existente is not None:
        # Já existe, retorna o caminho
        caminho = os.path.join("dados", "vault", f"{titulo.replace(' ', '-').lower()}.md")
        return caminho
    
    # Cria nova nota de diario vazia para hoje
    corpo_inicial = f"# Diário de {hoje_str}\n\n---\n*Iniciado automaticamente pelo Sumé*\n\n"
    caminho = salvar(titulo, corpo_inicial, tags=["diario", "automatico"])
    log_info("diario", f"Criado diario para {hoje_str}: {caminho}")
    return caminho


def anotar_no_diario(texto: str) -> str:
    """
    Anexa um texto ao diario de hoje.
    Retorna mensagem de sucesso ou erro.
    """
    try:
        hoje_str = _hoje_str()
        titulo = f"{DIARIO_PREFIX}{hoje_str}"
        existente = ler(titulo) or ""
        # Avoid double newline if existente is empty
        if existente and not existente.endswith('\n'):
            existente += '\n'
        novo_corpo = existente + texto
        caminho = salvar(titulo, novo_corpo, tags=["diario", "automatico"])
        if caminho:
            return f"Anotado no diario de hoje."
        return "Falha ao atualizar o diario."
    except Exception as e:
        log_erro("diario", str(e))
        return "Erro ao anotar no diario."


def ler_diario_hoje() -> str | None:
    """Retorna o conteúdo completo do diario de hoje (sem frontmatter)."""
    titulo = f"{DIARIO_PREFIX}{_hoje_str()}"
    return ler(titulo)


def listar_diarios(limite: int = 7) -> list[dict]:
    """
    Lista os diarios mais recentes (padrão: últimos 7 dias).
    Returns list of note dicts from vault.listar() filtered by diario prefix.
    """
    try:
        todas = listar()
        diarios_com_data = []
        for nota in todas:
            if nota["titulo"].startswith(DIARIO_PREFIX):
                # Extrai a data do titulo para ordenacao
                data_str = nota["titulo"][len(DIARIO_PREFIX):]
                try:
                    # Valida se é uma data válida
                    date_obj = date.fromisoformat(data_str)
                    diarios_com_data.append((date_obj, nota))
                except ValueError:
                    # Não é uma data válida, pula
                    continue
        
        # Ordena por data (mais recente primeiro)
        diarios_com_data.sort(key=lambda x: x[0], reverse=True)
        # Extrai apenas as notas, descartando as datas usadas para ordenacao
        diarios = [nota for _, nota in diarios_com_data]
        return diarios[:limite]
    except Exception as e:
        log_erro("diario", str(e))
        return []


def apagar_diario(data_str: str) -> bool:
    """
    Apaga o diario de uma data específica (formato YYYY-MM-DD).
    Retorna True se apagou, False se não encontrou ou erro.
    """
    try:
        # Valida formato
        date.fromisoformat(data_str)
        titulo = f"{DIARIO_PREFIX}{data_str}"
        return apagar(titulo)
    except ValueError:
        return False
    except Exception as e:
        log_erro("diario", str(e))
        return False


# Teste rápido
if __name__ == "__main__":
    # Teste básico
    print("Hoje é:", _hoje_str())
    print("Caminho diario:", os.path.join("dados", "vault", f"diario_{_hoje_str().replace(' ', '-').lower()}.md"))
    print("Garantindo diario de hoje:", garantir_diario_hoje())
    print("Anotando no diario:", anotar_no_diario("Teste de anotacao automática"))
    print("Lendo diario de hoje:")
    conteudo = ler_diario_hoje()
    print(conteudo if conteudo else "Vazio")
    print("Diarios recentes:")
    for d in listar_diarios(3):
        print(f"  - {d['titulo']}: {d['caminho']}")