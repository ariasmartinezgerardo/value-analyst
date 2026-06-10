"""
scanner.py — Opportunity Scanner ("NOVEDAD").
Scans a universe of stocks for undervalued, high-quality businesses.

v2: Uses composite SCORING instead of hard AND filters.
     Every company gets a score (0-105) across 7 dimensions,
     then results are ranked. No more "0 results" on bull markets.
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from fetcher import fetch_company_data, get_market_tickers
from engine import run_full_analysis, generate_investment_thesis

logger = logging.getLogger(__name__)

# P0 FIX: Max tickers to scan per request to prevent HTTP timeouts.
MAX_SCAN_TICKERS = 30

# P0 FIX: Delay between Yahoo Finance requests to prevent rate limiting.
SCAN_DELAY_SECONDS = 1.5


# ─── Scoring System ──────────────────────────────────────────────
# Max score: 105 points across 7 dimensions.

MAX_SCORE = 105


def score_opportunity(analysis: dict) -> dict:
    """
    Score a company on multiple value investing dimensions.

    Instead of binary pass/fail filters, this assigns points
    across 7 categories. A Visa (PER=30, ROIC=35%) now scores
    high instead of being rejected for "PER > 20".

    Dimensions:
      1. Semáforo (engine's holistic verdict):  30 pts max
      2. Quality / Piotroski F-Score:           20 pts max
      3. Margin of Safety:                      20 pts max
      4. ROIC / Economic Moat:                  15 pts max
      5. FCF Trend:                             10 pts max
      6. Accounting Transparency:                5 pts max
      7. Data Reliability:                       5 pts max

    Returns:
        Dict with 'score', 'max_score', 'grade', 'breakdown'.
    """
    breakdown = {}

    # 1. Traffic Light — the engine's holistic verdict (30 pts)
    semaforo = analysis.get('estado_semaforo', '')
    if '🟢' in semaforo:
        breakdown['semaforo'] = 30
    elif '🟡' in semaforo:
        breakdown['semaforo'] = 15
    else:
        breakdown['semaforo'] = 0

    # 2. Quality / Piotroski F-Score (20 pts)
    calidad = analysis.get('calidad', '')
    if '⭐' in calidad or 'Alta' in calidad:
        breakdown['calidad'] = 20
    elif '✅' in calidad or 'Aceptable' in calidad:
        breakdown['calidad'] = 12
    elif '⚠' in calidad or 'Media' in calidad:
        breakdown['calidad'] = 5
    else:
        breakdown['calidad'] = 0

    # 3. Margin of Safety — continuous, not binary (20 pts)
    mos = analysis.get('margen_seguridad', 0) or 0
    if mos >= 30:
        breakdown['mos'] = 20
    elif mos >= 15:
        breakdown['mos'] = 15
    elif mos >= 0:
        breakdown['mos'] = 8
    else:
        breakdown['mos'] = 0

    # 4. ROIC — measures economic moat strength (15 pts)
    roic = analysis.get('roic_current') or 0
    if roic >= 20:
        breakdown['roic'] = 15
    elif roic >= 15:
        breakdown['roic'] = 12
    elif roic >= 10:
        breakdown['roic'] = 8
    elif roic >= 5:
        breakdown['roic'] = 4
    else:
        breakdown['roic'] = 0

    # 5. FCF Trend — improving cash generation (10 pts)
    # Engine's _trend() returns: '↑', '→', '↓', or '?'
    fcf_trend = str(analysis.get('fcf_trend', ''))
    if '↑' in fcf_trend:
        breakdown['fcf_trend'] = 10
    elif '→' in fcf_trend:
        breakdown['fcf_trend'] = 5
    else:
        breakdown['fcf_trend'] = 0

    # 6. Accounting transparency — GAAP compliance (5 pts)
    non_gaap = analysis.get('non_gaap_flag', '')
    if '✅' in non_gaap:
        breakdown['transparencia'] = 5
    elif '⚠' in non_gaap:
        breakdown['transparencia'] = 2
    else:
        breakdown['transparencia'] = 0

    # 7. Data reliability — fewer warnings = more trustworthy (5 pts)
    warnings_count = len(analysis.get('data_quality_warnings', []))
    if warnings_count == 0:
        breakdown['fiabilidad'] = 5
    elif warnings_count <= 2:
        breakdown['fiabilidad'] = 2
    else:
        breakdown['fiabilidad'] = 0

    total = sum(breakdown.values())

    # Letter grade
    if total >= 80:
        grade = 'A'
    elif total >= 65:
        grade = 'B'
    elif total >= 50:
        grade = 'C'
    elif total >= 35:
        grade = 'D'
    else:
        grade = 'F'

    return {
        'score': total,
        'max_score': MAX_SCORE,
        'grade': grade,
        'breakdown': breakdown,
    }


# ─── Main Scanner ────────────────────────────────────────────────

def scan_opportunities(market: str = 'sp500',
                       archetype_filter: str = None,
                       sector_filter: str = None,
                       min_score: int = 0,
                       max_stocks: int = 30,
                       sort_by: str = 'score') -> dict:
    """
    Scan the stock universe for value investing opportunities
    using composite scoring.

    Process:
    1. Fetch data for each stock in the universe
    2. Run full analysis (engine handles all the heavy lifting)
    3. Score each company on 7 dimensions (105 pts max)
    4. Optionally filter by archetype, sector, and minimum score
    5. Sort by chosen metric (default: composite score)

    Returns:
        Dict with 'opportunities', 'total_scanned', 'total_passed'.
    """
    all_tickers = get_market_tickers(market)

    # P0 FIX: Cap tickers to prevent HTTP timeouts.
    if len(all_tickers) > MAX_SCAN_TICKERS:
        logger.info(f"Scanner: Capping {len(all_tickers)} tickers to "
                     f"{MAX_SCAN_TICKERS} (timeout prevention)")
    tickers = all_tickers[:MAX_SCAN_TICKERS]

    total_scanned = len(tickers)
    opportunities = []

    def analyze_stock(ticker):
        try:
            time.sleep(SCAN_DELAY_SECONDS)
            data = fetch_company_data(ticker)
            if data.get('error'):
                return None
            analysis = run_full_analysis(data)
            if analysis.get('error'):
                return None
            return analysis
        except Exception as e:
            logger.warning(f"Scanner error for {ticker}: {e}")
            return None

    # Parallel fetch & analyze (2 workers to be gentle on Yahoo)
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {executor.submit(analyze_stock, t): t for t in tickers}
        for future in as_completed(futures):
            ticker = futures[future]
            try:
                analysis = future.result()
                if analysis is None:
                    continue

                # ─── Hard Rejection: only for genuinely bad data ──────
                non_gaap = analysis.get('non_gaap_flag', '')
                if '🚫' in non_gaap:
                    continue

                # ─── Optional Pre-filters (archetype / sector) ────────
                arch = analysis.get('archetype_id', '')
                sect = analysis.get('sector', '')

                if archetype_filter and archetype_filter != 'all':
                    if arch != archetype_filter:
                        continue

                if sector_filter and sector_filter != 'all':
                    if sector_filter.lower() not in sect.lower():
                        continue

                # ─── Score the opportunity ─────────────────────────────
                scoring = score_opportunity(analysis)

                if scoring['score'] < min_score:
                    continue

                # ─── Compute FCF Yield for display ────────────────────
                fcf_yield = 0
                if (analysis.get('ev_fcf_actual') and
                        analysis['ev_fcf_actual'] > 0):
                    fcf_yield = (1.0 / analysis['ev_fcf_actual']) * 100
                else:
                    fcf_ttm = analysis.get('fcf_real_ttm', 0)
                    market_cap = analysis.get('market_cap', 0)
                    if fcf_ttm and market_cap and market_cap > 0:
                        fcf_yield = (fcf_ttm / market_cap) * 100

                # ─── Generate thesis ──────────────────────────────────
                thesis = generate_investment_thesis(analysis)

                opportunities.append({
                    'ticker': analysis.get('ticker'),
                    'empresa': analysis.get('empresa'),
                    'sector': analysis.get('sector'),
                    'archetype_id': arch,
                    'archetype_label': analysis.get('archetype_label', ''),
                    'current_price': analysis.get('current_price'),
                    'intrinsic_value': analysis.get('intrinsic_value'),
                    'margen_seguridad': analysis.get('margen_seguridad', 0),
                    'roic_current': analysis.get('roic_current'),
                    'per_actual': analysis.get('per_actual'),
                    'fcf_yield': round(fcf_yield, 2),
                    'calidad': analysis.get('calidad'),
                    'fcf_trend': analysis.get('fcf_trend'),
                    'eps_trend': analysis.get('eps_trend'),
                    'thesis': thesis,
                    'non_gaap_flag': non_gaap,
                    # ── Scoring ──
                    'score': scoring['score'],
                    'max_score': scoring['max_score'],
                    'grade': scoring['grade'],
                    'score_breakdown': scoring['breakdown'],
                    # ── Extra transparency ──
                    'growth_source': analysis.get('growth_source', ''),
                })

            except Exception as e:
                logger.warning(f"Error processing {ticker}: {e}")

    # Sort by chosen metric
    sort_keys = {
        'score': lambda x: x.get('score', 0),
        'mos': lambda x: x.get('margen_seguridad', 0),
        'roic': lambda x: x.get('roic_current', 0) or 0,
        'fcf_yield': lambda x: x.get('fcf_yield', 0),
        'per': lambda x: -(x.get('per_actual', 999) or 999),
    }
    sort_fn = sort_keys.get(sort_by, sort_keys['score'])
    opportunities.sort(key=sort_fn, reverse=True)

    return {
        'opportunities': opportunities[:max_stocks],
        'total_scanned': total_scanned,
        'total_passed': len(opportunities),
    }


# ─── Quick Scan (targeted) ───────────────────────────────────────

def scan_quick(tickers_list: list = None) -> list:
    """
    Quick scan of specific tickers (for smaller, targeted scans).
    Returns all results with scoring, without strict filtering.
    """
    if tickers_list is None:
        tickers_list = get_market_tickers('sp500')[:10]

    results = []

    def analyze(ticker):
        try:
            data = fetch_company_data(ticker)
            if data.get('error'):
                return None
            return run_full_analysis(data)
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {executor.submit(analyze, t): t for t in tickers_list}
        for future in as_completed(futures):
            result = future.result()
            if result and not result.get('error'):
                result['thesis'] = generate_investment_thesis(result)
                scoring = score_opportunity(result)
                result['score'] = scoring['score']
                result['grade'] = scoring['grade']
                result['score_breakdown'] = scoring['breakdown']
                results.append(result)

    results.sort(key=lambda x: x.get('score', 0), reverse=True)
    return results
