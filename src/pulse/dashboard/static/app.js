/* ============================================================
   Pulse Dashboard — app.js
   Main application logic, routing, WebSocket, data display
   ============================================================ */

const App = (() => {
  let ws = null;
  let currentView = 'home';
  let pollInterval = null;
  let exchangeStatuses = {};

  // ---------- Init ----------
  async function init() {
    setupNavigation();
    setupBacktestForm();
    setupSettings();
    await loadSettings();
    await connectWS();
    startPolling();
    showView('home');
  }

  // ---------- Navigation ----------
  function setupNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
      item.addEventListener('click', e => {
        e.preventDefault();
        const view = item.dataset.view;
        showView(view);
      });
    });
    document.getElementById('menuToggle')?.addEventListener('click', () => {
      document.getElementById('sidebar').classList.toggle('open');
    });
  }

  function showView(view) {
    currentView = view;
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.getElementById(`view-${view}`)?.classList.add('active');
    document.querySelectorAll('.nav-item').forEach(n => {
      n.classList.toggle('active', n.dataset.view === view);
    });
    document.getElementById('sidebar')?.classList.remove('open');
  }

  // ---------- WebSocket ----------
  async function connectWS() {
    updateConnectionStatus('connecting');
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    const wsUrl = `${proto}://${location.host}/api/ws/live`;
    try {
      ws = new WebSocket(wsUrl);
      ws.onopen = () => {
        updateConnectionStatus('connected');
        showToast('Connected to Pulse', 'success');
      };
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleMessage(data);
      };
      ws.onerror = () => updateConnectionStatus('disconnected');
      ws.onclose = () => {
        updateConnectionStatus('disconnected');
        setTimeout(connectWS, 3000);
      };
    } catch (e) {
      updateConnectionStatus('disconnected');
      setTimeout(connectWS, 3000);
    }
  }

  function handleMessage(data) {
    updateLastUpdate();
    if (data.type === 'orderbook' || data.type === 'ticker') {
      updateMarketCard(data);
      updateMarketsTable(data);
    } else if (data.type === 'signal') {
      addSignalCard(data);
    } else if (data.type === 'trade') {
      // optional trade feed
    }
  }

  function updateConnectionStatus(status) {
    const dot = document.querySelector('.status-dot');
    const text = document.querySelector('.status-text');
    dot.className = `status-dot ${status}`;
    const labels = { connected: 'Connected', disconnected: 'Disconnected', connecting: 'Connecting...' };
    text.textContent = labels[status] || status;
  }

  function updateLastUpdate() {
    const el = document.getElementById('lastUpdate');
    if (el) el.textContent = new Date().toLocaleTimeString();
  }

  // ---------- REST Polling Fallback ----------
  function startPolling() {
    pollInterval = setInterval(async () => {
      if (currentView === 'home') await loadHomeData();
      if (currentView === 'markets') await loadMarketsTable();
      if (currentView === 'signals') await loadSignals();
      if (currentView === 'news') await loadNews();
      if (currentView === 'settings') await loadSettings();
    }, 5000);
  }

  // ---------- REST API helpers ----------
  async function apiGet(path) {
    try {
      const resp = await fetch(`/api${path}`);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      return await resp.json();
    } catch (e) {
      console.error(`API ${path} failed:`, e);
      return null;
    }
  }

  async function apiPost(path, body) {
    try {
      const resp = await fetch(`/api${path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      return await resp.json();
    } catch (e) {
      console.error(`API POST ${path} failed:`, e);
      return null;
    }
  }

  // ---------- Home ----------
  async function loadHomeData() {
    const data = await apiGet('/markets/symbols');
    if (!data || !data.symbols) return;
    const grid = document.getElementById('homeCards');
    if (!grid) return;
    grid.innerHTML = data.symbols.map(s => `
      <div class="card" data-symbol="${s.symbol}" data-exchange="${s.exchange}">
        <div class="card-symbol">${s.symbol}</div>
        <div class="card-price">${formatPrice(s.price)}</div>
        <div class="card-change ${s.change_24h_pct >= 0 ? 'positive' : 'negative'}">
          ${s.change_24h_pct >= 0 ? '+' : ''}${s.change_24h_pct?.toFixed(2) || '0.00'}%
        </div>
        <div class="card-exchange">${s.exchange}</div>
      </div>
    `).join('');
    grid.querySelectorAll('.card').forEach(card => {
      card.addEventListener('click', () => {
        const symbol = card.dataset.symbol;
        const exchange = card.dataset.exchange;
        showToast(`Opening ${symbol} on ${exchange}...`, 'info');
      });
    });
  }

  function updateMarketCard(data) {
    // Update matching card in home view if visible
  }

  // ---------- Markets ----------
  let chart = null;
  let currentSymbol = null;

  async function loadMarketsTable() {
    const data = await apiGet('/markets/symbols');
    if (!data || !data.symbols) return;
    const tbody = document.getElementById('marketsBody');
    if (!tbody) return;
    tbody.innerHTML = data.symbols.map(s => `
      <tr data-symbol="${s.symbol}" data-exchange="${s.exchange}" class="market-row">
        <td><strong>${s.symbol}</strong></td>
        <td><span class="exchange-badge">${s.exchange}</span></td>
        <td>${formatPrice(s.price)}</td>
        <td class="${s.change_24h_pct >= 0 ? 'change-positive' : 'change-negative'}">
          ${s.change_24h_pct >= 0 ? '+' : ''}${s.change_24h_pct?.toFixed(2) || '0.00'}%
        </td>
        <td>${formatVolume(s.volume_24h)}</td>
        <td>${s.spread?.toFixed(2) ?? '--'} bps</td>
      </tr>
    `).join('');
    tbody.querySelectorAll('.market-row').forEach(row => {
      row.addEventListener('click', () => {
        const symbol = row.dataset.symbol;
        const exchange = row.dataset.exchange;
        openChart(symbol, exchange);
      });
    });
  }

  function openChart(symbol, exchange) {
    currentSymbol = symbol;
    const panel = document.getElementById('chartPanel');
    document.getElementById('chartSymbol').textContent = symbol;
    document.getElementById('chartExchange').textContent = exchange;
    panel.style.display = 'block';
    if (chart) chart.destroy();
    chart = new MiniChart('chartContainer');
    chart.setData(generateDemoCandles(symbol));
    showToast(`Loading chart for ${symbol}...`, 'info');
  }

  function generateDemoCandles(symbol) {
    const base = symbol.includes('BTC') ? 67000 : symbol.includes('ETH') ? 3500 : 170;
    const candles = [];
    let price = base;
    const now = Date.now();
    for (let i = 100; i >= 0; i--) {
      const open = price;
      const change = (Math.random() - 0.48) * base * 0.02;
      const close = open + change;
      const high = Math.max(open, close) + Math.random() * base * 0.005;
      const low = Math.min(open, close) - Math.random() * base * 0.005;
      candles.push({
        time: Math.floor((now - i * 3600000) / 1000),
        open, high, low, close,
        volume: Math.random() * 1000,
      });
      price = close;
    }
    return candles;
  }

  function updateMarketsTable(data) {
    // Live update single row when WS data arrives
  }

  // ---------- Signals ----------
  async function loadSignals() {
    const data = await apiGet('/signals/latest');
    if (!data || !data.signals) return;
    const grid = document.getElementById('signalsGrid');
    if (!grid) return;
    grid.innerHTML = data.signals.map(s => renderSignalCard(s)).join('');
  }

  function addSignalCard(signal) {
    const grid = document.getElementById('signalsGrid');
    if (!grid) return;
    const empty = grid.querySelector('.empty-state');
    if (empty) empty.remove();
    const div = document.createElement('div');
    div.innerHTML = renderSignalCard(signal);
    grid.prepend(div.firstElementChild);
  }

  function renderSignalCard(s) {
    const confidenceClass = s.confidence >= 0.7 ? 'high' : s.confidence >= 0.4 ? 'medium' : 'low';
    return `
      <div class="signal-card ${confidenceClass}">
        <div class="signal-header">
          <span class="signal-type">${s.strategy || s.signal_type}</span>
          <span class="signal-confidence confidence-${confidenceClass}">${Math.round(s.confidence * 100)}%</span>
        </div>
        <div class="signal-details">
          ${s.symbol} — ${s.direction || 'N/A'}
        </div>
        <div class="signal-meta">${new Date(s.timestamp).toLocaleString()}</div>
      </div>
    `;
  }

  // ---------- Backtest ----------
  function setupBacktestForm() {
    const form = document.getElementById('backtestForm');
    form?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = document.getElementById('runBacktest');
      btn.disabled = true;
      btn.textContent = 'Running...';
      const req = {
        symbol: document.getElementById('btSymbol').value,
        exchange: document.getElementById('btExchange').value,
        strategy: document.getElementById('btStrategy').value,
        start_date: document.getElementById('btStart').value,
        end_date: document.getElementById('btEnd').value,
        initial_capital: parseFloat(document.getElementById('btCapital').value),
        fill_model: document.getElementById('btFillModel').value,
        slippage_bps: parseFloat(document.getElementById('btSlippage').value),
      };
      const result = await apiPost('/backtest/run', req);
      btn.disabled = false;
      btn.textContent = 'Run Backtest';
      if (result && result.status === 'ok') {
        renderBacktestResults(result.metrics);
      } else {
        showToast(result?.error || 'Backtest failed', 'error');
      }
    });
  }

  function renderBacktestResults(metrics) {
    const container = document.getElementById('backtestResults');
    const grid = document.getElementById('metricsGrid');
    container.style.display = 'block';
    if (!metrics) {
      grid.innerHTML = '<div class="empty-state">No results</div>';
      return;
    }
    grid.innerHTML = Object.entries(metrics).map(([key, val]) => `
      <div class="metric-card">
        <div class="metric-label">${formatMetricLabel(key)}</div>
        <div class="metric-value">${val}</div>
      </div>
    `).join('');
  }

  // ---------- News ----------
  async function loadNews() {
    const source = document.querySelector('.filter-btn.active')?.dataset.source || 'all';
    const data = await apiGet(`/news/latest?source=${source}`);
    if (!data || !data.items) return;
    const list = document.getElementById('newsList');
    if (!list) return;
    list.innerHTML = data.items.map(item => `
      <div class="news-item" onclick="window.open('${item.url}', '_blank')">
        <span class="news-source ${item.source}">${item.source}</span>
        <div class="news-title">${item.title}</div>
        <div class="news-meta">${new Date(item.published_at).toLocaleString()}</div>
      </div>
    `).join('');
  }

  // ---------- Settings ----------
  async function loadSettings() {
    const data = await apiGet('/settings/');
    if (!data) return;
    const list = document.getElementById('exchangeList');
    if (list) {
      list.innerHTML = (data.exchanges || []).map(ex => `
        <div class="exchange-item">
          <span class="exchange-name">${ex.name}</span>
          <span class="exchange-status ${ex.enabled ? 'status-ok' : 'status-error'}">
            ${ex.enabled ? 'Enabled' : 'Disabled'}
          </span>
        </div>
      `).join('');
    }
  }

  function setupSettings() {
    document.getElementById('saveRetention')?.addEventListener('click', async () => {
      const days = parseInt(document.getElementById('retentionDays').value);
      const result = await apiPost('/settings/retention', { days });
      showToast(result?.status === 'ok' ? 'Retention updated' : 'Failed', result?.status === 'ok' ? 'success' : 'error');
    });
    document.getElementById('saveRefresh')?.addEventListener('click', async () => {
      const ms = parseInt(document.getElementById('refreshRate').value);
      showToast('Refresh rate saved (restart to apply)', 'success');
    });
    document.querySelectorAll('.filter-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        loadNews();
      });
    });
  }

  // ---------- Utilities ----------
  function formatPrice(p) {
    if (p == null) return '--';
    if (p >= 1000) return '$' + p.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    if (p >= 1) return '$' + p.toFixed(2);
    return '$' + p.toFixed(4);
  }

  function formatVolume(v) {
    if (v == null) return '--';
    if (v >= 1e9) return (v / 1e9).toFixed(2) + 'B';
    if (v >= 1e6) return (v / 1e6).toFixed(2) + 'M';
    if (v >= 1e3) return (v / 1e3).toFixed(2) + 'K';
    return v.toFixed(2);
  }

  function formatMetricLabel(key) {
    return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  }

  function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
  }

  // ---------- Boot ----------
  document.addEventListener('DOMContentLoaded', init);

  // Close chart panel
  document.getElementById('closeChart')?.addEventListener('click', () => {
    document.getElementById('chartPanel').style.display = 'none';
    if (chart) { chart.destroy(); chart = null; }
  });

  // Resize chart on window resize
  window.addEventListener('resize', () => { if (chart) chart.resize(); });

  return { init, showView };
})();
