# ⚡ Sumé — Guia para Desenvolvedores

Este documento é para os integrantes da equipe. Siga as instruções abaixo antes de começar a programar.

---

# 🚀 Primeira configuração

## 1. Instalar ferramentas

### Python

https://python.org

⚠️ Durante a instalação marque:

```text
Add Python to PATH
```

### Git

https://git-scm.com/downloads/win

### VS Code

https://code.visualstudio.com

---

## 2. Baixar o projeto

Abra o CMD e execute:

```bash
git clone https://github.com/BernardoMachadoSousa/sume.git
cd sume
```

---

## 3. Criar ambiente virtual

```bash
python -m venv venv
venv\Scripts\activate
```

---

## 4. Instalar dependências

```bash
pip install -r requirements.txt
```

---

## 5. Baixar o modelo de voz

Acesse:

https://alphacephei.com/vosk/models

Baixe:

```text
vosk-model-small-pt-0.3.zip
```

Extraia para dentro da pasta do projeto.

Renomeie a pasta para:

```text
modelo_voz
```

---

## 6. Criar arquivo de configuração

```bash
mkdir dados
echo {"gemini_api_key": ""} > dados\configuracoes.json
```

---

## 7. Rodar o projeto

```bash
python main.py
```

---

# 📁 Onde alterar cada coisa

```text
main.py
```

Inicialização do sistema.

---

```text
core/nexus_core.py
```

Interpretação dos comandos.

---

```text
modulos/memoria.py
```

Sistema de memória.

---

```text
modulos/automacoes.py
```

Abrir e fechar programas, sites e automações.

---

```text
modulos/ia_conversacional.py
```

Integração com IA.

---

```text
utils/voz.py
```

Sistema de fala.

---

```text
utils/escuta.py
```

Reconhecimento de voz.

---

```text
interface/index.html
```

Estrutura da interface.

---

```text
interface/assets/style.css
```

Visual da interface.

---

```text
interface/assets/script.js
```

Comportamento da interface.

---

# 🔄 Fluxo obrigatório antes de programar

Sempre execute:

```bash
git pull
```

Isso garante que você está com a versão mais recente.

---

# ✅ Depois de fazer alterações

Teste tudo antes.

Se estiver funcionando:

```bash
git add .
git commit -m "Descrição da alteração"
git push
```

Exemplo:

```bash
git commit -m "Adicionado comando para abrir calculadora"
```

---

# ⚠️ Antes de alterar qualquer coisa

Avise no grupo:

```text
Vou trabalhar no módulo de memória.
```

ou

```text
Vou alterar a interface.
```

Assim evitamos conflitos.

---

# 🚫 Não alterar sem avisar

Arquivos críticos:

```text
main.py
dados/configuracoes.json
core/nexus_core.py
```

Se precisar alterar, avise no grupo antes.

---

# 🤝 Regras da equipe

1. Sempre fazer git pull antes de começar.
2. Avisar no grupo o módulo que será alterado.
3. Testar antes de fazer push.
4. Não enviar código quebrado.
5. Commits em português e objetivos.
6. Fazer uma alteração por vez.
7. Em caso de dúvida, perguntar antes de modificar.

---

# ❗ Problemas comuns

### pip não é reconhecido

Reinstale o Python marcando:

```text
Add Python to PATH
```

---

### Não consegue ativar a venv

Use CMD.

Não use PowerShell.

---

### ModuleNotFoundError

Instale o módulo faltante:

```bash
pip install nome-do-modulo
```

---

### modelo_voz não encontrado

Verifique se existe:

```text
sume/modelo_voz/
```

---

# 👥 Equipe

* Bernardo Machado Sousa 
* Gabriel Almeida Carvalho
* Matheus Torquato Gomes
