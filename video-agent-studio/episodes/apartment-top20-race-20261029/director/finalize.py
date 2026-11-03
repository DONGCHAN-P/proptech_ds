"""Publish local verified files to the shelf; no network or remote upload."""
import hashlib,json
from datetime import datetime,timezone,timedelta
from pathlib import Path
EP=Path(__file__).resolve().parents[1];ROOT=EP.parents[2]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
video=EP/'outputs/apartment_top20_race_v1.mp4';technical=read(EP/'qa/encoded/verification.json');source=read(EP/'qa/source_validation.json');data=read(EP/'research/data.json');timing=read(EP/'editor/timing.json');cli=read(EP/'qa/hyperframes_check.json')
qa=read(EP/'qa/independent/findings.json');handoff=read(EP/'qa/independent/handoff.json')
assert sha(video)==technical['sha256']
assert technical['decode_exit']==0 and technical['decoded_frames']==1704 and technical['potential_blank_frames']==0 and technical['audio_clipped_samples']==0
assert source['safe_area_issue_frames']==0 and source['stable_state_issue_frames']==0 and source['name_collision_frames']==0 and source['actual_position_change_segments']==78
assert cli['ok'] and not cli['browserSkipped']
assert qa['verdict']['required_open']==0 and qa['verdict']['critical_open']==0
assert sha(video)==qa['artifact']['sha256']==handoff['input_sha256']
now=datetime.now(timezone(timedelta(hours=9))).isoformat()
state=read(EP/'state.json');state.update(phase='completed_local_delivery',final_video=str(video.relative_to(ROOT)),final_sha256=sha(video),duration_s=56.8,independent_qa='sampled_encoded_frames_and_scoped_numeric_review',actual_listening_performed=False,continuous_playback_performed=False,updated_at_kst=now);save(EP/'state.json',state)
scenes=read(EP/'scenes.json')
for scene in scenes:scene['status']='rendered_and_scoped_verified';scene['message']='전체 수집 대상에서 다시 선정되는 단지별 중위가격 TOP20의 진입·추월·이탈'
save(EP/'scenes.json',scenes)
pre=read(ROOT/'video-agent-studio/templates/episode_preflight.json');pre.update(episode_id=EP.name,status='completed_local_top20_delivery')
pre['input_contract'].update(narration_mode='none_original_local_BGM',timing_basis='frame-authored30fps',episode_specific_choices=['moving20complexrows','all eligible collected complexes reselected each quarter','84<=area<85;trailing4quarters;minimum5trades','56.8s;final8sheld'],superseded_historical_defaults=['previous fixed six region rows replaced by direct user request','52px key-value default adjusted for explicit 20-row view','spoken-word outro rule not applicable; no voice'])
for key in ['topic','script','completed']:pre['approvals'][key]['status']='delegated_by_user_no_intermediate_checkpoints'
pre['approvals']['budget'].update(status='no_new_paid_generation',credits_cap=0,cash_cap=0)
pre['approvals']['pre_upload']['status']='out_of_scope_local_delivery'
pre['story'].update(opening_question='2006→2026,어떤단지가올라왔을까?',order=['initial_top20','rank_race','major_leader_changes','final_top20','subscribe_like_CTA'],each_section_answers=['period','area','rolling_window','n','rank'],candidate_scope='all identifiable collected complexes in seven regions')
pre['qa'].update(timeline_font_bbox_and_stroke_all_cases='1704frames_safe0',actual_encoded_frames='sampled initial/final/leader/entry transitions',protected_numbers_units_names='1580 median/n/rank claims verified by separate research algorithm; scoped independent QA',all_cut_boundaries_no_flash='full1704frame_signal+sampled_boundaries',full_decode='exit0_1704frames',continuous_playback_performed=False,actual_listening_performed=False,required_open_issues=0,evidence_paths=['research/validation.json','qa/source_validation.json','qa/hyperframes_check.json','qa/encoded/verification.json','qa/independent/findings.json'])
save(EP/'director/episode_preflight.json',pre)
notes=f'''# 단지 중위가격 TOP20 쇼츠 · 제작 결과

최종본: `apartment_top20_race_v1.mp4` ·56.8초·1080×1920·30fps·H.264/AAC

사용자 수정에 따라 지역 고정행을 **단지별 순위 레이스**로 교체했다. 단지의 이름·색·동일DOM을 유지한 채 실제 새순위 위치로 이동한다. 진입 단지는 아래에서 올라오고 이탈 단지는 아래로 빠진다. 기존 지역별 영상은 보존했다.

## 실제 집계와 변화

- 수집7개지역(서울·경기·인천·부산·대구·대전·세종),식별가능12,470개단지·2,153,830건
- 전용84㎡이상85㎡미만,분기말최근4분기개별매매금액중위값,5건이상
- 2006Q4~2026Q2의79시점마다전체적격풀에서TOP20재선정.최종20개만과거에고정하지않음
- 등장단지127개,초기이후첫진입107건·재진입197건,1위교체13회
- 신규진입은랭킹진입이며준공·입주사실을대신하지않음
- 원명과표시명/위치매핑은`research/name_mapping.csv`. 원자료미관측기간은0원·전방채움으로만들지않음
- 원자료수집일은파일별로다르고공통계약종점은2026-06-30.5건과10건조건에따른끝점1위민감도는`research/sensitivity.json`

## 연출

첫화면의훅은‘1위가13번바뀌었다’.20개단지·가격·거래건수를함께보여준다. 2010Q4/2016Q3/2023Q3/2025Q4의실제주요교체에읽을시간을추가했다. 같은단지의위치가달라지는전환78개를구현했다. 교차중글자경계가맞붙는짧은구간은해당이름/숫자를가려겹침을줄이고막대이동은계속보여준다. 마지막TOP20은48.8~56.8초에8초정지하고마지막4초에구독·좋아요문구를유지한다.

20개행요청을유지하기위해57초로늘리고이름31px·가격32px·순위27px·보조건수/위치24px로설계했다. 이전6개행패널을통째로축소한구성이아니다. 내레이션없이직접만든원본BGM모티프를확장했고마지막1초페이드했다.

## Claude와 검수

Claude Opus/max로문자구성·익명단지집계를검토했다.7개지역표기·각행n·13회교체훅·속도조정의견을반영했다.TOP15축소제안은사용자TOP20요구를우선했다.소수1자리표시제안은실제중위금액의순서/화면상동률을구분하기위해2자리를유지했다.Claude가실제렌더를시청한것으로기록하지않았다.

- 연구담당이별도NumPy정렬방식으로79시점·1,580개가격/n/순위검산. 원천수집파일해시보존
- 소스1,704프레임:안전영역오류0,안정상태TOP20·위치/값오류0,이름충돌0
- 78개전환모두실제위치이동존재확인.숫자만바꾸는고정행이아님
- HyperFrames 실제브라우저검사:런타임/레이아웃/대비오류0,448개글자대비통과.단일장면의하위구성분리권고1건은구조권고로보관
- MP4전체1,704프레임디코딩오류0,빈프레임후보0,오디오클리핑0
- 실제MP4의최초/최종·대표1위교체2개·신규진입구간/모바일축소표본확인
- 독립검수범위·근거·미확인사항:`qa/independent/findings.json`/`handoff.json`
- 실제연속재생·음악청취·실기기재생은수행하지않았으며미확인으로기록

## 파일

- 영상:`outputs/apartment_top20_race_v1.mp4`
- 표지:`outputs/cover.png`
- 화면구성:`writer/화면구성.md`
- 업로드제목/설명:`outputs/업로드정보.md`
- TOP20·진입·1위변경CSV:`research/top20_quarterly.csv`,`entry_events.csv`,`leader_changes.csv`
- 재현:`editor/build_race.py`→HyperFrames프로젝트`editor/project/`
- 실제출력검사:`qa/inspect_render.py`

원본채널분석HTML은사용자요청대로기존개인텔레그램에전송했다.전송message_id376,전송파일32,276바이트.수신확인기록은`output/telegram_deliveries/youtube_channel_review_20261029.json`.

이영상은로컬납품본으로새유튜브업로드는실행하지않았다.
'''
(EP/'outputs/제작결과.md').write_text(notes,encoding='utf-8')
cfgpath=ROOT/'config/video_shelf.json';cfg=read(cfgpath);name='단지_TOP20_쇼츠';assert not any(e['name']==name for e in cfg['entries'])
for entry in cfg['entries']:
 if entry['name']=='84㎡_지역가격_쇼츠':entry['status']='이전 지역 비교안 · 사용자 단지 TOP20 수정 전 버전 보존'
rel=EP.relative_to(ROOT).as_posix()
cfg['entries'].append({'name':name,'workspace':rel,'status':'현재 수정본 · 단지TOP20실제순위레이스 ·56.8초·로컬납품','files':{'영상.mp4':rel+'/outputs/apartment_top20_race_v1.mp4','표지.png':rel+'/outputs/cover.png','화면구성.md':rel+'/writer/화면구성.md','제작결과.md':rel+'/outputs/제작결과.md','업로드정보.md':rel+'/outputs/업로드정보.md','TOP20_데이터.csv':rel+'/research/top20_quarterly.csv','단지명_매핑.csv':rel+'/research/name_mapping.csv','진입이벤트.csv':rel+'/research/entry_events.csv','Claude_검토.md':rel+'/collaboration/top20_direction_response.md','독립검수.json':rel+'/qa/independent/findings.json'}})
save(cfgpath,cfg)
summary=ROOT/'reports/단지_TOP20_쇼츠_제작결과_20261029.md';summary.write_text('# 단지 TOP20 쇼츠 수정 결과\n\n- [영상](../영상/단지_TOP20_쇼츠/영상.mp4)\n- [제작·검수·집계 기준](../영상/단지_TOP20_쇼츠/제작결과.md)\n- [TOP20 CSV](../영상/단지_TOP20_쇼츠/TOP20_데이터.csv)\n- [화면 구성](../영상/단지_TOP20_쇼츠/화면구성.md)\n\n56.8초 세로영상.7개수집지역12,470개단지의전용84㎡대최근1년중위가격·5건이상으로79시점전체TOP20을다시선정했습니다.단지가진입·추월·이탈하며실제위치가바뀝니다.1위교체13회,127개단지가등장합니다.최종순위8초유지.기존지역비교영상은보존했습니다.\n\n채널분석HTML보고서의개인텔레그램전송은완료했습니다(message376).\n',encoding='utf-8')
overview=ROOT/'reports/20261029_작업결과.md'
overview.write_text(overview.read_text(encoding='utf-8')+'\n\n## 사용자 후속 수정: 단지 TOP20\n\n지역 고정행 대신 단지가 실제 순위 위치로 이동하는 레이스로 재제작했습니다. [현재 수정본](../영상/단지_TOP20_쇼츠/영상.mp4) · [제작 정리](단지_TOP20_쇼츠_제작결과_20261029.md). 초기 지역 비교 MP4는 보존했습니다. 채널 보고서는 개인 텔레그램 전송을 완료했습니다.\n',encoding='utf-8')
receipt=read(ROOT/'output/telegram_deliveries/youtube_channel_review_20261029.json');assert receipt['ok'] and receipt['sent_bytes']==32276
completion={'status':'completed_local_delivery','completed_at_kst':now,'video':str(video.relative_to(ROOT)),'sha256':sha(video),'bytes':video.stat().st_size,'duration':56.8,'rank_snapshots':79,'ever_top20_complexes':127,'rank_motion_transitions':78,'telegram_report_message_id':receipt['message_id'],'qa_required_open':0,'new_paid_generation_calls':0,'uploaded':False,'summary':str(summary.relative_to(ROOT))};save(EP/'director/completion.json',completion);print(json.dumps(completion,ensure_ascii=False))
