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


def _growth_rate(values):
    """
    Estimate compound annual growth rate from values (most recent first).
    """
    clean = [v for v in values if v is not None and v > 0]
    if len(clean) < 2:
        return 0.05  # default 5% if insufficient data
    n = len(clean) - 1
    if clean[-1] <= 0 or clean[0] <= 0:
        return 0.05
    cagr = (clean[0] / clean[-1]) ** (1 / n) - 1
    return max(min(cagr, 0.25), -0.10)  # clamp between -10% and 25%


# ─── FCF REAL ─────────────────────────────────────────────────────

def calculate_fcf_real(data: dict) -> dict:
    """
    Calculate Real Free Cash Flow (GAAP-only):
    FCF = EBITDA - CAPEX - Interest - Taxes - ΔWorkingCapital

    Returns dict with historical and TTM FCF values.
    """
    ebitda = data.get('ebitda_values', [])
    capex = data.get('capex_values', [])
    interest = data.get('interest_values', [])
    taxes = data.get('tax_values', [])
    wc_changes = data.get('wc_values', [])

    min_len = min(len(ebitda), len(capex)) if ebitda and capex else 0

    fcf_real_values = []
    for i in range(min_len):
        e = ebitda[i] or 0
        c = capex[i] or 0
        intr = interest[i] if i < len(interest) else 0
        tax = taxes[i] if i < len(taxes) else 0
        wc = wc_changes[i] if i < len(wc_changes) else 0

        # FCF = EBITDA - |CapEx| - |Interest| - |Taxes| + ΔWC
        # Note: capex already abs()'d in fetcher, but we abs() again for safety
        fcf = e - abs(c) - abs(intr or 0) - abs(tax or 0) + (wc or 0)
        fcf_real_values.append(fcf)

    # TTM calculation
    ebitda_ttm = data.get('ebitda_ttm')
    fcf_ttm = None
    if ebitda_ttm and capex:
        capex_latest = capex[0] if capex else 0
        interest_latest = interest[0] if interest else 0
        tax_latest = taxes[0] if taxes else 0
        wc_latest = wc_changes[0] if wc_changes else 0
        fcf_ttm = ebitda_ttm - abs(capex_latest) - abs(interest_latest or 0) - abs(tax_latest or 0) + (wc_latest or 0)

    hist_avg = _avg(fcf_real_values[1:]) if len(fcf_real_values) > 1 else _avg(fcf_real_values)

    return {
        'fcf_real_values': fcf_real_values,
        'fcf_real_ttm': fcf_ttm,
        'fcf_real_hist_avg': hist_avg,
        'fcf_trend': _trend(fcf_real_values),
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
        eq = equity[i] if i < len(equity) else 0
        d = debt[i] if i < len(debt) else 0
        c = cash[i] if i < len(cash) else 0
        invested_capital = (eq or 0) + (d or 0) - (c or 0)

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

    Classification priority:
    1. Financial Services → 'financial'
    2. REITs / Utilities → 'reit_utility'
    3. EPS ≤ 0 + Revenue Growth > 15% → 'hypergrowth'
    4. EPS ≤ 0 + Low Revenue Growth → 'speculative'
    5. EPS > 0 + growth > 25% + rev_growth > 20% → 'hypergrowth'
    6. ROIC > 25% (ultra-high moat, regardless of growth) → 'compounder'
    7. ROIC > 15% + growth > 10% → 'compounder'
    8. ROIC > 15% + active buybacks → 'compounder'
    9. Everything else with EPS > 0 → 'classic_value'
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

    # Buyback detection: shares outstanding declining over time
    shares_history = data.get('shares_history', [])
    has_buybacks = False
    if len(shares_history) >= 2:
        clean_shares = [s for s in shares_history if s is not None and s > 0]
        if len(clean_shares) >= 2 and clean_shares[0] < clean_shares[-1]:
            # Most recent < oldest → shrinking share count
            shrink_pct = (clean_shares[-1] - clean_shares[0]) / clean_shares[-1]
            has_buybacks = shrink_pct > 0.02  # At least 2% reduction over the period

    # 1. Financial Services (banks, insurance, asset management)
    if 'financial' in sector:
        return 'financial', '🏦 Financiero'

    # 2. REITs and Utilities
    if 'real estate' in sector or 'reit' in industry:
        return 'reit_utility', '🏠 REIT / Inmobiliario'
    if 'utilities' in sector:
        return 'reit_utility', '⚡ Utility / Suministros'

    # 3. Hypergrowth (negative EPS with strong revenue growth)
    if (eps_ttm is None or eps_ttm <= 0):
        if rev_growth and rev_growth > 0.15:
            return 'hypergrowth', '🔥 Hipercrecimiento'
        else:
            return 'speculative', '⚠️ Especulativo (Sin Beneficios)'

    # From here, EPS > 0 is guaranteed
    if growth_rate and growth_rate > 0.25 and rev_growth and rev_growth > 0.20:
        return 'hypergrowth', '🔥 Hipercrecimiento'

    # 4. Compounder — two paths to qualify:
    #    A) Ultra-high ROIC (>25%): massive moat regardless of growth (e.g. Apple, Visa)
    if roic_avg and roic_avg > 25:
        return 'compounder', '🚀 Compounder'

    #    B) High ROIC (>15%) with moderate-high growth
    if roic_avg and roic_avg > 15 and growth_rate and growth_rate > 0.10:
        return 'compounder', '🚀 Compounder'

    # 5. Classic Value (everything else with positive earnings)
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
    if growth and growth > 0:
        base_growth_rate = growth
    else:
        # Estimate from EPS history
        base_growth_rate = eps_growth if eps_growth else 0.05
    
    # Haircut: if EPS growth > 1.5x Revenue growth, it's likely unsustainable (e.g. buybacks, margin expansion).
    # We apply this sanity check to prevent overvaluation, except for hypergrowth which is evaluated on revenue anyway.
    if rev_growth and rev_growth > 0 and base_growth_rate > (rev_growth * 1.5):
        growth_rate = rev_growth * 1.5
    else:
        growth_rate = base_growth_rate
        
    growth_rate_pct = growth_rate * 100  # For Graham formula

    # ─── Detect Archetype ────────────────────────────────────
    archetype_id, archetype_label = detect_archetype(
        data,
        roic_avg=roic_result.get('roic_hist_avg'),
        growth_rate=growth_rate,
        eps_ttm=eps_ttm,
        fcf_ttm=fcf_result.get('fcf_real_ttm'),
    )

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
    fcf_for_dcf = fcf_result.get('fcf_real_ttm') or (
        fcf_result['fcf_real_values'][0] if fcf_result.get('fcf_real_values') else None
    )
    # Fallback to Yahoo's FCF
    if not fcf_for_dcf or fcf_for_dcf <= 0:
        yahoo_fcf = data.get('fcf_yahoo_values', [])
        fcf_for_dcf = yahoo_fcf[0] if yahoo_fcf else 0

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
        # Classic Value: Graham + Standard DCF
        graham_value = graham_valuation(eps_ttm, growth_rate_pct)
        dcf_value = dcf_valuation(
            fcf_current=fcf_for_dcf, growth_rate=growth_rate,
            shares=shares, total_debt=current_debt, cash=current_cash, wacc=wacc
        )
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
        # Financial: Book Value Model + standard DCF as secondary
        book_val = data.get('book_value', 0)
        roe = data.get('roe', 0)
        if roe and roe > 0:
            alt_value = book_value_valuation(book_val, roe, coe=wacc)
            alt_model_name = 'P/Book Justificado'
        # Also compute DCF if FCF is available
        dcf_value = dcf_valuation(
            fcf_current=fcf_for_dcf, growth_rate=growth_rate,
            shares=shares, total_debt=current_debt, cash=current_cash, wacc=wacc
        )
        valuation_models_used = ['P/Book', 'DCF']

    elif archetype_id == 'reit_utility':
        # REIT/Utility: DDM + DCF
        dividend_rate = data.get('dividend_rate', 0) or 0
        div_growth = min(growth_rate, 0.05) if growth_rate > 0 else 0.02
        if dividend_rate and dividend_rate > 0:
            alt_value = ddm_valuation(dividend_rate, div_growth, discount_rate=wacc)
            alt_model_name = 'Div. Discount (DDM)'
        # DCF as secondary
        dcf_value = dcf_valuation(
            fcf_current=fcf_for_dcf, growth_rate=growth_rate,
            shares=shares, total_debt=current_debt, cash=current_cash, wacc=wacc
        )
        valuation_models_used = ['DDM'] if alt_value > 0 else []
        valuation_models_used.append('DCF')

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
    # Use only the models that produced valid (> 0) results
    valid_values = [v for v in [graham_value, dcf_value, alt_value] if v and v > 0]
    if valid_values:
        # Conservative: take the lower of the valid values
        best_intrinsic = min(valid_values)
    else:
        best_intrinsic = 0

    # ─── Margin of Safety (using trading currency) ───────────
    mos = margin_of_safety(best_intrinsic, current_price)
    ms_abs = mos

    # ─── PER & EV/FCF (Actuals) ──────────────────────────────
    per_actual = data.get('per_trailing')
    ev_fcf = None
    ev = data.get('enterprise_value', 0)
    if ev and fcf_for_dcf and fcf_for_dcf > 0:
        ev_fcf = ev / fcf_for_dcf

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

    if non_gaap_flag == '🚫 No Elegible':
        estado_semaforo = '🚫 NO ELEGIBLE'
        alerta_compra = 0
    elif ms_abs > 15.0 and ms_rel > 10.0:
        estado_semaforo = '🟢 STRONG BUY'
        alerta_compra = 1
    elif ms_abs < 0.0 and ms_rel < 0.0:
        estado_semaforo = '🔴 SOBREVALORADA'
        alerta_compra = 0
    else:
        estado_semaforo = '🟡 MANTENER / SEGUIMIENTO'
        alerta_compra = 0

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
        dividend_yield_valid = False
        logger.warning(f"{ticker}: Dividend yield {dividend_yield:.2%} suspiciously high — marking as unreliable")

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
        'fcf_real_ttm': fcf_result.get('fcf_real_ttm'),
        'fcf_real_hist_avg': fcf_result.get('fcf_real_hist_avg'),
        'fcf_trend': fcf_result.get('fcf_trend'),

        # ROIC
        'roic_values': roic_result.get('roic_values', []),
        'roic_current': roic_result.get('roic_current'),
        'roic_hist_avg': roic_result.get('roic_hist_avg'),
        'roic_trend': roic_result.get('roic_trend'),

        # Valuation
        'per_actual': per_actual,
        'per_history': per_history,
        'per_forward': data.get('per_forward'),
        'ev_fcf_actual': ev_fcf,
        'ev_fcf_history': ev_fcf_history,
        'graham_value': graham_value,
        'dcf_value': dcf_value,
        'alt_value': alt_value if alt_value > 0 else None,
        'alt_model_name': alt_model_name,
        'intrinsic_value': best_intrinsic,
        'margen_seguridad': mos,
        'ms_absoluto': ms_abs,
        'ms_relativo': ms_rel,
        'analyst_target': data.get('target_price_mean'),
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

        # Dividend
        'dividend_yield': dividend_yield if dividend_yield_valid else None,
        'dividend_yield_raw': dividend_yield,  # Always available for debugging
        'dividend_yield_valid': dividend_yield_valid,
        'payout_ratio': payout_ratio,

        # Meta
        'fetched_at': data.get('fetched_at', ''),
        'error': None
    }

    return analysis


def generate_investment_thesis(analysis: dict) -> str:
    """
    Generate a brief investment thesis based on analysis results.
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

    parts = []

    # Archetype context
    parts.append(f"Clasificada como {archetype}.")

    # Quality
    if '⭐' in calidad:
        parts.append(f"Negocio de alta calidad con ventajas competitivas duraderas.")
    elif '✅' in calidad:
        parts.append(f"Negocio de calidad aceptable con fundamentos sólidos.")
    elif '⚠️' in (analysis.get('archetype_id') or ''):
        parts.append(f"Empresa sin beneficios — valoración altamente especulativa.")
    else:
        parts.append(f"Negocio que requiere análisis cualitativo adicional.")

    # ROIC
    if roic and roic > 20:
        parts.append(f"ROIC del {roic:.1f}% indica un moat económico fuerte.")
    elif roic and roic > 12:
        parts.append(f"ROIC del {roic:.1f}% sugiere ventajas competitivas moderadas.")

    # FCF
    if fcf_trend == '↑':
        parts.append("Flujo de caja libre creciente en los últimos años.")
    elif fcf_trend == '→':
        parts.append("Flujo de caja libre estable.")
    elif fcf_trend == '↓':
        parts.append("⚠️ Flujo de caja libre decreciente — investigar causas.")

    # Valuation
    if mos > 30:
        parts.append(f"Cotiza a {currency} {price:.2f} vs valor intrínseco {currency} {intrinsic:.2f} — Margen de seguridad amplio ({mos:.0f}%).")
        if '⭐' in calidad or '✅' in calidad:
            parts.append("⚠️ **Alerta Cualitativa:** Números excelentes pero con un castigo bursátil muy severo. Auditar si existe una disrupción permanente por parte de la competencia (pérdida de momentum, nuevos rivales) o si es un problema temporal.")
    elif mos > 20:
        parts.append(f"Margen de seguridad del {mos:.0f}% — dentro del rango aceptable para inversión valor.")
    elif mos > 0:
        parts.append(f"Margen de seguridad del {mos:.0f}% — insuficiente, esperar mejor precio.")
    else:
        parts.append(f"Cotiza por encima del valor intrínseco estimado — sobrevalorada.")

    # PER
    if per and per < 15:
        parts.append(f"PER de {per:.1f}x — valoración atractiva.")
    elif per and per > 30:
        parts.append(f"PER de {per:.1f}x — valoración exigente.")

    return " ".join(parts)
