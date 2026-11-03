"""Correct only seven individually reviewed infographic Shorts; no blanket changes."""
from pathlib import Path
import json,sys,hashlib,argparse
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'analysis'))
from upload_changneung_scheduled_v8 import service
OUT=ROOT/'output/youtube_ai_disclosure/per_video_review_20261020'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
save=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assessment=read(OUT/'assessment.json')
ALLOW={'nfeT2nfDeS4','ETXkCHF4Si0','cY451x1_Fz4','Hz45kCsuuvo','JgOoB_-3XnI','7rRKo08NvWc','dIcVPPvpJVM'}
assert set(assessment['eligible_update_ids'])==ALLOW
for row in assessment['reviews']:
    if row['id'] in ALLOW:
        assert row['classification']=='clear_not_required' and row['recommended_setting'] is False
        assert hashlib.sha256((ROOT/row['video']).read_bytes()).hexdigest()==row['sha256']
parser=argparse.ArgumentParser()
parser.add_argument('--after-reauthorization',action='store_true')
args=parser.parse_args()
token_scopes=read(ROOT/'config/youtube-token.json').get('scopes',[])
assert any(s in token_scopes for s in ('https://www.googleapis.com/auth/youtube.force-ssl','https://www.googleapis.com/auth/youtube')), 'Edit scope required; no mutation attempted'
receipt_path=OUT/('changes_after_reauthorization.json' if args.after_reauthorization else 'changes.json')
receipt=read(receipt_path) if receipt_path.exists() else {'started_at':datetime.now(timezone.utc).isoformat(),'assessment_sha256':hashlib.sha256((OUT/'assessment.json').read_bytes()).hexdigest(),'videos':[]}
y=service()
channels=y.channels().list(part='id',mine=True).execute(num_retries=0)['items']
assert len(channels)==1 and channels[0]['id']=='UCr_mTC0x_Uobv6MrIsOkrXw'
keys=('privacyStatus','license','embeddable','publicStatsViewable','selfDeclaredMadeForKids','publishAt')
for ident in assessment['eligible_update_ids']:
    if any(r['id']==ident for r in receipt['videos']):continue
    before=y.videos().list(part='snippet,status',id=ident).execute(num_retries=0)['items'][0]
    assert before['snippet']['channelId']==channels[0]['id'] and before['status']['privacyStatus']=='public'
    row={'id':ident,'title':before['snippet']['title'],'before_status':before['status'],'phase':'update_started','requested_containsSyntheticMedia':False}
    receipt['videos'].append(row);save(receipt_path,receipt)
    try:
        status={k:before['status'][k] for k in keys if k in before['status']}
        status['containsSyntheticMedia']=False
        response=y.videos().update(part='status',body={'id':ident,'status':status}).execute(num_retries=0)
        row.update(phase='update_accepted',response=response)
        save(receipt_path,receipt)
        after=y.videos().list(part='snippet,status',id=ident).execute(num_retries=0)['items'][0]
        row['after_status']=after['status']
        row['other_metadata_preserved']=all(after['status'].get(k)==before['status'].get(k) for k in keys) and all(after['snippet'].get(k)==before['snippet'].get(k) for k in ('title','description','tags'))
        row['setting_readback']=after['status'].get('containsSyntheticMedia','not_returned_by_api')
        row['visible_label_check']='not_verified_in_Studio_or_player'
    except Exception as exc:
        row['phase']='error_no_automatic_retry';row['error_type']=type(exc).__name__;row['http_status']=getattr(getattr(exc,'resp',None),'status',None)
    save(receipt_path,receipt)
receipt['finished_at']=datetime.now(timezone.utc).isoformat()
receipt['accepted_count']=sum(r['phase']=='update_accepted' for r in receipt['videos'])
receipt['preserved_count']=sum(r.get('other_metadata_preserved',False) for r in receipt['videos'])
receipt['untouched_ids']=assessment['do_not_change_ids']+assessment['unchanged_existing_false_ids']
save(receipt_path,receipt)
print(json.dumps({'accepted':receipt['accepted_count'],'other_metadata_preserved':receipt['preserved_count'],'attempted':len(receipt['videos']),'label_visibility':'not_verified; API may omit disclosure property; no label absence claim'},ensure_ascii=False))
