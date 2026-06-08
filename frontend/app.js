/**
 * app.js — Value Analyst SPA
 * Single Page Application for Value Investing fundamental analysis.
 * Hash-based routing, REST API communication, dynamic rendering.
 */

// ─── Configuration ──────────────────────────────────────────────
const API_BASE = window.location.origin + '/api';

// ─── State ──────────────────────────────────────────────────────
const state = {
  currentPage: 'dashboard',
  activePortfolioTab: 'portfolio',
  portfolio: [],
  currentDetail: null,
  explorerResults: [],
  isLoading: false,
  isUpdating: false,
  isExploring: false,
  compareTickers: [],
  token: localStorage.getItem('token') || null,
  role: localStorage.getItem('role') || 'user',
  username: localStorage.getItem('username') || '',
  authMode: 'login' // 'login' or 'register'
};

// ─── Utility Helpers ────────────────────────────────────────────

function formatNumber(num, decimals = 2) {
  if (num === null || num === undefined || isNaN(num)) return '—';
  return Number(num).toFixed(decimals);
}

const CURRENCY_SYMBOLS = {
  USD: '$', EUR: '€', GBP: '£', JPY: '¥', CNY: '¥', CHF: 'Fr.',
  CAD: 'C$', AUD: 'A$', HKD: 'HK$', SGD: 'S$', NZD: 'NZ$',
  SEK: 'kr', NOK: 'kr', DKK: 'kr', ISK: 'kr',
  KRW: '₩', TWD: 'NT$', INR: '₹', BRL: 'R$', MXN: 'MX$',
  ZAR: 'R', TRY: '₺', PLN: 'zł', CZK: 'Kč', HUF: 'Ft',
  ILS: '₪', THB: '฿', MYR: 'RM', IDR: 'Rp', PHP: '₱', VND: '₫',
  ARS: 'AR$', CLP: 'CL$', COP: 'CO$', PEN: 'S/.',
};

function getCurrencySymbol(code) {
  return CURRENCY_SYMBOLS[(code || 'USD').toUpperCase()] || (code || '$') + ' ';
}

function formatCurrency(num, currencyCode) {
  if (num === null || num === undefined || isNaN(num)) return '—';
  const sym = getCurrencySymbol(currencyCode);
  return sym + Number(num).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatLargeNumber(num) {
  if (num === null || num === undefined || isNaN(num)) return '—';
  const abs = Math.abs(num);
  if (abs >= 1e12) return (num / 1e12).toFixed(2) + 'T';
  if (abs >= 1e9) return (num / 1e9).toFixed(2) + 'B';
  if (abs >= 1e6) return (num / 1e6).toFixed(2) + 'M';
  if (abs >= 1e3) return (num / 1e3).toFixed(1) + 'K';
  return formatNumber(num);
}

function formatPercent(num) {
  if (num === null || num === undefined || isNaN(num)) return '—';
  return Number(num).toFixed(1) + '%';
}

function getMosBadgeClass(mos) {
  if (mos === null || mos === undefined) return 'badge--neutral';
  if (mos >= 20) return 'badge--positive';
  if (mos >= 0) return 'badge--neutral';
  return 'badge--negative';
}

function getMosColor(mos) {
  if (mos === null || mos === undefined) return 'var(--text-muted)';
  if (mos >= 30) return 'var(--color-success)';
  if (mos >= 20) return '#4ade80';
  if (mos >= 0) return 'var(--color-warning)';
  return 'var(--color-danger)';
}

function getTrendEmoji(trend) {
  const map = { '↑': '🟢 ↑', '↓': '🔴 ↓', '→': '🟡 →', '?': '⚪ ?' };
  return map[trend] || '⚪ ?';
}

function getSemaforoClass(status) {
  if (!status) return 'neutral';
  if (status.includes('STRONG BUY') || status.includes('CALIDAD') || status.includes('GROWTH BUY')) return 'strong-buy';
  if (status.includes('SOBREVALORADA') || status.includes('OVERPRICED')) return 'overvalued';
  if (status.includes('NO ELEGIBLE')) return 'no-eligible';
  if (status.includes('ALTO RIESGO')) return 'overvalued';
  return 'neutral';
}

function getSemaforoEmoji(status) {
  if (!status) return '⚪';
  if (status.includes('STRONG BUY') || status.includes('CALIDAD') || status.includes('GROWTH BUY')) return '🟢';
  if (status.includes('SOBREVALORADA') || status.includes('OVERPRICED')) return '🔴';
  if (status.includes('NO ELEGIBLE')) return '🚫';
  if (status.includes('ALTO RIESGO')) return '⚠️';
  return '🟡';
}

function getSemaforoMeaning(status) {
  if (!status) return 'No hay datos de valoración.';
  if (status.includes('STRONG BUY')) return 'Convergencia total. Empresa barata por fundamentales e históricamente.';
  if (status.includes('GROWTH BUY')) return 'Metodología Growth: PEG < 1.5 (infravalorada para su crecimiento) + Rule of 40 ≥ 40 (calidad tech premium).';
  if (status.includes('COMPRA DE CALIDAD')) return 'Caso Buffett: Empresa de extraordinaria calidad (Wide Moat y excelente directiva) cotizando a un precio razonable.';
  if (status.includes('GROWTH OVERPRICED')) return 'Growth sobrecomprado: PEG > 2.5 o Rule of 40 < 20. El mercado ya descuenta demasiado crecimiento futuro en el precio.';
  if (status.includes('GROWTH HOLD')) return 'Growth en rango intermedio. El PEG y Rule of 40 no confirman ni ganga ni burbuja. Vigilar evolución trimestral.';
  if (status.includes('SOBREVALORADA')) return 'Precio excesivo, alto riesgo de corrección por fundamentales y valoración histórica.';
  if (status.includes('NO ELEGIBLE')) return 'No elegible. Reportes no transparentes o EBITDA Ajustado manipulado (>30% de divergencia).';
  if (status.includes('ALTO RIESGO')) return 'Empresa sin beneficios y crecimiento insuficiente. Valoración especulativa con riesgo muy alto.';
  if (status.includes('SIN DATOS')) return 'Datos de crecimiento insuficientes para calcular métricas Growth fiables.';
  return 'Señal mixta o intermedia. Requiere análisis cualitativo profundo.';
}

// ─── API Calls ──────────────────────────────────────────────────

function getHeaders() {
  const headers = { 
    'Content-Type': 'application/json',
    'ngrok-skip-browser-warning': 'true'
  };
  if (state.token) headers['Authorization'] = `Bearer ${state.token}`;
  return headers;
}

function handleApiError(res) {
  if (res.status === 401) {
    logout();
    throw new Error('Sesión expirada o inválida. Por favor, inicia sesión de nuevo.');
  }
  if (!res.ok) throw new Error(`API Error ${res.status}`);
}

async function apiGet(path) {
  const res = await fetch(API_BASE + path, { headers: getHeaders() });
  handleApiError(res);
  return res.json();
}

async function apiPost(path, body = {}) {
  const res = await fetch(API_BASE + path, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(body),
  });
  handleApiError(res);
  return res.json();
}

async function apiDelete(path) {
  const res = await fetch(API_BASE + path, { 
    method: 'DELETE',
    headers: getHeaders()
  });
  handleApiError(res);
  return res.json();
}

// ─── Toast Notifications ────────────────────────────────────────

function showToast(message, type = 'info') {
  const toast = document.getElementById('toast');
  toast.textContent = message;
  toast.className = `toast toast--${type} active`;
  setTimeout(() => toast.classList.remove('active'), 3000);
}

// ─── Router ─────────────────────────────────────────────────────

function navigate(page, params = {}) {
  // Authentication Guard
  if (!state.token && page !== 'auth') {
    page = 'auth';
  } else if (state.token && page === 'auth') {
    page = 'dashboard';
  }

  // Admin Guard
  if (page === 'admin' && state.role !== 'admin') {
    page = 'dashboard';
  }

  state.currentPage = page;
  updateUserDisplay();
  
  // Update hash
  if (page === 'detail' && params.ticker) {
    window.location.hash = `#detail/${params.ticker}`;
  } else {
    window.location.hash = `#${page}`;
  }

  // Hide all pages
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  
  // Show target page
  const pageEl = document.getElementById(`page-${page}`);
  if (pageEl) {
    pageEl.classList.add('active');
    // Re-trigger animation
    pageEl.style.animation = 'none';
    pageEl.offsetHeight; // trigger reflow
    pageEl.style.animation = '';
  }

  // Update bottom nav (hide if auth)
  const bottomNav = document.querySelector('.bottom-nav');
  if (bottomNav) bottomNav.style.display = page === 'auth' ? 'none' : 'flex';
  
  // Show/Hide Admin Nav Button
  const adminNav = document.getElementById('nav-admin');
  if (adminNav) {
    adminNav.style.display = (state.token && state.role === 'admin') ? 'flex' : 'none';
  }

  // Update top nav actions (hide if auth)
  const topNavBtn = document.querySelector('.top-nav__btn');
  if (topNavBtn) topNavBtn.style.display = page === 'auth' ? 'none' : 'block';

  document.querySelectorAll('.bottom-nav__item').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.page === page);
  });

  // Load data for page
  if (page === 'dashboard') loadPortfolio();
  if (page === 'detail' && params.ticker) loadCompanyDetail(params.ticker);
  if (page === 'explore') { window.updateExploreChips && window.updateExploreChips(); }
  if (page === 'wiki') loadWiki();
  if (page === 'admin') loadAdminPanel();
  if (page === 'compare') loadComparePage();
}

function handleHashChange() {
  const hash = window.location.hash.replace('#', '') || 'dashboard';
  const parts = hash.split('/');
  
  if (parts[0] === 'detail' && parts[1]) {
    navigate('detail', { ticker: parts[1] });
  } else {
    navigate(parts[0]);
  }
}

// ─── Portfolio / Dashboard ──────────────────────────────────────

async function loadPortfolio() {
  const container = document.getElementById('portfolio-list');
  
  try {
    container.innerHTML = renderLoadingCards(3);
    const data = await apiGet('/portfolio');
    state.portfolio = data.portfolio || [];
    renderPortfolio();
  } catch (err) {
    container.innerHTML = renderEmptyState('🍊', 'Error de conexión', 'No se pudo conectar con el servidor. Verifica que el backend esté ejecutándose.');
  }
}

function switchPortfolioTab(tab) {
  state.activePortfolioTab = tab;
  document.getElementById('tab-btn-portfolio').classList.toggle('active', tab === 'portfolio');
  document.getElementById('tab-btn-watchlist').classList.toggle('active', tab === 'watchlist');
  renderPortfolio();
}

function renderPortfolio() {
  const container = document.getElementById('portfolio-list');
  const filteredPortfolio = state.portfolio.filter(item => item.list_type === state.activePortfolioTab);
  
  if (filteredPortfolio.length === 0) {
    container.innerHTML = renderEmptyState(
      '📦', 
      state.activePortfolioTab === 'portfolio' ? 'Cartera vacía' : 'Seguimiento vacío', 
      'Añade tickers para empezar a analizar empresas con criterios de inversión en valor.'
    );
    const scatterEl = document.getElementById('scatter-container');
    if (scatterEl) scatterEl.style.display = 'none';
    return;
  }

  let html = '';
  for (const item of filteredPortfolio) {
    const mosBadge = getMosBadgeClass(item.margen_seguridad);
    const mosText = item.margen_seguridad !== null ? formatPercent(item.margen_seguridad) : 'Sin datos';
    const archetypeShort = item.archetype_label ? item.archetype_label.split(' ')[0] : '';
    html += `
      <div class="card card--clickable" onclick="navigate('detail', {ticker: '${item.ticker}'})">
        <button class="portfolio-card__delete" onclick="event.stopPropagation(); removeTicker('${item.ticker}')" title="Eliminar">✕</button>
        <div class="portfolio-card">
          <div class="portfolio-card__info">
            <span class="portfolio-card__ticker">${getSemaforoEmoji(item.estado_semaforo)} ${item.ticker}</span>
            <span class="portfolio-card__name">${item.empresa || 'Cargando...'}</span>
            <span style="font-size: 0.65rem; color: var(--text-muted); margin-top: 2px;">${archetypeShort} ${item.sector ? '· ' + item.sector : ''}</span>
          </div>
          <div class="portfolio-card__metrics">
            <span class="portfolio-card__price">${item.precio_mercado ? formatCurrency(item.precio_mercado) : '—'}</span>
            <span class="portfolio-card__mos ${mosBadge}">MoS: ${mosText}</span>
            <span style="font-size: 0.62rem; color: var(--text-muted);">${item.calidad || ''}</span>
          </div>
        </div>
      </div>
    `;
  }
  container.innerHTML = html;

  // Render scatter plot if 2+ items with data
  const scatterEl = document.getElementById('scatter-container');
  const itemsWithData = state.portfolio.filter(p => p.roic_actual != null && p.margen_seguridad != null);
  if (scatterEl && itemsWithData.length >= 2) {
    scatterEl.style.display = 'block';
    setTimeout(renderScatterPlot, 100);
  } else if (scatterEl) {
    scatterEl.style.display = 'none';
  }
}

async function executeUpdate() {
  if (state.isUpdating) return;
  
  const btn = document.getElementById('btn-update');
  state.isUpdating = true;
  btn.classList.add('btn-update--loading');
  btn.innerHTML = '<span class="spinner"></span> Actualizando...';
  
  try {
    const data = await apiPost('/update');
    showToast(`✅ ${data.message}`, 'success');
    if (data.errors && data.errors.length > 0) {
      showToast(`⚠️ ${data.errors.length} errores`, 'error');
    }
    await loadPortfolio();
  } catch (err) {
    showToast('❌ Error al actualizar', 'error');
  } finally {
    state.isUpdating = false;
    btn.classList.remove('btn-update--loading');
    btn.innerHTML = '⚡ EJECUTAR UPDATE';
  }
}

// ─── Add / Remove Ticker ────────────────────────────────────────

function openAddModal() {
  document.getElementById('modal-add').classList.add('active');
  setTimeout(() => document.getElementById('input-ticker').focus(), 100);
}

function closeAddModal() {
  document.getElementById('modal-add').classList.remove('active');
  document.getElementById('input-ticker').value = '';
}

async function moveTickerList(ticker, newListType) {
  try {
    const data = await apiPatch(`/portfolio/${ticker}`, { list_type: newListType });
    if (data.error) {
      showToast(`⚠️ ${data.error}`, 'error');
    } else {
      showToast(`✅ ${ticker} movido a ${newListType === 'portfolio' ? 'Cartera' : 'Seguimiento'}`, 'success');
      loadPortfolio();
    }
  } catch (err) {
    showToast('❌ Error al mover ticker', 'error');
  }
}

async function addTicker() {
  const input = document.getElementById('input-ticker');
  const typeSelect = document.getElementById('input-list-type');
  const ticker = input.value.trim().toUpperCase();
  const list_type = typeSelect ? typeSelect.value : 'watchlist';
  if (!ticker) return;

  try {
    const data = await apiPost('/portfolio', { ticker, list_type });
    if (data.error) {
      showToast(`⚠️ ${data.error}`, 'error');
    } else {
      showToast(`✅ ${ticker} añadido a ${list_type === 'portfolio' ? 'la cartera' : 'seguimiento'}`, 'success');
      closeAddModal();
      loadPortfolio();
    }
  } catch (err) {
    showToast('❌ Error al añadir ticker', 'error');
  }
}

async function addTickerFromExplorer(ticker) {
  try {
    const data = await apiPost('/portfolio', { ticker });
    if (data.error) {
      showToast(`⚠️ ${data.error}`, 'error');
    } else {
      showToast(`✅ ${ticker} añadido a la cartera`, 'success');
    }
  } catch (err) {
    showToast('❌ Error al añadir ticker', 'error');
  }
}

async function removeTicker(ticker) {
  try {
    await apiDelete(`/portfolio/${ticker}`);
    showToast(`🗑️ ${ticker} eliminado`, 'info');
    loadPortfolio();
  } catch (err) {
    showToast('❌ Error al eliminar', 'error');
  }
}

// ─── Company Detail ─────────────────────────────────────────────

async function loadCompanyDetail(ticker) {
  const container = document.getElementById('detail-content');
  container.innerHTML = `
    <div class="card loading-card">
      <div class="loading-skeleton"></div>
      <div class="loading-skeleton"></div>
      <div class="loading-skeleton"></div>
    </div>
    <div class="card loading-card">
      <div class="loading-skeleton"></div>
      <div class="loading-skeleton"></div>
      <div class="loading-skeleton"></div>
      <div class="loading-skeleton"></div>
      <div class="loading-skeleton"></div>
    </div>
  `;

  try {
    const data = await apiGet(`/company/${ticker}`);
    if (data.error) {
      container.innerHTML = renderEmptyState('❌', 'Error', data.error);
      return;
    }
    state.currentDetail = data;
    renderCompanyDetail(data);
    
  } catch (err) {
    container.innerHTML = renderEmptyState('❌', 'Error de conexión', 'No se pudo cargar los datos de la empresa.');
  }
}

function renderCompanyDetail(d) {
  const container = document.getElementById('detail-content');
  const cur = d.currency || 'USD';
  const mosColor = getMosColor(d.margen_seguridad);

  // Dividend yield display with sanity check
  let divYieldDisplay = '—';
  if (d.dividend_yield_valid === false) {
    divYieldDisplay = '⚠️ Dato no fiable';
  } else if (d.dividend_yield) {
    divYieldDisplay = formatPercent(d.dividend_yield * 100);
  }

  // Scorecard signal helpers
  const roicSignal = d.roic_hist_avg > 20 ? '🟢' : d.roic_hist_avg > 12 ? '🟡' : '🔴';
  const fcfSignal = d.fcf_trend === '↑' ? '🟢' : d.fcf_trend === '→' ? '🟡' : '🔴';
  const mosSignal = d.margen_seguridad > 15 ? '🟢' : d.margen_seguridad > 0 ? '🟡' : '🔴';
  const debtSignal = d.net_debt_ebitda != null ? (d.net_debt_ebitda < 2 ? '🟢' : d.net_debt_ebitda < 4 ? '🟡' : '🔴') : '⚪';
  const qualSignal = d.calidad && d.calidad.includes('⭐') ? '🟢' : d.calidad && d.calidad.includes('✅') ? '🟡' : '🔴';

  // Growth source badge
  const gsClass = d.growth_source === 'analyst' ? 'high' : d.growth_source === 'eps_cagr' ? 'medium' : 'low';
  const gsLabel = d.growth_source === 'analyst' ? 'Analistas' : d.growth_source === 'eps_cagr' ? 'CAGR EPS' : 'Por defecto';

  // SBC percentage
  let sbcPct = null;
  if (d.sbc_values && d.sbc_values[0] && d.fcf_ttm_pre_sbc && d.fcf_ttm_pre_sbc > 0) {
    sbcPct = (d.sbc_values[0] / d.fcf_ttm_pre_sbc) * 100;
  }

  container.innerHTML = `
    <!-- Header -->
    <div class="detail-header">
      <button class="detail-header__back" onclick="navigate('dashboard')">←</button>
      <div class="detail-header__info">
        <div class="detail-header__ticker">${d.ticker}</div>
        <div class="detail-header__company">${d.empresa}</div>
      </div>
      <div class="detail-header__price">
        <div class="detail-header__price-value">${formatCurrency(d.current_price, cur)}</div>
        <span class="detail-header__sector">${d.sector}</span>
      </div>
    </div>

    <!-- Archetype & Methodology Badges -->
    <div style="display: flex; flex-wrap: wrap; gap: var(--space-xs); margin-bottom: var(--space-sm); align-items: center;">
      ${d.archetype_label ? `<span class="badge--positive" style="font-size: 0.72rem; padding: 4px 10px; border-radius: 20px; font-weight: 700;">${d.archetype_label}</span>` : ''}
      ${d.methodology_label ? `<span style="background: var(--surface-hover); color: var(--text-secondary); border: 1px solid var(--border-subtle); font-size: 0.72rem; padding: 4px 10px; border-radius: 20px; font-weight: 700;">${d.methodology_label}</span>` : ''}
      <span style="font-size: 0.68rem; color: var(--text-tertiary);">WACC: ${d.wacc_used ? formatPercent(d.wacc_used * 100) : '10%'} · ${cur}</span>
      <span class="confidence-badge confidence-badge--${gsClass}">📊 ${gsLabel}</span>
      ${d.beta ? `<span style="font-size: 0.68rem; color: var(--text-tertiary);">β ${d.beta.toFixed(2)}</span>` : ''}
    </div>

    <!-- Scorecard -->
    <div class="scorecard">
      <div class="scorecard__item">
        <span class="scorecard__label">ROIC</span>
        <span class="scorecard__value">${d.roic_hist_avg != null ? formatPercent(d.roic_hist_avg) : '—'}</span>
        <span class="scorecard__signal">${roicSignal}</span>
      </div>
      <div class="scorecard__item">
        <span class="scorecard__label">FCF</span>
        <span class="scorecard__value">${getTrendEmoji(d.fcf_trend)}</span>
        <span class="scorecard__signal">${fcfSignal}</span>
      </div>
      <div class="scorecard__item">
        <span class="scorecard__label">MoS</span>
        <span class="scorecard__value" style="color: ${mosColor}">${d.margen_seguridad != null ? formatPercent(d.margen_seguridad) : '—'}</span>
        <span class="scorecard__signal">${mosSignal}</span>
      </div>
      <div class="scorecard__item">
        <span class="scorecard__label">Deuda</span>
        <span class="scorecard__value">${d.net_debt_ebitda != null ? formatNumber(d.net_debt_ebitda, 1) + 'x' : '—'}</span>
        <span class="scorecard__signal">${debtSignal}</span>
      </div>
      <div class="scorecard__item">
        <span class="scorecard__label">Calidad</span>
        <span class="scorecard__value" style="font-size: 0.7rem;">${d.calidad ? d.calidad.split(' ')[0] : '—'}</span>
        <span class="scorecard__signal">${qualSignal}</span>
      </div>
    </div>

    <!-- Non-GAAP Flag -->
    ${d.non_gaap_flag && d.non_gaap_flag !== '✅ OK' ? `
      <div class="non-gaap-badge ${d.non_gaap_flag.includes('🚫') ? 'badge--negative' : 'badge--neutral'}" 
           style="margin-bottom: var(--space-md); display: flex;">
        ${d.non_gaap_flag} — ${d.non_gaap_detail || ''}
      </div>
    ` : ''}

    <!-- Tabs Navigation -->
    <div class="detail-tabs">
      <button class="detail-tab active" onclick="switchDetailTab('resumen', this)">📊 Resumen</button>
      <button class="detail-tab" onclick="switchDetailTab('metricas', this)">📈 Métricas</button>
      <button class="detail-tab" onclick="switchDetailTab('valoracion', this)">💎 Valoración</button>
      <button class="detail-tab" onclick="switchDetailTab('cualitativo', this)">🔍 Cualitativo</button>
    </div>

    <!-- TAB: Resumen -->
    <div id="tab-resumen" class="detail-tab-content active">
      <!-- Semáforo Card -->
      <div class="card semaforo-card semaforo-card--${getSemaforoClass(d.estado_semaforo)}">
        <div class="semaforo-card__icon">${getSemaforoEmoji(d.estado_semaforo)}</div>
        <div class="semaforo-card__content">
          <div class="semaforo-card__status">${d.estado_semaforo || 'SIN CLASIFICAR'}</div>
          ${d.methodology === 'growth' ? `
          <div class="responsive-metrics-grid" style="margin-bottom: var(--space-sm);">
            <div style="background: rgba(0,0,0,0.2); padding: var(--space-sm) var(--space-md); border-radius: var(--radius-sm); border: 1px solid var(--border-subtle);">
              <div style="font-size: 0.68rem; color: var(--text-tertiary); text-transform: uppercase;">PEG Ratio</div>
              <div style="font-size: 1.05rem; font-weight: 700; font-family: var(--font-mono); color: ${d.peg_signal === 'undervalued' ? 'var(--color-success)' : d.peg_signal === 'fair' ? '#fbbf24' : 'var(--color-danger)'};">
                ${d.peg_forward != null ? d.peg_forward + 'x' : (d.peg_trailing != null ? d.peg_trailing + 'x' : 'N/A')}
              </div>
            </div>
            <div style="background: rgba(0,0,0,0.2); padding: var(--space-sm) var(--space-md); border-radius: var(--radius-sm); border: 1px solid var(--border-subtle);">
              <div style="font-size: 0.68rem; color: var(--text-tertiary); text-transform: uppercase;">Regla del 40</div>
              <div style="font-size: 1.05rem; font-weight: 700; font-family: var(--font-mono); color: ${d.rule_of_40 >= 40 ? 'var(--color-success)' : d.rule_of_40 >= 20 ? '#fbbf24' : 'var(--color-danger)'};">
                ${d.rule_of_40 != null ? d.rule_of_40.toFixed(1) : 'N/A'}
              </div>
            </div>
          </div>
          ` : d.methodology !== 'speculative' ? `
          <div class="responsive-metrics-grid">
            <div style="background: rgba(0,0,0,0.2); padding: var(--space-sm) var(--space-md); border-radius: var(--radius-sm); border: 1px solid var(--border-subtle);">
              <div style="font-size: 0.68rem; color: var(--text-tertiary); text-transform: uppercase;">Fundamentales (${d.alt_model_name || 'DCF'})</div>
              <div style="font-size: 1.05rem; font-weight: 700; font-family: var(--font-mono); color: ${d.ms_absoluto >= 0 ? 'var(--color-success)' : 'var(--color-danger)'};">
                ${d.ms_absoluto >= 0 ? 'Descuento: ' + formatPercent(d.ms_absoluto) : 'Sobreprecio: ' + formatPercent(Math.abs(d.ms_absoluto))}
              </div>
            </div>
            <div style="background: rgba(0,0,0,0.2); padding: var(--space-sm) var(--space-md); border-radius: var(--radius-sm); border: 1px solid var(--border-subtle);">
              <div style="font-size: 0.68rem; color: var(--text-tertiary); text-transform: uppercase;">Histórico (${d.multiple_type || 'N/A'})</div>
              <div style="font-size: 1.05rem; font-weight: 700; font-family: var(--font-mono); color: ${d.ms_relativo >= 0 ? 'var(--color-success)' : 'var(--color-warning)'};">
                ${d.ms_relativo >= 0 ? 'Descuento: ' + formatPercent(d.ms_relativo) : 'Sobreprecio: ' + formatPercent(Math.abs(d.ms_relativo))}
              </div>
            </div>
          </div>
          ` : `
          <div style="font-size: 0.85rem; color: var(--text-secondary); margin-top: var(--space-sm);">
            Empresa sin beneficios y crecimiento insuficiente para justificar una valoración fiable. Riesgo muy alto.
          </div>
          `}
          ${d.methodology !== 'growth' && d.methodology !== 'speculative' && (d.peg_forward != null || d.peg_trailing != null) ? `
          <div style="display: flex; align-items: center; gap: var(--space-sm); padding: 6px var(--space-md); margin-top: 4px; background: rgba(0,0,0,0.15); border-radius: var(--radius-sm); border: 1px solid var(--border-subtle);">
            <span style="font-size: 0.65rem; color: var(--text-tertiary); text-transform: uppercase; white-space: nowrap;">PEG (Lynch)</span>
            <span style="font-size: 0.9rem; font-weight: 700; font-family: var(--font-mono); color: ${d.peg_signal === 'undervalued' ? 'var(--color-success)' : d.peg_signal === 'fair' ? '#fbbf24' : 'var(--color-danger)'};">
              ${d.peg_forward != null ? d.peg_forward + 'x' : d.peg_trailing + 'x'}
            </span>
            <span style="font-size: 0.62rem; color: ${d.peg_signal === 'undervalued' ? 'var(--color-success)' : d.peg_signal === 'fair' ? '#fbbf24' : 'var(--color-danger)'};">
              ${d.peg_signal === 'undervalued' ? '● Barata vs crecimiento' : d.peg_signal === 'fair' ? '● Precio justo' : '● Cara vs crecimiento'}
            </span>
          </div>
          ` : ''}
          <div class="semaforo-card__meaning">${getSemaforoMeaning(d.estado_semaforo)}</div>
        </div>
      </div>

      <!-- Chart -->
      <div class="card" style="padding: 0; overflow: hidden; height: 350px; margin-bottom: var(--space-md); border-radius: var(--radius-md);">
        <div id="tv_chart_container" style="height: 100%; width: 100%;"></div>
      </div>

      <!-- Investment Thesis -->
      ${d.thesis ? `
        <div class="thesis-box">
          <div class="thesis-box__title">📝 TESIS DE INVERSIÓN</div>
          <div class="thesis-box__text">${d.thesis}</div>
        </div>
      ` : ''}

      <!-- Quarterly Earnings & Next Earnings Call -->
      ${(d.quarterly_data && d.quarterly_data.length > 0) || d.next_earnings ? `
        <div class="card" style="margin-top: var(--space-md); border: 1px solid var(--border-subtle); position: relative; overflow: hidden;">
          <div style="position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, var(--accent-primary), #a855f7, var(--accent-primary)); opacity: 0.7;"></div>
          <div style="font-size: 0.78rem; font-weight: 700; color: var(--accent-primary); margin-bottom: var(--space-md); display: flex; align-items: center; gap: var(--space-xs);">
            🗓️ RESULTADOS TRIMESTRALES & PRÓXIMO EARNINGS CALL
          </div>

          ${d.next_earnings ? `
          <div class="responsive-metrics-grid" style="margin-bottom: var(--space-md);">
            <div style="background: rgba(59,130,246,0.08); padding: var(--space-sm) var(--space-md); border-radius: var(--radius-sm); border: 1px solid rgba(59,130,246,0.2); transition: transform 0.2s ease, box-shadow 0.2s ease; cursor: default;"
                 onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(59,130,246,0.15)';"
                 onmouseout="this.style.transform='none'; this.style.boxShadow='none';">
              <div style="font-size: 0.62rem; color: var(--text-tertiary); text-transform: uppercase; letter-spacing: 0.05em;">Próximo Earnings</div>
              <div style="font-size: 1.0rem; font-weight: 700; font-family: var(--font-mono); color: var(--accent-primary);">${d.next_earnings.date || '—'}</div>
            </div>
            <div style="background: rgba(34,197,94,0.08); padding: var(--space-sm) var(--space-md); border-radius: var(--radius-sm); border: 1px solid rgba(34,197,94,0.2); transition: transform 0.2s ease, box-shadow 0.2s ease; cursor: default;"
                 onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(34,197,94,0.15)';"
                 onmouseout="this.style.transform='none'; this.style.boxShadow='none';">
              <div style="font-size: 0.62rem; color: var(--text-tertiary); text-transform: uppercase; letter-spacing: 0.05em;">EPS Estimado</div>
              <div style="font-size: 1.0rem; font-weight: 700; font-family: var(--font-mono); color: var(--color-success);">
                ${d.next_earnings.eps_estimate != null ? formatCurrency(d.next_earnings.eps_estimate, cur) : '—'}
                ${d.next_earnings.eps_low != null && d.next_earnings.eps_high != null ? `<span style="font-size: 0.6rem; color: var(--text-tertiary); font-weight: 400;"> (${formatCurrency(d.next_earnings.eps_low, cur)} – ${formatCurrency(d.next_earnings.eps_high, cur)})</span>` : ''}
              </div>
            </div>
            <div style="background: rgba(168,85,247,0.08); padding: var(--space-sm) var(--space-md); border-radius: var(--radius-sm); border: 1px solid rgba(168,85,247,0.2); transition: transform 0.2s ease, box-shadow 0.2s ease; cursor: default;"
                 onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(168,85,247,0.15)';"
                 onmouseout="this.style.transform='none'; this.style.boxShadow='none';">
              <div style="font-size: 0.62rem; color: var(--text-tertiary); text-transform: uppercase; letter-spacing: 0.05em;">Revenue Estimado</div>
              <div style="font-size: 1.0rem; font-weight: 700; font-family: var(--font-mono); color: #a855f7;">
                ${d.next_earnings.revenue_estimate != null ? formatLargeNumber(d.next_earnings.revenue_estimate) : '—'}
              </div>
            </div>
          </div>
          ` : ''}

          ${d.quarterly_data && d.quarterly_data.length > 0 ? `
          <div style="overflow-x: auto; -webkit-overflow-scrolling: touch;">
            <table class="metrics-table" style="font-size: 0.78rem;">
              <thead>
                <tr>
                  <th>Trimestre</th>
                  ${d.quarterly_data.slice().reverse().map(q => {
                    const parts = q.date.split('-');
                    const m = parseInt(parts[1]);
                    const qLabel = m <= 3 ? 'Q1' : m <= 6 ? 'Q2' : m <= 9 ? 'Q3' : 'Q4';
                    return '<th>' + qLabel + ' ' + parts[0] + '</th>';
                  }).join('')}
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td class="metrics-table__metric">Revenue</td>
                  ${d.quarterly_data.slice().reverse().map((q, i, arr) => {
                    const val = q.revenue;
                    let qoq = '';
                    if (i > 0 && arr[i-1].revenue && arr[i-1].revenue !== 0 && val) {
                      const pct = ((val - arr[i-1].revenue) / Math.abs(arr[i-1].revenue) * 100);
                      const color = pct >= 0 ? 'var(--color-success)' : 'var(--color-danger)';
                      const arrow = pct >= 0 ? '▲' : '▼';
                      qoq = '<div style="font-size:0.6rem;color:' + color + ';">' + arrow + ' ' + Math.abs(pct).toFixed(1) + '% QoQ</div>';
                    }
                    return '<td class="metrics-table__value">' + formatLargeNumber(val) + qoq + '</td>';
                  }).join('')}
                </tr>
                <tr>
                  <td class="metrics-table__metric">Benef. Operativo</td>
                  ${d.quarterly_data.slice().reverse().map(q => '<td class="metrics-table__value">' + formatLargeNumber(q.operating_income) + '</td>').join('')}
                </tr>
                <tr>
                  <td class="metrics-table__metric">Benef. Neto</td>
                  ${d.quarterly_data.slice().reverse().map(q => '<td class="metrics-table__value">' + formatLargeNumber(q.net_income) + '</td>').join('')}
                </tr>
                <tr>
                  <td class="metrics-table__metric" style="color: var(--accent-primary);">EPS</td>
                  ${d.quarterly_data.slice().reverse().map((q, i, arr) => {
                    const val = q.eps;
                    let beat = '';
                    if (i > 0 && arr[i-1].eps && arr[i-1].eps !== 0 && val) {
                      const pct = ((val - arr[i-1].eps) / Math.abs(arr[i-1].eps) * 100);
                      const color = pct >= 0 ? 'var(--color-success)' : 'var(--color-danger)';
                      const arrow = pct >= 0 ? '▲' : '▼';
                      beat = '<div style="font-size:0.6rem;color:' + color + ';">' + arrow + ' ' + Math.abs(pct).toFixed(1) + '%</div>';
                    }
                    return '<td class="metrics-table__value" style="font-weight:600;">' + formatCurrency(val, cur) + beat + '</td>';
                  }).join('')}
                </tr>
              </tbody>
            </table>
          </div>
          ` : ''}
        </div>
      ` : ''}
    </div>

    <!-- TAB: Métricas -->
    <div id="tab-metricas" class="detail-tab-content">
      <!-- Sparklines (mobile) -->
      <div class="sparkline-container">
        ${renderSparklineRow('FCF Real', d.fcf_real_values, d.fcf_trend)}
        ${renderSparklineRow('ROIC', d.roic_values, d.roic_trend, true)}
        ${d.eps_values ? renderSparklineRow('EPS', d.eps_values, d.eps_trend) : ''}
      </div>

      <!-- Metrics Table -->
      <div class="card metrics-table-container" style="overflow-x: auto; -webkit-overflow-scrolling: touch;">
        <table class="metrics-table">
          <thead>
            <tr>
              <th>Métrica</th>
              ${(d.fiscal_dates || []).map(dateStr => {
                try { return `<th>${dateStr.split('-')[0]}</th>`; }
                catch(e) { return `<th>${dateStr}</th>`; }
              }).reverse().join('')}
              <th>Actual/TTM</th>
              <th>Tend.</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td class="metrics-table__metric">EPS</td>
              ${(d.eps_values || []).map(val => `<td class="metrics-table__value">${formatCurrency(val, cur)}</td>`).reverse().join('')}
              <td class="metrics-table__value">${formatCurrency(d.eps_ttm, cur)}</td>
              <td class="metrics-table__trend">${getTrendEmoji(d.eps_trend)}</td>
            </tr>
            <tr>
              <td class="metrics-table__metric">FCF Real</td>
              ${(d.fcf_real_values || []).map(val => `<td class="metrics-table__value">${formatLargeNumber(val)}</td>`).reverse().join('')}
              <td class="metrics-table__value">${formatLargeNumber(d.fcf_real_ttm)}</td>
              <td class="metrics-table__trend">${getTrendEmoji(d.fcf_trend)}</td>
            </tr>
            ${d.sbc_values && d.sbc_values.some(v => v > 0) ? `
            <tr>
              <td class="metrics-table__metric" style="color: var(--color-warning);">SBC ⚠️</td>
              ${(d.sbc_values || []).map(val => `<td class="metrics-table__value" style="color: var(--color-warning);">${formatLargeNumber(val)}</td>`).reverse().join('')}
              <td class="metrics-table__value" style="color: var(--color-warning);">${d.sbc_values[0] ? formatLargeNumber(d.sbc_values[0]) : '—'}</td>
              <td class="metrics-table__trend">—</td>
            </tr>
            ` : ''}
            <tr>
              <td class="metrics-table__metric">ROIC</td>
              ${(d.roic_values || []).map(val => `<td class="metrics-table__value">${formatPercent(val)}</td>`).reverse().join('')}
              <td class="metrics-table__value">${formatPercent(d.roic_current)}</td>
              <td class="metrics-table__trend">${getTrendEmoji(d.roic_trend)}</td>
            </tr>
            <tr>
              <td class="metrics-table__metric">PER</td>
              ${(d.per_history || []).map(val => `<td class="metrics-table__value">${val ? formatNumber(val, 1) + 'x' : '—'}</td>`).reverse().join('')}
              <td class="metrics-table__value">${formatNumber(d.per_actual, 1)}x</td>
              <td class="metrics-table__trend">—</td>
            </tr>
            <tr>
              <td class="metrics-table__metric">EV/FCF</td>
              ${(d.ev_fcf_history || []).map(val => `<td class="metrics-table__value">${val ? formatNumber(val, 1) + 'x' : '—'}</td>`).reverse().join('')}
              <td class="metrics-table__value">${formatNumber(d.ev_fcf_actual, 1)}x</td>
              <td class="metrics-table__trend">—</td>
            </tr>
            ${d.peg_forward != null || d.peg_trailing != null ? `
            <tr>
              <td class="metrics-table__metric" style="color: var(--accent-primary);">PEG (Lynch)</td>
              ${(d.fiscal_dates || []).map(() => `<td class="metrics-table__value">—</td>`).reverse().join('')}
              <td class="metrics-table__value" style="font-weight: 700; color: ${d.peg_signal === 'undervalued' ? 'var(--color-success)' : d.peg_signal === 'fair' ? '#fbbf24' : 'var(--color-danger)'};">${d.peg_forward != null ? d.peg_forward + 'x' : d.peg_trailing + 'x'}</td>
              <td class="metrics-table__trend">${d.peg_signal === 'undervalued' ? '💎' : d.peg_signal === 'fair' ? '✅' : '⚠️'}</td>
            </tr>
            ` : ''}
          </tbody>
        </table>
      </div>

      ${sbcPct && sbcPct > 10 ? `
        <div class="sbc-badge" style="margin-bottom: var(--space-md);">⚠️ SBC = ${sbcPct.toFixed(0)}% del FCF pre-SBC — compensación en acciones significativa</div>
      ` : ''}

      <!-- Margins and Debt -->
      <div class="responsive-metrics-grid">
        <div class="card">
          <div style="font-size: 0.72rem; font-weight: 700; color: var(--text-tertiary); margin-bottom: var(--space-xs);">📊 RENTABILIDAD</div>
          <div class="info-row"><span class="info-row__label">Margen Bruto</span><span class="info-row__value">${d.current_gross_margin != null ? formatPercent(d.current_gross_margin * 100) : '—'}</span></div>
          <div class="info-row"><span class="info-row__label">Margen Operativo</span><span class="info-row__value">${d.current_operating_margin != null ? formatPercent(d.current_operating_margin * 100) : '—'}</span></div>
          <div class="info-row"><span class="info-row__label">Margen Neto</span><span class="info-row__value">${d.current_net_margin != null ? formatPercent(d.current_net_margin * 100) : '—'}</span></div>
        </div>
        <div class="card">
          <div style="font-size: 0.72rem; font-weight: 700; color: var(--text-tertiary); margin-bottom: var(--space-xs);">🏦 DEUDA</div>
          <div class="info-row"><span class="info-row__label">Interest Coverage</span><span class="info-row__value" style="color: ${d.interest_coverage != null && d.interest_coverage < 3 ? 'var(--color-danger)' : 'var(--text-primary)'}">${d.interest_coverage != null ? (d.interest_coverage > 900 ? 'Sin Deuda' : formatNumber(d.interest_coverage, 1) + 'x') : '—'}</span></div>
          <div class="info-row"><span class="info-row__label">Net Debt / EBITDA</span><span class="info-row__value" style="color: ${d.net_debt_ebitda != null && d.net_debt_ebitda > 3 ? 'var(--color-danger)' : (d.net_debt_ebitda != null && d.net_debt_ebitda < 0 ? 'var(--color-success)' : 'var(--text-primary)')}">${d.net_debt_ebitda != null ? (d.net_debt_ebitda < 0 ? 'Caja Neta' : formatNumber(d.net_debt_ebitda, 1) + 'x') : '—'}</span></div>
        </div>
      </div>

      <!-- Additional Info -->
      <div class="card">
        <div class="info-row"><span class="info-row__label">Market Cap</span><span class="info-row__value">${formatLargeNumber(d.market_cap)}</span></div>
        <div class="info-row"><span class="info-row__label">Industria</span><span class="info-row__value" style="font-family: var(--font-main); font-size: 0.8rem;">${d.industry || '—'}</span></div>
        <div class="info-row"><span class="info-row__label">Div. Yield</span><span class="info-row__value">${divYieldDisplay}</span></div>
        <div class="info-row"><span class="info-row__label">Crecimiento Est.</span><span class="info-row__value">${d.growth_rate ? formatPercent(d.growth_rate * 100) : '—'}</span></div>
        ${d.beta ? `<div class="info-row"><span class="info-row__label">Beta (β)</span><span class="info-row__value" style="color: ${d.beta > 1.5 ? 'var(--color-danger)' : d.beta < 0.7 ? 'var(--color-info)' : 'var(--text-primary)'}">${d.beta.toFixed(2)}</span></div>` : ''}
        <div class="info-row"><span class="info-row__label">Precio Objetivo Analistas</span><span class="info-row__value">${d.analyst_target ? formatCurrency(d.analyst_target, cur) : '—'}</span></div>
        <div class="info-row"><span class="info-row__label">Modelos</span><span class="info-row__value">${d.valuation_models_used ? d.valuation_models_used.join(', ') : '—'}</span></div>
      </div>
    </div>

    <!-- TAB: Valoración -->
    <div id="tab-valoracion" class="detail-tab-content">
      ${d.methodology !== 'speculative' ? `
      <!-- Valuation Box -->
      <div class="valuation-box">
        <div class="valuation-box__title">💎 VALORACIÓN INTRÍNSECA</div>
        ${d.methodology === 'growth' ? `
        <!-- Growth companies: no DCF, explain PEG methodology -->
        <div class="valuation-box__row">
          <span class="valuation-box__label">Precio Mercado</span>
          <span class="valuation-box__value" style="color: var(--text-primary)">${formatCurrency(d.current_price, cur)}</span>
        </div>
        <div class="valuation-box__divider"></div>
        <div style="font-size: 0.72rem; color: var(--text-tertiary); padding: var(--space-sm) 0; line-height: 1.5;">
          ⚡ Esta empresa se valora por <strong>PEG + Rule of 40</strong>, no por DCF.
          El DCF no es fiable para empresas en fase de hipercrecimiento porque el FCF actual no refleja
          el potencial futuro. El semáforo usa el PEG y la rentabilidad del modelo de negocio.
        </div>
        <div class="valuation-box__row" style="margin-top: var(--space-sm);">
          <span class="valuation-box__label">PEG (Forward)</span>
          <span class="valuation-box__value" style="color: ${d.peg_signal === 'undervalued' ? 'var(--color-success)' : d.peg_signal === 'fair' ? '#fbbf24' : 'var(--color-danger)'}">${d.peg_forward != null ? d.peg_forward + 'x' : (d.peg_trailing != null ? d.peg_trailing + 'x' : 'N/A')}</span>
        </div>
        <div class="valuation-box__row">
          <span class="valuation-box__label">Rule of 40</span>
          <span class="valuation-box__value" style="color: ${d.rule_of_40 >= 40 ? 'var(--color-success)' : d.rule_of_40 >= 20 ? '#fbbf24' : 'var(--color-danger)'}">${d.rule_of_40 != null ? d.rule_of_40.toFixed(1) : 'N/A'}</span>
        </div>
        <div class="valuation-box__quality" style="margin-top: var(--space-sm);">
          <span class="valuation-box__quality-label">Calidad</span>
          <span class="valuation-box__quality-value">${d.calidad || '—'}</span>
        </div>
        ${d.naranjos_score != null ? `
        <div class="valuation-box__quality" title="${(d.naranjos_details || []).join('&#10;')}">
          <span class="valuation-box__quality-label">Naranjos Score ℹ️</span>
          <span class="valuation-box__quality-value" style="color: ${d.naranjos_score >= 80 ? 'var(--color-success)' : d.naranjos_score >= 50 ? '#fbbf24' : 'var(--color-danger)'}; font-weight: 700;">${d.naranjos_score}/100</span>
        </div>
        ` : ''}
        ${d.piotroski_score != null && d.margen_seguridad != null && d.margen_seguridad > 0 ? `
        <div class="valuation-box__quality" style="margin-top: 4px;" title="${(d.piotroski_details || []).join('&#10;')}">
          <span class="valuation-box__quality-label">Piotroski F-Score ℹ️</span>
          <span class="valuation-box__quality-value" style="color: ${d.piotroski_score >= 7 ? 'var(--color-success)' : d.piotroski_score >= 4 ? '#fbbf24' : 'var(--color-danger)'}; font-weight: 700;">${d.piotroski_score}/9</span>
        </div>
        ${d.piotroski_score <= 3 && d.estado_semaforo && d.estado_semaforo.includes('STRONG BUY') ? `
        <div style="font-size: 0.7rem; color: var(--color-danger); text-align: right; margin-top: 2px;">
          ⚠️ RIESGO VALUE TRAP
        </div>` : ''}
        ` : ''}
        ` : `
        ${d.graham_value && d.graham_value > 0 ? `
        <div class="valuation-box__row">
          <span class="valuation-box__label">Graham</span>
          <span class="valuation-box__value">${formatCurrency(d.graham_value, cur)}</span>
        </div>
        ` : ''}
        ${d.dcf_value && d.dcf_value > 0 ? `
        <div class="valuation-box__row">
          <span class="valuation-box__label">${d.archetype_id === 'compounder' ? 'DCF (Multi-Fase)' : 'DCF (10a)'}</span>
          <span class="valuation-box__value">${formatCurrency(d.dcf_value, cur)}</span>
        </div>
        ${d.terminal_value_pct && d.terminal_value_pct > 60 ? `
        <div style="font-size: 0.7rem; color: #fbbf24; text-align: right; margin-top: 2px;" title="Una gran parte de la valoración depende de flujos muy lejanos y del valor terminal.">
          ⚠️ ${d.terminal_value_pct}% del valor es terminal
        </div>
        ` : ''}
        ${d.excess_capex_warning && d.excess_capex_warning > 0 ? `
        <div style="font-size: 0.7rem; color: var(--color-info); text-align: right; margin-top: 2px;" title="La empresa está invirtiendo en CAPEX muy por encima de su media histórica. Este exceso podría ser inversión para crecimiento futuro, pero no se suma al FCF actual por prudencia.">
          ℹ️ Inversión extra detectada: ${formatLargeNumber(d.excess_capex_warning)}
        </div>
        ` : ''}
        ` : ''}
        ${d.alt_value && d.alt_model_name ? `
        <div class="valuation-box__row">
          <span class="valuation-box__label">${d.alt_model_name}</span>
          <span class="valuation-box__value">${formatCurrency(d.alt_value, cur)}</span>
        </div>
        ` : ''}
        <div class="valuation-box__row">
          <span class="valuation-box__label">Precio Mercado</span>
          <span class="valuation-box__value" style="color: var(--text-primary)">${formatCurrency(d.current_price, cur)}</span>
        </div>
        <div class="valuation-box__divider"></div>
        <div class="valuation-box__mos">
          <span class="valuation-box__mos-label">Margen de Seguridad</span>
          <span class="valuation-box__mos-value" style="color: ${mosColor}">${formatPercent(d.margen_seguridad)}</span>
        </div>
        <div class="valuation-box__quality">
          <span class="valuation-box__quality-label">Calidad</span>
          <span class="valuation-box__quality-value">${d.calidad || '—'}</span>
        </div>
        ${d.naranjos_score != null ? `
        <div class="valuation-box__quality" title="${(d.naranjos_details || []).join('&#10;')}">
          <span class="valuation-box__quality-label">Naranjos Score ℹ️</span>
          <span class="valuation-box__quality-value" style="color: ${d.naranjos_score >= 80 ? 'var(--color-success)' : d.naranjos_score >= 50 ? '#fbbf24' : 'var(--color-danger)'}; font-weight: 700;">${d.naranjos_score}/100</span>
        </div>
        ` : ''}
        ${d.piotroski_score != null && d.margen_seguridad != null && d.margen_seguridad > 0 ? `
        <div class="valuation-box__quality" style="margin-top: 4px;" title="${(d.piotroski_details || []).join('&#10;')}">
          <span class="valuation-box__quality-label">Piotroski F-Score ℹ️</span>
          <span class="valuation-box__quality-value" style="color: ${d.piotroski_score >= 7 ? 'var(--color-success)' : d.piotroski_score >= 4 ? '#fbbf24' : 'var(--color-danger)'}; font-weight: 700;">${d.piotroski_score}/9</span>
        </div>
        ${d.piotroski_score <= 3 && d.estado_semaforo && d.estado_semaforo.includes('STRONG BUY') ? `
        <div style="font-size: 0.7rem; color: var(--color-danger); text-align: right; margin-top: 2px;">
          ⚠️ RIESGO VALUE TRAP
        </div>` : ''}
        ` : ''}
        `}
      </div>
      
      <!-- Reverse DCF — hidden for growth/hypergrowth (DCF not applicable) -->
      ${d.implied_growth != null && d.methodology !== 'growth' ? `
      <div class="card" style="margin-bottom: var(--space-md);">
        <div style="font-size: 0.72rem; font-weight: 700; color: var(--text-tertiary); text-transform: uppercase; margin-bottom: var(--space-sm);">🔄 Reverse DCF — Crecimiento Implícito en el Precio</div>
        <div class="reverse-dcf-bar">
          <span style="font-size: 0.75rem; color: var(--text-secondary); min-width: 60px;">Estimado</span>
          <div class="reverse-dcf-bar__track">
            <div class="reverse-dcf-bar__fill" style="width: ${Math.min(Math.max(d.growth_rate * 100 / 50 * 100, 5), 100)}%; background: var(--accent-primary);"></div>
          </div>
          <span style="font-family: var(--font-mono); font-size: 0.85rem; font-weight: 700; color: var(--accent-primary); min-width: 50px; text-align: right;">${formatPercent(d.growth_rate * 100)}</span>
        </div>
        <div class="reverse-dcf-bar">
          <span style="font-size: 0.75rem; color: var(--text-secondary); min-width: 60px;">Implícito</span>
          <div class="reverse-dcf-bar__track">
            <div class="reverse-dcf-bar__fill" style="width: ${Math.min(Math.max(d.implied_growth * 100 / 50 * 100, 5), 100)}%; background: ${d.implied_growth > d.growth_rate * 1.3 ? 'var(--color-danger)' : d.implied_growth < d.growth_rate * 0.7 ? 'var(--color-success)' : '#fbbf24'};"></div>
          </div>
          <span style="font-family: var(--font-mono); font-size: 0.85rem; font-weight: 700; color: ${d.implied_growth > d.growth_rate * 1.3 ? 'var(--color-danger)' : d.implied_growth < d.growth_rate * 0.7 ? 'var(--color-success)' : '#fbbf24'}; min-width: 50px; text-align: right;">${formatPercent(d.implied_growth * 100)}</span>
        </div>
        <div style="font-size: 0.72rem; color: var(--text-tertiary); margin-top: var(--space-xs);">
          ${d.implied_growth > d.growth_rate * 1.5 ? '⚠️ El mercado descuenta un crecimiento mucho mayor al estimado — optimismo excesivo.' :
            d.implied_growth < d.growth_rate * 0.5 ? '💎 El mercado descuenta un crecimiento bajo — posible oportunidad si los fundamentales se mantienen.' :
            'El mercado descuenta un crecimiento cercano al estimado — valoración razonable.'}
        </div>
      </div>
      ` : ''}

      <!-- Sensitivity Table — hidden for growth/hypergrowth (DCF not applicable) -->
      ${d.sensitivity && d.methodology !== 'growth' ? `
      <div class="card" style="margin-bottom: var(--space-md);">
        <div style="font-size: 0.72rem; font-weight: 700; color: var(--text-tertiary); text-transform: uppercase; margin-bottom: var(--space-sm);">📐 TABLA DE SENSIBILIDAD (Valor Intrínseco por Acción)</div>
        <div style="overflow-x: auto;">
          <table class="sensitivity-table">
            <thead>
              <tr>
                <th>WACC \\ Growth</th>
                ${d.sensitivity.growth_values.map(g => `<th>${(g * 100).toFixed(0)}%</th>`).join('')}
              </tr>
            </thead>
            <tbody>
              ${d.sensitivity.wacc_values.map((w, wi) =>
                `<tr>
                  <td style="font-weight: 700; color: var(--text-secondary);">${(w * 100).toFixed(0)}%</td>
                  ${d.sensitivity.matrix[wi].map((val, gi) => {
                    const isBase = wi === 1 && gi === 1;
                    const cls = val > d.current_price * 1.15 ? 'sens-cell--green' : val > d.current_price * 0.85 ? 'sens-cell--yellow' : 'sens-cell--red';
                    return `<td class="${cls} ${isBase ? 'sens-cell--base' : ''}">${formatCurrency(val, cur)}</td>`;
                  }).join('')}
                </tr>`
              ).join('')}
            </tbody>
          </table>
        </div>
        <div style="font-size: 0.65rem; color: var(--text-muted); margin-top: var(--space-xs);">Precio actual: ${formatCurrency(d.current_price, cur)} · Centro = caso base · Verde = infravalorada · Rojo = sobrevalorada</div>
      </div>
      ` : ''}
      ` : `
      <div class="card">
        <div style="text-align: center; padding: var(--space-lg); color: var(--text-tertiary);">
          ⚠️ Empresa clasificada como especulativa — sin modelos de valoración fiables disponibles.
        </div>
      </div>
      `}
    </div>

    <!-- TAB: Cualitativo -->
    <div id="tab-cualitativo" class="detail-tab-content">
      ${d.qualitative_audit ? `
        <div class="card" style="margin-bottom: var(--space-md);">
          <div style="font-size: 0.72rem; font-weight: 700; color: var(--accent-primary); text-transform: uppercase; margin-bottom: 2px;">🛡️ Análisis de Foso (Moat)</div>
          <div style="font-size: 0.8rem; color: var(--text-secondary); line-height: 1.5; padding-left: var(--space-sm); border-left: 2px solid var(--accent-primary);">
            <strong>${d.qualitative_audit.moat_strength}</strong>: ${d.qualitative_audit.moat_details}
          </div>
        </div>
        
        <div class="card" style="margin-bottom: var(--space-md);">
          <div style="font-size: 0.72rem; font-weight: 700; color: var(--accent-primary); text-transform: uppercase; margin-bottom: 2px;">💼 Directiva y Asignación de Capital</div>
          <div style="font-size: 0.8rem; color: var(--text-secondary); line-height: 1.5; padding-left: var(--space-sm); border-left: 2px solid var(--accent-primary);">
            ${d.qualitative_audit.management_details}
          </div>
        </div>

        <div class="card" style="margin-bottom: var(--space-md);">
          <div style="font-size: 0.72rem; font-weight: 700; color: var(--accent-primary); text-transform: uppercase; margin-bottom: 2px;">🌐 Tamaño de Mercado y Crecimiento (TAM)</div>
          <div style="font-size: 0.8rem; color: var(--text-secondary); line-height: 1.5; padding-left: var(--space-sm); border-left: 2px solid var(--accent-primary);">
            <strong>${d.qualitative_audit.growth_strength || 'Análisis de Crecimiento'}</strong>: ${d.qualitative_audit.growth_details || ''}
          </div>
        </div>
        
        <div class="card" style="margin-bottom: var(--space-md);">
          <div style="font-size: 0.72rem; font-weight: 700; color: var(--color-danger); text-transform: uppercase; margin-bottom: 2px;">⚠️ Análisis de Riesgos y Gobernanza</div>
          <div style="font-size: 0.8rem; color: var(--text-secondary); line-height: 1.5; padding-left: var(--space-sm); border-left: 2px solid var(--color-danger);">
            ${d.qualitative_audit.risk_details}
          </div>
        </div>
      ` : '<div class="card"><div style="text-align: center; padding: var(--space-lg); color: var(--text-tertiary);">Sin datos cualitativos disponibles.</div></div>'}
    </div>
  `;


  // Initialize TradingView Widget
  if (typeof TradingView !== 'undefined') {
    new TradingView.widget({
      "autosize": true,
      "symbol": d.ticker,
      "interval": "D",
      "timezone": "Etc/UTC",
      "theme": "dark",
      "style": "1",
      "locale": "es",
      "enable_publishing": false,
      "backgroundColor": "rgba(30, 31, 35, 1)",
      "gridColor": "rgba(43, 43, 54, 1)",
      "hide_top_toolbar": true,
      "save_image": false,
      "container_id": "tv_chart_container"
    });
  }
}

// ─── Tab Switching ──────────────────────────────────────────────

function switchDetailTab(tabId, btn) {
  document.querySelectorAll('.detail-tab-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.detail-tab').forEach(el => el.classList.remove('active'));
  const target = document.getElementById('tab-' + tabId);
  if (target) target.classList.add('active');
  if (btn) btn.classList.add('active');
}

// ─── Sparkline Renderer ─────────────────────────────────────────

function renderSparklineRow(label, values, trend, isPercent = false) {
  if (!values || values.length === 0) return '';
  const clean = values.filter(v => v != null);
  if (clean.length === 0) return '';
  const maxVal = Math.max(...clean.map(v => Math.abs(v)));
  const barHeight = 40;
  
  const bars = [...values].reverse().map(v => {
    if (v == null) return '<span class="sparkline-bar" style="height: 2px; background: var(--text-muted);"></span>';
    const h = maxVal > 0 ? Math.max(2, Math.abs(v) / maxVal * barHeight) : 2;
    const color = v >= 0 ? 'var(--color-success)' : 'var(--color-danger)';
    return `<span class="sparkline-bar" style="height: ${h}px; background: ${color};"></span>`;
  }).join('');

  const latest = clean[0];
  const display = isPercent ? formatPercent(latest) : formatLargeNumber(latest);

  return `
    <div class="card" style="margin-bottom: var(--space-sm); padding: var(--space-sm) var(--space-md);">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
        <span style="font-size: 0.72rem; font-weight: 700; color: var(--text-tertiary);">${label}</span>
        <span style="font-family: var(--font-mono); font-size: 0.8rem; font-weight: 600; color: var(--text-primary);">${display} ${getTrendEmoji(trend)}</span>
      </div>
      <div style="height: ${barHeight}px; display: flex; align-items: flex-end;">${bars}</div>
    </div>
  `;
}

// ─── Scatter Plot Renderer ──────────────────────────────────────

function renderScatterPlot() {
  const canvasEl = document.getElementById('scatter-canvas');
  if (!canvasEl) return;
  
  const items = state.portfolio.filter(p => p.roic_actual != null && p.margen_seguridad != null);
  if (items.length < 2) {
    canvasEl.parentElement.style.display = 'none';
    return;
  }

  const ctx = canvasEl.getContext('2d');
  const W = canvasEl.parentElement.clientWidth - 32;
  const H = 250;
  canvasEl.width = W * window.devicePixelRatio;
  canvasEl.height = H * window.devicePixelRatio;
  canvasEl.style.width = W + 'px';
  canvasEl.style.height = H + 'px';
  ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

  const pad = { top: 20, right: 20, bottom: 30, left: 45 };
  const chartW = W - pad.left - pad.right;
  const chartH = H - pad.top - pad.bottom;

  // Data ranges
  const mosValues = items.map(i => i.margen_seguridad);
  const roicValues = items.map(i => i.roic_actual);
  const mosMin = Math.min(...mosValues, -20);
  const mosMax = Math.max(...mosValues, 40);
  const roicMin = Math.min(...roicValues, 0);
  const roicMax = Math.max(...roicValues, 30);

  const scaleX = v => pad.left + ((v - mosMin) / (mosMax - mosMin)) * chartW;
  const scaleY = v => pad.top + chartH - ((v - roicMin) / (roicMax - roicMin)) * chartH;

  // Background
  ctx.fillStyle = '#1f1f22';
  ctx.fillRect(0, 0, W, H);

  // Grid lines
  ctx.strokeStyle = 'rgba(255,255,255,0.06)';
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const y = pad.top + (chartH / 4) * i;
    ctx.beginPath(); ctx.moveTo(pad.left, y); ctx.lineTo(W - pad.right, y); ctx.stroke();
  }
  // Zero line for MoS
  if (mosMin < 0 && mosMax > 0) {
    ctx.strokeStyle = 'rgba(255,255,255,0.15)';
    const zeroX = scaleX(0);
    ctx.beginPath(); ctx.moveTo(zeroX, pad.top); ctx.lineTo(zeroX, H - pad.bottom); ctx.stroke();
  }

  // Axis labels
  ctx.fillStyle = '#64748b';
  ctx.font = '10px Outfit';
  ctx.textAlign = 'center';
  ctx.fillText('← Sobrevalorada | MoS (%) | Infravalorada →', W / 2, H - 5);
  ctx.save();
  ctx.translate(12, H / 2);
  ctx.rotate(-Math.PI / 2);
  ctx.fillText('ROIC (%)', 0, 0);
  ctx.restore();

  // Points
  items.forEach(item => {
    const x = scaleX(item.margen_seguridad);
    const y = scaleY(item.roic_current);
    const color = item.estado_semaforo && item.estado_semaforo.includes('🟢') ? '#22c55e' :
                  item.estado_semaforo && item.estado_semaforo.includes('🔴') ? '#ef4444' : '#fbbf24';
    
    // Glow
    ctx.beginPath();
    ctx.arc(x, y, 8, 0, Math.PI * 2);
    ctx.fillStyle = color + '33';
    ctx.fill();
    
    // Point
    ctx.beginPath();
    ctx.arc(x, y, 5, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();

    // Label
    ctx.fillStyle = '#f1f5f9';
    ctx.font = '600 10px Outfit';
    ctx.textAlign = 'center';
    ctx.fillText(item.ticker, x, y - 10);
  });
}













// ─── Explorer Profiles ───────────────────────────────────────────
const exploreProfiles = {
  conservative: { max_per: 15, min_roic: 15, min_fcf_yield: 7, min_mos: 30 },
  moderate: { max_per: 20, min_roic: 12, min_fcf_yield: 5, min_mos: 20 },
  aggressive: { max_per: 25, min_roic: 8, min_fcf_yield: 3, min_mos: 10 },
};

// Apply a profile preset to the sliders
window.applyExploreProfile = function() {
  const select = document.getElementById('explore-profile');
  if (!select) return;
  const key = select.value;
  if (key === 'custom') return; // Don't change sliders for custom
  const p = exploreProfiles[key];
  if (!p) return;

  document.getElementById('slider-per').value = p.max_per;
  document.getElementById('slider-roic').value = p.min_roic;
  document.getElementById('slider-fcf').value = p.min_fcf_yield;
  document.getElementById('slider-mos').value = p.min_mos;
  onSliderChange();
};

// Update value labels when sliders change
window.onSliderChange = function() {
  const perVal = document.getElementById('slider-per').value;
  const roicVal = document.getElementById('slider-roic').value;
  const fcfVal = document.getElementById('slider-fcf').value;
  const mosVal = document.getElementById('slider-mos').value;

  document.getElementById('slider-per-value').textContent = perVal + 'x';
  document.getElementById('slider-roic-value').textContent = roicVal + '%';
  document.getElementById('slider-fcf-value').textContent = fcfVal + '%';
  document.getElementById('slider-mos-value').textContent = mosVal + '%';

  // Switch profile to "Custom" when user manually adjusts
  const profileSelect = document.getElementById('explore-profile');
  if (profileSelect) {
    const currentProfile = profileSelect.value;
    if (currentProfile !== 'custom') {
      const p = exploreProfiles[currentProfile];
      if (p && (
        parseInt(perVal) !== p.max_per ||
        parseInt(roicVal) !== p.min_roic ||
        parseInt(fcfVal) !== p.min_fcf_yield ||
        parseInt(mosVal) !== p.min_mos
      )) {
        profileSelect.value = 'custom';
      }
    }
  }

  // Update filter chips
  updateExploreChips();
};

window.updateExploreChips = function() {
  const container = document.getElementById('explorer-filters-container');
  if (!container) return;

  const perVal = document.getElementById('slider-per')?.value || 20;
  const roicVal = document.getElementById('slider-roic')?.value || 12;
  const fcfVal = document.getElementById('slider-fcf')?.value || 5;
  const mosVal = document.getElementById('slider-mos')?.value || 20;

  const archSelect = document.getElementById('explore-archetype');
  const sectorSelect = document.getElementById('explore-sector');
  const archLabel = archSelect && archSelect.value !== 'all' 
    ? archSelect.options[archSelect.selectedIndex].text : null;
  const sectorLabel = sectorSelect && sectorSelect.value !== 'all'
    ? sectorSelect.options[sectorSelect.selectedIndex].text : null;

  let chips = `
    <span class="filter-chip">PER &lt; ${perVal}x</span>
    <span class="filter-chip">ROIC &gt; ${roicVal}%</span>
    <span class="filter-chip">FCF Yield &gt; ${fcfVal}%</span>
    <span class="filter-chip">MoS &gt; ${mosVal}%</span>
  `;
  if (archLabel) chips += `<span class="filter-chip filter-chip--accent">${archLabel}</span>`;
  if (sectorLabel) chips += `<span class="filter-chip filter-chip--accent">${sectorLabel}</span>`;
  container.innerHTML = chips;
};

// ─── Explorer / NOVEDAD ─────────────────────────────────────────

async function exploreOpportunities() {
  if (state.isExploring) return;
  
  let market = document.getElementById('explore-market')?.value || 'sp500';
  const marketSelect = document.getElementById('explore-market');
  let marketName = marketSelect ? marketSelect.options[marketSelect.selectedIndex].text : 'del mercado';
  
  // Read slider values
  const maxPer = document.getElementById('slider-per')?.value || 20;
  const minRoic = document.getElementById('slider-roic')?.value || 12;
  const minFcf = document.getElementById('slider-fcf')?.value || 5;
  const minMos = document.getElementById('slider-mos')?.value || 20;

  // Read archetype/sector
  const archetype = document.getElementById('explore-archetype')?.value || 'all';
  const sectorRaw = document.getElementById('explore-sector')?.value || 'all';
  const sectorSelect = document.getElementById('explore-sector');
  
  // Determine if sector is a curated list (sector_*) or a Yahoo filter
  let sectorFilter = 'all';
  if (sectorRaw.startsWith('sector_')) {
    // Curated list: override market with the themed list
    market = sectorRaw;
    const sectorName = sectorSelect ? sectorSelect.options[sectorSelect.selectedIndex].text : sectorRaw;
    marketName = sectorName;
  } else if (sectorRaw !== 'all') {
    // Yahoo sector filter: filter within the selected market
    sectorFilter = sectorRaw;
  }

  const btn = document.getElementById('btn-explore');
  const resultsContainer = document.getElementById('explorer-results');
  const sortBar = document.getElementById('explorer-sort');
  
  state.isExploring = true;
  btn.classList.add('btn-explore--loading');
  btn.innerHTML = '<span class="spinner"></span> Escaneando mercado...';
  if (sortBar) sortBar.style.display = 'none';
  
  resultsContainer.innerHTML = `
    <div class="progress-bar"><div class="progress-bar__fill" style="width: 60%"></div></div>
    <p style="text-align: center; color: var(--text-tertiary); font-size: 0.85rem;">
      Analizando empresas de <strong>${marketName}</strong>...<br>
      <span style="font-size: 0.75rem;">Esto puede tardar 1-2 minutos</span>
    </p>
  `;

  try {
    let queryStr = `?market=${encodeURIComponent(market)}&max_per=${maxPer}&min_roic=${minRoic}&min_fcf_yield=${minFcf}&min_mos=${minMos}`;
    if (archetype !== 'all') queryStr += `&archetype=${archetype}`;
    if (sectorFilter !== 'all') queryStr += `&sector=${encodeURIComponent(sectorFilter)}`;
    queryStr += `&sort_by=mos`; // Initial sort

    const data = await apiGet('/explore' + queryStr);
    state.explorerResults = data.opportunities || [];
    
    // Show sort bar if results
    if (sortBar && state.explorerResults.length > 0) {
      sortBar.style.display = 'flex';
      // Reset active sort tab
      sortBar.querySelectorAll('.explorer-sort__btn').forEach(b => b.classList.remove('active'));
      sortBar.querySelector('[data-sort="mos"]')?.classList.add('active');
    }
    
    renderExplorerResults();
  } catch (err) {
    resultsContainer.innerHTML = renderEmptyState('❌', 'Error', 'No se pudo completar el escaneo. Inténtalo de nuevo.');
  } finally {
    state.isExploring = false;
    btn.classList.remove('btn-explore--loading');
    btn.innerHTML = '🔎 Buscar Oportunidades';
  }
}

// Client-side sort (re-sort cached results without re-fetching)
window.sortExplorerResults = function(sortKey, btnEl) {
  if (!state.explorerResults || state.explorerResults.length === 0) return;

  // Update active button
  document.querySelectorAll('.explorer-sort__btn').forEach(b => b.classList.remove('active'));
  if (btnEl) btnEl.classList.add('active');

  const sortFns = {
    mos: (a, b) => (b.margen_seguridad || 0) - (a.margen_seguridad || 0),
    roic: (a, b) => (b.roic_current || 0) - (a.roic_current || 0),
    fcf_yield: (a, b) => (b.fcf_yield || 0) - (a.fcf_yield || 0),
    per: (a, b) => ((a.per_actual || 999) - (b.per_actual || 999)), // Lower PER first
  };

  state.explorerResults.sort(sortFns[sortKey] || sortFns.mos);
  renderExplorerResults();
};

function renderExplorerResults() {
  const container = document.getElementById('explorer-results');
  
  if (state.explorerResults.length === 0) {
    container.innerHTML = renderEmptyState(
      '🔍',
      'Sin resultados',
      'No se encontraron empresas que cumplan todos los criterios. Prueba a relajar los filtros (bajar ROIC, subir PER máximo, o bajar MoS).'
    );
    return;
  }

  let html = `
    <div class="explorer-results__title">
      Oportunidades encontradas
      <span class="explorer-results__count">${state.explorerResults.length}</span>
    </div>
  `;

  for (const opp of state.explorerResults) {
    const mosColor = getMosColor(opp.margen_seguridad);
    const archBadge = opp.archetype_label ? `<span class="archetype-badge">${opp.archetype_label}</span>` : '';
    html += `
      <div class="card opportunity-card">
        <div class="opportunity-card__header">
          <div>
            <div class="opportunity-card__ticker">🏆 ${opp.ticker}</div>
            <div class="opportunity-card__name">${opp.empresa}</div>
            <div class="opportunity-card__meta">${opp.sector || ''} ${archBadge}</div>
          </div>
          <div style="text-align: right;">
            <div class="opportunity-card__price">${formatCurrency(opp.current_price)}</div>
            <div class="opportunity-card__intrinsic" style="font-size: 0.75rem; color: var(--text-tertiary);">
              Intrínseco: ${formatCurrency(opp.intrinsic_value)}
            </div>
          </div>
        </div>
        
        <div class="opportunity-card__metrics">
          <div class="opportunity-card__metric">
            <span class="opportunity-card__metric-label">MoS</span>
            <span class="opportunity-card__metric-value" style="color: ${mosColor}">${formatPercent(opp.margen_seguridad)}</span>
          </div>
          <div class="opportunity-card__metric">
            <span class="opportunity-card__metric-label">ROIC</span>
            <span class="opportunity-card__metric-value">${formatPercent(opp.roic_current)}</span>
          </div>
          <div class="opportunity-card__metric">
            <span class="opportunity-card__metric-label">PER</span>
            <span class="opportunity-card__metric-value">${opp.per_actual ? formatNumber(opp.per_actual, 1) + 'x' : '—'}</span>
          </div>
          <div class="opportunity-card__metric">
            <span class="opportunity-card__metric-label">FCF Yield</span>
            <span class="opportunity-card__metric-value">${formatPercent(opp.fcf_yield)}</span>
          </div>
        </div>

        ${opp.thesis ? `<div class="opportunity-card__thesis">${opp.thesis}</div>` : ''}

        <button class="btn-add-portfolio" onclick="addTickerFromExplorer('${opp.ticker}')">
          + Añadir a Cartera
        </button>
      </div>
    `;
  }

  container.innerHTML = html;
}

// ─── Sidebar ────────────────────────────────────────────────────

function openSidebar() {
  document.getElementById('sidebar-overlay').classList.add('active');
  document.getElementById('sidebar').classList.add('active');
}

function closeSidebar() {
  document.getElementById('sidebar-overlay').classList.remove('active');
  document.getElementById('sidebar').classList.remove('active');
}

function toggleAuthMode() {
  state.authMode = state.authMode === 'login' ? 'register' : 'login';
  
  const title = document.querySelector('#page-auth .page__title');
  const subtitle = document.querySelector('#page-auth .page__subtitle');
  const submitBtn = document.getElementById('auth-submit-btn');
  const toggleBtn = document.getElementById('auth-toggle-btn');
  
  if (state.authMode === 'register') {
    title.textContent = 'Crear Cuenta';
    subtitle.textContent = 'Regístrate para crear tu propia cartera aislada';
    submitBtn.textContent = 'Registrarse';
    toggleBtn.textContent = '¿Ya tienes cuenta? Inicia Sesión aquí';
  } else {
    title.textContent = 'Bienvenido';
    subtitle.textContent = 'Inicia sesión para acceder a tu cartera';
    submitBtn.textContent = 'Iniciar Sesión';
    toggleBtn.textContent = '¿No tienes cuenta? Regístrate aquí';
  }
}

async function handleAuth(e) {
  e.preventDefault();
  const userEl = document.getElementById('auth-username');
  const passEl = document.getElementById('auth-password');
  const submitBtn = document.getElementById('auth-submit-btn');
  
  const username = userEl.value.trim();
  const password = passEl.value.trim();
  if (!username || !password) return;
  
  const originalText = submitBtn.textContent;
  submitBtn.textContent = 'Cargando...';
  submitBtn.disabled = true;
  
  const endpoint = state.authMode === 'login' ? '/auth/login' : '/auth/register';
  
  try {
    // No usamos apiPost porque intercepta 401 y no incluye Authorization
    const res = await fetch(API_BASE + endpoint, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'ngrok-skip-browser-warning': 'true'
      },
      body: JSON.stringify({ username, password })
    });
    const data = await res.json();
    
    if (!res.ok) {
      showToast(`⚠️ ${data.error || 'Error de autenticación'}`, 'error');
    } else {
      showToast(`✅ ${data.message}`, 'success');
      state.token = data.token;
      state.role = data.role || 'user';
      state.username = data.username || 'Usuario';
      localStorage.setItem('token', data.token);
      localStorage.setItem('role', state.role);
      localStorage.setItem('username', state.username);
      userEl.value = '';
      passEl.value = '';
      navigate('dashboard');
    }
  } catch (err) {
    showToast('❌ Error de conexión al servidor', 'error');
  } finally {
    submitBtn.textContent = originalText;
    submitBtn.disabled = false;
  }
}

function updateUserDisplay() {
  document.querySelectorAll('.current-username-display').forEach(el => {
    el.textContent = state.username || 'Usuario';
  });
  document.querySelectorAll('.current-role-display').forEach(el => {
    el.textContent = state.role === 'admin' ? '👑 Administrador' : 'Inversor en Valor';
  });
}

function logout() {
  state.token = null;
  state.role = 'user';
  state.username = '';
  localStorage.removeItem('token');
  localStorage.removeItem('role');
  localStorage.removeItem('username');
  closeSidebar();
  navigate('auth');
  showToast('🚪 Has cerrado sesión', 'info');
}

// ─── Admin Panel ────────────────────────────────────────────────
async function loadAdminPanel() {
  const container = document.getElementById('admin-users-list');
  container.innerHTML = renderLoadingCards(1);
  
  try {
    const data = await apiGet('/admin/users');
    const users = data.users || [];
    
    if (users.length === 0) {
      container.innerHTML = renderEmptyState('👥', 'Sin usuarios', 'No hay usuarios registrados.');
      return;
    }
    
    let html = '';
    users.forEach(u => {
      const isMe = u.role === 'admin';
      const createdDate = new Date(u.created_at).toLocaleDateString('es-ES');
      html += `
        <div class="card" style="display: flex; justify-content: space-between; align-items: center;">
          <div>
            <div style="font-weight: 700; font-size: 1.1rem;">
              ${isMe ? '👑' : '👤'} ${u.username} 
              ${isMe ? '<span class="badge--positive" style="font-size:0.65rem; padding: 2px 6px;">Admin</span>' : ''}
            </div>
            <div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 4px;">
              Registrado: ${createdDate}
            </div>
            <div style="font-size: 0.8rem; color: var(--accent-primary); font-weight: 600; margin-top: 2px;">
              Empresas en cartera: ${u.portfolio_count}
            </div>
          </div>
          ${!isMe ? `
            <button onclick="deleteUser(${u.id}, '${u.username}')" style="background: rgba(239, 68, 68, 0.1); border: 1px solid var(--color-danger); color: var(--color-danger); padding: 8px 12px; border-radius: var(--radius-md); font-weight: 700; cursor: pointer; transition: all 0.2s;">
              Eliminar
            </button>
          ` : ''}
        </div>
      `;
    });
    
    container.innerHTML = html;
  } catch (err) {
    container.innerHTML = renderEmptyState('❌', 'Error de acceso', 'No tienes permisos de administrador o el servidor falló.');
  }
}

async function deleteUser(userId, username) {
  if (!confirm(`¿Estás seguro de que quieres eliminar a ${username} y toda su cartera para siempre?`)) return;
  
  try {
    await apiDelete(`/admin/users/${userId}`);
    showToast(`🗑️ Usuario ${username} eliminado`, 'success');
    loadAdminPanel();
  } catch (err) {
    showToast('❌ Error al eliminar usuario', 'error');
  }
}

// ─── Wiki Module (NOVEDAD) ──────────────────────────────────────
const wikiData = [
  {
    id: 'fcf-real',
    category: 'operativas',
    title: '💸 FCF Real (Free Cash Flow Real)',
    short: 'La caja neta real que genera la empresa sin maquillajes contables.',
    concept: 'Es el flujo de caja libre real calculado bajo estrictas normas GAAP. Representa el dinero contante y sonante neto que le queda a la empresa para reinversión, pago de dividendos o reducción de deuda, tras deducir todos los costes reales operativos y de capital.',
    formula: 'EBITDA - CAPEX - Intereses - Impuestos - ΔWorking Capital',
    utility: 'Es la métrica de oro en inversión en valor. A diferencia del FCF comercial de Yahoo que puede estar inflado con trampas contables, el FCF Real de la app te dice de manera cruda y real si el negocio produce caja o está quemando recursos.'
  },
  {
    id: 'roic',
    category: 'operativas',
    title: '💪 ROIC (Return on Invested Capital)',
    short: 'La rentabilidad obtenida por el capital total invertido en el negocio.',
    concept: 'Mide la eficiencia del equipo de dirección para asignar capital y generar retornos netos de alta calidad. Se calcula dividiendo el beneficio operativo neto después de impuestos (NOPAT) entre el capital total invertido (patrimonio neto más deuda total menos caja).',
    formula: 'NOPAT / (Patrimonio Neto + Deuda Total - Efectivo) * 100',
    utility: 'Un ROIC sostenido por encima del 15% es el indicador más potente de la existencia de ventajas competitivas duraderas (Motes o "Moats"). Indica que el negocio tiene poder de fijación de precios y un modelo altamente rentable.'
  },
  {
    id: 'ebitda-gaap',
    category: 'operativas',
    title: '🛡️ EBITDA Real vs Ajustado (Regla Contable)',
    short: 'Beneficios operativos limpios sin manipulaciones financieras ("Non-GAAP").',
    concept: 'El EBITDA GAAP representa los beneficios puros antes de intereses, impuestos, depreciaciones y amortizaciones. Muchos equipos directivos recurren al "EBITDA Ajustado" para ocultar gastos reales (como compensaciones basadas en acciones) e inflar artificialmente la rentabilidad aparente del negocio.',
    formula: 'EBIT + Depreciación y Amortización (Calculado de componentes operativos)',
    utility: 'La app calcula el EBITDA directamente desde sus componentes fundamentales y lo compara con el reportado por la empresa. Si la divergencia supera el 30%, la empresa se marca automáticamente como "No Elegible" debido al alto riesgo de falta de transparencia contable.'
  },
  {
    id: 'eps',
    category: 'operativas',
    title: '📈 EPS (Beneficio por Acción)',
    short: 'El beneficio neto de la empresa dividido entre el número de acciones en circulación.',
    concept: 'Representa la porción de beneficio asignada a cada acción ordinaria. Es la métrica más observada para evaluar la rentabilidad por acción de un negocio. En la app se analiza la tendencia del EPS (creciente, decreciente o estable) en los últimos 5 años y su promedio para estimar la tasa de crecimiento futuro del negocio.',
    formula: 'Beneficio Neto / Acciones Ordinarias en Circulación',
    utility: 'Es el insumo fundamental para valorar empresas mediante el modelo de Graham y para calcular el múltiplo PER. Su crecimiento constante a lo largo de los años es síntoma de ventajas competitivas sólidas.'
  },
  {
    id: 'wacc',
    category: 'valuation',
    title: '🎯 WACC Variable (Costo Medio Ponderado del Capital)',
    short: 'La tasa de descuento utilizada para traer los flujos de caja futuros al presente, ajustada por riesgo.',
    concept: 'Es el coste medio ponderado que le cuesta a la empresa financiar sus activos mediante fondos propios y deuda. En la aplicación el WACC es dinámico: las Utilities estables descuentan al 7-9%, las tecnológicas maduras al 9-10%, y el riesgo se ajusta según la capitalización de mercado (las Small Caps añaden +2% de riesgo).',
    formula: 'Tasa base por Sector ± Prima por Tamaño de Capitalización',
    utility: 'A mayor WACC (tasa de descuento), menor será el valor intrínseco resultante. El WACC variable penaliza a las empresas de alto riesgo y tamaño pequeño, recompensando a monopolios maduros con alta predictibilidad.'
  },
  {
    id: 'graham-value',
    category: 'valuation',
    title: '📜 Benjamin Graham (Valor Intrínseco)',
    short: 'Modelo clásico de valoración basado en beneficios y crecimiento estimado.',
    concept: 'Fórmula creada por el padre del Value Investing y mentor de Warren Buffett. Calcula el valor teórico de una acción multiplicando el EPS por un factor de crecimiento, ponderado frente al rendimiento histórico de bonos AAA de 1962 frente a los actuales.',
    formula: 'V = (EPS * (8.5 + 2g) * 4.4) / Rendimiento del Bono AAA actual',
    utility: 'Es ideal para empresas estables y maduras con beneficios positivos predecibles. Penaliza severamente a empresas sin beneficios históricos y nos da una base conservadora de valoración.'
  },
  {
    id: 'dcf-value',
    category: 'valuation',
    title: '💎 Discounted Cash Flow Dinámico (DCF)',
    short: 'Valoración teórica descontando los flujos de caja futuros al presente.',
    concept: 'Mapea la capacidad futura del negocio de generar caja. La app utiliza un motor adaptativo: para empresas maduras usa un DCF estándar (10 años); para "Compounders" usa un DCF Multi-Fase (alto crecimiento inicial que decae a la media); y para empresas de Hipercrecimiento usa un DCF basado en Revenue con márgenes objetivo.',
    formula: 'Σ NPV(Flujos Proyectados según Arquetipo) + NPV(Valor Terminal Perpetuo a 2.5%)',
    utility: 'Es la metodología de valoración más rigurosa a nivel financiero. Al adaptarse al "arquetipo" de la empresa, evita valorar a una biotecnológica emergente con las mismas reglas que a un banco consolidado.'
  },
  {
    id: 'per',
    category: 'valuation',
    title: '📊 PER (Price to Earnings Ratio)',
    short: 'Múltiplo de valoración que indica cuántas veces el beneficio neto se paga por acción.',
    concept: 'Es la relación entre el precio actual de la acción y el beneficio por acción (EPS). Indica el número de años de beneficio neto que se necesitarían para recuperar la inversión inicial si las ganancias permanecieran constantes. Se compara el PER actual con el promedio de PER de los últimos 5 años para calcular el Margen de Seguridad Relativo.',
    formula: 'Precio de la Acción / EPS (Earnings Per Share)',
    utility: 'Es el múltiplo de valoración de mercado clásico. Nos dice si una acción cotiza cara o barata en relación con sus ganancias y en comparación directa con cómo el mercado la ha valorado en el pasado.'
  },
  {
    id: 'ev-fcf',
    category: 'valuation',
    title: '💸 EV/FCF (Enterprise Value / Free Cash Flow)',
    short: 'Múltiplo de valoración que compara el valor total del negocio con el FCF que genera.',
    concept: 'Es la relación entre el Valor de Empresa (Enterprise Value = Capitalización de Mercado + Deuda Total - Efectivo) y el Flujo de Caja Libre Real. Es considerado un múltiplo muy superior al PER ya que mide el coste real de adquirir toda la compañía frente al efectivo neto que produce y es menos susceptible a manipulaciones contables.',
    formula: 'Enterprise Value / Free Cash Flow (Real)',
    utility: 'Es el múltiplo prioritario por la aplicación para calcular el Margen de Seguridad Relativo, ya que refleja fielmente la capacidad de generación de efectivo del negocio.'
  },
  {
    id: 'ms-absoluto',
    category: 'valuation',
    title: '🟢 Margen de Seguridad Absoluto ($MS_{Abs}$)',
    short: 'El descuento del precio de cotización frente a su valor intrínseco fundamental.',
    concept: 'El pilar sagrado de la inversión en valor. Compara el valor intrínseco de la empresa (tomando de forma conservadora el menor entre Graham y el DCF) frente a su precio actual de cotización.',
    formula: '((Valor Intrínseco - Precio Actual) / Valor Intrínseco) * 100',
    utility: 'Determina si la empresa está infravalorada por los flujos de caja reales que produce. Buscamos un descuento mínimo del 15% al 20% para contar con un colchón de seguridad que nos proteja contra imprevistos del mercado.'
  },
  {
    id: 'ms-relativo',
    category: 'valuation',
    title: '🟡 Margen de Seguridad Relativo ($MS_{Rel}$)',
    short: 'Compara la valoración actual frente a su promedio histórico de 5 años.',
    concept: 'Evalúa la valoración del mercado de la empresa frente a su propio promedio histórico de múltiplos de los últimos 5 años (priorizando EV/FCF Real y usando PER como alternativa).',
    formula: '((Múltiplo Medio 5y - Múltiplo Actual) / Múltiplo Medio 5y) * 100',
    utility: 'Te dice si la acción está barata en comparación con cómo el mercado la ha valorado en el pasado. Es sumamente útil para detectar si estamos comprando una excelente empresa a múltiplos históricamente bajos.'
  },
  {
    id: 'semaforo-valor',
    category: 'strategy',
    title: '🚥 Semáforo de Inversión',
    short: 'Clasificación automática analizando ambos márgenes simultáneamente.',
    concept: 'Lógica algorítmica integrada en la aplicación que analiza los dos tipos de márgenes de seguridad para emitir una alerta definitiva.',
    formula: 'Convergencia matemática de MS Absoluto > 15% y MS Relativo > 10%',
    utility: 'Ayuda a evitar trampas de valor.\n\n🟢 STRONG BUY: Convergencia total. Barata por fundamentales y barata históricamente.\n🟡 MANTENER: Señal mixta. Requiere análisis cualitativo profundo.\n🔴 SOBREVALORADA: Margen absoluto y relativo negativos. Alto riesgo.\n🚫 NO ELEGIBLE: Falta de transparencia o EBITDA Ajustado manipulado.'
  },
  {
    id: 'moat',
    category: 'qualitative',
    title: '🛡️ Foso Económico (Economic Moat)',
    short: 'La ventaja competitiva sostenible que protege al negocio de sus competidores.',
    concept: 'Representa la capacidad de una empresa para mantener ventajas competitivas a largo plazo y resguardar su cuota de mercado y rentabilidad frente al ataque de competidores. Se clasifica en la app en base al ROIC histórico medio: Wide Moat (Foso Amplio, ROIC > 18%), Narrow Moat (Foso Estrecho, ROIC > 12%) o Sin Foso. Ejemplos incluyen Efectos de Red, Activos Intangibles (Marca/Patentes), Bajos Costes de Producción o Altos Costes de Cambio.',
    formula: 'ROIC Histórico Medio > 18% (Wide Moat) | > 12% (Narrow Moat)',
    utility: 'Asegura que los beneficios y flujos de caja futuros sigan creciendo y no sean erosionados por competidores salvajes. En la app, determina la fuerza del foso y asocia ventajas automáticas según el sector del negocio.'
  },
  {
    id: 'skin-in-the-game',
    category: 'qualitative',
    title: '👤 Skin in the Game (Alineación de Directiva)',
    short: 'El porcentaje de acciones del negocio que está en manos de sus propios directivos.',
    concept: 'Representa la alineación de intereses entre los gestores y los accionistas. Si el CEO y los directores clave poseen una parte significativa de la empresa en acciones comunes, sufrirán las pérdidas y celebrarán las ganancias en la misma proporción que los accionistas externos.',
    formula: 'Acciones de Directores / Acciones Totales en Circulación * 100',
    utility: 'Un alto Skin in the Game (>0.1% en megacaps o >1.0% en general) reduce los problemas de agencia, asegurando que la directiva tome decisiones para incrementar el valor intrínseco del negocio a largo plazo en lugar de priorizar bonos cortoplacistas.'
  },
  {
    id: 'buybacks',
    category: 'qualitative',
    title: '📈 Recompra de Acciones (Share Buybacks)',
    short: 'Reducción del número de acciones en circulación para crear valor inteligente.',
    concept: 'Ocurre cuando la propia empresa utiliza su flujo de caja libre para comprar sus propias acciones en el mercado abierto y amortizarlas. Esto reduce el número total de acciones en circulación, incrementando automáticamente el porcentaje de propiedad, los beneficios por acción (EPS) y el flujo de caja por acción de los accionistas restantes sin requerir desembolso adicional.',
    formula: 'Acciones en Circulación (Año Actual) < Acciones en Circulación (Años Anteriores)',
    utility: 'Es una de las mejores herramientas de asignación de capital si se hace a precios inferiores al valor intrínseco. En el motor, el decrecimiento en el histórico de acciones en circulación activa la calificación de recompras inteligentes.'
  },
  {
    id: 'caso-ferrari',
    category: 'strategy',
    title: '🟢 Caso Ferrari (Compra de Calidad)',
    short: 'Ascenso a compra de empresas extraordinarias que cotizan a precios razonables.',
    concept: 'Es la aplicación práctica de la famosa cita de Warren Buffett: "Es mucho mejor comprar una empresa maravillosa a un precio justo, que una empresa justa a un precio maravilloso". Aplica a empresas excepcionales (Wide Moat, ROIC > 18%) que tienen márgenes de seguridad positivos pero no alcanzan los descuentos profundos requeridos para Strong Buy.',
    formula: 'ROIC > 18% Y MS Absoluto > 0 Y MS Relativo > 0 Y (Recompras o Insiders > 0.1%)',
    utility: 'Evita perder oportunidades en negocios de altísima rentabilidad sobre el capital (como Ferrari, Apple o Coca-Cola) que rara vez cotizan con descuentos masivos, permitiendo comprarlos cuando están a un valor razonable con directivas fuertemente alineadas.'
  },
  {
    id: 'governance-risks',
    category: 'strategy',
    title: '⚠️ Riesgos de Gobernanza y Auditoría',
    short: 'Métricas de gobernanza corporativa que alertan sobre riesgos internos y contables.',
    concept: 'Mapea las puntuaciones de riesgo de la directiva, compensación y auditoría suministradas por agencias calificadoras de gobernanza. Evalúa si el consejo de administración tiene incentivos desalineados, compensaciones excesivas desvinculadas del rendimiento del accionista, o prácticas contables agresivas.',
    formula: 'yfinance Risk Scores (Escala del 1 al 10, donde >6 representa un riesgo elevado)',
    utility: 'Permite detectar alertas cualitativas graves antes de que se reflejen de forma destructiva en los estados financieros. Una puntuación alta previene pérdidas por fraude, dilución descontrolada u opacidad contable.'
  },
  {
    id: 'tam-sam-som',
    category: 'qualitative',
    title: '🌐 TAM, SAM y SOM (Pista de Crecimiento)',
    short: 'Métricas de dimensionamiento de mercado que indican la pista de crecimiento futuro y saturación del negocio.',
    concept: 'Representan tres capas del mercado potencial de una empresa:\n\n• TAM (Total Addressable Market): El tamaño total del mercado global si la empresa tuviera 100% de cuota y no hubiera competencia.\n• SAM (Serviceable Addressable Market): El segmento del mercado al que los productos de la empresa están realmente enfocados y pueden atender.\n• SOM (Serviceable Obtainable Market): La porción del SAM que la empresa puede capturar de forma viable en el corto/medio plazo.\n\nEn la app, comparamos los ingresos anuales de la empresa (convertidos a USD) con el TAM de su sector para calcular de forma automatizada su cuota de mercado y nivel de saturación.',
    formula: 'Cuota de Mercado (%) = (Ingresos Anuales de la Empresa en USD / TAM del Sector) * 100',
    utility: 'Actúa como un indicador crítico de crecimiento futuro.\n\nUna excelente empresa de alta calidad (alto ROIC) que opera en un TAM gigante y posee una cuota minúscula (SOM < 2%) es una joya en potencia, ya que tiene décadas de crecimiento por delante (compounding). Por el contrario, si una empresa ya factura casi todo su TAM, está saturada y carece de escalabilidad inercial.'
  },
  {
    id: 'market-cap',
    category: 'mercado',
    title: '💰 Capitalización de Mercado (Market Cap)',
    short: 'El valor total de mercado de todas las acciones en circulación de la empresa.',
    concept: 'Es una medida básica que indica el tamaño financiero de una empresa en bolsa. Se obtiene multiplicando el precio actual de la acción por el número total de acciones en circulación. Divide a las empresas en Megacaps, Largecaps, Midcaps y Smallcaps.',
    formula: 'Precio de la Acción * Número Total de Acciones en Circulación',
    utility: 'Determina el tamaño del negocio y su liquidez. En inversión de valor, se utiliza como base para calcular el Enterprise Value (EV) y para evaluar el rendimiento de los flujos de caja (FCF Yield) frente al tamaño total del capital accionario.'
  },
  {
    id: 'dividend-yield',
    category: 'mercado',
    title: '💵 Rentabilidad por Dividendo (Dividend Yield)',
    short: 'El porcentaje anual de dividendos que reparte la empresa en relación con el precio de su acción.',
    concept: 'Es un ratio financiero que muestra cuánto paga una empresa en dividendos cada año en relación con el precio actual de cotización de sus acciones. Representa el retorno inmediato por flujo de caja que recibe el accionista por su tenencia pasiva.',
    formula: '(Dividendo Anual por Acción / Precio de la Acción) * 100',
    utility: 'Permite evaluar la generación de renta pasiva de la inversión. Un dividend yield saludable (2%-5%) respaldado por un negocio de alta calidad (alto ROIC) es excelente. Sin embargo, yields extremadamente altos (>10%) suelen ser trampas de valor donde el precio de la acción está colapsando debido al deterioro del negocio.'
  },
  {
    id: 'payout-ratio',
    category: 'mercado',
    title: '📈 Payout Ratio (Ratio de Distribución de Dividendos)',
    short: 'El porcentaje de los beneficios netos que la empresa destina al pago de dividendos.',
    concept: 'Indica qué proporción de las ganancias de la empresa se devuelve a los accionistas en forma de dividendos en lugar de retenerse en el negocio para su reinversión, pago de deuda o recompra de acciones.',
    formula: '(Dividendos Totales / Beneficio Neto) * 100',
    utility: 'Mide la sostenibilidad del dividendo. Un payout ratio inferior al 60% se considera seguro y sostenible en la mayoría de los sectores. Un payout ratio superior al 100% indica que la empresa paga más de lo que gana, lo que compromete su futuro financiero y anticipa un recorte inminente del dividendo.'
  },
  {
    id: 'growth-estimate',
    category: 'mercado',
    title: '🚀 Crecimiento Estimado (Expected Growth)',
    short: 'La tasa anual de crecimiento proyectada para los ingresos o beneficios de la empresa.',
    concept: 'Es la expectativa de crecimiento futuro (g) calculada por el consenso de analistas del mercado o estimada a partir de la tendencia histórica de la empresa. Es un parámetro crítico que alimenta los modelos matemáticos de valoración.',
    formula: 'Estimación del Consenso de Analistas (Earnings/Revenue Growth) en Yahoo Finance',
    utility: 'Es el corazón de las valoraciones de Graham y DCF. Un crecimiento estimado alto justifica valoraciones intrínsecas más elevadas. No obstante, el inversor de valor debe aplicar prudenccia y descontar estas estimaciones para evitar pagar de más por un optimismo excesivo.'
  },
  {
    id: 'analyst-target',
    category: 'mercado',
    title: '🎯 Precio Objetivo de Analistas (Analyst Target)',
    short: 'La media de los precios proyectados a 12 meses por los analistas profesionales de Wall Street.',
    concept: 'Representa el valor promedio de cotización que los analistas profesionales de bancos de inversión y firmas de análisis estiman que alcanzará la acción en un horizonte de 12 meses.',
    formula: 'Media Aritmética de las Estimaciones de Analistas (Target Mean Price en yfinance)',
    utility: 'Sirve como una referencia externa sobre el sentimiento del mercado institucional. Sin embargo, no debe usarse como sustituto del valor intrínseco fundamental (Graham/DCF), ya que los analistas institucionales suelen ser excesivamente influenciables por las tendencias a corto plazo y el precio reciente de cotización.'
  },
  {
    id: 'quality-rating',
    category: 'operativas',
    title: '⭐ Calidad de la Empresa (El Algoritmo)',
    short: 'La nota global de salud financiera y rentabilidad del negocio.',
    concept: 'Es un sistema de puntuación interno (de 0 a 9 puntos) que evalúa si un negocio es estructuralmente sano. Premia a las empresas que generan mucho retorno por cada euro invertido (ROIC), cuyos beneficios (EPS) y caja (FCF) crecen año tras año, y que tienen un buen Margen de Seguridad.',
    formula: 'Suma de puntos: ROIC > 20% (3pts), EPS creciente (2pts), FCF creciente (2pts), MoS > 30% (2pts).',
    utility: '⭐ Alta Calidad (7 a 9 pts): Negocios excepcionales con fuertes ventajas competitivas (Wide Moat).\n✅ Calidad Aceptable (4 a 6 pts): Empresas sólidas y rentables.\n⚠️ Calidad Media (2 a 3 pts): Negocios estancados o muy dependientes del ciclo económico.\n❌ Calidad Baja (0 a 1 pt): Destructores de valor, altísimo riesgo. Huye de ellas.'
  },
  {
    id: 'interest-coverage',
    category: 'operativas',
    title: '🏦 Cobertura de Intereses (Interest Coverage)',
    short: 'Capacidad de la empresa para pagar los intereses de su deuda con su beneficio operativo.',
    concept: 'Indica cuántas veces podría la empresa pagar sus gastos financieros (intereses) utilizando su Beneficio Operativo (EBIT). Es una métrica vital de solvencia. Si el ratio cae por debajo de 3x, significa que la empresa destina una parte peligrosa de su beneficio a pagar al banco, acercándose al riesgo de quiebra si sus ventas caen.',
    formula: 'EBIT / Gastos por Intereses',
    utility: 'Evita caer en "Value Traps" (trampas de valor). Una empresa puede cotizar muy barata, pero si su Cobertura de Intereses es roja (<3x), el mercado está descontando un posible colapso crediticio.'
  },
  {
    id: 'net-debt-ebitda',
    category: 'operativas',
    title: '💳 Net Debt / EBITDA',
    short: 'Los años que tardaría la empresa en pagar toda su deuda si el EBITDA se mantuviera constante.',
    concept: 'Mide el apalancamiento bruto de la empresa descontando la caja que ya tiene en el banco. Compara la deuda neta contra la capacidad bruta de generar caja (EBITDA). Un valor por encima de 3x se considera deuda de alto riesgo ("High Yield" o bono basura).',
    formula: '(Deuda Total - Efectivo y Equivalentes) / EBITDA',
    utility: 'Es el ratio de apalancamiento más utilizado en banca de inversión. Te ayuda a ver instantáneamente si la empresa está abusando del endeudamiento para crecer o si tiene un balance "fortaleza" (ratio < 1x).'
  },
  {
    id: 'margenes-rentabilidad',
    category: 'operativas',
    title: '📊 Análisis de Márgenes (Bruto, Op. y Neto)',
    short: 'La conversión de cada dólar vendido en beneficio contante y sonante.',
    concept: 'El Margen Bruto revela si la empresa tiene "Pricing Power" (si puede subir precios sin perder clientes). El Margen Operativo indica la eficiencia de sus costes fijos (marketing, I+D). El Margen Neto es lo que queda al final tras pagar impuestos e intereses.',
    formula: 'Beneficio Bruto (o EBIT, o Neto) / Ventas Totales',
    utility: 'Si el Margen Bruto es > 40-50%, la empresa tiene un excelente Foso Económico. Si los márgenes se estrechan con el tiempo, la competencia está destruyendo sus ventajas.'
  },
  {
    id: 'growth-haircut',
    category: 'valuation',
    title: '✂️ Recorte Preventivo de Crecimiento (Haircut)',
    short: 'Auditoría cruzada para evitar estimaciones de crecimiento irreales.',
    concept: 'Si las previsiones estiman que el EPS crecerá a un 30% anual pero históricamente las Ventas (Revenue) solo crecen al 5%, la aplicación asume que es insostenible (provocado por recompras masivas o expansión temporal de márgenes).',
    formula: 'Si EPS Growth > 1.5x Revenue Growth → Growth = Revenue Growth * 1.5',
    utility: 'Ancla las expectativas del algoritmo a la realidad de las ventas orgánicas. Impide que compremos empresas basándonos en proyecciones artificialmente infladas.'
  },
  {
    id: 'arquetipos-valoracion',
    category: 'valuation',
    title: '🧩 Arquetipos de Valoración',
    short: 'Clasificación automática para usar el modelo matemático correcto según el tipo de empresa.',
    concept: 'No puedes valorar a un Banco usando el modelo de crecimiento de Benjamin Graham, ni a una empresa de alto crecimiento sin beneficios usando PER. La app clasifica cada empresa en: Classic Value, Compounder, Hypergrowth, Financiero o REIT/Utility.',
    formula: 'Clasificación basada en el Sector, EPS, ROIC y Tasa de Crecimiento.',
    utility: 'Aplica a las Financieras el ratio P/Book, a las Utilities el modelo DDM (Descuento de Dividendos) y a las Tecnológicas el DCF. Esto da como resultado valoraciones realistas y fiables.'
  },
  {
    id: 'compounder',
    category: 'strategy',
    title: '🚀 Compounder (Componedora de Capital)',
    short: 'El santo grial del Value Investing: crecimiento y rentabilidad excepcionales.',
    concept: 'Empresas con fortísimas ventajas competitivas (Wide Moat), un ROIC mantenido muy alto (>15-20%) y capaces de crecer a tasas de doble dígito (15-25%) de forma consistente durante años. Reinvierten su caja a altísimas tasas de retorno.',
    formula: 'Se valoran usando un DCF Multi-Fase (crecimiento inicial alto que decae progresivamente).',
    utility: 'Son empresas que de media cotizan "caras" (PER alto), pero que justifican esa valoración gracias a su brutal efecto compuesto a largo plazo (ej. Microsoft, Visa, ASML).'
  },
  {
    id: 'hypergrowth',
    category: 'strategy',
    title: '🔥 Hypergrowth (Hipercrecimiento)',
    short: 'Empresas disruptivas creciendo a tasas salvajes, a menudo sin beneficios actuales.',
    concept: 'Compañías emergentes o líderes de nuevas tendencias (IA, Cloud, Biotech) que crecen en ventas a más del +30% anual. Sus beneficios contables (EPS) suelen ser nulos o negativos porque reinvierten todo en expandirse y dominar el mercado.',
    formula: 'Se valoran usando un DCF basado en Ventas (Revenue) proyectando márgenes futuros.',
    utility: 'Alto riesgo, alta recompensa. La app penaliza el valor si los márgenes proyectados no son realistas. El Graham arrojará 0€, dependemos puramente de sus ventas futuras.'
  },
  {
    id: 'classic-value',
    category: 'strategy',
    title: '🕰️ Classic Value (Valor Clásico)',
    short: 'Negocios maduros, aburridos pero altamente predecibles y rentables.',
    concept: 'Empresas industriales, de consumo defensivo o maduras que crecen poco (0-10% anual) pero son auténticas "vacas lecheras" (*Cash Cows*). Generan montañas de Flujo de Caja Libre real y suelen repartirlo en jugosos dividendos o recompras de acciones.',
    formula: 'Se valoran usando el modelo de Benjamin Graham tradicional y el DCF a 10 años.',
    utility: 'El foco principal de Warren Buffett en sus inicios. Son inversiones muy seguras si se compran con un buen margen de seguridad y tienen un suelo de valoración muy sólido.'
  },
  {
    id: 'financial-reit',
    category: 'strategy',
    title: '🏦 Financieras y REITs',
    short: 'Bancos, aseguradoras y Sociedades Anónimas Cotizadas de Inversión Inmobiliaria.',
    concept: 'Negocios cuyo "producto" es el propio dinero o propiedades inmobiliarias. Sus balances no se pueden analizar como los de una empresa normal (tienen deuda masiva que en realidad son depósitos de clientes).',
    formula: 'Las Financieras se valoran usando Precio/Valor en Libros (Price to Book Justificado). Los REITs con el Modelo de Descuento de Dividendos (DDM).',
    utility: 'La app desactiva automáticamente el DCF para este tipo de empresas, ya que el FCF no tiene sentido contable en bancos. Te protege de cometer errores graves de valoración.'
  },
  {
    id: 'sector-benchmark',
    category: 'strategy',
    title: '📈 Benchmark Sectorial',
    short: 'Comparativa en tiempo real contra las medias estandarizadas de la industria.',
    concept: 'Un PER de 15x es barato para el sector Software (media 25x) pero es caro para el sector Bancario (media 12x). La aplicación almacena internamente las medianas de PER y ROIC de todos los sectores de la economía.',
    formula: '(Ratio Empresa - Media Sectorial) / Media Sectorial',
    utility: 'Proporciona contexto al instante. Se inyecta directamente en el Informe Cualitativo indicando si la empresa cotiza con prima o descuento sectorial y si su rentabilidad supera a sus rivales.'
  },
  {
    id: 'peg-ratio',
    category: 'growth',
    title: '📊 PEG Ratio (Peter Lynch)',
    short: 'Valoración relativa al crecimiento: ¿estás pagando demasiado por el crecimiento futuro?',
    concept: 'Creado por el legendario gestor Peter Lynch (Fidelity Magellan Fund). El PEG ajusta el múltiplo PER por la tasa de crecimiento esperada del beneficio. Un PER de 50x puede parecer carísimo en análisis Value clásico, pero si la empresa crece al 50% anual, el PEG es 1.0 — precio justo. Es la metodología GARP (Growth at a Reasonable Price).',
    formula: 'PEG = PER / Tasa de Crecimiento EPS (%)',
    utility: 'PEG < 1.0 = Infravalorada para su crecimiento (oportunidad Growth). PEG ≈ 1.0-2.0 = Precio justo. PEG > 2.0 = Sobrevalorada incluso considerando su crecimiento. La app calcula PEG Trailing (PER actual) y PEG Forward (PER estimado por analistas).'
  },
  {
    id: 'rule-of-40',
    category: 'growth',
    title: '🔥 Regla del 40 (Rule of 40)',
    short: 'El estándar de oro para evaluar empresas SaaS y tecnológicas de alto crecimiento.',
    concept: 'Originada en el mundo del capital riesgo (VC) de Silicon Valley. Suma el porcentaje de crecimiento de ventas y el margen de flujo de caja libre. La idea es que una empresa puede sacrificar rentabilidad si crece rápidamente, o viceversa, mientras la suma sea mayor que 40.',
    formula: 'Rule of 40 = Crecimiento Revenue (%) + Margen FCF (%)',
    utility: 'Score ≥ 40 = Premium (empresa élite que merece cotizar a múltiplos altos). Score 20-40 = Aceptable. Score < 20 = Débil (necesita mejorar crecimiento o rentabilidad). Útil para empresas como CrowdStrike, Shopify o Palantir donde el Value clásico falla.'
  },
  {
    id: 'ev-revenue',
    category: 'growth',
    title: '💰 EV/Revenue (Enterprise Value sobre Ventas)',
    short: 'Múltiplo de valoración basado en ventas, clave para empresas sin beneficios.',
    concept: 'Cuando una empresa no tiene beneficios (EPS negativo) ni flujo de caja libre positivo, el PER y el DCF tradicional no funcionan. El EV/Revenue compara el valor total de la empresa (capitalización + deuda neta) contra sus ingresos. La app también calcula el EV/Revenue Forward a 3 años, proyectando las ventas futuras al ritmo de crecimiento actual.',
    formula: 'EV/Revenue = Enterprise Value / Ingresos Totales Anuales',
    utility: 'Permite comparar empresas de hipercrecimiento entre sí independientemente de su rentabilidad actual. Un EV/Revenue Forward de 5x es mucho más barato que uno de 20x. La proyección a 3 años muestra lo barata que puede estar una empresa si mantiene su ritmo de crecimiento.'
  },
  {
    id: 'epv-value',
    category: 'valuation',
    title: '🧮 Earnings Power Value (EPV) Fallback',
    short: 'Valoración alternativa para empresas cíclicas o con CAPEX pesado y FCF distorsionado.',
    concept: 'Es una metodología de valoración desarrollada por el profesor Bruce Greenwald (Columbia Business School) que asume que la empresa dejará de crecer y operará en un estado de beneficios constantes a perpetuidad. La app la activa automáticamente como salvaguarda (\'fallback\') cuando el FCF Real de una empresa madura y con beneficios netos estables es inusualmente bajo debido a inversiones de capital intensivas y temporales (CAPEX pesado), asegurando que no descartemos excelentes oportunidades por anomalías temporales de flujo de caja libre.',
    formula: 'EPV = (Beneficio Neto Promedio de 5 años / WACC + Caja actual - Deuda total) / Acciones en circulación',
    utility: 'Evita el sesgo del DCF tradicional que penaliza severamente a empresas industriales o cíclicas estables en momentos de alta inversión. Si el DCF sale extremadamente bajo por culpa del CAPEX pero la empresa sigue imprimiendo beneficios contables sólidos, el EPV nos da una red de seguridad analítica de valoración de "poder de beneficios".'
  },
  {
    id: 'subunit-currency',
    category: 'mercado',
    title: '💱 Ajuste de Subunidad Monetaria (GBp / GBX) y Multidivisa',
    short: 'Conversión inteligente para acciones listadas en peniques y discrepancias de divisas.',
    concept: 'Muchas empresas que cotizan en la bolsa de Londres (LSE) muestran su precio de cotización en peniques esterlinas (GBp o GBX, por ejemplo, 3118.0p) en lugar de libras esterlinas (GBP, 31.18£). Sin embargo, sus estados financieros presentados en sus reportes anuales se expresan en libras esterlinas (GBP) o incluso en dólares (USD). Si un algoritmo compara directamente el precio de 3118p con los beneficios de 2.5£ por acción, el margen de seguridad resultante saldrá absurdamente negativo.',
    formula: 'Si cotización = GBp/GBX → Precio / 100 | Tipo de cambio implícito derivado de PER y EPS',
    utility: 'El motor de la app detecta automáticamente los tickers de Londres (.L) y corrige la subunidad dividiendo por 100 el precio de cotización. Además, si la cotización está en una divisa y los reportes en otra, el sistema calcula de forma dinámica un tipo de cambio cruzado exacto basado en la relación entre el PER y el beneficio por acción (EPS), asegurando que todas las métricas de margen de seguridad y rendimientos sean 100% consistentes y libres de distorsiones multidivisa.'
  },
  {
    id: 'filtros-avanzados',
    category: 'strategy',
    title: '🎛️ Filtros Avanzados y Score de Calidad (Explorador)',
    short: 'Uso de los nuevos deslizadores dinámicos y perfiles para buscar oportunidades.',
    concept: 'El nuevo Opportunity Explorer permite filtrar en tiempo real las empresas escaneadas utilizando deslizadores táctiles para cuatro métricas clave: Nota de Calidad mínima, Tasa de Crecimiento mínima, Dividend Yield mínimo y Margen de Seguridad Absoluto mínimo. Los resultados se pueden ordenar de forma dinámica por cualquiera de estas columnas haciendo clic en las pestañas de ordenación.',
    formula: 'Calificación de Calidad (0-9 pts) = ROIC (3pts) + Crecimiento EPS (2pts) + Crecimiento FCF (2pts) + MoS > 30% (2pts).',
    utility: 'Te permite aplicar "Perfiles de Exploración" predefinidos al instante. Por ejemplo, pulsando "Compounders de Calidad" se ajustan los sliders a alta calidad y crecimiento medio, mientras que con "Cazador de Dividendos" se prioriza el Dividend Yield. Puedes refinar la búsqueda filtrando por Arquetipo y Sector/Mercado.'
  }
];

let activeWikiCategory = 'all';

function loadWiki() {
  activeWikiCategory = 'all';
  
  // Reset filter chips UI
  document.querySelectorAll('.wiki-categories .filter-chip').forEach(chip => {
    chip.classList.toggle('active', chip.id === 'chip-all');
  });
  
  const searchInput = document.getElementById('input-wiki-search');
  if (searchInput) searchInput.value = '';
  
  renderWiki(wikiData);
}

function filterWikiCategory(category) {
  activeWikiCategory = category;
  
  // Update chips UI
  document.querySelectorAll('.wiki-categories .filter-chip').forEach(chip => {
    chip.classList.toggle('active', chip.id === `chip-${category}`);
  });
  
  filterWiki();
}

function renderWikiCardHtml(item) {
  return `
    <div class="card wiki-card" id="wiki-card-${item.id}" onclick="toggleWikiCard('${item.id}')">
      <div class="wiki-card__header" style="display: flex; justify-content: space-between; align-items: center;">
        <div class="wiki-card__title" style="font-weight: 700; font-size: 0.95rem; color: var(--text-primary);">${item.title}</div>
        <div class="wiki-card__toggle-icon" id="wiki-icon-${item.id}" style="font-size: 1.2rem; color: var(--text-tertiary); transition: transform 0.2s;">+</div>
      </div>
      <p class="wiki-card__short" style="font-size: 0.78rem; color: var(--text-secondary); margin-top: var(--space-xs);">${item.short}</p>
      
      <div class="wiki-card__expanded" id="wiki-expanded-${item.id}" style="display: none; margin-top: var(--space-md);">
        <div class="wiki-card__divider" style="height: 1px; background: var(--border-subtle); margin-bottom: var(--space-sm);"></div>
        
        <div class="wiki-card__section" style="margin-bottom: var(--space-sm);">
          <span class="wiki-card__section-label" style="font-size: 0.72rem; font-weight: 600; text-transform: uppercase; color: var(--accent-primary); display: block; margin-bottom: 2px;">Concepto Fundamental:</span>
          <p class="wiki-card__section-text" style="font-size: 0.8rem; color: var(--text-secondary); line-height: 1.6;">${item.concept}</p>
        </div>
        
        ${item.formula ? `
          <div class="wiki-card__section" style="margin-bottom: var(--space-sm);">
            <span class="wiki-card__section-label" style="font-size: 0.72rem; font-weight: 600; text-transform: uppercase; color: var(--accent-primary); display: block; margin-bottom: 2px;">Fórmula:</span>
            <code class="wiki-card__code" style="font-family: var(--font-mono); font-size: 0.74rem; background: var(--bg-elevated); padding: 4px var(--space-sm); border-radius: var(--radius-sm); color: var(--text-primary); display: inline-block; border: 1px solid var(--border-subtle);">${item.formula}</code>
          </div>
        ` : ''}
        
        <div class="wiki-card__section">
          <span class="wiki-card__section-label" style="font-size: 0.72rem; font-weight: 600; text-transform: uppercase; color: var(--accent-primary); display: block; margin-bottom: 2px;">Utilidad Práctica:</span>
          <p class="wiki-card__section-text" style="font-size: 0.8rem; color: var(--text-secondary); line-height: 1.6; white-space: pre-line;">${item.utility}</p>
        </div>
      </div>
    </div>
  `;
}

function renderWiki(data) {
  const container = document.getElementById('wiki-list');
  if (!container) return;

  if (data.length === 0) {
    container.innerHTML = renderEmptyState('📖', 'Sin resultados', 'No se encontraron términos que coincidan con la búsqueda.');
    return;
  }

  let html = '';
  
  if (activeWikiCategory === 'all') {
    const categoriesMap = {
      'operativas': '📊 Métricas Operativas y Rentabilidad',
      'mercado': '💰 Dividendos y Métricas de Mercado',
      'valuation': '🧮 Modelos y Metodologías de Valoración',
      'qualitative': '🔍 Auditoría Cualitativa & Foso',
      'strategy': '🚦 Lógica de Inversión y Estrategias'
    };
    
    for (const [catId, catTitle] of Object.entries(categoriesMap)) {
      const catItems = data.filter(item => item.category === catId);
      if (catItems.length > 0) {
        html += `
          <div class="wiki-group-header" style="font-size: 0.76rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: var(--accent-primary); margin: var(--space-lg) 0 var(--space-sm); display: flex; align-items: center; gap: var(--space-xs); border-left: 3px solid var(--accent-primary); padding-left: var(--space-sm);">
            ${catTitle}
          </div>
        `;
        for (const item of catItems) {
          html += renderWikiCardHtml(item);
        }
      }
    }
  } else {
    for (const item of data) {
      html += renderWikiCardHtml(item);
    }
  }
  
  container.innerHTML = html;
}

function toggleWikiCard(id) {
  const exp = document.getElementById(`wiki-expanded-${id}`);
  const icon = document.getElementById(`wiki-icon-${id}`);
  const card = document.getElementById(`wiki-card-${id}`);
  
  if (!exp || !icon) return;

  if (exp.style.display === 'none') {
    exp.style.display = 'block';
    icon.textContent = '✕';
    icon.style.transform = 'rotate(90deg)';
    card.style.borderColor = 'var(--accent-primary)';
    card.style.boxShadow = '0 0 15px var(--accent-primary-dim)';
  } else {
    exp.style.display = 'none';
    icon.textContent = '+';
    icon.style.transform = 'rotate(0deg)';
    card.style.borderColor = '';
    card.style.boxShadow = '';
  }
}

function toggleQualitativeReport() {
  const content = document.getElementById('qualitative-content');
  const icon = document.getElementById('qualitative-icon');
  const card = document.getElementById('qualitative-card');
  
  if (!content || !icon) return;

  if (content.style.display === 'none') {
    content.style.display = 'block';
    icon.textContent = '✕';
    icon.style.transform = 'rotate(90deg)';
    if (card) {
      card.style.borderColor = 'var(--gold)';
      card.style.boxShadow = '0 0 15px rgba(251, 191, 36, 0.15)';
    }
  } else {
    content.style.display = 'none';
    icon.textContent = '+';
    icon.style.transform = 'rotate(0deg)';
    if (card) {
      card.style.borderColor = '';
      card.style.boxShadow = '';
    }
  }
}

function filterWiki() {
  const query = document.getElementById('input-wiki-search').value.toLowerCase().trim();
  
  let filtered = wikiData;
  
  // 1. Filter by category
  if (activeWikiCategory !== 'all') {
    filtered = filtered.filter(item => item.category === activeWikiCategory);
  }
  
  // 2. Filter by search query
  if (query) {
    filtered = filtered.filter(item => 
      item.title.toLowerCase().includes(query) ||
      item.short.toLowerCase().includes(query) ||
      item.concept.toLowerCase().includes(query) ||
      item.utility.toLowerCase().includes(query)
    );
  }
  
  renderWiki(filtered);
}

// ─── Render Helpers ─────────────────────────────────────────────

function renderLoadingCards(count) {
  let html = '';
  for (let i = 0; i < count; i++) {
    html += `
      <div class="card loading-card">
        <div class="loading-skeleton"></div>
        <div class="loading-skeleton"></div>
        <div class="loading-skeleton"></div>
      </div>
    `;
  }
  return html;
}

function renderEmptyState(icon, title, text) {
  return `
    <div class="empty-state">
      <div class="empty-state__icon">${icon}</div>
      <div class="empty-state__title">${title}</div>
      <div class="empty-state__text">${text}</div>
    </div>
  `;
}

// ─── Event Listeners ────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  // Bottom nav
  document.querySelectorAll('.bottom-nav__item').forEach(btn => {
    btn.addEventListener('click', () => navigate(btn.dataset.page));
  });

  // Add ticker modal - enter key
  const tickerInput = document.getElementById('input-ticker');
  if (tickerInput) {
    tickerInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') addTicker();
      if (e.key === 'Escape') closeAddModal();
    });
  }

  // Close modal on overlay click
  document.getElementById('modal-add').addEventListener('click', (e) => {
    if (e.target.id === 'modal-add') closeAddModal();
  });

  // Wiki search input
  const wikiSearchInput = document.getElementById('input-wiki-search');
  if (wikiSearchInput) {
    wikiSearchInput.addEventListener('input', filterWiki);
  }

  // Hash routing
  window.addEventListener('hashchange', handleHashChange);
  
  // Initial load
  handleHashChange();
});

// ─── Compare Page Logic ─────────────────────────────────────────

function loadComparePage() {
  const select = document.getElementById('compare-select');
  if (!select) return;

  // Populate select with portfolio tickers
  let options = '<option value="" disabled selected>Selecciona un ticker...</option>';
  state.portfolio.forEach(p => {
    options += `<option value="${p.ticker}">${p.ticker} - ${p.empresa}</option>`;
  });
  select.innerHTML = options;

  renderCompareTable();
}

async function addCompareTicker() {
  const select = document.getElementById('compare-select');
  const ticker = select.value;
  if (!ticker) return;

  if (state.compareTickers.length >= 3) {
    showToast('Máximo 3 empresas para comparar.', 'warning');
    return;
  }

  if (state.compareTickers.some(t => t.ticker === ticker)) {
    showToast('La empresa ya está en el comparador.', 'warning');
    return;
  }

  try {
    const data = await apiGet(`/company/${ticker}`);
    state.compareTickers.push(data);
    renderCompareTable();
  } catch (err) {
    showToast('Error al cargar datos del ticker.', 'error');
  }
}

function clearCompare() {
  state.compareTickers = [];
  renderCompareTable();
}

function renderCompareTable() {
  const container = document.getElementById('compare-table-container');
  if (!container) return;

  if (state.compareTickers.length === 0) {
    container.innerHTML = renderEmptyState('⚖️', 'Ninguna empresa seleccionada', 'Añade empresas usando el selector de arriba.');
    return;
  }

  const t = state.compareTickers;
  let html = `<table class="wiki-table" style="width: 100%; text-align: left;">
    <thead>
      <tr>
        <th>Métrica</th>`;
  
  t.forEach(comp => {
    html += `<th>${comp.ticker}</th>`;
  });
  html += `</tr></thead><tbody>`;

  // Helper function to render a row with highlights
  const renderRow = (label, key, formatter = null, bestCondition = 'highest') => {
    let rowHtml = `<tr><td style="font-weight: 700;">${label}</td>`;
    
    // Find best value
    let bestVal = null;
    if (bestCondition === 'highest') {
      bestVal = Math.max(...t.map(x => Number(x[key]) || -Infinity));
    } else if (bestCondition === 'lowest') {
      bestVal = Math.min(...t.map(x => Number(x[key]) || Infinity));
    }

    t.forEach(comp => {
      const val = Number(comp[key]);
      const isBest = val === bestVal && !isNaN(val) && val !== Infinity && val !== -Infinity;
      let displayVal = formatter ? formatter(val) : val;
      if (isNaN(val) || comp[key] == null) displayVal = 'N/A';
      
      rowHtml += `<td style="${isBest ? 'color: var(--color-success); font-weight: 700;' : ''}">${displayVal}</td>`;
    });
    rowHtml += `</tr>`;
    return rowHtml;
  };

  html += renderRow('Margen Operativo', 'current_operating_margin', v => formatPercent(v * 100), 'highest');
  html += renderRow('M. Operativo (I+D Cap)', 'rd_adjusted_operating_margin', v => formatPercent(v * 100), 'highest');
  html += renderRow('Naranjos Score', 'naranjos_score', v => v + '/100', 'highest');
  html += renderRow('Piotroski F-Score', 'piotroski_score', v => v + '/9', 'highest');
  html += renderRow('Margen Seguridad', 'margen_seguridad', v => formatPercent(v), 'highest');
  html += renderRow('ROIC Medio', 'roic_hist_avg', v => formatPercent(v), 'highest');
  html += renderRow('PER Actual', 'per_actual', v => v.toFixed(1) + 'x', 'lowest');
  html += renderRow('Crecimiento (EPS)', 'growth_rate', v => formatPercent(v * 100), 'highest');
  html += renderRow('Deuda / EBITDA', 'debt_to_ebitda', v => v.toFixed(2) + 'x', 'lowest');

  // Semáforo
  html += `<tr><td style="font-weight: 700;">Semáforo</td>`;
  t.forEach(comp => {
    let sColor = comp.estado_semaforo === 'Verde' ? 'var(--color-success)' : comp.estado_semaforo === 'Naranja' ? '#fbbf24' : 'var(--color-danger)';
    html += `<td style="color: ${sColor}; font-weight: 700;">${comp.estado_semaforo || 'N/A'}</td>`;
  });
  html += `</tr>`;

  html += `</tbody></table>`;
  container.innerHTML = html;
}

