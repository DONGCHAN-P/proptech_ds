import hashlib,json
from pathlib import Path
EP=Path(__file__).resolve().parents[1];ROOT=EP.parents[2]
def write(name,text):
 p=EP/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8')
def save(name,x):write(name,json.dumps(x,ensure_ascii=False,indent=2)+'\n')
facts=json.loads((EP/'research/facts.json').read_text(encoding='utf-8'))
save('brief.json',{'episode_id':EP.name,'title':'같은 84㎡대, 서울·경기 가격 차이의 20년','user_scope':'YouTube 채널 분석 후 참고 쇼츠 4개를 토대로 주제 선정·Claude 논의·쇼츠 제작. 중간 승인 없이 두 결과를 로컬 납품.','duration_s':30,'aspect':'9:16','voice_mode':'none_screen_data_with_original_BGM','cost_cap_new_paid_apis':0,'upload_requested':False,'studio_root':str(ROOT/'video-agent-studio'),'baseline':'affordable-home-price-20261026 public v3; channel typography and safe-area rules','guide':'video-agent-studio/guides/영상제작_마스터가이드.md'})
save('state.json',{'phase':'rendering_then_independent_qa','revision':'v1','topic_decision':'delegated_by_current_user','script_decision':'delegated_by_current_user','Claude_concept_review':'completed_text_packet_only_2_rounds','final_qa':'pending','actual_listening_performed':False,'continuous_playback_performed':False,'private_analytics_external_transmission':False})
scenes=[{'scene_id':'S01','message':'6지역 84㎡대 중위거래가의 시간 변화와 서울-경기 차이','start':0,'end':23,'subphases':{'2006_hold':[0,2.4],'quarter_timelapse':[2.4,19],'2026Q2_hold':[19,23]},'narration_text':None,'claim_ids':['C01','C02','C03'],'asset_ids':['chart_data','original_data_pulse'],'script_revision':'screen-v1','audio_revision':'original-data-pulse-v1','timing_basis':'frame-authored no-voice 30fps','status':'rendering'}, {'scene_id':'S02','message':'차이 1.16억→4.90억을 읽고 다음 지역을 제안','start':23,'end':30,'narration_text':None,'claim_ids':['C03'],'asset_ids':['chart_data','original_data_pulse'],'script_revision':'screen-v1','audio_revision':'original-data-pulse-v1','timing_basis':'frame-authored; conclusion hold7s; CTA4s','status':'rendering'}]
save('scenes.json',scenes)
save('decisions.json',[{'id':'D01','choice':'candidate_B','basis':'사용자가 주제와 판단 위임. 4개 참고의 차트/순위 문법, 기존 실거래 자료. Claude concept_v1 논의 반영.'},{'id':'D02','choice':'fixed_rows_not_rank_crossing','basis':'지역명/가격 교차 겹침 방지, 최종 인사이트는 절대 가격 차이.'},{'id':'D03','choice':'silent_narration_original_local_BGM','basis':'사용자 지정 참고 형식과 맞춤. 새 유료 API0원.'},{'id':'D04','choice':'no_external_private_Analytics','basis':'Claude에는 공개 참고물 관찰·지역 집계·제작안만 전송.'},{'id':'D05','choice':'rounded_prices_half_up_0.01_eok','basis':'Claude revision_v2 지적. 1.275억→1.28억. 최종 차이는 반올림 전 원자료로 계산.'},{'id':'D06','choice':'separate_difference_panel','basis':'인천 중위값4.90억과 서울-경기차이4.90억 혼동을 막도록 독립된 진한 카드·명시적 제목 사용.'}])
preflight=json.loads((ROOT/'video-agent-studio/templates/episode_preflight.json').read_text(encoding='utf-8-sig'))
preflight.update(status='applied_for_current_delegated_short',episode_id=EP.name)
preflight['input_contract'].update(narration_mode='none_original_BGM',timing_basis='frame_authored_30fps',episode_specific_choices=['data-first 30s vertical Short','six fixed rows','original local BGM','no upload requested'],superseded_historical_defaults=['new Jun voice not required for this data Short','newtown geography sequence does not apply'])
for gate in ['topic','script','completed']:preflight['approvals'][gate]['status']='delegated_by_current_user_no_intermediate_checkpoints'
preflight['approvals']['budget'].update(status='no_new_paid_calls',cash_cap=0,credits_cap=0)
preflight['approvals']['pre_upload']['status']='out_of_scope_local_delivery'
preflight['story'].update(opening_question='같은84㎡대,지역별가격은?',previous_episode_reference='지역 비교 채널의 강점과 예산 영상의 지역 가격 맥락',next_episode_promise='댓글로 다음 비교 지역 제안',order=['question','time_series','endpoint','absolute_difference','comment_CTA'],each_section_answers=['measure','period','region','difference'],candidate_scope='six_collected_regions')
preflight['qa']['last_speech_plus_three_seconds']='not_applicable_no_voice_CTA_hold4s'
save('director/episode_preflight.json',preflight)
write('writer/대본_화면문구.md','''# 같은 84㎡대, 서울·경기 가격 차이의 20년

30초 · 1080×1920 · 내레이션 없이 화면 문구와 원본 BGM으로 전달

| 시간 | 화면에서 말할 것 | 보여줄 자료/움직임 |
|---|---|---|
| 0–2.4초 | 같은 84㎡대, 지역별 가격은? / 2006Q1 / 서울−경기 차이 1.16억 | 실제 2006Q1 6지역 가격 막대. 첫 화면부터 자료가 보임 |
| 2.4–19초 | 각 분기의 지역별 중위가격과 서울−경기 차이 | 82개 분기 관측의 타임랩스. 지역은 고정 행. 수치·막대 비례·날짜 함께 변화 |
| 19–23초 | 2026Q2 / 서울10.70억·경기5.80억 / 차이4.90억 | 종점 4초 유지. 인천4.90억과 별도 차이 카드 구분 |
| 23–26초 | 20년이 흐른 뒤, 가격 차이는? / 서울−경기84㎡대 중위가격 차이 / 2006Q1 1.16억 → 2026Q2 4.90억 | 두 시점 금액을 읽을 크기로 나란히 연결. 다른 지역 가격 제거 |
| 26–30초 | 같은 면적대에서 확인한 지역 격차 / 다음 비교 지역은? 댓글로 남겨주세요 | 결론 유지. CTA만 진입한 뒤 고정. 마지막 음향 페이드 |

표시값은 억원 단위 소수 둘째 자리 반올림. 부산 최초값 1.275억원은 1.28억원으로 표시한다. 격차는 반올림 이전 원자료의 서울 중위값−경기 중위값으로 계산한다.

통계는 전용면적84㎡이상85㎡미만 아파트의 거래금액 중위값이다. 지역별로 거래된 단지·입지·연식 구성 변화가 포함된다. 가격 변동 원인이나 보유수익률을 주장하는 영상으로 만들지 않는다.
''')
write('editor/project/STORYBOARD.md','''---
duration: 30
music: original-local-data-pulse
captions: skipped (no narration; designed on-screen data labels carry all content)
---

## Video direction
Ink/cream/teal/orange channel design. First-frame data. One paused seek-safe timeline. Fixed six-row horizontal bars on one 0–14억원 scale. Graphic proportion and readable numeric columns. 82 observations drive time; interpolation is visual motion between quarterly observations. Every endpoint and start observation has a hold. Regions retain fixed identity and row position. No copied reference footage/music.

## S01 · 0–23s
Question → 2006Q1 hold2.4s → 82-quarter timeline through19s → final-quarter hold4s. Focal: measured transaction medians and separately labeled Seoul−Gyeonggi difference. Animation rules: stat-bars-and-fills, discrete-text-sequence. Registry: animated-bar-chart adapted with horizontal fixed rows. Guide-safe text rect140,260..840,1360.

## S02 · 23–30s
Absolute difference before/after, same teal/ink. Data conclusion available from23s; comment CTA26–30s. Static reading hold, original music resolves/fades. No late information after26s.
''')
write('research/참고영상_분석.md','''# 참고 영상 4편 분석

공개 영상 4개를 쿠키 없이 내려받고 FFmpeg로 실제 표본19장을 추출해 총괄이 확인했다. 연속 재생·실제 청취는 수행하지 않았다. 원영상의 투자·순위 수치 자체를 우리 영상 근거로 검증하거나 재사용하지 않았다.

| 참고 | 확인한 구간 | 구성 | 채택 |
|---|---|---|---|
| [MSFT 적립 차트](https://youtube.com/shorts/UguOzeTENco) | 0·1·4·8·12·18.5초 | 고정 제목, 날짜 진행, 선/면 차트, 투자금과 평가액 변화 | 시간 진행과 수치·도형 동시 변화, 종점 유지 |
| [대학 순위](https://youtube.com/shorts/rMKZ1AYdS78) | 0·0.8·4.5초 | 첫 프레임부터 완성표, 짧은 루프 | 처음부터 자료 제시. 43행 정보량은 6행으로 축소 |
| [브랜드 순위](https://youtube.com/shorts/Kmfn_lWwfUQ) | 0·2·6·10·14·20·25초 | 날짜별 막대 순위 경쟁, 색/사진 정체성 | 지역별 고유색과 시간 변화. 교차 라벨 겹침은 고정행으로 해결 |
| [부자 순위](https://youtube.com/shorts/xrPYY7tQvG8) | 0·1·4.5초 | 큰 제목, 숫자와 인물/기업 연결, 완성표 유지 | 큰 값과 항목명 연결. 사진과 원곡은 재사용하지 않음 |

프레임 접촉표와 추출 영상/메타데이터는 `research/references/<video_id>/`에 있다. 원본은 참고 검토용이며 결과물에 삽입하지 않았다.

## 선택 이유

단순 목록보다 변화 자체를 보게 한다. 기존 채널의 지역 비교 맥락을 이어가고, 84㎡대라는 공통 범위에서 거래 수준의 지역 차이를 보여준다. 새 예산 본편의 성공/실패는 Analytics가 아직 처리되지 않아 이번 선택의 근거로 사용하지 않았다.

Claude의 첫 의견: 순위 변화 자체보다 서울−경기 절대 격차를 남길 것. 두 번째 의견: 인천4.90억과 격차4.90억 구분, 소수자리 통일, 짧은 초기 막대 밖에 값 고정, 색만으로 지역을 구분하지 않을 것. 실제 화면 설계와 반올림 함수에 반영했다. Claude는 문자 구성·집계를 검토했으며 실제 렌더를 봤다는 기록은 남기지 않았다.
''')
write('outputs/업로드정보.md','''# 업로드용 정보

제목: 같은 84㎡대, 서울·경기 가격 차이의 20년 #Shorts

설명:
2006년 1분기부터 2026년 2분기까지, 수집한 6개 지역의 전용84㎡대 아파트 실거래 중위가격을 비교했습니다.

서울과 경기의 중위 거래가격 차이는 2006Q1 1억1600만원, 2026Q2 4억9000만원입니다.
서울·경기·인천·부산·대구·대전의 분기별 흐름을 같은 금액 축에서 볼 수 있습니다.

다음에는 어느 지역을 비교해 볼까요? 댓글로 남겨주세요.
지역의 차이를 데이터로 확인하고 싶다면 데이터로보는부동산을 구독해 주세요.

집계 기준:
- 기간: 2006Q1~2026Q2, 자료 종점2026-06-30
- 전용면적84㎡이상85㎡미만 아파트, 정제된 거래2,075,440건
- 각 지역·분기에 실제 거래된 아파트 금액의 중위값, 명목가격
- 분기마다 거래 단지·입지·연식의 구성이 달라지는 특성을 포함
- 자료: 국토교통부 실거래가를 수집한 프로젝트 고정 캐시. 해제표시/양수금액/면적/단지ID 확인 후 거래 해시 중복 제거. 대구 군위 제외. 캐시 이후 신고 정정은 이번 제작에서 갱신하지 않음
- 화면 금액: 0.01억원(100만원) 단위 반올림, 차이는 반올림 전 중위값으로 계산
- 관측 분기 사이의 막대·숫자는 시각적 보간으로 연결. 실제 분기 관측값은 별도 데이터에 보관
- 음악·도형·화면은 이번 작업에서 직접 제작

#실거래가 #아파트 #서울 #경기 #부동산데이터 #Shorts

현재 상태: 로컬 납품. 이번 요청에는 신규 유튜브 업로드가 포함되지 않았습니다.
''')
print(json.dumps({'documents':'written','episode':EP.name,'sources_total':facts['area84_sample_total']},ensure_ascii=False))
