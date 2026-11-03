import json,re,hashlib
from pathlib import Path
q=Path(__file__).parent;ep=q.parents[1]
def rd(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def wr(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
script=ep/'outputs/script-review-v8/script_v8.md';t=script.read_text(encoding='utf-8-sig');sha=hashlib.sha256(script.read_bytes()).hexdigest()
assert sha=='6ffc9fc4819460d4cf6f03fd3b28102e2864402b9965ca14e158230474963982'
n=rd(ep/'writer/revision-v8/narration_packet.json');s=rd(ep/'writer/revision-v8/scene_proposals.json');a=rd(q/'script_audit.json')
assert n['script_sha256']==s['script_sha256']==sha
texts={m.group(1):m.group(2).strip() for m in re.finditer(r'## (M\d+) ·[^\n]*\n\n### 낭독\n\n(.*?)\n\n### 화면 지시',t,re.S)}
assert all(x['text']==texts[x['scene_id']] for x in n['scenes'])
assert a['all_numeric_tokens_unchanged'] and a['M008_absent']
wr(q/'findings.json',[{'issue_id':'QAV8-S01','scene_id':'shared visual direction','timecode':'script only','severity':'required','문제':'초기 공통화면지침은 최신사용자 GPT챕터배경 허용·분석번호체계와 반대','evidence':'최신6ffc9fc 공통헤더 직접확인: GPT개념배경허용·실제장소계획증거오인금지/메타순번과분석번호분리; scene_proposals동기화','수정안':'최신root확인기준 공통지침·패킷교정','owner':'writer_v7','status':'closed_verified','checked_revision':sha}])
r={'status':'passed_for_user_script_review','script_sha256':sha,'required_unresolved':[],'scope':'v7→v8 낭독 어미·호흡/동일정보와 최신공통화면지침만 좁은검수. 유저새확정 아님','verified':['9장면 순서 및 M008삭제유지','장면별 숫자토큰 전부v7동일; 통근/가격/시점/표본/세대·기산사건변경없음','합니다/하겠습니다/입니다 중심정보체로변경, 기존해요체종결잔존검색0 및 전낭독직접확인','S4가격수준가설≠상승률/S5경쟁/S1관찰·현재계획구분/공급부분합과두효과·서로다른3년기산 논리유지','학교보조비중9.61%, 주된후보기준기존수요·취득가격·접근성 유지','GTX개통월미정·S1개교미정 등 불확실성을 새사실로 승격하지 않음','GPT개념챕터배경허용과실제자료구분/본문큰텍스트카드대체 최신지시로동기화','대본·narration_packet·scene_proposals SHA일치와 낭독text동일'],'narration_characters':6543,'estimated_final_seconds':825.6,'estimate_basis':'기존Jun 문자/시간비율; 실측아님, 챕터체류별도','voice_generated_by_qa':False,'actual_listening':False,'rendered_full_episode':False,'limits':['새v8사용자확정대기; 음성/전체렌더/게시승인으로확대금지','문체전환후실제호흡·발음·정렬은새음성없어미검증','불변사실은기존v7검수승계; 전수재취득/외부API재조사없음'],'next_owner':'director/user; editor representative visual review'}
wr(q/'script_review.json',r)
wr(q/'handoff.json',{'status':'script_passed_visual_pending','outputs':['qa/revision-v8/script_review.json','qa/revision-v8/script_audit.json','qa/revision-v8/findings.json'],'input_versions':{'script_sha256':sha},'required_unresolved':[],'unresolved':['user script-v8 approval pending','visual representatives pending','voice/fullvideo not produced'],'next_owner':'editor_v6 representative handoff then QA'})
print(json.dumps({'status':r['status'],'script_sha256':sha,'required_unresolved':[]},ensure_ascii=False))
