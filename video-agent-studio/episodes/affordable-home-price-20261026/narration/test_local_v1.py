"""Offline tests. All event timestamps and PCM in these tests are synthetic fixtures."""
import array
import asyncio
import importlib.util
import io
from pathlib import Path
import re
import shutil
import tempfile
import unittest
from unittest.mock import patch
import wave

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('narration_local',HERE/'production_v1.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
PREPARED=HERE/'prepare-v2-r2/prepared.json'


class LocalPreparation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=r.load(PREPARED)

    def test_body_only_exact_source_and_frozen_readings(self):
        q=[q for c in self.plan['chapters'] for q in c['paragraphs']]
        self.assertEqual(len(q),45)
        self.assertEqual(sum(len(x['text']) for x in q),6550)
        self.assertEqual(r.sha(PREPARED.parent/'source.md'),r.SCRIPT_SHA)
        self.assertTrue(all(not x['text'].startswith(('---','#')) for x in q))
        notes=r.load(r.EP/'writer/pronunciation_notes_v2.json')
        for x,note in zip(q,notes['scenes']):
            self.assertEqual(x['text'],note['display_text']);self.assertEqual(x['spoken_text'],note['spoken_text'])
        text=' '.join(x['text'] for x in q);spoken=' '.join(x['spoken_text'] for x in q)
        for exact in ('0.75%포인트','3.65%','5억 103만 원','3억 4,676만 원','300개월','176.4만 원'):
            self.assertIn(exact,text)
        self.assertIn('영점칠오 퍼센트 포인트',spoken);self.assertIn('삼점육오 퍼센트',spoken)
        self.assertNotRegex(spoken,r'\d|DSR|LTV|DTI|%|㎡')

    def test_all_meaning_units_and_synthetic_word_alignment(self):
        count=0
        for ch in self.plan['chapters']:
            for q in ch['paragraphs']:
                # Deliberately fixed event clock. This is not estimated actual TTS timing.
                events=[{'type':'WordBoundary','text':m.group(),'offset':i*2000000,
                    'duration':2100000} for i,m in enumerate(re.finditer(r'\S+',q['spoken_text']))]
                cues=r.align(q,events);count+=len(cues)
                for cue in cues:
                    self.assertGreater(len(r.compact(cue['text'])),9)
                    self.assertIn(len(cue['display_lines']),(1,2))
                    self.assertLessEqual(max(map(len,cue['display_lines'])),40)
                    self.assertEqual(' '.join(cue['text'].split()),' '.join(' '.join(cue['display_lines']).split()))
                    self.assertAlmostEqual(cue['start_s'],events[cue['first_word_index']]['offset']/1e7)
                self.assertTrue(all(a['end_s']<=b['start_s'] for a,b in zip(cues,cues[1:])))
                for a,b in q['protected_ranges']:
                    self.assertEqual(sum(c['source_start']<=a and c['source_end']>=b for c in cues),1)
                    cue=next(c for c in cues if c['source_start']<=a and c['source_end']>=b)
                    self.assertTrue(any(q['text'][a:b] in line for line in cue['display_lines']))
        self.assertGreater(count,100)

    def test_approval_block_precedes_any_provider_or_output(self):
        with tempfile.TemporaryDirectory(dir=HERE,prefix='offline_gate_') as temp:
            out=Path(temp)/'must_not_exist'
            with patch.object(r,'dependencies',side_effect=AssertionError('provider/deps must not be reached')):
                with self.assertRaises(r.p.GateError):asyncio.run(r.generate(PREPARED,out,Path(temp)/'missing_auth.json'))
            self.assertFalse(out.exists())
            auth=Path(temp)/'auth.json'
            r.save(auth,{'approved':True,'network_tts_authorized':True,'episode_id':r.EP.name,
                'script_sha256':r.SCRIPT_SHA,'prepared_sha256':r.sha(PREPARED),'cash_cap_krw':0,'paid_calls_authorized':False,
                'source':'main_direct_instruction','instruction_reference':'synthetic test only'})
            with patch.object(r,'LOCK',Path(temp)/'absent_lock.json'):
                with self.assertRaises(r.p.GateError):r.check_gate(PREPARED,auth)

    def test_sentenceboundary_or_incomplete_coverage_rejected(self):
        q=self.plan['chapters'][0]['paragraphs'][0]
        with self.assertRaises(AssertionError):r.align(q,[{'type':'SentenceBoundary','text':q['spoken_text'],'offset':0,'duration':10}])
        with self.assertRaises(AssertionError):r.align(q,[{'type':'WordBoundary','text':'일부','offset':0,'duration':10}])

    def test_exact_dual_receipt_gate_and_receipt_tampering(self):
        with tempfile.TemporaryDirectory(dir=HERE,prefix='offline_dual_gate_') as temp:
            ep=Path(temp)/r.EP.name;ep.mkdir()
            for name in self.plan['inputs']:
                target=ep/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r.EP/name,target)
            canonical=ep/'outputs/script-final-v2/script_v2.md';canonical.parent.mkdir(parents=True)
            shutil.copyfile(PREPARED.parent/'source.md',canonical)
            lock={'approved':True,'script_path':'outputs/script-final-v2/script_v2.md','script_sha256':r.SCRIPT_SHA}
            for name in ('codex','claude'):
                receipt=ep/(name+'_synthetic_receipt.json')
                r.save(receipt,{'reviewer':name,'approved':True,'required_issues':[],
                    'critical_issues':[],'script_sha256':r.SCRIPT_SHA,'approval_scope':'script_content'})
                lock[name+'_receipt']={'path':receipt.name,'sha256':r.sha(receipt)}
            lockfile=ep/'synthetic_locked_script.json';r.save(lockfile,lock)
            authfile=ep/'synthetic_main_instruction.json'
            r.save(authfile,{'approved':True,'network_tts_authorized':True,'episode_id':ep.name,
                'script_sha256':r.SCRIPT_SHA,'prepared_sha256':r.sha(PREPARED),'cash_cap_krw':0,
                'paid_calls_authorized':False,'source':'main_direct_instruction','instruction_reference':'SYNTHETIC TEST FIXTURE ONLY'})
            with patch.object(r,'EP',ep),patch.object(r,'LOCK',lockfile):
                _,evidence=r.check_gate(PREPARED,authfile)
                self.assertEqual(set(evidence['receipts']),{'codex','claude'})
                receipt=ep/'claude_synthetic_receipt.json'
                receipt.write_text(receipt.read_text(encoding='utf8')+'\n',encoding='utf8')
                with self.assertRaises(r.p.GateError):r.check_gate(PREPARED,authfile)

    def test_pcm_tail_30fps_and_native_signal_end_distinction(self):
        with tempfile.TemporaryDirectory(dir=HERE,prefix='offline_pcm_') as temp:
            path=Path(temp)/'synthetic.wav'
            samples=array.array('h',[0]*24000);samples[21000:21600]=array.array('h',[100]*600)
            with wave.open(str(path),'wb') as w:w.setparams((1,2,24000,0,'NONE','not compressed'));w.writeframes(samples.tobytes())
            record={'paragraph':1,'wave_file':str(path),'last_word_end_s':0.8,'cues':[]}
            result=r.p.assemble_chapter(10,'synthetic fixture',[record],r.CONTRACT,Path(temp)/'padded.wav')
            self.assertEqual(result['pcm_frames']%800,0)
            self.assertGreaterEqual(result['tail_from_last_spoken_s'],3)
            self.assertGreater(result['last_pcm_signal_end_s'],result['last_native_word_end_s'])
            self.assertAlmostEqual(result['last_speech_end_s'],result['last_pcm_signal_end_s'])


if __name__=='__main__':unittest.main(verbosity=2)
