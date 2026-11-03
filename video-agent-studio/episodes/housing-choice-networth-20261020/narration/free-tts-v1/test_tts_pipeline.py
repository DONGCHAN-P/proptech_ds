"""Contract checks: unauthorized synthesis, Korean text spans and real PCM timing."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import wave

SIDE = Path(__file__).resolve().parent
SAMPLE = '육억원 집에서 십년을 비교합니다. 초기 순자산은 이억오천만원입니다.'


class PipelineContract(unittest.TestCase):
    def pipeline(self):
        source = SIDE / 'tts_pipeline.py'
        self.assertTrue(source.is_file(), '샘플 범위 잠금과 측정 파이프라인이 아직 없음')
        spec = importlib.util.spec_from_file_location('tts_pipeline', source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_arbitrary_script_cannot_enter_sample_synthesis(self):
        p = self.pipeline()
        p.assert_sample_scope(SAMPLE)
        for text in ('전체 대본을 생성합니다.', SAMPLE + '\n추가 문장입니다.'):
            with self.assertRaises(PermissionError):
                p.assert_sample_scope(text)

    def test_paragraph_sentence_spans_preserve_decimal_and_original(self):
        p = self.pipeline()
        text = '초기 순자산은 2.5억원입니다. DSR을 비교합니다.\n\n십년 뒤를 봅니다.'
        units = p.prepare_units(text, {'DSR': '디에스알', '2.5억원': '이억오천만원'}, 'fixture-r1')
        self.assertEqual([u['paragraph_id'] for u in units], ['P001', 'P001', 'P002'])
        self.assertEqual([u['original_text'] for u in units], [
            '초기 순자산은 2.5억원입니다.', 'DSR을 비교합니다.', '십년 뒤를 봅니다.'])
        self.assertEqual(units[0]['spoken_text'], '초기 순자산은 이억오천만원입니다.')
        self.assertEqual(units[1]['spoken_text'], '디에스알을 비교합니다.')
        for unit in units:
            self.assertEqual(text[unit['source_start']:unit['source_end']], unit['original_text'])
            self.assertIsNone(unit['meaningcue'][0]['start_s'])

    def test_boundary_coverage_and_duration_reject_missing_or_outside_speech(self):
        p = self.pipeline()
        events = [
            {'type': 'SentenceBoundary', 'offset': 1000000, 'duration': 29000000,
             'text': '육억원 집에서 십년을 비교합니다.'},
            {'type': 'SentenceBoundary', 'offset': 32000000, 'duration': 33000000,
             'text': '초기 순자산은 이억오천만원입니다.'},
        ]
        result = p.validate_boundaries(events, 7.0, SAMPLE)
        self.assertEqual(result['boundary_count'], 2)
        self.assertAlmostEqual(result['last_boundary_end_s'], 6.5)
        with self.assertRaises(ValueError):
            p.validate_boundaries(events[:1], 7.0, SAMPLE)
        with self.assertRaises(ValueError):
            p.validate_boundaries(events, 4.0, SAMPLE)

    def test_measured_time_map_uses_pcm_frames_without_text_duration_guess(self):
        p = self.pipeline()
        units = p.prepare_units('첫 문장입니다. 두 번째 문장입니다.', {}, 'fixture-r1')
        with tempfile.TemporaryDirectory(prefix='test-pcm-', dir=SIDE) as temp:
            files = {}
            for unit, frames in zip(units, (2400, 1600)):
                path = Path(temp) / (unit['unit_id'] + '.wav')
                with wave.open(str(path), 'wb') as out:
                    out.setparams((1, 2, 8000, 0, 'NONE', 'not compressed'))
                    out.writeframes(b'\0\0' * frames)
                files[unit['unit_id']] = path
            timeline = p.measure_units(units, files, 'fixture-a1')
        self.assertEqual([(u['start_s'], u['end_s']) for u in timeline], [(0.0, 0.3), (0.3, 0.5)])
        self.assertEqual(timeline[1]['meaningcue'][0]['end_s'], 0.5)
        self.assertEqual(timeline[0]['audio_revision'], 'fixture-a1')

    def test_native_small_overlap_is_reported_and_display_cue_is_trimmed(self):
        p = self.pipeline()
        events = [
            {'type': 'SentenceBoundary', 'offset': 1000000, 'duration': 36717105,
             'text': '육억원 집에서 십년을 비교합니다.'},
            {'type': 'SentenceBoundary', 'offset': 37217105, 'duration': 41703947,
             'text': '초기 순자산은 이억오천만원입니다.'},
        ]
        result = p.validate_boundaries(events, 7.896, SAMPLE)
        self.assertAlmostEqual(result['max_native_overlap_s'], 0.05)
        cues = p.display_boundaries(events)
        self.assertEqual(cues[0]['offset'] + cues[0]['duration'], 37217105)
        self.assertEqual(events[0]['duration'], 36717105)
        bad = [dict(events[0]), dict(events[1], offset=32000000)]
        with self.assertRaises(ValueError):
            p.validate_boundaries(bad, 7.896, SAMPLE)


if __name__ == '__main__':
    unittest.main(verbosity=2)
