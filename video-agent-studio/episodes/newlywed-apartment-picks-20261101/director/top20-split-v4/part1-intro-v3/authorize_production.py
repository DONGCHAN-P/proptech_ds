"""Apply the user's '진행해줘' only to the immediately preceding intro v3 draft."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys
D=Path(__file__).resolve().parent;E=D.parents[2];R=E.parents[2]
sys.path.insert(0,str(R));from notify.video_decisions import write
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    dest=D/'production_authorization.json'
    if dest.exists():print('Already applied');return
    gate=read(D/'script_decision.json');assert gate['id']=='d884be1c4e38'and gate['status']=='pending'
    for a in gate['artifacts']:assert sha(R/a['path'])==a['sha256'],a['path']
    at=datetime.now(timezone.utc).isoformat()
    gate.update(status='approved',approved_at=at,response={'source':'same_conversation_direct_user_request','text':'진행해줘','applies_to':'immediately preceding intro v3 script and motion proposal'})
    write(D/'script_decision.json',gate);write(R/'output/video_decisions/decisions/d884be1c4e38.json',gate)
    auth={'status':'approved','approved_at':at,'decision_id':gate['id'],'user_request':'진행해줘',
      'scope':{'part':1,'revision':'intro-rationale-v3','changed_scene_ids':['P01-INTRO'],'free_InJoon_intro_voice_generation':True,
               'cash_cap_krw':0,'paid_generation_authorized':False,'upload_authorized':False,'external_file_export_authorized':False,'part2_production_authorized':False},
      'artifacts':gate['artifacts'],'existing_body_video':'outputs/top20-split-v4/part1/part1_free_v4.mp4',
      'existing_body_sha256':'9de0ac10a1d177b49da95b720d863f913fbf8ecc8cdb972a461eb02524b180b2',
      'approval_gates':['topic','script','budget','completed','pre_upload']}
    write(dest,auth)
    state=read(E/'state.json');state.update(phase='part1_intro_v3_production',pending_decision_id=None,active_new_intro_audio_generated=False,active_upload_authorized=False,updated_at=at)
    state['active_approval_status'].update(script='intro_v3_approved:d884be1c4e38',budget='free_only_cash_0',completed='not_reached_intro_v3',pre_upload='not_reached_part1')
    state['active_parts'][0].update(status='intro_v3_in_production');write(E/'state.json',state)
    write(D/'production_plan.json',{'request_type':'enhance_video','changed_scene_ids':['P01-INTRO'],'script_gate':'d884be1c4e38',
      'voice':'free ko-KR-InJoonNeural +0% then fixed atempo1.35','strategy':'new intro in HyperFrames; reuse approved encoded body beyond a verified keyframe; remux actual retimed audio and captions',
      'proofs':['actual new voice word alignment','seek-safe source checks','encoded intro frames and continuous motion frame strips','old/new body decoded equality and audio alignment','independent bounded QA'],
      'cash_cap_krw':0,'new_paid_calls':0,'actual_listening':False,'completed_gate':'new pending decision only after local file ready'})
    print(json.dumps({'status':'approved_intro_v3_free_production','decision_id':gate['id'],'part2':False,'uploads':False},ensure_ascii=False))
if __name__=='__main__':main()
