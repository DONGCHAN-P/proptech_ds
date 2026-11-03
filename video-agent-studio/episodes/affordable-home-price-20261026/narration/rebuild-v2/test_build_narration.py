"""오프라인 계약 회귀 검사. fixture 승인은 이 소유 폴더 안 가상 episode에만 존재한다."""
import array
import asyncio
import copy
import importlib.util
import json
import math
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest import mock

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('build_narration_under_test', HERE/'build_narration.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def fixture(text='보유자금 2억5천만원으로 살 집을 살펴봅니다. 금리는 3.65%를 적용합니다.', anchor='금리는 3.65%를'):
    return {'revision': 'TEST_FIXTURE_NOT_APPROVED_SCRIPT', 'policy_as_of': '2026-10-26',
            'chapters': [{'id': 1, 'title': '현금'}],
            'scenes': [{'id': 'R001', 'chapter': 1, 'title': '시험 데이터', 'narration': text,
                        'graphic': {}, 'beats': [{'anchor': anchor, 'action': '강조'}] if anchor else [],
                        'source_ids': [], 'visual_notes': '오프라인 fixture, 외부 전송 금지'}]}


def events_for(text):
    # Explicitly synthetic. These timestamps are never evidence for new TTS timing.
    return [{'type': 'WordBoundary', 'text': token, 'offset': 1000000+i*7000000, 'duration': 5000000}
            for i, token in enumerate(text.split())]


class TextTests(unittest.TestCase):
    def test_minimal_normalization_and_unicode(self):
        q = m.prepare_data(fixture(), [])[0]
        self.assertIn('2억5천만원', q['spoken_text'])
        self.assertIn('삼점육오%', q['spoken_text'])
        self.assertEqual(m.number_spoken('4,902'), '\uc0ac\ucc9c\uad6c\ubc31\uc774')
        self.assertEqual(m.number_spoken('176.40'), '백칠십육점사영')
        self.assertEqual(m.number_spoken('0.06'), '영점영육')
        self.assertGreater(q['source_hangul_count'], 0)
        self.assertTrue(q['transforms'])

    def test_utf8_damage_rejected(self):
        for text in ('???? ????', '한글 ?? 손상입니다.', '한글 � 손상입니다.', '한글 ? ? ? 손상입니다.'):
            with self.assertRaises(m.BuildError):
                m.prepare_data(fixture(text, None), [])

    def test_scenes_array_order_is_timeline_even_if_ids_or_chapters_go_backwards(self):
        source = fixture()
        source['chapters'].append({'id': 2, 'title': '월 예산'})
        later = {**copy.deepcopy(source['scenes'][0]), 'id': 'R029', 'chapter': 2}
        source['scenes'] = [later, source['scenes'][0]]
        result = m.prepare_data(source, [])
        self.assertEqual([q['scene_id'] for q in result], ['R029', 'R001'])
        self.assertEqual([q['chapter'] for q in result], [2, 1])
        source['scenes'].append(copy.deepcopy(later))
        with self.assertRaises(m.BuildError):
            m.prepare_data(source, [])

    def test_decimal_is_not_sentence_boundary_and_short_sentence(self):
        self.assertEqual(len(m.sentence_spans('금리는 3.65%입니다. 감사합니다.')), 2)
        q = m.prepare_data(fixture('감사합니다.', None), [])[0]
        cues = m.align_sentence(q, events_for(q['spoken_text']))
        self.assertEqual(cues[0]['text'], '감사합니다.')
        q = m.prepare_data(fixture('집값과 매달 갚을 돈을 함께 확인하겠습니다. 감사합니다.', None), [])[0]
        cues = m.align_sentence(q, events_for(q['spoken_text']))
        self.assertEqual(cues[-1]['text'], '감사합니다.')

    def test_missing_duplicate_anchors_rejected(self):
        for source in (fixture(anchor='없는 원문'), fixture('금리를 봅니다. 금리를 봅니다.', '금리를')):
            with self.assertRaises(ValueError):
                m.prepare_data(source, [])

    def test_native_exact_anchor_no_interpolation(self):
        q = m.prepare_data(fixture('보유자금으로 집값을 계산합니다.', '보유자금'), [])[0]
        words = [{'text': '보유자금으로', 'start_s': 0.2, 'end_s': 0.8},
                 {'text': '집값을', 'start_s': 0.9, 'end_s': 1.1},
                 {'text': '계산합니다.', 'start_s': 1.2, 'end_s': 1.8}]
        covered = m.align_beats(q, words)
        self.assertEqual((covered[0]['start_s'], covered[0]['end_s']), (0.2, 0.8))
        self.assertFalse(covered[0]['anchor_matches_word_edges'])
        transformed = m.prepare_data(fixture(anchor='3.6'), [])[0]
        self.assertTrue(m.align_beats(transformed, [{'text': e['text'], 'start_s': e['offset']/1e7,
                      'end_s': (e['offset']+e['duration'])/1e7} for e in events_for(transformed['spoken_text'])]))
        q = m.prepare_data(fixture('보유자금으로 집값을 계산합니다.', '집값을'), [])[0]
        result = m.align_beats(q, words)
        self.assertEqual((result[0]['start_s'], result[0]['end_s']), (0.9, 1.1))

    def test_provider_mismatch_and_sentence_boundary_rejected(self):
        q = m.prepare_data(fixture(), [])[0]
        events = events_for(q['spoken_text'])
        self.assertTrue(m.align_sentence(q, events))
        events[0]['text'] = '다른말'
        with self.assertRaises(m.BuildError):
            m.align_sentence(q, events)
        events[0]['type'] = 'SentenceBoundary'
        with self.assertRaises(m.BuildError):
            m.align_sentence(q, events)

    def test_protected_amount_and_exact_source_spans(self):
        q = m.prepare_data(fixture('필요한 금액 6억 9천363만 원을 확인합니다.', None), [])[0]
        for cue in q['meaning_plan']:
            self.assertEqual(q['text'][cue['source_start']:cue['source_end']], cue['text'])
            self.assertLessEqual(len(cue['display_lines']), 2)
        self.assertTrue(any(q['text'][a:b] == '6억 9천363만 원' for a, b in q['protected_ranges']))

    def test_existing_real_wordboundary_regression(self):
        # Existing approved files are read only; this is not a new synthesis or listening check.
        previous = m.load(m.HERE.parent/'prepare-v2-r2/prepared.json')
        q = previous['chapters'][0]['paragraphs'][0]
        events = m.load(m.HERE.parent/'production-injoon-v3/paragraphs'/q['scene_id']/'native_boundaries.json')
        result = m.align_sentence(q, events)
        old = m.base.align(q, events)
        self.assertEqual([(c['text'], c['source_start'], c['source_end'], c['start_s']) for c in result],
                         [(c['text'], c['source_start'], c['source_end'], c['start_s']) for c in old])


class GateTests(unittest.TestCase):
    def setUp(self):
        fixtures = m.owned(HERE/'offline-tests')
        fixtures.mkdir(exist_ok=True)
        self.directory = m.owned(tempfile.mkdtemp(prefix='gate-fixture-', dir=fixtures))
        self.ep = self.directory/'FAKE_EPISODE'
        self.ep.mkdir()
        self.patcher = mock.patch.object(m, 'EP', self.ep)
        self.patcher.start()
        (self.ep/'writer/rebuild-v2').mkdir(parents=True)
        (self.ep/'director').mkdir()
        self.script = self.ep/'writer/rebuild-v2/fixture.json'
        self.script.write_text(json.dumps(fixture(), ensure_ascii=False), encoding='utf8')
        self.plan_dir = self.directory/'prepare'
        self.plan = m.prepare(self.script, self.plan_dir)
        self.prepared = self.plan_dir/'prepared.json'
        self.lock = self.ep/'director/fixture-lock.json'
        self.auth = self.ep/'director/fixture-auth.json'
        self.out = self.directory/'NEVER_GENERATE_REAL_AUDIO'
        self.lock_data = {'approved': True, 'episode_id': self.ep.name, 'script_revision': self.plan['revision'],
                          'script_path': m.relative(self.script), 'script_sha256': m.digest(self.script),
                          'claude_approved': True, 'review_reference': 'TEST_FIXTURE_ONLY_NOT_REAL_CLAUDE_REVIEW'}
        self.lock.write_text(json.dumps(self.lock_data), encoding='utf8')
        self.auth_data = {'approved': True, 'episode_id': self.ep.name, 'script_revision': self.plan['revision'],
                         'script_sha256': self.plan['script_sha256'], 'source': 'main_direct_instruction',
                         'instruction_reference': 'TEST_FIXTURE_ONLY_NOT_PARENT_APPROVAL', 'network_tts_authorized': True,
                         'provider': 'edge-tts', 'voice': m.VOICE, 'rate': m.RATE, 'external_payload': 'text_only',
                         'cash_cap_krw': 0, 'paid_calls_authorized': False, 'credentials_allowed': False,
                         'automatic_retries': 0, 'prepared_sha256': m.digest(self.prepared), 'lock_sha256': m.digest(self.lock),
                         'allowed_scene_ids': ['R001'], 'max_network_attempts': 1,
                         'command_argv': m.command_argv(self.prepared, self.lock, self.auth, self.out)}
        self.write_auth()

    def tearDown(self):
        self.patcher.stop()

    def write_auth(self):
        self.auth.write_text(json.dumps(self.auth_data), encoding='utf8')

    def check(self):
        return m.check_gate(self.prepared, self.lock, self.auth, self.out)

    def test_exact_fixture_gate_check_only(self):
        self.assertEqual(self.check()[0]['script_sha256'], m.digest(self.script))
        self.assertFalse(self.out.exists())

    def test_scope_and_paid_or_slow_voice_rejected(self):
        original = copy.deepcopy(self.auth_data)
        for key, bad in [('cash_cap_krw', 1), ('cash_cap_krw', False), ('paid_calls_authorized', True),
                         ('credentials_allowed', True), ('rate', '-15%'), ('max_network_attempts', 99),
                         ('script_sha256', '0'*64), ('prepared_sha256', '0'*64), ('automatic_retries', 1),
                         ('command_argv', ['unapproved command']), ('allowed_scene_ids', ['R002'])]:
            with self.subTest(key=key, bad=bad):
                self.auth_data = {**original, key: bad}
                self.write_auth()
                with self.assertRaises(m.BuildError):
                    self.check()

    def test_unapproved_claude_lock_rejected(self):
        self.lock_data['claude_approved'] = False
        self.lock.write_text(json.dumps(self.lock_data), encoding='utf8')
        self.auth_data['lock_sha256'] = m.digest(self.lock)
        self.write_auth()
        with self.assertRaises(m.BuildError):
            self.check()

    def test_missing_approval_no_dependency_or_provider_call(self):
        with mock.patch.object(m, 'dependencies', side_effect=AssertionError('must not reach provider')):
            with self.assertRaises(m.BuildError):
                coroutine = m.generate(self.prepared, self.ep/'director/missing.json', self.auth, self.out)
                try:
                    coroutine.send(None)
                finally:
                    coroutine.close()
        self.assertFalse(self.out.exists())

    def test_mutated_prepared_text_rejected(self):
        plan = m.load(self.prepared)
        plan['scenes'][0]['spoken_text'] += '추가'
        self.prepared.write_text(json.dumps(plan, ensure_ascii=False), encoding='utf8')
        self.auth_data['prepared_sha256'] = m.digest(self.prepared)
        self.write_auth()
        with self.assertRaises(m.BuildError):
            self.check()

    def test_write_ownership_guard(self):
        with self.assertRaises(m.BuildError):
            m.save(HERE.parent/'forbidden_test.json', {})


    def test_mocked_scene_once_preserves_PCM_and_accepts_natural_pauses(self):
        source = fixture()
        source['scenes'].append({**copy.deepcopy(source['scenes'][0]), 'id': 'R002'})
        self.script.write_text(json.dumps(source, ensure_ascii=False), encoding='utf8')
        self.plan = m.prepare(self.script, self.directory/'prepare-two')
        self.prepared = self.directory/'prepare-two/prepared.json'
        self.lock_data.update(script_sha256=m.digest(self.script))
        self.lock.write_text(json.dumps(self.lock_data), encoding='utf8')
        self.auth_data.update(script_sha256=m.digest(self.script), prepared_sha256=m.digest(self.prepared),
                              lock_sha256=m.digest(self.lock), allowed_scene_ids=['R001', 'R002'], max_network_attempts=2,
                              command_argv=m.command_argv(self.prepared, self.lock, self.auth, self.out))
        self.write_auth()
        called = []
        async def fake_synth(q, folder):
            called.append(q['scene_id'])
            folder.mkdir()
            events = events_for(q['spoken_text'])
            for i, event in enumerate(events):
                event['offset'] = 1000000+i*12000000
            end = (events[-1]['offset']+events[-1]['duration'])/1e7
            samples = array.array('h', [100]*math.ceil((end+0.4)*m.HZ))
            m.pcm_write(folder/'original.wav', samples)
            (folder/'original.mp3').write_bytes(b'OFFLINE_TEST_FIXTURE_NOT_REAL_MP3')
            m.save(folder/'WordBoundary.json', events)
            return samples, events, {'source_pcm_frames': len(samples), 'signal_start_s': 0,
                  'signal_end_s': len(samples)/m.HZ, 'first_word_start_s': 0.1, 'last_word_end_s': end,
                  'pcm_peak': 100, 'pcm_preserved': True, 'cues': m.align_sentence(q, events)}
        original_save = m.save
        def fixture_save(path, value):
            if isinstance(value, dict):
                value = {**value, 'TEST_FIXTURE_ONLY': True, 'actual_network_calls': 0,
                         'synthesis_function_mocked': True}
            original_save(path, value)
        with mock.patch.object(m, 'synthesize_scene', side_effect=fake_synth), mock.patch.object(m, 'save', side_effect=fixture_save):
            timing = asyncio.run(m.generate(self.prepared, self.lock, self.auth, self.out))
        self.assertEqual(called, ['R001', 'R002'])
        self.assertEqual(timing['total_cut_silence_s'], 0.25)
        self.assertAlmostEqual(timing['total_duration_s'], sum(s['duration_s'] for s in timing['scenes'])+0.25)
        self.assertTrue(any(gap['gap_s'] > 0.35 for s in timing['scenes'] for gap in s['natural_word_gaps']))
        self.assertGreaterEqual(timing['scenes'][-1]['tail_from_last_speech_s'], 3.0)
        self.assertEqual(m.load(self.out/'run_receipt.json')['network_attempts_started'], 2)
        schema = m.load(m.CONTRACT_PATH)['final_timing_schema']
        self.assertTrue(set(schema['required']) <= set(timing))
        for scene in timing['scenes']:
            self.assertTrue(set(schema['$defs']['scene']['required']) <= set(scene))
            for cue in scene['cues']:
                self.assertTrue(set(schema['$defs']['cue']['required']) <= set(cue))


if __name__ == '__main__':
    # Windows asyncio builds a loopback socket pair. All external connects are errors.
    original_connect = socket.socket.connect
    def offline_connect(sock, address):
        if isinstance(address, tuple) and address[0] in ('127.0.0.1', '::1'):
            return original_connect(sock, address)
        raise AssertionError('OFFLINE_TEST_EXTERNAL_NETWORK_FORBIDDEN')
    with mock.patch.object(socket.socket, 'connect', new=offline_connect):
        unittest.main(verbosity=2)
