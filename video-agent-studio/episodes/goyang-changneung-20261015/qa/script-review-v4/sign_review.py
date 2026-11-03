from pathlib import Path
import json,re,hashlib,datetime
q=Path(__file__).resolve().parent;ep=q.parents[1];o=ep/'outputs/script-review-v4';w=ep/'writer/script-v4'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
doc=(w/'script_v4.md').read_text(encoding='utf-8-sig')
assert doc==(o/'script_v4.md').read_text(encoding='utf-8-sig')
sc=json.loads((w/'scene_proposals.json').read_text(encoding='utf-8-sig'))['scenes']
chunks=re.findall(r'## (M\d+) · ([^\n]+)\n\n### 낭독\n\n(.*?)\n\n### 화면 지시',doc,re.S)
assert len(chunks)==len(sc)==10
for (sid,title,text),s in zip(chunks,sc):
 assert sid==s['scene_id'] and text.strip()==s['narration_text'].strip()
narr=(o/'narration_v4.txt').read_text(encoding='utf-8-sig')
parts=re.findall(r'\[(M\d+)\] [^\n]+\n\n(.*?)(?=\n\n\[M\d+\]|\Z)',narr,re.S)
assert len(parts)==10
for (sid,text),s in zip(parts,sc):assert sid==s['scene_id'] and text.strip()==s['narration_text'].strip()
assert '당첨자는 입주 준비로' in sc[0]['narration_text']
assert '예정 위치를 안내하는 권역' in sc[1]['narration_text']
assert '주변 기존 비교단지' in sc[4]['narration_text']
assert '2,277' in sc[6]['narration_text'] and 'S6' in sc[6]['narration_text']
files=[{'file':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in [o/'script_v4.md',o/'narration_v4.txt',o/'changes_v4.md',o/'changes_v4.txt',w/'script_v4.md',w/'scene_proposals.json',w/'claim_mapping.json']]
issues=[]
for i,scene,problem,fix in [
 (1,'M000','취득 검토 대상이 도입에 명확하지 않음','당첨자 입주 준비와 향후 취득·기존집 비교를 도입에 연결'),
 (2,'M004','동산동/삼송 대안의 가격을 도래울로 묶음','주변 기존 비교단지로 중립화'),
 (3,'M001','예정역 안내권역을 확정 계획구역처럼 부름','예정 위치를 안내하는 권역으로 수정')]:
 issues.append({'issue_id':f'SR4-{i:03}','scene_id':scene,'timecode':'새 음성 없음·타임코드 미확정','severity':'required','문제':problem,'evidence':'script_v4.md의 해당 장 낭독문 직접 대조','수정안':fix,'owner':'writer','status':'closed_text_verified','checked_revision':files[0]['sha256']})
(q/'findings.json').write_text(json.dumps({'revision':'script-v4-review','required_open_count':0,'critical_open_count':0,'findings':issues},ensure_ascii=False,indent=2),encoding='utf-8')
r={'revision':'script-review-v4','reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'required_open_count':0,'critical_open_count':0,'review_ready':True,'reviewed_file':files[0]['file'],'sha256':files[0]['sha256'],'script_file':files[0]['file'],'script_sha256':files[0]['sha256'],'files':files,'text_synchronization':{'writer_output_script_identical':True,'scene_narration_identical':True,'plain_narration_identical':True,'scene_count':10},'checks':{'취득전제_도입결론일치':True,'원흥역열차구간_현관총시간구별':True,'S4가격차_원값반올림_결론회수':True,'세후보2277부분합_S6이른일정':True,'S5미검증전체방위삭제':True,'기산_상품분리':True,'각장판단문장_종합판':True,'지도실제기능_권역정밀도구별':True},'intro':{'characters_with_spaces':len(sc[0]['narration_text']),'estimated_seconds':sc[0]['estimated_duration_seconds'],'actual_audio_generated':False},'source_basis':['research/price-stage-v3/report.md','research/script-v4-addendum/report.md','research/script-v4-addendum/facts_addendum.json','writer/script-v3/script_v3.md','qa/editorial-review-v1/편집품질_독립검토.md'],'scope':'10개 장의 낭독문·화면 지시 1회 독립 검토와 필수 3건 수정 영향 대조. 가격 원값 및 차액, 공급규모 부분합, 통근 범위, 거래 기산·상품 분리 확인. 새 주장에 대한 전면 재조사 아님.','actual_video_review':False,'actual_listening':False,'continuous_playback':False,'timing_locked':False,'authorization':'대본 수정안 검토만 완료. 사용자 대본 승인·음성 생성·유료 실행·영상 제작·업로드 승인 아님.','limitations':['새 음성·새 영상은 없으므로 발음·실제 길이·시각 가독성·최종 동기화 미확인.','학교·교통·입주 일정은 기존 출처의 예정/목표 조건이며 미래 확정을 보증하지 않음.']}
(q/'final_review.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
h={'status':'대본 수정안 독립 검토 완료','next_owner':'director','outputs':[str(q/'final_review.json'),str(q/'findings.json'),str(q/'독립검토_메모.md')],'input_script_sha256':files[0]['sha256'],'required_open_count':0,'critical_open_count':0,'review_ready':True,'unresolved':[],'scope':r['scope'],'authorization':r['authorization'],'actual_video_review':False,'actual_listening':False}
(q/'handoff.json').write_text(json.dumps(h,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'script_sha256':files[0]['sha256'],'review_ready':True,'intro_characters':r['intro']['characters_with_spaces'],'intro_estimate_s':r['intro']['estimated_seconds']}))
