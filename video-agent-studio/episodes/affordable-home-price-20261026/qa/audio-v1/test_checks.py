"""Meaningful text/gate checks; no generated speech or model inference."""
import json, sys, unittest
from pathlib import Path
from unittest.mock import patch
sys.dont_write_bytecode=True
QA=Path(__file__).resolve().parent
sys.path.insert(0,str(QA))
import checks,run_asr
from prepare import read,dump

class Checks(unittest.TestCase):
    def equal(self,a,b):
        c=checks.compare(a,b)
        self.assertEqual(c['numeric_differences'],[])
        self.assertEqual(c['coreterm_differences'],[])
    def test_krw_costs_and_required_loan(self):
        self.equal('1,074만 원 3,615만 원 4,902만 원 3억 9,074만 원','천칠십사만 원 삼천육백십오만 원 사천구백이만 원 삼억 구천칠십사만 원')
        self.assertEqual([r['value'] for r in checks.numbers('1,074만 원 3,615만 원 4,902만 원')],['10740000','36150000','49020000'])
    def test_decimal_reset_and_units(self):
        self.equal('162.6만 원 176.4만 원 0.75%포인트 3.65%','백육십이점육만 원 백칠십육점사만 원 영점칠오 퍼센트 포인트 삼점육오 퍼센트')
        self.assertTrue(checks.compare('0.75%포인트','0.75%')['numeric_differences'])
    def test_reset_remaining_vs_new_loan(self):
        self.equal('60회 300개월 30년','육십회 삼백개월 삼십년')
        self.assertTrue(checks.compare('60회 300개월','60회 360개월')['numeric_differences'])
    def test_false_small_amount_is_flagged_not_approved(self):
        c=checks.compare('176.4만 원','170.4만 원')
        self.assertTrue(c['numeric_differences']);self.assertFalse(c['actual_pronunciation_verified'])
    def test_acronyms_and_ordinary_korean_not_substituted(self):
        self.equal('DSR LTV DTI 비상자금','디 에스 알 엘 티 브 이 디 티 아 이 비상자금')
        self.assertIn('비상자금',checks.norm('비상자금'))
    def test_particle_and_decimal_boundaries(self):
        self.equal('필요 대출이 10억 2,902만 원입니다. 상한은 0.4%입니다.','필요 대출이 십억 이천구백이만 원입니다. 상한은 영점사 퍼센트입니다.')
    def test_dates_age_area(self):
        self.equal('2026년 10월 19일 만 2세 84㎡','이천이십육년 시월 십구일 만 이세 팔십사 제곱미터')
    def test_all45_pinned_source_reading_pairs(self):
        e=read(QA/'expected.json');rows=[p for c in e['chapters'] for p in c['paragraphs']]
        self.assertEqual(len(rows),45);self.assertEqual(sum(len(p['protected_occurrences']) for p in rows),187)
        for p in rows:
            with self.subTest(scene=p['scene_id']):self.equal(p['text'],p['spoken_text'])
    def test_gate_denies_unapproved_authorization(self):
        cfg=read(QA/'config.json');realread=run_asr.read
        def denied(p):
            d=realread(p)
            if str(p)==cfg['main_authorization']:d['approved']=False
            return d
        with patch.object(run_asr,'read',side_effect=denied):
            with self.assertRaises(AssertionError):run_asr.gate(cfg)
    def test_gate_denies_wrong_episode(self):
        cfg=read(QA/'config.json');realread=run_asr.read
        def wrong(p):
            d=realread(p)
            if str(p)==cfg['main_authorization']:d['episode_id']='other_episode'
            return d
        with patch.object(run_asr,'read',side_effect=wrong):
            with self.assertRaises(AssertionError):run_asr.gate(cfg)

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks))
    dump(QA/'tests.json',{'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'passed':result.wasSuccessful(),'actual_audio_inference_here':False,'actual_listening':False})
    raise SystemExit(not result.wasSuccessful())
