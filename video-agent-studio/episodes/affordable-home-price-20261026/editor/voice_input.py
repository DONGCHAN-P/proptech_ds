"""Pinned formal v3 input; technical adoption does not authorize rendering."""
import sys
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build import EP,read,sha

TIMING=EP/'narration/production-injoon-v3/final_timing.json'
FORMAL=EP/'narration/handoff.production-v3.json'
TECHNICAL=EP/'narration/production-injoon-v3/technical_validation.json'
QA_PACKET=EP/'narration/production-injoon-v3/qa_packet.json'
EXPECTED='86a3c01e344f8c24da930404355b60d34eb9e1a0f49431cd299b5b38034939e7'

def load_voice():
    timing,formal,technical=read(TIMING),read(FORMAL),read(TECHNICAL)
    assert sha(TIMING)==EXPECTED==formal['final_timing_sha256']==technical['final_timing_sha256']
    assert not formal['required_technical_errors'] and not technical['required_technical_errors']
    assert technical['status']=='v3_delta_actual_technical_pass_pending_independent_ASR'
    assert timing['audio_revision']=='production-injoon-v3'
    total=sum(c['total_seconds'] for c in timing['chapters'])
    assert abs(total-formal['total_seconds'])<1e-8
    packet=read(QA_PACKET)
    assert packet['final_timing']['sha256']==EXPECTED and packet['technical_validation']['sha256']==sha(TECHNICAL)
    return timing,formal,technical

def spoken_overrides():
    return {t['scene_id']:t['spoken_expected'] for t in read(QA_PACKET)['targets']}
