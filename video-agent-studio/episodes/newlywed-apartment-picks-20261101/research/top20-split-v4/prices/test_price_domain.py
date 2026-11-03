import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from price_domain import price_band,select_official

class PriceTests(unittest.TestCase):
    def test_exact_boundaries_belong_to_higher_band(self):
        for amount,expected in [(49999,0),(50000,1),(69999,1),(70000,2),(99999,2),(100000,3),(149999,3),(150000,4),(199999,4),(200000,5),(300000,5)]:
            self.assertEqual(price_band(amount),expected,(amount,expected))
    def test_invalid_prices_are_not_colored(self):
        for v in [0,-1,float('nan'),float('inf')]:
            with self.assertRaises(ValueError):price_band(v)
    def test_shared_address_is_not_an_arbitrary_point(self):
        a={'names_normalized':{'푸른마을'},'HSMP_INNB':'one'}
        b={'names_normalized':{'푸른마을'},'HSMP_INNB':'two'}
        self.assertIsNone(select_official([a,b],'푸른마을'))
        self.assertIsNone(select_official([a],'다른단지'))
        self.assertEqual(select_official([a],'푸른마을')['HSMP_INNB'],'one')

if __name__=='__main__':unittest.main()
