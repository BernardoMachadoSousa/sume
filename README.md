# ⚡ Sumé — Assistente Virtual

Assistente pessoal com voz, memória e automações.

---

## 1. O que instalar

| Ferramenta | Link                              | Observação                             |
| ---------- | --------------------------------- | -------------------------------------- |
| Python     | https://python.org                | **Marcar "Add to PATH"** na instalação |
| Git        | https://git-scm.com/downloads/win | Instalação padrão (Next, Next, Finish) |
| VS Code    | https://code.visualstudio.com     | Editor de código                       |

### Conferir se instalou certo

Abra o **CMD** (Windows + R, digite `cmd`, Enter) e execute:

```bash
python --version
```

Deve mostrar `Python 3.10.x` ou superior.

```bash
git --version
```

Deve mostrar `git version 2.x.x`.

```bash
code --version
```

Deve mostrar a versão do VS Code.

---

## 2. Baixar o projeto

```bash
git clone https://github.com/BernardoMachadoSousa/sume.git
cd sume
```

---

## 3. Criar ambiente virtual e instalar dependências

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

## 4. Modelo de voz (Whisper)

Não há download manual. Na primeira execução o `openai-whisper` baixa sozinho o modelo
definido em `utils/escuta.py` (`MODELO = "small"`, ~460 MB) e guarda no cache do usuário.
Demora alguns minutos e precisa de internet **só nessa primeira vez**.

> O projeto usava Vosk antes, mas ele foi removido do `requirements.txt` na Etapa 1.
> Se ainda existir uma pasta `modelo_voz` na raiz, pode apagar.

---

## 5. Configuração

Não é preciso criar arquivo. O `utils/config.py` gera `dados/config.json` sozinho na primeira
execução, já com os valores padrão. Para mudar algo, edite esse arquivo depois da primeira
execução ou chame `utils.config.set("chave", valor)`.

---

## 6. Rodar o projeto

```bash
python main.py
```

Se tudo deu certo, a janela do Sumé vai abrir.

---

## 📁 Estrutura de pastas

```
sume/
├── main.py                  # Inicia o app (pywebview)
├── requirements.txt         # Bibliotecas necessárias
├── core/
│   ├── nexus_core.py        # Cérebro: interpreta e roteia comandos
│   ├── router.py            # Registro de handlers por ação
│   ├── handlers.py          # Ações concretas (abrir, fechar, etc.)
│   └── intents/             # Um arquivo por intent, com detector e confiança
├── modulos/
│   ├── memoria.py           # Memória em SQLite
│   ├── automacoes.py        # Abrir/fechar apps e sites
│   └── ia_conversacional.py # Conversa via Ollama
├── utils/
│   ├── voz.py               # Síntese de fala (Edge TTS)
│   ├── escuta.py            # Captura + transcrição (Whisper)
│   ├── config.py            # Preferências em dados/config.json
│   └── logger.py            # Logs
├── interface/
│   ├── index.html           # Tela
│   └── assets/
│       ├── style.css        # Visual
│       └── script.js        # Comportamento
├── testes/                  # Testes automatizados e diagnósticos
└── dados/                   # Gerado em runtime (fora do Git)
    ├── config.json          # Preferências
    ├── memoria.db           # Memória SQLite
    └── catalogo_programas.json
```

---

## 🔄 Como usar o Git

### Configurar (só na primeira vez)

```bash
git config --global user.email "seu-email@gmail.com"
git config --global user.name "SeuNomeNoGitHub"
```

### Antes de programar

```bash
git pull
```

### Depois de fazer alterações

```bash
git add .
git commit -m "O que você fez"
git push
```

---

## 🤝 Regras da equipe

1. **Sempre faça `git pull` antes de começar**
2. Avise no WhatsApp o que vai mexer
3. Teste antes de dar `git push`
4. Não mexa no `main.py` ou `dados/config.json` sem avisar
5. Commits em português, objetivos: `"Adicionei comando de clima"`

---

## ❗ Problemas comuns

| Erro                        | Solução                                   |
| --------------------------- | ----------------------------------------- |
| `pip não é reconhecido`     | Reinstale o Python marcando "Add to PATH" |
| PowerShell não ativa venv   | Use o **CMD**, não o PowerShell           |
| `ModuleNotFoundError`       | `pip install nome-do-modulo`              |
| Falha ao baixar o Whisper    | Precisa de internet só na 1ª execução; o modelo tem ~460 MB |

---

## 📖 Histórico do projeto

Conversa completa com todas as decisões e ideias:

https://chat.deepseek.com/share/6f64u0d6s37xcameki

---

## 👥 Time

* Bernardo Machado Sousa — Coordenação
* Gabriel Almeida Carvalho
* Matheus Torquato Gomes

---

Salve (Ctrl+S) e depois no CMD:

```bash
git add README.md
git commit -m "README final organizado"
git push
```


## 📋 Tarefas do Sumé

### ✅ Concluído
- [x] Edge TTS (voz natural Antônio)
- [x] Ollama + Phi-3 Mini (IA local)
- [x] Whisper (reconhecimento de voz)
- [x] Corte de silêncio por limiar de amplitude — **não é VAD real**, ver Etapa 3
- [x] Push-to-talk (segurar Espaço)
- [x] SQLite (substituiu JSON)
- [x] Automações inteligentes (abrir/fechar programas)
- [x] Pré-carregamento do Whisper
- [x] Atalhos de desenvolvimento
- [x] Corrigir inconsistência `nome` vs `nome_usuario`
- [x] Sistema de logs
- [x] Remover `except: pass`
- [x] Catálogo/cache de programas
- [x] Centralizar interpretação no Core
- [x] Tratamento padronizado de resultados (classe Resultado)
- [x] Testes automatizados (20 testes)

### 🔴 Fase 1 — Estabilidade e Organização 🎉
- [x] Tudo concluído!

### 🟡 Fase 2 — Preparação para Crescimento 🎉
- [x] Sistema de intenções (core/intents/)
- [x] Configurações persistentes (dados/config.json)
- [x] Modo desenvolvedor
- [ ] DeepSeek API (aguardando crédito)

### 🟢 Fase 3 — Experiência do Usuário
- [ ] Correção inteligente de voz
- [ ] Histórico visual de conversas
- [ ] Atalho global Ctrl+Espaço
- [ ] Feedback sonoro

### 🔵 Fase 4 — Utilidade Real
- [ ] Memória contextual
- [ ] Agendamentos e lembretes
- [ ] Busca inteligente no computador
- [ ] Comandos compostos
- [ ] Central de conhecimento pessoal

### 🟣 Fase 5 — Escalabilidade
- [ ] Sistema de plugins
- [ ] Perfis de usuário
- [ ] Dashboard administrativo
- [ ] Camada de serviços
- [ ] Expandir cobertura de testes

### ⚫ Fase 6 — Avançado
- [ ] Palavra de ativação "Sumé"
- [ ] OCR e leitura de tela
- [ ] Automação de navegador
- [ ] Modo reunião
- [ ] Resumo automático do dia
- [ ] Multiagentes