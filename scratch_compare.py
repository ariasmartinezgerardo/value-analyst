import sys
import os
sys.path.append(os.path.abspath('backend'))

from fetcher import fetch_company_data
from engine import run_full_analysis

def compare(ticker):
    print(f"\n--- Analizando {ticker} ---")
    data = fetch_company_data(ticker)
    if data.get('error'):
        print(f"Error fetching {ticker}: {data['error']}")
        return
    
    print(f"Analyst Growth Estimate: {data.get('growth_estimate')}")
    print(f"Historical Revenue: {data.get('revenue_values')}")
    print(f"Historical FCF: {data.get('fcf_yahoo_values')}")
    print(f"Historical Net Income: {data.get('net_income_values')}")

    analysis = run_full_analysis(data)
    
    growth_metrics = analysis.get('growth_metrics', {})
    print(f"Growth Rate (used in DCF): {analysis.get('growth_rate')}")
    print(f"Revenue Growth: {analysis.get('rev_growth')}")
    print(f"PEG Trailing: {growth_metrics.get('peg_trailing')}")
    print(f"Rule of 40: {growth_metrics.get('rule_of_40')}")
    print(f"Archetype: {analysis.get('archetype')}")

if __name__ == '__main__':
    compare('MXL')
    compare('PLTR')
