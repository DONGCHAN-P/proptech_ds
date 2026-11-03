import json,hashlib
from pathlib import Path
from PIL import Image
q=Path(__file__).parent;ep=q.parents[1];repo=ep.parents[2];out=ep/'outputs/visual-review-v8'
def rd(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def wr(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
d=rd(out/'delivery_manifest.json');guard=rd(out/'layout_guard.json');mapping=rd(out/'note_replacement_map.json')
errors=[];checked=[]
for x in d['input_versions']+d['artifacts']+d['source_files']:
 p=repo/Path(x['path'])
 if not p.exists():errors.append(['missing',str(p)]);continue
 if sha(p)!=x['sha256']:errors.append(['hash',str(p)])
 checked.append({'path':x['path'],'sha256':sha(p),'bytes':p.stat().st_size})
pngs=sorted(p for p in out.glob('*.png') if p.name[:2].isdigit())
assert len(pngs)==9 and guard['passed'] and len(guard['checks'])==9
assert all(Image.open(p).size==(1920,1080) for p in pngs)
project=rd(ep/'outputs/production-v7-preview/project_v7.json')
notes=[x for x in project['visual_intervals'] if x.get('props',{}).get('mode')=='note']
original={(x['unit_id'],x['start_frame'],x['end_frame']) for x in notes}
mapped={(x['unit_id'],x['start_frame'],x['end_frame']) for x in mapping['intervals']}
assert len(notes)==37 and original==mapped and all(x.get('replacement_id') and x.get('message_specific_execution') for x in mapping['intervals'])
assert abs(sum(x['duration_frames'] for x in notes)/30-163.76666666666668)<1e-8
assert not errors
r={'status':'passed_for_representative_review_with_limits','required_unresolved':[],'critical_open':[],'script_sha256':'6ffc9fc4819460d4cf6f03fd3b28102e2864402b9965ca14e158230474963982','scope':'v8 대표3대체화면+6챕터PNG 및512px9종. 새로운전체본편/음성/encoded모션 검수아님','coverage':{'full_png_viewed':9,'mobile512_contactsheet_tiles_viewed':9,'chapter_contactsheet_tiles_viewed':6,'continuous_playback':False,'actual_listening':False,'new_full_mp4':'not produced'},'verified':['01 실제좌표대표점/5목적지·리더는노선아님·확정출입구아님 표시. 08:00기준 08:06출발→09:34도착=6분대기+88분경로=94분, 기존 research/commute-v6/report.md 예시와 직접대조','02 실제6단지대표점의중위가격11.275/9.2/8.5/8.45/8.375/7.45와 특정84㎡대5층이상 공고S5 776598000·S1 790380000·S4 873329000 별도배치.2025/26공고와2026Q3거래시점/옵션세금별도·시점타입차이 표시','03 실제S4_detail.svg와동일좌표기하의 상업/근린생활·초6유6·공원녹지하천시설면강조. 학교보조/현재개장개교아님/계획변경가능 표시','6개챕터 01일자리02교통03가격04주변가격비교05공급06생활시설, 제목대비/여백/한글정상. 각각 AI개념이미지·실제창릉모습아님표시 확인','본문3대표 흰자막박스·출처하단별도영역, 잘림/겹침없음. 모바일핵심수치·제목·자막확인','가드9/9passed를actual시안과대조; 원문/도형의의도적인겹침을텍스트잘림으로오판하지않음','원본v7 note37구간/25unit/163.7667초를mapping37/37에독립대조. 모든replacement_id/메시지별실행지시존재; 새확정시간으로사용하지않음','delivery_manifest 입력/산출물/소스SHA·파일존재·9PNG1920x1080자체검사'],'guard_states':9,'mapping':{'intervals':37,'units':25,'duration_s':163.76666666666668,'all_note_intervals_match_original':True,'source_video_sha256':'77fb48719ae2f78a98633ef072ec30c1d2cb323bde7a27724fa4f276bb5f98fc'},'files_checked':checked,'limits':['정지PNG만검수. 정확3초카드체류·전후전환·의미모션·새발화정렬은본편미제작으로미검증','37구간중3대표그룹시각검수이며나머지10메시지그룹은구체대체매핑만확인,실제렌더통과로승격하지않음','모바일축소에서출처·원문세부표시는작음; 핵심재표기수치/본문자막을확인','AI배경은범용개념이며실제단지/노선/학교/확정계획의증거가아님','새v8대본사용자확정대기. 무료유료음성·전체렌더·업로드권한확대없음'],'next_owner':'director/user script and representative review'}
wr(q/'visual_review.json',r)
h=rd(q/'handoff.json');h.update(status='script_and_representatives_passed_for_user_review',required_unresolved=[],next_owner='director/user review')
h['outputs']+=['qa/revision-v8/visual_review.json'];h['unresolved']=['user script-v8 approval pending','voice/fullvideo not produced','remaining10messagegroups actual render unverified','chapter3s actual dwell/transitions unverified']
wr(q/'handoff.json',h)
print(json.dumps({'status':r['status'],'required_unresolved':[],'files_checked':len(checked),'mapping_intervals':37},ensure_ascii=False))
