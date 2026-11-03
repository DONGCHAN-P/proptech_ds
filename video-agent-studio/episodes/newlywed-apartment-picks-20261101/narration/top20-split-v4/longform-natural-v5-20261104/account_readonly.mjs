// 승인된 세 GET만 실행. 응답 원본, 키, .env, 계정 식별정보는 저장하지 않는다.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const own = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(own, '../../../../../../');
const cfg = JSON.parse((await fs.readFile(path.join(root, 'config/tts.json'), 'utf8')).replace(/^\uFEFF/, ''));
if (cfg.voice_id !== '4p6UA7mnodF5q7JFFrnW' || cfg.model !== 'eleven_v4') throw Error('승인 음성 설정 불일치');
let key = process.env.ELEVENLABS_API_KEY;
if (!key) {
  const env = await fs.readFile(path.join(root, '.env'), 'utf8');
  const match = env.match(/^\s*(?:export\s+)?ELEVENLABS_API_KEY\s*=\s*(.*?)\s*$/m);
  key = match?.[1].replace(/^(['"])(.*)\1$/, '$2');
}
const endpoints = ['/v1/user/subscription', '/v1/models', '/v1/voices/' + cfg.voice_id];
const requests = await Promise.all(endpoints.map(async endpoint => {
  const started_at_utc = new Date().toISOString();
  if (!key) return {endpoint, method:'GET', started_at_utc, status:'credential_missing'};
  try {
    const response = await fetch('https://api.elevenlabs.io' + endpoint, {
      method:'GET', headers:{'xi-api-key':key}, redirect:'error', signal:AbortSignal.timeout(30000)
    });
    const safe = {endpoint, method:'GET', started_at_utc, completed_at_utc:new Date().toISOString(), http_status:response.status, server_date:response.headers.get('date')};
    if (!response.ok) {
      // API 오류 본문의 메시지/PII는 보존하지 않는다.
      const body = await response.json().catch(() => null);
      const code = body?.detail?.status;
      return {...safe, status:'http_error', api_error_code:typeof code === 'string' && /^[a-zA-Z0-9_.-]{1,80}$/.test(code) ? code : null};
    }
    return {...safe, status:'ok', data:await response.json()};
  } catch (error) {
    return {endpoint, method:'GET', started_at_utc, completed_at_utc:new Date().toISOString(), status:'network_error', error_type:error.name, network_code:error.cause?.code ?? error.code ?? null};
  }
}));
const [subResult, modelResult, voiceResult] = requests;
const s = subResult.data;
const m = modelResult.data?.find(item => item.model_id === cfg.model);
const v = voiceResult.data;
const pick = (object, fields) => Object.fromEntries(fields.filter(field => object?.[field] !== undefined).map(field => [field, object[field]]));
const subscription = s ? {
  ...pick(s, ['tier','status','character_count','character_limit','max_credit_limit_extension','max_character_limit_extension','can_extend_character_limit','allowed_to_extend_character_limit','next_character_count_reset_unix']),
  included_remaining:Number.isFinite(s.character_limit) && Number.isFinite(s.character_count) ? s.character_limit - s.character_count : null
} : null;
const model = m ? {
  ...pick(m, ['model_id','name','can_do_text_to_speech','can_use_style','can_use_speaker_boost','serves_pro_voices','requires_alpha_access','maximum_text_length_per_request','max_characters_request_subscribed_user']),
  model_rates:pick(m.model_rates, ['character_cost_multiplier','cost_discount_multiplier']),
  supports_korean:m.languages?.some(language => language.language_id === 'ko') ?? null
} : null;
const voice = v ? {
  voice_id:v.voice_id, approved_voice_id_matches:v.voice_id === cfg.voice_id,
  ...pick(v, ['category','available_for_tiers','high_quality_base_model_ids']),
  settings:pick(v.settings, ['stability','similarity_boost','style','speed','use_speaker_boost']),
  sharing:pick(v.sharing, ['status','rate','free_users_allowed','review_status','enabled_in_library','disable_at_unix']),
  fine_tuning_state_for_approved_model:v.fine_tuning?.state?.[cfg.model] ?? null
} : null;
const snapshot = {
  checked_at_utc:new Date().toISOString(), status:requests.every(r => r.status === 'ok') ? 'read_only_queries_succeeded' : 'read_only_queries_incomplete',
  requests:requests.map(({data,...safe}) => safe), subscription, model_found:Boolean(m), model, voice,
  tts_post_calls:0, paid_generation_calls:0, automatic_retries:0, raw_responses_saved:false,
  confidentiality:'키·환경파일·계정 ID·청구서·이메일·응답 원본은 출력/복사/저장하지 않음'
};
await fs.writeFile(path.join(own, 'account_readonly.json'), JSON.stringify(snapshot, null, 2) + '\n');
console.log(JSON.stringify({status:snapshot.status, requests:snapshot.requests, included_remaining:subscription?.included_remaining ?? null, model_found:snapshot.model_found, model_rates:model?.model_rates ?? null, voice_access_http:voiceResult.http_status ?? null, voice_rate:voice?.sharing.rate ?? null, voice_settings:voice?.settings ?? null}));
