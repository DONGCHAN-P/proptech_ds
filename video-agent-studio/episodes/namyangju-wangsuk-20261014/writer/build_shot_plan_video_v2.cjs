const fs=require('fs'),path=require('path');
const root=path.resolve(__dirname,'..');
const read=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8').replace(/^\uFEFF/,''));
const scenes=read('writer/scene_proposals_v2.json').scenes;
const timing=read('narration/timing_proposals_v1.json');
const captions=read('editor/render_v1/caption_estimates.json');
const facts=read('research/facts.json').facts;
const specs=`
S001|광교와 동탄을|previous_episode_excerpt|전편 시리즈의 실제 영상 기억을 연결|원본 v14 03:16.8~03:20.8 4초 음소거; 전편 광교·동탄 라벨|CONT-001|previous_v14
S001|다섯 가지|real_map|전편에서 새 도시로 위치 전환|수도권 실제지도 남쪽→남양주 카메라 이동 뒤 멈춤|DEV-001|regional
S001|일자리는 가까운가|motion_diagram|다섯 질문을 낭독 순서로 소개|일자리·철도·가격·생활·공급 아이콘 순차 점등; 장문 목록 금지|CONT-001|five_questions
S001|오늘 처음 보셔도|real_map|이번 조사 범위를 지역으로 보임|별내·다산·진접 위치핀 등장; 실제지도 좌표 유지|DEV-011,LIV-011|regional
S001|이미 살고 있는|motion_diagram|거래 관측과 입주전 계획의 차이|과거 거래 관측→입주·이용·운영 달력으로 축 변환|CONT-003|calendar
S001|지난 예고에서는|motion_diagram|왕숙 예고블록과 이번 사례 구분|예고 A1·A2 카드는 지구 불명확 라벨; 왕숙2 A1·A3 새 카드 분리|CONT-002,LIV-003,LIV-004|block_cards
S001|전편에서 가져올|ai_concept|질문을 이어가는 편집적 휴지|기존 근거확인 책상 이미지 1.02배 미세크롭; 가격상승 재현 없음|CONT-001|owned_desk
S001|내 직장과 학교|real_photo|실제 생활의 질문으로 도입을 닫음|확보한 남양주 역·거리 실사 짧은 디테일→다음 실제지도 컷|LIV-010|station_photo
S002|왕숙 이야기에|real_map|기존 남양주 공간 안내|광역 지도 고정 후 읍동별 지역이름 차례대로 핀 강조|DEV-001|regional
S002|실제 생활은|motion_diagram|행정경계와 개인동선 구분|집·역·직장·학교 연결노드; 이동분 수치 없음||commute
S002|현재 교통을|real_photo|별내역 실제 장소 인식|별내역 표지 실사 원비율 유지; 출처촬영일 표시|LIV-010,DEV-011|station_photo
S002|여기서 이름이|real_map|별내역과 별내별가람 구별|실제지도 두 지점 분리 강조; 임의 환승선 금지|LIV-010,LIV-011|station_pins
S002|별내역과 별내별가람역은|motion_diagram|이름유사로 생기는 혼동 해소|8호선·경춘선/4호선 카드 분리 뒤 집→역 접근단계 추가|LIV-010,LIV-011|station_diagram
S002|다산도 마찬가지|real_photo|기존 다산 생활공간 보여줌|권리확인된 다산역·공원 실사 2개 의미컷; 실제왕숙 장면 아님|LIV-012,DEV-011|dasan_photo
S002|그럼 어떤 순서로|real_map|목적지부터 거꾸로 후보 찾기|목적지 핀→역핀→집 후보영역 강조; 실제통근시간 계산하지 않음||regional
S002|전편에서도|ai_concept|대표단지와 생활권 개념 복습|기존 대표단지 생활권 AI 그림 짧은 연결; 실제남양주 아님|CONT-004|owned_life
S003|이제 이 지도에|real_map|왕숙1·2 위치를 기존지도에 더함|광역핀에서 확보 공식 지구계획도로 매치컷|DEV-001,DEV-003|official_plans
S003|남양주시 사업개요에서|real_map|왕숙1의 장소와 면적|왕숙1 공식도면 원본전체무변형 표시; 별도독립지도에서위치확대|DEV-001,DEV-002|wangsuk1
S003|왕숙2는|real_map|왕숙2 별도지구 확인|왕숙2 공식도면으로 컷; 일패·이패 이름 강조|DEV-001,DEV-002|wangsuk2
S003|두 지구를 합치면|data_chart|계획규모의 합산 의미|64159+15955=80114 한 번 표시; 계획수용 라벨 유지|DEV-001|district_size
S003|지금 8만|motion_diagram|계획·분양·입주 지표를 구분|계획→공급→입주 3단계 다른상태; 완료색 자동채우기 없음|DEV-001|stage
S003|왕숙1의 면적은|real_map|큰지구 안의 블록차이 질문|공식지구도 전체원본 두패널, 광역지도와 연결; 도면위추가레이어/크롭금지|DEV-001,DEV-002|official_plans
S003|오늘 지도에서는|ai_concept|도보·생활조건 질문으로 전환|기존 세가지성장조건 개념이미지에 실제왕숙아님 라벨; 다음달력 컷||owned_conditions
S004|전편에서는|previous_episode_excerpt|전편 철도 판단기준 기억|v14 04:23~04:27 발췌 음소거; 전편광교·동탄 라벨|CONT-006|previous_v14
S004|지금 운행하는|real_map|현재와 미래 교통망 분리|현재지도 실선 레이어 / 미개통계획 점선 범례 표시|DEV-008,DEV-009,DEV-011|transport
S004|왕숙2의 구체적인|data_chart|A1·A3 입주 달력|A1 812/2029.2→A3 686/2030.5 순차강조 뒤 읽는유지|LIV-003,LIV-004|calendar
S004|국토교통부의|motion_diagram|GTX-B 목표와 개별역확인 구분|2025.8착공 이력→2031목표; 왕숙역세부 미확인 작은태그|DEV-008|gtx_timeline
S004|9호선 연장으로|real_map|9호선 사업과 최신 절차|공식계획노선; 2026.9 2·5공구절차 인용 인셋; 최신개통연도 없음|DEV-009,DEV-010|transport
S004|왕숙2 A1의|data_chart|입주와 철도 시차를 읽음|동일시간축 A1/A3/GTX목표 3행; 차이영역 음영만 표시; 확정불편기간 금지|LIV-003,LIV-004,DEV-008|calendar
S004|예를 들어 서울로|ai_concept|통근가구의 생활 질문|기존 철도연결 AI 이미지 개념표시→집/버스/역 연결도||owned_rail
S004|여기까지 다섯|motion_diagram|교통 소결 후 일자리 질문 연결|다섯질문 중철도만 확인범위 표기; 이동선 끝이 일자리노드로 연결||commute
S005|전편에서 동탄의|previous_episode_excerpt|전편 사업장 지도 연결|v14 03:34.9~03:38.9 지도 4초 음소거; 동탄 명시|CONT-005|previous_v14
S005|왕숙도 같은 질문|motion_diagram|기업이름보다 사업진행 단계|운영/계획/허가 태그 서로분리; 로고장식나열 없음||stage
S005|먼저 기존 기반|real_map|기존3산단과 신규산단 위치 분리|기존진관·금곡·광릉 좌표핀; 신규산단은 별도범위|DEV-012,DEV-004|jobs_map
S005|새로운 움직임도|motion_diagram|산단승인의 최신 문서근거|2026.10.8 발표본문 출처 인셋→승인상태 한칸점등|DEV-004|official_document
S005|발표에서 설명한|data_chart|규모·사업비의 정의|약120만㎡/1조8993억 원 표시; 발표계획비용·지출완료아님|DEV-005|industrial_size
S005|시 소개에는|real_map|예정기업과 입지의 연결|산단위치+예정기업 텍스트태그; 확인안된 필지정확핀 금지|DEV-006|jobs_map
S005|그중 우리금융|motion_diagram|개별기업 진척 사례|2026.5 허가→2029 준공목표; 8500억 발표계획 태그|DEV-007|company_timeline
S005|기업 투자액과|ai_concept|투자액과 상주인원을 구분|기존책상 AI 컷에 투자액≠상주직원 간결기호; 시설실사로 오인금지||owned_desk
S005|지역에서 일하는|real_photo|지역근무가구와 통근가구 조건 차이|실제남양주역·거리 생활사진; 해당기업근무자라 단정금지||station_photo
S006|광교와 동탄에서는|ai_concept|완성도시 생활관점→첫입주 질문|기존 수변생활 AI 개념 컷; 미래왕숙 완성모습으로 쓰지않음|CONT-003|owned_water
S006|교육지원청의|motion_diagram|학교4곳 승인근거|교육청 문서헤드 출처 인셋→4학교명 순차줄강조|LIV-001|school_document
S006|같은 해 11월|data_chart|유치원 승인·목표|2유치원명+2029.3 목표를 별도행으로 추가|LIV-002|school_calendar
S006|다만 심사를|motion_diagram|심사와 실제개교·배정 차이|심사통과→공사→개교→배정 연결; 미확인단계 빈칸유지|LIV-001,LIV-002|stage
S006|앞서 본 왕숙2|data_chart|입주와 학교목표 시간비교|A1 2029.2/A3 2030.5/학교2029.3 목표 같은축; 배정보장 없음|LIV-001,LIV-003,LIV-004|school_calendar
S006|교육과 문화공간의|real_map|WE드림파크는 계획시설|확보공식계획도 전체원본 축소제시와별도계획카드; 정확부지미확정시설핀금지|LIV-008|official_plans
S006|발표 당시 총사업비|data_chart|확보비와 총사업비 구분|669전체/335확보 다른색; 완공증거아님|LIV-008|we_budget
S006|가족이 생활하는|real_photo|첫입주자의 하루를 실감|위치권리확인된 공원·역 실사; 학교미확보면 통학노드 그래픽으로 대체||life_photo
S007|이제 예산을|ai_concept|가격을 읽는 시선 전환|기존 근거확인책상 이미지 짧은컷→타입표||owned_desk
S007|LH의 왕숙2 A1|data_chart|A1 타입별 표시가격|59A4.9304/84A6.9363억 빠른막대그림 뒤 유지; 5층이상기준층|LIV-005|price_chart
S007|A3 페이지에서|data_chart|A3를 같은타입구조로 비교|59A5.2634/84A7.3245억 두번째패널; 단지명항상왕숙2|LIV-006|price_chart
S007|이 값은 이번|motion_diagram|페이지값과 최종계약가 구분|공고표원문 인셋→타입별/층/정정/옵션 4조건강조|LIV-005,LIV-006,LIV-007|price_source
S007|여기에 발코니|motion_diagram|최종비용의 빈칸|확장·옵션·층별가격 체크노드; 근거없는추가금 금지|LIV-007|price_conditions
S007|주변 단지와|real_map|주변비교 조건을 생활권에 연결|다산·별내·진접 지도 각 후보영역; 미검증실거래수치 없음||regional
S007|전편에서 최고가|motion_diagram|지표뜻을 분리한 전편 원칙|최고가/중위/공고타입가격 세영역 분리; 숫자섞지않음|CONT-007|statistic
S007|다섯 번째 질문인|data_chart|계획규모와 연간공급 다름|80114 계획원통→A1/A3 입주예정만 달력분해; 기타연도빈칸|DEV-001,LIV-003,LIV-004|supply
S008|광교와 동탄에서|motion_diagram|다섯질문 회수|각 항목 확인범위 순차강조; 점수나완료체크 없음|CONT-001|five_questions
S008|분양가는 왕숙2|data_chart|미완료범위 가격·공급 회수|표시가격 확인/동일조건비교 미완/연도총물량 미완 3칸 간결표시|LIV-005,LIV-006,DEV-001|status
S008|서울로 통근하는|real_photo|가구별 우선질문|실제남양주생활사진→통근/지역근무/자녀노드 3단강조||life_photo
S008|전편이 이미|ai_concept|전편 관측과 이번 준비의 차이|기존세시간표 개념 이미지에 관측→입주전달력 작은전환|CONT-003|owned_calendars
S008|이 기준을 이어가며|real_map|남양주→왕숙→내블록으로 좁힘|실제광역지도에서공식지구도로 이동; 블록확인불가면지구수준멈춤|DEV-001|official_plans
S008|다음에 새 발표를|motion_diagram|다섯질문을 시리즈의 끝으로 남김|가벼운BGM리프트; 브랜드마크/다섯아이콘 조용히정리||five_questions
`.trim().split('\n').map(line=>{const [scene,cue,type,purpose,motion,ids,need]=line.split('|');return {scene,cue,type,purpose,motion,ids:ids?ids.split(','):[],need};});
const owned={owned_desk:'video/public/asset-pack-v9/01_images/09m00s_근거를_확인하는_책상_AI.png',owned_life:'video/public/asset-pack-v9/01_images/05m00s_대표단지와_생활권_AI.png',owned_conditions:'video/public/asset-pack-v9/01_images/03m00s_세가지_성장조건_AI.png',owned_rail:'video/public/asset-pack-v9/01_images/04m05s_철도_연결_AI.png',owned_water:'video/public/asset-pack-v9/01_images/03m34s_수변_생활권_AI.png',owned_calendars:'video/public/asset-pack-v9/01_images/09m30s_세개의_시간표_개념.png'};
const norm=s=>s.replace(/\s+/g,'');
let shots=[],issues=[];
for(const t of timing.scenes){
 const s=scenes.find(x=>x.scene_id===t.scene_id),chapter=specs.filter(x=>x.scene===t.scene_id),cap=captions[t.scene_id],full=norm(s.narration_text);
 let starts=[];
 for(let i=0;i<chapter.length;i++){
  const q=chapter[i],offset=full.indexOf(norm(q.cue));
  if(offset<0)issues.push({scene:t.scene_id,cue:q.cue,issue:'anchor_not_found'});
  let anchor=0,cs=0,ce=0,anchorText='';
  for(const c of cap){const next=cs+norm(c.text).length;if(offset>=cs&&offset<next){anchor=c.start_s;ce=c.end_s;anchorText=c.text;break;}cs=next;}
  // Within a character-weight caption, use fractional position only to avoid collapsing adjacent semantic cues.
  const local=i===0?0:Math.max(0,Math.min(t.duration_s,anchor+(Math.max(0,offset-cs)/Math.max(1,norm(anchorText).length))*(ce-anchor)));
  starts.push({local,anchor,anchorText,offset,q});
 }
 for(let i=0;i<starts.length;i++){
  const a=starts[i],end=i+1<starts.length?starts[i+1].local:t.duration_s;
  if(end<=a.local)issues.push({scene:t.scene_id,cue:a.q.cue,issue:'nonmonotonic_anchor'});
  const factual=a.q.ids.filter(x=>!x.startsWith('CONT')),continuity=a.q.ids.filter(x=>x.startsWith('CONT'));
  shots.push({shot_id:'V2-'+String(shots.length+1).padStart(3,'0'),chapter_id:t.scene_id,script_revision:'script-v2',audio_revision:'audio-v1',start_s:+(t.start_s+a.local).toFixed(3),end_s:+(t.start_s+end).toFixed(3),chapter_local_start_s:+a.local.toFixed(3),chapter_local_end_s:+end.toFixed(3),timing_basis:'measured_chapter_duration_plus_existing_character_weight_caption_anchor_HEURISTIC_NOT_WORD_ALIGNED',anchor:{cue:a.q.cue,existing_caption_start_s:a.anchor,existing_caption_text:a.anchorText},type:a.q.type,purpose:a.q.purpose,claim_ids:factual,continuity_claim_ids:continuity,source_urls:factual.map(id=>facts.find(f=>f.claim_id===id)?.source_url).filter(Boolean),representation:a.q.type==='ai_concept'?'illustration_only_not_place_evidence':a.q.type==='previous_episode_excerpt'?'owned_previous_episode_not_current_namyangju':factual.length?'claim_explanation_use_verified_source':'editorial_explanation_no_new_fact',asset_request:a.q.need,asset_candidate:owned[a.q.need]||null,asset_status:owned[a.q.need]?'existing_owned_candidate_visual_inspection_required':'visual_peer_confirmation_required',camera_motion:a.q.motion,transition_in:a.q.type==='real_map'?'cut_or_geographic_match_cut_0.3s':a.q.type==='real_photo'?'cut_or_dissolve_0.25s':'clean_cut_avoid_slide_wipe',transition_out:'meaning_boundary_not_fixed_interval',caption_intent:'기존승인음성의문장자막; 1~2줄, 지도라벨·출처와겹치지않음; heuristic수동청취검증필요',onscreen_label:a.q.type==='ai_concept'?'AI 개념 이미지 · 실제 왕숙 모습 아님':a.q.type==='previous_episode_excerpt'?'전편: 광교·동탄':'출처·기준일·계획/목표 조건 유지',bgm_intent:'기존 Data City Ambient v1 승인소유트랙 후보, 내레이션덕킹; 숫자/조건구간은더낮춤; 새유료음악없음',fallback:a.q.type==='real_photo'?'동일주제실제지도+노드다이어그램. 허위실사/AI실제장소대체금지':a.q.type==='ai_concept'?'독립제작개념노드그래픽':'확보된실제지도/검증표를다른의미확대구도로전개',long_hold_reason:end-a.local>24?'문서·지도·조건읽기 필요. 이 구간 안에 대상하이라이트 변화 최소1회; 정지타이틀 지속금지':null});
 }
}
// First shot deliberately uses a four-second owned excerpt rather than a long chapter card.
const first=shots[0],next=shots[1];first.end_s=4;first.chapter_local_end_s=4;next.start_s=4;next.chapter_local_start_s=4;
const out={revision:'shot-plan-video-v2',status:'editorial_shot_plan_not_rendered_not_listened',inputs:{script:'writer/script_v2.md',scene_proposals:'writer/scene_proposals_v2.json',timing:'narration/timing_proposals_v1.json',caption_anchors:'editor/render_v1/caption_estimates.json',actual_previous:'config/current_video.json v14 and source dependencies'},total_audio_duration_seconds:timing.total_duration_seconds,additional_cash_usd:0,paid_generation_authorized_by_this_plan:false,style_reference:'actual_v14_user_requested; unapproved_30sec_proposal_not_reference',shot_count:shots.length,representative_sequence:{start_s:0,end_s:90,shot_ids:shots.filter(s=>s.start_s<90).map(s=>s.shot_id),scope:'S001 and S002 opening; full913s timeline remains required, not sample-only delivery'},global_rules:['8章≠8slides','AI概念illustration_only','real_map_coordinate_source_required','no_future_city_fabrication','no_constant5sec_cut_rule','word_alignment_and_actual_listening_not_done','stage_and_price_conditions_preserved','original_script_audio_files_preserved','chapter_offsets_may_shift_if_editor_uses_decoded_pcm_duration; recalc_all_shots_consistently'],issues,shots};
fs.writeFileSync(path.join(__dirname,'shot_plan_video_v2.json'),JSON.stringify(out,null,2)+'\n');
console.log(JSON.stringify({shots:shots.length,issues,coverage_end:shots.at(-1).end_s,representative:out.representative_sequence.shot_ids,types:shots.reduce((a,s)=>(a[s.type]=(a[s.type]||0)+1,a),{})}));
