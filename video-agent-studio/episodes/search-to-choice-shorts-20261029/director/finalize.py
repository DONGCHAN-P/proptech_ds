"""Finalize verified local deliverables; never publishes or changes remote videos."""
import hashlib,json
from datetime import datetime,timezone,timedelta
from pathlib import Path
EP=Path(__file__).resolve().parents[1];ROOT=EP.parents[2]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
video=EP/'outputs/regional_gap_84m2_v2.mp4'
checks=read(EP/'qa/encoded_v2/verification.json')
geometry=read(EP/'qa/source_geometry.json')
source=read(EP/'qa/source_numeric_comparison.json')
cli=read(EP/'qa/hyperframes_check_v2.json')
independent=EP/'qa/independent/findings.json'
handoff=EP/'qa/independent/handoff.json'
assert independent.is_file() and handoff.is_file(),'Independent QA artifacts pending'
assert checks['sha256']==sha(video)
assert checks['decode_exit']==0 and checks['decoded_frames']==900 and checks['potential_blank_frame_count']==0
assert checks['audio_clipped_samples']==0 and geometry['safe_area_failures']==0 and source['exact_source_mismatches']==0
assert cli['ok'] and not cli['browserSkipped']
# Final QA disposition is inspected by the director before invoking this script.
qa=read(independent);qa_handoff=read(handoff)
findings=qa if isinstance(qa,list) else qa.get('findings',[])
required=[r for r in findings if r.get('severity') in ['critical','required'] and not str(r.get('status','')).startswith(('closed','resolved','fixed','passed','verified','not_reproduced'))]
assert not required, 'Unresolved required independent findings'
assert qa['target']['sha256']==sha(video) and qa['open_critical_count']==0 and qa['open_required_count']==0
now=datetime.now(timezone(timedelta(hours=9))).isoformat()
state=read(EP/'state.json');state.update(phase='completed_local_delivery',revision='v2',final_file=str(video.relative_to(ROOT)),final_sha256=sha(video),final_qa='independent_sampled_frame_and_numeric_review',actual_listening_performed=False,continuous_playback_performed=False,updated_at_kst=now)
save(EP/'state.json',state)
scenes=read(EP/'scenes.json')
for scene in scenes:scene['status']='rendered_and_sampled_verified';scene['script_revision']='screen-v2'
save(EP/'scenes.json',scenes)
decisions=read(EP/'decisions.json');decisions.append({'id':'D07','choice':'quarter_range_labels_during_interpolation','basis':'타임랩스는 두 분기의 범위와 관측값을 연결한 흐름으로 표시. 거래 표본 수는 실제 시작·종점 홀드에서 표시.','revision':'v2'})
save(EP/'decisions.json',decisions)
pre=read(EP/'director/episode_preflight.json');pre['status']='completed_local_delivery_v2'
pre['qa'].update(timeline_font_bbox_and_stroke_all_cases='900 source frames; zero critical rect failures',actual_encoded_frames='12 sampled frames + 216x384 contact sheet',all_cut_boundaries_no_flash='boundary samples + full900-frame signal analysis; zero potential blank frames',protected_numbers_units_names='492 source CSV rows exact match; first/final prices and differences checked',full_decode='900 frames, exit0',actual_listening_performed=False,continuous_playback_performed=False,required_open_issues=0,evidence_paths=['qa/encoded_v2/verification.json','qa/source_geometry.json','qa/hyperframes_check_v2.json','qa/source_numeric_comparison.json','qa/independent/findings.json'])
save(EP/'director/episode_preflight.json',pre)
notes='''# 84㎡대 지역별 가격 격차 쇼츠 · 제작 결과

최종본: `regional_gap_84m2_v2.mp4` · 30초 · 1080×1920 · 30fps · H.264/AAC

주제는 **같은 전용84㎡대, 서울·경기 가격 차이의 20년**이다. 서울·경기·인천·부산·대구·대전의 실거래 중위가격을 같은0~14억원 축에서 보여주고, 서울−경기의 차이가2006Q1 1.16억원에서2026Q2 4.90억원으로 변한 점을 남긴다.

자료는6지역의84㎡이상85㎡미만 유효 거래2,075,440건,82분기×6지역=492개 집계다. 지역·분기마다 거래 단지·입지·연식 구성이 달라지는 거래가격 수준 비교이며, 자료 종점은2026-06-30이다. 화면 숫자는0.01억원 단위로 반올림하고 차이는 반올림 전 수치로 계산했다. 보간 구간은 두 분기 범위로 표시하며 실제 거래 건수는 시작·종점 홀드에만 표시한다.

## 참고와 협의

- 참고4편의 실제 프레임19장을 총괄이 확인했다. 연속 재생/실제 청취는 수행하지 않았다.
- Claude Opus4.8 / effort max와2차례 기획·문자 구성 검토를 진행했다. 응답·전달문·해시·모델 사용 기록은 `collaboration/`에 있다. Claude가 실제 렌더를 시청한 것으로 표시하지 않았다.
- 핵심 격차에 집중, 고정 행으로 라벨 교차 제거, 인천4.90억과 격차4.90억의 패널 분리, 반올림 통일, 고정 금액 열을 반영했다.
- 원본 참고물의 프레임·사진·음원은 결과물에 삽입하지 않았다. 내레이션 없이 직접 합성한 원본 로컬 BGM을 사용했다.

## 검수 범위

- 원본 집계CSV492행과 제작 데이터: 가격·표본 불일치0
- 소스900프레임의 실제 글자 경계: 안전영역 위반0
- HyperFrames v2 실제 브라우저 검사: 런타임·레이아웃·대비 오류0, 글자 대비116건 통과. 구조상 하위 구성 분리 권고3건은 인코딩/화면 오류와 구별해 보관
- MP4 전체900프레임 디코딩 오류0, 빈 화면 후보0, 오디오 클리핑0
- 실제 인코딩12개 시점, 두 장면과 전환·CTA·최종 프레임,216×384 축소 접촉표 확인
- 독립 QA의 실제 확인 범위/판정은 `qa/independent/findings.json`, `handoff.json`에 보관
- 실제 연속 재생과 음악 청취는 수행하지 않았으며 그 항목은 미확인으로 기록

## 위치와 재현

- 영상: `outputs/regional_gap_84m2_v2.mp4`
- 표지: `outputs/cover.png`
- 화면 대본: `writer/대본_화면문구.md`
- 설명문/제목: `outputs/업로드정보.md`
- 데이터/산출 정의: `research/chart_data.csv`, `research/facts.json`
- 참고 분석: `research/참고영상_분석.md`
- 편집 가능한 HyperFrames 프로젝트: `editor/project/`
- 생성/검수: `editor/build_project.py`, `qa/check_source.cjs`, `qa/inspect_render.py --version v2`

새 유튜브 업로드는 실행하지 않은 로컬 납품본이다. 기존 공개 영상/채널 설정은 변경하지 않았다.
'''
(EP/'outputs/제작결과.md').write_text(notes,encoding='utf-8')
# Keep a stable, discoverable user shelf without duplicating large media bytes.
cfgpath=ROOT/'config/video_shelf.json';cfg=read(cfgpath);name='84㎡_지역가격_쇼츠'
assert not any(e['name']==name for e in cfg['entries']),'Shelf entry already exists; inspect before updating'
rel=EP.relative_to(ROOT).as_posix()
cfg['entries'].append({'name':name,'status':'30초 데이터 쇼츠 v2 · 로컬 완성 · 표본 프레임/기술/독립 검수 기록 포함','workspace':rel,'files':{'영상.mp4':rel+'/outputs/regional_gap_84m2_v2.mp4','표지.png':rel+'/outputs/cover.png','대본.md':rel+'/writer/대본_화면문구.md','제작결과.md':rel+'/outputs/제작결과.md','업로드정보.md':rel+'/outputs/업로드정보.md','데이터.csv':rel+'/research/chart_data.csv','참고영상_분석.md':rel+'/research/참고영상_분석.md','Claude_1차협의.md':rel+'/collaboration/concept_v1_response.md','Claude_2차협의.md':rel+'/collaboration/revision_v2_response.md','독립검수.json':rel+'/qa/independent/findings.json'}})
save(cfgpath,cfg)
summary='''# 두 작업 결과 · 2026-10-29

## 1. 유튜브 채널 분석

- [HTML 보고서](유튜브_채널분석_20261029/보고서.html)
- [Markdown 보고서](유튜브_채널분석_20261029/보고서.md)
- 원본 API·CSV·재현 스크립트: `analysis/youtube_channel_review_20261029/`

소유자 YouTube Analytics/Data API를 실제 조회했다. 현재 공개19편을 확인했고, 처리된2026-10-02~10-25기간을 분석했다. 기간 조회8,439회·시청110.4시간이다. 본편 검색 유입이 본편 시청시간75.5%를 차지했고, 창릉·왕숙 두 본편이 전체 시청시간의77.0%를 만들었다. 영상별 유지율·초기3개 보고일·기기·검색어와8가지 인사이트/실행 순서를 담았다. 10월26일 이후 새 영상은 Analytics 처리 기간 밖이라 성공·실패 평가를 보류했다.

조회는 채널·영상 설정 변경 없이 수행했다. 확장 요청31개 중30개 성공, 특정 쇼츠 유지율1개는HTTP500이어서 오류 상태를 보존했다. 썸네일 CTR/노출수는 이번 수집에서 확보되지 않았다. 비공개 Analytics는 로컬 보관하고 Claude 전달문에서 제외했다.

## 2. 참고 쇼츠 기반 새 영상

- [최종 쇼츠 MP4](../영상/84㎡_지역가격_쇼츠/영상.mp4)
- [화면 대본](../영상/84㎡_지역가격_쇼츠/대본.md)
- [표지](../영상/84㎡_지역가격_쇼츠/표지.png)
- [제작·검수 정리](../영상/84㎡_지역가격_쇼츠/제작결과.md)
- [집계CSV](../영상/84㎡_지역가격_쇼츠/데이터.csv)
- [제목·설명문](../영상/84㎡_지역가격_쇼츠/업로드정보.md)
- [Claude1차](../영상/84㎡_지역가격_쇼츠/Claude_1차협의.md) · [Claude2차](../영상/84㎡_지역가격_쇼츠/Claude_2차협의.md)

주제: **같은84㎡대, 서울·경기 가격 차이의20년**. 6지역2,075,440건의 실거래,82분기의 흐름을30초 세로 데이터 쇼츠로 만들었다. 내레이션 없이 원본 BGM과 큰 숫자로 전달한다. 서울−경기 중위가격 차이1.16억→4.90억을 결론으로 남긴다.

글자 경계·숫자·분기 표시·실제 출력 표본·전환/엔딩·전체 디코딩·오디오 신호와 독립 검수를 마쳤다. 연속 재생·실제 음악 청취는 미실시다. 현재 로컬 납품이며 신규 업로드는 실행하지 않았다.
'''
(ROOT/'reports/20261029_작업결과.md').write_text(summary,encoding='utf-8')
manifest={'status':'completed_local_delivery','completed_at_kst':now,'task1_report':'reports/유튜브_채널분석_20261029/보고서.html','task2_video':str(video.relative_to(ROOT)),'sha256':sha(video),'bytes':video.stat().st_size,'qa_required_open':0,'private_analytics_sent_to_Claude':False,'new_paid_voice_music_image_calls':0,'uploaded':False,'summary':'reports/20261029_작업결과.md'}
save(EP/'director/completion.json',manifest);print(json.dumps(manifest,ensure_ascii=False))
