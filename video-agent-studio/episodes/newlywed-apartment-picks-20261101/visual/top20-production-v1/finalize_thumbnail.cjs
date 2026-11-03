const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const work=__dirname,ep=path.resolve(work,'../..'),out=path.join(ep,'outputs/top20-production-v1/thumbnail');
const slash=p=>p.replaceAll('\\','/');
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const write=(p,o)=>fs.writeFileSync(p,JSON.stringify(o,null,2)+'\n');
const sourcePath=path.resolve(work,'../top20-8min-v2/photo_assets_v2.json');
const source=JSON.parse(fs.readFileSync(sourcePath,'utf8'));
const technical=JSON.parse(fs.readFileSync(path.join(work,'technical_checks.json'),'utf8'));
const rankingPath=path.join(ep,'research/top20-8min-v2/top20.json');
const ranking=JSON.parse(fs.readFileSync(rankingPath,'utf8'));
const selected=['R03','R02'].map(id=>source.assets.find(a=>a.region_id===id));
const initial=JSON.parse(fs.readFileSync(path.join(work,'input_snapshot.json'),'utf8'));
const now=new Date().toISOString();
const artifact=(p,role)=>({path:slash(p),role,bytes:fs.statSync(p).size,sha256:sha(p)});
for(const a of selected)if(sha(a.absolute_file)!==a.sha256)throw Error('Photo hash changed');
for(const a of technical.outputs)if(sha(a.path)!==a.sha256)throw Error('Output hash changed');
const copyTexts=technical.checks.texts.filter(t=>!t.text.includes('촬영'));
for(let i=0;i<copyTexts.length;i++)for(let j=i+1;j<copyTexts.length;j++){
 const a=copyTexts[i].rect,b=copyTexts[j].rect;
 if(a.x<b.right&&a.right>b.x&&a.y<b.bottom&&a.bottom>b.y)throw Error('Text rectangle overlap');
}
const brief={
 task_id:'top20-thumbnail-v1',role:'visual',episode_id:'newlywed-apartment-picks-20261101',revision:'top20-production-v1',
 scope:'썸네일 PNG 1장과 320px 모바일 미리보기. 수정 소유권은 visual/top20-production-v1 및 outputs/top20-production-v1/thumbnail 한정.',
 user_requirements:{headline:'신혼부부는 어디에 살까?',secondary:'수도권 TOP20',context:'2024년 신혼부부 수 기준',dimensions:[1280,720],mobile:[320,180],style:'기존 승인 채널의 Pretendard ExtraBold, 큰 흰 글자와 노란 질문, 네이비 텍스트 영역, 실제 아파트/공원 사진',photos:'기존 photo_assets_v2의 검증된 사진 사용, 원본 픽셀 변경 금지, 배치용 축소/제한 크롭 허용',external_api:'신규 외부 API·유료 생성·imagegen 사용 안 함'},
 composition:{text_area:{x:0,y:0,width:680,height:720,ratio:0.53125},photo_area:{x:680,y:0,width:600,height:720,ratio:0.46875},palette:{navy:'#06182e',white:'#ffffff',question:'#ffdf2b'},font:'기존 Pretendard-ExtraBold.woff2',primary_question_font_px:127},
 ranking_basis:{scope:ranking.scope,reference_date:ranking.statistic_reference_date,source_path:slash(rankingPath),sha256:sha(rankingPath),meaning:'거주지 기준 신혼부부 전체 수 순위. 선호도 조사·구매자 순위·단지 추천 순위로 표시하지 않음.'},
 choices:{selected:['PHOTO_R03','PHOTO_R02_ALT01'],inspected_not_selected:{asset_id:'PHOTO_R18',reason:'실제 사진 직접 확인. 역 이미지 추가는 표지의 주택/생활환경 메시지를 분산해 제외.'},alternative:'차별화 필요가 없어 별도 대안 미제작',map:'실제 사진과 질문의 즉시 인지를 위해 소형 지도·개별 순위 생략'},
 preflight:{master_guide_read:true,template_read:true,thumbnail_only_contract_applied:true,approved_actual_thumbnails_viewed:true,representative_internal_check:'동일 1안의 최초 출력 1280/320을 직접 확인 후 제목 확대·촬영연도 라벨 위치 수정, 최종 1280/320 재확인',non_applicable:['본편 편집','음성/타이밍 잠금','쇼츠 생성','업로드']},
 initial_input_snapshot:slash(path.join(work,'input_snapshot.json')),final_render_inputs:technical.inputs
};
write(path.join(work,'production_brief.json'),brief);
const sources=selected.map(a=>({
 ...a,
 composition_use:{thumbnail_scene_id:'TH001',source_file_sha256_after_render:sha(a.absolute_file),source_file_unchanged:true,source_pixels_recolored:false,generated_or_reconstructed:false,
  layout:a.region_id==='R03'?{frame:[680,0,600,450],fit:'contain',visible_source_rectangle_px:[0,0,3840,2880],crop:false,source_top_edge_note:'원사진의 아파트가 원래 상단에서 프레임 밖으로 이어짐. 편집으로 추가 잘림 없음.'}:{frame:[680,456,600,264],fit:'cover',position:'center bottom',visible_source_rectangle_px:[0,1190.4,3840,1689.6],crop:true,crop_purpose:'상단 하늘을 줄이고 수면·벚꽃 수변을 유지. 배경 건물·인물·로고를 재확대하지 않음.'},
  overlay:'장소명·촬영연도는 별도 HTML 레이어. 각 장소 사진은 6px 네이비 구분선으로 분리하며 하나의 실제 연속 풍경으로 합성하지 않음.',
  changes_notice:'원본 파일 바이트 보존. 썸네일에서 비율 유지 축소; R02는 상단 제한 크롭. 색보정·생성수정·왜곡 없음. 장소·촬영연도 텍스트 레이어 추가.'}
}));
const ledger={task_id:brief.task_id,input_manifest:{path:slash(sourcePath),sha256:sha(sourcePath),revision:source.photo_revision},license_evidence_scope:'photo_assets_v2의 기존 개별 라이선스·장소 확인 기록 계승. 이 작업에서는 선택 원본의 실제 픽셀과 SHA, 최종 배치만 재검수. 외부 사이트 재조회 없음.',sources};
write(path.join(work,'source_ledger.json'),ledger);
const full=technical.outputs[0],mobile=technical.outputs[1];
const review={
 task_id:brief.task_id,reviewed_utc:now,status:'self_checked_pending_independent_QA',reviewer_role:'제작 visual 담당의 자체 검수',independent_qa_performed:false,
 actual_viewed_files:[{...full,view:'view_image로 최종 1280×720 직접 확인'},{...mobile,view:'view_image로 최종 320×180 직접 확인'}],
 source_photos_directly_viewed:['PHOTO_R02_ALT01','PHOTO_R03','PHOTO_R18'],
 findings:[
  {id:'TH001-READ',result:'pass',evidence:'320px에서 신혼부부는/어디에 살까?/수도권 TOP20을 식별. 메인 글자 환산 크기 29.5/31.75/20.75px. 아파트와 수변도 구분됨.'},
  {id:'TH001-BOUNDS',result:'pass',evidence:'실제 출력의 한글·물음표·TOP20 잘림 없음. DOM Range 기준 캔버스 경계 안, 주요 글자 영역 겹침 0. 질문 오른쪽 654.03px, 사진 시작 680px.'},
  {id:'TH001-SMALL',result:'qualified',evidence:'2024년 신혼부부 수 기준은 보조 문구 6.75px, 장소·촬영연도는 5.25px 환산이므로 작은 화면의 즉시 판독은 주요 제목보다 약함. 원본 1280px와 출처 기록에서 명확하게 제공.'},
  {id:'TH001-PLACE',result:'pass',evidence:'삼송 2021년 사진은 전체 contain, 석촌호수 2025년 사진은 상단 제한 크롭. 서로 별도 패널과 장소·촬영연도 표시. 사진연도를 통계2024년으로 오인시키지 않음.'},
  {id:'TH001-TONE',result:'pass',evidence:'직접 본 housing-choice TH003 및 최신 affordable photo-v1과 동일 계열 ExtraBold·흰/노랑 위계·왼쪽 질문/오른쪽 주거 풍경을 계승.'},
  {id:'TH001-CLAIM',result:'pass',evidence:'신혼부부 수 기준을 명시. 선호 지역·구매자·투자 순위 표현 없음. 특정 사진이 TOP1 또는 신혼부부 주거 원인의 증거라고 표시하지 않음.'},
  {id:'TH001-PRESERVE',result:'pass',evidence:'두 출처 사진의 제작 전·후 SHA256 일치. 원본 보존, 사진 필터 none/opacity1; 출력 모두 원본보다 축소. AI 생성 없음.'}
 ],limitations:['320px PNG를 데스크톱 도구로 직접 열람한 검수이며 실제 휴대전화 기기 테스트는 수행하지 않음.','영상 연속 재생·음성 청취·본편 및 쇼츠 검수·업로드 범위가 아님.','독립 QA는 다음 담당이 수행. 클릭률 효과는 미측정.'],open_required_issues:[]
};
write(path.join(work,'visual_review.json'),review);
const assets={task_id:brief.task_id,revision:'top20-production-v1',assets:[
 {asset_id:'TH001',scene_ids:['TH001'],type:'thumbnail_real_photo_native_text',source_or_prompt:{method:'native static HTML/CSS; local Chromium export',photos:sources.map(a=>({asset_id:a.asset_id,path:a.absolute_file,sha256:a.sha256,author:a.source_or_prompt.author,file_page:a.source_or_prompt.file_page,capture_year:a.photo_capture_year,license:a.license.name}))},dimensions:{width:1280,height:720},actual_file:full.path,sha256:full.sha256,actual_place:['경기 고양 삼송로','서울 송파 석촌호수 동호'],AI_표기:'해당 없음: 출처가 있는 실제 장소 사진과 네이티브 텍스트',ai_generated:false,upscaled:false,usage_conditions:'사진 2장 CC0 1.0. 개별 원문·저자·촬영연도·원본 이용조건은 source_ledger.json에 보존. 최종 배치의 제한 크롭 및 텍스트 오버레이를 별도 표시.',inspection_status:review.status},
 {asset_id:'TH001_MOBILE320',scene_ids:['TH001'],type:'thumbnail_mobile_preview',source_or_prompt:{derived_from:'TH001',method:'browser canvas high quality proportional downsample'},dimensions:{width:320,height:180},actual_file:mobile.path,sha256:mobile.sha256,actual_place:'TH001과 동일',AI_표기:'해당 없음',ai_generated:false,upscaled:false,usage_conditions:'TH001 출처와 동일',inspection_status:review.status}
]};
write(path.join(work,'assets.json'),assets);
const credits=sources.map(a=>`- ${a.actual_place} · ${a.photo_capture_year}년 촬영 · ${a.source_or_prompt.author}, 「${a.source_or_prompt.title}」 · ${a.license.name}\n  원문: ${a.source_or_prompt.file_page}\n  이용조건: ${a.license.license_url}\n  원본 SHA256: ${a.sha256}\n  썸네일 배치: ${a.composition_use.changes_notice}`).join('\n\n');
fs.writeFileSync(path.join(out,'사진출처.md'),'# TOP20 썸네일 사진 출처\n\n통계 기준: 2024-11-01 거주지의 신혼부부 전체 수. 사진은 지역 생활환경의 실제 풍경이며 촬영연도는 통계연도와 다릅니다.\n\n'+credits+'\n','utf8');
const manifest={
 task_id:brief.task_id,created_utc:now,status:review.status,affected_scene_ids:['TH001'],title:'신혼부부는 어디에 살까? / 수도권 TOP20',context:'2024년 신혼부부 수 기준',
 artifacts:technical.outputs,
 records:['production_brief.json','source_ledger.json','visual_review.json','technical_checks.json','assets.json','thumbnail.html','render_thumbnail.cjs','finalize_thumbnail.cjs'].map(n=>artifact(path.join(work,n),n)),
 credits:artifact(path.join(out,'사진출처.md'),'credits'),
 ranking:{path:slash(rankingPath),sha256:sha(rankingPath),scope:ranking.scope,reference_date:ranking.statistic_reference_date},
 source_photo_hashes:sources.map(a=>({asset_id:a.asset_id,source_sha256:a.sha256,after_render_sha256:sha(a.absolute_file),license:a.license.name,photo_capture_year:a.photo_capture_year})),
 technical:{resolution_verified:true,png_decode_verified_by_browser:true,text_clipping:0,main_text_overlap:0,source_hashes_unchanged:true,external_network_requests:0,paid_calls:0,ai_generated:false,upscaled:false},
 self_visual_review_performed:true,independent_QA:'pending_next_role',handoff:slash(path.join(work,'handoff.json'))
};
write(path.join(out,'artifact_manifest.json'),manifest);
const handoff={
 task_id:brief.task_id,role:'visual',status:'완료·독립 QA 대기',
 input_revisions:{photo_assets:'photo_assets_v2',photo_manifest_sha256:sha(sourcePath),ranking:ranking.revision,ranking_sha256:sha(rankingPath),initial_inputs:slash(path.join(work,'input_snapshot.json'))},
 outputs:[full.path,mobile.path,slash(path.join(out,'artifact_manifest.json')),slash(path.join(work,'assets.json'))],affected_scene_ids:['TH001'],
 checks:[{check:'해상도·PNG·경계·겹침·원본 SHA',result:'passed',evidence:'technical_checks.json'},{check:'최종1280/320 실제 열람·사진3장 직접 확인',result:'self_checked',evidence:'visual_review.json'},{check:'CC0 2장 출처·2021/2025 촬영연도 보존',result:'passed',evidence:'source_ledger.json'}],
 open_issue_ids:[],unresolved:'독립 QA 대기. 320px 보조 촬영연도는 작음. 실제 휴대전화 테스트 없음.',next_role:'qa → director',
 note:'썸네일만 제작. 본편·쇼츠·음성·공통 상태 변경 없음. 신규 외부API·유료생성·업로드 없음.'
};
write(path.join(work,'handoff.json'),handoff);
// Reopen records and outputs; verify actual sizes and current hashes after writing.
for(const p of ['production_brief.json','source_ledger.json','visual_review.json','assets.json','handoff.json'])JSON.parse(fs.readFileSync(path.join(work,p),'utf8'));
const final=JSON.parse(fs.readFileSync(path.join(out,'artifact_manifest.json'),'utf8'));
for(const a of [...final.artifacts,...final.records,final.credits])if(sha(a.path)!==a.sha256)throw Error('Manifest mismatch: '+a.path);
console.log(JSON.stringify({status:handoff.status,artifacts:final.artifacts,manifest:slash(path.join(out,'artifact_manifest.json')),handoff:slash(path.join(work,'handoff.json')),records_verified:true,main_text_overlap:0},null,2));
