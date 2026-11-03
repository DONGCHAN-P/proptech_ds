import sys; from pathlib import Path; sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import unittest
from collector.collect_three_cities import parse_page
class ParseTest(unittest.TestCase):
 def test_success(self):
  total,items=parse_page('<response><header><resultCode>000</resultCode></header><body><totalCount>2</totalCount><items><item/><item/></items></body></response>'); self.assertEqual((total,len(items)),(2,2))
 def test_error(self):
  with self.assertRaises(ValueError): parse_page('<response><header><resultCode>22</resultCode></header></response>')
 def test_missing_total(self):
  with self.assertRaises(ValueError): parse_page('<response><header><resultCode>000</resultCode></header></response>')
if __name__=='__main__': unittest.main()

