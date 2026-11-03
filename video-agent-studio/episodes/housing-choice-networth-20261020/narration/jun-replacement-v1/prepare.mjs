// 로컬 준비 전용. 네트워크·음성 생성·업로드·삭제 기능 없음.
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';

const own = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(own, '../../../../../');
const episode = 'video-agent-studio/episodes/housing-choice-networth-20261020';
const out = episode + '/narration/jun-replacement-v1';
const at = new Date().toISOString();
const expected = '0368c9e08b8a2447ed429d9e78ab9a8238b2d823c27467362174600876a797b7';
const sha = value => crypto.createHash('sha256').update(value).digest('hex');
const count = value => [...value].length;
const readBytes = name => fs.readFile(path.join(root, name));
const read = async name => JSON.parse((await readBytes(name)).toString('utf8').replace(/^\uFEFF/, ''));
const ref = async name => ({path:name, sha256:sha(await readBytes(name))});
const put = async (name, value) => {
  const full = path.join(own, name);
  assert(full.startsWith(own + path.sep));
  await fs.mkdir(path.dirname(full), {recursive:true});
  await fs.writeFile(full, typeof value === 'string' ? value : JSON.stringify(value, null, 2) + '\n');
  return ref(out + '/' + name);
};
const script = episode + '/outputs/script-final-v6/script_v6.md';
const preparedPath = episode + '/narration/free-tts-v1/prepare-v6/prepared.json';
const dictionaryPath = episode + '/narration/free-tts-v1/prepare-v6/pronunciation_dictionary.json';
const oldTimingPath = episode + '/narration/free-tts-v1/production-injoon-v6/final_timing.json';
const runInputsPath = episode + '/narration/free-tts-v1/production-injoon-v6/run_inputs.json';
const [sourceBytes, prepared, dictionary, timing, runInputs, cfg, account] = await Promise.all([
  readBytes(script), read(preparedPath), read(dictionaryPath), read(oldTimingPath), read(runInputsPath), read('config/tts.json'), read(out + '/account_readonly.json')
]);
assert.equal(sha(sourceBytes), expected);
assert.equal(prepared.script_sha256, expected);
assert.equal(timing.script_sha256, expected);
assert.equal(runInputs.prepared_sha256, (await ref(preparedPath)).sha256);
assert.equal(prepared.dictionary_sha256, (await ref(dictionaryPath)).sha256);
assert.equal(cfg.voice_id, '4p6UA7mnodF5q7JFFrnW');
assert.equal(cfg.model, 'eleven_v4');
const source = sourceBytes.toString('utf8');
const sections = [...source.matchAll(/^## (\d+)\. ([^\n]+)\n([\s\S]*?)(?=^## |$(?![\s\S]))/gm)];
assert.equal(sections.length, 10);
const parsed = sections.flatMap(section => section[3].trim().split(/\n\s*\n/).map(text => ({chapter:Number(section[1]), title:section[2], text:text.trim()})));
const grounding = prepared.chapters.flatMap(chapter => chapter.paragraphs.map(p => ({...p, chapter:chapter.chapter, title:chapter.title})));
assert.equal(parsed.length, 54);
assert.equal(grounding.length, 54);
assert.equal(timing.chapters.reduce((sum, chapter) => sum + chapter.paragraphs.length, 0), 54);
const inputs = {
  script:await ref(script), free_tts_v6_manifest:await ref(preparedPath), pronunciation_dictionary:await ref(dictionaryPath),
  previous_audio_timing:await ref(oldTimingPath), previous_run_inputs:await ref(runInputsPath),
  tts_config:await ref('config/tts.json'), brief:await ref(episode + '/brief.json'), state_snapshot:await ref(episode + '/state.json'),
  account_snapshot:await ref(out + '/account_readonly.json')
};
const paragraphs = [];
const proposals = [];
for (let i = 0; i < grounding.length; i++) {
  const p = grounding[i];
  assert.equal(p.text, parsed[i].text);
  assert.equal(p.chapter, parsed[i].chapter);
  assert.equal(p.title, parsed[i].title);
  assert.equal([...source].slice(p.source_start, p.source_end).join(''), p.text);
  assert.equal(p.display_mapping.map(item => item.original).join(''), p.text);
  assert.equal(p.display_mapping.map(item => item.spoken).join(''), p.spoken_text);
  const textRef = await put('paragraphs/' + p.paragraph_id + '.txt', p.text);
  paragraphs.push({paragraph_id:p.paragraph_id, scene_id:'C' + String(p.chapter).padStart(2,'0'), chapter:p.chapter, chapter_title:p.title, paragraph:p.paragraph,
    chapter_paragraph:p.chapter_paragraph, text:p.text, characters:count(p.text), utf8_bytes:Buffer.byteLength(p.text), ...textRef,
    source_start:p.source_start, source_end:p.source_end, offset_unit:'Unicode code points', tts_text_variant:'exact_locked_body'});
  proposals.push({paragraph_id:p.paragraph_id, scene_id:'C' + String(p.chapter).padStart(2,'0'), source_text_sha256:sha(p.text), proposed_spoken_text:p.spoken_text,
    proposed_spoken_text_sha256:sha(p.spoken_text), characters:count(p.spoken_text), character_delta:count(p.spoken_text)-count(p.text),
    substitutions:p.display_mapping.filter(item => item.kind !== 'literal'), display_mapping_grounding:{path:preparedPath, paragraph_id:p.paragraph_id}});
}
const rawCount = paragraphs.reduce((sum,p) => sum+p.characters,0);
const expandedCount = proposals.reduce((sum,p) => sum+p.characters,0);
const body = await put('narration_body.txt', paragraphs.map(p => p.text).join('\n\n'));
const manifest = await put('narration_manifest.json', {
  revision:'jun-replacement-v1-exact-body', created_at_utc:at, script_revision:'script-final-v6', script_sha256:expected,
  inputs, status:'frozen_preparation_only', text_policy:'확정 SHA의 본문 54문단을 완전 일치로 고정. 제목·머리말·추가 태그·발음 치환 제외.',
  paragraph_count:54, chapter_count:10, characters:rawCount, character_count_basis:'각 문단 Unicode code point 합계. 공백·문장부호 포함, 문단 사이 구분자와 TXT 끝 개행 없음.',
  body_file:{...body, characters_with_separators:count(paragraphs.map(p => p.text).join('\n\n')), separator:'LF LF', separator_characters_excluded_from_54_requests:106},
  voice:{provider:cfg.provider, voice_id:cfg.voice_id, voice_name:cfg.voice_name, model:cfg.model, style:cfg.style}, paragraphs
});
const pronunciation = await put('pronunciation_proposal.json', {
  revision:'jun-replacement-v1-phonetics-candidate', created_at_utc:at, status:'proposed_not_applied_not_authorized_for_generation',
  script_sha256:expected, raw_manifest:manifest, grounding:inputs.free_tts_v6_manifest, dictionary:inputs.pronunciation_dictionary,
  policy:'기존 무료 TTS v6 spoken_text와 발음 대응을 그대로 후보로 제시. 원문·표시 자막·확정 대본은 변경하지 않음. 실제 Jun 청취로 검증하지 않음.',
  aliases:dictionary.aliases, overrides:dictionary.overrides, observed_entries:dictionary.observed_entries, rules:dictionary.rules,
  paragraph_count:54, characters:expandedCount, character_delta:expandedCount-rawCount, actual_listening:false, paragraphs:proposals
});
const sceneIds = prepared.chapters.map(c => 'C' + String(c.chapter).padStart(2,'0'));
const timingPlan = await put('timing_proposals.json', {
  revision:'jun-replacement-v1-preparation', created_at_utc:at, audio_revision:'jun-replacement-v1-not-generated',
  scope:'계획만 고정. Jun 시작/끝·길이·기존 대비 delta는 측정 전 null. 기존 실측값은 참조용이며 Jun estimate 또는 확정 타임코드가 아님.',
  previous_timing:inputs.previous_audio_timing, previous_audio_revision:'production-injoon-v6', proposed_changed_scene_ids:sceneIds, actual_changed_scene_ids:[],
  previous_body_seconds:timing.chapters.reduce((sum,c) => sum+c.total_seconds,0), new_body_seconds:null, timing_delta_s:null,
  scenes:timing.chapters.map(c => ({scene_id:'C'+String(c.chapter).padStart(2,'0'), start_s:null, end_s:null, measured_seconds:null, estimate_seconds:null,
    timing_basis:'pending_actual_Jun_audio_and_character_alignment', confidence:'unmeasured', audio_revision:'jun-replacement-v1-not-generated',
    previous_measured_seconds:c.total_seconds, previous_audio_revision:'production-injoon-v6', timing_delta_s:null,
    planned_replacement_paragraph_ids:paragraphs.filter(p => p.chapter===c.chapter).map(p => p.paragraph_id)})),
  readiness_steps:[
    '총괄이 마케팅 제안 단계와 사용자 예산 결정 순서를 관리. 현재 생성 실행 승인은 없음.',
    '승인 대상 대본 SHA·선택 텍스트 manifest SHA·voice/model·현재 저장 속도0.97·해당 비용 상한을 명시하고 실행 직전 재검증.',
    '실행 직전 구독 잔여량·요율·접근 가능 여부를 GET으로 갱신. 같은 계정의 병렬 소비를 합산하여 예산을 예약하고 초과 시 중단.',
    '승인 후에만 문단별 timestamps 생성 경로를 사용. audio와 alignment/normalized_alignment를 원문 텍스트 SHA에 연결하여 보존. 자동 재시도 없음.',
    '문단 음성 PCM 프레임/샘플레이트로 실제 길이를 측정하고, 타임스탬프 개수·단조 증가·범위·문자열 대응을 검사. 미지원/실패 시 다른 모델로 자동 전환하지 않고 총괄에게 보고.',
    '발음 확장안 선택 시 v6 display_mapping으로 원문 숫자·단위·약어를 자막에 역매핑. 추정 시간을 실제 정렬로 기록하지 않음.',
    '기존 chapter 선행 무음·문단 간격·tail 규칙을 편집 담당과 합의해 새 길이에 적용. 총괄 확정 전 공통 장면표를 쓰지 않음.',
    '숫자·고유명사·문장 경계·자연스러움은 실제 청취 담당이 확인. ASR/파형만으로 청취 완료 처리하지 않음.',
    'scene_id별 새 길이·변경 문장·timing delta와 changed_scene_ids를 editor/총괄에 전달. 의미 단위 자막과 영향 장면만 재정렬 후 독립 검수.',
    '새 비공개본의 처리·자막·내용 검증을 마친 뒤에만 총괄이 기존 비공개본 삭제 여부를 처리. 본 작업은 업로드/삭제를 실행하지 않음.'
  ]
});
const rates = account.model?.model_rates;
const voiceRate = account.voice?.sharing?.rate;
const unit = [rates?.character_cost_multiplier, rates?.cost_discount_multiplier, voiceRate].every(x => typeof x==='number' && x>0)
  ? rates.character_cost_multiplier * rates.cost_discount_multiplier * voiceRate : null;
const scenario = (id, characters, reference, maxParagraph) => {
  const reserve = Math.ceil(characters * .2);
  return {variant:id, manifest:reference, input_characters:characters, paragraph_requests:54, revision_reserve_ratio:.2, revision_reserve_characters:reserve,
    character_cap:characters+reserve, estimated_first_pass_credits:unit===null?null:Math.ceil(characters*unit),
    proposed_included_credit_cap:unit===null?null:Math.ceil((characters+reserve)*unit), max_paragraph_characters:maxParagraph,
    generation_authorized:false};
};
const scenarios = [scenario('exact_locked_body',rawCount,manifest,Math.max(...paragraphs.map(p=>p.characters))),
  scenario('proposed_v6_pronunciation_expansion',expandedCount,pronunciation,Math.max(...proposals.map(p=>p.characters)))];
const cap = unit===null ? null : Math.max(...scenarios.map(s=>s.proposed_included_credit_cap));
const remaining = account.subscription?.included_remaining ?? null;
const creditFit = typeof remaining==='number' && typeof cap==='number' ? remaining>=cap : null;
const checks = {
  authenticated_gets_http_200:account.requests.every(r=>r.http_status===200), active_subscription:account.subscription?.status==='active',
  approved_model_found:account.model_found, model_supports_tts:account.model?.can_do_text_to_speech===true, model_supports_korean:account.model?.supports_korean===true,
  voice_get_accessible:account.voice?.approved_voice_id_matches===true,
  voice_model_fine_tuned:account.voice?.fine_tuning_state_for_approved_model==='fine_tuned',
  all_paragraphs_within_model_limit:scenarios.every(s=>s.max_paragraph_characters<=account.model?.maximum_text_length_per_request),
  overage_disabled:account.subscription?.max_credit_limit_extension===0 && account.subscription?.can_extend_character_limit===false && account.subscription?.allowed_to_extend_character_limit===false,
  cap_fits_included:creditFit
};
const budget = await put('budget_proposal.json', {
  task_id:'housing-choice-jun-replacement-v1-preparation', status:'prepared_for_director_budget_review_generation_not_authorized', at_utc:at,
  scope:'Jun 교체 준비만. 마케팅 제안 작업과 승인 순서는 총괄 담당.', script_revision:'script-final-v6', script_sha256:expected,
  narration_manifest_sha256:manifest.sha256, pronunciation_proposal_sha256:pronunciation.sha256, inputs,
  voice:{provider:cfg.provider,voice_id:cfg.voice_id,voice_name:cfg.voice_name,model:cfg.model,approved_style:cfg.style,
    observed_stored_settings:account.voice?.settings ?? null, settings_provenance:'2026-10-26 GET 현재 저장값. 선택된 모델/voice 승인과 구분하며 설정 변경은 실행하지 않음.'},
  input_characters:rawCount, proposed_expanded_input_characters:expandedCount, paragraph_requests:54, text_variant_selected_for_generation:null, scenarios,
  account_checked_at_utc:account.checked_at_utc, included_remaining:remaining, credit_limit:account.subscription?.character_limit ?? null,
  used_credits:account.subscription?.character_count ?? null, model_rates:rates ?? null, voice_rate:voiceRate ?? null,
  estimated_credits_per_character:unit, estimate_basis:'현재 조회 배수1×1 및 voice rate1에 한해 1자=1크레딧 추정. 실제 청구를 측정한 값이 아님. 두 텍스트 후보 예산은 합산하지 않음.',
  proposed_cap:cap, proposed_included_credit_cap:cap, proposed_cap_basis:'두 후보 중 큰 값에 ceil(20%) 수정 글자 예비분을 더한 검토 상한. 확장안 채택 승인을 뜻하지 않음.',
  proposed_revision_reserve_characters:scenarios[1].revision_reserve_characters, cap_fits_included:creditFit,
  included_headroom_after_proposed_cap:creditFit===null?null:remaining-cap, additionalcash0:true, additional_cash_usd_cap:0,
  topup_or_overage_authorized:false, recharge_allowed:false, automatic_retry:false, shared_account_reservation_made:false,
  snapshot_not_a_reservation:true, generation_started:false, generation_authorized:false, sample_generated:false, tts_post_calls:0, paid_generation_calls:0, upload_calls:0, delete_calls:0,
  readiness_checks:checks, account_checks_passed:Object.values(checks).every(x=>x===true),
  caveats:[
    'GET 접근·fine_tuned·high_quality_base_model_ids에서 v4를 확인했으나 TTS 호출 성공은 미검증.',
    '모델 응답 serves_pro_voices=false와 Jun category=professional은 기록상 차이. 지원 모델 목록/fine_tuned는 일치하므로 자동 교체하지 않고 실제 실행 전 담당이 검토.',
    'v4 can_use_style=false, can_use_speaker_boost=false. 저장 style1/boost true를 지원되는 요청 파라미터로 간주하지 않음. 속도0.97을 변경하거나 다른 모델로 자동 우회하지 않음.',
    '잔여 크레딧은 조회 시점 스냅샷이며 다른 작업 소비로 달라질 수 있음. 상한은 실제 실행 전 다시 확인.',
    '확장안은 기존 free-TTS 표기 제안이며 Jun 발음 품질 검증 결과가 아님.',
    '파일의 머리말은 script-final-v5로 남아 있으나 사용자 지정 v6 경로/확정 SHA가 일치함. 본문이나 머리말 수정 없음.'
  ],
  network_evidence:{initial_sandbox_block:'EACCES, 세 GET 모두 HTTP 응답 전 실패', initial_attempt:out+'/account_readonly.sandbox-blocked.json',
    resolution:'명시 승인된 GET 세 건만 제한 해제 실행하여 모두 HTTP200. TTS POST 없음.'},
  api_docs_checked_at_utc:at, api_docs:[
    {url:'https://elevenlabs.io/docs/api-reference/user/subscription/get', checked:true, used_for:'사용량/한도 필드와 max_credit_limit_extension=0 의미'},
    {url:'https://elevenlabs.io/docs/api-reference/models/list', checked:true, used_for:'모델 지원·언어·요율·최대 요청 길이 필드'},
    {url:'https://elevenlabs.io/docs/api-reference/voices/get', checked:true, used_for:'음성 GET·현재 settings·sharing.rate 필드'},
    {url:'https://elevenlabs.io/docs/eleven-creative/voices/voice-library/', checked:true, used_for:'공식 검색 결과의 custom rate 크레딧 배수 설명; 전체 페이지 정독 아님'},
    {url:'https://elevenlabs.io/docs/api-reference/text-to-speech/convert-with-timestamps', checked:true, used_for:'승인 후 문자별 alignment/normalized_alignment 계획; POST 실행 없음'}
  ], timing_readiness:timingPlan
});
const issue = await put('issue_JUN_PREPARATION_REVIEW.json', {
  issue_id:'JUN_PREPARATION_REVIEW', scene_ids:sceneIds, severity:'review_before_generation', status:'proposed_to_director_no_peer_message_tool',
  problem:'생성 전 텍스트 후보/예산 범위 확정과 v4 요청 옵션 지원 검토 필요.',
  evidence:{budget, exact_manifest:manifest, pronunciation_proposal:pronunciation, account_snapshot:inputs.account_snapshot},
  proposal:'마케팅 제안을 우선 완료한 뒤 동일 SHA/Jun v4/추가 현금0/10,739크레딧 이하 범위로 결정. 발음 치환은 별도 후보 선택으로 기록. v4가 지원하지 않는 style/boost를 무조건 전송하거나 모델/속도를 변경하지 않음.',
  impact:'10장54문단의 음성이 교체되면 모든 실제 타이밍을 다시 측정. 현재 편집·공통 시간표·기존 비공개본은 그대로 보존.',
  requested_decision:'총괄이 budget 게이트와 텍스트 선택을 관리. 실제 생성은 현재 범위 밖.', next_roles:['video_director','video_editor']
});
const outputs = [manifest, pronunciation, body, budget, timingPlan, issue, inputs.account_snapshot, await ref(out+'/account_readonly.sandbox-blocked.json')];
await put('handoff.json', {
  task_id:'housing-choice-jun-replacement-v1-preparation',role:'video_narration',status:'준비 완료·생성 미승인',
  input_revisions:{script_revision:'script-final-v6',script_sha256:expected,manifest_sha256:manifest.sha256,pronunciation_proposal_sha256:pronunciation.sha256,tts_config_sha256:inputs.tts_config.sha256},
  outputs,affected_scene_ids:sceneIds,changed_scene_ids:[],
  checks:[{check:'본문·근거',result:'10장54문단·확정SHA/무료v6 manifest/원문 offset 일치',evidence:manifest.path},
    {check:'예산',result:`원문${rawCount}자·확장후보${expandedCount}자·20%포함상한${cap}크레딧·잔여${remaining}·추가현금0달러`,evidence:budget.path},
    {check:'API',result:'인증 GET3건 HTTP200; 생성/샘플/충전/업로드/삭제0',evidence:inputs.account_snapshot.path}],
  account_checked_at_utc:account.checked_at_utc,open_issue_ids:['JUN_PREPARATION_REVIEW'],
  unresolved:'발음 확장안은 미채택. Jun 음성/실제길이/타임스탬프/청취 미확인. v4 style·boost 비지원 및 professional 플래그 차이는 예산 제안 caveats에 기록. 검증 증거는 validation.json.',
  next_role:'video_director → 승인 후 narration → editor → 독립 QA',
  summary:'마케팅 제안 우선. 준비 자료만 작성. 공통 상태·장면·결정과 기존 영상/오디오를 수정하지 않음.'
});
console.log(JSON.stringify({paragraphs:54,chapters:10,raw_characters:rawCount,proposed_spoken_characters:expandedCount,revision_reserve:scenarios[1].revision_reserve_characters,
  proposed_cap:cap,included_remaining:remaining,headroom:remaining-cap,additional_cash_usd_cap:0,script_sha256:expected,manifest_sha256:manifest.sha256,
  pronunciation_proposal_sha256:pronunciation.sha256,budget_proposal:budget.path,handoff:out+'/handoff.json'}));
