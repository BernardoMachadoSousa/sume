SUMÉ A.I. - DOCUMENTAÇÃO TÉCNICA
=================================

## Visão Geral

Sumé A.I. é um assistente de voz inteligente desktop com capacidades de busca semântica, 
gerenciamento de memória em camadas, e interface web responsiva. O sistema implementa um 
núcleo híbrido (Groq/Ollama) com foco em privacidade e performance.

## Arquitetura

### Camadas do Sistema

1. **Núcleo (core/)**
   - nexus_core.py: orquestrador principal, processamento de comandos
   - memoria.py: sistema de memória em 3 camadas (cache/trabalho/longo prazo)
   - vault.py: gerenciamento de notas Markdown no disco

2. **Entrada de Voz (voz/)**
   - captura.py: captura de áudio com VAD (Voice Activity Detection)
   - transcricao.py: reconhecimento de fala com Groq/Ollama
   - vad.py: detecção adaptativa de fala por frames

3. **Processamento (plugins/)**
   - busca/: busca semântica em notas + busca de arquivos no PC
   - seguranca.py: sanitização, validação, rate limiting
   - Handlers específicos para cada intent (BUSCAR_NOTAS, BUSCAR_ARQUIVOS, etc)

4. **Interface Web (interface/)**
   - index.html: widget responsivo com controles de filtro
   - assets/style.css: design glassmorphism com media queries
   - assets/script.js: lógica de cliente com touch gestures

5. **Testes (testes/)**
   - Cobertura completa: Etapa 1-15
   - Validação de memory, busca, segurança, performance

### Sistema Híbrido Groq/Ollama

```
Entrada de Comando
       ↓
   [Cache LRU] → Retorna resultado imediato
       ↓ (miss)
   Privacy Flag? ↓
   compartilhar_conteudo_nuvem (default: False)
       ↓
   Sim → [Groq API] → Processamento remoto + cloud storage
   Não → [Ollama Local] → Processamento local (phi3:mini)
       ↓
   [Fallback] → Se um falhar, tenta o outro
       ↓
   Resposta ao usuário
```

## Componentes-Chave

### 1. Busca Inteligente (Etapa 10)
- **Semântica**: TF-IDF + embeddings do Ollama
- **Arquivo**: Busca no PC com filtros (extensão, caminho, tamanho)
- **Relevância**: Score 0.0-1.0 baseado em similaridade textual
- **Cache**: LRU com TTL para reutilização rápida

Handlers:
- BUSCAR_NOTAS: busca em vault.md com contexto
- BUSCAR_ARQUIVOS: busca no computador com escopo

### 2. Interface Web (Etapa 11)
- **Backend**: WebView Pywebview com API Python
- **Comunicação**: JSON via pywebview.api
- **Dados**: Estrutura com notas[], arquivos[], relevancia, metadados

Fluxo:
1. Usuário fala comando
2. Transcrito → Núcleo processa
3. Núcleo envia dados para frontend
4. Frontend renderiza cards com filtros/ordenação

### 3. Filtros e Ordenação (Etapa 12)
- **Filtros**: tipo (notas/arquivos), relevância (min-max)
- **Ordenação**: relevância, nome, data, tamanho
- **Exportação**: JSON, CSV, TXT, Markdown
- **UI**: Controles ocultos até fullscreen mode

### 4. Performance (Etapa 13)
- **Cache LRU**: 100 itens, TTL 3600s, evicção automática
- **Índice**: Hash MD5 de arquivos, palavras-chave extraídas
- **Ganho**: 100% mais rápido em buscas repetidas

Mecanismo:
```python
cache.obter(termo, tipo) → resultado ou None
cache.guardar(termo, resultado, tipo) → armazena com TTL
```

### 5. Responsividade Móvel (Etapa 14)
- **Media Queries**: 768px (tablet), 480px (smartphone), landscape
- **Touch Gestures**: Swipe esquerda/direita para controlar filtros
- **Otimizações**: Font-sizes dinâmicos, botões 44px min, overflow hidden
- **Viewport**: viewport-fit=cover para notch, user-scalable=no

### 6. Segurança (Etapa 15)
- **XSS Prevention**: Sanitização de HTML, escape de entities
- **Injection Detection**: Reconhece ;, &&, backticks, $(...), pipe
- **Rate Limiting**: 100 req/60s por usuário/IP
- **Path Traversal**: Valida caminhos, bloqueia '..'
- **CSRF Tokens**: Gerador e validador de tokens

## Fluxo de Execução

### 1. Inicialização
```
main.py start
   ↓
Carrega config.json (GROQ_API_KEY, modo híbrido)
   ↓
Inicializa núcleo (memoria, vault, plugins)
   ↓
Abre interface web (localhost:5000)
   ↓
Aguarda comandos de voz/texto
```

### 2. Processamento de Comando
```
Entrada (voz ou texto)
   ↓
Transcrição (Groq/Ollama com fallback)
   ↓
Sanitização & Validação (seguranca.py)
   ↓
Detecção de intent (regex patterns)
   ↓
Rate limiting check
   ↓
Cache lookup → Executar handler → Guardar no cache
   ↓
Formatar resposta + dados estruturados
   ↓
Enviar para UI + guardar no histórico
```

### 3. Busca Semântica
```
Termo de busca
   ↓
Sanitizar + Validar
   ↓
Cache lookup
   ↓
Gerar embedding (Ollama)
   ↓
Calcular similaridade TF-IDF
   ↓
Rank por relevância (score 0-1)
   ↓
Aplicar filtros (tipo, relevância mín)
   ↓
Aplicar ordenação
   ↓
Retornar top N resultados
```

## Configuração e Variáveis de Ambiente

```bash
GROQ_API_KEY=sk_... (opcional, ativa Groq remoto)
OLLAMA_HOST=http://localhost:11434 (padrão)
```

### config.json
```json
{
  "modo_hibrido": true,
  "compartilhar_conteudo_nuvem": false,
  "cache_ttl": 3600,
  "rate_limit": 100,
  "vault_path": "~/.sume/vault.md"
}
```

## API Endpoints (WebView)

```javascript
// Processamento de comando
pywebview.api.processar_comando_info(texto)
  → { resposta, erro, dados: { notas, arquivos } }

// Ouvir comando de voz
pywebview.api.ouvir_comando()
  → texto transcrito ou "silencio"

// Minimizar/fechar janela
pywebview.api.minimizar_janela()
pywebview.api.fechar_janela()
```

## Testes

Todas as 15 etapas têm cobertura de testes:

```bash
pytest testes/teste_etapa*.py -v

# Ou executar individualmente:
python testes/teste_etapa12.py  # Filtros (18 testes)
python testes/teste_etapa13.py  # Performance (19 testes)
python testes/teste_etapa14.py  # Mobile (24 testes)
python testes/teste_etapa15.py  # Segurança (27 testes)
```

Total: 88+ testes passando

## Performance

### Benchmarks

- **Primeira busca**: ~500-800ms (processamento + embedding)
- **Busca em cache**: ~10-50ms (LRU hit)
- **UI responsiveness**: < 100ms (filtros/ordenação/export)
- **Mobile (480px)**: < 200ms no slowest phone (3G)

### Otimizações

1. Cache LRU com TTL automático
2. Índices com hash MD5 para detecção rápida de mudanças
3. Extração de palavras-chave pré-computada
4. Rate limiting para evitar DDOS

## Segurança

### Defesas Implementadas

1. **XSS**: Sanitização de HTML, escape de entities
2. **Injection**: Detecção de padrões suspeitos (;, &&, `, etc)
3. **Path Traversal**: Validação de caminhos, rejeição de '..'
4. **Rate Limiting**: 100 req/60s por usuário
5. **CSRF**: Tokens gerados e validados

### Boas Práticas

- Nenhum secret armazenado em repo (GROQ_API_KEY via env)
- Limpeza de texto antes de exibir
- Validação de entrada em todos os handlers
- Normalização de caminhos antes de acesso

## Deployment

### Requisitos

```
Python 3.8+
pywebview >= 4.0
groq >= 0.7.0 (opcional)
requests
```

### Instalação

```bash
pip install -r requirements.txt
python main.py
```

### Build Executável

```bash
pyinstaller --onefile --windowed main.py
```

## Melhorias Futuras

- [ ] Suporte para múltiplos idiomas
- [ ] Integração com calendário/lembretes
- [ ] Sincronização na nuvem (com encriptação)
- [ ] Plugin system extensível
- [ ] Análise de sentimento em notas
- [ ] Backup automático
- [ ] Modo offline completo
- [ ] Customização de atalhos

## Suporte

Para bugs ou sugestões:
1. Abrir issue no GitHub
2. Incluir logs: `~/.sume/logs.txt`
3. Descrever ambiente (Windows/Linux/Mac, Python version)
