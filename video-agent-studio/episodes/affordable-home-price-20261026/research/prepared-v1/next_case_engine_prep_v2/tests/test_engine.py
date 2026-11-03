"""각 테스트는 산식·경계·제약 선택의 실제 오류를 검출한다. 외부 서비스는 호출하지 않는다."""
import importlib.util
from contextlib import redirect_stdout
from io import StringIO
import json
from decimal import Decimal as D, localcontext
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
engine = __import__('engine') if importlib.util.find_spec('engine') else None


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(engine, '연구용 계산 엔진 미구현: 실제 동작 구현 필요')

    def scenario(self, profile='A_first', price=600000000, deduction=0):
        packet = json.loads((ROOT / 'cases.json').read_text(encoding='utf-8'))
        return next(c for c in engine.expand_cases(packet)
                    if c['profile_id'] == profile and c['price_krw'] == price
                    and c['deduction_krw'] == deduction)

    def test_payment_matches_independent_reference(self):
        self.assertLess(abs(engine.payment(300000000, '0.04', 360) - D('1432245.8864')), D('.01'))

    def test_pv_amortizes_independently_for_360_months(self):
        # 독립 잔액 갱신: 엔진의 PV/payment 산식을 기대값 계산에 재사용하지 않는다.
        with localcontext() as ctx:
            ctx.prec = 40
            for annual_rate in ['.04','.07','.029','0']:
                with self.subTest(annual_rate=annual_rate):
                    principal = engine.pv(1000000, annual_rate, 360)
                    balance, repaid = principal, D(0)
                    for _ in range(360):
                        interest = balance * D(annual_rate) / 12
                        paid_principal = D(1000000) - interest
                        repaid += paid_principal
                        balance -= paid_principal
                    self.assertLess(abs(balance), D('.000001'))
                    self.assertLess(abs(repaid - principal), D('.000001'))

    def test_zero_rate_and_exhausted_service_budget(self):
        self.assertEqual(engine.payment(360000000, 0, 360), D(1000000))
        self.assertEqual(engine.pv(1000000, 0, 360), D(360000000))
        self.assertEqual(engine.service_ceiling(100000000, '.4', 41000000, '.07', 360), 0)

    def test_dsr_existing_annual_service_6m_reduces_available_budget(self):
        full = engine.service_ceiling(100000000, '.4', 0, '.07', 360)
        reduced = engine.service_ceiling(100000000, '.4', 6000000, '.07', 360)
        self.assertLess(abs(reduced - full * D('.85')), D('.000001'))
        self.assertLess(abs(engine.payment(reduced, '.07', 360) * 12 - D(34000000)), D('.000001'))

    def test_acquisition_and_education_tax_fixtures(self):
        for price, acquisition, education in [(600000000,6000000,600000),(750000000,15000000,1500000),
                                               (900000000,27000000,2700000),(1200000000,36000000,3600000)]:
            with self.subTest(price=price):
                x = engine.tax(price)
                self.assertEqual(x['acquisition_krw'], acquisition)
                self.assertEqual(x['education_krw'], education)
                self.assertEqual(x['agricultural_krw'], 0)

    def test_tax_rate_rounds_fraction_to_four_places_not_percentage(self):
        self.assertEqual(engine.tax(700000000)['acquisition_krw'], D(11690000))
        self.assertEqual(engine.tax(712345678)['rate_percent'], D('1.75'))
        for price in [599999999,600000000,600000001]:
            self.assertEqual(engine.tax(price)['rate_percent'], D(1))
        for price in [899999999,900000000,900000001]:
            self.assertEqual(engine.tax(price)['rate_percent'], D(3))

    def test_fractional_rate_four_decimal_regression_and_half_up_boundary(self):
        # 현행 법11 원식 전체와 송파 공식 JS212행의 독립 고정값.
        for price, want_rate, want_tax in [(650000000,'.0133',8645000),
                                          (700000000,'.0167',11690000),
                                          (750000000,'.0200',15000000)]:
            with self.subTest(price=price):
                got=engine.tax(price)
                effective_rate=got.get('rate_fraction',got['acquisition_krw']/D(price))
                self.assertEqual(effective_rate,D(want_rate))
                self.assertEqual(got['acquisition_krw'],D(want_tax))
        self.assertEqual(engine.tax(674249999)['rate_percent'],D('1.49'))
        self.assertEqual(engine.tax(674250000)['rate_percent'],D('1.50'))

    def test_each_tax_truncates_under_ten_won_before_total(self):
        # 합계 후 한번 절사하면13,712,650원이 되어10원 과다. 세목별 합계는13,712,640원.
        got=engine.tax(712345678)
        self.assertEqual(got['acquisition_krw'],D(12466040))
        self.assertEqual(got['education_krw'],D(1246600))
        self.assertEqual(got['acquisition_krw']+got['education_krw'],D(13712640))
        self.assertEqual(got.get('acquisition_before_truncation_krw'),D('12466049.365'))
        self.assertEqual(got.get('education_before_truncation_krw'),D('1246604.9365'))

    def test_video_review_subset_excludes_counterfactual_and_ineligible_cases(self):
        with redirect_stdout(StringIO()): engine.main()
        output=json.loads((ROOT/'results.json').read_text(encoding='utf-8'))
        subset=output.get('video_review_subset',{}).get('case_ids',[])
        self.assertEqual(len(subset),18)
        for row in output['case_results']:
            excluded=(row['deduction_scenario_status']=='counterfactual_sensitivity'
                      or not row['eligible_under_stated_inputs'])
            self.assertEqual(row['case_id'] in subset,not excluded)
            if excluded:self.assertTrue(row.get('video_use_label','').startswith('exclude_'))
        self.assertNotIn('B_bogeum_P600000000_C55000000',subset)
        self.assertNotIn('B_newborn_P900000000_C0',subset)

    def test_brokerage_9_and_12_boundaries_including_one_won(self):
        for price, want in [(899999999,'3959999.9956'),(900000000,'4950000'),(900000001,'4950000.0055'),
                            (1199999999,'6599999.9945'),(1200000000,'7920000'),(1200000001,'7920000.0066')]:
            with self.subTest(price=price):
                self.assertEqual(engine.brokerage(price)['with_vat_krw'], D(want))

    def test_cap_15_and_25_boundaries_including_one_won(self):
        for price, want in [(1499999999,600000000),(1500000000,600000000),(1500000001,400000000),
                            (2499999999,400000000),(2500000000,400000000),(2500000001,200000000)]:
            with self.subTest(price=price): self.assertEqual(engine.regulatory_cap(price), want)

    def test_cost_components_match_6_9_12_and_do_not_deduct_relief(self):
        for price, want in [(600000000,10740000),(900000000,36150000),(1200000000,49020000)]:
            self.assertEqual(engine.costs(price, 1500000)['total_krw'], want)

    def test_collateral_deduction_precedes_product_cap(self):
        case = self.scenario('B_newborn',900000000,55000000)
        x = engine.evaluate(case)
        self.assertEqual(x['limits_krw']['collateral'], 575000000)
        self.assertEqual(x['loan_ceiling_krw'], 400000000)
        self.assertIn('product', x['binding_constraints'])

    def test_bank_profiles_choose_actual_binding_constraints(self):
        for profile, price, deduction, want, binding in [
                ('A_ordinary',600000000,0,240000000,'collateral'),
                ('A_ordinary',600000000,55000000,185000000,'collateral'),
                ('A_first',600000000,0,420000000,'collateral'),
                ('A_first',600000000,55000000,365000000,'collateral'),
                ('A_ordinary',1200000000,0,480000000,'collateral')]:
            x=engine.evaluate(self.scenario(profile,price,deduction))
            self.assertEqual(x['loan_ceiling_krw'],want)
            self.assertIn(binding,x['binding_constraints'])
        x=engine.evaluate(self.scenario('A_first',900000000,0))
        self.assertEqual(x['binding_constraints'],['DSR'])

    def test_regulatory_total_cap_can_bind_independently(self):
        case=self.scenario();case['price_krw']=1600000000;case['annual_income_krw']=1000000000
        x=engine.evaluate(case)
        self.assertEqual(x['loan_ceiling_krw'],400000000)
        self.assertEqual(x['binding_constraints'],['regulatory_total'])

    def test_bank_dti_is_separate_and_nonbinding_with_zero_existing_debt(self):
        for profile in ['A_ordinary','A_first']:
            for price in [600000000,900000000,1200000000]:
                x=engine.evaluate(self.scenario(profile,price,0))
                self.assertGreater(x['limits_krw']['DTI'], x['limits_krw']['DSR'])
                self.assertGreater(x['limits_krw']['DTI'], x['loan_ceiling_krw'])

    def test_required_loan_cash_shortfall_and_ceiling_are_different(self):
        x=engine.evaluate(self.scenario('A_ordinary',600000000,0))
        self.assertEqual(x['required_loan_krw'],390740000)
        self.assertEqual(x['cash_shortfall_krw'],150740000)
        self.assertEqual(x['cash_required_including_reserve_krw'],400740000)
        self.assertFalse(x['cash_feasible'])
        self.assertIsNone(x['payment_if_financeable_krw'])

    def test_contract_payment_does_not_use_stress_rate(self):
        x=engine.evaluate(self.scenario())
        self.assertLess(abs(x['payment_at_ceiling_krw']-D('2005144.2410')),D('.01'))
        self.assertGreater(x['payment_at_ceiling_shock_krw'],x['payment_at_ceiling_krw'])
        self.assertLess(abs(x['payment_at_ceiling_shock_krw']-D('2518112.2059')),D('.01'))

    def test_policy_product_caps_and_dti_do_not_become_dsr40(self):
        for profile, want in [('B_didim',320000000),('B_bogeum',420000000),('B_newborn',400000000)]:
            x=engine.evaluate(self.scenario(profile,600000000,0))
            self.assertEqual(x['loan_ceiling_krw'],want)
            self.assertIsNone(x['limits_krw']['DSR'])
            self.assertGreater(x['limits_krw']['DTI'],want)
        self.assertEqual(engine.evaluate(self.scenario('B_newborn',600000000,55000000))['loan_ceiling_krw'],365000000)

    def test_policy_price_filters_and_firstbuyer_zero_debt(self):
        for profile in ['B_didim','B_bogeum']:
            for price in [900000000,1200000000]:
                x=engine.evaluate(self.scenario(profile,price,0))
                self.assertFalse(x['eligible_under_stated_inputs'])
                self.assertEqual(x['loan_ceiling_krw'],0)
                self.assertEqual(x['binding_constraints'],['eligibility'])
        self.assertTrue(engine.evaluate(self.scenario('B_newborn',900000000,0))['eligible_under_stated_inputs'])
        self.assertFalse(engine.evaluate(self.scenario('B_newborn',1200000000,0))['eligible_under_stated_inputs'])

    def test_solver_has_possible_and_impossible_neighbors_10000_won(self):
        for profile in ['A_ordinary','A_first']:
            for deduction in [0,55000000]:
                for budget in [None,1700000]:
                    case=self.scenario(profile,600000000,deduction)
                    sol=engine.solve_affordability(case,budget)
                    p=sol['max_price_krw'];self.assertEqual(p % 10000,0)
                    for offset,want in [(-10000,True),(0,True),(10000,False)]:
                        c=dict(case,price_krw=p+offset)
                        self.assertEqual(engine.affordable(c,budget),want,(profile,deduction,budget,p,offset))
        bank=engine.solve_affordability(self.scenario(),None)['max_price_krw']
        personal=engine.solve_affordability(self.scenario(),1700000)['max_price_krw']
        self.assertLess(personal,bank)

    def test_rounding_is_display_only_and_uses_half_up(self):
        self.assertEqual(engine.money_layers({'v':D(15000)})['reading_manwon']['v'],2)
        self.assertEqual(engine.money_layers({'v':D('14999.49')})['rounded_krw']['v'],14999)
        self.assertEqual(engine.money_layers({'v':D('14999.49')})['calculation_krw_decimal']['v'],'14999.49')

    def test_main_writes_30_cases_with_unrounded_and_reading_layers(self):
        with redirect_stdout(StringIO()): engine.main()
        output=json.loads((ROOT/'results.json').read_text(encoding='utf-8'))
        self.assertEqual(len(output['case_results']),30)
        self.assertEqual(len(output['affordability_A']),4)
        first=next(x for x in output['case_results'] if x['case_id']=='A_ordinary_P600000000_C0')
        self.assertEqual(D(first['required_loan_krw']),390740000)
        self.assertEqual(first['presentation']['reading_manwon']['required_loan_krw'],39074)
        self.assertTrue(all(not row['applied_to_base'] for row in output['conditional_relief_table']))
        for row in output['case_results']:
            if row['household_id']=='B' and row['eligible_under_stated_inputs']:
                self.assertGreater(D(row['policy_dti_sensitivity_7pct_krw']),D(row['loan_ceiling_krw']))


if __name__ == '__main__':
    unittest.main()
