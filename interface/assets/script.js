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

  registrarTroca(texto, null, false);
  
  if (window.pywebview) {
    pywebview.api.processar_comando_info(texto).then(res => {
      historico[historico.length - 1].sume = res.resposta;
      historico[historico.length - 1].erro = res.erro;
      historico[historico.length - 1].dados = res.dados || null;
      
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

function registrarTroca(userText, sumeText, isError, dados = null) {
  historico.push({ user: userText, sume: sumeText, erro: isError, dados: dados });
  if (historico.length > MAX_HIST) historico.shift();
  renderizarHistorico();
}

function renderizarResultadosBusca(dados) {
  const container = document.createElement('div');
  container.className = 'search-results';
  
  if (dados.notas) {
    const notasDiv = document.createElement('div');
    notasDiv.className = 'search-section';
    notasDiv.innerHTML = '<div class="search-title">Notas encontradas:</div>';
    
    dados.notas.slice(0, 5).forEach(nota => {
      const item = document.createElement('div');
      item.className = 'search-item nota-item';
      item.innerHTML = `
        <div class="search-item-title">${nota.titulo}</div>
        <div class="search-item-excerpt">${nota.trecho.substring(0, 150)}...</div>
        <div class="search-item-path">${nota.caminho}</div>
      `;
      notasDiv.appendChild(item);
    });
    container.appendChild(notasDiv);
  }
  
  if (dados.arquivos) {
    const arquivosDiv = document.createElement('div');
    arquivosDiv.className = 'search-section';
    arquivosDiv.innerHTML = '<div class="search-title">Arquivos encontrados:</div>';
    
    dados.arquivos.slice(0, 5).forEach(arquivo => {
      const item = document.createElement('div');
      item.className = 'search-item arquivo-item';
      const extensao = arquivo.nome.split('.').pop().toUpperCase();
      item.innerHTML = `
        <div class="search-item-header">
          <span class="file-icon">${extensao}</span>
          <div class="search-item-title">${arquivo.nome}</div>
        </div>
        <div class="search-item-excerpt">${arquivo.trecho.substring(0, 150)}...</div>
        <div class="search-item-path">${arquivo.caminho}</div>
      `;
      arquivosDiv.appendChild(item);
    });
    container.appendChild(arquivosDiv);
  }
  
  return container;
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

    // Resultados de busca (se houver)
    if (item.dados && (item.dados.notas || item.dados.arquivos)) {
      const resultsEl = renderizarResultadosBusca(item.dados);
      historyEl.appendChild(resultsEl);
    }

    // Sumé bubble
    if (item.sume) {
      const s = document.createElement('div');
      s.className = `msg sume ${item.erro ? 'error' : ''}`;
      s.innerHTML = item.sume
        .replace(/&/g, '&amp;').replace(/</g, '&lt;')
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
