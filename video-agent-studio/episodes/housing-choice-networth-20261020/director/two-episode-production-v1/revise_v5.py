import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[5]
EP=Path(__file__).resolve().parents[2]
OUT=EP/'outputs/script-final-v5'
OUT.mkdir(parents=True,exist_ok=True)
source=EP/'writer/private-production-v1/script_v4_candidate.md'
before=source.read_text(encoding='utf-8')
old='이번 계산에서 투자수익은 연 6%로 놓았습니다. 영상의 집값·금리·임대료 조건을 유지하면서 그보다 높은 성과를 꾸준히 낼 수 있고, 전월세 주거비를 내면서도 차액을 계속 투자할 수 있다면 임차로 살며 금융자산을 키우는 선택이 더 유리해질 수 있습니다. 투자 역량과 실제로 이어갈 수 있는 저축 습관까지 내 상황에 맞춰 넣어봐야 합니다.'
new='이번 계산에서 투자수익은 연 6%로 놓았고, 앞에서 본 기본 조건에서는 전세와 월세의 순자산이 매매보다 크게 계산됐습니다. 전월세 주거비를 내면서 차액을 계속 투자하고, 이보다 높은 성과를 꾸준히 낼 수 있다면 같은 집값과 계약 조건에서 임차의 순자산 우위가 더 커질 수 있습니다. 투자 역량과 실제로 이어갈 수 있는 저축 습관까지 내 상황에 맞춰 넣어봐야 합니다.'
assert before.count(old)==1
after=before.replace(old,new,1).replace('버전: script-v4-candidate · 최종영상용 후보 · 독립 QA 대기 · 작성일 2026-10-26',
                                    '버전: script-final-v5 · 최종영상용 재검수본 · 작성일 2026-10-26',1)
risk='전세 갱신 때 보증금이 오르거나, 월세가 인상되거나, 투자시장이 하락한 시기에 이사해야 하는 경우도 같은 장부에 넣을 수 있습니다.'
assert after.count(risk)==1
after=after.replace(risk,risk+' 전세·월세는 계약이 끝날 때 보증금을 돌려받을 수 있는지도 함께 확인해야 합니다.',1)
target=OUT/'script_v5.md'
assert not target.exists()
target.write_text(after,encoding='utf-8')
record={'source':source.relative_to(ROOT).as_posix(),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'target':target.relative_to(ROOT).as_posix(),'target_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
        'changed':['CH10 P2: 기본 6%에서도 임차 순자산이 매매보다 큰 사실을 명시; 추가성과는 같은집값·계약조건에 한정',
                   'CH09 P4: 보증금 반환 여부 확인을 위험 비교에 추가', 'metadata version only'],
        'amounts_and_model_inputs':'unchanged','original_600_100_100_cost_bundles':'preserved',
        'claude_round1_required':'sec10-6pct-threshold-vs-base-rank addressed; recheck pending',
        'claude_recommended_market_rent_claim':'not adopted: no verified market-rate evidence supplied',
        'claude_recommended_cost':'existing explicit illustrative bundle and separate itemized-estimation statement retained',
        'tts_started':False,'final_media_approved':False}
(OUT/'changes.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record,ensure_ascii=False))
