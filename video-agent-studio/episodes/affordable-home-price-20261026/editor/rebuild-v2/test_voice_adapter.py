import copy
import sys
import unittest
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
from voice_adapter import normalize_payload,NATIVE


class VoiceAdapterTests(unittest.TestCase):
    def fixture(self):
        text='현금 2억.';beat={'anchor':'현금','action':'현금 표시'}
        script={'scenes':[{'id':'R029','title':'검사','narration':text,'beats':[beat]}]}
        cue={'id':'R029Q001','text':text,'display_lines':[text],'spoken_text':text,'source_start':0,'source_end':len(text),'first_word_index':0,'last_word_index':1,'start_s':.2,'end_s':1.1,'native_start_s':.2,'native_end_s':1.1,'timing_basis':'actual_provider_WordBoundary_semantic_grouping_no_interpolation'}
        measured={**beat,'source_start':0,'source_end':2,'start_s':.2,'end_s':.5,'first_word_index':0,'last_word_index':0,'timing_basis':NATIVE}
        s={'id':'R029','title':'검사','narration':text,'audio_48k_path':'fake/audio48.wav','audio_48k_sha256':'a'*64,'audio_path':'fake/audio24.wav','audio_sha256':'b'*64,'duration_s':2,'last_speech_end_s':1.1,'last_speech_basis':'synthetic_test_not_audio','gap_after_s':0,'scene_start_s':0,'scene_end_s':2,'cues':[cue],'beats':[measured],'words':[],'display_mapping':[],'transforms':[],'segments':[]}
        raw={'scenes':[s],'status':'measured_pending_independent_QA','rate':'+0%','brand_and_chapter_cards_included':False,'script_sha256':'c'*64,'audio_revision':'fake-test','voice':'ko-KR-InJoonNeural','timing_scope':'scene-local','cut_gap_s':.25,'final_hold_from_last_speech_s':3}
        return script,raw

    def test_preserves_native_times_and_keeps_parent_lock_pending(self):
        script,raw=self.fixture();v=normalize_payload(script,raw)
        self.assertEqual(v['status'],'measured_adapter_ready_parent_lock_pending')
        self.assertEqual(v['scenes'][0]['beatanchors'][0]['start_s'],.2)
        self.assertEqual(v['scenes'][0]['cues'],raw['scenes'][0]['cues'])
        self.assertTrue(v['final_hold_already_in_last_WAV'])

    def test_rejects_unmeasured_or_changed_narration(self):
        script,raw=self.fixture()
        for mutate in ['status','text']:
            r=copy.deepcopy(raw)
            if mutate=='status':r['status']='offline_prepared_NOT_synthesized'
            else:r['scenes'][0]['narration']='다른 원문'
            with self.assertRaises(ValueError):normalize_payload(script,r)

    def test_rejects_missing_native_word_evidence(self):
        script,raw=self.fixture();raw['scenes'][0]['cues'][0]['first_word_index']=1
        with self.assertRaises(ValueError):normalize_payload(script,raw)

    def test_anchor_span_is_not_interpolated(self):
        script,raw=self.fixture();raw['scenes'][0]['beats'][0]['source_end']=3
        with self.assertRaises(ValueError):normalize_payload(script,raw)


if __name__=='__main__':unittest.main()
