"""
scanner.py — Opportunity Scanner ("NOVEDAD").
Scans a universe of stocks for undervalued, high-quality businesses.
Filters by quantitative value investing criteria.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from fetcher import fetch_company_data, get_market_tickers
from engine import run_full_analysis, generate_investment_thesis

logger = logging.getLogger(__name__)

# ─── Scanner Criteria ─────────────────────────────────────────────
DEFAULT_CRITERIA = {
    'max_per': 20,          # PER < 20
    'min_roic': 12,         # ROIC > 12%
    'min_fcf_yield': 5,     # FCF Yield > 5%
    'min_mos': 20,          # Margin of Safety > 20%
}


def scan_opportunities(criteria: dict = None, max_stocks: int = 20, market: str = 'sp500') -> list:
    """
    Scan the stock universe for value investing opportunities.

    Process:
    1. Fetch data for each stock in the universe
    2. Run full analysis
    3. Filter by criteria
    4. Generate investment thesis
    5. Sort by margin of safety (highest first)

    Args:
        criteria: Dict of filter criteria (uses defaults if None)
        max_stocks: Maximum number of results to return

    Returns:
        List of opportunity dicts sorted by margin of safety
    """
    if criteria is None:
        criteria = DEFAULT_CRITERIA

    tickers = get_market_tickers(market)
    opportunities = []
    errors = []

    def analyze_stock(ticker):
        try:
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

    # Parallel fetch & analyze
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(analyze_stock, t): t for t in tickers}
        for future in as_completed(futures):
            ticker = futures[future]
            try:
                analysis = future.result()
                if analysis is None:
                    continue

                # ─── Apply Filters ────────────────────────────
                per = analysis.get('per_actual')
                roic = analysis.get('roic_current')
                mos = analysis.get('margen_seguridad', 0)
                fcf_ttm = analysis.get('fcf_real_ttm', 0)
                market_cap = analysis.get('market_cap', 0)
                non_gaap = analysis.get('non_gaap_flag', '')

                # Reject Non-GAAP abusers
                if '🚫' in non_gaap:
                    continue

                # PER filter
                if per is not None and per > criteria.get('max_per', 20):
                    continue

                # ROIC filter
                if roic is None or roic < criteria.get('min_roic', 12):
                    continue

                # Margin of Safety filter
                if mos < criteria.get('min_mos', 20):
                    continue

                # FCF Yield filter
                fcf_yield = 0
                if fcf_ttm and market_cap and market_cap > 0:
                    fcf_yield = (fcf_ttm / market_cap) * 100
                if fcf_yield < criteria.get('min_fcf_yield', 5):
                    continue

                # ─── Generate thesis ─────────────────────────
                thesis = generate_investment_thesis(analysis)

                opportunities.append({
                    'ticker': analysis.get('ticker'),
                    'empresa': analysis.get('empresa'),
                    'sector': analysis.get('sector'),
                    'current_price': analysis.get('current_price'),
                    'intrinsic_value': analysis.get('intrinsic_value'),
                    'margen_seguridad': mos,
                    'roic_current': roic,
                    'per_actual': per,
                    'fcf_yield': fcf_yield,
                    'calidad': analysis.get('calidad'),
                    'fcf_trend': analysis.get('fcf_trend'),
                    'eps_trend': analysis.get('eps_trend'),
                    'thesis': thesis,
                    'non_gaap_flag': non_gaap,
                })

            except Exception as e:
                logger.warning(f"Error processing {ticker}: {e}")

    # Sort by margin of safety (highest first)
    opportunities.sort(key=lambda x: x.get('margen_seguridad', 0), reverse=True)

    return opportunities[:max_stocks]


def scan_quick(tickers_list: list = None) -> list:
    """
    Quick scan of specific tickers (for smaller, targeted scans).
    Returns all results without strict filtering.
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

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(analyze, t): t for t in tickers_list}
        for future in as_completed(futures):
            result = future.result()
            if result and not result.get('error'):
                result['thesis'] = generate_investment_thesis(result)
                results.append(result)

    results.sort(key=lambda x: x.get('margen_seguridad', 0), reverse=True)
    return results
