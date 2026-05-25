"""
fetcher.py — Financial data fetching module via yfinance.
Downloads income statements, balance sheets, cash flows, and market data.
Provides clean, structured data for the analysis engine.
"""

import os
# Force direct internet connection (bypass PythonAnywhere free proxy)
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)

import requests
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import logging
import requests
import time

logger = logging.getLogger(__name__)

# Simple in-memory cache to prevent yfinance IP bans
_FETCH_CACHE = {}
_QUICK_CACHE = {}
CACHE_TTL = 3600  # 1 hour


def _safe_get(df, key, col_idx=0, default=None):
    """Safely extract a value from a DataFrame by row label and column index."""
    try:
        if key in df.index:
            val = df.loc[key].iloc[col_idx]
            if pd.isna(val):
                return default
            return float(val)
    except (IndexError, KeyError, TypeError):
        pass
    return default


def _safe_get_all(df, key, default=None):
    """Get all values for a row label across all columns."""
    try:
        if key in df.index:
            vals = df.loc[key].values.tolist()
            return [float(v) if not pd.isna(v) else default for v in vals]
    except (KeyError, TypeError):
        pass
    return []


def fetch_company_data(ticker_symbol: str) -> dict:
    """
    Fetch comprehensive financial data for a company.
    Returns a structured dict with all data needed for analysis.
    """
    ticker_clean = ticker_symbol.upper().strip()
    now = time.time()
    
    if ticker_clean in _FETCH_CACHE and (now - _FETCH_CACHE[ticker_clean]['time'] < CACHE_TTL):
        logger.info(f"Serving {ticker_clean} from local memory cache")
        return _FETCH_CACHE[ticker_clean]['data']

    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        })
        
        stock = yf.Ticker(ticker_clean)
        info = stock.info or {}

        # Guard: check if valid ticker
        if not info.get('shortName') and not info.get('longName'):
            return {'error': f'Ticker "{ticker_symbol}" not found or no data available.'}

        # ─── Financial Statements (Annual) ──────────────────────
        try:
            income_stmt = stock.income_stmt
            if income_stmt is None or income_stmt.empty:
                income_stmt = pd.DataFrame()
        except Exception:
            income_stmt = pd.DataFrame()

        try:
            balance_sheet = stock.balance_sheet
            if balance_sheet is None or balance_sheet.empty:
                balance_sheet = pd.DataFrame()
        except Exception:
            balance_sheet = pd.DataFrame()

        try:
            cash_flow = stock.cashflow
            if cash_flow is None or cash_flow.empty:
                cash_flow = pd.DataFrame()
        except Exception:
            cash_flow = pd.DataFrame()

        # ─── Quarterly Statements (for TTM) ─────────────────────
        try:
            q_income = stock.quarterly_income_stmt
            if q_income is None: q_income = pd.DataFrame()
        except Exception:
            q_income = pd.DataFrame()
        try:
            q_cash_flow = stock.quarterly_cashflow
            if q_cash_flow is None: q_cash_flow = pd.DataFrame()
        except Exception:
            q_cash_flow = pd.DataFrame()

        # ─── Basic Info ──────────────────────────────────────────
        company_name = info.get('longName') or info.get('shortName', ticker_symbol)
        sector = info.get('sector', 'N/A')
        industry = info.get('industry', 'N/A')
        currency = info.get('currency', 'USD')
        market_cap = info.get('marketCap', 0)
        shares_outstanding = info.get('sharesOutstanding', 0)
        current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
        enterprise_value = info.get('enterpriseValue', 0)

        # ─── EPS ─────────────────────────────────────────────────
        # Historical EPS from income statement
        eps_values = []
        eps_keys = ['Basic EPS', 'BasicEPS', 'Diluted EPS', 'DilutedEPS']
        for key in eps_keys:
            vals = _safe_get_all(income_stmt, key)
            if vals:
                eps_values = vals
                break

        eps_ttm = info.get('trailingEps', None)
        if eps_ttm is None and eps_values:
            eps_ttm = eps_values[0] if eps_values else None

        # ─── EBITDA ──────────────────────────────────────────────
        ebitda_values = _safe_get_all(income_stmt, 'EBITDA')
        if not ebitda_values:
            ebitda_values = _safe_get_all(income_stmt, 'Normalized EBITDA')
        if not ebitda_values:
            # Calculate: Operating Income + Depreciation & Amortization
            op_income = _safe_get_all(income_stmt, 'Operating Income')
            if not op_income:
                op_income = _safe_get_all(income_stmt, 'OperatingIncome')
            da_cf = _safe_get_all(cash_flow, 'Depreciation And Amortization')
            if not da_cf:
                da_cf = _safe_get_all(cash_flow, 'DepreciationAndAmortization')
            if not da_cf:
                da_cf = _safe_get_all(cash_flow, 'Depreciation Amortization Depletion')
            if op_income and da_cf:
                min_len = min(len(op_income), len(da_cf))
                ebitda_values = [
                    (op_income[i] or 0) + abs(da_cf[i] or 0)
                    for i in range(min_len)
                ]

        ebitda_ttm = info.get('ebitda', ebitda_values[0] if ebitda_values else None)

        # ─── CAPEX ───────────────────────────────────────────────
        capex_keys = ['Capital Expenditure', 'CapitalExpenditure', 'Purchase Of PPE']
        capex_values = []
        for key in capex_keys:
            capex_values = _safe_get_all(cash_flow, key)
            if capex_values:
                break
        # CAPEX is typically negative in cash flow statements
        capex_values = [abs(v) if v else 0 for v in capex_values]

        # ─── Interest Expense ────────────────────────────────────
        interest_keys = ['Interest Expense', 'InterestExpense', 'Interest Expense Non Operating']
        interest_values = []
        for key in interest_keys:
            interest_values = _safe_get_all(income_stmt, key)
            if interest_values:
                break
        interest_values = [abs(v) if v else 0 for v in interest_values]

        # ─── Tax Provision ───────────────────────────────────────
        tax_keys = ['Tax Provision', 'TaxProvision', 'IncomeTaxExpense']
        tax_values = []
        for key in tax_keys:
            tax_values = _safe_get_all(income_stmt, key)
            if tax_values:
                break
        tax_values = [abs(v) if v else 0 for v in tax_values]

        # ─── Working Capital Change ──────────────────────────────
        wc_keys = ['Change In Working Capital', 'ChangeInWorkingCapital',
                    'Changes In Account Receivables', 'ChangesInAccountReceivables']
        wc_values = []
        for key in wc_keys:
            wc_values = _safe_get_all(cash_flow, key)
            if wc_values:
                break

        # ─── Operating Income (for ROIC) ─────────────────────────
        ebit_keys = ['EBIT', 'Operating Income', 'OperatingIncome']
        ebit_values = []
        for key in ebit_keys:
            ebit_values = _safe_get_all(income_stmt, key)
            if ebit_values:
                break

        # ─── Pretax Income (for tax rate) ────────────────────────
        pretax_keys = ['Pretax Income', 'PretaxIncome']
        pretax_values = []
        for key in pretax_keys:
            pretax_values = _safe_get_all(income_stmt, key)
            if pretax_values:
                break

        # ─── Balance Sheet items (for ROIC) ──────────────────────
        equity_keys = ['Stockholders Equity', 'StockholdersEquity', 'Common Stock Equity', 'Total Equity Gross Minority Interest']
        equity_values = []
        for key in equity_keys:
            equity_values = _safe_get_all(balance_sheet, key)
            if equity_values:
                break

        total_debt_keys = ['Total Debt', 'TotalDebt']
        total_debt_values = []
        for key in total_debt_keys:
            total_debt_values = _safe_get_all(balance_sheet, key)
            if total_debt_values:
                break

        cash_keys = ['Cash And Cash Equivalents', 'CashAndCashEquivalents',
                     'Cash Cash Equivalents And Short Term Investments']
        cash_values = []
        for key in cash_keys:
            cash_values = _safe_get_all(balance_sheet, key)
            if cash_values:
                break

        # ─── FCF from Yahoo (for comparison / Non-GAAP check) ───
        fcf_yahoo_keys = ['Free Cash Flow', 'FreeCashFlow']
        fcf_yahoo_values = []
        for key in fcf_yahoo_keys:
            fcf_yahoo_values = _safe_get_all(cash_flow, key)
            if fcf_yahoo_values:
                break

        # ─── Revenue (for growth estimation) ─────────────────────
        revenue_keys = ['Total Revenue', 'TotalRevenue', 'Operating Revenue']
        revenue_values = []
        for key in revenue_keys:
            revenue_values = _safe_get_all(income_stmt, key)
            if revenue_values:
                break

        # ─── Depreciation & Amortization ─────────────────────────
        da_keys = ['Depreciation And Amortization', 'DepreciationAndAmortization', 'Depreciation Amortization Depletion', 'Reconciled Depreciation']
        da_values = []
        for key in da_keys:
            da_values = _safe_get_all(cash_flow, key)
            if da_values:
                break
        if not da_values:
            # Try from income statement
            da_values = _safe_get_all(income_stmt, 'Reconciled Depreciation')
        da_values = [abs(v) if v else 0 for v in da_values]

        # ─── Dates for historical columns ────────────────────────
        fiscal_dates = []
        if not income_stmt.empty:
            fiscal_dates = [str(col.date()) if hasattr(col, 'date') else str(col) for col in income_stmt.columns]

        # Fetch 5-year price history for historical multiples
        historical_prices = []
        try:
            hist = stock.history(period="5y")
            if not hist.empty and fiscal_dates:
                # Strip timezone to avoid comparison errors with timezone-naive fiscal_dates
                if hist.index.tz is not None:
                    hist.index = hist.index.tz_localize(None)
                for f_date in fiscal_dates:
                    try:
                        target_dt = pd.to_datetime(f_date)
                        # Find closest available trading day's closing price
                        idx = hist.index.get_indexer([target_dt], method='nearest')[0]
                        if idx != -1:
                            close_price = float(hist.iloc[idx]['Close'])
                            historical_prices.append(close_price)
                        else:
                            historical_prices.append(None)
                    except Exception:
                        historical_prices.append(None)
            else:
                historical_prices = [None] * len(fiscal_dates)
        except Exception as e:
            logger.warning(f"Error fetching historical prices for {ticker_symbol}: {e}")
            historical_prices = [None] * len(fiscal_dates)

        # ─── Net Income (for additional checks) ─────────────────
        net_income_keys = ['Net Income', 'NetIncome', 'Net Income Common Stockholders']
        net_income_values = []
        for key in net_income_keys:
            net_income_values = _safe_get_all(income_stmt, key)
            if net_income_values:
                break

        # ─── Analyst Growth Estimate ─────────────────────────────
        growth_estimate = info.get('earningsGrowth') or info.get('revenueGrowth')
        analyst_target = info.get('targetMeanPrice')

        # ─── Trailing PER ────────────────────────────────────────
        per_trailing = info.get('trailingPE')
        per_forward = info.get('forwardPE')

        # ─── Dividend Info ───────────────────────────────────────
        dividend_yield = info.get('dividendYield', 0)
        payout_ratio = info.get('payoutRatio', 0)

        # ─── Qualitative & Governance Info ──────────────────────
        held_percent_insiders = info.get('heldPercentInsiders')
        audit_risk = info.get('auditRisk')
        board_risk = info.get('boardRisk')
        compensation_risk = info.get('compensationRisk')
        business_summary = info.get('longBusinessSummary', '')

        # Historical shares outstanding to detect buybacks
        shares_history = []
        shares_keys = ['Ordinary Shares Number', 'Common Stock Shares Outstanding', 'Share Capital']
        for key in shares_keys:
            shares_history = _safe_get_all(balance_sheet, key)
            if shares_history:
                break

        # ─── Build result ────────────────────────────────────────
        result = {
            'ticker': ticker_symbol.upper().strip(),
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

            # Core metrics arrays (most recent first)
            'eps_values': eps_values,
            'eps_ttm': eps_ttm,
            'ebitda_values': ebitda_values,
            'ebitda_ttm': ebitda_ttm,
            'capex_values': capex_values,
            'interest_values': interest_values,
            'tax_values': tax_values,
            'wc_values': wc_values,
            'da_values': da_values,

            # ROIC components
            'ebit_values': ebit_values,
            'pretax_values': pretax_values,
            'equity_values': equity_values,
            'total_debt_values': total_debt_values,
            'cash_values': cash_values,

            # Additional
            'fcf_yahoo_values': fcf_yahoo_values,
            'revenue_values': revenue_values,
            'net_income_values': net_income_values,

            # Ratios & Estimates
            'per_trailing': per_trailing,
            'per_forward': per_forward,
            'growth_estimate': growth_estimate,
            'analyst_target': analyst_target,
            'dividend_yield': dividend_yield,
            'payout_ratio': payout_ratio,

            # Qualitative
            'held_percent_insiders': held_percent_insiders,
            'audit_risk': audit_risk,
            'board_risk': board_risk,
            'compensation_risk': compensation_risk,
            'business_summary': business_summary,
            'shares_history': shares_history,

            'fetched_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'error': None
        }

        _FETCH_CACHE[ticker_clean] = {'time': now, 'data': result}
        return result

    except Exception as e:
        logger.exception(f"Error fetching data for {ticker_symbol}")
        return {
            'ticker': ticker_symbol.upper().strip(),
            'error': str(e)
        }


def fetch_quick_info(ticker_symbol: str) -> dict:
    """Fetch minimal info for portfolio cards (fast)."""
    ticker_clean = ticker_symbol.upper().strip()
    now = time.time()
    
    if ticker_clean in _QUICK_CACHE and (now - _QUICK_CACHE[ticker_clean]['time'] < CACHE_TTL):
        return _QUICK_CACHE[ticker_clean]['data']
        
    try:
        stock = yf.Ticker(ticker_clean)
        info = stock.info or {}
        result = {
            'ticker': ticker_clean,
            'empresa': info.get('longName') or info.get('shortName', ticker_clean),
            'current_price': info.get('currentPrice') or info.get('regularMarketPrice', 0),
            'sector': info.get('sector', 'N/A'),
            'market_cap': info.get('marketCap', 0),
            'per_trailing': info.get('trailingPE'),
            'error': None
        }
        _QUICK_CACHE[ticker_clean] = {'time': now, 'data': result}
        return result
    except Exception as e:
        logger.exception(f"Error quick fetching {ticker_symbol}")
        return {'ticker': ticker_clean, 'error': str(e)}


def get_market_tickers(market: str = 'sp500') -> list:
    """Return a curated list of well-known tickers for the selected market."""
    markets = {
        'sp500': [
            'AAPL', 'MSFT', 'GOOG', 'AMZN', 'META', 'BRK-B', 'JNJ', 'V', 'PG', 'UNH',
            'HD', 'MA', 'DIS', 'NVDA', 'PYPL', 'ADBE', 'NFLX', 'CMCSA', 'PFE', 'KO',
            'PEP', 'TMO', 'COST', 'AVGO', 'CSCO', 'ABT', 'ACN', 'MRK', 'NKE', 'WMT',
            'T', 'CVX', 'XOM', 'LLY', 'MCD', 'DHR', 'MDT', 'HON', 'AMGN', 'TXN',
            'UNP', 'LIN', 'BMY', 'PM', 'LOW', 'RTX', 'SBUX', 'INTC', 'ORCL', 'IBM'
        ],
        'nasdaq': [
            'AAPL', 'MSFT', 'GOOG', 'AMZN', 'META', 'NVDA', 'AVGO', 'TSLA', 'ASML', 'COST',
            'PEP', 'CSCO', 'TMUS', 'ADBE', 'TXN', 'NFLX', 'AMD', 'INTU', 'QCOM', 'AMAT',
            'HON', 'AMGN', 'ISRG', 'SBUX', 'GILD', 'BKNG', 'MDLZ', 'ADI', 'LRCX', 'VRTX',
            'REGN', 'ADP', 'MU', 'PANW', 'SNPS', 'KLAC', 'CDNS', 'MELI', 'CSX', 'PYPL',
            'MAR', 'MNST', 'ORLY', 'NXPI', 'CTAS', 'PCAR', 'WDAY', 'CRWD', 'LULU', 'ROST'
        ],
        'stoxx600': [
            'NVO', 'MC.PA', 'ASML.AS', 'SAP.DE', 'RMS.PA', 'SIE.DE', 'OR.PA', 'TTE.PA', 'SAN.PA', 'SU.PA',
            'ALV.DE', 'AIR.PA', 'IBE.MC', 'ITX.MC', 'BNP.PA', 'DPW.DE', 'DTE.DE', 'MUV2.DE', 'ENGI.PA', 'SAN.MC',
            'VCI.PA', 'BMW.DE', 'MBG.DE', 'BAS.DE', 'BAYN.DE', 'VOW3.DE', 'CS.PA', 'BN.PA', 'DG.PA', 'LR.PA',
            'CABK.MC', 'REP.MC', 'BBVA.MC', 'TEF.MC', 'AENA.MC', 'FER.MC', 'AMS.MC', 'ANA.MC', 'ENG.MC', 'RED.MC',
            'UNA.AS', 'HEIA.AS', 'INGA.AS', 'AD.AS', 'PRX.AS', 'AKZA.AS', 'ASM.AS', 'BESI.AS', 'DSM.AS', 'KPN.AS'
        ],
        'dowjones': [
            'MMM', 'AXP', 'AMGN', 'AAPL', 'BA', 'CAT', 'CVX', 'CSCO', 'KO', 'DIS',
            'DOW', 'GS', 'HD', 'HON', 'IBM', 'INTC', 'JNJ', 'JPM', 'MCD', 'MRK',
            'MSFT', 'NKE', 'PG', 'CRM', 'TRV', 'UNH', 'VZ', 'V', 'WBA', 'WMT'
        ],
        'japan': [
            'TM', 'SONY', 'KEY', 'MUFG', 'NTTYY', 'SMFG', 'MITSF', 'HMC', 'TAK', 'CAJ',
            'SFTBY', 'FUJIY', 'PCRFY', 'DCSO', 'NSANY', 'MRAAY', 'KUBTY', 'NIPNY', 'MZHOF', 'RNMBY',
            'TDK', 'DNZOY', 'KAO', 'FJTSY', 'MCO', 'SHCAY', 'YAMCY', 'SNE', 'SMNNY', 'KMTUY',
            'FANUY', 'TKOMY', 'TYHOY', 'AONNY', 'SSUMY', 'KMBUY', 'ITOCY', 'MIELY', 'MTU', 'MFG'
        ],
        'pharma': [
            'JNJ', 'LLY', 'NVO', 'UNH', 'MRK', 'ABBV', 'TMO', 'AZN', 'NVS', 'DHR',
            'PFE', 'AMGN', 'ABT', 'ISRG', 'SYK', 'MDT', 'VRTX', 'REGN', 'BSX', 'ZTS',
            'GSK', 'GILD', 'BDX', 'CVS', 'CI', 'ELV', 'HUM', 'MCK', 'CNC', 'BIIB',
            'ILMN', 'IDXX', 'ALGN', 'DXCM', 'RMD', 'STE', 'WST', 'CRL', 'BIO', 'TECH'
        ],
        'finance': [
            'JPM', 'V', 'MA', 'BAC', 'WFC', 'MS', 'GS', 'SPGI', 'AXP', 'RY',
            'C', 'SCHW', 'BLK', 'CB', 'PGR', 'CME', 'MMC', 'TD', 'USB', 'PNC',
            'TFC', 'COF', 'BK', 'AON', 'ICE', 'MCO', 'AIG', 'PRU', 'MET', 'TRV',
            'ALL', 'DFS', 'SYF', 'FITB', 'MTB', 'HBAN', 'RF', 'CFG', 'KEY', 'CMA'
        ],
        'consumer': [
            'WMT', 'PG', 'KO', 'PEP', 'COST', 'LVMH.PA', 'HD', 'MCD', 'NKE', 'SBUX',
            'TGT', 'LOW', 'EL', 'CL', 'KMB', 'GIS', 'SYY', 'HSY', 'K', 'CAG',
            'DG', 'DLTR', 'ROST', 'TJX', 'ORLY', 'AZO', 'TSCO', 'YUM', 'DRI', 'CMG',
            'DPZ', 'M', 'JWN', 'GPS', 'KSS', 'VFC', 'UAA', 'RCL', 'CCL', 'HLT'
        ],
        'energy': [
            'XOM', 'CVX', 'SHEL', 'TTE', 'BP', 'COP', 'EOG', 'PXD', 'OXY', 'VLO',
            'MPC', 'PSX', 'HES', 'DVN', 'HAL', 'SLB', 'BKR', 'KMI', 'WMB', 'OKE',
            'NEE', 'DUK', 'SO', 'D', 'AEP', 'EXC', 'XEL', 'SRE', 'WEC', 'ES',
            'ED', 'PEG', 'EIX', 'AWK', 'CNP', 'CMS', 'LNT', 'ATO', 'NI', 'NRG'
        ],
        'defense': [
            'LMT', 'RTX', 'NOC', 'GD', 'BA', 'LHX', 'HII', 'TDG', 'TXT', 'LDOS',
            'BA.L', 'HO.PA', 'SAF.PA', 'RHO.PA', 'LDO.MI', 'MTX.DE', 'SU.PA', 'AM.PA',
            'HEI', 'WWD', 'BWXT', 'PLTR', 'OSK', 'AVAV', 'KTOS', 'HWM', 'SPR', 'RKLB'
        ]
    }
    return markets.get(market.lower(), markets['sp500'])
