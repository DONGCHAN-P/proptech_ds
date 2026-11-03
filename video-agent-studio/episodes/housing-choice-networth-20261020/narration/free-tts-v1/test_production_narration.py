import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import wave
import hashlib
import asyncio

SIDE = Path(__file__).resolve().parent


class ProductionContracts(unittest.TestCase):
    def module(self):
        source = SIDE / 'production_narration.py'
        self.assertTrue(source.is_file(), '본문 게이트·발음·단어 타임맵 구현 전')
        spec = importlib.util.spec_from_file_location('production_narration', source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_gate_requires_two_separate_approved_receipts_for_same_actual_sha(self):
        p = self.module()
        with tempfile.TemporaryDirectory(dir=SIDE) as tmp:
            root = Path(tmp)
            script = root / 'script.md'
            script.write_text('검수할 본문', encoding='utf8')
            digest = hashlib.sha256(script.read_bytes()).hexdigest()
            for who in ('codex', 'claude'):
                (root / (who+'.json')).write_text(json.dumps({'approved': True,'reviewer':who,
                    'artifact_sha256': digest, 'required_issues': [],
                    'approval_scope': 'script_content'}), encoding='utf8')
            lock = {'script_path': 'script.md', 'script_sha256': digest,
                    'codex_receipt': 'codex.json', 'claude_receipt': 'claude.json'}
            path = root / 'locked_script.json'
            with self.assertRaises(p.GateError):
                p.check_gate(root, path, digest)
            path.write_text(json.dumps(lock), encoding='utf8')
            self.assertEqual(p.check_gate(root, path, digest)['script_sha256'], digest)
            lock['review_receipt_sha256']={'codex.json':'0'*64,'claude.json':hashlib.sha256((root/'claude.json').read_bytes()).hexdigest()}
            path.write_text(json.dumps(lock),encoding='utf8')
            with self.assertRaises(p.GateError):
                p.check_gate(root,path,digest)
            del lock['review_receipt_sha256']
            lock['claude_receipt'] = 'codex.json'
            path.write_text(json.dumps(lock), encoding='utf8')
            with self.assertRaises(p.GateError):
                p.check_gate(root, path, digest)
            lock['claude_receipt'] = 'claude.json'
            path.write_text(json.dumps(lock), encoding='utf8')
            (root/'claude.json').write_bytes((root/'codex.json').read_bytes())
            with self.assertRaises(p.GateError):
                p.check_gate(root,path,digest)
            (root/'claude.json').write_text(json.dumps({'approved':True,'artifact_sha256':'0'*64,
                'required_issues':[],'approval_scope':'script_content'}),encoding='utf8')
            with self.assertRaises(p.GateError):
                p.check_gate(root, path, digest)
            script.write_text('수정된 본문',encoding='utf8')
            with self.assertRaises(p.GateError):
                p.check_gate(root, path, digest)

    def test_unapproved_receipt_with_required_issue_never_passes(self):
        p = self.module()
        with self.assertRaises(p.GateError):
            p.validate_content_receipt({'approved':True,'checked_sha256':'a'*64,
                'approval_scope':'script_content','required_issues':[{'id':'OPEN'}]},'a'*64)

    def test_generate_entrypoint_blocks_before_output_or_network_when_lock_missing(self):
        self.module()
        source=SIDE/'production_generate.py'
        self.assertTrue(source.is_file())
        spec=importlib.util.spec_from_file_location('production_generate',source)
        generator=importlib.util.module_from_spec(spec);spec.loader.exec_module(generator)
        with tempfile.TemporaryDirectory(dir=SIDE) as tmp:
            root=Path(tmp);prepared=root/'prepared.json';out=root/'must-not-exist'
            prepared.write_text(json.dumps({'script_sha256':'a'*64}),encoding='utf8')
            generator.EP=root;generator.LOCK=root/'missing_locked_script.json'
            with self.assertRaises(generator.p.GateError):
                asyncio.run(generator.generate(prepared,out))
            self.assertFalse(out.exists())

    def test_manifest_workspace_path_accepts_relative_prepared_input(self):
        source=SIDE/'production_generate.py'
        spec=importlib.util.spec_from_file_location('production_generate',source)
        generator=importlib.util.module_from_spec(spec);spec.loader.exec_module(generator)
        self.assertTrue(hasattr(generator,'workspace_relative'),'상대 경로 최종 manifest 회귀 수정 전')
        path=SIDE/'prepare-v5/prepared.json'
        relative=path.relative_to(generator.ROOT)
        self.assertEqual(generator.workspace_relative(relative),relative.as_posix())

    def test_candidate_has_exactly_54_body_paragraphs_in_10_chapters(self):
        p = self.module()
        path = SIDE.parents[1] / 'writer/private-production-v1/script_v4_candidate.md'
        chapters = p.parse_script(path.read_text(encoding='utf8'))
        self.assertEqual([c['chapter'] for c in chapters],list(range(1,11)))
        self.assertEqual(sum(len(c['paragraphs']) for c in chapters),54)
        self.assertTrue(chapters[0]['paragraphs'][0]['text'].startswith('같은 아파트에서'))
        self.assertNotIn('최종영상용 후보', ''.join(x['text'] for c in chapters for x in c['paragraphs']))

    def test_money_percentage_decimal_year_and_protected_alias_readings(self):
        p = self.module()
        cases = {'S&P500':'에스 앤드 피 오백','ETF':'이 티 에프','2억5천만원':'이억 오천만 원',
            '2억4천400만원':'이억사천사백만 원','6억900만원':'육억구백만 원',
            '11.7%':'십일 점 칠 퍼센트','4.0%':'사 점 영 퍼센트','1.21배':'일 점 이일 배',
            '2006년':'이천육 년','2016년':'이천십육 년','2건':'두 건','30단지':'서른 단지'}
        for original, expected in cases.items():
            self.assertEqual(p.reading(original), expected, original)

    def test_original_cues_map_to_real_words_without_splitting_money(self):
        p = self.module()
        text = 'S&P500 ETF를 봅니다. 2억5천만원입니다.'
        spoken, mapping = p.pronounce(text)
        words = ['에스','앤드','피','오백','이','티','에프를','봅니다','이억','오천만','원입니다']
        events = [{'type':'WordBoundary','offset':i*2000000,'duration':1500000,'text':w}
                  for i,w in enumerate(words)]
        cues = p.word_cues(text,spoken,mapping,events,paragraph=1)
        self.assertEqual(p.norm(''.join(c['text'] for c in cues)),p.norm(text))
        self.assertTrue(any('2억5천만원' in c['text'] for c in cues))
        starts = {event['offset']/1e7 for event in events}
        ends = {(event['offset']+event['duration'])/1e7 for event in events}
        self.assertTrue(all(c['start_s'] in starts and c['end_s'] in ends for c in cues))
        bad = events[:-1]
        with self.assertRaises(ValueError):
            p.word_cues(text,spoken,mapping,bad,paragraph=1)

    def test_chapter_pcm_padding_frame_ceiling_and_final_spoken_hold(self):
        p = self.module()
        with tempfile.TemporaryDirectory(dir=SIDE) as tmp:
            root=Path(tmp);source=root/'p.wav'
            with wave.open(str(source),'wb') as out:
                out.setparams((1,2,24000,0,'NONE','not compressed'))
                out.writeframes(b'\x64\x00'*4800+b'\0\0'*19200)
            rec={'wave_file':str(source),'paragraph':1,'last_word_end_s':0.15,
                 'cues':[{'id':'p1c1','text':'본문','spoken_text':'본문','paragraph':1,
                          'start_s':0.0,'end_s':0.15,'timing_basis':'provider_word_boundary'}]}
            contract=json.loads((SIDE.parents[1]/'director/two-episode-production-v1/media_contract.json').read_text(encoding='utf8'))
            first=p.assemble_chapter(1,'첫 장',[rec],contract,root/'c01.wav')
            self.assertAlmostEqual(first['cues'][0]['start_s'],0.6)
            self.assertAlmostEqual(first['total_seconds'],2.0)
            last=p.assemble_chapter(10,'끝 장',[rec],contract,root/'c10.wav')
            self.assertGreaterEqual(last['total_seconds']-last['last_speech_end_s'],3.0)
            self.assertAlmostEqual(last['total_seconds'],6.7)
            self.assertEqual(last['pcm_frames']%800,0)


if __name__=='__main__':
    unittest.main(verbosity=2)
