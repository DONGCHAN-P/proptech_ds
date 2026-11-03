from pathlib import Path
import json,hashlib
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/youtube_ai_disclosure/per_video_review_20261020'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
catalog=read(OUT/'shorts/catalog.json')
reviews=[]
for row in catalog:
    job=read(ROOT/row['job'])
    receipt_path=job.get('receipt')
    if not receipt_path:
        receipt_path='video-agent-studio/episodes/goyang-changneung-20261015/outputs/shorts-release-v2/upload_receipt.json'
    receipt=read(ROOT/receipt_path)
    assert receipt['video_id']==row['id']
    if receipt.get('sha256'):assert receipt['sha256']==row['sha256']
    newtown=row['id'] in ('JgOoB_-3XnI','7rRKo08NvWc','dIcVPPvpJVM')
    evidence=['analysis/shorts_v1.py','analysis/assemble_v12.py','video/out/newtown-v14-sources.md'] if newtown else [row['job']]
    if row['id']=='nfeT2nfDeS4': evidence+=['video/src/changneung-shorts-leader-v2/entry.tsx']
    if row['id']=='ACJcKe1Xs2c': evidence+=['video-agent-studio/episodes/hanam-gyosan-20261019/editor/shorts-leader-v1/entry.tsx','video-agent-studio/episodes/hanam-gyosan-20261019/qa/shorts-leader-v1/final_review.json']
    if row['id'] in ('ETXkCHF4Si0','cY451x1_Fz4','Hz45kCsuuvo'): evidence+=['video-agent-studio/episodes/namyangju-wangsuk-20261014/outputs/shorts-release-v1/manifest.json','video-agent-studio/episodes/namyangju-wangsuk-20261014/outputs/video-review-v8/music_mix_schedule.json']
    reviews.append({**row,'classification':'clear_not_required','reason':'Actual rendered samples and edit sources show data charts/map diagrams, or an attributed actual GTX station photograph; no photorealistic generated places/persons or impersonation. No generated music track identified. Generic narrator does not claim to be an identifiable real speaker.','audio_assessment':'Existing Jun narration. Newtown background is directly programmed sine/bell synthesis (no generative music model or sampled performance); music is not the focus.' if newtown else 'Existing Jun voice excerpts, map/chart visuals; no new generated music. Original source and composition reviewed; actual listening not performed.','source_evidence':evidence,'already_submitted_false_at_upload':row['id']=='ACJcKe1Xs2c','recommended_setting':False})
longs=read(OUT/'longforms/review.json')['reviews']
for v in longs:
    reviews.append({'id':v['video_id'],'classification':v['classification'],'recommended_setting':v['recommended_setting'],'reason':'Photorealistic AI-generated city footage is actually included in the branded intro/outro; Changneung/Gyosan also contain photographic generated chapter scenes. Concept-image caption does not remove the realistic-generated-scene criterion.','detailed_review':'output/youtube_ai_disclosure/per_video_review_20261020/longforms/review.json','intervals':v['intervals'],'sha256':v['sha256']})
reviews += [
 {'id':'8shvS0--yBQ','classification':'uncertain','recommended_setting':None,'reason':'Available local reference file is video-only. Do not infer the original upload lacks audio; original music provenance/full editing inputs not established. Leave unchanged.'},
 {'id':'smQdOqu8Fjg','classification':'uncertain','recommended_setting':None,'reason':'Private legacy Top3 upload has no matched source/render receipt in the reviewed project records. Leave unchanged rather than assert no disclosure-triggering assets.'}
]
inventory=read(OUT/'inventory.json')
assert {r['id'] for r in reviews}=={v['id'] for v in inventory['videos']}
data={'created_at':datetime.now(timezone.utc).isoformat(),'policy_url':'https://support.google.com/youtube/answer/14328491?hl=en','authorization':'Direct owner request: accurately review existing channel videos and change applicable settings. No blanket automatic false.','readback_limit':'Data API inventory omitted containsSyntheticMedia for every video; missing is not false. API update acceptance and UI label disappearance must be reported separately.','coverage':'Root viewed 32 actual encoded short frames plus generation/edit sources. Separate QA sampled decisive generated longform/intro scenes. Not continuous playback/listening.','reviews':reviews,'eligible_update_ids':[r['id'] for r in reviews if r['classification']=='clear_not_required' and not r.get('already_submitted_false_at_upload')],'unchanged_existing_false_ids':['ACJcKe1Xs2c'],'do_not_change_ids':[r['id'] for r in reviews if r['classification']!='clear_not_required']}
(OUT/'assessment.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'reviewed':len(reviews),'eligible_updates':len(data['eligible_update_ids']),'required':len(longs),'uncertain':2},ensure_ascii=False))
