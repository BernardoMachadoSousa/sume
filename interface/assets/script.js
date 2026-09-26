/* ════════════════════════════════════════════════
   SUMÉ A.I. — SCRIPT.JS (GLASS UI)
   ════════════════════════════════════════════════ */

let isListening  = false;
let isProcessing = false;
let isFullscreen = false;

let historico = [];
const MAX_HIST = 200;

// Elementos
const app        = document.getElementById('app');
const circle     = document.getElementById('circle');
const statusText = document.getElementById('status-text');
const cmdInput   = document.getElementById('cmd-input');
const historyEl  = document.getElementById('history');

// Lembretes do Python
window._sume_lembrete = function(texto) {
  registrarTroca("🔔", texto, false);
};

function setCircleState(state) {
  circle.classList.remove('ready', 'listening', 'processing');
  circle.classList.add(state);
  
  const labels = {
    ready: 'Aguardando',
    listening: 'Ouvindo...',
    processing: 'Processando...'
  };
  statusText.textContent = labels[state] || '';
}

function toggleListening() {
  if (isProcessing) return;
  isListening = !isListening;
  
  if (isListening) {
    setCircleState('listening');
    if (window.pywebview) pywebview.api.ouvir_comando().then(onMicResult);
  } else {
    setCircleState('ready');
  }
}

function onMicResult(texto) {
  if (!texto || texto === "silencio") {
    isListening = false;
    setCircleState('ready');
    return;
  }
  isListening = false;
  enviarComando(texto);
}

function onInputKeydown(e) {
  if (e.key === 'Enter') onSendClick();
}

function onSendClick() {
  const texto = cmdInput.value.trim();
  if (!texto) return;
  cmdInput.value = '';
  enviarComando(texto);
}

function enviarComando(texto) {
  if (isProcessing) return;
  isProcessing = true;
  setCircleState('processing');

  // Adiciona a pergunta do usuário na UI logo de cara
  registrarTroca(texto, null, false);
  
  if (window.pywebview) {
    pywebview.api.processar_comando_info(texto).then(res => {
      // Atualiza o histórico com a resposta do Sumé
      historico[historico.length - 1].sume = res.resposta;
      historico[historico.length - 1].erro = res.erro;
      
      isProcessing = false;
      setCircleState('ready');
      renderizarHistorico();
      atualizarDevTools();
    }).catch(err => {
      historico[historico.length - 1].sume = "Erro de conexão com o núcleo.";
      historico[historico.length - 1].erro = true;
      isProcessing = false;
      setCircleState('ready');
      renderizarHistorico();
    });
  } else {
    // Modo Web puro (Teste)
    setTimeout(() => {
      historico[historico.length - 1].sume = "Mock de resposta local.";
      isProcessing = false;
      setCircleState('ready');
      renderizarHistorico();
    }, 1500);
  }
}

function registrarTroca(userText, sumeText, isError) {
  historico.push({ user: userText, sume: sumeText, erro: isError });
  if (historico.length > MAX_HIST) historico.shift();
  renderizarHistorico();
}

function renderizarHistorico() {
  if (historico.length === 0) {
    historyEl.innerHTML = '<div class="empty-state">Inicie a conversa...</div>';
    return;
  }
  
  historyEl.innerHTML = '';
  historico.forEach(item => {
    // User bubble
    if (item.user && item.user !== '🔔') {
      const u = document.createElement('div');
      u.className = 'msg user';
      u.textContent = item.user;
      historyEl.appendChild(u);
    } else if (item.user === '🔔') {
       // Apenas visual para lembretes
    }

    // Sumé bubble
    if (item.sume) {
      const s = document.createElement('div');
      s.className = `msg sume ${item.erro ? 'error' : ''}`;
      // Tratamento muito básico para markdown bold/italic (pode melhorar)
      s.innerHTML = item.sume
        .replace(/&/g, '&amp;').replace(/</g, '&lt;') // escape tag
        .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')
        .replace(/\*(.*?)\*/g, '<i>$1</i>')
        .replace(/\n/g, '<br>');
      historyEl.appendChild(s);
    }
  });

  // Scroll to bottom
  historyEl.scrollTop = historyEl.scrollHeight;
}

// ── JANELA E MODO DEV ──

function toggleFullscreen() {
  isFullscreen = !isFullscreen;
  if (isFullscreen) {
    app.classList.remove('widget-mode');
    app.classList.add('fullscreen-mode');
  } else {
    app.classList.remove('fullscreen-mode');
    app.classList.add('widget-mode');
  }
  atualizarDevTools();
}

function minimizarJanela() { if(window.pywebview) pywebview.api.minimizar(); }
function fecharJanela()    { if(window.pywebview) pywebview.api.fechar(); }

function atualizarDevTools() {
  if(!window.pywebview) return;
  // Painel lateral
  pywebview.api.ver_memorias().then(itens => {
    const ml = document.getElementById('memory-list');
    if(!itens || itens.length === 0) {
      ml.innerHTML = '<div class="mem-val">Nada na memória.</div>';
      return;
    }
    ml.innerHTML = itens.map(i => `
      <div class="mem-item">
        <div class="mem-key">${i.chave} <span class="mem-tag">${i.camada}</span></div>
        <div class="mem-val">${i.valor}</div>
      </div>
    `).join('');
  });

  // Confiança
  pywebview.api.ultima_intencao().then(uit => {
    if(uit && uit.intent) {
      document.getElementById('confidence').textContent = `[${uit.intent} : ${uit.confianca}]`;
    }
  });
}

// Teclas Globais na Janela (atalhos)
window.addEventListener('keydown', e => {
  if (e.ctrlKey && e.code === 'Space') {
    e.preventDefault();
    toggleListening();
  }
});
