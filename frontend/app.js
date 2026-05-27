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
  portfolio: [],
  currentDetail: null,
  explorerResults: [],
  isLoading: false,
  isUpdating: false,
  isExploring: false,
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
  if (status.includes('STRONG BUY') || status.includes('CALIDAD')) return 'strong-buy';
  if (status.includes('SOBREVALORADA')) return 'overvalued';
  if (status.includes('NO ELEGIBLE')) return 'no-eligible';
  return 'neutral';
}

function getSemaforoEmoji(status) {
  if (!status) return '⚪';
  if (status.includes('STRONG BUY') || status.includes('CALIDAD')) return '🟢';
  if (status.includes('SOBREVALORADA')) return '🔴';
  if (status.includes('NO ELEGIBLE')) return '🚫';
  return '🟡';
}

function getSemaforoMeaning(status) {
  if (!status) return 'No hay datos de valoración.';
  if (status.includes('STRONG BUY')) return 'Convergencia total. Empresa barata por fundamentales (DCF/Graham) e históricamente.';
  if (status.includes('COMPRA DE CALIDAD')) return 'Caso Ferrari: Empresa de extraordinaria calidad (Wide Moat y excelente directiva) cotizando a un precio razonable.';
  if (status.includes('SOBREVALORADA')) return 'Precio excesivo, alto riesgo de corrección por fundamentales y valoración histórica.';
  if (status.includes('NO ELEGIBLE')) return 'No elegible. Reportes no transparentes o EBITDA Ajustado manipulado (>30% de divergencia).';
  return 'Señal mixta o intermedia. Requiere análisis cualitativo profundo (ej. caso Ferrari).';
}

// ─── API Calls ──────────────────────────────────────────────────

function getHeaders() {
  const headers = { 'Content-Type': 'application/json' };
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

function renderPortfolio() {
  const container = document.getElementById('portfolio-list');
  
  if (state.portfolio.length === 0) {
    container.innerHTML = renderEmptyState(
      '📈', 
      'Cartera vacía', 
      'Añade tickers para empezar a analizar empresas con criterios de inversión en valor.'
    );
    return;
  }

  let html = '';
  for (const item of state.portfolio) {
    const mosBadge = getMosBadgeClass(item.margen_seguridad);
    const mosText = item.margen_seguridad !== null ? formatPercent(item.margen_seguridad) : 'Sin datos';
    
    html += `
      <div class="card card--clickable" onclick="navigate('detail', {ticker: '${item.ticker}'})">
        <button class="portfolio-card__delete" onclick="event.stopPropagation(); removeTicker('${item.ticker}')" title="Eliminar">✕</button>
        <div class="portfolio-card">
          <div class="portfolio-card__info">
            <span class="portfolio-card__ticker">${getSemaforoEmoji(item.estado_semaforo)} ${item.ticker}</span>
            <span class="portfolio-card__name">${item.empresa || 'Cargando...'}</span>
            <span style="font-size: 0.7rem; color: var(--text-muted); margin-top: 2px;">${item.calidad || ''}</span>
          </div>
          <div class="portfolio-card__metrics">
            <span class="portfolio-card__price">${item.precio_mercado ? formatCurrency(item.precio_mercado) : '—'}</span>
            <span class="portfolio-card__mos ${mosBadge}">MoS: ${mosText}</span>
          </div>
        </div>
      </div>
    `;
  }
  container.innerHTML = html;
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

async function addTicker() {
  const input = document.getElementById('input-ticker');
  const ticker = input.value.trim().toUpperCase();
  if (!ticker) return;

  try {
    const data = await apiPost('/portfolio', { ticker });
    if (data.error) {
      showToast(`⚠️ ${data.error}`, 'error');
    } else {
      showToast(`✅ ${ticker} añadido a la cartera`, 'success');
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

    <!-- Archetype Badge -->
    ${d.archetype_label ? `
      <div style="display: flex; flex-wrap: wrap; gap: var(--space-xs); margin-bottom: var(--space-md); align-items: center;">
        <span class="badge--positive" style="font-size: 0.72rem; padding: 4px 10px; border-radius: 20px; font-weight: 700;">${d.archetype_label}</span>
        <span style="font-size: 0.68rem; color: var(--text-tertiary);">WACC: ${d.wacc_used ? formatPercent(d.wacc_used * 100) : '10%'} · ${cur}</span>
        ${d.valuation_models_used ? `<span style="font-size: 0.68rem; color: var(--text-tertiary);">· Modelos: ${d.valuation_models_used.join(', ')}</span>` : ''}
      </div>
    ` : ''}

    <!-- TradingView Chart -->
    <div class="card" style="padding: 0; overflow: hidden; height: 350px; margin-bottom: var(--space-md); border-radius: var(--radius-md);">
      <div id="tv_chart_container" style="height: 100%; width: 100%;"></div>
    </div>

    <!-- Non-GAAP Flag -->
    ${d.non_gaap_flag && d.non_gaap_flag !== '✅ OK' ? `
      <div class="non-gaap-badge ${d.non_gaap_flag.includes('🚫') ? 'badge--negative' : 'badge--neutral'}" 
           style="margin-bottom: var(--space-md); display: flex;">
        ${d.non_gaap_flag} — ${d.non_gaap_detail || ''}
      </div>
    ` : ''}

    <!-- Metrics Table -->
    <div class="card" style="overflow-x: auto; -webkit-overflow-scrolling: touch;">
      <table class="metrics-table">
        <thead>
          <tr>
            <th>Métrica</th>
            ${(d.fiscal_dates || []).map(dateStr => {
              try {
                return `<th>${dateStr.split('-')[0]}</th>`;
              } catch(e) {
                return `<th>${dateStr}</th>`;
              }
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
        </tbody>
      </table>
    </div>

    <!-- Semáforo Card -->
    <div class="card semaforo-card semaforo-card--${getSemaforoClass(d.estado_semaforo)}">
      <div class="semaforo-card__icon">${getSemaforoEmoji(d.estado_semaforo)}</div>
      <div class="semaforo-card__content">
        <div class="semaforo-card__status">${d.estado_semaforo || 'SIN CLASIFICAR'}</div>
        <div class="responsive-metrics-grid">
          <div style="background: rgba(0,0,0,0.2); padding: var(--space-sm) var(--space-md); border-radius: var(--radius-sm); border: 1px solid var(--border-subtle);">
            <div style="font-size: 0.68rem; color: var(--text-tertiary); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">Fundamentales (DCF)</div>
            <div style="font-size: 1.05rem; font-weight: 700; font-family: var(--font-mono); color: ${d.ms_absoluto >= 0 ? 'var(--color-success)' : 'var(--color-danger)'};">
              ${d.ms_absoluto >= 0 ? 'Descuento: ' + formatPercent(d.ms_absoluto) : 'Sobreprecio: ' + formatPercent(Math.abs(d.ms_absoluto))}
            </div>
          </div>
          <div style="background: rgba(0,0,0,0.2); padding: var(--space-sm) var(--space-md); border-radius: var(--radius-sm); border: 1px solid var(--border-subtle);">
            <div style="font-size: 0.68rem; color: var(--text-tertiary); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">Histórico (${d.multiple_type || 'N/A'})</div>
            <div style="font-size: 1.05rem; font-weight: 700; font-family: var(--font-mono); color: ${d.ms_relativo >= 0 ? 'var(--color-success)' : 'var(--color-warning)'};">
              ${d.ms_relativo >= 0 ? 'Descuento: ' + formatPercent(d.ms_relativo) : 'Sobreprecio: ' + formatPercent(Math.abs(d.ms_relativo))}
            </div>
          </div>
        </div>
        <div class="semaforo-card__meaning">
          ${getSemaforoMeaning(d.estado_semaforo)}
        </div>
      </div>
    </div>

    <!-- Phase 3: Margins and Debt Ratios -->
    <div class="responsive-metrics-grid">
      <div class="card">
        <div style="font-size: 0.72rem; font-weight: 700; color: var(--text-tertiary); margin-bottom: var(--space-xs);">📊 RENTABILIDAD Y MÁRGENES</div>
        <div class="info-row">
          <span class="info-row__label">Margen Bruto</span>
          <span class="info-row__value">${d.current_gross_margin != null ? formatPercent(d.current_gross_margin * 100) : '—'}</span>
        </div>
        <div class="info-row">
          <span class="info-row__label">Margen Operativo</span>
          <span class="info-row__value">${d.current_operating_margin != null ? formatPercent(d.current_operating_margin * 100) : '—'}</span>
        </div>
        <div class="info-row">
          <span class="info-row__label">Margen Neto</span>
          <span class="info-row__value">${d.current_net_margin != null ? formatPercent(d.current_net_margin * 100) : '—'}</span>
        </div>
      </div>
      <div class="card">
        <div style="font-size: 0.72rem; font-weight: 700; color: var(--text-tertiary); margin-bottom: var(--space-xs);">🏦 SALUD FINANCIERA (DEUDA)</div>
        <div class="info-row">
          <span class="info-row__label" title="Cobertura de intereses (EBIT / Gastos Financieros). >3x es seguro.">Interest Coverage</span>
          <span class="info-row__value" style="color: ${d.interest_coverage != null && d.interest_coverage < 3 ? 'var(--color-danger)' : 'var(--text-primary)'}">${d.interest_coverage != null ? (d.interest_coverage > 900 ? 'Sin Deuda' : formatNumber(d.interest_coverage, 1) + 'x') : '—'}</span>
        </div>
        <div class="info-row">
          <span class="info-row__label" title="Net Debt / EBITDA. <3x es seguro.">Net Debt / EBITDA</span>
          <span class="info-row__value" style="color: ${d.net_debt_ebitda != null && d.net_debt_ebitda > 3 ? 'var(--color-danger)' : 'var(--text-primary)'}">${d.net_debt_ebitda != null ? formatNumber(d.net_debt_ebitda, 1) + 'x' : '—'}</span>
        </div>
      </div>
    </div>

    <!-- Qualitative Audit Accordion -->
    ${d.qualitative_audit ? `
      <div class="card qualitative-accordion" id="qualitative-card" onclick="toggleQualitativeReport()" style="cursor: pointer; border: 1px solid var(--border-subtle); transition: all var(--transition-base); margin-bottom: var(--space-md);">
        <div class="qualitative-accordion__header" style="display: flex; justify-content: space-between; align-items: center;">
          <span style="font-weight: 700; font-size: 0.9rem; color: var(--gold);">🔍 Informe Cualitativo de Auditoría</span>
          <span id="qualitative-icon" style="font-size: 1.1rem; color: var(--text-tertiary); transition: transform 0.2s;">+</span>
        </div>
        
        <div id="qualitative-content" style="display: none; margin-top: var(--space-md);">
          <div style="height: 1px; background: var(--border-subtle); margin-bottom: var(--space-sm);"></div>
          
          <div class="qualitative-point" style="margin-bottom: var(--space-sm);">
            <div style="font-size: 0.72rem; font-weight: 700; color: var(--accent-primary); text-transform: uppercase; margin-bottom: 2px;">🛡️ Análisis de Foso (Moat)</div>
            <div style="font-size: 0.8rem; color: var(--text-secondary); line-height: 1.5; padding-left: var(--space-sm); border-left: 2px solid var(--accent-primary);">
              <strong>${d.qualitative_audit.moat_strength}</strong>: ${d.qualitative_audit.moat_details}
            </div>
          </div>
          
          <div class="qualitative-point" style="margin-bottom: var(--space-sm);">
            <div style="font-size: 0.72rem; font-weight: 700; color: var(--accent-primary); text-transform: uppercase; margin-bottom: 2px;">💼 Directiva y Asignación de Capital</div>
            <div style="font-size: 0.8rem; color: var(--text-secondary); line-height: 1.5; padding-left: var(--space-sm); border-left: 2px solid var(--accent-primary);">
              ${d.qualitative_audit.management_details}
            </div>
          </div>

          <div class="qualitative-point" style="margin-bottom: var(--space-sm);">
            <div style="font-size: 0.72rem; font-weight: 700; color: var(--accent-primary); text-transform: uppercase; margin-bottom: 2px;">🌐 Tamaño de Mercado y Crecimiento (TAM/SAM/SOM)</div>
            <div style="font-size: 0.8rem; color: var(--text-secondary); line-height: 1.5; padding-left: var(--space-sm); border-left: 2px solid var(--accent-primary);">
              <strong>${d.qualitative_audit.growth_strength || 'Análisis de Crecimiento'}</strong>: ${d.qualitative_audit.growth_details || 'Estimando pista de crecimiento...'}
            </div>
          </div>
          
          <div class="qualitative-point">
            <div style="font-size: 0.72rem; font-weight: 700; color: var(--color-danger); text-transform: uppercase; margin-bottom: 2px;">⚠️ Análisis de Riesgos y Gobernanza</div>
            <div style="font-size: 0.8rem; color: var(--text-secondary); line-height: 1.5; padding-left: var(--space-sm); border-left: 2px solid var(--color-danger);">
              ${d.qualitative_audit.risk_details}
            </div>
          </div>
        </div>
      </div>
    ` : ''}

    <!-- Additional Info -->
    <div class="card">
      <div class="info-row">
        <span class="info-row__label">Market Cap</span>
        <span class="info-row__value">${formatLargeNumber(d.market_cap)}</span>
      </div>
      <div class="info-row">
        <span class="info-row__label">Industria</span>
        <span class="info-row__value" style="font-family: var(--font-main); font-size: 0.8rem;">${d.industry || '—'}</span>
      </div>
      <div class="info-row">
        <span class="info-row__label">Div. Yield</span>
        <span class="info-row__value">${divYieldDisplay}</span>
      </div>
      <div class="info-row">
        <span class="info-row__label">Crecimiento Est.</span>
        <span class="info-row__value">${d.growth_rate ? formatPercent(d.growth_rate * 100) : '—'}</span>
      </div>
      <div class="info-row">
        <span class="info-row__label">Precio Objetivo Analistas</span>
        <span class="info-row__value">${d.analyst_target ? formatCurrency(d.analyst_target, cur) : '—'}</span>
      </div>
      <div class="info-row">
        <span class="info-row__label">Moneda</span>
        <span class="info-row__value">${cur}${d.financial_currency && d.financial_currency !== cur ? ' (Reporta en ' + d.financial_currency + ')' : ''}</span>
      </div>
    </div>

    <!-- Valuation Box -->
    <div class="valuation-box">
      <div class="valuation-box__title">💎 VALORACIÓN INTRÍNSECA</div>
      
      ${d.graham_value && d.graham_value > 0 ? `
      <div class="valuation-box__row">
        <span class="valuation-box__label">Graham</span>
        <span class="valuation-box__value">${formatCurrency(d.graham_value, cur)}</span>
      </div>
      ` : ''}
      ${d.dcf_value && d.dcf_value > 0 ? `
      <div class="valuation-box__row">
        <span class="valuation-box__label">${
          d.archetype_id === 'hypergrowth' ? 'DCF Revenue' :
          d.archetype_id === 'compounder' ? 'DCF (Multi-Fase)' :
          d.archetype_id === 'speculative' ? 'DCF (Tentativo)' :
          'DCF (10a)'
        }</span>
        <span class="valuation-box__value">${formatCurrency(d.dcf_value, cur)}</span>
      </div>
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
    </div>

    <!-- Investment Thesis -->
    ${d.thesis ? `
      <div class="thesis-box">
        <div class="thesis-box__title">📝 TESIS DE INVERSIÓN</div>
        <div class="thesis-box__text">${d.thesis}</div>
      </div>
      </div>
    ` : ''}
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

// ─── Explorer Profiles ───────────────────────────────────────────
const exploreProfiles = {
  conservative: { max_per: 15, min_roic: 15, min_fcf_yield: 7, min_mos: 30 },
  moderate: { max_per: 20, min_roic: 12, min_fcf_yield: 5, min_mos: 20 },
  aggressive: { max_per: 25, min_roic: 8, min_fcf_yield: 3, min_mos: 10 }
};

window.updateExploreChips = function() {
  const select = document.getElementById('explore-profile');
  if (!select) return;
  const profileKey = select.value;
  const p = exploreProfiles[profileKey];
  const container = document.getElementById('explorer-filters-container');
  if (container) {
    container.innerHTML = `
      <span class="filter-chip">PER &lt; ${p.max_per}</span>
      <span class="filter-chip">ROIC &gt; ${p.min_roic}%</span>
      <span class="filter-chip">FCF Yield &gt; ${p.min_fcf_yield}%</span>
      <span class="filter-chip">MoS &gt; ${p.min_mos}%</span>
    `;
  }
};

// ─── Explorer / NOVEDAD ─────────────────────────────────────────

async function exploreOpportunities() {
  if (state.isExploring) return;
  
  const selectProfile = document.getElementById('explore-profile');
  const profileKey = selectProfile ? selectProfile.value : 'moderate';
  const p = exploreProfiles[profileKey];
  
  const selectMarket = document.getElementById('explore-market');
  const market = selectMarket ? selectMarket.value : 'sp500';
  const marketName = selectMarket ? selectMarket.options[selectMarket.selectedIndex].text : 'del mercado seleccionado';
  
  const btn = document.getElementById('btn-explore');
  const resultsContainer = document.getElementById('explorer-results');
  
  state.isExploring = true;
  btn.classList.add('btn-explore--loading');
  btn.innerHTML = '<span class="spinner"></span> Escaneando mercado...';
  
  resultsContainer.innerHTML = `
    <div class="progress-bar"><div class="progress-bar__fill" style="width: 60%"></div></div>
    <p style="text-align: center; color: var(--text-tertiary); font-size: 0.85rem;">
      Analizando ~50 empresas de <strong>${marketName}</strong>...<br>
      <span style="font-size: 0.75rem;">Esto puede tardar 1-2 minutos</span>
    </p>
  `;

  try {
    const queryStr = `?market=${market}&max_per=${p.max_per}&min_roic=${p.min_roic}&min_fcf_yield=${p.min_fcf_yield}&min_mos=${p.min_mos}`;
    const data = await apiGet('/explore' + queryStr);
    state.explorerResults = data.opportunities || [];
    renderExplorerResults();
  } catch (err) {
    resultsContainer.innerHTML = renderEmptyState('❌', 'Error', 'No se pudo completar el escaneo. Inténtalo de nuevo.');
  } finally {
    state.isExploring = false;
    btn.classList.remove('btn-explore--loading');
    btn.innerHTML = '🔎 Buscar Oportunidades';
  }
}

function renderExplorerResults() {
  const container = document.getElementById('explorer-results');
  
  if (state.explorerResults.length === 0) {
    container.innerHTML = renderEmptyState(
      '🔍',
      'Sin resultados',
      'No se encontraron empresas que cumplan todos los criterios de valor. Intenta ajustar los filtros.'
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
    html += `
      <div class="card opportunity-card">
        <div class="opportunity-card__header">
          <div>
            <div class="opportunity-card__ticker">🏆 ${opp.ticker}</div>
            <div class="opportunity-card__name">${opp.empresa}</div>
          </div>
          <div class="opportunity-card__price">${formatCurrency(opp.current_price)}</div>
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
      headers: { 'Content-Type': 'application/json' },
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
