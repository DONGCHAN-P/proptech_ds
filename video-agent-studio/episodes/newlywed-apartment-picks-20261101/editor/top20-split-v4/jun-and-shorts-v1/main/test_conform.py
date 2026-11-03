"""Focused safety/meaning checks for source conform; no mocked render claims."""
import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from conform import Warp, windows, ass_time


class ConformContractTests(unittest.TestCase):
    def test_nonuniform_sentence_and_numeric_anchor(self):
        w=Warp([{'source_s':s,'target_s':t}for s,t in [(0,0),(2,3),(4,4),(8,10)]],10,8)
        self.assertEqual(w.source_at(3),2)
        self.assertEqual(w.source_at(4),4)
        self.assertEqual(w.source_at(7),6)
        self.assertNotEqual(w.source_at(4),4*8/10)

    def test_holds_do_not_advance_source(self):
        w=Warp([{'source_s':s,'target_s':t}for s,t in [(0,0),(2,2),(2,4),(5,7)]],7,5)
        self.assertEqual(w.source_at(3),2)
        self.assertEqual(w.source_at(5),3)

    def test_source_regression_rejected(self):
        with self.assertRaisesRegex(ValueError,'Non-monotonic'):
            Warp([{'source_s':0,'target_s':0},{'source_s':2,'target_s':3},{'source_s':1,'target_s':4}],4,1)

    def test_brand_exclusion_mask_covers_silent_gaps(self):
        self.assertEqual(windows({'brand_intro':{'start_s':6,'duration_s':5},
                                  'brand_outro':{'start_s':100,'duration_s':10}}),[(0.,6.),(11.,100.)])

    def test_ass_centisecond_rounding_carries_minutes(self):
        self.assertEqual(ass_time(59.999),'0:01:00.00')


if __name__=='__main__':
    unittest.main()
