from pathlib import Path
import json,hashlib,subprocess
EP=Path('video-agent-studio/episodes/goyang-changneung-20261015');E=EP/'editor/revision-v8';O=EP/'outputs/visual-review-v8';E.mkdir(exist_ok=True);O.mkdir(exist_ok=True);D=O/'v7_actual_note';D.mkdir(exist_ok=True);p=json.loads((EP/'outputs/production-v7-preview/project_v7.json').read_text());units={x['unit_id']:x for x in json.loads((EP/'narration/preview-v7/segments.json').read_text())};movie=EP/'outputs/production-v7-preview/changneung_full_v7_preview.mp4';sha=hashlib.file_digest(movie.open('rb'),'sha256').hexdigest();assert sha=='77fb48719ae2f78a98633ef072ec30c1d2cb323bde7a27724fa4f276bb5f98fc'
def choice(uid):
 s,n=(uid.rsplit('_',1) if uid!='last_hold' else ('hold','0'));n=int(n)
 if s=='M000':return ('candidate_question','실제 S1·S4·S5 계획면+세 공고가 배지','세 후보의 위치와 확인된 공고가격 차이를 동시에 보여주는 질문 화면. 미래 순위·수익률은 수치화하지 않음.')
 if s=='M002':return ('commute_method','실제 출발3점·목적지5점 지도+08:00시계+접근/대기/환승 도식','실제 조회조건을 지도와 시간 기준으로 시각화. S4→강남08:06~09:34,08:00기준94분은 기존 조회의 예시로만 사용. 지도 선은 라벨 리더로만 사용.')
 if s=='M003':return ('rail_entry_evidence','기존 입주/철도달력과 실제 공고가3종의 병렬 비교','완만한 달력행 강조 후 7.77/7.90/8.73억 진입가격을 연결. 미래가격/수익률막대·가공가치차액 생성 금지.')
 if s=='M004' and n==9:return ('actual_price_delta','실제 S1·S4 공고가2막대+정확원/타입/공고일','S4-S1=82,949,000원, 약8300만원. 원문표의 출처/단위/선택행 연결. 미래차익으로 표시하지 않음.')
 if s=='M004' and n==10:return ('price_and_location','S4 실제면·기존생활시설지도+S5/S1 대비 실제공고가차이','입지접점과 공고가차이는 나란히 표시하고 인과/가치환산으로 연결하지 않음.')
 if s=='M004' and n==11:return ('original_price_conditions','기존 S4 공고원문 헤더/단위/84AH 선택행+날짜/타입 비교','정확원 환산·발코니 합산을 기존 검수된 원문표로 회수. 현재 취득가격은 신규숫자없이 별도확인 표시.')
 if s=='M004' and n in [12,13]:return ('entry_vs_existing_prices','세 공고가와 실제 주변6단지 중위값 지도','확인된 공고가 사례/주변 실거래 위치라는 서로 다른 근거를 분리. 대장/상승률 순위·미래 수익 숫자 없음.')
 if s=='M004' and n==14:return ('completion_evidence','실제 LH 후보면·공원·학교·업무용지+입주일정','계획면과 입주 예정 시점을 말할 때만 순차 강조. 가상 완공조감도/미래가격곡선 없음.')
 if s=='M004':return ('resale_descending','기존6단지 내림차순 실거래표→동일실제지도','기존 검수된6가격/거래건수를 그대로 연결.')
 if s=='M005' and n<=3:return ('life_parcels','실제 S4 상세필지의 상업·학교·공원면과 전체locator','구체적 시설면을 색으로 분리하고 말하는 항목만 강조. 실제개장/개교 확정처럼 표현하지 않음.')
 if s=='M005':return ('life_as_support','실제3후보면과 공고가/업무지표의 근거 썸네일','주기준(위치/진입가격/직장) 근거3개를 먼저, 학교 실제필지는 작은 보조로 유지. 새 이사달력 없음.')
 if s=='M009' and n==7:return ('commute_s4_comparison','기존3×5 현재통근표에서 S4열·해당목적지 강조','S4 모든 목적지 최단 아님을 실제15값으로 확인. 표/지도 겹치지 않음.')
 return ('series_evidence_cta','검증된 전편소스+창릉지도/가격표 썸네일과 채널CTA','교산은 다음편명만 편집텍스트로 표시. 검증되지 않은 교산 지도·현장 이미지 생성/삽입 금지. 마지막무발화홀드도 같은 근거화면 유지.')
rows=[];groups=[]
for x in p['visual_intervals']:
 if x['props'].get('mode')!='note':continue
 uid=x['unit_id'];design,asset,purpose=choice(uid);row=dict(unit_id=uid,start_frame=x['start_frame'],end_frame=x['end_frame'],start_s=x['start_frame']/30,end_s=x['end_frame']/30,duration_s=x['duration_frames']/30,narration=units.get(uid,{}).get('text','[마지막발화후무음홀드]'),caption=x['props'].get('caption',''),current_title=x['props'].get('title'),current_purpose=x['props'].get('lines'),replacement_id=design,replacement_visual=asset,message_specific_execution=purpose);rows.append(row)
 if not groups or groups[-1]['replacement_id']!=design or groups[-1]['end_frame']!=x['start_frame']:groups.append(dict(replacement_id=design,start_frame=x['start_frame'],end_frame=x['end_frame'],unit_ids=[uid]))
 else:groups[-1]['end_frame']=x['end_frame'];groups[-1]['unit_ids'].append(uid)
F=Path('video/node_modules/@remotion/compositor-win32-x64-msvc/ffmpeg.exe')
for i,g in enumerate(groups):
 f=g['start_frame']+min(45,(g['end_frame']-g['start_frame'])//2);out=D/f'{i+1:02}_{g["replacement_id"]}_f{f}.png';z=subprocess.run(list(map(str,[F,'-v','error','-y','-ss',f/30,'-i',movie,'-frames:v','1',out])),capture_output=True);assert z.returncode==0,z.stderr;g.update(actual_frame=str(out),seek_frame=f,seek_s=f/30)
record=dict(input_video=str(movie),input_video_sha256=sha,interval_count=len(rows),unit_count=len({x['unit_id']for x in rows}),duration_s=sum(x['duration_s']for x in rows),all_note_modes_mapped=True,text_only_fallback_allowed=False,intervals=rows,representative_groups=groups,scope='v8 visual proposals only; no new full film or voice generation')
(E/'note_audit.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8');(O/'note_replacement_map.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8');print('NOTE_AUDIT',len(rows),len(groups),record['duration_s'])
