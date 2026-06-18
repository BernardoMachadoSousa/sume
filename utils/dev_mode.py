"""
Modo Desenvolvedor — exibe logs em tempo real no terminal.
Execute em um CMD separado: python utils/dev_mode.py
"""

import os
import time

LOG_FILE = "dados/sume.log"

def iniciar():
    print("=" * 60)
    print("MODO DESENVOLVEDOR — acompanhando logs em tempo real")
    print("Pressione Ctrl+C para sair")
    print("=" * 60)
    
    if not os.path.exists(LOG_FILE):
        print("Aguardando logs... (abra o Sumé e use comandos)")
    
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        f.seek(0, 2)  # vai pro final
        try:
            while True:
                linha = f.readline()
                if linha:
                    print(linha, end="")
                else:
                    time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nModo desenvolvedor encerrado.")

if __name__ == "__main__":
    iniciar()