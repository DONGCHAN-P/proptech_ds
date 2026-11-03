"""Meaningful gate + layout tests on synthetic clocks. NEVER renders MP4/TTS."""
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pipeline as p
from graphics import make


class InputGates(unittest.TestCase):
    def setUp(self):
        self.scene={'id':'R001','title':'검사 제목','narration':'현금 예비 비용 자기자금 한도 부족','beats':[{'anchor':v,'action':v} for v in ['현금','예비','비용','자기자금','한도','부족']]}
        self.voice={'scene_id':'R001','duration_s':15,'last_speech_end_s':14,'cues':[{'id':'R001C01','text':self.scene['narration'],'display_lines':[self.scene['narration']],'start_s':0,'end_s':14}],'beatanchors':[]}
        for i,b in enumerate(self.scene['beats']):
            pos=self.scene['narration'].index(b['anchor'])
            self.voice['beatanchors'].append({'beat_index':i,'anchor':b['anchor'],'char_start':pos,'char_end':pos+len(b['anchor']),'start_s':i*2+.5,'end_s':i*2+1.3,'cue_ids':['R001C01'],'timing_basis':'native_word_boundary'})
        self.g=make('funding_waterfall',p.read(p.EP/'research/verified_case_packet.json'))
        self.mapping={s['key']:i for i,s in enumerate(self.g['stages'])}

    def test_exact_actual_anchors(self):
        p.validate_voice(self.scene,self.voice)
        self.assertEqual(len(p.resolve_beats(self.scene,self.voice,self.g,self.mapping)),6)

    def test_missing_or_changed_anchor_does_not_fallback(self):
        for field,value in [('anchor','틀린 앵커'),('char_start',3),('timing_basis','estimated')]:
            v=copy.deepcopy(self.voice);v['beatanchors'][0][field]=value
            with self.assertRaises(ValueError):p.resolve_beats(self.scene,v,self.g,self.mapping)

    def test_empty_and_corrupt_korean_rejected(self):
        for narration in ['', '??????']:
            s={**self.scene,'narration':narration}
            with self.assertRaises(ValueError):p.validate_voice(s,self.voice)

    def test_prohibited_output_path(self):
        with self.assertRaises(ValueError):p.owned(p.EP/'state.json')

    def test_future_amounts_hidden_no_focus_ring(self):
        self.assertNotIn('focus-ring',self.g['html'])
        self.assertIn('class="semantic"',self.g['html'])
        self.assertEqual([s['key'] for s in self.g['stages']],list(self.mapping))


def main():
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(InputGates)
    result=unittest.TextTestRunner().run(suite)
    if not result.wasSuccessful():raise SystemExit(1)
    run=p.OUT/(sys.argv[1] if len(sys.argv)>1 else 'template-check-v3')
    if run.exists():raise ValueError('Template check outputs already exist; preserve and use a new explicit version')
    packet=p.read(p.EP/'research/verified_case_packet.json')
    newborn=p.read(p.EP/'research/newborn_policy_addendum_v2.json')
    kinds=p.KINDS+['opening_answers','expense_receipt','policy_comparison','rate_sensitivity','newborn_rate_timeline','price_case_comparison']
    for i,kind in enumerate(kinds):
        g=make(kind,packet,newborn);sid='TEST_'+kind
        beats=[{**s,'start_s':.5+n*2,'end_s':1.3+n*2,'anchor':'TEMPLATE_ONLY','cue_ids':[]} for n,s in enumerate(g['stages'])]
        scene={'id':sid,'title':{'funding_waterfall':'6억원 집에 추가로 필요한 현금','ltv_dsr':'집값 기준과 소득 기준 중 낮은 한도','monthly_budget':'월 상환예산에서 다시 정하는 집값','opening_answers':'은행 한도와 월예산이 만드는 두 가격','expense_receipt':'6억원 집의 거래비용','policy_comparison':'같은 B가구의 상품별 한도','rate_sensitivity':'금리가 오르면 남는 저축은 줄어듭니다','newborn_rate_timeline':'5년 뒤에는 남은 원금과 기간으로 다시 계산','price_case_comparison':'가격이 오를수록 필요한 현금'}[kind]}
        voice={'duration_s':len(beats)*2+1,'last_speech_end_s':None,'cues':[],'audio_path':None}
        p.emit_project(run/'scenes'/sid,scene,voice,g,beats,'검증 자금계획 사례 · 2026.10.26 · 서울 84㎡ · 조건부 계획값',template=True)
    subprocess.run(['node',str(p.HERE/'verify_templates.cjs'),str(run)],check=True,env=p.ENV)
    p.dump(p.HERE/'initial_validation.json',{'status':'input_gate_and_template_geometry_pass','unittest_count':result.testsRun,'geometry_receipt':str(run/'geometry_receipt.json'),'template_only':True,'writer_text_consumed':False,'audio_generated':False,'MP4_rendered':False,'actual_listening':False,'continuous_playback':False})


if __name__=='__main__':main()
