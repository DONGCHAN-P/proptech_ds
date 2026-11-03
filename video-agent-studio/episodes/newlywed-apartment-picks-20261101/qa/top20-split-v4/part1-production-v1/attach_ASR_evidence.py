"""총괄이 만든 로컬 ASR 증거를 연결하며 실제 청취와 구분한다."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

Q=Path(__file__).resolve().parent
E=Q.parents[2]
D=E/'director/top20-split-v4/part1-production-v1'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
lock=read(D/'locked_timing.json')
expected={s['scene_id']:' '.join(v['reading_text'] for v in s['sentences']) for s in lock['scenes']}
evidence=[]
for model in ['small','medium']:
    for p in sorted((D/'evidence/asr'/model).glob('P01-*.json')):
        if model=='medium' and p.stem not in {'P01-INTRO','P01-R20','P01-R15'}:
            continue
        j=read(p)
        clip=Path(j['audio_file'])
        evidence.append(dict(model=model,scene_id=j['scene_id'],file=str(p),sha256=sha(p),timing_hash_matches=j['timing_sha256']==sha(D/'locked_timing.json'),expected_reading_exact=j['expected_reading']==expected[j['scene_id']],actual_clip_hash_matches=clip.exists() and sha(clip)==j['audio_sha256'],reported_external_transfer=j['external_audio_transfer'],actual_listening=False))
assert len([v for v in evidence if v['model']=='small'])==12
assert len([v for v in evidence if v['model']=='medium'])==3
assert all(v['timing_hash_matches'] and v['expected_reading_exact'] and v['actual_clip_hash_matches'] and not v['reported_external_transfer'] for v in evidence)
notes=[
 dict(scene_id='P01-INTRO',subject='통계 기준일',source='2024년 11월 1일',small='2024년 11월 1일',medium='2024년 11월 11일',decision='ASR 간 불일치. 원문·생성입력·native metadata의 1일 일치 확인. 실제 발음 청취 미확인.'),
 dict(scene_id='P01-INTRO',subject='53개 구',source='쉰세 개 구',small='신세 개구',medium='50세 개구',decision='두 ASR의 표기만으로 숫자 발음 오류를 확정할 수 없음. 53→쉰세 독립 값 복원 통과. 실제 청취 미확인.'),
 dict(scene_id='P01-INTRO / P01-R20',subject='20위',source='이십 위',small='22위 / 22는',medium='20위',decision='동일 음성에 대한 medium은20위 복원. small 표기만으로 재합성하지 않음.'),
 dict(scene_id='P01-R20',subject='쌍 수·가격',source='7,365쌍 / 8억9,900만원',small='7365상',medium='7,365 쌍 / 8억 9,900만원',decision='숫자 source/read/native coverage 정확. 음성 자연스러움 미확인.'),
 dict(scene_id='P01-R15',subject='8,016쌍',source='팔천십육 쌍',small='816상',medium='8016상',decision='medium이8016 복원. 쌍/상 표기 차이는 청취 없이 실제 발음 오류로 확정하지 않음.'),
 dict(scene_id='P01-R18',subject='GTX-A',source='지티엑스 에이',small='GTXA',medium=None,decision='원문·alias·provider metadata와 small의 노선명 인식은 부합. 발음 자연스러움 미확인.'),
]
out=dict(status='supporting_ASR_evidence_linked_not_listening_certificate',generated_at=datetime.now(timezone.utc).isoformat(),evidence=evidence,manually_read_scope='small/medium INTRO 전문; R20/R15 순위·쌍수·가격 관련 구간 및 small R18 GTX-A 구간. 그 외 장면은 해시·expected_reading 연결만 검사.',observations=notes,confirmed_pronunciation_defects=[],required_open_count=0,actual_listening=False,naturalness='unchecked',ASR_regenerated_by_QA=False,network_calls=0,files_changed_outside_QA=False)
path=Q/'ASR_support_review.json'
path.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
report=read(Q/'audio_script_review.json')
report['coverage']['ASR']='parent small12 + medium3 local files hash/timing/expected-reading linked; selected disagreement excerpts manually read; no QA rerun'
report['ASR_support']=dict(path=str(path),sha256=sha(path),actual_listening=False,confirmed_pronunciation_defects=0,notes='날짜·53개 구·20위·8016 인식 불일치는 ASR 증거의 한계로 기록. 재생성 근거로 확정하지 않음.')
(Q/'audio_script_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
handoff=read(Q/'handoff.json')
handoff['outputs'].append(str(path))
handoff['unresolved']=[v for v in handoff['unresolved'] if v!='parent_ASR_pending']
handoff['ASR_support_review_sha256']=sha(path)
(Q/'handoff.json').write_text(json.dumps(handoff,ensure_ascii=False,indent=2),encoding='utf-8')
assert read(Q/'audio_script_review.json')['ASR_support']['sha256']==sha(path)
print(json.dumps(dict(status=out['status'],small=12,medium=3,required_open_count=0,actual_listening=False,report_sha256=sha(Q/'audio_script_review.json')),ensure_ascii=False))
