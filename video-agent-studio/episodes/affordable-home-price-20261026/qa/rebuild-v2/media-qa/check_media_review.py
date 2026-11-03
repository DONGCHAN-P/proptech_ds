"""회귀: 경계 누락·짧은 큐 제외·원문순서 변경·소유범위 이탈을 잡는다."""
import copy
import importlib.util
import pathlib
import sys
import unittest

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('media_review', HERE / 'media_review.py') if (HERE / 'media_review.py').exists() else None
qa = importlib.util.module_from_spec(spec) if spec else None
if spec:
    spec.loader.exec_module(qa)


def fixture():
    ids = [f'R{i:03}' for i in range(1, 35)]
    scenes = [{'scene_id': sid, 'start_frame': i * 10, 'end_frame': (i + 1) * 10} for i, sid in enumerate(ids)]
    edl = {'clock': 'global_frames', 'fps': 30, 'total_frames': 340, 'scenes': scenes,
           'segments': [{'id': s['scene_id'], 'start_frame': s['start_frame'], 'end_frame': s['end_frame']} for s in scenes],
           'progressions': [{'kind': k, 'scene_id': sid, 'beat_frames': [i * 10 + 2, i * 10 + 5], 'timing_basis': 'native_word_boundary'} for i, (k, sid) in enumerate(zip(['funding_waterfall', 'ltv_dsr', 'monthly_budget'], ids))],
           'zoom': {'mode': 'fixed', 'max_frames': []}}
    return ids, edl


class CoverageTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(qa, '필수 수집기 media_review.py 미구현')

    def test_every_scene_caption_and_cut_is_sampled(self):
        ids, edl = fixture()
        cues = qa.parse_srt('1\n00:00:00,000 --> 00:00:00,100\n짧은 큐\n\n2\n00:00:00,100 --> 00:00:00,300\n긴 큐\n')
        plan = qa.make_plan(edl, ids, cues)
        tags = {t for row in plan for t in row['reasons']}
        self.assertIn('scene:R034:mid', tags)
        self.assertIn('scene:R034:final', tags)
        self.assertIn('caption:1:mid', tags)
        self.assertIn('caption:2:mid', tags)
        byframe = {row['frame_index']: row['reasons'] for row in plan}
        self.assertIn('cut:10:before', byframe[9])
        self.assertIn('cut:10:after', byframe[10])
        self.assertIn('cut:10:next', byframe[11])
        self.assertIn('scene:R034:final', byframe[339])

    def test_subframe_cue_selects_visible_frame_or_fails(self):
        ids, edl = fixture()
        plan = qa.make_plan(edl, ids, qa.parse_srt('1\n00:00:00,020 --> 00:00:00,040\n짧음\n'))
        self.assertIn('caption:1:mid', next(x['reasons'] for x in plan if x['frame_index'] == 1))
        with self.assertRaises(ValueError):
            qa.make_plan(edl, ids, qa.parse_srt('1\n00:00:00,001 --> 00:00:00,020\n표시 불가\n'))

    def test_exact_edl_cue_frames_survive_srt_millisecond_rounding(self):
        ids, edl = fixture()
        edl['cues'] = [{'id': 'R009Q001', 'start_frame': 80, 'end_frame': 83, 'text': '정밀 자막'}]
        cues = qa.parse_srt('1\n00:00:02,667 --> 00:00:02,767\n정밀 자막\n')
        plan = qa.make_plan(edl, ids, cues)
        self.assertIn('caption:1:mid', next(r['reasons'] for r in plan if r['frame_index'] == 81))
        bad = copy.deepcopy(cues)
        bad[0]['text'] = '다른 자막'
        with self.assertRaises(ValueError):
            qa.make_plan(edl, ids, bad)

    def test_reordered_or_missing_scene_rejected(self):
        ids, edl = fixture()
        for scenes in [edl['scenes'][:-1], list(reversed(edl['scenes']))]:
            bad = copy.deepcopy(edl)
            bad['scenes'] = scenes
            with self.assertRaises(ValueError):
                qa.make_plan(bad, ids, [])

    def test_gap_or_missing_progression_rejected(self):
        ids, edl = fixture()
        for field in ['segments', 'progressions']:
            bad = copy.deepcopy(edl)
            bad[field] = bad[field][:-1]
            with self.assertRaises(ValueError):
                qa.make_plan(bad, ids, [])

    def test_invalid_srt_and_unknown_zoom_rejected(self):
        with self.assertRaises(ValueError):
            qa.parse_srt('1\n00:00:01,000 --> 00:00:00,000\n뒤집힘\n')
        ids, edl = fixture()
        del edl['zoom']
        with self.assertRaises(ValueError):
            qa.make_plan(edl, ids, [])

    def test_all_scene_anchor_states_are_sampled_for_hidden_labels(self):
        ids, edl = fixture()
        edl['scenes'][28]['beat_frames'] = [282, 285]
        plan = qa.make_plan(edl, ids, [])
        byframe = {row['frame_index']: row['reasons'] for row in plan}
        self.assertIn('beat:R029:0:before', byframe[281])
        self.assertIn('beat:R029:0:onset', byframe[282])
        self.assertIn('beat:R029:1:settled', byframe[289])

    def test_one_actual_representative_can_be_reviewed_before_full_film(self):
        ids, edl = fixture()
        edl['scenes'] = edl['scenes'][:1]
        edl['segments'] = edl['segments'][:1]
        edl['progressions'] = edl['progressions'][:1]
        edl['total_frames'] = 10
        plan = qa.make_plan(edl, ids, [], scope='representatives')
        self.assertIn('scene:R001:final', next(x['reasons'] for x in plan if x['frame_index'] == 9))
        with self.assertRaises(ValueError):
            qa.make_plan(edl, ids, [], scope='full')

    def test_requested_opening_frames_are_not_lost_to_regular_sampling(self):
        ids, edl = fixture()
        edl['inspection_frames'] = [42, 73]
        rows = qa.make_plan(edl, ids, [])
        self.assertIn('requested_inspection', next(r['reasons'] for r in rows if r['frame_index'] == 42))
        self.assertIn('requested_inspection', next(r['reasons'] for r in rows if r['frame_index'] == 73))

    def test_writer_rejects_outside_qa_and_preserves_existing_run(self):
        with self.assertRaises(ValueError):
            qa.owned(HERE.parent / 'content_review.json')
        with self.assertRaises(ValueError):
            qa.new_run(HERE)


if __name__ == '__main__':
    unittest.main()
