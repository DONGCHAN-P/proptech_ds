import importlib.util
from pathlib import Path
import re
import unittest

HERE=Path(__file__).resolve().parent


class CaptionV7Contracts(unittest.TestCase):
    def module(self):
        path=HERE/'repair_captions.py'
        self.assertTrue(path.is_file(),'의미구 orphan 수선 구현 전')
        spec=importlib.util.spec_from_file_location('caption_v7',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module

    def test_all_orphans_repaired_without_text_duplication_or_loss(self):
        r=self.module();old=r.p.load(r.SOURCE);new,changes=r.build()
        self.assertEqual(sum(r.is_short(c) for ch in old['chapters'] for c in ch['cues']),47)
        self.assertEqual(sum(r.is_short(c) for ch in new['chapters'] for c in ch['cues']),0)
        compact=lambda s:re.sub(r'\s+','',s)
        for a,b in zip(old['chapters'],new['chapters']):
            for key in ('text','spoken_text'):
                self.assertEqual(compact(''.join(c[key] for c in a['cues'])),compact(''.join(c[key] for c in b['cues'])))
        for ch in new['chapters']:
            for c in ch['cues']:
                self.assertIn(len(c['display_lines']),(1,2))
                self.assertEqual(' '.join(c['text'].split()),' '.join(' '.join(c['display_lines']).split()))
                self.assertTrue(all(r.width_ceiling(line)<=1600 for line in c['display_lines']))
        self.assertTrue(changes)

    def test_predicates_have_context_and_all_word_timing_is_actual(self):
        r=self.module();new,_=r.build()
        for ch in new['chapters']:
            previous=0
            for c in ch['cues']:
                self.assertNotIn(c['text'],['바뀝니다.','있습니다.'])
                self.assertGreater(c['end_s'],c['start_s'])
                self.assertGreaterEqual(c['start_s'],previous-1e-8);previous=c['end_s']
                self.assertLessEqual(c['end_s'],ch['total_seconds'])
                r.check_word_timing(ch,c)

    def test_audio_chapter_times_numbers_and_original_root_are_frozen(self):
        r=self.module();old=r.p.load(r.SOURCE);new,_=r.build()
        self.assertEqual(old['script_sha256'],new['script_sha256'])
        self.assertEqual(old['audio_revision'],new['audio_revision'])
        for a,b in zip(old['chapters'],new['chapters']):
            self.assertEqual({k:v for k,v in a.items() if k!='cues'},{k:v for k,v in b.items() if k!='cues'})
            for paragraph in {c['paragraph'] for c in b['cues']}:
                for token in r.p.TOKEN.findall(r.paragraph(paragraph)['text']):
                    self.assertTrue(any(token in c['text'] for c in b['cues'] if c['paragraph']==paragraph),token)

    def test_full_source_pronunciation_word_coverage_and_actual_audio_hashes(self):
        r=self.module();new,_=r.build();checks=r.validate(new)
        self.assertTrue(checks['passed'])
        self.assertEqual(checks['native_words'],2272)
        self.assertEqual(len(checks['paragraph_checks']),54)
        self.assertEqual(len(checks['audio_files_verified']),10)


if __name__=='__main__':unittest.main(verbosity=2)
