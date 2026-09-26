/* ════════════════════════════════════════════════
   NEXUS — script.js
   ════════════════════════════════════════════════ */

// ── ESTADO ──────────────────────────────────────
let isListening   = false;
let isProcessing  = false;
let isFullscreen  = false;

// Histórico da conversa (sessão): {usuario, sume, erro}
let historico = [];
const HISTORICO_MAXIMO = 200;

// ── ELEMENTOS ───────────────────────────────────
const app        = document.getElementById('app');
const circle     = document.getElementById('circle');
const statusText = document.getElementById('status-text');
const cmdInput   = document.getElementById('cmd-input');
const btnExpand  = document.getElementById('btn-expand');
const historyEl  = document.getElementById('history');

// ════════════════════════════════════════════════
// ESTADO DO CÍRCULO
// ════════════════════════════════════════════════

function setCircleState(state) {
  // state: 'ready' | 'listening' | 'processing'
  circle.classList.remove('ready', 'listening', 'processing');
  circle.classList.add(state);

  const labels = {
    ready:      'Pronto',
    listening:  'Ouvindo...',
    processing: 'Processando...',
  };
  statusText.textContent = labels[state] || '';
}

// ════════════════════════════════════════════════
// MICROFONE / VOZ
// ════════════════════════════════════════════════

// ════════════════════════════════════════════════
// MICROFONE / VOZ (Push-to-Talk + VAD)
// ════════════════════════════════════════════════

let pushToTalkActive = false;

async function startListening() {
  if (isProcessing || isListening) return;

  isListening = true;
  setCircleState('listening');

  try {
    let texto = '';
    if (window.pywebview) {
      texto = await window.pywebview.api.ouvir_comando();
    } else {
      await delay(2000);
      texto = 'comando de teste';
    }

    if (texto && texto.trim()) {
      await enviarComando(texto.trim());
    } else {
      showStatus('Não entendi', 1800);
    }
  } catch (err) {
    console.error('Erro ao ouvir:', err);
    showStatus('Erro ao ouvir', 1800);
  } finally {
    isListening = false;
    pushToTalkActive = false;
    setCircleState('ready');
  }
}

function toggleListening() {
  if (pushToTalkActive) return;
  startListening();
}

// ════════════════════════════════════════════════
// ENVIAR COMANDO (voz ou texto)
// ════════════════════════════════════════════════

async function enviarComando(comando) {
  if (!comando || isProcessing) return;

  isProcessing = true;
  setCircleState('processing');
  cmdInput.value = '';

  try {
    let resposta = '';
    let ehErro = false;
    if (window.pywebview) {
      const info = await window.pywebview.api.processar_comando_info(comando);
      resposta = (info && info.resposta) ? info.resposta : '';
      ehErro = !!(info && info.erro);
    } else {
      // fallback de desenvolvimento
      await delay(1800);
      resposta = `Resposta para: "${comando}"`;
    }

    registrarTroca(comando, resposta, ehErro);
    renderizarHistorico();
    atualizarPainelMemoria();
    atualizarConfianca();
  } catch (err) {
    console.error('Erro ao processar:', err);
    registrarTroca(comando, 'Erro ao processar o comando.', true);
    renderizarHistorico();
    showStatus('Erro ao processar', 2000);
  } finally {
    isProcessing = false;
    setCircleState('ready');
  }
}

// ════════════════════════════════════════════════
// INPUT DE TEXTO
// ════════════════════════════════════════════════

function onInputKeydown(e) {
  if (e.key === 'Enter') {
    const val = cmdInput.value.trim();
    if (val) enviarComando(val);
  }
}

function onSendClick() {
  const val = cmdInput.value.trim();
  if (val) enviarComando(val);
}

// ════════════════════════════════════════════════
// HISTÓRICO DA CONVERSA (Etapa 4)
// ════════════════════════════════════════════════

function registrarTroca(usuario, sume, ehErro) {
  historico.push({ usuario: usuario, sume: sume, erro: ehErro });
  if (historico.length > HISTORICO_MAXIMO) {
    historico.splice(0, historico.length - HISTORICO_MAXIMO);
  }
}

function renderizarHistorico() {
  const visiveis = isFullscreen ? historico : historico.slice(-3);
  const html = [];
  for (const item of visiveis) {
    html.push(
      '<div class="msg usuario">você · ' + escapar(item.usuario) + '</div>',
      '<div class="msg sume' + (item.erro ? ' erro' : '') + '">sumé · ' +
        escapar(item.sume || '') + '</div>'
    );
  }
  historyEl.innerHTML = html.join('');
  historyEl.scrollTop = historyEl.scrollHeight;
}

function escapar(texto) {
  return String(texto).replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[c]);
}

// ════════════════════════════════════════════════
// PAINEL DE MEMÓRIA + INDICADOR DE CONFIANÇA (Etapa 4)
// ════════════════════════════════════════════════

async function atualizarPainelMemoria() {
  if (!window.pywebview) return;
  try {
    const itens = await window.pywebview.api.ver_memorias();
    const lista = document.getElementById('memory-list');
    if (!itens || itens.length === 0) {
      lista.innerHTML = '<div class="mem-vazio">Nada guardado ainda.</div>';
      return;
    }
    const rotulos = { sessao: 'SESSÃO', curta: 'CURTA', permanente: 'PERM' };
    const html = [];
    for (const item of itens) {
      const tag = rotulos[item.camada] || item.camada;
      html.push(
        '<div class="mem-item">' +
          '<span class="mem-tag ' + String(tag).toLowerCase() + '">' + tag + '</span>' +
          '<span class="mem-text">' +
            '<b>' + escapar(item.chave) + '</b> = ' + escapar(item.valor) +
          '</span></div>'
      );
    }
    lista.innerHTML = html.join('');
  } catch (err) {
    console.error('Erro ao buscar memórias:', err);
  }
}

async function atualizarConfianca() {
  if (!window.pywebview) return;
  try {
    const info = await window.pywebview.api.ultima_intencao();
    const el = document.getElementById('confidence');
    if (info && info.intent) {
      const conf = (typeof info.confianca === 'number')
        ? ' | confiança: ' + info.confianca.toFixed(2)
        : '';
      el.textContent = '[intent: ' + info.intent + conf + ']';
      el.classList.add('visivel');
    } else {
      el.textContent = '';
      el.classList.remove('visivel');
    }
  } catch (err) {
    console.error('Erro ao buscar intenção:', err);
  }
}

function showStatus(texto, duracao = 1800) {
  statusText.textContent = texto;
  setTimeout(() => {
    if (!isListening && !isProcessing) {
      statusText.textContent = 'Pronto';
    }
  }, duracao);
}

// ════════════════════════════════════════════════
// JANELA — EXPANDIR / MINIMIZAR / FECHAR
// ════════════════════════════════════════════════

function toggleFullscreen() {
  isFullscreen = !isFullscreen;
  app.classList.toggle('widget-mode',     !isFullscreen);
  app.classList.toggle('fullscreen-mode',  isFullscreen);
  btnExpand.innerHTML = isFullscreen ? '&#10064;' : '&#9633;';
  btnExpand.title     = isFullscreen ? 'Restaurar' : 'Expandir';
  renderizarHistorico();
  atualizarPainelMemoria();
  atualizarConfianca();
}

function minimizarJanela() {
  if (window.pywebview) {
    window.pywebview.api.minimizar();
  }
}

function fecharJanela() {
  if (window.pywebview) {
    window.pywebview.api.fechar();
  } else {
    window.close();
  }
}


// ════════════════════════════════════════════════
// TECLAS GLOBAIS + PUSH-TO-TALK
// ════════════════════════════════════════════════

document.addEventListener('keydown', (e) => {
  // ESC: sair da tela cheia ou minimizar
  if (e.key === 'Escape') {
    e.preventDefault();
    if (isFullscreen) {
      toggleFullscreen();
    } else {
      minimizarJanela();
    }
    return;
  }

  // Espaço: push-to-talk (segurar para falar)
  if (e.key === ' ' && !isProcessing && !isListening && !pushToTalkActive) {
    e.preventDefault();
    const inputFocado = document.activeElement === cmdInput;
    if (!inputFocado) {
      pushToTalkActive = true;
      startListening();
    }
  }
});

// ════════════════════════════════════════════════
// INICIALIZAÇÃO
// ════════════════════════════════════════════════

function init() {
  setCircleState('ready');

  if (window.pywebview) {
    atualizarPainelMemoria();
  }

  // Pulso de boas-vindas — pisca uma vez ao abrir
  setTimeout(() => {
    circle.style.boxShadow = '0 0 60px rgba(139, 92, 246, 0.7)';
    setTimeout(() => {
      circle.style.boxShadow = '';
    }, 600);
  }, 400);
}

// Aguarda PyWebView pronto (se existir) ou inicia direto
if (window.pywebview) {
  window.addEventListener('pywebviewready', init);
} else {
  document.addEventListener('DOMContentLoaded', init);
}

// ── UTILITÁRIO ──────────────────────────────────
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}