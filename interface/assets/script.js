/* ════════════════════════════════════════════════
   NEXUS — script.js
   ════════════════════════════════════════════════ */

// ── ESTADO ──────────────────────────────────────
let isListening   = false;
let isProcessing  = false;
let isFullscreen  = false;

// ── ELEMENTOS ───────────────────────────────────
const app        = document.getElementById('app');
const circle     = document.getElementById('circle');
const statusText = document.getElementById('status-text');
const cmdInput   = document.getElementById('cmd-input');
const btnExpand  = document.getElementById('btn-expand');

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

async function toggleListening() {
  if (isProcessing) return;
  if (isListening) return; // já está ouvindo, ignora novo clique

  isListening = true;
  setCircleState('listening');

  try {
    // Chama a API Python (PyWebView)
    // window.pywebview.api.ouvir_comando() deve retornar o texto reconhecido
    let texto = '';
    if (window.pywebview) {
      texto = await window.pywebview.api.ouvir_comando();
    } else {
      // fallback de desenvolvimento — simula delay
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
    setCircleState('ready');
  }
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
    if (window.pywebview) {
      resposta = await window.pywebview.api.processar_comando(comando);
    } else {
      // fallback de desenvolvimento
      await delay(1800);
      resposta = `Resposta para: "${comando}"`;
    }

    // Exibe a resposta brevemente no input (fade)
    if (resposta) {
      showResposta(resposta);
    }
  } catch (err) {
    console.error('Erro ao processar:', err);
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
// FEEDBACK VISUAL — RESPOSTA NO INPUT
// ════════════════════════════════════════════════

function showResposta(texto) {
  cmdInput.style.transition = 'opacity 0.2s';
  cmdInput.value = texto;
  cmdInput.style.opacity = '1';
  setTimeout(() => {
    cmdInput.style.opacity = '0.4';
    setTimeout(() => {
      cmdInput.value = '';
      cmdInput.style.opacity = '1';
    }, 2500);
  }, 100);
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
// TECLAS GLOBAIS
// ════════════════════════════════════════════════

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    if (isFullscreen) {
      toggleFullscreen();
    } else {
      minimizarJanela();
    }
  }
});

// ════════════════════════════════════════════════
// INICIALIZAÇÃO
// ════════════════════════════════════════════════

function init() {
  setCircleState('ready');

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