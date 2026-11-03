"""Offline v3 plan checks only. Word events here are synthetic test fixtures."""
import asyncio
import importlib.util
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('repair',HERE/'repair_v3.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class DeltaPreparation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=m.r.load(m.PREPARED)
        cls.base=m.r.load(m.BASE_PREPARED)

    def test_only_four_spoken_rates_and_no_display_or_meaning_unit_changes(self):
        old=[q for ch in self.base['chapters'] for q in ch['paragraphs']]
        new=[q for ch in self.plan['chapters'] for q in ch['paragraphs']]
        self.assertEqual([q['scene_id'] for a,q in zip(old,new) if a['spoken_text']!=q['spoken_text']],m.TARGETS)
        timing=m.r.load(m.BASE/'final_timing.json')
        original=[c for ch in timing['chapters'] for c in ch['cues']]
        self.assertEqual(len(original),150)
        for a,q in zip(old,new):
            self.assertEqual(a['text'],q['text'])
            self.assertEqual(a['protected_ranges'],q['protected_ranges'])
            if q['scene_id'] not in m.TARGETS:self.assertEqual(a['display_mapping'],q['display_mapping'])
        fixed=[c for q in new for c in q['fixed_cues']]
        for before,after in zip(original,fixed):
            for key in ('text','source_start','source_end','display_lines'):self.assertEqual(before[key],after[key])
            self.assertEqual(before['id'].split('_',1)[1],after['id'])

    def test_independent_whole_amount_parser_preserves_values(self):
        for display,(spoken,value) in m.MONEY.items():
            units={'억':100000000,'만':10000,'원':1}
            expected=sum(int(n.replace(',',''))*units[u] for n,u in re.findall(r'(\d[\d,]*)\s*(억|만|원)',display))
            self.assertEqual(expected,value);self.assertEqual(m.korean_amount(spoken),expected)
        self.assertNotEqual(m.korean_amount('오억 백삼십만 원'),m.korean_amount('오억, 일백삼만 원'))
        self.assertNotEqual(m.korean_amount('사천구백이십만 원'),m.korean_amount('사천구백 이만 원'))
        self.assertNotEqual(m.korean_amount('십억 이천구백만 원'),m.korean_amount('십억, 이천구백 이만 원'))

    def test_all45_fixed_cues_align_without_source_loss_on_fixture_events(self):
        count=0
        for ch in self.plan['chapters']:
            for q in ch['paragraphs']:
                events=[{'type':'WordBoundary','text':word.group(),'offset':i*2000000,'duration':2100000}
                    for i,word in enumerate(re.finditer(r'\S+',q['spoken_text']))]
                cues=m.fixed_align(q,events);count+=len(cues)
                self.assertEqual(m.r.compact(''.join(c['text'] for c in cues)),m.r.compact(q['text']))
                self.assertEqual(m.r.compact(''.join(c['spoken_text'] for c in cues)),m.r.compact(q['spoken_text']))
        self.assertEqual(count,150)

    def test_original45_and_unchanged41_match_independent_Kant_pins(self):
        m.verify_pins(self.plan)
        packet=m.r.load(m.r.EP/'qa/audio-v1/v3_delta/target_packet.json')
        qa=m.r.load(packet['v2_raw_manifest']['path'])
        self.assertEqual(len(qa['entries']),45)
        own={x['scene_id']:x for x in self.plan['paragraph_pins']}
        self.assertEqual(sum(x['reused'] for x in own.values()),41)
        for item in qa['entries']:
            pin=own[item['scene_id']]
            for key,filename in (('audio','audio.wav'),('request','request.json'),('native_boundaries','native_boundaries.json')):
                self.assertEqual(item[key]['sha256'],pin['files'][filename])
        self.assertEqual(m.r.sha(HERE/'final_timing.json'),self.plan['base_final_timing_sha256'])

    def test_v2_authorization_cannot_enable_v3_network(self):
        with tempfile.TemporaryDirectory(dir=HERE,prefix='offline_v3_gate_') as temp:
            auth=Path(temp)/'v2_auth.json';auth.write_bytes(m.r.MAIN_AUTH.read_bytes())
            with patch.object(m,'AUTH',auth),patch.object(m.r,'dependencies',side_effect=AssertionError('Must not reach provider')):
                with self.assertRaises(m.r.p.GateError):asyncio.run(m.generate())
        self.assertFalse(m.OUT.exists())


if __name__=='__main__':unittest.main(verbosity=2)
