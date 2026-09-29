import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from modulos.ia_extracao import extrair_grafo

print(extrair_grafo('o meu nome é bernardo jonas e nasci em 2004'))
