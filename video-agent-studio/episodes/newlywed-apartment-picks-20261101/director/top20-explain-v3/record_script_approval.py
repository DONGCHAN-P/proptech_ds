"""Record the direct IDE-conversation approval of the exact delivered v6 script."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
D=Path(__file__).resolve().parent; E=D.parents[1]; R=E.parents[2]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=D/'script_decision.json'; d=read(p); gp=R/'output/video_decisions/decisions'/f'{d["id"]}.json';gate=read(gp)
    for a in d['artifacts']:assert sha(R/a['path'])==a['sha256'],a['path']
    assert sha(E/'writer/top20-explain-v3/script_v6.md')==d['script_sha256']
    assert sha(E/'writer/top20-explain-v3/scene_proposals_v6.json')==d['scene_sha256']
    stamp=datetime.now(timezone.utc).isoformat()
    approval={'source':'direct_user_instruction_in_current_IDE_conversation','text':'이대로 진행해줘',
              'context':'User open tab: 영상/신혼부부_지역별아파트/수정안_v3/대본_v6.md; previous assistant delivered exact v6 script and prototypes',
              'recorded_at':stamp,'gate':'script','decision_id':d['id'],
              'script_md_sha256':d['script_sha256'],'scene_json_sha256':d['scene_sha256'],
              'scope':'approve the delivered v6 content and proceed with free TTS, timed local video production and QA',
              'cash_cap_krw':0,'paid_generation_authorized':False,
              'telegram_deliverable_file_export_authorized':False,'youtube_upload_authorized':False,
              'completed_and_pre_upload_gates':'remain separate; no new approval inferred'}
    receipt=D/'script_approval.json'
    if receipt.exists():
        old=read(receipt);assert old['scene_json_sha256']==approval['scene_json_sha256'];approval=old
    else:write(receipt,approval)
    gate.update(status='approved',approval_source='direct_current_conversation',response=approval);write(gp,gate)
    d.update(status='approved',approval_receipt=receipt.relative_to(R).as_posix());write(p,d)
    state=read(E/'state.json'); state.update(phase='approved_v6_free_narration_and_production',active_revision='top20-explain-v3',
          active_script='writer/top20-explain-v3/script_v6.md',script_approval_receipt=receipt.relative_to(R).as_posix(),
          pending_decision_id=None,updated_at=stamp)
    state['active_approval_status']['script']='approved:'+d['id'];write(E/'state.json',state)
    write(D/'production_authorization.json',approval)
    print(json.dumps({'script_gate':d['id'],'status':'approved','artifacts_unchanged':True,'cash_cap_krw':0,'upload_approval':'separate'},ensure_ascii=False))
if __name__=='__main__':main()
