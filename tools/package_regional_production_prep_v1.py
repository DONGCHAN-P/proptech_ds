"""Package the corrected silent preview while the scoped voice budget is pending."""
from pathlib import Path
import argparse,datetime as dt,hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1]
EP=ROOT/'video-agent-studio/episodes/regional-price-recovery-20261022'
OUT=EP/'outputs/production-v1-jun'
parser=argparse.ArgumentParser();parser.add_argument('--qa',required=True);args=parser.parse_args()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(ROOT).as_posix()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
qa_path=(ROOT/args.qa).resolve();qa_path.relative_to(EP/'qa/production-v1');qa=read(qa_path)
required=qa.get('counts',{}).get('required_open',qa.get('required_open_issue_count',qa.get('required_open_count')))
assert required==0,'Corrected preview QA must have no required issues'
tech=read(OUT/'checks/preview_technical_v2.json');video=ROOT/tech['combined_preview']['path']
assert sha(video)==tech['combined_preview']['sha256']
qtext=json.dumps(qa,ensure_ascii=False)
incheon=next(c for c in tech['clips'] if c['clip']=='incheon2008-2016recovery')
assert incheon['sha256'] in qtext and tech['combined_preview']['sha256'] in qtext,'QA must name the exact corrected media'
budget=read(EP/'outputs/production-v1-budget/budget_proposal.json')
decision=read(ROOT/'output/video_decisions/decisions/5fe307eed02c.json')
assert decision['status']=='pending','Budget state changed; handle that decision before this pending-budget handoff'
script=EP/'outputs/script-review-v3/script_v3.md';assert sha(script)==budget['script_sha256']
editor=read(EP/'editor/production-v1/handoff.json')
assert not editor['full_length_render_performed'] and editor['paid_or_cloud_generation_calls']==0
memo=(
'# 지역별 가격 회복 — 제작 현황\n\n'
'대본 v3를 기준으로 12장면·39문단의 편집 구성과 실제 데이터 차트 모션을 준비했습니다. 대표 장면 3개를 묶은 24초 무음 시안을 제공합니다. 본편의 실제 길이는 Jun 음성 확정 후 결정합니다.\n\n'
'시안은 ①2006년 이후 여섯 지역 가격 흐름 ②인천의 고점부터 최초 회복까지 ③전체 거래의 ㎡당 가격과 동일 단지·면적 지수 비교 순서입니다. 인천 지수 기준값과 회복일 라벨을 수정했습니다. 실제 MP4의 1080p·30fps·전체 디코드와 표본 프레임을 검수했습니다. 연속 재생·음성 청취·전체 본편 검수는 수행하지 않았습니다.\n\n'
f'Jun 원문은 {budget["input_characters"]:,}자·39문단입니다. 수정 여유를 포함한 한도 {budget["included_credit_cap"]:,}크레딧, 추가 결제0원·충전없음·자동재시도없음으로 제안했고 예산 승인을 기다립니다. 결정 ID는 `5fe307eed02c`입니다. `AGENTS.md`의 유료 생성 전 예산·상한 확인 규칙을 적용합니다. 실제 합성은 아직 실행하지 않았습니다.\n\n'
'승인 후 실제 음성·문자 정렬을 확보해 한 번 타임록하고, 자막·차트 동작·기존 브랜드와 음악을 연결해 본편을 렌더합니다. 마지막 발화3초 뒤 아웃트로가 시작합니다. 업로드 승인은 별도입니다.\n\n'
'원본과 이전 시안은 보존했습니다. 편집·합성 재개 명령은 작업폴더의 `editor/production-v1/README.md`, `narration/production-v1/README_prepared.md`에 있습니다.\n')
(OUT/'제작현황.md').write_text(memo,encoding='utf8')
files={'모션시안_v2_무음.mp4':video,'제작현황.md':OUT/'제작현황.md',
'대표프레임.png':ROOT/tech['contact_sheet'],'대본_v3.md':script,
'화면설계.md':EP/'outputs/script-review-v3/visual_storyboard.md',
'음성예산.json':EP/'outputs/production-v1-budget/budget_proposal.json',
'검수/수정시안_독립검수.json':qa_path,'검수/실제MP4_기술검사.json':OUT/'checks/preview_technical_v2.json',
'권리/emoji_LICENSE.md':OUT/'reusable_assets/emoji_LICENSE.md',
'권리/thinking_music.license.json':OUT/'reusable_assets/thinking_music.license.json'}
package={'at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'status':'corrected_silent_preview_awaiting_voice_budget',
 'script_sha256':sha(script),'qa_path':rel(qa_path),'qa_sha256':sha(qa_path),'required_open':0,
 'video':tech['combined_preview'],'voice_generated':False,'timing_locked':False,
 'files':{rel(p):{'sha256':sha(p),'bytes':p.stat().st_size}for p in files.values()}}
write(OUT/'prep_package_checks.json',package)
archive=OUT/'지역별회복_제작준비_v1.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED)as z:
    for name,p in files.items():z.write(p,name)
    z.write(OUT/'prep_package_checks.json','검수/패키지목록.json')
with zipfile.ZipFile(archive)as z:assert z.testzip()is None
write(OUT/'prep_archive_manifest.json',{'path':rel(archive),'sha256':sha(archive),'bytes':archive.stat().st_size})
state=read(EP/'state.json');state.update(stage='motion_preview_ready_awaiting_voice_budget',updated_at=package['at_utc'],
 production_preview=rel(video),production_preview_qa_file=rel(qa_path),production_preparation_package=rel(archive),
 budget_status='awaiting_5807_included_credit_cap_approval',audio_status='not_generated_budget_pending',timing_locked=False)
write(EP/'state.json',state)
pre=read(EP/'episode_preflight_production_v1.json')
pre['approvals']['budget'].update(decision_id=decision['id'],status='pending',credits_cap=5807,cash_cap=0,
 artifact_hashes={'narration_manifest':budget['narration_manifest_sha256'],'script_v3.md':budget['script_sha256']})
pre['qa'].update(preview_required_open_issues=0,evidence_paths=[rel(qa_path),rel(OUT/'checks/preview_technical_v2.json')],
 actual_encoded_frames='3representative_silent_clips_sampled;fullbody_not_rendered',required_open_issues='Preview required fixes closed; final voice/video QA not reached')
write(EP/'episode_preflight_production_v1.json',pre)
cfg=read(ROOT/'config/video_shelf.json');entry=next(e for e in cfg['entries']if e['name']=='지역별가격회복')
entry['status']='대본 v3 제작 확정 · 12장면39문단 준비 · 수정 모션시안 v2 24초 무음 · Jun 음성 예산 승인 대기 · 본편 타임록·전체 렌더 전. 대본보기.html은 이전 v1.'
entry['files'].update({'제작현황.md':rel(OUT/'제작현황.md'),'모션시안_v2_무음.mp4':rel(video),
 '모션시안_프레임.png':tech['contact_sheet'],'음성예산.json':rel(EP/'outputs/production-v1-budget/budget_proposal.json'),
 '제작준비자료.zip':rel(archive)})
write(ROOT/'config/video_shelf.json',cfg)
print(json.dumps({'status':package['status'],'required_open':0,'preview_bytes':video.stat().st_size,'archive_bytes':archive.stat().st_size},ensure_ascii=False))
