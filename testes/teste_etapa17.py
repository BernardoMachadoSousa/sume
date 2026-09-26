"""
Teste da Etapa 17: Sincronizacao em nuvem com encriptacao.
Valida encriptacao, versionamento e conflito resolution.
"""

import sys
import os
import json
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from plugins.encriptacao import (
    GerenciadorChaves, EncriptadorAES, EnvelopeEncriptado,
    VerificadorIntegridade, gerar_chave_mestra, criar_encriptador,
    criar_envelope, abrir_envelope
)
from plugins.sincronizacao import (
    ClienteSincronizacao, VersaoArquivo, ArquivoSincronizado,
    RepositorioLocal, inicializar_cliente
)
import hashlib

def teste_gerenciador_chaves():
    """Testa geracao e armazenamento de chaves."""
    print("\n--- Gerenciador de Chaves ---")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        gerenciador = GerenciadorChaves(os.path.join(tmpdir, "chaves.json"))
        
        # Gerar chave mestra
        chave, salt = gerenciador.gerar_chave_mestra("minha_senha_secreta")
        assert len(chave) == 32, "Chave deve ter 32 bytes (256 bits)"
        assert len(salt) == 32, "Salt deve ter 32 bytes"
        print("  X chave mestra gerada corretamente")
        
        # Mesmo salt deve gerar mesma chave
        chave2, _ = gerenciador.gerar_chave_mestra("minha_senha_secreta", salt)
        assert chave == chave2, "Mesma senha com mesmo salt deve gerar mesma chave"
        print("  X derivacao de chave deterministica")
        
        # Senhas diferentes devem gerar chaves diferentes
        chave3, _ = gerenciador.gerar_chave_mestra("outra_senha", salt)
        assert chave != chave3, "Senhas diferentes devem gerar chaves diferentes"
        print("  X senhas diferentes geram chaves diferentes")
        
        # Gerar ID dispositivo
        dispositivo = gerenciador.gerar_chave_dispositivo()
        assert len(dispositivo) > 0, "ID dispositivo deve ser gerado"
        print("  X ID dispositivo gerado")

def teste_encriptador_aes():
    """Testa encriptacao e descriptografia AES."""
    print("\n--- Encriptador AES ---")
    
    chave_mestra, _ = gerar_chave_mestra("teste123")
    encriptador = criar_encriptador(chave_mestra)
    
    # Encriptar texto simples
    texto_original = "Esta eh uma mensagem confidencial"
    texto_encriptado = encriptador.encriptar(texto_original)
    assert texto_encriptado != texto_original, "Texto encriptado nao deve ser legivel"
    print("  X texto encriptado com sucesso")
    
    # Descriptografar
    texto_recuperado = encriptador.descriptografar(texto_encriptado)
    assert texto_recuperado == texto_original, "Texto deve ser recuperado corretamente"
    print("  X texto descriptografado corretamente")
    
    # Encriptar JSON
    json_original = {"usuario": "joao", "email": "joao@example.com"}
    json_encriptado = encriptador.encriptar_json(json_original)
    json_recuperado = encriptador.descriptografar_json(json_encriptado)
    assert json_recuperado == json_original, "JSON deve ser recuperado"
    print("  X JSON encriptado e descriptografado")

def teste_verificador_integridade():
    """Testa verificacao de integridade com HMAC."""
    print("\n--- Verificador de Integridade ---")
    
    chave = b"chave_secreta_123"
    dados = "dados importantes"
    
    # Gerar hash
    hash_correto = VerificadorIntegridade.gerar_hash(dados, chave)
    assert len(hash_correto) == 64, "SHA256 deve ter 64 caracteres hex"
    print("  X hash gerado corretamente")
    
    # Verificar hash correto
    assert VerificadorIntegridade.verificar_hash(dados, hash_correto, chave), "Hash deve ser valido"
    print("  X hash validado com sucesso")
    
    # Verificar hash incorreto
    hash_falso = "0" * 64
    assert not VerificadorIntegridade.verificar_hash(dados, hash_falso, chave), "Hash falso deve falhar"
    print("  X hash falso rejeitado")
    
    # Dados alterados devem falhar
    dados_alterados = "dados importantes alterados"
    assert not VerificadorIntegridade.verificar_hash(dados_alterados, hash_correto, chave), "Dados alterados devem falhar"
    print("  X deteccao de alteracao de dados")

def teste_envelope_encriptado():
    """Testa criacao e abertura de envelope."""
    print("\n--- Envelope Encriptado ---")
    
    chave_mestra, _ = gerar_chave_mestra("senha123")
    encriptador = criar_encriptador(chave_mestra)
    senha = "senha123"
    
    dados = {
        "usuario": "maria@example.com",
        "notas": [
            {"titulo": "Python", "conteudo": "Linguagem de programacao"}
        ]
    }
    
    # Criar envelope
    envelope_json = criar_envelope(encriptador, dados, senha)
    assert envelope_json, "Envelope deve ser criado"
    
    # Envelope deve ser JSON valido
    envelope = json.loads(envelope_json)
    assert "versao" in envelope, "Envelope deve ter versao"
    assert "dados" in envelope, "Envelope deve ter dados"
    assert "hash" in envelope, "Envelope deve ter hash"
    print("  X envelope criado com estrutura correta")
    
    # Abrir envelope
    dados_recuperados = abrir_envelope(encriptador, envelope_json, senha)
    assert dados_recuperados["dados"] == dados, "Dados devem ser recuperados"
    assert "timestamp" in dados_recuperados, "Deve ter timestamp"
    print("  X envelope aberto e validado")
    
    # Tentar abrir com chave errada deve falhar
    chave_errada, _ = gerar_chave_mestra("outra_senha")
    encriptador_errado = criar_encriptador(chave_errada)
    try:
        abrir_envelope(encriptador_errado, envelope_json, "outra_senha")
        assert False, "Deve falhar com chave errada"
    except ValueError:
        print("  X rejeita envelope com chave errada")

def teste_versao_arquivo():
    """Testa criacao de versoes de arquivo."""
    print("\n--- Versao de Arquivo ---")
    
    versao1 = VersaoArquivo("conteudo 1")
    assert versao1.conteudo == "conteudo 1", "Deve armazenar conteudo"
    assert versao1.hash, "Deve gerar hash"
    print("  X versao criada corretamente")
    
    versao2 = VersaoArquivo("conteudo 2")
    assert versao1.hash != versao2.hash, "Hashes diferentes para conteudos diferentes"
    print("  X hashes diferentes para conteudos diferentes")

def teste_arquivo_sincronizado():
    """Testa arquivo com historico de versoes."""
    print("\n--- Arquivo Sincronizado ---")
    
    arquivo = ArquivoSincronizado("/path/to/file.md", "file.md")
    
    # Adicionar versoes
    v1 = VersaoArquivo("versao 1")
    arquivo.adicionar_versao(v1)
    assert len(arquivo.versoes) == 1, "Deve ter 1 versao"
    print("  X versao adicionada")
    
    v2 = VersaoArquivo("versao 2")
    arquivo.adicionar_versao(v2)
    assert len(arquivo.versoes) == 2, "Deve ter 2 versoes"
    
    # Obter versao atual
    versao_atual = arquivo.obter_versao_atual()
    assert versao_atual.conteudo == "versao 2", "Deve retornar versao mais recente"
    print("  X versao atual correta")

def teste_cliente_sincronizacao():
    """Testa cliente de sincronizacao."""
    print("\n--- Cliente de Sincronizacao ---")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        chave_mestra, _ = gerar_chave_mestra("senha_teste")
        cliente = ClienteSincronizacao(chave_mestra, "senha_teste")
        
        # Registrar arquivo
        arquivo_path = os.path.join(tmpdir, "test.md")
        with open(arquivo_path, 'w', encoding='utf-8') as f:
            f.write("conteudo teste")
        
        arquivo = cliente.registrar_arquivo(arquivo_path, "test.md")
        assert arquivo, "Arquivo deve ser registrado"
        print("  X arquivo registrado")
        
        # Sincronizar local
        sucesso = cliente.sincronizar_arquivo_local("test.md")
        assert sucesso, "Deve sincronizar arquivo local"
        assert len(arquivo.versoes) > 0, "Deve ter versoes"
        print("  X sincronizacao local funcionando")
        
        # Status
        status = cliente.obter_status()
        assert status["total_arquivos"] == 1, "Deve ter 1 arquivo"
        assert status["arquivos_com_conflito"] == 0, "Nao deve ter conflitos"
        print("  X status correto")

def teste_conflito_resolution():
    """Testa resolucao de conflitos."""
    print("\n--- Conflito Resolution ---")
    
    chave_mestra, _ = gerar_chave_mestra("senha_teste")
    cliente = ClienteSincronizacao(chave_mestra, "senha_teste")
    
    # Registrar arquivo
    arquivo = cliente.registrar_arquivo("/path/file.md", "file.md")
    
    # Marcar como em conflito
    arquivo.em_conflito = True
    assert arquivo.em_conflito, "Deve estar em conflito"
    print("  X conflito detectado")
    
    # Resolver conflito
    sucesso = cliente.resolver_conflito("file.md", "local")
    assert sucesso, "Deve resolver conflito"
    assert not arquivo.em_conflito, "Conflito deve ser resolvido"
    assert arquivo.resolucao["estrategia"] == "local", "Deve usar estrategia local"
    print("  X conflito resolvido com sucesso")

def teste_repositorio_local():
    """Testa repositorio local de sincronizacao."""
    print("\n--- Repositorio Local ---")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = RepositorioLocal(tmpdir)
        
        # Registrar arquivo
        hash_local = "abc123"
        repo.registrar_arquivo("file.md", hash_local, "2026-09-26T00:00:00")
        assert "file.md" in repo.indice, "Arquivo deve estar no indice"
        print("  X arquivo registrado no repositorio")
        
        # Verificar status
        status = repo.obter_status_arquivo("file.md")
        assert status["hash_local"] == hash_local, "Hash deve corresponder"
        assert not status["sincronizado"], "Nao deve estar sincronizado inicialmente"
        print("  X status correto")
        
        # Marcar como sincronizado
        repo.marcar_sincronizado("file.md")
        status = repo.obter_status_arquivo("file.md")
        assert status["sincronizado"], "Deve estar sincronizado"
        print("  X marcado como sincronizado")
        
        # Listar pendentes
        pendentes = repo.listar_pendentes()
        assert "file.md" not in pendentes, "Arquivo sincronizado nao deve estar em pendentes"
        print("  X listar pendentes funcionando")

def teste_fluxo_completo_sincronizacao():
    """Testa fluxo completo de sincronizacao."""
    print("\n--- Fluxo Completo ---")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Criar arquivo
        arquivo_path = os.path.join(tmpdir, "notas.md")
        with open(arquivo_path, 'w', encoding='utf-8') as f:
            f.write("# Minhas Notas\n\nPython eh legal")
        print("  1. Arquivo criado")
        
        # 2. Inicializar cliente
        chave_mestra, _ = gerar_chave_mestra("senha_secreta")
        cliente = inicializar_cliente(chave_mestra, "senha_secreta")
        cliente.registrar_arquivo(arquivo_path, "notas.md")
        print("  2. Cliente inicializado")
        
        # 3. Sincronizar local
        cliente.sincronizar_arquivo_local("notas.md")
        print("  3. Sincronizacao local")
        
        # 4. Sincronizar para nuvem
        sucesso, msg = cliente.sincronizar_para_nuvem("notas.md")
        assert sucesso, f"Deve sincronizar para nuvem: {msg}"
        print("  4. Sincronizacao para nuvem")
        
        # 5. Verificar status
        status = cliente.obter_status()
        assert status["total_arquivos"] == 1, "Deve ter 1 arquivo"
        print("  5. Status verificado")
        
        print("  X FLUXO COMPLETO FUNCIONANDO")

def main():
    print("=" * 68)
    print("TESTE DA ETAPA 17: Sincronizacao em Nuvem")
    print("=" * 68)
    
    try:
        teste_gerenciador_chaves()
        teste_encriptador_aes()
        teste_verificador_integridade()
        teste_envelope_encriptado()
        teste_versao_arquivo()
        teste_arquivo_sincronizado()
        teste_cliente_sincronizacao()
        teste_conflito_resolution()
        teste_repositorio_local()
        teste_fluxo_completo_sincronizacao()
        
        print("\n" + "=" * 68)
        print("OK TODOS OS TESTES DA ETAPA 17 PASSARAM!")
        print("Sincronizacao em nuvem validada.")
        print("=" * 68)
        return 0
        
    except AssertionError as e:
        print(f"\nERRO: {e}")
        return 1
    except Exception as e:
        print(f"\nERRO INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
