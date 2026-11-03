import math
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
from caption_stage_v3 import body_windows,enable
import conform as c


class CaptionCueUnionTests(unittest.TestCase):
    def test_merge_only_overlap_or_touch_and_keep_inactive_gaps(self):
        d={'captions':[{'start_s':.8,'end_s':4.48},{'start_s':10.,'end_s':12.},
                        {'start_s':12.,'end_s':13.},{'start_s':12.5,'end_s':14.},
                        {'start_s':14.5,'end_s':15.}]}
        self.assertEqual(body_windows(d),[(.8,4.48),(10.,14.),(14.5,15.)])
        self.assertFalse(any(a<=5.<b for a,b in body_windows(d)))

    def test_actual_181_cues_have_exact_same_active_frame_union(self):
        d=c.read(c.LOCK);self.assertEqual(len(d['captions']),181)
        def frames(rows):
            active=set()
            for a,b in rows:active.update(range(math.ceil(a*30-1e-7),math.ceil(b*30-1e-7)))
            return active
        expected=frames([(x['start_s'],x['end_s'])for x in d['captions']])
        actual=frames(body_windows(d))
        self.assertEqual(actual,expected)
        for t in [.1,5.,669.53]:self.assertNotIn(round(t*30),actual)


if __name__=='__main__':
    unittest.main()
