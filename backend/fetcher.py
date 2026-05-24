"""
fetcher.py — Financial data fetching module via Financial Modeling Prep (FMP).
Downloads income statements, balance sheets, cash flows, and market data.
Provides clean, structured data for the analysis engine.
"""

import os
import requests
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

API_KEY = "YbtdwIo6Ih89vcUO9Cq0TeAY4KlHRvOo"
BASE_URL = "https://financialmodelingprep.com/api/v3"

def _safe_float(val, default=None):
    if val is None: return default
    try: return float(val)
    except: return default

def fetch_company_data(ticker_symbol: str) -> dict:
    ticker = ticker_symbol.upper().strip()
    try:
        # 1. Profile (Company Name, Sector, Industry, Price, Market Cap)
        prof_resp = requests.get(f"{BASE_URL}/profile/{ticker}?apikey={API_KEY}", timeout=10)
        prof_data = prof_resp.json()
        if not prof_data or not isinstance(prof_data, list):
            return {'error': f'Ticker "{ticker}" not found or no data available.'}
        profile = prof_data[0]
        
        # 2. Quote (Shares Outstanding, EPS, PE)
        quote_resp = requests.get(f"{BASE_URL}/quote/{ticker}?apikey={API_KEY}", timeout=10)
        quote_data = quote_resp.json()
        quote = quote_data[0] if quote_data else {}
        
        # 3. Key Metrics TTM (Enterprise Value, Dividend Yield, Payout Ratio)
        km_resp = requests.get(f"{BASE_URL}/key-metrics-ttm/{ticker}?apikey={API_KEY}", timeout=10)
        km_data = km_resp.json()
        km = km_data[0] if km_data else {}
        
        # 4. Income Statement (EPS history, EBITDA, Revenue, Net Income, etc.)
        inc_resp = requests.get(f"{BASE_URL}/income-statement/{ticker}?period=annual&limit=5&apikey={API_KEY}", timeout=10)
        inc_data = inc_resp.json() if inc_resp.status_code == 200 else []
        
        # 5. Balance Sheet (Equity, Debt, Cash)
        bal_resp = requests.get(f"{BASE_URL}/balance-sheet-statement/{ticker}?period=annual&limit=5&apikey={API_KEY}", timeout=10)
        bal_data = bal_resp.json() if bal_resp.status_code == 200 else []
        
        # 6. Cash Flow Statement (CAPEX, Free Cash Flow, D&A)
        cf_resp = requests.get(f"{BASE_URL}/cash-flow-statement/{ticker}?period=annual&limit=5&apikey={API_KEY}", timeout=10)
        cf_data = cf_resp.json() if cf_resp.status_code == 200 else []
        
        # --- Extract Basic Info ---
        company_name = profile.get('companyName', ticker)
        sector = profile.get('sector', 'N/A')
        industry = profile.get('industry', 'N/A')
        currency = profile.get('currency', 'USD')
        current_price = _safe_float(profile.get('price')) or _safe_float(quote.get('price'), 0)
        market_cap = _safe_float(profile.get('mktCap', 0))
        shares_outstanding = _safe_float(quote.get('sharesOutstanding', 0))
        enterprise_value = _safe_float(km.get('enterpriseValueTTM', 0))
        
        # --- Extract Dates ---
        # FMP returns data with the newest date first
        fiscal_dates = [item.get('date', '')[:10] for item in inc_data]
        
        # --- Extract Arrays (Most recent first) ---
        eps_values = [_safe_float(item.get('eps')) for item in inc_data]
        ebitda_values = [_safe_float(item.get('ebitda')) for item in inc_data]
        interest_values = [abs(_safe_float(item.get('interestExpense'), 0)) for item in inc_data]
        tax_values = [abs(_safe_float(item.get('incomeTaxExpense'), 0)) for item in inc_data]
        ebit_values = [_safe_float(item.get('operatingIncome')) for item in inc_data]
        pretax_values = [_safe_float(item.get('incomeBeforeTax')) for item in inc_data]
        revenue_values = [_safe_float(item.get('revenue')) for item in inc_data]
        net_income_values = [_safe_float(item.get('netIncome')) for item in inc_data]
        
        equity_values = [_safe_float(item.get('totalEquity')) for item in bal_data]
        total_debt_values = [_safe_float(item.get('totalDebt')) for item in bal_data]
        cash_values = [_safe_float(item.get('cashAndCashEquivalents')) for item in bal_data]
        shares_history = [_safe_float(item.get('commonStock')) for item in bal_data]
        
        capex_values = [abs(_safe_float(item.get('capitalExpenditure'), 0)) for item in cf_data]
        wc_values = [_safe_float(item.get('changeInWorkingCapital')) for item in cf_data]
        da_values = [abs(_safe_float(item.get('depreciationAndAmortization'), 0)) for item in cf_data]
        fcf_values = [_safe_float(item.get('freeCashFlow')) for item in cf_data]
        
        # --- TTM and Ratios ---
        eps_ttm = _safe_float(quote.get('eps'))
        ebitda_ttm = ebitda_values[0] if ebitda_values else None
        
        per_trailing = _safe_float(km.get('peRatioTTM')) or _safe_float(quote.get('pe'))
        per_forward = None  # Free tier limitation
        
        div_yield_pct = _safe_float(km.get('dividendYieldPercentageTTM'), 0)
        dividend_yield = div_yield_pct / 100.0 if div_yield_pct else 0
        payout_ratio = _safe_float(km.get('payoutRatioTTM'), 0)
        
        # --- 7. Historical Prices (for 5-year multiples) ---
        historical_prices = []
        try:
            if fiscal_dates:
                hist_resp = requests.get(f"{BASE_URL}/historical-price-full/{ticker}?timeseries=1260&apikey={API_KEY}", timeout=10)
                hist_data = hist_resp.json().get('historical', [])
                # Create dictionary of Date -> Close Price
                hist_dict = {item['date']: item['close'] for item in hist_data}
                
                # For each fiscal date, find the exact or closest previous trading day price
                for f_date in fiscal_dates:
                    found = False
                    for offset in range(10): # search up to 10 days backwards to account for weekends/holidays
                        target = (datetime.strptime(f_date, "%Y-%m-%d") - timedelta(days=offset)).strftime("%Y-%m-%d") if offset > 0 else f_date
                        if target in hist_dict:
                            historical_prices.append(hist_dict[target])
                            found = True
                            break
                    if not found:
                        historical_prices.append(None)
        except Exception as e:
            logger.warning(f"Error fetching historical prices for {ticker}: {e}")
            historical_prices = [None] * len(fiscal_dates)
            
        return {
            'ticker': ticker,
            'empresa': company_name,
            'sector': sector,
            'industry': industry,
            'currency': currency,
            'market_cap': market_cap,
            'shares_outstanding': shares_outstanding,
            'current_price': current_price,
            'enterprise_value': enterprise_value,
            'fiscal_dates': fiscal_dates,
            'historical_prices': historical_prices,
            'eps_values': eps_values,
            'eps_ttm': eps_ttm,
            'ebitda_values': ebitda_values,
            'ebitda_ttm': ebitda_ttm,
            'capex_values': capex_values,
            'interest_values': interest_values,
            'tax_values': tax_values,
            'wc_values': wc_values,
            'da_values': da_values,
            'ebit_values': ebit_values,
            'pretax_values': pretax_values,
            'equity_values': equity_values,
            'total_debt_values': total_debt_values,
            'cash_values': cash_values,
            'fcf_yahoo_values': fcf_values, # Reuse key to maintain compatibility
            'revenue_values': revenue_values,
            'net_income_values': net_income_values,
            'per_trailing': per_trailing,
            'per_forward': per_forward,
            'growth_estimate': None,
            'analyst_target': None,
            'dividend_yield': dividend_yield,
            'payout_ratio': payout_ratio,
            'held_percent_insiders': None,
            'audit_risk': None,
            'board_risk': None,
            'compensation_risk': None,
            'business_summary': profile.get('description', ''),
            'shares_history': shares_history,
            'fetched_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'error': None
        }

    except Exception as e:
        logger.exception(f"Error fetching data for {ticker}")
        return {
            'ticker': ticker,
            'error': str(e)
        }

def fetch_quick_info(ticker_symbol: str) -> dict:
    """Fetch minimal info for portfolio cards (fast)."""
    ticker = ticker_symbol.upper().strip()
    try:
        prof_resp = requests.get(f"{BASE_URL}/profile/{ticker}?apikey={API_KEY}", timeout=10)
        prof_data = prof_resp.json()
        if not prof_data or not isinstance(prof_data, list):
            return {'ticker': ticker, 'error': 'Not found'}
            
        quote_resp = requests.get(f"{BASE_URL}/quote/{ticker}?apikey={API_KEY}", timeout=10)
        quote_data = quote_resp.json()
        
        profile = prof_data[0]
        quote = quote_data[0] if quote_data else {}
        
        return {
            'ticker': ticker,
            'empresa': profile.get('companyName', ticker),
            'current_price': _safe_float(profile.get('price')) or _safe_float(quote.get('price'), 0),
            'sector': profile.get('sector', 'N/A'),
            'market_cap': _safe_float(profile.get('mktCap', 0)),
            'per_trailing': _safe_float(quote.get('pe')),
            'error': None
        }
    except Exception as e:
        return {'ticker': ticker, 'error': str(e)}

def get_sp500_tickers() -> list:
    """Return a curated list of well-known S&P 500 tickers for the scanner."""
    return [
        'AAPL', 'MSFT', 'GOOG', 'AMZN', 'META', 'BRK-B', 'JNJ', 'V', 'PG', 'UNH',
        'HD', 'MA', 'DIS', 'NVDA', 'PYPL', 'ADBE', 'NFLX', 'CMCSA', 'PFE', 'KO',
        'PEP', 'TMO', 'COST', 'AVGO', 'CSCO', 'ABT', 'ACN', 'MRK', 'NKE', 'WMT',
        'T', 'CVX', 'XOM', 'LLY', 'MCD', 'DHR', 'MDT', 'HON', 'AMGN', 'TXN',
        'UNP', 'LIN', 'BMY', 'PM', 'LOW', 'RTX', 'SBUX', 'INTC', 'ORCL', 'IBM'
    ]
