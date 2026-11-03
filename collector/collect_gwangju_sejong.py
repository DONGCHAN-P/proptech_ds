"""Approved expansion; shared daily request ledger with prior three-city job."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import collector.collect_three_cities as worker
worker.CODES={'gwangju':['29110','29140','29155','29170','29200'],'sejong':['36110']}
worker.LEDGER=worker.OUT
worker.OUT=worker.ROOT/'raw/rtms_trade_expansion/gwangju_sejong'
if __name__=='__main__':worker.main()
