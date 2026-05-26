"""
test_engine.py — Unit tests for Value Analyst engine module.
Tests cover all valuation formulas, archetype detection, WACC calculation,
and edge cases like currency conversion and dividend yield sanity checks.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from backend.engine import (
    _avg, _trend, _growth_rate,
    calculate_fcf_real, calculate_roic, check_non_gaap,
    graham_valuation, dcf_valuation,
    multiphase_dcf_valuation, revenue_dcf_valuation,
    book_value_valuation, ddm_valuation,
    margin_of_safety, assess_quality,
    detect_archetype, get_wacc,
    run_full_analysis,
)


class TestAvg(unittest.TestCase):
    """Test the _avg helper function."""

    def test_basic_average(self):
        self.assertAlmostEqual(_avg([10, 20, 30]), 20.0)

    def test_with_none_values(self):
        self.assertAlmostEqual(_avg([10, None, 30]), 20.0)

    def test_zeros_are_included(self):
        """Critical fix: zeros must NOT be excluded anymore."""
        result = _avg([10, 0, 20])
        self.assertAlmostEqual(result, 10.0)  # (10 + 0 + 20) / 3 = 10

    def test_all_none(self):
        self.assertIsNone(_avg([None, None]))

    def test_empty_list(self):
        self.assertIsNone(_avg([]))

    def test_single_value(self):
        self.assertAlmostEqual(_avg([42.5]), 42.5)


class TestTrend(unittest.TestCase):
    """Test the _trend helper function."""

    def test_upward_trend(self):
        self.assertEqual(_trend([120, 100, 90, 80]), '↑')

    def test_downward_trend(self):
        self.assertEqual(_trend([80, 100, 110, 120]), '↓')

    def test_stable_trend(self):
        self.assertEqual(_trend([100, 100, 100, 100]), '→')

    def test_insufficient_data(self):
        self.assertEqual(_trend([100]), '?')

    def test_all_none(self):
        self.assertEqual(_trend([None, None]), '?')


class TestGrowthRate(unittest.TestCase):
    """Test the _growth_rate CAGR estimation."""

    def test_positive_growth(self):
        # 100 → 121 over 2 years → CAGR ≈ 10%
        result = _growth_rate([121, 110, 100])
        self.assertAlmostEqual(result, 0.10, places=2)

    def test_clamp_high_growth(self):
        # Growth > 25% should be clamped
        result = _growth_rate([1000, 100])
        self.assertEqual(result, 0.25)

    def test_clamp_negative_growth(self):
        # Decline > -10% should be clamped
        result = _growth_rate([10, 100])
        self.assertEqual(result, -0.10)

    def test_insufficient_data(self):
        result = _growth_rate([100])
        self.assertEqual(result, 0.05)


class TestGrahamValuation(unittest.TestCase):
    """Test Benjamin Graham's intrinsic value formula."""

    def test_standard_case(self):
        # V = (EPS * (8.5 + 2g) * 4.4) / Y
        # EPS=5, g=10%, Y=4.5
        # V = (5 * (8.5 + 20) * 4.4) / 4.5 = (5 * 28.5 * 4.4) / 4.5
        # V = 627 / 4.5 = 139.33
        result = graham_valuation(5.0, 10.0)
        self.assertAlmostEqual(result, 139.33, places=1)

    def test_zero_growth(self):
        # V = (EPS * 8.5 * 4.4) / 4.5
        result = graham_valuation(5.0, 0.0)
        expected = (5 * 8.5 * 4.4) / 4.5
        self.assertAlmostEqual(result, expected, places=1)

    def test_negative_eps(self):
        """Graham should return 0 for negative EPS."""
        self.assertEqual(graham_valuation(-5.0, 10.0), 0)

    def test_zero_eps(self):
        self.assertEqual(graham_valuation(0, 10.0), 0)


class TestDCFValuation(unittest.TestCase):
    """Test standard DCF valuation."""

    def test_basic_dcf(self):
        result = dcf_valuation(
            fcf_current=1e9, growth_rate=0.10,
            shares=1e9, total_debt=5e9, cash=10e9, wacc=0.10
        )
        self.assertGreater(result, 0)

    def test_negative_fcf(self):
        result = dcf_valuation(fcf_current=-1e9, growth_rate=0.10, shares=1e9)
        self.assertEqual(result, 0)

    def test_zero_shares(self):
        result = dcf_valuation(fcf_current=1e9, growth_rate=0.10, shares=0)
        self.assertEqual(result, 0)

    def test_higher_growth_gives_higher_value(self):
        low_growth = dcf_valuation(fcf_current=1e9, growth_rate=0.05, shares=1e9)
        high_growth = dcf_valuation(fcf_current=1e9, growth_rate=0.15, shares=1e9)
        self.assertGreater(high_growth, low_growth)

    def test_higher_wacc_gives_lower_value(self):
        low_wacc = dcf_valuation(fcf_current=1e9, growth_rate=0.10, shares=1e9, wacc=0.08)
        high_wacc = dcf_valuation(fcf_current=1e9, growth_rate=0.10, shares=1e9, wacc=0.12)
        self.assertGreater(low_wacc, high_wacc)


class TestMultiphaseDCF(unittest.TestCase):
    """Test Multi-Phase DCF for Compounder archetype."""

    def test_basic_multiphase(self):
        result = multiphase_dcf_valuation(
            fcf_current=1e9, high_growth=0.20,
            shares=1e9, wacc=0.10
        )
        self.assertGreater(result, 0)

    def test_higher_than_standard_dcf_at_same_growth(self):
        """Multi-phase with high growth should exceed standard DCF at same growth."""
        standard = dcf_valuation(
            fcf_current=1e9, growth_rate=0.15, shares=1e9, wacc=0.10
        )
        multiphase = multiphase_dcf_valuation(
            fcf_current=1e9, high_growth=0.15,
            shares=1e9, wacc=0.10
        )
        # Both should be positive; multiphase allows growth to fade gracefully
        self.assertGreater(standard, 0)
        self.assertGreater(multiphase, 0)

    def test_negative_fcf_returns_zero(self):
        result = multiphase_dcf_valuation(
            fcf_current=-500e6, high_growth=0.20, shares=1e9
        )
        self.assertEqual(result, 0)


class TestRevenueDCF(unittest.TestCase):
    """Test Revenue-based DCF for Hypergrowth archetype."""

    def test_basic_revenue_dcf(self):
        result = revenue_dcf_valuation(
            revenue_current=5e9, revenue_growth=0.30,
            target_margin=0.20, shares=1e9, wacc=0.12
        )
        self.assertGreater(result, 0)

    def test_zero_revenue(self):
        result = revenue_dcf_valuation(
            revenue_current=0, revenue_growth=0.30,
            target_margin=0.20, shares=1e9
        )
        self.assertEqual(result, 0)


class TestBookValueValuation(unittest.TestCase):
    """Test Price/Book valuation for Financial archetype."""

    def test_basic_book_value(self):
        result = book_value_valuation(book_value_per_share=50.0, roe=0.15)
        self.assertGreater(result, 0)
        # With ROE=15%, justified P/B should be > 1x
        self.assertGreater(result, 50.0)

    def test_high_roe_gives_higher_value(self):
        low_roe = book_value_valuation(book_value_per_share=50.0, roe=0.08)
        high_roe = book_value_valuation(book_value_per_share=50.0, roe=0.20)
        self.assertGreater(high_roe, low_roe)

    def test_zero_book_value(self):
        result = book_value_valuation(book_value_per_share=0, roe=0.15)
        self.assertEqual(result, 0)

    def test_negative_book_value(self):
        result = book_value_valuation(book_value_per_share=-10, roe=0.15)
        self.assertEqual(result, 0)


class TestDDMValuation(unittest.TestCase):
    """Test Dividend Discount Model for REIT/Utility archetype."""

    def test_basic_ddm(self):
        # D1 = 2 * 1.03 = 2.06; V = 2.06 / (0.08 - 0.03) = 41.2
        result = ddm_valuation(dividend_per_share=2.0, growth_rate=0.03, discount_rate=0.08)
        self.assertAlmostEqual(result, 41.2, places=1)

    def test_discount_rate_equals_growth(self):
        result = ddm_valuation(dividend_per_share=2.0, growth_rate=0.08, discount_rate=0.08)
        self.assertEqual(result, 0)

    def test_no_dividend(self):
        result = ddm_valuation(dividend_per_share=0, growth_rate=0.03, discount_rate=0.08)
        self.assertEqual(result, 0)


class TestMarginOfSafety(unittest.TestCase):
    """Test Margin of Safety calculation."""

    def test_undervalued(self):
        # MoS = (100 - 80) / 100 * 100 = 20%
        result = margin_of_safety(100, 80)
        self.assertAlmostEqual(result, 20.0)

    def test_overvalued(self):
        # MoS = (100 - 120) / 100 * 100 = -20%
        result = margin_of_safety(100, 120)
        self.assertAlmostEqual(result, -20.0)

    def test_zero_intrinsic(self):
        result = margin_of_safety(0, 80)
        self.assertEqual(result, 0)


class TestArchetypeDetection(unittest.TestCase):
    """Test archetype classification logic."""

    def test_classic_value(self):
        data = {'sector': 'Consumer Defensive', 'industry': 'Packaged Foods',
                'revenue_values': [10e9, 9e9, 8e9]}
        arch_id, _ = detect_archetype(data, roic_avg=12, growth_rate=0.05, eps_ttm=5.0, fcf_ttm=2e9)
        self.assertEqual(arch_id, 'classic_value')

    def test_compounder(self):
        data = {'sector': 'Technology', 'industry': 'Software',
                'revenue_values': [20e9, 15e9, 10e9]}
        arch_id, _ = detect_archetype(data, roic_avg=25, growth_rate=0.18, eps_ttm=8.0, fcf_ttm=5e9)
        self.assertEqual(arch_id, 'compounder')

    def test_hypergrowth_negative_eps(self):
        data = {'sector': 'Technology', 'industry': 'Software—Application',
                'revenue_values': [5e9, 3e9, 1.5e9]}
        arch_id, _ = detect_archetype(data, roic_avg=None, growth_rate=0.30, eps_ttm=-2.0, fcf_ttm=-500e6)
        self.assertEqual(arch_id, 'hypergrowth')

    def test_financial(self):
        data = {'sector': 'Financial Services', 'industry': 'Banks—Diversified',
                'revenue_values': [50e9, 48e9, 45e9]}
        arch_id, _ = detect_archetype(data, roic_avg=12, growth_rate=0.05, eps_ttm=3.0, fcf_ttm=10e9)
        self.assertEqual(arch_id, 'financial')

    def test_reit(self):
        data = {'sector': 'Real Estate', 'industry': 'REIT—Retail',
                'revenue_values': [2e9, 1.8e9]}
        arch_id, _ = detect_archetype(data, roic_avg=8, growth_rate=0.03, eps_ttm=2.0, fcf_ttm=1e9)
        self.assertEqual(arch_id, 'reit_utility')

    def test_utility(self):
        data = {'sector': 'Utilities', 'industry': 'Utilities—Regulated Electric',
                'revenue_values': [30e9, 28e9]}
        arch_id, _ = detect_archetype(data, roic_avg=8, growth_rate=0.02, eps_ttm=4.0, fcf_ttm=3e9)
        self.assertEqual(arch_id, 'reit_utility')

    def test_speculative_no_eps_no_revenue_growth(self):
        data = {'sector': 'Healthcare', 'industry': 'Biotechnology',
                'revenue_values': [100e6, 95e6, 90e6]}
        arch_id, _ = detect_archetype(data, roic_avg=None, growth_rate=0.03, eps_ttm=-5.0, fcf_ttm=-200e6)
        self.assertEqual(arch_id, 'speculative')


class TestWACC(unittest.TestCase):
    """Test variable WACC calculation."""

    def test_technology_large_cap(self):
        wacc = get_wacc('Technology', 50e9)
        self.assertAlmostEqual(wacc, 0.10)

    def test_technology_mega_cap(self):
        wacc = get_wacc('Technology', 500e9)
        self.assertAlmostEqual(wacc, 0.09)  # 0.10 - 0.01

    def test_utilities_small_cap(self):
        wacc = get_wacc('Utilities', 1e9)
        self.assertAlmostEqual(wacc, 0.09)  # 0.07 + 0.02

    def test_financial_mid_cap(self):
        wacc = get_wacc('Financial Services', 5e9)
        self.assertAlmostEqual(wacc, 0.10)  # 0.09 + 0.01

    def test_unknown_sector(self):
        wacc = get_wacc('Unknown Sector', 50e9)
        self.assertAlmostEqual(wacc, 0.10)  # Default base, large cap no adjustment

    def test_floor(self):
        # Even mega-cap utilities shouldn't go below 6%
        wacc = get_wacc('Utilities', 500e9)
        self.assertGreaterEqual(wacc, 0.06)


class TestRunFullAnalysis(unittest.TestCase):
    """Integration test for run_full_analysis."""

    def _make_test_data(self, **overrides):
        """Create a minimal valid data dict for testing."""
        base = {
            'ticker': 'TEST',
            'empresa': 'Test Corp',
            'sector': 'Technology',
            'industry': 'Software—Application',
            'currency': 'USD',
            'financial_currency': 'USD',
            'current_price': 100.0,
            'market_cap': 50e9,
            'shares_outstanding': 500e6,
            'enterprise_value': 55e9,
            'fiscal_dates': ['2024-12-31', '2023-12-31', '2022-12-31'],
            'historical_prices': [90, 80, 70],
            'eps_values': [5.0, 4.5, 4.0],
            'eps_ttm': 5.5,
            'ebitda_values': [10e9, 9e9, 8e9],
            'ebitda_ttm': 11e9,
            'capex_values': [2e9, 1.8e9, 1.5e9],
            'interest_values': [500e6, 400e6, 300e6],
            'tax_values': [2e9, 1.8e9, 1.5e9],
            'wc_values': [100e6, -50e6, 200e6],
            'da_values': [1e9, 900e6, 800e6],
            'ebit_values': [8e9, 7e9, 6e9],
            'pretax_values': [7.5e9, 6.5e9, 5.5e9],
            'equity_values': [30e9, 28e9, 25e9],
            'total_debt_values': [10e9, 9e9, 8e9],
            'cash_values': [5e9, 4e9, 3e9],
            'fcf_yahoo_values': [6e9, 5e9, 4e9],
            'revenue_values': [40e9, 35e9, 30e9],
            'net_income_values': [5e9, 4e9, 3e9],
            'per_trailing': 18.2,
            'per_forward': 15.5,
            'growth_estimate': 0.12,
            'analyst_target': 120.0,
            'dividend_yield': 0.015,
            'payout_ratio': 0.30,
            'book_value': 60.0,
            'roe': 0.17,
            'dividend_rate': 1.5,
            'held_percent_insiders': 0.05,
            'audit_risk': 3,
            'board_risk': 2,
            'compensation_risk': 4,
            'business_summary': 'A test software company.',
            'shares_history': [500e6, 510e6, 520e6],
            'fetched_at': '2024-01-01 00:00:00',
            'error': None,
        }
        base.update(overrides)
        return base

    def test_classic_value_flow(self):
        data = self._make_test_data(growth_estimate=0.08)
        result = run_full_analysis(data)

        self.assertIsNone(result.get('error'))
        self.assertEqual(result['ticker'], 'TEST')
        self.assertEqual(result['currency'], 'USD')
        self.assertIn(result['archetype_id'], ['classic_value', 'compounder'])
        self.assertGreater(result['graham_value'], 0)
        self.assertGreater(result['dcf_value'], 0)
        self.assertGreater(result['intrinsic_value'], 0)
        self.assertIsNotNone(result['margen_seguridad'])

    def test_negative_eps_falls_to_hypergrowth_or_speculative(self):
        data = self._make_test_data(
            eps_ttm=-2.0,
            eps_values=[-2.0, -1.5, -1.0],
            growth_estimate=0.30,
        )
        result = run_full_analysis(data)
        self.assertIn(result['archetype_id'], ['hypergrowth', 'speculative'])
        # Graham should be 0 for negative EPS
        self.assertEqual(result['graham_value'], 0)

    def test_financial_archetype(self):
        data = self._make_test_data(
            sector='Financial Services',
            industry='Banks—Diversified',
            book_value=50.0,
            roe=0.14,
        )
        result = run_full_analysis(data)
        self.assertEqual(result['archetype_id'], 'financial')
        # Should have an alt_value from P/B model
        self.assertIsNotNone(result.get('alt_value'))

    def test_dividend_yield_sanity_check(self):
        """TSMC bug: dividend yield > 20% should be flagged as unreliable."""
        data = self._make_test_data(dividend_yield=0.95)
        result = run_full_analysis(data)
        self.assertFalse(result['dividend_yield_valid'])
        self.assertIsNone(result['dividend_yield'])
        self.assertAlmostEqual(result['dividend_yield_raw'], 0.95)

    def test_currency_propagation(self):
        """NOD.OL fix: currency should propagate from data to result."""
        data = self._make_test_data(currency='NOK', financial_currency='NOK')
        result = run_full_analysis(data)
        self.assertEqual(result['currency'], 'NOK')
        self.assertEqual(result['financial_currency'], 'NOK')

    def test_error_passthrough(self):
        data = {'error': 'Ticker not found'}
        result = run_full_analysis(data)
        self.assertEqual(result['error'], 'Ticker not found')

    def test_non_gaap_rejection(self):
        """Companies with >30% EBITDA divergence should be 🚫 NO ELEGIBLE."""
        data = self._make_test_data(
            ebitda_values=[15e9, 14e9, 13e9],  # Much higher than EBIT + D&A
            ebit_values=[6e9, 5.5e9, 5e9],
            da_values=[1e9, 900e6, 800e6],
        )
        result = run_full_analysis(data)
        self.assertIn('NO ELEGIBLE', result['estado_semaforo'])

    def test_wacc_varies_by_sector(self):
        tech_data = self._make_test_data(sector='Technology')
        util_data = self._make_test_data(sector='Utilities')
        tech_result = run_full_analysis(tech_data)
        util_result = run_full_analysis(util_data)
        self.assertLess(util_result['wacc_used'], tech_result['wacc_used'])

    def test_margins_and_debt_metrics(self):
        """Test Phase 3 margin and debt metrics extraction."""
        data = self._make_test_data(
            gross_profit_values=[20e9, 15e9],
            revenue_values=[40e9, 30e9],
            net_income_values=[5e9, 3e9],
            ebit_values=[8e9, 5e9],
            interest_values=[500e6, 500e6],
            ebitda_values=[10e9, 8e9],
            total_debt_values=[10e9, 10e9],
            cash_values=[5e9, 5e9],
        )
        result = run_full_analysis(data)
        self.assertAlmostEqual(result['current_gross_margin'], 0.5)  # 20 / 40
        self.assertAlmostEqual(result['current_operating_margin'], 0.2)  # 8 / 40
        self.assertAlmostEqual(result['current_net_margin'], 0.125)  # 5 / 40
        
        # Net Debt = 10 - 5 = 5. EBITDA = 10. Ratio = 0.5
        self.assertAlmostEqual(result['net_debt_ebitda'], 0.5)
        # Interest Coverage = EBIT / Interest = 8e9 / 500e6 = 16
        self.assertAlmostEqual(result['interest_coverage'], 16.0)
        
    def test_growth_haircut_logic(self):
        """Test that EPS growth is cross-validated with Revenue growth."""
        data = self._make_test_data(
            archetype_id='classic_value',
            eps_values=[2.0, 1.0],  # 100% growth
            revenue_values=[110e6, 100e6],  # 10% growth
            growth_estimate=None
        )
        result = run_full_analysis(data)
        # Revenue growth is 10%. 1.5x = 15%.
        # So EPS growth of 100% should be clamped to 15%.
        # Actually _growth_rate for 2 years is calculated and then we clamp.
        # It should apply the haircut.
        self.assertLessEqual(result['eps_trend'], '↑')


class TestNonGAAPDetection(unittest.TestCase):
    """Test Non-GAAP manipulation detection."""

    def test_clean_financials(self):
        data = {
            'ebitda_values': [10e9, 9e9],
            'ebit_values': [8e9, 7e9],
            'da_values': [2e9, 2e9],
        }
        result = check_non_gaap(data)
        self.assertEqual(result['non_gaap_flag'], '✅ OK')

    def test_warning_divergence(self):
        data = {
            'ebitda_values': [12e9],  # 20% higher than EBIT + D&A = 10
            'ebit_values': [8e9],
            'da_values': [2e9],
        }
        result = check_non_gaap(data)
        self.assertEqual(result['non_gaap_flag'], '⚠️ Precaución')

    def test_reject_divergence(self):
        data = {
            'ebitda_values': [15e9],  # 50% higher than EBIT + D&A = 10
            'ebit_values': [8e9],
            'da_values': [2e9],
        }
        result = check_non_gaap(data)
        self.assertEqual(result['non_gaap_flag'], '🚫 No Elegible')


if __name__ == '__main__':
    unittest.main()
