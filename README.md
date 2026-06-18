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

## 4. Baixar modelo de voz (Vosk)

* Link direto: https://alphacephei.com/vosk/models/vosk-model-small-pt-0.3.zip
* Site com todos os modelos: https://alphacephei.com/vosk/models

Passos:

1. Extraia o `.zip` para dentro da pasta `sume`
2. Renomeie a pasta extraída para `modelo_voz`

Deve ficar assim: `C:\Users\seu-usuario\sume\modelo_voz\`

---

## 5. Criar arquivo de configuração

```bash
mkdir dados
echo {"gemini_api_key": ""} > dados\configuracoes.json
```

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
├── main.py                 # Inicia o app
├── requirements.txt        # Bibliotecas necessárias
├── core/
│   └── nexus_core.py       # Interpreta comandos
├── modulos/
│   ├── memoria.py          # Memória
│   ├── automacoes.py       # Abrir/fechar apps e sites
│   └── ia_conversacional.py # IA
├── utils/
│   ├── voz.py              # Fala
│   └── escuta.py           # Escuta
├── interface/
│   ├── index.html          # Tela
│   └── assets/
│       ├── style.css       # Visual
│       └── script.js       # Comportamento
└── dados/
    └── configuracoes.json  # Chaves
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

1. **Sempre faça **``** antes de começar**
2. Avise no WhatsApp o que vai mexer
3. Teste antes de dar `git push`
4. Não mexa no `main.py` ou `dados/configuracoes.json` sem avisar
5. Commits em português, objetivos: `"Adicionei comando de clima"`

---

## ❗ Problemas comuns

| Erro                        | Solução                                   |
| --------------------------- | ----------------------------------------- |
| `pip não é reconhecido`     | Reinstale o Python marcando "Add to PATH" |
| PowerShell não ativa venv   | Use o **CMD**, não o PowerShell           |
| `ModuleNotFoundError`       | `pip install nome-do-modulo`              |
| `modelo_voz não encontrado` | O modelo Vosk não está na pasta correta   |

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
- [x] VAD (detecção de silêncio)
- [x] Push-to-talk (segurar Espaço)
- [x] SQLite (substituiu JSON)
- [x] Automações inteligentes (abrir/fechar programas)
- [x] Pré-carregamento do Whisper
- [x] Atalhos de desenvolvimento

---

## 📋 Tarefas do Sumé

### ✅ Concluído
- [x] Edge TTS (voz natural Antônio)
- [x] Ollama + Phi-3 Mini (IA local)
- [x] Whisper (reconhecimento de voz)
- [x] VAD (detecção de silêncio)
- [x] Push-to-talk (segurar Espaço)
- [x] SQLite (substituiu JSON)
- [x] Automações inteligentes (abrir/fechar programas)
- [x] Pré-carregamento do Whisper
- [x] Atalhos de desenvolvimento
- [x] Corrigir inconsistência `nome` vs `nome_usuario`
- [x] Sistema de logs (comandos, intents, resultados, erros)
- [x] Remover `except: pass` (tratamento com log)
- [x] Catálogo/cache de programas (Menu Iniciar)
- [x] Centralizar interpretação no Core
- [x] Tratamento padronizado de resultados (classe Resultado)
- [x] Testes automatizados (20 testes, abre e fecha tudo)

### 🔴 Fase 1 — Estabilidade e Organização
- [x] Tudo concluído! 🎉

### 🟡 Fase 2 — Preparação para Crescimento
- [ ] Sistema de intenções (core/intents/)
- [ ] Configurações persistentes (dados/config.json)
- [ ] Modo desenvolvedor
- [ ] DeepSeek API como IA 

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
- [ ] Testes automatizados (expandir cobertura)

### ⚫ Fase 6 — Avançado
- [ ] Palavra de ativação "Sumé"
- [ ] OCR e leitura de tela
- [ ] Automação de navegador
- [ ] Modo reunião
- [ ] Resumo automático do dia
- [ ] Multiagentes
