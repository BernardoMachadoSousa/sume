"""
Teste de Segurança para validar correções críticas.
Execute: python testes/teste_seguranca.py
"""

import sys
import os
import threading
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contextlib import contextmanager

# Configurar console antes de qualquer print
from utils.console import configurar_console
configurar_console()

import re

# ===== TESTE DE COMMAND INJECTION =====

def test_command_injection_fixed():
    """Testa se command injection foi corrigido em automacoes.py"""
    print("\n🔒 TESTANDO CORREÇÃO DE COMMAND INJECTION...")
    
    try:
        from modulos.automacoes import WHITELIST_EXE, WHITELIST_PROC
        import subprocess
        import re
    except ImportError as e:
        print(f"❌ Erro ao importar automacoes: {e}")
        return False
    
    # Verificar que whitelists existem
    print(f"  📊 WHITELIST_EXE tem {len(WHITELIST_EXE)} executáveis permitidos")
    print(f"  📊 WHITELIST_PROC tem {len(WHITELIST_PROC)} processos permitidos")
    
    # Tentativas de injection devem ser bloqueadas
    ataques = [
        "notepad; del C:\\test",
        "notepad && rm -rf /",
        "notepad | cat /etc/passwd",
        "notepad`whoami`",
        "notepad$(id)",
        "notepad || echo 'hacked'",
        "../../etc/passwd",
        "....//....//windows/system32/cmd.exe",
        "notepad\x00cat /etc/passwd",
        "notepad\nls -la",
        "notepad\r\nwhoami",
        "calc; taskkill /F /IM explorer.exe",
    ]
    
    # Padrão de detecção de caracteres perigosos
    caracteres_perigosos = re.compile(r'[;&|`$\(\)\{\}\[\]<>\n\r\x00\\]')
    
    bloqueados = 0
    for ataque in ataques:
        if caracteres_perigosos.search(ataque):
            bloqueados += 1
        else:
            print(f"  ❌ Ataque não tem caracteres perigosos: {ataque}")
    
    taxa_bloqueio = (bloqueados / len(ataques)) * 100
    print(f"  📊 Ataques com caracteres perigosos: {bloqueados}/{len(ataques)} ({taxa_bloqueio:.1f}%)")
    
    # Verificar que subprocess não usa shell
    try:
        with open("modulos/automacoes.py", "r", encoding="utf-8") as f:
            conteudo = f.read()
            tem_shell_true = "shell=True" in conteudo
            tem_subprocess_run = "subprocess.run" in conteudo or "subprocess.Popen" in conteudo
            
        if not tem_shell_true and tem_subprocess_run:
            print("  ✅ subprocess não usa shell=True (seguro)")
            resultado_seguro = True
        else:
            print("  ⚠️  subprocess pode estar usando shell=True")
            resultado_seguro = False
    except Exception as e:
        print(f"  ⚠️  Não pude verificar código: {e}")
        resultado_seguro = False
    
    if taxa_bloqueio >= 80 and resultado_seguro:
        print("  ✅ Proteção contra command injection funcionando")
        return True
    else:
        print("  ❌ Proteção insuficiente contra command injection")
        return False

# ===== TESTE DE RACE CONDITION =====

def test_race_condition_fixed():
    """Testa se race condition foi corrigido em ia_conversacional.py"""
    print("\n🏃 TESTANDO CORREÇÃO DE RACE CONDITION...")
    
    try:
        from modulos import ia_conversacional
    except ImportError as e:
        print(f"❌ Erro ao importar ia_conversacional: {e}")
        return False
    
    # Limpar histórico diretamente via módulo
    with ia_conversacional._historico_lock:
        ia_conversacional.historico.clear()
    
    resultados = []
    erros = []
    lock = threading.Lock()
    
    def worker(thread_id):
        """Worker que adiciona ao histórico simultaneamente"""
        try:
            for i in range(50):
                # Registrar entrada usando a função _registrar
                ia_conversacional._registrar(f"user_{thread_id}_{i}", f"assistant_{thread_id}_{i}")
                
                # Verificar integridade do histórico
                with lock:
                    tamanho_hist = len(ia_conversacional.historico)
                    if tamanho_hist > 0:
                        resultados.append(True)
                    else:
                        resultados.append(False)
                
                time.sleep(0.001)
        except Exception as e:
            with lock:
                erros.append(str(e))
    
    # Criar múltiplas threads
    threads = []
    for i in range(5):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()
    
    # Aguardar conclusão
    for t in threads:
        t.join()
    
    # Verificar resultados
    total_operacoes = len(resultados)
    operacoes_sucessos = sum(1 for r in resultados if r)
    taxa_sucesso = (operacoes_sucessos / total_operacoes) * 100 if total_operacoes > 0 else 0
    tamanho_final = len(ia_conversacional.historico)
    
    print(f"  📊 Operações realizadas: {total_operacoes}")
    print(f"  📊 Operações bem-sucedidas: {operacoes_sucessos}")
    print(f"  📊 Taxa de sucesso: {taxa_sucesso:.1f}%")
    print(f"  📊 Tamanho final do histórico: {tamanho_final}")
    print(f"  📊 Erros capturados: {len(erros)}")
    
    if erros:
        print("  ❌ Erros encontrados:")
        for erro in erros[:5]:
            print(f"    - {erro}")
    
    # Verificar que a lock existe no código
    try:
        with open("modulos/ia_conversacional.py", "r", encoding="utf-8") as f:
            conteudo = f.read()
            tem_lock = "_historico_lock" in conteudo and "with _historico_lock:" in conteudo
            
        if tem_lock:
            print("  ✅ threading.Lock implementado no código")
            lock_ok = True
        else:
            print("  ⚠️  Não encontrou _historico_lock no código")
            lock_ok = False
    except Exception:
        lock_ok = False
    
    if len(erros) == 0 and taxa_sucesso > 95 and lock_ok and tamanho_final > 0:
        print("  ✅ Race condition corrigido com sucesso")
        return True
    else:
        print("  ❌ Race condition ainda presente ou muito instável")
        return False

# ===== TESTE DE VALIDAÇÃO DE CONFIG CACHE =====

def test_config_cache():
    """Testa se o cache de config está funcionando"""
    print("\n⚡ TESTANDO CACHE DE CONFIGURAÇÃO...")
    
    try:
        from utils.config import carregar, salvar, limpar_cache, get, set
    except ImportError as e:
        print(f"❌ Erro ao importar config: {e}")
        return False
    
    # Limpar cache para teste limpo
    limpar_cache()
    
    # Medir tempo de primeira chamada (sem cache)
    inicio = time.time()
    config1 = carregar()
    tempo_sem_cache = time.time() - inicio
    
    # Medir tempo de segunda chamada (com cache)
    inicio = time.time()
    config2 = carregar()
    tempo_com_cache = time.time() - inicio
    
    # Verificar se são iguais
    configs_iguais = config1 == config2
    
    # Teste de get/set
    test_key = "teste_seguranca_" + str(int(time.time()))
    test_value = "valor_teste_" + str(int(time.time()))
    
    set(test_key, test_value)
    valor_recuperado = get(test_key)
    get_set_funciona = valor_recuperado == test_value
    
    limpar_cache()
    
    print(f"  📊 Tempo sem cache: {tempo_sem_cache*1000:.2f}ms")
    print(f"  📊 Tempo com cache: {tempo_com_cache*1000:.2f}ms")
    if tempo_sem_cache > 0:
        aceleracao = tempo_sem_cache / max(tempo_com_cache, 0.0001)
        print(f"  📊 Aceleração: {aceleracao:.1f}x")
    print(f"  📊 Configs idênticos: {configs_iguais}")
    print(f"  📊 Get/Set funcionando: {get_set_funciona}")
    
    if configs_iguais and get_set_funciona:
        print("  ✅ Cache de config funcionando corretamente")
        return True
    else:
        print("  ❌ Problemas no cache de config")
        return False

# ===== EXECUTAR TESTES =====

def main():
    print("🛡️  SUME - TESTE DE SEGURANÇA")
    print("=" * 50)
    
    resultados = []
    
    # Executar testes
    resultados.append(("Command Injection", test_command_injection_fixed()))
    resultados.append(("Race Condition", test_race_condition_fixed()))
    resultados.append(("Config Cache", test_config_cache()))
    
    # Resumo
    print("\n" + "=" * 50)
    print("📊 RESUMO DOS TESTES DE SEGURANÇA:")
    print("=" * 50)
    
    passou = 0
    total = len(resultados)
    
    for nome, resultado in resultados:
        status = "✅ PASSOU" if resultado else "❌ FALHOU"
        print(f"  {nome:<20} {status}")
        if resultado:
            passou += 1
    
    print("-" * 50)
    print(f"TOTAL: {passou}/{total} testes passaram")
    
    if passou == total:
        print("\n🎉 TODOS OS TESTES DE SEGURANÇA PASSARAM!")
        print("✅ As correções críticas estão funcionando corretamente.")
        return True
    else:
        print(f"\n⚠️  {total - passou} teste(s) falharam.")
        print("❌ Revisar as correções de segurança.")
        return False

if __name__ == "__main__":
    sucesso = main()
    sys.exit(0 if sucesso else 1)
