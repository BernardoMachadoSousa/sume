SUMÉ A.I. - GUIA DO USUÁRIO
============================

## O que é Sumé?

Sumé é um assistente de voz inteligente que você pode usar para:
- Buscar notas no seu vault pessoal
- Encontrar arquivos no seu computador
- Gerenciar lembretes e anotações
- Organizar informações com filtros e exportação

## Primeiros Passos

### 1. Instalação

```bash
# Clonar repositório
git clone https://github.com/anomalyco/sume.git
cd sume

# Instalar dependências
pip install -r requirements.txt

# (Opcional) Instalar Groq para processamento remoto
# Adicionar GROQ_API_KEY ao ambiente
export GROQ_API_KEY=sk_...
```

### 2. Iniciar Sumé

```bash
python main.py
```

Uma janela aparecerá com o logo do Sumé. Você pode:
- **Clicar no círculo** para falar um comando
- **Digitar** na caixa de entrada abaixo
- **Pressionar Enter** para enviar o comando

### 3. Primeiros Comandos

Tente estes comandos:

```
"Buscar python"
"Procurar arquivos json"
"Encontrar nota sobre memória"
"Listar documentos"
```

## Interface

### Painel Principal

```
┌─────────────────────────────────┐
│  SUMÉ    [↔]  [_]  [×]         │  ← Barra de título
├─────────────────────────────────┤
│                                 │
│        ◐ (círculo)              │  ← Status (pronto/ouvindo)
│      Aguardando                 │
│                                 │
│  ─────────────────────────────  │
│  Comando 1: resposta...         │  ← Histórico
│  Você: buscar python            │
│  Sumé: Encontrei 3 notas...     │
│  ─────────────────────────────  │
│                                 │
│  [Digite aqui...] [Enviar]      │  ← Input
│                                 │
└─────────────────────────────────┘
```

### Modo Tela Cheia

Clique no botão **[↔]** (expandir) para ativar modo tela cheia.

No modo tela cheia você pode:
- Ver mais resultados
- Aplicar filtros
- Ordenar resultados
- Exportar dados

#### Controles de Filtro

```
Tipo de resultado:  [Notas ▼]  [Todos ▼]
Ordenar por:        [Relevância ▼]
Relevância mín:     [●────●────●] 0.0 - 1.0
Exportar:           [JSON] [CSV] [TXT] [Markdown]
```

## Buscando Informações

### Buscar em Notas

```
Você: "Buscar Python"
Sumé: Encontrei 3 nota(s):
      - Python Basics: Python é uma linguagem de programação...
      - Python OOP: Classes e objetos em Python...
      - Python Web: Framework Django para web...
```

As notas vêm com:
- **Relevância** (porcentagem de similaridade)
- **Caminho** do arquivo
- **Trecho** do conteúdo

### Buscar Arquivos

```
Você: "Procurar arquivos PDF"
Sumé: Encontrei 5 arquivo(s):
      - documento.pdf (Relevância: 95%)
      - relatorio.pdf
      - manual.pdf
      - ...
```

Os arquivos mostram:
- **Nome** do arquivo
- **Caminho** completo
- **Relevância** da busca

## Filtros e Ordenação

### Filtrar por Tipo

No modo tela cheia, você pode filtrar:
- **Notas**: Mostra apenas notas do vault
- **Arquivos**: Mostra apenas arquivos encontrados
- **Todos**: Mostra notas e arquivos

### Filtrar por Relevância

Use o slider para definir a relevância mínima:
- **0.0 - 0.3**: Resultados frouxos
- **0.3 - 0.7**: Resultados medianos
- **0.7 - 1.0**: Resultados muito relevantes

### Ordenar Resultados

Escolha como ordenar:
- **Relevância** (padrão): Melhores correspondências primeiro
- **Nome**: Ordem alfabética
- **Data**: Mais recentes primeiro
- **Tamanho**: Maiores primeiro

## Exportar Dados

### Formatos Disponíveis

1. **JSON**: Estrutura de dados completa
   ```json
   {
     "notas": [...],
     "arquivos": [...]
   }
   ```

2. **CSV**: Tabela para Excel/Sheets
   ```
   tipo,titulo/nome,relevancia,caminho
   nota,"Python",0.95,"vault.md"
   arquivo,"script.py",0.88,"C:/Users/.../script.py"
   ```

3. **TXT**: Texto simples legível
   ```
   RESULTADOS DE BUSCA
   =====================
   NOTAS:
   - Python (95%)
   - Programação (87%)
   
   ARQUIVOS:
   - script.py (88%)
   ```

4. **Markdown**: Formatado para documentos
   ```markdown
   # Resultados de Busca
   
   ## Notas
   - **Python** (95%) - [Abrir](vault.md)
   
   ## Arquivos
   - **script.py** (88%) - [Abrir](C:/...)
   ```

## Mobile e Responsividade

### Usar no Smartphone

Sumé funciona em qualquer navegador ou app mobile:

1. **Toque no círculo** para ativar voz
2. **Digite** na caixa grande no topo
3. **Deslize esquerda** para esconder filtros
4. **Deslize direita** para mostrar filtros

### Ajustes Automáticos

A interface se adapta automaticamente:
- **Tablet (768px)**: Menu reduzido, botões maiores
- **Smartphone (480px)**: Layout vertical, touch-friendly
- **Landscape**: Altura otimizada
- **Notch**: Espaço automático reservado

## Privacidade

### Compartilhamento de Dados

Por padrão, Sumé **NÃO** compartilha seus dados na nuvem.

Para usar Groq (processamento remoto):
1. Defina `GROQ_API_KEY` no ambiente
2. Ative `compartilhar_conteudo_nuvem` em config.json

```json
{
  "compartilhar_conteudo_nuvem": false
}
```

### Dados Armazenados Localmente

- Histórico de comandos: `~/.sume/historico.json`
- Memória: `~/.sume/memoria.json`
- Índice de notas: `~/.sume/indice_notas.json`
- Logs: `~/.sume/logs.txt`

## Atalhos do Teclado

| Tecla | Ação |
|-------|------|
| **Enter** | Enviar comando |
| **Ctrl+L** | Limpar histórico |
| **Ctrl+E** | Expandir/Recolher |
| **Ctrl+F** | Foco no input |
| **Escape** | Sair do fullscreen |

## Comandos Comuns

### Busca

```
"Buscar {termo}"
"Procurar {termo}"
"Encontrar {termo}"
"Listar {tipo}"
```

### Notas

```
"Criar nota sobre {tema}"
"Abrir note de {tema}"
"Editar nota {nome}"
"Remover nota {nome}"
```

### Lembretes

```
"Lembrar-me de {tarefa}"
"Agendar {tarefa} para {data}"
"Ver lembretes"
```

## Dicas e Truques

### 1. Buscas Mais Rápidas

Use o cache! Buscas repetidas são **100x mais rápidas**:

```
1ª busca: "Buscar python" → ~500ms
2ª busca: "Buscar python" → ~10ms ⚡
```

### 2. Combinar Filtros

Filtro por tipo + Relevância alta = Resultados precisos

```
Tipo: Notas
Relevância mín: 0.8
→ Mostra apenas notas muito relevantes
```

### 3. Exportar para Análise

Use CSV para analisar em Excel:

```
1. Fazer busca
2. Exportar em CSV
3. Abrir em Excel/Sheets
4. Criar gráficos/análises
```

### 4. Fullscreen para Mais Espaço

Use **Ctrl+E** ou clique **[↔]** para:
- Ver mais resultados
- Ter mais espaço para ler
- Acessar filtros avançados

## Troubleshooting

### Problema: Microfone não funciona

**Solução**:
1. Verifique permissões de microfone
2. Teste com outro app
3. Reinicie Sumé
4. Use digite em vez de falar

### Problema: Busca muito lenta

**Solução**:
1. Primeira busca é sempre lenta (embedding)
2. Buscas repetidas usam cache (rápido)
3. Se ainda lento: verifique Ollama está rodando

### Problema: Nenhum resultado encontrado

**Solução**:
1. Tente termos diferentes
2. Abaixe o filtro de relevância
3. Verifique se vault tem notas
4. Use "Listar tudo" para ver todos os arquivos

### Problema: Interface não responsiva

**Solução**:
1. Atualize o navegador (F5)
2. Limpe cache do navegador
3. Feche e abra novamente Sumé
4. Verifique espaço em disco

## Privacidade e Segurança

### Como seus dados são protegidos

✅ **Processamento local** (padrão)
- Nenhum dado deixa seu computador
- Ollama roda localmente
- Notas permanecem offline

✅ **Validação de entrada**
- Caracteres especiais são filtrados
- Caminhos são validados
- Injection attacks são bloqueadas

✅ **Rate limiting**
- Proteção contra abuso
- Máximo 100 requisições/minuto
- Limites por usuário

### Se usar Groq (Remoto)

⚠️ Dados são processados na nuvem
- Use apenas se conforável
- Desative por padrão
- Ative em config.json se necessário

## Contato e Suporte

### Reportar um Bug

1. Abra uma issue no GitHub
2. Inclua:
   - Comando que executou
   - Erro recebido
   - Versão do Python
   - Sistema operacional

### Sugerir Melhoria

Envie sugestões para melhorar Sumé:
- Interface mais intuitiva
- Novos tipos de filtro
- Novos formatos de exportação
- Melhor performance

## Glossário

| Termo | Significado |
|-------|------------|
| **Vault** | Pasta com suas notas em Markdown |
| **Relevância** | Quanto um resultado corresponde à busca (0-100%) |
| **Cache** | Armazenamento rápido de buscas recentes |
| **Embedding** | Representação vetorial de texto para busca semântica |
| **Groq** | Serviço de processamento remoto (opcional) |
| **Ollama** | Motor de IA local rodando no seu PC |
| **Fullscreen** | Modo de tela cheia com mais controles |
| **Rate Limit** | Limite de requisições por minuto |

## Próximas Etapas

Sumé está em desenvolvimento contínuo. Próximas features:

- 📅 Integração com calendário
- 🔐 Sincronização encriptada na nuvem
- 🌐 Suporte para múltiplos idiomas
- 📱 App nativo para mobile
- 🔌 Plugin system extensível

Acompanhe as atualizações no GitHub!

---

**Última atualização**: Setembro 2026
**Versão**: 1.0.0 (Etapas 12-15 completas)
