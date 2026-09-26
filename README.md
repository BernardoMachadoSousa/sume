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

### Detecção de fala (VAD)

`utils/voz_vad.py` decide frame a frame de 30ms o que é fala, e a captura em
`utils/escuta.py` usa isso para parar no silêncio em vez de gravar um tempo fixo.
Não depende de `webrtcvad` (que não tem wheel para Python 3.14) — só de NumPy, que já
vinha no projeto.

A decisão combina quatro coisas:

| Sinal | O que separa | Pega |
|---|---|---|
| RMS vs percentil 15 da própria gravação | ruído da fala, sem limiar fixo |Volume e zumbido |
| Coeficiente de variação do RMS | silêncio de ruído de frase contínua | Ventilador, fonte |
| ZCR (trocas de sinal) | grave de chiado | Zumbido de 50/60Hz |
| Planura espectral | grave de chiado branco | Chiado de alta frequência |

Depois disso há histerese: 3 frames seguidos de fala abrem a janela (90ms) e
**10 frames de silêncio contínuo fecham** (0.30s). Esse 0.30s é o número mais
delicado do arquivo — sem ele os vales do envelope de sílabas picavam a frase em
seis trechos, e nenhum dos trechos contava como fala.

`dados/config.json` controla a captura:

| Chave | Padrão | Efeito |
|---|---|---|
| `tempo_escuta_max` | `15` | Teto de gravação, em segundos |
| `silencios_para_parar` | `1.2` | Silêncio contínuo que encerra a captura |

Para testar com áudio sintético, sem microfone:

```bash
python testes/teste_vad.py
```

Para testar com o seu microfone de verdade, e ver o que o VAD decidiu:

```bash
python testes/diagnostico_pipeline.py
```

Esse segundo salva `diag_bruto.wav`, `diag_cortado.wav` e `diag_resample.wav`
para você ouvir o que foi capturado.

---

## 4b. IA conversacional: local ou OmniRoute

Por padrão o Sumé responde **local**, com o `phi3:mini` no Ollama. Nada sai da sua
máquina. O OmniRoute (gateway com Claude, Gemini e Nemotron) é **opt-in**.

Para ligar, defina a chave no ambiente e peça por voz:

```bash
# no terminal, antes de abrir o Sumé
set OMNIROUTE_API_KEY=sk-sua-chave-aqui
```

```
"usar omniroute"     # passa a responder pelo gateway
"usar ollama"        # volta para o local
"qual modelo"        # mostra qual está respondendo agora
```

Se o gateway estiver fora do ar ou faltar a chave, o Sumé cai no Ollama sozinho e não
derruba a conversa.

### O que vai para o modelo remoto

Nada, por padrão. Quando o OmniRoute está ligado, ainda assim o prompt vai só com a
instrução de papel: **nem o seu nome, nem a memória, nem o histórico** são enviados.
Para liberar isso de propósito:

```json
"compartilhar_contexto_omniroute": true
```

Ligado, o modelo remoto passa a receber nome, memórias e histórico recente. Vale
lembrar que aí o conteúdo sai da máquina.

Chaves de configuração:

| Chave | Padrão | Para que serve |
| --- | --- | --- |
| `usar_omniroute` | `false` | Liga o gateway remoto |
| `modelo_omniroute` | `SUME-CLAUDE` | Combo usado no gateway |
| `endpoint_omniroute` | `http://localhost:20128/v1` | Endereço do gateway |
| `compartilhar_contexto_omniroute` | `false` | Autoriza enviar nome/memória/histórico |
| `timeout_omniroute` | `120` | Segundos até desistir do gateway |

A chave nunca fica no código: ela vem de `OMNIROUTE_API_KEY` no ambiente.

---

## 4c. Memória em camadas e vault

### Memória: três camadas

Falar com o Sumé já guarda coisa, sem precisar de comando nenhum. A camada é deduzida
do que você disse:

| Camada | Vale | Como pedir |
| --- | --- | --- |
| `sessao` | Some quando o Sumé fecha, não vai para o disco | `"anote que X só nesta sessão"` |
| `curta` | Dura 7 dias e expira sozinho | `"anote que X por alguns dias"` (padrão) |
| `permanente` | Não expira | `"anote que X sempre"` |

```
"anote que eu prefiro café sem açúcar"
"anote que estou de folga por alguns dias"
"anote que meu visto vence sempre"
"o que você sabe sobre mim"
"esqueça que eu prefiro café sem açúcar"
```

O que vence o prazo é apagado sozinho na próxima leitura — não precisa de manutenção.

### Vault: notas em Markdown

O vault são arquivos `.md` de verdade, em `dados/vault/`, no formato do Obsidian. Dá
para abrir a pasta no seu editor, versionar no git ou sincronizar na mão.

```
"anote no vault que a reunião de sexta é às 10h"
```

O vault **não** vai para o prompt por padrão: ele é justamente o que costuma ser
sensible. Ele só entra no contexto quando o chamador pede, e o chamador precisa estar
com `compartilhar_contexto_omniroute` ligado.

Para testar as duas coisas sem microfone, rede nem Ollama:

```bash
python testes/teste_memoria.py
```

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
│   ├── memoria.py           # Memória em camadas (sessão/curta/permanente)
│   ├── vault.py             # Notas em Markdown (formato Obsidian)
│   ├── automacoes.py        # Abrir/fechar apps e sites
│   └── ia_conversacional.py # Conversa: Ollama local ou OmniRoute
├── utils/
│   ├── voz.py               # Síntese de fala (Edge TTS)
│   ├── escuta.py            # Captura adaptativa + transcrição (Whisper)
│   ├── voz_vad.py           # VAD de voz por frames de 30ms
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
- [x] VAD por frames (30ms) em `utils/voz_vad.py` — rms relativo ao ruído da
      própria gravação, ZCR, planura espectral e histerese
- [x] Captura adaptativa: para no silêncio (`silencios_para_parar`) em vez de
      gravar tempo fixo
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
- [x] 53 testes do VAD, incluindo a parada antecipada com stream falso

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