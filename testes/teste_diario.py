#!/usr/bin/env python3
"""
Teste do sistema de diario do Sumé.
"""

import os
import sys
import tempfile
import shutil
from datetime import date, timedelta

# Define o diretório raiz do projeto (um nível acima deste script)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Muda o diretório de trabalho atual para a raiz do projeto para garantir
# que os caminhos relativos (como "dados/vault") funcionem corretamente.
original_cwd = os.getcwd()
os.chdir(PROJECT_ROOT)

# Adiciona o diretório raiz ao path para imports (já estamos nele, mas garantimos)
sys.path.insert(0, PROJECT_ROOT)

def test_diario_basico():
    """Testa funcionalidade básica do diario."""
    print("=== Teste Básico do Diario ===")
    
    # Backup do diretório de dados atual
    dados_backup = None
    if os.path.exists("dados"):
        dados_backup = "dados_backup"
        if os.path.exists(dados_backup):
            shutil.rmtree(dados_backup)
        shutil.copytree("dados", dados_backup)
    
    try:
        # Limpa o diretório de dados para teste limpo
        if os.path.exists("dados"):
            shutil.rmtree("dados")
        os.makedirs("dados/vault", exist_ok=True)
        
        # Importa os módulos após garantir que o diretório existe
        from modulos.diario import (
            _hoje_str, garantir_diario_hoje, anotar_no_diario, 
            ler_diario_hoje, listar_diarios, apagar_diario
        )
        from modulos.vault import ler, salvar
        
        hoje = _hoje_str()
        # # # # print(f"Data de hoje: {hoje}")
        
        # Testa garantia do diario de hoje
        caminho = garantir_diario_hoje()
        # print(f"Caminho do diario de hoje: {caminho}")
        assert os.path.exists(caminho), "Diario de hoje deve existir"
        
# Testa anotacao no diario
        resultado = anotar_no_diario("Primeira anotacao de teste")
        assert "Anotado no diario" in resultado, "Deve indicar sucesso na anotacao"
        
        # Testa leitura do diario
        conteudo = ler_diario_hoje()
        assert conteudo is not None, "Conteudo do diario nao deve ser None"
        assert "Primeira anotacao de teste" in conteudo, "Anotacao deve estar no conteudo"
        
        # Testa segunda anotacao
        resultado2 = anotar_no_diario("\nSegunda anotacao de teste")
        # # # print(f"Resultado da segunda anotacao: {resultado2}")
        assert "Anotado no diario" in resultado2, "Segunda anotacao deve funcionar"
        
conteudo2 = ler_diario_hoje()
        # print(f"Conteudo apos segunda anotacao:\n{conteudo2}")
        assert "Primeira anotacao de teste" in conteudo2, "Primeira anotacao deve permanecer"
        assert "Segunda anotacao de teste" in conteudo2, "Segunda anotacao deve estar presente"
        
        # Testa listagem de diarios
        diarios = listar_diarios(5)
        # print(f"Diarios encontrados: {len(diarios)}")
        assert len(diarios) >= 1, "Deve ter pelo menos o diario de hoje"
        assert diarios[0]["titulo"].startswith("diario_"), "Primeiro deve ser um diario"
        
        # Testa apagamento de diario (com data de amanha para nao afetar hoje)
        amanha = (date.today() + timedelta(days=1)).isoformat()
        resultado_amanha = garantir_diario_hoje()  # Garante que hoje existe
        # Cria um diario de amanha propositalmente para teste
        from modulos.vault import salvar
        titulo_amanha = f"diario_{amanha}"
        corpo_amanha = f"---\n# Diario de {amanha}\n\nTeste de diario futuro\n---\n"
        caminho_amanha = salvar(titulo_amanha, corpo_amanha, tags=["diario", "automatico"])
        
        # Testa funcao de apagamento
        from modulos.vault import _caminho
# print(f"Tentando apagar diario para data: {amanha}")
# print(f"caminho_amanha (manual): {caminho_amanha}")
# print(f"os.path.exists(caminho_amanha) before: {os.path.exists(caminho_amanha)}")
# print(f"_caminho result: {caminho_do_titulo}")
# print(f"os.path.exists(caminho_do_titulo) before: {os.path.exists(caminho_do_titulo)}")
        resultado_apagar = apagar_diario(amanha)
resultado_apagar = apagar_diario(amanha)
# print(f"Resultado do apagamento do diario de amanha: {resultado_apagar}")
# print(f"os.path.exists(caminho_amanha) after: {os.path.exists(caminho_amanha)}")
# print(f"os.path.exists(caminho_do_titulo) after: {os.path.exists(caminho_do_titulo)}")
        assert resultado_apagar, "Deve conseguir apagar o diario de amanha"
        assert not os.path.exists(caminho_amanha), "Arquivo do diario de amanha deve ter sido removido"
        
        print("[OK] Todos os testes do diario passaram!")
        return True
        
    except Exception as e:
        print(f"ERRO nos testes: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Restaura backup se existir
        if dados_backup and os.path.exists(dados_backup):
            if os.path.exists("dados"):
                shutil.rmtree("dados")
            shutil.move(dados_backup, "dados")
        elif os.path.exists("dados"):
            # Se nao tinha backup mas criou dados de teste, remove
            shutil.rmtree("dados")

if __name__ == "__main__":
    success = test_diario_basico()
    sys.exit(0 if success else 1)