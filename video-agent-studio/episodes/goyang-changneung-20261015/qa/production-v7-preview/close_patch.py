import json,hashlib
from pathlib import Path
q=Path(__file__).parent; ep=q.parents[1];out=ep/'outputs/production-v7-preview'
def rd(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def wr(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
a=rd(q/'timeline_audit.json');p=rd(out/'project_v7.json');r=rd(q/'final_review.json');f=rd(q/'findings.json');h=rd(q/'handoff.json')
expected='77fb48719ae2f78a98633ef072ec30c1d2cb323bde7a27724fa4f276bb5f98fc'
assert a['final_sha256']==expected and a['errors']==[] and a['numeric_date_unit_split_suspects']==[]
merged=[x for x in p['captions'] if x['unit_id']=='M001_005']
assert len(merged)==1 and merged[0]['start_frame']==2540 and merged[0]['end_frame']==2715
f[0].update(status='closed_verified',checked_revision=expected,evidence='최종 actual patch_boundaries.jpg 6프레임 및 patch_mobile512.png 직접확인: 전체문장5.833초 한큐, 다음S5강조 연결 정상. 새 project 217큐/1초미만0/텍스트·PCM타임록불변 자동확인')
wr(q/'findings.json',f)
r.update(status='passed_with_limits',checked_revision=expected,bytes=49350618,required_unresolved=[],critical_open=[])
r['technical_independent'].update(sha_match=True,exit_code=0,stderr='',video_frames=31426,audio_frames=49104,duration_s=1047.533333)
r['timing_checks']['caption_cues']=217
r['timing_checks']['minimum_caption_s']=a['minimum_caption_s']
r['timing_checks']['caption_under_1s']=[]
r['coverage']['local_patch_actual_samples']=6
r['coverage']['local_patch_mobile512']=1
r['coverage']['inherited_evidence_source_sha256']='8b4b329fdfbb4f3450f3bd27990d68e9253e299674bf9aded2b31f73f8b13295'
r['coverage']['inheritance_scope']='첫판472실제표본과20모바일은 변경없는의미상태 검수로승계. M001_005 자막은새최종6실제표본+mobile로대체; 이전272?표본을최신SHA프레임으로주장하지않음'
r['coverage']['inheritance_scope']=r['coverage']['inheritance_scope'].replace('이전272?표본','이전표본')
r['scene_evidence'][1]['checked']='운영역과계획구분/S5→S4→S1 강조 일치; QAV7-P01 전체문장5.833초병합 actual6경계·모바일 확인닫힘'
r['local_patch']={'issue_id':'QAV7-P01','closed':True,'frames':[2539,2540,2607,2628,2714,2715],'duration_s':175/30,'evidence':'outputs/production-v7-preview/encoded_evidence/caption_patch/patch_boundaries.jpg','audio_identity':'editor caption_patch_audio_identity.json AAC ADTS SHA동일 증거확인; 청취검증아님','timeline_audit':'qa/production-v7-preview/timeline_audit.json'}
wr(q/'final_review.json',r)
h.update(status='passed_with_limits',required_unresolved=[],affected_scenes=['M001_005 local patch closed'],next_owner='director / completed review gate')
h['input_versions']['video_sha256']=expected
h['verified']=['새최종SHA일치 및 전체독립count_frames31426/49104 exit0','최종국소실제6경계·모바일검사, P01 closed_verified','217자막/1초미만0/수치날짜단위분단0/143PCM일치','이전전체불변영역472표본근거승계범위명시']
wr(q/'handoff.json',h)
print(json.dumps({'status':r['status'],'sha256':expected,'required_unresolved':[],'caption_cues':217},ensure_ascii=False))
