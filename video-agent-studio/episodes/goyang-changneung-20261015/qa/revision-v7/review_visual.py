import json, hashlib, subprocess
from pathlib import Path
ep=Path(__file__).resolve().parents[2]
qa=Path(__file__).parent
out=ep/'outputs/visual-review-v7'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,o): p.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf-8')
probe=ep.parents[2]/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'
probe=Path('C:/projects/realestate_reco/video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe')
clips=[]
for name,n in [('supply_branch_6s.mp4',180),('restriction_events_6s.mp4',180),('chapter_title_3s_demo_4s.mp4',120)]:
 p=out/name
 r=subprocess.run([str(probe),'-v','error','-count_frames','-show_entries','stream=codec_type,codec_name,width,height,r_frame_rate,nb_read_frames','-show_entries','format=duration','-of','json',str(p)],capture_output=True,text=True)
 d=json.loads(r.stdout); assert r.returncode==0 and not r.stderr
 assert len(d['streams'])==1 and d['streams'][0]['codec_type']=='video' and int(d['streams'][0]['nb_read_frames'])==n
 clips.append(dict(file=name,sha256=sha(p),bytes=p.stat().st_size,probe=d,exit_code=r.returncode,stderr=r.stderr))
files=[p for p in out.glob('*.png') if p.name[:2].isdigit()]
assert len(files)==12 and len(list((out/'mobile').glob('*.png')))==12
inventory=[dict(file=str(p.relative_to(out)),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(files+list((out/'mobile').glob('*.png'))) ]
old=ep/'outputs/production-v6-ui-r5/changneung_full_v6_ui_r5.mp4'
assert sha(old)=='5763a26b875a06769347ff384908d01010adee9d7fcc60119f8e803001e3d5f4'
issues=json.loads((qa/'findings.json').read_text(encoding='utf-8-sig'))
issues=[x for x in issues if x['issue_id']!='QAV7-V01']
issues.append({'issue_id':'QAV7-V01','scene_id':'chapter demo / M002','timecode':'00:00–00:03; frames 0,75,89,90,119','severity':'required','문제':'최초 encoded demo는 제목과 본문을 동시 표시하여 독립 챕터 요구와 불일치','evidence':'수정 actual encoded sheet의 0/75/89f는 번호·제목만,90/119f는 동일 좌표 본문/자막/출처; 최종 mobile07도 직접 확인','수정안':'첫90f 독립카드 후 본문 전환','owner':'editor_v6','status':'closed_verified','checked_revision':clips[2]['sha256']})
write(qa/'findings.json',issues)
report={'status':'passed_with_limits','scope':'v7 대표 시각팩 12PNG + 12 mobile + 무음3클립. 새 전체본편 검수/승인 아님','script_sha256':'ceb9a4e443dc2d7b36cdf84f5c515fa726d501a85e04d82ca81a4439c894bbbc','required_unresolved':[],'critical_open':[],'coverage':{'representative_full_png':12,'mobile_512_png':12,'encoded_sample_frames':26,'encoded_samples_method':'3 contact sheets의 전26단계 직접 확인; chapter 수정판 5단계 재확인','continuous_human_playback':False,'actual_listening':False,'speech_alignment':'unchecked; UI용 샘플자막','whole_new_episode':'not produced / unchecked'},'verified':['통근15셀 각 분 단위와 대표좌표/현재 Google 예상 조건','6단지 실거래 중위가격 내림차순과 거래 건수 6/11/3/17/20/11; 2026Q3·83이상85미만·5층이상·해제제외','실제 대표점 지도/설명 단지 강조/긴 단지명 2행; 계획/실제 구분','입주→생활수요 및 매매임대대안 두 분기, 단계적 선 진행 확인. S6 별도430, 비교3후보 부분합2277','전매 당첨자발표일3년/거주 거주의무개시일3년 독립 기산; S3 LH환매 구조 별도. 임의 5년 없음','첫90프레임 독립 번호제목 카드; 90f부터 본문 고정좌표. 본문 자막과 하단 출처 분리','원문84AH 5층~최상층 기본형867190천원→867190000원, 확장6139천원→6139000원, 합873329000원','Claude 성공 receipt exit0와 기여/기각 내역 확인; source-only 성공 주장을 actual sample 진행 확인으로 보완','r5 기준본 SHA 불변 자체 확인'],'limits':['원문 표 전체와 출처 20px는 512px 축소에서 세부 판독이 어렵지만 핵심 금액 재표기/본문자막은 읽힘','새 음성/본편 없음. 발화 정렬·전 장면 연결·실제 청취·연속 인간재생 미검증','기존 연구팩 원문/권리/최신 정정본 검증 한계 승계; 새 전수 외부재조사 없음'],'technical_independent':clips,'files':inventory,'preserved_r5_sha256':sha(old),'guide_references':['guides/제작_기본가이드.md 최신2026-10-18','guides/사용자_피드백_이력.md 필요한 최신항목','editor/revision-v7/layout_contract.json'],'next_owner':'director/user script + visual review'}
write(qa/'visual_review.json',report)
h=json.loads((qa/'handoff.json').read_text(encoding='utf-8-sig'))
h['status']='script_and_representative_visual_independent_review_passed_with_limits'
h['outputs']=list(dict.fromkeys(h['outputs']+['qa/revision-v7/visual_review.json']))
h['unresolved']=[x for x in h['unresolved'] if x!='visual-review-v7 pending']
h['unresolved']+=['full new episode/audio alignment and continuous playback unchecked']
h['verified']+=['12 representative full PNG / 12 mobile / 26 encoded samples; QAV7-V01 closed on corrected actual clip','3 silent clips independent full count_frames decode; r5 SHA preserved']
write(qa/'handoff.json',h)
print(json.dumps({'status':report['status'],'required_unresolved':[],'clips':[(x['file'],x['sha256']) for x in clips]},ensure_ascii=False))
