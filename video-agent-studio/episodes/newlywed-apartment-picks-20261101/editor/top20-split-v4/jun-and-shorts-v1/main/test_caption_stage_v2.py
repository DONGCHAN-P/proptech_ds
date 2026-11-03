import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
from caption_stage_v2 import body_windows,background_windows,enable


class CaptionBoxBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.d={'main_sentences':[{'start_s':.8}], 'last_spoken_end_s':668.73,
                'brand_intro':{'start_s':5.03,'duration_s':5},
                'brand_outro':{'start_s':671.73,'duration_s':10}}

    def test_box_hides_before_first_voice_and_after_last_voice(self):
        for got,expected in zip(body_windows(self.d),[(.8,5.03),(10.03,668.73)]):
            for a,b in zip(got,expected):self.assertAlmostEqual(a,b,places=9)

    def test_baked_old_boxes_still_cleared_during_silent_edges(self):
        for got,expected in zip(background_windows(self.d),[(0.,5.03),(10.03,671.73)]):
            for a,b in zip(got,expected):self.assertAlmostEqual(a,b,places=9)

    def test_frame_boundaries_are_half_open_and_keep_body_gaps(self):
        self.assertEqual(enable(body_windows(self.d)),
                         'between(n,24,150)+between(n,301,20061)')


if __name__=='__main__':
    unittest.main()
