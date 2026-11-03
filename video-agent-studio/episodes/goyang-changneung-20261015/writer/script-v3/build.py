from pathlib import Path
import json, hashlib, re, math

ep=Path(__file__).resolve().parents[2]
out=ep/'writer/script-v3'; review=ep/'outputs/script-review-v3'
out.mkdir(parents=True,exist_ok=True); review.mkdir(parents=True,exist_ok=True)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,t): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(t,encoding='utf-8',newline='\n')
def dump(p,v): write(p,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
source=ep/'outputs/script-review-v2/script_v2.md'
assert sha(source)=='7e77b50a09982e6eec35bcbeaa49b73bb814cab6d59c243a1dbd10c60d4dadd5'
src=source.read_text(encoding='utf-8-sig')
parts=re.findall(r'## (M\d{3}) · ([^\n]+)\n(.*?)(?=\n## M|\Z)',src,re.S)
assert len(parts)==10
base=json.loads((ep/'writer/script-v2/scene_proposals.json').read_text(encoding='utf-8-sig'))
common='共通'.replace('共通','공통 적용: 직전 왕숙 최종 v15의 채널 톤·지도·의미단위 자막·브랜드를 계승하고, 추가 세 레퍼런스의 질문→증거→생활의 의미→조건부 판단과 자료 역할 분리를 적용한다. 고정 지도 구도, 대상 가까운 짧은 라벨, 본문 흰 자막 박스 유지. 지도 줌·급팬 없이 현재 발화 대상만 강조한다. 이전 영상 실제 복기→대표 장면 비교→차이 수정→부분 검수의 루프를 수행하고 근거를 남긴다. guides/채널_톤앤매너와_복기루프.md 및 해당 tokens를 제작 시 확인한다. 이번 writer 작업은 실제 영상 재생·청취를 수행하지 않았으며 기존 전문 담당의 표본 프레임 관찰만 승계한다.')
common+=' 채널 공통 외형: 크림 바탕·Pretendard 일반/굵게·작은 브랜드 행·굵은 제목·얇은 연도축을 계승한다. visual/channel-style-v1/style_tokens.json과 outputs/channel-style-v1/comparison_contactsheet.png를 재사용하고, 교통 W15_175/235·가격 W15_650·생활 W15_365와 새 컷을 실제 프레임으로 나란히 비교한다. 큰 설명 부제·상시 우측 장문·중앙 대형 면책 문구는 두지 않으며, 근거 옆 짧은 조건만 표시한다. 대표 3종 내부 QA 뒤 확장하고 각 컷 대표 및 경계 전후를 검수한다. 외부 레퍼런스는 설명 기법 보완이며 채널 색·자막·브랜드는 기존 기준을 따른다.'
details=[
('왕숙 v15 훅·전편 연결·5초 브랜드 인트로 대응','SbDrzVB47xQ 00:20 위치+공식 근거 원리를 선택 질문에 연결. FSB-esdhikE 결론 회수 원리를 예고한다.'),
('왕숙 v15 전체지도→현재 지구 단일 locator→상세 생활 배치 대응','FSB-esdhikE 02:36 전체→04:53 상세의 정보 순서와 u3Ncol4Jx5I 12:19 위치 기준/주제 자료 분리. 변경금지 원도면은 전체 fit 독립판으로 보존한다.'),
('왕숙 v15 일자리 위치·현재/계획 상태 분리 대응','SbDrzVB47xQ 00:34 업무 자료 역할과 02:09 교통 연결 원리. 자족계획→이전 기업 사실표→외부 업무지 후보→현재 역간 표 순서. 업무지 표 옆에 ‘통근통계 실증 순위가 아닌 편집상 검토 후보’ 주석을 유지한다.'),
('왕숙 v15 운영/계획 철도·역명·입주 달력 대응','u3Ncol4Jx5I 09:09 지도+노선과 SbDrzVB47xQ 02:50 도로 자료 역할. 현재 버스·기존역 구조, 입주/철도 달력, 도로 개선을 질문별 교체한다.'),
('왕숙 v15 같은 조건 가격표·근거·숫자 자막 대응','u3Ncol4Jx5I 13:20/15:05 위치 기준 옆 주제 자료 교체 원리. 공고 원문/직접 작성 가격표/현재 대안/미래 조건 카드를 분리하며 지도에 표를 가리지 않는다.'),
('왕숙 v15 다산역 주변 배치 방식·학교/상업/공원 상세와 단일 locator 대응','FSB-esdhikE 04:53/07:06/08:00 학교·도로·배치도 원리. 대상 가까운 학교명·목표월을 표시하고 생활시설 사진은 해당 장소·권리 검증 후 삽입한다.'),
('왕숙 v15 입주·개교·개통 lane과 상품 조건 분리 대응','SbDrzVB47xQ 강점 뒤 제약 검증 원리. 공급 달력 다음에 규제별 기산점을 독립표로 읽게 하고 S3를 별도 상품으로 구분한다.'),
('왕숙 v15 동일 조건 대안 가격표·생활권 지도 대응','u3Ncol4Jx5I 주제 자료 교체와 FSB-esdhikE 단지별 요약 원리. 생활권별 2개 단지를 같은 형식으로 분할하고 중위값 옆 n을 유지한다.'),
('왕숙 v15 가구 조건 판단·검증 자료 회수 대응','SbDrzVB47xQ 동일 항목 비교 후 최초 질문 회수 원리. 직장/입주/주거비 순서로 앞 장 근거를 재사용하며 새 사실을 추가하지 않는다.'),
('왕숙 v15 조건부 후보·교산 예고·CTA·발화종료+3초·10초 아웃트로 대응','FSB-esdhikE 09:24 단지별 한 줄 요약과 SbDrzVB47xQ 최초 질문 회수. S4/S5/S1 근거·유보를 같은 형식에 놓고 가격 예측 순위로 연출하지 않는다.')]
chapters=[]; texts=[]; scenes=[]
md=['# 창릉 전체 영상 대본 v3','사용자가 저장한 v2 낭독문을 그대로 추출한 제작 입력. 화면 지시만 보강. 시간은 estimate이며 음성 생성·청취·타임록·영상 검수는 이 산출물 범위에 포함되지 않습니다.', '제목 제안: **고양 창릉, 새 철도를 기다릴까? 통근·본청약 가격과 기존 생활권 비교**','썸네일 카피: **창릉을 기다릴까?** / **기존 생활권과 비교**']
for i,(sid,title,body) in enumerate(parts):
    text=body.split('### 낭독\n\n',1)[1].split('\n\n### 화면 지시',1)[0].strip()
    old=(ep/f'writer/script-v2/narration_input/{sid}.txt').read_text(encoding='utf-8-sig')
    if sid!='M002': assert text==old, sid
    else:
        assert '창릉 주민이 가장 많이 출근할만한 서북권에서 검토할 업무지 후보입니다.' in text
    p=out/f'narration_input/{sid}.txt'; write(p,text); texts.append(text)
    chapters.append(dict(scene_id=sid,chapter_id=sid,path=f'narration_input/{sid}.txt',characters=len(text),characters_including_whitespace=len(text),characters_excluding_whitespace=len(re.sub(r'\s','',text)),utf8_bytes=p.stat().st_size,sha256=sha(p)))
    s=base['scenes'][i]; assert s['scene_id']==sid
    s.update(narration_text=text,script_revision='script-v3',status='user_saved_text_production_input',duration_estimate_seconds=math.ceil(len(text)/8))
    s['screen_direction']+='\n'+common+'\n왕숙 자료 대응: '+details[i][0]+'\n추가 레퍼런스별 적용: '+details[i][1]
    s['reference_direction_guide']='guides/레퍼런스_설명과_자료연출.md'
    s['channel_style_guide']='guides/채널_톤앤매너와_복기루프.md'
    s['previous_video_baseline']='episodes/namyangju-wangsuk-20261014/outputs/readability-cta-v15'
    s['hold']= '기존 개별 자료의 권리·위치 조건을 유지; 음성 승인·예산 집행 상태는 director의 최신 결정에 따른다. writer가 상태를 변경하지 않음.' if sid!='M001' else s['hold']
    if sid=='M002': s['editorial_claim_note']='사용자 문장 그대로 낭독. ‘가장 많이’는 통근통계로 실증된 순위 주장이 아닌 서북권 업무지 검토 후보의 편집적 표현으로 화면 주석에서 구분.'
    scenes.append(s)
    md += [f'## {sid} · {title}',f'예상 낭독 {s["duration_estimate_seconds"]}초 (estimate).','### 낭독',text,'### 화면 지시',s['screen_direction'],'자료 유형: '+', '.join(s['asset_types'])+' / 목적: '+s['visual_purpose'],'claim_ids: '+', '.join(s['claim_ids'])]
write(out/'narration_joined.txt','\n\n'.join(texts)); write(out/'script_v3.md','\n\n'.join(md)+'\n')
dump(out/'scene_proposals.json',dict(revision='script-v3',common_scenes_modified=False,timing_locked=False,scenes=scenes))
basis=json.loads((ep/'writer/script-v2/claim_basis.json').read_text(encoding='utf-8-sig')); basis['revision']='script-v3'; basis['editorial_notes']=[dict(scene_id='M002',note=scenes[2]['editorial_claim_note'],statistical_rank_verified=False)]; dump(out/'claim_basis.json',basis)
pron=json.loads((ep/'writer/script-v2/pronunciation.json').read_text(encoding='utf-8-sig')); pron['revision']='script-v3'; dump(out/'pronunciation.json',pron)
changes=dict(revision='script-v3',source_user_saved_script_sha256=sha(source),narration_changed_scenes_vs_writer_v2=['M002'],narration_policy='사용자 저장본 10장 정확 추출; 그 외 낭독문 개작 없음',screen_direction_changed_scenes=[x[0] for x in parts],facts_or_numbers_changed=False,paid_calls=0)
dump(out/'changes.json',changes)
manifest=dict(revision='script-v3',status='user_saved_text_production_input',encoding='UTF-8 without BOM',character_definition='Unicode code points including whitespace; chapter text no terminal newline; joined separator LF LF',chapters=chapters,individual_character_sum=sum(len(t) for t in texts),total_characters=sum(len(t) for t in texts),source_user_saved_script=dict(path='outputs/script-review-v2/script_v2.md',sha256=sha(source)),source_script_sha256=sha(out/'script_v3.md'),narration_joined=dict(path='narration_joined.txt',characters_including_whitespace=len('\n\n'.join(texts)),sha256=sha(out/'narration_joined.txt')),credit_cap=7661,within_credit_cap=sum(map(len,texts))<=7661,duration_estimate=dict(speech_seconds=sum(s['duration_estimate_seconds'] for s in scenes),basis='480 characters/minute assumption; not measured',brand_intro_seconds=5,post_final_speech_hold_seconds=3,brand_outro_seconds=10),paid_calls=0,actual_listening=False,continuous_playback=False)
assert manifest['within_credit_cap']
dump(out/'manifest.json',manifest)
for name in ['script_v3.md','manifest.json','changes.json','scene_proposals.json']: write(review/name,(out/name).read_text(encoding='utf-8'))
verification=dict(chapters=10,user_source_sha256=sha(source),source_sha_matches_expected=True,narration_matches_user_saved_all_10=True,unchanged_non_M002_vs_writer_v2=True,chapter_character_sum=manifest['total_characters'],joined_characters=manifest['narration_joined']['characters_including_whitespace'],within_7661=True,script_sha256=sha(out/'script_v3.md'),manifest_sha256=sha(out/'manifest.json'),paid_calls=0,actual_listening=False,continuous_playback=False)
dump(out/'verification.json',verification)
dump(out/'handoff.json',dict(role='writer',revision='script-v3',outputs=[str(out/x) for x in ['script_v3.md','scene_proposals.json','manifest.json','narration_joined.txt','pronunciation.json','claim_basis.json','verification.json']],input_versions=['user_saved_script_v2:'+sha(source),'writer/script-v2','reference-direction-v1','wangsuk-readability-cta-v15'],verification=verification,unresolved=['실제 이전 영상 복기·대표 화면 비교·청취 및 타임록은 후속 담당이 수행','공통 상태/장면표/승인 기록은 director 반영'],affected_scenes=[x[0] for x in parts],next_owner=['director','narration','visual','editor']))
print(json.dumps(verification,ensure_ascii=False))
