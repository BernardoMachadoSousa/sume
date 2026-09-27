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
      
      if (res.dados) {
        ultimosResultados = res;
        if (isFullscreen) {
          document.getElementById('search-controls').style.display = 'flex';
        }
      }
      
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
    if (ultimosResultados && ultimosResultados.dados) {
      document.getElementById('search-controls').style.display = 'flex';
    }
  } else {
    app.classList.remove('fullscreen-mode');
    app.classList.add('widget-mode');
    document.getElementById('search-controls').style.display = 'none';
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

let ultimosResultados = null;

function aplicarFiltros() {
  if (!ultimosResultados || !ultimosResultados.dados) return;
  
  const tipo = document.getElementById('filter-type')?.value || 'todos';
  const ordenacao = document.getElementById('sort-by')?.value || 'relevancia';
  const minRel = (document.getElementById('relevancia-min')?.value || 0) / 100;
  
  document.getElementById('relevancia-min-display').textContent = 
    (document.getElementById('relevancia-min')?.value || 0) + '%';
  
  let resultados = JSON.parse(JSON.stringify(ultimosResultados.dados));
  
  if (tipo === 'notas') {
    resultados = { notas: resultados.notas || [] };
  } else if (tipo === 'arquivos') {
    resultados = { arquivos: resultados.arquivos || [] };
  }
  
  if (resultados.notas) {
    resultados.notas = resultados.notas.filter(n => n.relevancia >= minRel);
  }
  if (resultados.arquivos) {
    resultados.arquivos = resultados.arquivos.filter(a => a.relevancia >= minRel);
  }
  
  if (ordenacao === 'nome') {
    if (resultados.notas) resultados.notas.sort((a, b) => a.titulo.localeCompare(b.titulo));
    if (resultados.arquivos) resultados.arquivos.sort((a, b) => a.nome.localeCompare(b.nome));
  } else if (ordenacao === 'relevancia') {
    if (resultados.notas) resultados.notas.sort((a, b) => b.relevancia - a.relevancia);
    if (resultados.arquivos) resultados.arquivos.sort((a, b) => b.relevancia - a.relevancia);
  }
  
  historico[historico.length - 1].dados = resultados;
  renderizarHistorico();
}

function exportarResultados(formato) {
  if (!ultimosResultados || !ultimosResultados.dados) {
    alert('Nenhum resultado para exportar');
    return;
  }
  
  let conteudo = '';
  const dados = ultimosResultados.dados;
  
  if (formato === 'json') {
    conteudo = JSON.stringify(dados, null, 2);
  } else if (formato === 'csv') {
    const linhas = [];
    linhas.push('tipo,titulo/nome,relevancia,caminho');
    
    if (dados.notas) {
      dados.notas.forEach(n => {
        linhas.push(`nota,"${n.titulo}",${n.relevancia},"${n.caminho}"`);
      });
    }
    
    if (dados.arquivos) {
      dados.arquivos.forEach(a => {
        linhas.push(`arquivo,"${a.nome}",${a.relevancia},"${a.caminho}"`);
      });
    }
    
    conteudo = linhas.join('\n');
  } else if (formato === 'txt') {
    const linhas = [];
    linhas.push('='.repeat(70));
    linhas.push('RESULTADOS DE BUSCA');
    linhas.push('='.repeat(70));
    
    if (dados.notas) {
      linhas.push('\nNOTAS:');
      dados.notas.forEach(n => {
        linhas.push(`- ${n.titulo} (${Math.round(n.relevancia * 100)}%)`);
      });
    }
    
    if (dados.arquivos) {
      linhas.push('\nARQUIVOS:');
      dados.arquivos.forEach(a => {
        linhas.push(`- ${a.nome} (${Math.round(a.relevancia * 100)}%)`);
      });
    }
    
    conteudo = linhas.join('\n');
  }
  
  const blob = new Blob([conteudo], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `resultados_busca_${Date.now()}.${formato === 'json' ? 'json' : formato === 'csv' ? 'csv' : 'txt'}`;
  a.click();
  URL.revokeObjectURL(url);
}

// ── TOUCH GESTURES PARA MOBILE ──

class TouchGestureDetector {
  constructor(element) {
    this.element = element;
    this.touchStartX = 0;
    this.touchStartY = 0;
    this.touchEndX = 0;
    this.touchEndY = 0;
    this.minSwipeDistance = 50;
    
    this.element.addEventListener('touchstart', e => this.onTouchStart(e), false);
    this.element.addEventListener('touchend', e => this.onTouchEnd(e), false);
  }
  
  onTouchStart(e) {
    this.touchStartX = e.changedTouches[0].screenX;
    this.touchStartY = e.changedTouches[0].screenY;
  }
  
  onTouchEnd(e) {
    this.touchEndX = e.changedTouches[0].screenX;
    this.touchEndY = e.changedTouches[0].screenY;
    this.handleGesture();
  }
  
  handleGesture() {
    const diffX = this.touchStartX - this.touchEndX;
    const diffY = this.touchStartY - this.touchEndY;
    
    if (Math.abs(diffX) > Math.abs(diffY)) {
      if (Math.abs(diffX) > this.minSwipeDistance) {
        if (diffX > 0) {
          this.onSwipeLeft();
        } else {
          this.onSwipeRight();
        }
      }
    }
  }
  
  onSwipeLeft() {
    if (isFullscreen && document.getElementById('search-controls')) {
      document.getElementById('search-controls').style.display = 'none';
    }
  }
  
  onSwipeRight() {
    if (isFullscreen && document.getElementById('search-controls')) {
      document.getElementById('search-controls').style.display = 'flex';
    }
  }
}

function inicializarTouchGestures() {
  if (window.innerWidth <= 768) {
    new TouchGestureDetector(document.getElementById('app'));
  }
}

function otimizarParaMobile() {
  if (window.innerWidth <= 768) {
    document.body.style.overflow = 'hidden';
    document.documentElement.style.overflow = 'hidden';
    
    if (cmdInput) {
      cmdInput.addEventListener('focus', () => {
        setTimeout(() => {
          window.scrollTo(0, document.body.scrollHeight);
        }, 200);
      });
    }
    
    const historyEl = document.getElementById('history');
    if (historyEl) {
      const observer = new MutationObserver(() => {
        historyEl.scrollTop = historyEl.scrollHeight;
      });
      observer.observe(historyEl, { childList: true });
    }
  }
}

window.addEventListener('load', () => {
  inicializarTouchGestures();
  otimizarParaMobile();
});

window.addEventListener('resize', () => {
  if (window.innerWidth <= 768) {
    otimizarParaMobile();
  }
});
