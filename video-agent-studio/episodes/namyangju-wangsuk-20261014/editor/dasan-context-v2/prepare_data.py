import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
EP=ROOT/'video-agent-studio/episodes/namyangju-wangsuk-20261014'
rp=EP/'research/dasan-context-v2/context.json'
ctx=json.loads(rp.read_text(encoding='utf-8-sig'))
ctx['source_note']='다산역 주변 배치 · OSM 등록정보/운영사 안내 · 개별 입주·영업 현황을 뜻하지 않음'
preferred=[('다산역경기행복주택아파트',-200,-24),('다산자이 IVY PLACE',110,-36),('다산역자연앤푸르지오',130,20),('현대프리미엄아울렛 스페이스원',140,-20),('다산중앙공원',85,0),('다산선형공원',-310,20)]
ctx['display_labels']=[]
for name,dx,dy in preferred:
    candidates=[f for f in ctx['features'] if f['name']==name]
    if not candidates: continue
    feature=min(candidates,key=lambda f:(f['lon']-ctx['station']['lon'])**2*.626+(f['lat']-ctx['station']['lat'])**2)
    ctx['display_labels'].append(dict(feature,dx=dx,dy=dy))
old=ROOT/'video/public/namyangju-rail-route-proof-v1/proof_data.json'
data=json.loads(old.read_text(encoding='utf-8'))
data['dasanContext']=ctx
out=ROOT/'video/public/namyangju-rail-route-proof-v2/proof_data.json'
out.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
manifest={'input_master':'outputs/rail-route-proof-v1/namyangju_rail-route-proof_v1b.mp4','modified_clip_interval_s':[40.3,61],'original_interval_s':[134.3,155],'duration_s':80,'voice_and_bgm':'unchanged original_audio_94_174.wav','old_data_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),'context_sha256':hashlib.sha256(rp.read_bytes()).hexdigest(),'context_feature_count':len(ctx['features']),'buildings':len(ctx['buildings']),'roads':len(ctx['roads']),'label_count':len(ctx['display_labels']),'source_kind':'OSM registered neighborhood context, NOT statutory land-use plan','new_paid_generation':False,'full_video_modified':False}
(Path(__file__).parent/'input_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('prepared',len(ctx['features']),'polygons',len(ctx['display_labels']),'named labels')
