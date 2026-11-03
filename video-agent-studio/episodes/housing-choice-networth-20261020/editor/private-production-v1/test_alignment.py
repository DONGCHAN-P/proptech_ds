"""Failure-oriented tests for text edits, split cues, and deleted-anchor handling."""
import sys
import unittest
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
from alignment import Alignment


def cues(*texts):
    return [dict(id=f'c{i}',text=t,start_s=3.5+i*2,end_s=5+i*2,paragraph=0) for i,t in enumerate(texts)]


class AlignmentTests(unittest.TestCase):
    def test_anchor_survives_cue_split_and_punctuation(self):
        a=Alignment(['집값은 6억원입니다.'],['집값은 6억원입니다.'],cues('집값은 6억원','입니다.'))
        self.assertEqual(a.locate('6억원입니다'),3.5)
        self.assertEqual(a.audit[-1]['cue_id'],'c0')

    def test_deleted_literal_fails_instead_of_zero(self):
        a=Alignment(['가상의 경고를 지웁니다.'],['실제 잔액을 계산합니다.'],cues('실제 잔액을 계산합니다.'))
        with self.assertRaises(ValueError): a.locate('가상의 경고')

    def test_positive_rewrite_has_explicit_audit(self):
        a=Alignment(['배당을 다시 더하면 중복입니다.'],['총수익에 배당이 포함됩니다.'],cues('총수익에 배당이 포함됩니다.'),{'배당을 다시 더하면':'총수익에 배당이 포함'})
        self.assertEqual(a.locate('배당을 다시 더하면'),3.5)
        self.assertEqual(a.audit[-1]['method'],'explicit_semantic_alias')

    def test_missing_display_text_cannot_pass(self):
        with self.assertRaises(ValueError): Alignment(['금액 6억원'],['금액 6억원'],cues('금액 5억원'))

    def test_long_insertions_use_equal_sequence_blocks(self):
        a=Alignment(['먼저 원금을 갚습니다. 다음 잔액을 확인합니다.'],['추가 설명입니다. 먼저 원금을 조금씩 갚습니다. 다음 잔액을 확인합니다.'],cues('추가 설명입니다. 먼저 원금을 조금씩 갚습니다.','다음 잔액을 확인합니다.'))
        self.assertGreaterEqual(a.locate('원금을 갚습니다'),3.5)
        self.assertEqual(a.audit[-1]['method'],'SequenceMatcher_equal_block')
        self.assertTrue(a.audit[-1]['review_required'])


if __name__=='__main__':unittest.main()
