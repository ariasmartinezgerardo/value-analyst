"""
AUDITORÍA COMPLETA DEL MOTOR DE ANÁLISIS
Testa invariantes de sanidad para cada ticker conocido.
Cualquier fallo = BUG real.
"""
import sys, os
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.path.append('backend')
import logging
logging.disable(logging.CRITICAL)  # Silenciar logs

from fetcher import fetch_company_data
from engine import run_full_analysis

PASS = "✅"
FAIL = "❌"
WARN = "⚠️"

results = []
bugs    = []
warns   = []

def check(ticker, label, condition, value_str="", is_warn=False):
    icon = PASS if condition else (WARN if is_warn else FAIL)
    entry = f"  {icon} [{ticker}] {label} {value_str}"
    results.append(entry)
    if not condition:
        if is_warn:
            warns.append(entry)
        else:
            bugs.append(entry)

# ─── Test cases: (ticker, expected_archetype, expected_method, expected_semaforo_contains, min_iv, max_iv) ───
TEST_CASES = [
    # Ticker,  archetype,         method,   semaforo_must_contain,   iv_min,  iv_max,  price_approx
    ('LULU',   'compounder',      'value',  'BUY',                    150,     400,     130),
    ('GOOG',   'compounder',      'value',  None,                     200,     600,     370),
    ('RACE',   'compounder',      'value',  None,                      80,     250,     345),
    ('NVDA',   'compounder',      'value',  None,                     100,     400,     210),
    ('META',   'compounder',      'value',  None,                     300,     700,     620),
    ('MRVL',   'hypergrowth',     'growth', None,                       0,    9999,     205),
    ('ACN',    'compounder',      'value',  None,                     100,     350,     190),
    ('TSM',    'compounder',      'value',  None,                     100,     400,     180),
    ('AAPL',   'compounder',      'value',  None,                      50,     400,     305),
    ('JNJ',    'compounder',      'value',  None,                      80,     300,     155),
    ('KO',     'classic_value',   'value',  None,                      30,     120,      70),
    ('V',      'compounder',      'value',  None,                     150,     600,     360),
]

print("=" * 70)
print("  AUDITORÍA COMPLETA — Value Analyst Engine")
print("=" * 70)

for (ticker, exp_arch, exp_method, exp_semaforo, iv_min, iv_max, price_approx) in TEST_CASES:
    print(f"\n── {ticker} ──────────────────────────────────────")
    try:
        raw = fetch_company_data(ticker)
        res = run_full_analysis(raw)

        arch    = res.get('archetype_id', '')
        method  = res.get('methodology', '')
        sem     = res.get('estado_semaforo', '') or ''
        iv      = res.get('intrinsic_value', 0) or 0
        price   = res.get('current_price', 0) or 0
        fcf_ttm = res.get('fcf_real_ttm', 0) or 0
        wacc    = res.get('wacc_used', 0) or 0
        growth  = res.get('growth_rate_pct', 0) or 0
        roic    = res.get('roic_current', 0) or 0
        mos_abs = res.get('ms_absoluto', 0) or 0
        mos_rel = res.get('ms_relativo', 0) or 0
        models  = res.get('valuation_models_used', [])
        gs      = res.get('growth_source', '')
        error   = res.get('error')

        # 1. No error
        check(ticker, "Sin error de fetch", error is None, f"(error={error})")

        # 2. Precio > 0
        check(ticker, "Precio > 0", price > 0, f"(price={price:.2f})")

        # 3. Arquetipo correcto
        check(ticker, f"Arquetipo = {exp_arch}", arch == exp_arch, f"(got={arch})")

        # 4. Metodología correcta
        check(ticker, f"Metodología = {exp_method}", method == exp_method, f"(got={method})")

        # 5. Valor intrínseco en rango razonable (para method=value)
        if exp_method == 'value':
            check(ticker, f"IV en rango [{iv_min},{iv_max}]",
                  iv_min <= iv <= iv_max, f"(iv={iv:.2f})")

        # 6. WACC razonable (6% - 14%)
        check(ticker, "WACC en rango [6%,14%]",
              0.06 <= wacc <= 0.14, f"(wacc={wacc*100:.1f}%)")

        # 7. FCF TTM > 0 (todas las empresas del test son rentables)
        if exp_method == 'value':
            check(ticker, "FCF TTM > 0", fcf_ttm > 0, f"(fcf={fcf_ttm/1e9:.2f}B)")

        # 8. Growth rate razonable (1% - 25% para value)
        if exp_method == 'value':
            check(ticker, "Growth rate [1%,25%]",
                  1.0 <= growth <= 25.0, f"(growth={growth:.1f}%, src={gs})")

        # 9. Valor intrínseco != precio actual (trivially)
        if exp_method == 'value':
            check(ticker, "IV != Precio (cálculo real)", abs(iv - price) > 1.0, f"(iv={iv:.2f}, price={price:.2f})")

        # 10. Al menos 1 modelo usado
        check(ticker, "Al menos 1 modelo de valoración", len(models) >= 1, f"(models={models})")

        # 11. Semáforo no vacío
        check(ticker, "Semáforo no vacío", len(sem) > 0, f"(sem={sem})")

        # 12. ROIC > 0 para compounders y value
        if exp_arch in ('compounder', 'classic_value'):
            check(ticker, "ROIC > 0", roic > 0, f"(roic={roic:.1f}%)", is_warn=True)

        # 13. MoS relativo en rango lógico (-200% a +200%)
        if exp_method == 'value':
            check(ticker, "MoS Relativo en rango [-200,200]",
                  -200 <= mos_rel <= 200, f"(mos_rel={mos_rel:.1f}%)", is_warn=True)

        # 14. Semáforo contiene texto esperado
        if exp_semaforo:
            check(ticker, f"Semáforo contiene '{exp_semaforo}'",
                  exp_semaforo in sem, f"(sem='{sem}')")

        print(f"  Precio={price:.2f}  IV={iv:.2f}  MoS_abs={mos_abs:.1f}%  "
              f"MoS_rel={mos_rel:.1f}%  WACC={wacc*100:.1f}%  Growth={growth:.1f}%  "
              f"FCF={fcf_ttm/1e9:.2f}B  Sem='{sem}'")

    except Exception as e:
        bugs.append(f"  {FAIL} [{ticker}] EXCEPCIÓN: {e}")
        print(f"  {FAIL} EXCEPCIÓN: {e}")

print("\n" + "=" * 70)
print(f"  RESUMEN: {len(bugs)} BUGS  |  {len(warns)} WARNINGS")
print("=" * 70)

if bugs:
    print(f"\n🚨 BUGS ({len(bugs)}):")
    for b in bugs:
        print(b)

if warns:
    print(f"\n⚠️  WARNINGS ({len(warns)}):")
    for w in warns:
        print(w)

if not bugs and not warns:
    print("\n✅ TODOS LOS CHECKS PASAN. Motor en buen estado.")
elif not bugs:
    print("\n✅ Sin bugs críticos. Solo warnings menores.")
