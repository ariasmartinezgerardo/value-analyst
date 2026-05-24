"""
engine.py — Financial Analysis Engine for Value Investing.
Implements FCF Real, ROIC, Graham & DCF valuations, Margin of Safety,
and Non-GAAP detection. All calculations follow strict GAAP-only rules.
"""

import numpy as np
import logging

logger = logging.getLogger(__name__)

# ─── Configuration ────────────────────────────────────────────────
DEFAULT_WACC = 0.10            # 10% discount rate
TERMINAL_GROWTH = 0.025        # 2.5% perpetual growth
GRAHAM_BASE_PE = 8.5           # Graham zero-growth P/E
GRAHAM_GROWTH_MULT = 2.0       # Graham growth multiplier
GRAHAM_BOND_YIELD_1962 = 4.4   # AAA bond yield in 1962
CURRENT_AAA_BOND_YIELD = 4.5   # Current AAA bond yield (approximate)
MIN_MARGIN_OF_SAFETY = 0.20    # 20% minimum for recommendation
NON_GAAP_WARN_THRESHOLD = 0.15  # 15% divergence warns
NON_GAAP_REJECT_THRESHOLD = 0.30  # 30% divergence rejects


def _avg(values, exclude_none=True):
    """Calculate average of a list, ignoring None values."""
    if exclude_none:
        values = [v for v in values if v is not None and v != 0]
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

        fcf = e - c - abs(intr or 0) - abs(tax or 0) - (wc or 0)
        fcf_real_values.append(fcf)

    # TTM calculation
    ebitda_ttm = data.get('ebitda_ttm')
    fcf_ttm = None
    if ebitda_ttm and capex:
        capex_latest = capex[0] if capex else 0
        interest_latest = interest[0] if interest else 0
        tax_latest = taxes[0] if taxes else 0
        wc_latest = wc_changes[0] if wc_changes else 0
        fcf_ttm = ebitda_ttm - capex_latest - abs(interest_latest or 0) - abs(tax_latest or 0) - (wc_latest or 0)

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
                  wacc: float = DEFAULT_WACC, years: int = 10) -> float:
    """
    Simplified DCF Valuation:
    1. Project FCF for N years at estimated growth rate
    2. Calculate terminal value using perpetuity growth
    3. Discount all to present value
    4. Divide by shares outstanding

    Args:
        fcf_current: Current annual FCF (total, not per share)
        growth_rate: Annual FCF growth rate (decimal, e.g. 0.10)
        shares: Shares outstanding
        wacc: Weighted Average Cost of Capital (decimal)
        years: Projection period
    Returns:
        Intrinsic value per share
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

    # Enterprise value
    enterprise_value = sum(projected_fcfs) + discounted_terminal

    # Per-share value
    intrinsic_value = enterprise_value / shares
    return max(intrinsic_value, 0)


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


def generate_qualitative_audit(data: dict, analysis: dict) -> dict:
    """
    Generate an intelligent Qualitative Audit Report based on real financial
    parameters, corporate governance risk scores, business summaries, and 
    automated TAM/SAM/SOM market size growth room calculations.
    """
    sector = data.get('sector', '').lower()
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

    # 4. TAM/SAM/SOM & Growth (Mercado y Crecimiento)
    # Global TAM values per major sectors in USD
    SECTOR_TAM_USD = {
        'technology': 5.5e12,          # $5.5 Trillion
        'healthcare': 12.0e12,         # $12.0 Trillion
        'financial services': 22.0e12,  # $22.0 Trillion
        'financial': 22.0e12,
        'consumer cyclical': 15.0e12,  # $15.0 Trillion
        'consumer defensive': 9.0e12,  # $9.0 Trillion
        'industrials': 8.0e12,         # $8.0 Trillion
        'industrial': 8.0e12,
        'communication services': 2.5e12, # $2.5 Trillion
        'communication': 2.5e12,
        'energy': 6.0e12,              # $6.0 Trillion
        'basic materials': 7.0e12,     # $7.0 Trillion
        'utilities': 3.5e12,           # $3.5 Trillion
        'real estate': 4.0e12          # $4.0 Trillion
    }

    rev_vals = data.get('revenue_values', [])
    latest_rev = rev_vals[0] if rev_vals else 0
    multiplier = analysis.get('multiplier', 1.0)
    
    latest_rev_usd = latest_rev / multiplier if latest_rev and multiplier else latest_rev
    
    sector_key = sector.strip()
    tam_val = 5.0e12  # default fallback $5T
    for key, val in SECTOR_TAM_USD.items():
        if key in sector_key:
            tam_val = val
            break
            
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
    Returns a comprehensive analysis result dict.
    """
    if data.get('error'):
        return data

    ticker = data.get('ticker', '?')
    current_price = data.get('current_price', 0)
    shares = data.get('shares_outstanding', 0)

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

    # ─── Growth rate estimation ──────────────────────────────
    growth = data.get('growth_estimate')
    if growth and growth > 0:
        growth_rate = growth
    else:
        # Estimate from EPS history
        growth_rate = _growth_rate(eps_values) if eps_values else 0.05
    growth_rate_pct = growth_rate * 100  # For Graham formula

    # ─── Graham Valuation ────────────────────────────────────
    graham_value = graham_valuation(eps_ttm, growth_rate_pct)

    # ─── DCF Valuation ───────────────────────────────────────
    fcf_for_dcf = fcf_result.get('fcf_real_ttm') or (
        fcf_result['fcf_real_values'][0] if fcf_result.get('fcf_real_values') else None
    )
    # If FCF Real isn't available, fallback to Yahoo's FCF
    if not fcf_for_dcf or fcf_for_dcf <= 0:
        yahoo_fcf = data.get('fcf_yahoo_values', [])
        fcf_for_dcf = yahoo_fcf[0] if yahoo_fcf else 0

    dcf_value = dcf_valuation(
        fcf_current=fcf_for_dcf,
        growth_rate=growth_rate,
        shares=shares,
        wacc=DEFAULT_WACC
    )

    # ─── Best intrinsic value (conservative: take lower) ─────
    valid_values = [v for v in [graham_value, dcf_value] if v and v > 0]
    best_intrinsic = min(valid_values) if valid_values else 0

    # ─── Currency / ADR Unit Multiplier ──────────────────────
    # Aligns the stock trading price currency (e.g. USD) and ADR conversion factor
    # with the company's financial statement reporting currency (e.g. TWD, EUR).
    multiplier = 1.0
    market_cap = data.get('market_cap', 0) or 0
    ev = data.get('enterprise_value', 0) or 0
    debt = data.get('total_debt_values', [])
    cash = data.get('cash_values', [])
    debt_val_curr = debt[0] if debt else 0
    cash_val_curr = cash[0] if cash else 0

    if ev and market_cap > 0:
        reporting_market_cap = ev - (debt_val_curr or 0) + (cash_val_curr or 0)
        if reporting_market_cap > 0:
            multiplier = reporting_market_cap / market_cap

    # Convert intrinsic values to trading currency for USD/user comparison
    graham_value = graham_value / multiplier if graham_value else 0
    dcf_value = dcf_value / multiplier if dcf_value else 0
    best_intrinsic = best_intrinsic / multiplier if best_intrinsic else 0

    # ─── Margin of Safety (using trading currency) ───────────
    mos = margin_of_safety(best_intrinsic, current_price)
    ms_abs = mos  # MS_Abs is mathematically the Absolute Margin of Safety

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
            
        # EV = Price * Shares + Debt - Cash (all in reporting currency)
        fcf_val = fcf_result.get('fcf_real_values')[i] if fcf_result.get('fcf_real_values') and i < len(fcf_result['fcf_real_values']) else None
        eq_val = equity[i] if i < len(equity) else 0
        debt_val = debt[i] if i < len(debt) else 0
        cash_val = cash[i] if i < len(cash) else 0
        
        if price_reporting and shares and shares > 0 and fcf_val and fcf_val > 0:
            ev_hist = (price_reporting * shares) + (debt_val or 0) - (cash_val or 0)
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

    # ─── Qualitative Audit ───────────────────────────────────
    qualitative_audit = generate_qualitative_audit(data, {
        'roic_hist_avg': roic_result.get('roic_hist_avg'),
        'fcf_trend': fcf_result.get('fcf_trend'),
        'non_gaap_flag': non_gaap_flag,
        'multiplier': multiplier
    })

    # ─── Decision Criterion: Compra de Calidad (Caso Ferrari) ─
    if estado_semaforo == '🟡 MANTENER / SEGUIMIENTO':
        if ms_abs > 0.0 and ms_rel > 0.0 and roic_result.get('roic_hist_avg', 0) > 18.0:
            has_buybacks = False
            shares_hist = data.get('shares_history', [])
            if len(shares_hist) >= 2 and shares_hist[0] and shares_hist[-1] and shares_hist[0] < shares_hist[-1]:
                has_buybacks = True
            insider_pct = data.get('held_percent_insiders', 0) or 0
            
            if has_buybacks or (insider_pct * 100 > 0.1):
                estado_semaforo = '🟢 COMPRA DE CALIDAD'
                alerta_compra = 1

    # ─── Build result ────────────────────────────────────────
    analysis = {
        'ticker': ticker,
        'empresa': data.get('empresa', ''),
        'sector': data.get('sector', ''),
        'industry': data.get('industry', ''),
        'currency': data.get('currency', 'USD'),
        'current_price': current_price,
        'market_cap': data.get('market_cap', 0),
        'shares_outstanding': shares,
        'fiscal_dates': data.get('fiscal_dates', []),
        'historical_prices': hist_prices,

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
        'intrinsic_value': best_intrinsic,
        'margen_seguridad': mos,
        'ms_absoluto': ms_abs,
        'ms_relativo': ms_rel,
        'estado_semaforo': estado_semaforo,
        'alerta_compra': alerta_compra,
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
        'dividend_yield': data.get('dividend_yield', 0),
        'payout_ratio': data.get('payout_ratio', 0),

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

    parts = []

    # Quality
    if '⭐' in calidad:
        parts.append(f"Negocio de alta calidad con ventajas competitivas duraderas.")
    elif '✅' in calidad:
        parts.append(f"Negocio de calidad aceptable con fundamentos sólidos.")
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
        parts.append(f"Cotiza a ${price:.2f} vs valor intrínseco ${intrinsic:.2f} — Margen de seguridad amplio ({mos:.0f}%).")
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
