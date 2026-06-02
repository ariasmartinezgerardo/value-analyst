"""
engine.py — Financial Analysis Engine for Value Investing.
Implements FCF Real, ROIC, Graham & DCF valuations, Margin of Safety,
Non-GAAP detection, and an Archetype-Based Multi-Model Valuation System.
"""

import numpy as np
import logging

logger = logging.getLogger(__name__)

# ─── Configuration ────────────────────────────────────────────────
TERMINAL_GROWTH = 0.025        # 2.5% perpetual growth
GRAHAM_BASE_PE = 8.5           # Graham zero-growth P/E
GRAHAM_GROWTH_MULT = 2.0       # Graham growth multiplier
GRAHAM_BOND_YIELD_1962 = 4.4   # AAA bond yield in 1962
CURRENT_AAA_BOND_YIELD = 4.5   # Current AAA bond yield (approximate)
MIN_MARGIN_OF_SAFETY = 0.20    # 20% minimum for recommendation
NON_GAAP_WARN_THRESHOLD = 0.15  # 15% divergence warns
NON_GAAP_REJECT_THRESHOLD = 0.30  # 30% divergence rejects

# ─── WACC by Sector ──────────────────────────────────────────────
WACC_BY_SECTOR = {
    'utilities': 0.07,
    'real estate': 0.07,
    'consumer defensive': 0.08,
    'healthcare': 0.09,
    'financial services': 0.09,
    'financial': 0.09,
    'industrials': 0.09,
    'industrial': 0.09,
    'basic materials': 0.09,
    'consumer cyclical': 0.10,
    'communication services': 0.10,
    'communication': 0.10,
    'technology': 0.10,
    'energy': 0.10,
}

# ─── Sector Benchmarks (Medians for PER, ROIC) ───────────────────
SECTOR_BENCHMARKS = {
    'technology': {'pe': 25, 'roic': 15, 'gross_margin': 0.50},
    'healthcare': {'pe': 20, 'roic': 12, 'gross_margin': 0.55},
    'consumer defensive': {'pe': 18, 'roic': 10, 'gross_margin': 0.40},
    'consumer cyclical': {'pe': 15, 'roic': 10, 'gross_margin': 0.35},
    'financial services': {'pe': 12, 'roic': 8, 'gross_margin': 0.0},
    'utilities': {'pe': 16, 'roic': 6, 'gross_margin': 0.35},
    'real estate': {'pe': 20, 'roic': 6, 'gross_margin': 0.60},
    'industrials': {'pe': 18, 'roic': 12, 'gross_margin': 0.30},
    'energy': {'pe': 10, 'roic': 8, 'gross_margin': 0.35},
    'basic materials': {'pe': 12, 'roic': 8, 'gross_margin': 0.25},
    'communication services': {'pe': 18, 'roic': 10, 'gross_margin': 0.45},
}

# ─── Industry-Level TAM (USD) ────────────────────────────────────
INDUSTRY_TAM_USD = {
    # Technology
    'semiconductor': 600e9, 'semiconductors': 600e9,
    'software': 700e9, 'software—infrastructure': 400e9,
    'software—application': 350e9, 'information technology services': 800e9,
    'internet content & information': 800e9, 'internet retail': 5.0e12,
    'electronic gaming & multimedia': 200e9, 'consumer electronics': 800e9,
    'scientific & technical instruments': 100e9, 'computer hardware': 400e9,
    'cloud': 500e9, 'cybersecurity': 200e9,
    # Healthcare
    'drug manufacturers—general': 1.5e12, 'drug manufacturers—specialty & generic': 600e9,
    'pharmaceuticals': 1.5e12, 'biotechnology': 600e9,
    'medical devices': 500e9, 'medical instruments & supplies': 200e9,
    'diagnostics & research': 100e9, 'health information services': 200e9,
    'healthcare plans': 1.2e12, 'medical care facilities': 800e9,
    # Financial
    'banks—diversified': 7.0e12, 'banks—regional': 3.0e12,
    'insurance—diversified': 6.0e12, 'insurance—life': 3.0e12,
    'insurance—property & casualty': 2.0e12,
    'asset management': 400e9, 'capital markets': 200e9,
    'financial data & stock exchanges': 60e9,
    'credit services': 3.0e12, 'financial conglomerates': 5.0e12,
    # Consumer
    'auto manufacturers': 3.0e12, 'auto parts': 500e9,
    'restaurants': 900e9, 'beverages—non-alcoholic': 800e9,
    'beverages—brewers': 600e9, 'beverages—wineries & distilleries': 400e9,
    'packaged foods': 3.0e12, 'household & personal products': 500e9,
    'apparel manufacturing': 1.8e12, 'luxury goods': 350e9,
    'specialty retail': 1.5e12, 'discount stores': 2.0e12,
    'home improvement retail': 800e9, 'grocery stores': 8.0e12,
    # Industrial
    'aerospace & defense': 800e9, 'farm & heavy construction machinery': 600e9,
    'railroads': 200e9, 'integrated freight & logistics': 4.0e12,
    'marine shipping': 500e9, 'building products & equipment': 600e9,
    'electrical equipment & parts': 400e9, 'industrial distribution': 300e9,
    # Energy
    'oil & gas integrated': 4.0e12, 'oil & gas e&p': 2.0e12,
    'oil & gas midstream': 500e9, 'oil & gas refining & marketing': 1.0e12,
    'solar': 300e9, 'renewable': 1.5e12, 'uranium': 30e9,
    'utilities—regulated electric': 2.5e12,
    'utilities—renewable': 500e9, 'utilities—diversified': 3.5e12,
    # Communication & Media
    'telecom services': 1.7e12, 'entertainment': 600e9,
    'advertising agencies': 700e9, 'broadcasting': 200e9,
    'electronic gaming': 200e9, 'publishing': 120e9,
    # Real Estate
    'reit—retail': 500e9, 'reit—residential': 400e9,
    'reit—industrial': 400e9, 'reit—office': 300e9,
    'reit—diversified': 600e9, 'reit—healthcare facilities': 200e9,
    'real estate—development': 1.5e12, 'real estate—diversified': 2.0e12,
    'real estate services': 500e9,
}

# Sector-level fallback (used when industry doesn't match)
SECTOR_TAM_USD = {
    'technology': 5.5e12,
    'healthcare': 12.0e12,
    'financial services': 22.0e12,
    'financial': 22.0e12,
    'consumer cyclical': 15.0e12,
    'consumer defensive': 9.0e12,
    'industrials': 8.0e12,
    'industrial': 8.0e12,
    'communication services': 2.5e12,
    'communication': 2.5e12,
    'energy': 6.0e12,
    'basic materials': 7.0e12,
    'utilities': 3.5e12,
    'real estate': 4.0e12,
}

# Target FCF Margins by industry (for Hypergrowth revenue-based DCF)
TARGET_FCF_MARGINS = {
    'software': 0.25, 'internet': 0.20, 'cloud': 0.25,
    'semiconductor': 0.22, 'technology': 0.18,
    'healthcare': 0.15, 'biotechnology': 0.12,
    'consumer': 0.10, 'industrial': 0.10,
    'energy': 0.10, 'financial': 0.15,
}


def _avg(values, exclude_none=True):
    """Calculate average of a list, ignoring None values. Zeros ARE included."""
    if exclude_none:
        values = [v for v in values if v is not None]
    if not values:
        return None
    return sum(values) / len(values)


def _trend(values):
    """
    Determine trend from a list of values (most recent first).
    Returns: '↑' (improving), '↓' (declining), '→' (stable), '?' (insufficient data)
    """
    clean = [v for v in values if v is not None and v != 0]
    if len(clean) < 2:
        return '?'

    # Compare most recent to average of older values
    recent = clean[0]
    older_avg = _avg(clean[1:])
    if older_avg is None or older_avg == 0:
        return '?'

    pct_change = (recent - older_avg) / abs(older_avg)
    if pct_change > 0.05:
        return '↑'
    elif pct_change < -0.05:
        return '↓'
    return '→'


# Growth rate caps by archetype (applied after detection in run_full_analysis)
GROWTH_CAPS = {
    'classic_value': 0.15,
    'compounder': 0.20,
    'hypergrowth': 0.30,
    'financial': 0.10,
    'reit_utility': 0.08,
    'speculative': 0.15,
}


def _growth_rate(values):
    """
    Estimate compound annual growth rate from values (most recent first).
    Returns RAW CAGR (uncapped), or None if insufficient data.
    The cap is applied per-archetype in run_full_analysis.
    """
    clean = [v for v in values if v is not None and v > 0]
    if len(clean) < 2:
        return None  # insufficient data — caller decides default
    n = len(clean) - 1
    if clean[-1] <= 0 or clean[0] <= 0:
        return None
    cagr = (clean[0] / clean[-1]) ** (1 / n) - 1
    return max(min(cagr, 1.0), -0.10)  # floor at -10%, raw cap at 100%


# ─── FCF REAL ─────────────────────────────────────────────────────

def calculate_fcf_real(data: dict) -> dict:
    """
    Calculate Real Free Cash Flow (GAAP-only), adjusted for SBC:
    FCF = FCF_Yahoo (Operating Cash Flow - Capex) - SBC

    SBC (Stock Based Compensation) is deducted because it dilutes shareholders
    even though it's a non-cash expense. This is critical for tech companies.

    If SBC data is not available (common for European companies), FCF Real = FCF Yahoo.

    Returns dict with historical FCF values (adjusted) and pre-SBC values.
    """
    fcf_yahoo = data.get('fcf_yahoo_values', [])
    sbc = data.get('sbc_values', [])
    
    fcf_real_values = []
    fcf_pre_sbc_values = []
    sbc_annual = []
    
    # FIX: Process all available FCF years. If SBC is missing/short, treat as 0.
    # Previously: min(len(fcf), len(sbc)) — which returned 0 when sbc was empty,
    # causing companies like RACE, LVMH, Hermès to have NO FCF data at all.
    for i in range(len(fcf_yahoo)):
        f = fcf_yahoo[i] or 0
        s = abs(sbc[i] or 0) if i < len(sbc) else 0
        fcf_pre_sbc_values.append(f)
        sbc_annual.append(s)
        fcf_real_values.append(f - s)
        
    fcf_ttm_pre_sbc = None
    fcf_ttm = None
    
    if fcf_yahoo and fcf_yahoo[0] is not None:
        fcf_ttm_pre_sbc = fcf_yahoo[0]
        sbc_latest = abs(sbc[0] or 0) if sbc and sbc[0] is not None else 0
        fcf_ttm = fcf_ttm_pre_sbc - sbc_latest
            
    hist_avg = _avg(fcf_real_values[1:]) if len(fcf_real_values) > 1 else _avg(fcf_real_values)
    
    return {
        'fcf_real_values': fcf_real_values,
        'fcf_pre_sbc_values': fcf_pre_sbc_values,
        'sbc_values': sbc_annual,
        'fcf_real_ttm': fcf_ttm,
        'fcf_ttm_pre_sbc': fcf_ttm_pre_sbc,
        'fcf_real_hist_avg': hist_avg,
        'fcf_trend': _trend(fcf_real_values)
    }


# ─── ROIC ─────────────────────────────────────────────────────────

def calculate_roic(data: dict) -> dict:
    """
    Calculate Return on Invested Capital:
    ROIC = NOPAT / Invested Capital
    NOPAT = EBIT × (1 - Tax Rate)
    Invested Capital = Total Equity + Total Debt - Cash
    """
    ebit = data.get('ebit_values', [])
    tax_vals = data.get('tax_values', [])
    pretax = data.get('pretax_values', [])
    equity = data.get('equity_values', [])
    debt = data.get('total_debt_values', [])
    cash = data.get('cash_values', [])

    roic_values = []
    min_len = min(len(ebit), len(equity)) if ebit and equity else 0

    for i in range(min_len):
        e = ebit[i]
        if e is None or e == 0:
            roic_values.append(None)
            continue

        # Tax rate
        tax_rate = 0.21  # Default US corporate tax
        if i < len(tax_vals) and i < len(pretax) and pretax[i] and pretax[i] != 0:
            tax_rate = abs(tax_vals[i] or 0) / abs(pretax[i])
            tax_rate = min(max(tax_rate, 0), 0.50)  # clamp

        nopat = e * (1 - tax_rate)

        # Invested capital
        eq = equity[i] if i < len(equity) else None
        if eq is None:
            roic_values.append(None)
            continue

        d = debt[i] if i < len(debt) else 0
        c = cash[i] if i < len(cash) else 0
        invested_capital = eq + (d or 0) - (c or 0)

        if invested_capital > 0:
            roic_values.append((nopat / invested_capital) * 100)
        else:
            roic_values.append(None)

    hist_avg = _avg(roic_values[1:]) if len(roic_values) > 1 else _avg(roic_values)

    return {
        'roic_values': roic_values,
        'roic_current': roic_values[0] if roic_values else None,
        'roic_hist_avg': hist_avg,
        'roic_trend': _trend(roic_values),
    }


# ─── GROWTH INVESTING METRICS ────────────────────────────────────

def calculate_growth_metrics(data: dict, growth_rate: float,
                             rev_growth: float,
                             fcf_margin: float,
                             per_actual: float,
                             per_forward: float,
                             ev: float,
                             revenue_current: float) -> dict:
    """
    Calculate Growth Investing metrics:
    - PEG Ratio (Peter Lynch GARP): PER / EPS Growth %
    - Rule of 40 (SaaS standard): Revenue Growth % + FCF Margin %
    - EV/Revenue Forward: Enterprise Value / Projected Revenue (3y)
    """
    result = {
        'peg_trailing': None,
        'peg_forward': None,
        'peg_signal': None,         # 'undervalued', 'fair', 'overvalued'
        'rule_of_40': None,
        'rule_of_40_signal': None,  # 'premium', 'acceptable', 'weak'
        'ev_revenue_current': None,
        'ev_revenue_forward_3y': None,
        'has_growth_metrics': False,
    }

    # ─── PEG Ratio (Trailing) ────────────────────────────────
    # PEG = PE / EPS Growth Rate (as %)
    growth_pct = (growth_rate or 0) * 100  # Convert 0.18 → 18
    if per_actual and per_actual > 0 and growth_pct > 0:
        result['peg_trailing'] = round(per_actual / growth_pct, 2)
        result['has_growth_metrics'] = True

    # ─── PEG Ratio (Forward) ─────────────────────────────────
    if per_forward and per_forward > 0 and growth_pct > 0:
        result['peg_forward'] = round(per_forward / growth_pct, 2)
        result['has_growth_metrics'] = True

    # ─── PEG Signal (use the best available) ─────────────────
    peg = result['peg_forward'] or result['peg_trailing']
    if peg is not None:
        if peg < 1.0:
            result['peg_signal'] = 'undervalued'
        elif peg <= 2.0:
            result['peg_signal'] = 'fair'
        else:
            result['peg_signal'] = 'overvalued'

    # ─── Rule of 40 ──────────────────────────────────────────
    rev_growth_pct = (rev_growth or 0) * 100  # 0.25 → 25
    fcf_margin_pct = (fcf_margin or 0) * 100  # 0.15 → 15
    if rev_growth_pct != 0 or fcf_margin_pct != 0:
        rule40 = round(rev_growth_pct + fcf_margin_pct, 1)
        result['rule_of_40'] = rule40
        result['has_growth_metrics'] = True

        if rule40 >= 40:
            result['rule_of_40_signal'] = 'premium'
        elif rule40 >= 20:
            result['rule_of_40_signal'] = 'acceptable'
        else:
            result['rule_of_40_signal'] = 'weak'

    # ─── EV/Revenue ──────────────────────────────────────────
    if ev and ev > 0 and revenue_current and revenue_current > 0:
        result['ev_revenue_current'] = round(ev / revenue_current, 2)
        result['has_growth_metrics'] = True

        # Forward 3-year projection
        if rev_growth and rev_growth > 0:
            projected_rev_3y = revenue_current * ((1 + rev_growth) ** 3)
            result['ev_revenue_forward_3y'] = round(ev / projected_rev_3y, 2)

    return result


# ─── NON-GAAP DETECTION ──────────────────────────────────────────

def check_non_gaap(data: dict) -> dict:
    """
    Detect potential Non-GAAP manipulation by comparing
    reported EBITDA vs calculated EBITDA (Operating Income + D&A).
    """
    ebitda_reported = data.get('ebitda_values', [])
    ebit = data.get('ebit_values', [])
    da = data.get('da_values', [])

    if not ebitda_reported or not ebit or not da:
        return {'non_gaap_flag': '✅ OK', 'non_gaap_detail': 'Insufficient data for comparison'}

    # Calculate EBITDA from components
    min_len = min(len(ebit), len(da), len(ebitda_reported))
    max_divergence = 0

    for i in range(min_len):
        calculated = (ebit[i] or 0) + abs(da[i] or 0)
        reported = ebitda_reported[i] or 0
        if calculated != 0:
            divergence = abs(reported - calculated) / abs(calculated)
            max_divergence = max(max_divergence, divergence)

    if max_divergence > NON_GAAP_REJECT_THRESHOLD:
        return {
            'non_gaap_flag': '🚫 No Elegible',
            'non_gaap_detail': f'EBITDA divergence {max_divergence:.0%} — Likely Non-GAAP adjustments'
        }
    elif max_divergence > NON_GAAP_WARN_THRESHOLD:
        return {
            'non_gaap_flag': '⚠️ Precaución',
            'non_gaap_detail': f'EBITDA divergence {max_divergence:.0%} — Possible adjustments'
        }
    return {
        'non_gaap_flag': '✅ OK',
        'non_gaap_detail': f'EBITDA divergence {max_divergence:.0%} — Within acceptable range'
    }


# ─── ARCHETYPE DETECTION ─────────────────────────────────────────

def detect_archetype(data: dict, roic_avg, growth_rate, eps_ttm, fcf_ttm) -> tuple:
    """
    Classify a company into a valuation archetype based on its financial profile.
    Returns (archetype_id, archetype_label).

    REVISED Classification priority (rentabilidad primero, crecimiento después):
    1. Financial Services → 'financial'
    2. REITs / Utilities → 'reit_utility'
    3. EPS ≤ 0 + Revenue Growth > 15% → 'hypergrowth'
    4. EPS ≤ 0 + Low Revenue Growth → 'speculative'
    5. EPS > 0 + ROIC > 20% → 'compounder' (ALWAYS, regardless of growth)
    6. EPS > 0 + ROIC > 15% + growth > 10% → 'compounder'
    7. EPS > 0 + growth > 25% + rev_growth > 20% + ROIC ≤ 20% → 'hypergrowth'
    8. Everything else with EPS > 0 → 'classic_value'
    """
    sector = (data.get('sector') or '').lower()
    industry = (data.get('industry') or '').lower()
    revenue_values = data.get('revenue_values', [])

    # Revenue growth (CAGR)
    rev_growth = None
    clean_rev = [v for v in revenue_values if v is not None and v > 0]
    if len(clean_rev) >= 2:
        n = len(clean_rev) - 1
        rev_growth = (clean_rev[0] / clean_rev[-1]) ** (1 / n) - 1

    # 1. Financial Services (banks, insurance, asset management)
    #    EXCEPTION: Payment networks (Visa, Mastercard, PayPal) have sector=Financial Services
    #    but are technology platforms with asset-light models and no credit risk.
    #    They should be valued as compounders, not by book value.
    PAYMENT_NETWORK_INDUSTRIES = ('credit services', 'payment processing', 'transaction processing')
    is_payment_network = any(p in industry for p in PAYMENT_NETWORK_INDUSTRIES)
    if 'financial' in sector and not is_payment_network:
        return 'financial', '🏦 Financiero'

    # 2. REITs and Utilities
    if 'real estate' in sector or 'reit' in industry:
        return 'reit_utility', '🏠 REIT / Inmobiliario'
    if 'utilities' in sector:
        return 'reit_utility', '⚡ Utility / Suministros'

    # 3. No earnings → Hypergrowth or Speculative
    #    BACKTEST FIX B8: Write-off detector.
    #    Before classifying EPS<=0 as speculative, check if Operating Cash Flow
    #    is strongly positive. If OCF is healthy but NI is negative, it's likely
    #    a non-cash write-off (impairments, goodwill, restructuring charges)
    #    rather than a true operational loss. In this case, use OCF-implied EPS
    #    to determine archetype so companies like AT&T (post-WarnerMedia write-off)
    #    or Disney (streaming investment losses) aren't wrongly classified.
    if (eps_ttm is None or eps_ttm <= 0):
        ocf_values = data.get('operating_cashflow_values', [])
        capex_values_arch = data.get('capital_expenditure_values', [])
        shares_out = data.get('shares_outstanding', 0)
        ocf_latest = ocf_values[0] if ocf_values else 0
        capex_latest = abs(capex_values_arch[0]) if capex_values_arch else 0
        implied_fcf = (ocf_latest or 0) - capex_latest

        if implied_fcf > 0 and shares_out and shares_out > 0:
            implied_eps = implied_fcf / shares_out
            if implied_eps > 0:
                ticker_name = data.get('ticker', '?')
                logger.info(f"{ticker_name}: EPS is negative ({eps_ttm}) but OCF-implied EPS is "
                            f"${implied_eps:.2f} → likely write-off, not operational loss. "
                            f"Overriding archetype classification with implied EPS.")
                # Override eps_ttm for archetype detection only (NOT for valuation)
                # Fall through to the profitable archetype detection below
                eps_ttm = implied_eps
            else:
                # OCF-implied EPS is also negative → genuine operational issue
                if rev_growth and rev_growth > 0.15:
                    return 'hypergrowth', '🔥 Hipercrecimiento'
                else:
                    return 'speculative', '⚠️ Especulativo (Sin Beneficios)'
        else:
            if rev_growth and rev_growth > 0.15:
                return 'hypergrowth', '🔥 Hipercrecimiento'
            else:
                return 'speculative', '⚠️ Especulativo (Sin Beneficios)'

    # From here, EPS > 0 is guaranteed

    # 4. COMPOUNDER — rentabilidad primero (ROIC > 20% = always compounder)
    #    EXCEPTION: Mature consumer staples (KO, PG, CL, etc.) have inflated ROIC due to
    #    decades of buybacks reducing equity, but revenue barely grows (<5% CAGR) and
    #    analyst estimates are also low (<6%). The multiphase DCF severely undervalues them.
    #    They belong in classic_value where Graham's formula works correctly.
    #    IMPORTANT: This exception is SECTOR-LIMITED (consumer defensive/staples only)
    #    so that AAPL (Technology) and ACN (Technology) are NOT affected.
    SLOW_GROWTH_SECTORS = ('consumer defensive', 'consumer staples', 'basic materials')
    is_consumer_staple_sector = any(s in sector for s in SLOW_GROWTH_SECTORS)
    is_mature_slow_grower = (
        is_consumer_staple_sector and
        rev_growth is not None and rev_growth < 0.05 and
        growth_rate is not None and growth_rate < 0.07
    )
    if roic_avg and roic_avg > 20 and not is_mature_slow_grower:
        return 'compounder', '🚀 Compounder'

    # 5. COMPOUNDER — moderate ROIC + growth
    #    Lowered growth threshold from 10% to 7% to capture stable compounders
    #    like JNJ (ROIC~17%, growth~8%) that are clearly not classic value stocks.
    if roic_avg and roic_avg > 15 and growth_rate and growth_rate > 0.07:
        return 'compounder', '🚀 Compounder'

    # 6. HYPERGROWTH — only for profitable companies with low ROIC but explosive growth
    #    These are companies growing fast but haven't yet built a durable moat
    if growth_rate and growth_rate > 0.25 and rev_growth and rev_growth > 0.20:
        return 'hypergrowth', '🔥 Hipercrecimiento'

    # 7. TURNAROUND GROWTH — recently profitable companies with explosive revenue
    #    Companies like MRVL that just exited losses but have strong revenue growth.
    #    Their EPS history is mostly negative so DCF on 1 year of FCF is unreliable.
    #    We detect: EPS > 0 (current) + majority of historical EPS negative + revenue accelerating
    #    Uses BOTH multi-year CAGR and 1-year YoY growth (whichever is higher),
    #    because CAGR can be diluted by old bad years in turnaround situations.
    eps_values = data.get('eps_values', [])
    if eps_values and len(eps_values) >= 3:
        negative_eps_count = sum(1 for e in eps_values if e is not None and e <= 0)
        if negative_eps_count >= len(eps_values) * 0.5:  # ≥50% of years had losses
            # Check revenue acceleration: use best of CAGR or 1-year YoY
            rev_yoy = None
            if len(clean_rev) >= 2 and clean_rev[1] > 0:
                rev_yoy = (clean_rev[0] / clean_rev[1]) - 1  # 1-year YoY growth
            best_rev_growth = max(rev_growth or 0, rev_yoy or 0)
            if best_rev_growth > 0.20:
                return 'hypergrowth', '🔥 Turnaround Growth'

    # 8. Classic Value (everything else with positive earnings)
    return 'classic_value', '🏛️ Value Clásico'


# ─── VARIABLE WACC ────────────────────────────────────────────────

def get_wacc(sector: str, market_cap: float) -> float:
    """
    Calculate WACC adjusted by sector and company size.
    Mega caps get a slight discount, small caps a premium.
    """
    sector_lower = (sector or '').lower().strip()
    base_wacc = 0.10  # default

    for key, val in WACC_BY_SECTOR.items():
        if key in sector_lower:
            base_wacc = val
            break

    # Adjust by market cap
    if market_cap and market_cap > 200e9:
        base_wacc -= 0.01  # Mega cap discount
    elif market_cap and market_cap > 10e9:
        pass  # Large cap: no adjustment
    elif market_cap and market_cap > 2e9:
        base_wacc += 0.01  # Mid cap premium
    else:
        base_wacc += 0.02  # Small cap premium

    return max(base_wacc, 0.06)  # Floor at 6%


# ─── GRAHAM VALUATION ────────────────────────────────────────────

def graham_valuation(eps_ttm: float, growth_rate_pct: float) -> float:
    """
    Benjamin Graham Intrinsic Value Formula:
    V = (EPS × (8.5 + 2g) × 4.4) / Y

    Args:
        eps_ttm: Trailing 12-month EPS
        growth_rate_pct: Expected annual growth rate (as percentage, e.g. 10 for 10%)
    Returns:
        Intrinsic value per share
    """
    if not eps_ttm or eps_ttm <= 0:
        return 0

    v = (eps_ttm * (GRAHAM_BASE_PE + GRAHAM_GROWTH_MULT * growth_rate_pct) * GRAHAM_BOND_YIELD_1962) / CURRENT_AAA_BOND_YIELD
    return max(v, 0)


# ─── DCF VALUATION ───────────────────────────────────────────────

def dcf_valuation(fcf_current: float, growth_rate: float, shares: int,
                  total_debt: float = 0, cash: float = 0,
                  wacc: float = 0.10, years: int = 10) -> float:
    """
    Standard single-phase DCF Valuation.
    Used for Classic Value archetype.
    """
    if not fcf_current or fcf_current <= 0 or not shares or shares <= 0:
        return 0

    # Project future FCFs
    projected_fcfs = []
    for year in range(1, years + 1):
        future_fcf = fcf_current * ((1 + growth_rate) ** year)
        discounted = future_fcf / ((1 + wacc) ** year)
        projected_fcfs.append(discounted)

    # Terminal value
    terminal_fcf = fcf_current * ((1 + growth_rate) ** years) * (1 + TERMINAL_GROWTH)
    if wacc > TERMINAL_GROWTH:
        terminal_value = terminal_fcf / (wacc - TERMINAL_GROWTH)
        discounted_terminal = terminal_value / ((1 + wacc) ** years)
    else:
        discounted_terminal = 0

    # Enterprise value → Equity value → Per-share
    enterprise_value = sum(projected_fcfs) + discounted_terminal
    equity_value = enterprise_value + (cash or 0) - (total_debt or 0)
    intrinsic_value = equity_value / shares
    return max(intrinsic_value, 0)


# ─── MULTI-PHASE DCF (COMPOUNDERS) ───────────────────────────────

def multiphase_dcf_valuation(fcf_current: float, high_growth: float, shares: int,
                              total_debt: float = 0, cash: float = 0,
                              wacc: float = 0.10,
                              high_years: int = 5, fade_years: int = 5) -> float:
    """
    Multi-phase DCF for Compounder archetype:
    Phase 1 (years 1-5): High growth rate
    Phase 2 (years 6-10): Linear fade from high growth to terminal growth
    Terminal: Gordon Growth Model
    """
    if not fcf_current or fcf_current <= 0 or not shares or shares <= 0:
        return 0

    projected_fcfs = []
    fcf = fcf_current

    # Phase 1: High growth
    for year in range(1, high_years + 1):
        fcf = fcf * (1 + high_growth)
        pv = fcf / ((1 + wacc) ** year)
        projected_fcfs.append(pv)

    # Phase 2: Fade to terminal growth
    fade_step = (high_growth - TERMINAL_GROWTH) / fade_years
    growth = high_growth
    for year in range(high_years + 1, high_years + fade_years + 1):
        growth = max(growth - fade_step, TERMINAL_GROWTH)
        fcf = fcf * (1 + growth)
        pv = fcf / ((1 + wacc) ** year)
        projected_fcfs.append(pv)

    # Terminal value
    total_years = high_years + fade_years
    terminal_fcf = fcf * (1 + TERMINAL_GROWTH)
    if wacc > TERMINAL_GROWTH:
        tv = terminal_fcf / (wacc - TERMINAL_GROWTH)
        pv_tv = tv / ((1 + wacc) ** total_years)
    else:
        pv_tv = 0

    ev = sum(projected_fcfs) + pv_tv
    equity_value = ev + (cash or 0) - (total_debt or 0)
    return max(equity_value / shares, 0)


# ─── REVENUE-BASED DCF (HYPERGROWTH) ─────────────────────────────

def revenue_dcf_valuation(revenue_current: float, revenue_growth: float,
                          target_margin: float, shares: int,
                          total_debt: float = 0, cash: float = 0,
                          wacc: float = 0.12, years: int = 10) -> float:
    """
    Revenue-based DCF for Hypergrowth archetype:
    Projects revenue growth (decelerating), ramps FCF margin from 0 to target,
    then discounts to present value.
    """
    if not revenue_current or revenue_current <= 0 or not shares or shares <= 0:
        return 0

    projected = []
    rev = revenue_current

    for year in range(1, years + 1):
        # Decelerate growth over time
        yr_growth = revenue_growth * max(0.3, 1.0 - year / (years * 1.2))
        rev = rev * (1 + yr_growth)
        # Ramp margin from ~0% to target over the projection period
        margin = target_margin * min(1.0, year / (years * 0.6))
        fcf = rev * margin
        pv = fcf / ((1 + wacc) ** year)
        projected.append(pv)

    # Terminal value
    terminal_rev = rev * (1 + TERMINAL_GROWTH)
    terminal_fcf = terminal_rev * target_margin
    if wacc > TERMINAL_GROWTH:
        tv = terminal_fcf / (wacc - TERMINAL_GROWTH)
        pv_tv = tv / ((1 + wacc) ** years)
    else:
        pv_tv = 0

    ev = sum(projected) + pv_tv
    equity_value = ev + (cash or 0) - (total_debt or 0)
    return max(equity_value / shares, 0)


# ─── BOOK VALUE VALUATION (FINANCIALS) ────────────────────────────

def book_value_valuation(book_value_per_share: float, roe: float,
                          coe: float = 0.10) -> float:
    """
    Justified Price/Book for Financial archetype:
    Justified P/B = (ROE - g) / (CoE - g)
    where g = sustainable growth = ROE × retention ratio (estimated at ~50%)
    Intrinsic Value = Book Value × Justified P/B
    """
    if not book_value_per_share or book_value_per_share <= 0:
        return 0
    if not roe or roe <= 0:
        roe = 0.08  # conservative default

    g = min(roe * 0.50, 0.05)  # sustainable growth = ROE × 50% retention, capped at 5%

    if coe <= g:
        return 0

    justified_pb = (roe - g) / (coe - g)
    justified_pb = max(min(justified_pb, 5.0), 0.5)  # clamp P/B between 0.5x and 5x
    return book_value_per_share * justified_pb


# ─── DIVIDEND DISCOUNT MODEL (REIT / UTILITY) ────────────────────

def ddm_valuation(dividend_per_share: float, growth_rate: float,
                   discount_rate: float = 0.08) -> float:
    """
    Gordon Growth Model for REITs/Utilities:
    V = D1 / (r - g)
    D1 = current dividend × (1 + g)
    """
    if not dividend_per_share or dividend_per_share <= 0:
        return 0
    if discount_rate <= growth_rate:
        return 0

    d1 = dividend_per_share * (1 + growth_rate)
    return max(d1 / (discount_rate - growth_rate), 0)

# ─── REVERSE DCF (IMPLIED GROWTH) ────────────────────────────────

def reverse_dcf(current_price: float, fcf_current: float, shares: int,
                total_debt: float = 0, cash: float = 0,
                wacc: float = 0.10, years: int = 10) -> float:
    """
    Calculate the growth rate implied by the current market price.
    Uses binary search to find the growth rate that produces the market price.
    
    Returns: implied annual growth rate (e.g. 0.18 = 18%)
    """
    if not fcf_current or fcf_current <= 0 or not shares or shares <= 0 or not current_price:
        return None

    low, high = -0.10, 0.80  # search range: -10% to 80%
    target_price = current_price
    
    for _ in range(50):  # max iterations for binary search
        mid = (low + high) / 2
        computed = dcf_valuation(fcf_current, mid, shares, total_debt, cash, wacc, years)
        if computed is None or computed <= 0:
            low = mid
            continue
        if abs(computed - target_price) / target_price < 0.005:  # 0.5% tolerance
            return round(mid, 4)
        if computed < target_price:
            low = mid
        else:
            high = mid
    
    return round((low + high) / 2, 4)


# ─── SENSITIVITY TABLE ───────────────────────────────────────────

def sensitivity_table(fcf_current: float, shares: int,
                      total_debt: float = 0, cash: float = 0,
                      base_wacc: float = 0.10, base_growth: float = 0.10,
                      archetype_id: str = 'classic_value') -> dict:
    """
    Generate a 3×3 sensitivity table varying WACC and growth rate.
    Returns dict with 'wacc_values', 'growth_values', and 'matrix' (3×3 list).
    """
    if not fcf_current or fcf_current <= 0 or not shares or shares <= 0:
        return None

    wacc_offsets = [-0.02, 0, 0.02]
    growth_offsets = [-0.03, 0, 0.03]
    
    wacc_values = [round(base_wacc + o, 3) for o in wacc_offsets]
    growth_values = [round(max(base_growth + o, 0.01), 3) for o in growth_offsets]
    
    # Use appropriate DCF model
    use_multiphase = archetype_id in ('compounder', 'hypergrowth')
    
    matrix = []
    for w in wacc_values:
        row = []
        for g in growth_values:
            if use_multiphase:
                val = multiphase_dcf_valuation(fcf_current, g, shares, total_debt, cash, w)
            else:
                val = dcf_valuation(fcf_current, g, shares, total_debt, cash, w)
            row.append(round(val, 2) if val else 0)
        matrix.append(row)
    
    return {
        'wacc_values': wacc_values,
        'growth_values': growth_values,
        'matrix': matrix
    }


# ─── MARGIN OF SAFETY ────────────────────────────────────────────

def margin_of_safety(intrinsic_value: float, market_price: float) -> float:
    """
    Margin of Safety = (Intrinsic Value - Market Price) / Intrinsic Value × 100
    Positive = undervalued, Negative = overvalued
    """
    if not intrinsic_value or intrinsic_value <= 0 or not market_price:
        return 0
    return ((intrinsic_value - market_price) / intrinsic_value) * 100


# ─── QUALITY ASSESSMENT ──────────────────────────────────────────

def assess_quality(roic_avg, fcf_trend, eps_trend, mos, non_gaap_flag) -> str:
    """
    Determine if a business is 'Alta Calidad' based on value investing criteria.
    """
    if non_gaap_flag == '🚫 No Elegible':
        return '🚫 No Elegible'

    score = 0

    # ROIC > 15% suggests durable competitive advantage (moat)
    if roic_avg and roic_avg > 20:
        score += 3
    elif roic_avg and roic_avg > 15:
        score += 2
    elif roic_avg and roic_avg > 10:
        score += 1

    # FCF trend
    if fcf_trend == '↑':
        score += 2
    elif fcf_trend == '→':
        score += 1

    # EPS trend
    if eps_trend == '↑':
        score += 2
    elif eps_trend == '→':
        score += 1

    # Margin of Safety
    if mos and mos > 30:
        score += 2
    elif mos and mos > 20:
        score += 1

    if score >= 7:
        return '⭐ Alta Calidad'
    elif score >= 4:
        return '✅ Calidad Aceptable'
    elif score >= 2:
        return '⚠️ Calidad Media'
    return '❌ Calidad Baja'


def _format_usd(val):
    """Format large USD values into human-readable strings."""
    if val >= 1e12:
        return f"${val/1e12:.1f}T"
    if val >= 1e9:
        return f"${val/1e9:.1f}B"
    if val >= 1e6:
        return f"${val/1e6:.1f}M"
    return f"${val:.0f}"


# ─── TAM LOOKUP (INDUSTRY-FIRST, SECTOR FALLBACK) ────────────────

def _lookup_tam(sector: str, industry: str) -> float:
    """Look up TAM using industry first, then sector as fallback."""
    industry_lower = (industry or '').lower().strip()
    sector_lower = (sector or '').lower().strip()

    # Try industry-level match (partial match)
    for key, val in INDUSTRY_TAM_USD.items():
        if key in industry_lower:
            return val

    # Fallback to sector-level
    for key, val in SECTOR_TAM_USD.items():
        if key in sector_lower:
            return val

    return 5.0e12  # ultimate fallback


def generate_qualitative_audit(data: dict, analysis: dict) -> dict:
    """
    Generate an intelligent Qualitative Audit Report based on real financial
    parameters, corporate governance risk scores, business summaries, and
    automated TAM/SAM/SOM market size growth room calculations.
    """
    sector = data.get('sector', '').lower()
    industry = data.get('industry', '')
    roic_avg = analysis.get('roic_hist_avg')
    shares = data.get('shares_outstanding', 0)

    # 1. Economic Moat (Foso Económico)
    if roic_avg and roic_avg > 18:
        moat_strength = "Wide Moat (Foso Amplio)"
        moat_desc = f"La empresa posee una ventaja competitiva excepcional demostrada por un ROIC medio histórico del {roic_avg:.1f}%. "
    elif roic_avg and roic_avg > 12:
        moat_strength = "Narrow Moat (Foso Estrecho)"
        moat_desc = f"La empresa posee ventajas competitivas moderadas reflejadas en un ROIC medio del {roic_avg:.1f}%. "
    else:
        moat_strength = "No Moat / Foso Débil"
        moat_desc = f"Retorno sobre el capital invertido modesto ({roic_avg or 0:.1f}%), lo que sugiere un entorno altamente competitivo. "

    moat_types = []
    if 'technology' in sector or 'communication' in sector:
        moat_types.append("Efecto Red (Network Effect) y Altos Costes de Cambio (Switching Costs) propios de su ecosistema digital.")
    elif 'consumer defensive' in sector:
        moat_types.append("Activos Intangibles potentes (Poder de Marca mundial) y ventajas de escala en distribución.")
    elif 'healthcare' in sector:
        moat_types.append("Activos Intangibles críticos basados en patentes de medicamentos y barreras regulatorias de entrada.")
    elif 'financial' in sector:
        moat_types.append("Altos Costes de Cambio y ventajas de Costes de Producción por escala y depósitos baratos.")
    elif 'industrial' in sector or 'basic materials' in sector:
        moat_types.append("Ventajas en Costes de Producción por eficiencia logística o activos geográficos exclusivos.")
    else:
        moat_types.append("Ventajas operativas por eficiencia a escala.")

    moat_text = moat_desc + "Factores clave: " + " ".join(moat_types)

    # 2. Management Audit (Auditoría de Directiva)
    insider_pct = data.get('held_percent_insiders')
    if insider_pct is not None:
        insider_val = insider_pct * 100
        if insider_val > 1.0:
            skin_game = f"Alineación alta: los directivos poseen el {insider_val:.2f}% de la empresa, lo que indica un fuerte 'Skin in the game'."
        elif insider_val > 0.1:
            skin_game = f"Alineación moderada: directivos poseen el {insider_val:.2f}% de la empresa (significativo en grandes capitalizaciones)."
        else:
            skin_game = "Alineación interna baja: los directivos poseen una participación muy reducida."
    else:
        skin_game = "Sin datos de participación interna de directivos."

    shares_hist = data.get('shares_history', [])
    buyback_text = "Asignación de capital estable."
    if len(shares_hist) >= 2:
        recent_shares = shares_hist[0]
        older_shares = shares_hist[-1]
        if recent_shares and older_shares and recent_shares < older_shares:
            decrease_pct = ((older_shares - recent_shares) / older_shares) * 100
            buyback_text = f"Recompra de acciones activa: reducción del {decrease_pct:.1f}% en acciones en circulación en los últimos años, creando valor para el accionista de forma inteligente."
        elif recent_shares and older_shares and recent_shares > older_shares:
            buyback_text = "Dilución para el accionista: incremento en el número de acciones en circulación en los últimos años."

    debt_val = data.get('total_debt_values', [])
    equity_val = data.get('equity_values', [])
    debt_text = "Estructura de deuda controlada."
    if debt_val and equity_val and debt_val[0] and equity_val[0] and equity_val[0] > 0:
        ratio = (debt_val[0] / equity_val[0]) * 100
        if ratio > 150:
            debt_text = f"⚠️ Apalancamiento elevado: Relación Deuda/Patrimonio del {ratio:.0f}% — vigilar la carga financiera."
        else:
            debt_text = f"Estructura financiera robusta: Relación Deuda/Patrimonio baja-moderada del {ratio:.0f}%."

    mgmt_text = f"{skin_game} {buyback_text} {debt_text}"

    # 3. Risk Analysis (Análisis de Riesgos)
    board_risk = data.get('board_risk')
    comp_risk = data.get('compensation_risk')
    audit_risk = data.get('audit_risk')

    risk_factors = []
    if board_risk and board_risk > 6:
        risk_factors.append("Riesgo elevado en la composición u operatividad del Consejo de Administración (yfinance Board Risk).")
    if comp_risk and comp_risk > 6:
        risk_factors.append("Riesgos en la estructura de compensación de directivos (incentivos desalineados).")
    if audit_risk and audit_risk > 6:
        risk_factors.append("⚠️ Riesgo de auditoría contable elevado — vigilar la transparencia de informes.")

    fcf_trend = analysis.get('fcf_trend', '')
    if fcf_trend == '↓':
        risk_factors.append("Tendencia decreciente en el Flujo de Caja Libre Real en los últimos años.")

    non_gaap = analysis.get('non_gaap_flag', '')
    if 'Precaución' in non_gaap:
        risk_factors.append("Presencia de ajustes y de divergencia Non-GAAP que reduce la transparencia contable.")

    if not risk_factors:
        risk_factors.append("No se detectan riesgos financieros o de gobernanza severos en las métricas analizadas.")

    risk_text = " ".join(risk_factors)

    # 4. TAM/SAM/SOM & Growth — Industry-level granularity
    rev_vals = data.get('revenue_values', [])
    latest_rev = rev_vals[0] if rev_vals else 0
    multiplier = analysis.get('multiplier', 1.0)

    latest_rev_usd = latest_rev / multiplier if latest_rev and multiplier else latest_rev

    tam_val = _lookup_tam(data.get('sector', ''), industry)

    mkt_share_pct = 0.0
    if tam_val > 0 and latest_rev_usd:
        mkt_share_pct = (latest_rev_usd / tam_val) * 100

    formatted_tam = _format_usd(tam_val)
    formatted_rev = _format_usd(latest_rev_usd)

    if mkt_share_pct > 10.0:
        growth_strength = "Saturación del Mercado Elevada"
        growth_desc = f"La empresa ya factura {formatted_rev} USD al año, controlando aproximadamente el {mkt_share_pct:.2f}% de su mercado direccionable global (TAM de {formatted_tam}). El crecimiento futuro dependerá en gran medida de adquisiciones, diversificación o innovación de nuevos productos (poca escalabilidad inercial pura)."
    elif mkt_share_pct > 2.0:
        growth_strength = "Posición Consolidada con Margen de Expansión"
        growth_desc = f"Controla aproximadamente el {mkt_share_pct:.2f}% de su mercado direccionable global (TAM de {formatted_tam}) con ingresos anuales de {formatted_rev} USD. Mantiene una posición sólida en la industria con espacio para seguir expandiendo su cuota de mercado a expensas de competidores menos eficientes."
    else:
        if roic_avg and roic_avg > 15.0:
            growth_strength = "💎 Joya de Crecimiento en Potencia (Baja Cuota + Alto ROIC)"
            growth_desc = f"Operando con una excelente rentabilidad (ROIC medio del {roic_avg:.1f}%), la empresa factura {formatted_rev} USD, lo que representa apenas el {mkt_share_pct:.2f}% de su mercado direccionable global (TAM de {formatted_tam}). Esta combinación de alta eficiencia interna y una pista de crecimiento masiva por delante representa un potencial extraordinario de compounding a largo plazo."
        else:
            growth_strength = "Baja Cuota en Mercado Fragmentado"
            growth_desc = f"La empresa factura {formatted_rev} USD, obteniendo una participación del {mkt_share_pct:.2f}% del mercado global sectorial (TAM de {formatted_tam}). Dado que el retorno del capital es moderado y la cuota es reducida, expandir su presencia requerirá de una disciplinada asignación de capital frente a una competencia fragmentada."

    return {
        'moat_strength': moat_strength,
        'moat_details': moat_text,
        'management_details': mgmt_text,
        'risk_details': risk_text,
        'growth_strength': growth_strength,
        'growth_details': growth_desc
    }


# ─── FULL ANALYSIS ───────────────────────────────────────────────

def run_full_analysis(data: dict) -> dict:
    """
    Run the complete value investing analysis on fetched data.
    Now with archetype-based valuation, variable WACC, and currency handling.
    """
    if data.get('error'):
        return data

    ticker = data.get('ticker', '?')
    current_price = data.get('current_price', 0)
    shares = data.get('shares_outstanding', 0)
    currency = data.get('currency', 'USD')
    financial_currency = data.get('financial_currency', currency)
    market_cap = data.get('market_cap', 0) or 0
    sector = data.get('sector', '')
    industry = data.get('industry', '')

    # ─── Calculate FCF Real ──────────────────────────────────
    fcf_result = calculate_fcf_real(data)

    # ─── Calculate ROIC ──────────────────────────────────────
    roic_result = calculate_roic(data)

    # ─── Non-GAAP Check ──────────────────────────────────────
    non_gaap = check_non_gaap(data)

    # ─── EPS metrics ─────────────────────────────────────────
    eps_values = data.get('eps_values', [])
    eps_ttm = data.get('eps_ttm')
    eps_hist_avg = _avg(eps_values[1:]) if len(eps_values) > 1 else _avg(eps_values)
    eps_trend = _trend(eps_values)

    # ─── Growth rate estimation (with cross-validation) ──────
    revenue_values = data.get('revenue_values', [])
    eps_growth = _growth_rate(eps_values) if eps_values else None
    rev_growth = _growth_rate(revenue_values) if revenue_values else None

    growth = data.get('growth_estimate')
    growth_source = 'default'  # Track where the estimate comes from

    # B1 FIX: Yahoo earningsGrowth can return extreme values (e.g. 7.56 = 756%).
    # Any value > 100% is likely a cyclical recovery spike, not sustainable growth.
    if growth and growth > 1.0:
        logger.info(f"{ticker}: growth_estimate {growth:.2%} is extreme (>100%), discarding")
        growth = None

    if growth and growth > 0:
        base_growth_rate = growth
        growth_source = 'analyst'
    else:
        # Estimate from EPS history (B6 FIX: _growth_rate now returns None instead of 0.05)
        if eps_growth is not None:
            base_growth_rate = eps_growth
            growth_source = 'eps_cagr'
        else:
            base_growth_rate = 0.05
            growth_source = 'default'



    # Analyst sanity check: if Yahoo's estimate is much lower than the company's
    # own revenue CAGR, it's likely a data quality issue (common for non-US tickers,
    # ADRs like RACE). In this case, blend analyst + revenue CAGR.
    if growth_source == 'analyst' and rev_growth and rev_growth > 0:
        if base_growth_rate < rev_growth * 0.4:  # Analyst < 40% of what revenue shows
            blended = (base_growth_rate + rev_growth) / 2
            logger.info(f"{ticker}: Analyst growth {base_growth_rate:.1%} is suspiciously low vs "
                        f"rev CAGR {rev_growth:.1%}. Blending to {blended:.1%}.")
            base_growth_rate = blended
            growth_source = 'blended (analyst+rev_cagr)'

    # Haircut: if EPS growth > 1.5x Revenue growth, it's likely unsustainable (e.g. buybacks, margin expansion).
    if rev_growth and rev_growth > 0 and base_growth_rate > (rev_growth * 1.5):
        growth_rate = rev_growth * 1.5
    else:
        growth_rate = base_growth_rate

    # ─── Detect Archetype ────────────────────────────────────
    archetype_id, archetype_label = detect_archetype(
        data,
        roic_avg=roic_result.get('roic_hist_avg'),
        growth_rate=growth_rate,
        eps_ttm=eps_ttm,
        fcf_ttm=fcf_result.get('fcf_real_ttm'),
    )

    # ─── Apply per-archetype growth cap ──────────────────────
    growth_cap = GROWTH_CAPS.get(archetype_id, 0.25)
    growth_rate = max(min(growth_rate, growth_cap), -0.10)
    growth_rate_pct = growth_rate * 100  # For Graham formula

    # ─── Determine Methodology ────────────────────────────────
    if archetype_id in ('classic_value', 'compounder'):
        methodology = 'value'
        methodology_label = '📜 Value Investing'
    elif archetype_id == 'hypergrowth':
        methodology = 'growth'
        methodology_label = '🚀 Growth Investing'
    elif archetype_id == 'financial':
        methodology = 'book_value'
        methodology_label = '🏦 Book Value'
    elif archetype_id == 'reit_utility':
        methodology = 'dividend'
        methodology_label = '🏠 Dividendos'
    else:  # speculative
        methodology = 'speculative'
        methodology_label = '⚠️ Especulativo'

    # ─── Variable WACC ───────────────────────────────────────
    wacc = get_wacc(sector, market_cap)

    # ─── Currency / ADR Multiplier ───────────────────────────
    # Derives conversion factor from financial-statement currency to trading currency
    # Also captures ADR ratio (e.g., 1 TSM ADR = 5 ordinary shares)
    multiplier = 1.0
    if eps_ttm and eps_values and len(eps_values) > 0 and eps_values[0] is not None:
        eps_financial = eps_values[0]
        if abs(eps_financial) > 0.001 and abs(eps_ttm) > 0.001:
            candidate_mult = eps_financial / eps_ttm
            # Sanity check: multiplier should be reasonable
            if 0.01 < abs(candidate_mult) < 10000:
                multiplier = candidate_mult

    # ─── Get FCF for DCF ─────────────────────────────────────
    fcf_real_values = fcf_result.get('fcf_real_values', [])
    fcf_for_dcf = fcf_result.get('fcf_real_ttm') or (
        fcf_real_values[0] if fcf_real_values else None
    )
    # Fallback to Yahoo's FCF
    if not fcf_for_dcf or fcf_for_dcf <= 0:
        yahoo_fcf = data.get('fcf_yahoo_values', [])
        fcf_for_dcf = yahoo_fcf[0] if yahoo_fcf else 0

    # CYCLICAL FIX: If FCF is very volatile (some years negative, some positive),
    # the most recent FCF may be unreliable. Use the average of positive years instead.
    # This normalizes cyclical businesses like MU, commodity producers, etc.
    positive_fcfs = [v for v in fcf_real_values if v is not None and v > 0]
    if len(fcf_real_values) >= 3 and positive_fcfs:
        negative_count = sum(1 for v in fcf_real_values if v is not None and v < 0)
        if negative_count >= 2:
            # High volatility: at least 2 negative FCF years out of 3+
            normalized_fcf = sum(positive_fcfs) / len(positive_fcfs)
            logger.info(f"{ticker}: Cyclical FCF detected ({negative_count} negative years). "
                        f"Using normalized FCF {normalized_fcf/1e9:.1f}B instead of TTM {(fcf_for_dcf or 0)/1e9:.1f}B")
            fcf_for_dcf = normalized_fcf
            # With normalized FCF, a negative growth rate makes no sense — use conservative default
            if growth_rate < 0:
                growth_rate = 0.03  # 3% conservative growth for normalized earnings
                growth_source = 'normalized'

    # Get most recent debt and cash (financial statement currency)
    debt_list = data.get('total_debt_values', [])
    cash_list = data.get('cash_values', [])
    current_debt = debt_list[0] if debt_list else 0
    current_cash = cash_list[0] if cash_list else 0

    # ─── Archetype-Based Valuation ───────────────────────────
    # All valuation models produce values in financial-statement currency,
    # then we convert to trading currency using the multiplier.

    graham_value = 0
    dcf_value = 0
    alt_value = 0  # Alternative model value
    alt_model_name = ''
    valuation_models_used = []

    if archetype_id == 'classic_value':
        # Classic Value: Graham (only if sector PE < 20x) + Standard DCF
        sector_lower = (sector or '').lower()
        sector_pe = SECTOR_BENCHMARKS.get(sector_lower, {}).get('pe', 15)
        if sector_pe < 20:
            graham_value = graham_valuation(eps_ttm, growth_rate_pct)
        dcf_value = dcf_valuation(
            fcf_current=fcf_for_dcf, growth_rate=growth_rate,
            shares=shares, total_debt=current_debt, cash=current_cash, wacc=wacc
        )

        # EPV FALLBACK: If FCF is very low relative to Net Income (heavy CAPEX companies
        # like MU, capital-intensive industrials), the DCF is unreliable.
        # Use Earnings Power Value = Normalized Net Income / WACC as alternative.
        net_income_vals = data.get('net_income_values', [])
        positive_ni = [v for v in net_income_vals if v is not None and v > 0]
        if positive_ni and fcf_for_dcf and fcf_for_dcf > 0:
            avg_net_income = sum(positive_ni) / len(positive_ni)
            fcf_to_ni_ratio = fcf_for_dcf / avg_net_income if avg_net_income > 0 else 1.0
            if fcf_to_ni_ratio < 0.30:
                # FCF is less than 30% of average Net Income → heavy CAPEX, DCF is misleading
                epv = (avg_net_income / wacc + (current_cash or 0) - (current_debt or 0)) / shares if shares else 0
                epv = max(epv, 0)
                logger.info(f"{ticker}: FCF/NI ratio {fcf_to_ni_ratio:.1%} is very low (heavy CAPEX). "
                            f"Adding EPV fallback: ${epv:.2f} (DCF was ${dcf_value:.2f})")
                alt_value = epv / multiplier if multiplier and abs(multiplier) > 0.001 else epv
                alt_model_name = 'EPV (Earnings Power)'
                valuation_models_used = ['Graham', 'DCF', 'EPV']
            else:
                valuation_models_used = ['Graham', 'DCF']
        else:
            valuation_models_used = ['Graham', 'DCF']

    elif archetype_id == 'compounder':
        # Compounder: Multi-Phase DCF
        dcf_value = multiphase_dcf_valuation(
            fcf_current=fcf_for_dcf, high_growth=growth_rate,
            shares=shares, total_debt=current_debt, cash=current_cash, wacc=wacc
        )
        valuation_models_used = ['DCF Multi-Fase']

    elif archetype_id == 'hypergrowth':
        # Hypergrowth: Revenue-based DCF only (no Graham — EPS likely ≤ 0)
        revenue_values = data.get('revenue_values', [])
        latest_rev = revenue_values[0] if revenue_values else 0
        rev_growth = growth_rate if growth_rate > 0 else 0.20

        # Determine target FCF margin from industry
        industry_lower = (industry or '').lower()
        target_margin = 0.12  # default
        for key, margin in TARGET_FCF_MARGINS.items():
            if key in industry_lower or key in sector.lower():
                target_margin = margin
                break

        dcf_value = revenue_dcf_valuation(
            revenue_current=latest_rev, revenue_growth=rev_growth,
            target_margin=target_margin, shares=shares,
            total_debt=current_debt, cash=current_cash, wacc=wacc + 0.02  # extra risk premium
        )
        alt_model_name = 'DCF sobre Revenue'
        valuation_models_used = ['DCF Revenue-Based']

    elif archetype_id == 'financial':
        # Financial: Book Value Model ONLY
        # DCF is completely invalid for banks/insurance as FCF includes deposits/reserves.
        book_val = data.get('book_value', 0)
        roe = data.get('roe', 0)
        if roe and roe > 0:
            alt_value = book_value_valuation(book_val, roe, coe=wacc)
            alt_model_name = 'P/Book Justificado'
            valuation_models_used = ['P/Book']
        else:
            # Fallback to Graham if ROE is missing and EPS is positive
            if eps_ttm and eps_ttm > 0:
                graham_value = graham_valuation(eps_ttm, growth_rate_pct)
                valuation_models_used = ['Graham (Fallback)']
            else:
                valuation_models_used = ['Ninguno aplicable']

    elif archetype_id == 'reit_utility':
        # REIT/Utility: DDM ONLY
        # DCF on FCF is invalid as REITs use FFO and Utilities have massive CAPEX distortions.
        raw_div_yield = data.get('dividend_yield', 0) or 0
        dividend_rate = data.get('dividend_rate', 0) or 0
        div_growth = min(growth_rate, 0.05) if growth_rate > 0 else 0.02
        if dividend_rate and dividend_rate > 0 and raw_div_yield <= 0.20:
            alt_value = ddm_valuation(dividend_rate, div_growth, discount_rate=wacc)
            alt_model_name = 'Div. Discount (DDM)'
            valuation_models_used = ['DDM']
        else:
            # Fallback to Graham
            if eps_ttm and eps_ttm > 0:
                graham_value = graham_valuation(eps_ttm, growth_rate_pct)
                valuation_models_used = ['Graham (Fallback)']
            else:
                valuation_models_used = ['Ninguno aplicable']

    else:  # 'speculative'
        # Speculative: No reliable valuation possible
        # Try DCF if we somehow have positive FCF
        dcf_value = dcf_valuation(
            fcf_current=fcf_for_dcf, growth_rate=growth_rate,
            shares=shares, total_debt=current_debt, cash=current_cash, wacc=wacc + 0.02
        )
        valuation_models_used = ['DCF (tentativo)'] if dcf_value > 0 else ['Ninguno aplicable']

    # ─── Convert all values to trading currency ──────────────
    if multiplier and abs(multiplier) > 0.001:
        graham_value = graham_value / multiplier if graham_value else 0
        dcf_value = dcf_value / multiplier if dcf_value else 0
        alt_value = alt_value / multiplier if alt_value else 0

    # ─── Best Intrinsic Value (smart selection) ──────────────
    # D2 FIX: Using min() was ultra-conservative and let broken models (e.g. low-FCF DCF)
    # dominate. Now we use median for 3+ models, average for 2 models.
    valid_values = [v for v in [graham_value, dcf_value, alt_value] if v and v > 0]
    if len(valid_values) >= 3:
        # Median: robust against one outlier model
        valid_values.sort()
        best_intrinsic = valid_values[len(valid_values) // 2]
    elif len(valid_values) == 2:
        # Average of two models
        best_intrinsic = sum(valid_values) / 2
    elif len(valid_values) == 1:
        best_intrinsic = valid_values[0]
    else:
        best_intrinsic = 0

    # ─── Margin of Safety (using trading currency) ───────────
    mos = margin_of_safety(best_intrinsic, current_price)
    ms_abs = mos

    # ─── Reverse DCF (Implied Growth) ────────────────────────
    # Convert FCF to trading currency for the reverse DCF calculation
    fcf_for_reverse = fcf_for_dcf / multiplier if fcf_for_dcf and multiplier and abs(multiplier) > 0.001 else fcf_for_dcf
    debt_for_reverse = current_debt / multiplier if current_debt and multiplier and abs(multiplier) > 0.001 else current_debt
    cash_for_reverse = current_cash / multiplier if current_cash and multiplier and abs(multiplier) > 0.001 else current_cash
    implied_growth = reverse_dcf(
        current_price=current_price,
        fcf_current=fcf_for_reverse,
        shares=shares,
        total_debt=debt_for_reverse or 0,
        cash=cash_for_reverse or 0,
        wacc=wacc,
    ) if methodology != 'speculative' else None

    # ─── Sensitivity Table (3×3) ─────────────────────────────
    sens_table = sensitivity_table(
        fcf_current=fcf_for_reverse,
        shares=shares,
        total_debt=debt_for_reverse or 0,
        cash=cash_for_reverse or 0,
        base_wacc=wacc,
        base_growth=growth_rate,
        archetype_id=archetype_id,
    ) if methodology not in ('speculative', 'growth') and fcf_for_dcf and fcf_for_dcf > 0 else None

    # ─── PER & EV/FCF (Actuals) ──────────────────────────────
    per_actual = data.get('per_trailing')
    ev_fcf = None
    ev_fcf_pre_sbc = None  # D3 FIX: comparable with market screeners
    ev = data.get('enterprise_value', 0)
    yahoo_fcf_list = data.get('fcf_yahoo_values', [])
    yahoo_fcf_latest = yahoo_fcf_list[0] if yahoo_fcf_list else None
    if ev and fcf_for_dcf and fcf_for_dcf > 0:
        ev_fcf = ev / fcf_for_dcf
    if ev and yahoo_fcf_latest and yahoo_fcf_latest > 0:
        ev_fcf_pre_sbc = ev / yahoo_fcf_latest

    # ─── Growth Investing Metrics ─────────────────────────────
    latest_rev = revenue_values[0] if revenue_values else 0
    fcf_margin_for_growth = 0
    if latest_rev and latest_rev > 0 and fcf_for_dcf:
        fcf_margin_for_growth = fcf_for_dcf / latest_rev

    growth_metrics = calculate_growth_metrics(
        data=data,
        growth_rate=growth_rate,
        rev_growth=rev_growth,
        fcf_margin=fcf_margin_for_growth,
        per_actual=per_actual,
        per_forward=data.get('per_forward'),
        ev=ev,
        revenue_current=latest_rev,
    )

    # Growth metrics (PEG, Rule of 40) are now available as complementary
    # indicators for ALL methodologies that have valid data.
    # The semáforo still uses PEG as PRIMARY signal only for 'growth' methodology.

    # ─── Historical Multiples & MS Relativo ──────────────────
    hist_prices = data.get('historical_prices', [])
    fiscal_dates = data.get('fiscal_dates', [])

    per_history = []
    ev_fcf_history = []

    equity = data.get('equity_values', [])
    debt = data.get('total_debt_values', [])
    cash = data.get('cash_values', [])
    shares_hist = data.get('shares_history', [])

    min_len_mult = min(len(eps_values), len(hist_prices)) if eps_values and hist_prices else 0
    for i in range(min_len_mult):
        price = hist_prices[i]
        eps = eps_values[i]

        # Convert historical price to reporting currency for clean comparison
        price_reporting = price * multiplier if price else None

        # PER = Price / EPS (both in reporting currency)
        if price_reporting and eps and eps > 0:
            per_history.append(price_reporting / eps)
        else:
            per_history.append(None)

        # EV/FCF with historical shares when available
        fcf_val = fcf_result.get('fcf_real_values')[i] if fcf_result.get('fcf_real_values') and i < len(fcf_result['fcf_real_values']) else None
        hist_shares = shares_hist[i] if i < len(shares_hist) and shares_hist[i] else shares
        debt_val = debt[i] if i < len(debt) else 0
        cash_val = cash[i] if i < len(cash) else 0

        if price_reporting and hist_shares and hist_shares > 0 and fcf_val and fcf_val > 0:
            ev_hist = (price_reporting * hist_shares) + (debt_val or 0) - (cash_val or 0)
            ev_fcf_history.append(ev_hist / fcf_val)
        else:
            ev_fcf_history.append(None)

    # Calculate 5-year averages
    per_avg_5y = _avg([p for p in per_history if p is not None and p > 0])
    ev_fcf_avg_5y = _avg([e for e in ev_fcf_history if e is not None and e > 0])

    # Select preferred multiple for MS_Relativo
    multiple_type = 'N/A'
    mult_actual = None
    mult_avg_5y = None
    ms_rel = -100.0  # Default to highly overvalued if no data exists

    if ev_fcf and ev_fcf > 0 and ev_fcf_avg_5y and ev_fcf_avg_5y > 0:
        multiple_type = 'EV/FCF'
        mult_actual = ev_fcf
        mult_avg_5y = ev_fcf_avg_5y
        ms_rel = ((ev_fcf_avg_5y - ev_fcf) / ev_fcf_avg_5y) * 100
    elif per_actual and per_actual > 0 and per_avg_5y and per_avg_5y > 0:
        multiple_type = 'PER'
        mult_actual = per_actual
        mult_avg_5y = per_avg_5y
        ms_rel = ((per_avg_5y - per_actual) / per_avg_5y) * 100
    elif eps_ttm and eps_ttm > 0:
        # Fallback to computing per_actual if yfinance per_actual was None
        calc_per_actual = current_price / eps_ttm
        if calc_per_actual > 0 and per_avg_5y and per_avg_5y > 0:
            multiple_type = 'PER'
            mult_actual = calc_per_actual
            mult_avg_5y = per_avg_5y
            ms_rel = ((per_avg_5y - calc_per_actual) / per_avg_5y) * 100

    # ─── Traffic Light (Semáforo) Lógica ─────────────────────
    non_gaap_flag = non_gaap.get('non_gaap_flag', '')

    estado_semaforo = '🟡 MANTENER / SEGUIMIENTO'
    alerta_compra = 0

    if non_gaap_flag == '🚫 No Elegible':
        estado_semaforo = '🚫 NO ELEGIBLE'
        alerta_compra = 0
    elif methodology == 'value':
        has_relative_data = multiple_type != 'N/A'
        if has_relative_data:
            # Full signal: both absolute and relative margins available
            if ms_abs > 15.0 and ms_rel > 10.0:
                estado_semaforo = '🟢 STRONG BUY'
                alerta_compra = 1
            elif ms_abs < 0.0 and ms_rel < 0.0:
                estado_semaforo = '🔴 SOBREVALORADA'
                alerta_compra = 0
            else:
                estado_semaforo = '🟡 MANTENER / SEGUIMIENTO'
        else:
            # BACKTEST FIX B9: Fallback when no historical multiples available.
            # Without ms_rel, the Strong Buy was mathematically impossible even
            # with 70%+ MoS (AAPL 2016, BABA 2022, etc.). Use ms_abs alone
            # with a higher threshold (30% instead of 15%) to compensate for
            # the missing relative confirmation.
            if ms_abs > 30.0:
                estado_semaforo = '🟢 STRONG BUY'
                alerta_compra = 1
            elif ms_abs < -15.0:
                estado_semaforo = '🔴 SOBREVALORADA'
                alerta_compra = 0
            else:
                estado_semaforo = '🟡 MANTENER / SEGUIMIENTO'
    elif methodology == 'growth':
        peg = growth_metrics.get('peg_forward') or growth_metrics.get('peg_trailing')
        rule40 = growth_metrics.get('rule_of_40')
        if peg and rule40:
            if peg < 1.5 and rule40 >= 40:
                estado_semaforo = '🟢 GROWTH BUY'
                alerta_compra = 1
            elif peg > 2.5 or rule40 < 20:
                estado_semaforo = '🔴 GROWTH OVERPRICED'
                alerta_compra = 0
            else:
                estado_semaforo = '🟡 GROWTH HOLD'
        else:
            estado_semaforo = '🟡 SIN DATOS GROWTH'
    elif methodology == 'speculative':
        estado_semaforo = '⚠️ ALTO RIESGO'
        alerta_compra = 0
    else:  # book_value, dividend
        if ms_abs > 15.0:
            estado_semaforo = '🟢 STRONG BUY'
            alerta_compra = 1
        elif ms_abs < 0.0:
            estado_semaforo = '🔴 SOBREVALORADA'
            alerta_compra = 0
        else:
            estado_semaforo = '🟡 MANTENER / SEGUIMIENTO'

    # ─── Quality Assessment ──────────────────────────────────
    calidad = assess_quality(
        roic_result.get('roic_hist_avg'),
        fcf_result.get('fcf_trend'),
        eps_trend,
        mos,
        non_gaap_flag
    )

    # ─── Margin Analysis (I6) ────────────────────────────────
    gross_profit_values = data.get('gross_profit_values', [])
    revenue_values = data.get('revenue_values', [])
    net_income_values = data.get('net_income_values', [])
    ebit_values = data.get('ebit_values', [])
    
    current_gross_margin = None
    current_operating_margin = None
    current_net_margin = None

    if revenue_values and revenue_values[0] and revenue_values[0] > 0:
        if gross_profit_values and gross_profit_values[0]:
            current_gross_margin = gross_profit_values[0] / revenue_values[0]
        if ebit_values and ebit_values[0]:
            current_operating_margin = ebit_values[0] / revenue_values[0]
        if net_income_values and net_income_values[0]:
            current_net_margin = net_income_values[0] / revenue_values[0]

    # ─── Debt Analysis (I5) ──────────────────────────────────
    interest_values = data.get('interest_values', [])
    ebitda_values = data.get('ebitda_values', [])
    current_interest = interest_values[0] if interest_values else 0
    current_ebitda = ebitda_values[0] if ebitda_values else 0
    current_ebit = ebit_values[0] if ebit_values else 0

    net_debt = current_debt - current_cash
    net_debt_ebitda = net_debt / current_ebitda if current_ebitda and current_ebitda > 0 else None
    
    interest_coverage = None
    if current_interest and current_interest > 0 and current_ebit and current_ebit > 0:
        interest_coverage = current_ebit / current_interest
    elif current_interest == 0 and current_ebit and current_ebit > 0:
        interest_coverage = 999  # Effectively infinite coverage if no debt interest

    # ─── Sector Benchmarking (I7) ────────────────────────────
    sector_lower = sector.lower() if sector else ''
    benchmark = SECTOR_BENCHMARKS.get(sector_lower)
    sector_assessment = "La empresa no se ha comparado con pares sectoriales por falta de datos."
    if benchmark and per_actual and per_actual > 0 and roic_result.get('roic_hist_avg'):
        pe_med = benchmark['pe']
        roic_med = benchmark['roic']
        pe_diff = (per_actual - pe_med) / pe_med
        roic_diff = (roic_result['roic_hist_avg'] - roic_med) / roic_med
        
        pe_eval = "con prima" if pe_diff > 0.1 else "con descuento" if pe_diff < -0.1 else "alineado"
        roic_eval = "supera" if roic_diff > 0.1 else "está por debajo de" if roic_diff < -0.1 else "está en línea con"
        
        sector_assessment = f"El ROIC ({roic_result['roic_hist_avg']:.1f}%) {roic_eval} la media sectorial de {sector} ({roic_med}%). El PER ({per_actual:.1f}x) cotiza {pe_eval} frente a la media de la industria ({pe_med}x)."

    # ─── Qualitative Audit ───────────────────────────────────
    qualitative_audit = generate_qualitative_audit(data, {
        'roic_hist_avg': roic_result.get('roic_hist_avg'),
        'fcf_trend': fcf_result.get('fcf_trend'),
        'non_gaap_flag': non_gaap_flag,
        'multiplier': multiplier
    })
    
    # Inject Sector Assessment into the audit
    qualitative_audit['growth_details'] = qualitative_audit.get('growth_details', '') + " " + sector_assessment

    # ─── Decision Criterion: Compra de Calidad (Caso Ferrari) ─
    if estado_semaforo == '🟡 MANTENER / SEGUIMIENTO':
        if ms_abs > 0.0 and ms_rel > 0.0 and roic_result.get('roic_hist_avg', 0) > 18.0:
            has_buybacks = False
            shares_history = data.get('shares_history', [])
            if len(shares_history) >= 2 and shares_history[0] and shares_history[-1] and shares_history[0] < shares_history[-1]:
                has_buybacks = True
            insider_pct = data.get('held_percent_insiders', 0) or 0

            if has_buybacks or (insider_pct * 100 > 0.1):
                estado_semaforo = '🟢 COMPRA DE CALIDAD'
                alerta_compra = 1

    # ─── Dividend Yield Sanity Check ─────────────────────────
    dividend_yield = data.get('dividend_yield', 0) or 0
    dividend_yield_valid = True
    if dividend_yield > 0.20:
        # Likely a data error (ADR mismatch, special dividend, etc.)
        logger.warning(f"{ticker}: Dividend yield {dividend_yield:.2%} suspiciously high - marking as unreliable")
        dividend_yield_valid = False

    payout_ratio = data.get('payout_ratio', 0) or 0
    if payout_ratio > 2.0:
        # Payout ratio > 200% is also suspect
        payout_ratio = None

    # ─── Build result ────────────────────────────────────────
    analysis = {
        'ticker': ticker,
        'empresa': data.get('empresa', ''),
        'sector': data.get('sector', ''),
        'industry': data.get('industry', ''),
        'currency': currency,
        'financial_currency': financial_currency,
        'current_price': current_price,
        'market_cap': data.get('market_cap', 0),
        'shares_outstanding': shares,
        'fiscal_dates': data.get('fiscal_dates', []),
        'historical_prices': hist_prices,

        # Archetype
        'archetype_id': archetype_id,
        'archetype_label': archetype_label,
        'valuation_models_used': valuation_models_used,
        'wacc_used': wacc,

        # EPS
        'eps_values': eps_values,
        'eps_ttm': eps_ttm,
        'eps_hist_avg': eps_hist_avg,
        'eps_trend': eps_trend,

        # FCF Real
        'fcf_real_values': fcf_result.get('fcf_real_values', []),
        'fcf_pre_sbc_values': fcf_result.get('fcf_pre_sbc_values', []),
        'sbc_values': fcf_result.get('sbc_values', []),
        'fcf_real_ttm': fcf_result.get('fcf_real_ttm'),
        'fcf_ttm_pre_sbc': fcf_result.get('fcf_ttm_pre_sbc'),
        'fcf_real_hist_avg': fcf_result.get('fcf_real_hist_avg'),
        'fcf_trend': fcf_result.get('fcf_trend'),

        # ROIC
        'roic_values': roic_result.get('roic_values', []),
        'roic_current': roic_result.get('roic_current'),
        'roic_hist_avg': roic_result.get('roic_hist_avg'),
        'roic_trend': roic_result.get('roic_trend'),

        # Methodology
        'methodology': methodology,
        'methodology_label': methodology_label,

        # Valuation
        'per_actual': per_actual,
        'per_history': per_history,
        'per_forward': data.get('per_forward'),
        'ev_fcf_actual': ev_fcf,
        'ev_fcf_pre_sbc': ev_fcf_pre_sbc,  # D3: comparable with screeners (uses Yahoo FCF)
        'ev_fcf_history': ev_fcf_history,
        'graham_value': graham_value,
        'dcf_value': dcf_value,
        'alt_value': alt_value if alt_value > 0 else None,
        'alt_model_name': alt_model_name,
        'intrinsic_value': best_intrinsic,
        'margen_seguridad': mos,
        'ms_absoluto': ms_abs,
        'ms_relativo': ms_rel,
        'analyst_target': data.get('analyst_target'),  # B2 FIX: was duplicated with wrong key
        'alerta_compra': alerta_compra,
        
        # New Phase 3 Metrics
        'current_gross_margin': current_gross_margin,
        'current_operating_margin': current_operating_margin,
        'current_net_margin': current_net_margin,
        'net_debt_ebitda': net_debt_ebitda,
        'interest_coverage': interest_coverage,
        'sector_assessment': sector_assessment,
        
        'estado_semaforo': estado_semaforo,
        'multiple_type': multiple_type,
        'multiple_actual': mult_actual,
        'multiple_avg_5y': mult_avg_5y,
        'qualitative_audit': qualitative_audit,

        # Quality
        'calidad': calidad,
        'non_gaap_flag': non_gaap_flag,
        'non_gaap_detail': non_gaap.get('non_gaap_detail', ''),

        # Growth
        'growth_rate': growth_rate,
        'growth_rate_pct': growth_rate_pct,
        'analyst_target': data.get('analyst_target'),

        # Growth Investing Metrics
        'peg_trailing': growth_metrics.get('peg_trailing'),
        'peg_forward': growth_metrics.get('peg_forward'),
        'peg_signal': growth_metrics.get('peg_signal'),
        'rule_of_40': growth_metrics.get('rule_of_40'),
        'rule_of_40_signal': growth_metrics.get('rule_of_40_signal'),
        'ev_revenue_current': growth_metrics.get('ev_revenue_current'),
        'ev_revenue_forward_3y': growth_metrics.get('ev_revenue_forward_3y'),
        'has_growth_metrics': growth_metrics.get('has_growth_metrics', False),

        # Dividend
        'dividend_yield': dividend_yield if dividend_yield_valid else None,
        'dividend_yield_raw': dividend_yield,  # Always available for debugging
        'dividend_yield_valid': dividend_yield_valid,
        'payout_ratio': payout_ratio,

        # New: Reverse DCF & Sensitivity
        'implied_growth': implied_growth,
        'sensitivity': sens_table,

        # New: Beta & Risk
        'beta': data.get('beta'),

        # New: Growth Source (confidence indicator)
        'growth_source': growth_source,

        # Revenue (for frontend display)
        'revenue_values': revenue_values,

        # Business Summary (for thesis)
        'business_summary': data.get('business_summary', ''),

        # Quarterly Earnings History & Calendar
        'quarterly_data': data.get('quarterly_data', []),
        'next_earnings': data.get('next_earnings'),

        # Meta
        'fetched_at': data.get('fetched_at', ''),
        'error': None
    }

    return analysis


def generate_investment_thesis(analysis: dict) -> str:
    """
    Generate a rich investment thesis with specific data, sector context,
    SBC warnings, and implied growth sanity check.
    """
    ticker = analysis.get('ticker', '?')
    empresa = analysis.get('empresa', '?')
    mos = analysis.get('margen_seguridad', 0)
    roic = analysis.get('roic_current', 0)
    calidad = analysis.get('calidad', '')
    fcf_trend = analysis.get('fcf_trend', '?')
    per = analysis.get('per_actual', 0)
    price = analysis.get('current_price', 0)
    intrinsic = analysis.get('intrinsic_value', 0)
    archetype = analysis.get('archetype_label', '')
    currency = analysis.get('currency', 'USD')
    sector = analysis.get('sector', '')
    industry = analysis.get('industry', '')
    implied = analysis.get('implied_growth')
    growth_rate = analysis.get('growth_rate', 0)
    growth_source = analysis.get('growth_source', 'default')
    fcf_ttm = analysis.get('fcf_real_ttm')
    sbc_vals = analysis.get('sbc_values', [])
    fcf_pre_sbc = analysis.get('fcf_ttm_pre_sbc')
    beta = analysis.get('beta')
    summary = analysis.get('business_summary', '')

    parts = []

    # Business context
    if summary:
        truncated = summary[:200] + '...' if len(summary) > 200 else summary
        parts.append(f"{empresa} ({industry}, {sector}): {truncated}")
    else:
        parts.append(f"{empresa} opera en {industry} ({sector}).")

    # Archetype
    parts.append(f"Clasificada como {archetype}.")

    # Quality + ROIC
    if roic and roic > 20:
        parts.append(f"ROIC del {roic:.1f}% indica un moat económico fuerte (ventaja competitiva duradera).")
    elif roic and roic > 12:
        parts.append(f"ROIC del {roic:.1f}% sugiere ventajas competitivas moderadas.")
    elif roic:
        parts.append(f"ROIC del {roic:.1f}% — retorno sobre capital modesto.")

    # FCF + SBC warning
    if fcf_ttm:
        fcf_str = f"${fcf_ttm/1e9:.1f}B" if abs(fcf_ttm) >= 1e9 else f"${fcf_ttm/1e6:.0f}M"
        parts.append(f"FCF Real (ajustado por SBC): {fcf_str}, tendencia {fcf_trend}.")
    if sbc_vals and sbc_vals[0] and fcf_pre_sbc and fcf_pre_sbc > 0:
        sbc_pct = (sbc_vals[0] / fcf_pre_sbc) * 100
        if sbc_pct > 30:
            parts.append(f"⚠️ SBC elevado ({sbc_pct:.0f}% del FCF pre-SBC) — dilución significativa para el accionista.")
        elif sbc_pct > 15:
            parts.append(f"SBC representa el {sbc_pct:.0f}% del FCF pre-SBC — nivel moderado de dilución.")

    # Valuation
    if mos > 30:
        parts.append(f"Cotiza a {currency} {price:.2f} vs valor intrínseco {currency} {intrinsic:.2f} — Margen de seguridad amplio ({mos:.0f}%).")
        if '⭐' in calidad or '✅' in calidad:
            parts.append("⚠️ Alerta: Números excelentes pero castigo bursátil severo. Auditar si hay disrupción competitiva permanente o si es una oportunidad temporal.")
    elif mos > 20:
        parts.append(f"Margen de seguridad del {mos:.0f}% — dentro del rango aceptable para inversión valor.")
    elif mos > 0:
        parts.append(f"Margen de seguridad del {mos:.0f}% — insuficiente, esperar mejor precio.")
    else:
        parts.append(f"Cotiza por encima del valor intrínseco estimado — sobrevalorada.")

    # Implied Growth sanity check
    if implied is not None and growth_rate:
        implied_pct = implied * 100
        growth_pct = growth_rate * 100
        if implied_pct > growth_pct * 1.5:
            parts.append(f"⚠️ El precio actual implica un crecimiento del {implied_pct:.1f}% anual (vs {growth_pct:.1f}% estimado) — el mercado es muy optimista.")
        elif implied_pct < growth_pct * 0.5 and implied_pct > 0:
            parts.append(f"💎 El precio actual solo implica un crecimiento del {implied_pct:.1f}% anual (vs {growth_pct:.1f}% estimado) — posible oportunidad.")

    # Growth confidence
    if growth_source == 'default':
        parts.append("📊 Nota: Estimación de crecimiento basada en valor por defecto (5%) — sin datos de analistas ni historial suficiente.")
    elif growth_source == 'eps_cagr':
        parts.append("📊 Estimación de crecimiento basada en el CAGR histórico de beneficios.")

    # Beta
    if beta and beta > 1.5:
        parts.append(f"Beta de {beta:.2f} — alta volatilidad relativa al mercado.")
    elif beta and beta < 0.7:
        parts.append(f"Beta de {beta:.2f} — activo defensivo con baja volatilidad.")

    return " ".join(parts)

