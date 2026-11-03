// Read-only adaptation of the existing account helper. No synthesis or account changes.
import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const outDir = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(outDir, '../../../../..');
const helperRel = 'video-agent-studio/episodes/namyangju-wangsuk-20261014/narration/series-hook-v6/preflight.mjs';
const helper = path.join(root, helperRel);
const cfg = JSON.parse(await fs.readFile(path.join(root, 'config/tts.json'), 'utf8'));
const allowed = new Set(['/v1/user/subscription', '/v1/models', '/v1/voices/' + cfg.voice_id]);
const originalFetch = globalThis.fetch;
const captured = {};
const requests = [];
globalThis.fetch = async (url, options = {}) => {
  const u = new URL(url);
  if (u.origin !== 'https://api.elevenlabs.io' || !allowed.has(u.pathname) || (options.method ?? 'GET') !== 'GET') {
    throw new Error('Read-only endpoint guard');
  }
  const receipt = { method: 'GET', endpoint: u.pathname, http_status: null };
  requests.push(receipt);
  const response = await originalFetch(url, { ...options, redirect: 'error' });
  receipt.http_status = response.status;
  if (response.ok) captured[u.pathname] = await response.clone().json();
  return response;
};
let helperPassed = false;
let error = null;
try {
  const { account } = await import(pathToFileURL(helper).href);
  const result = await account();
  helperPassed = result.safe.passed === true;
} catch (e) {
  error = { name: e.name, reason: /^GET HTTP \d+$|^Account\/credit\/rate preflight failed$|^Voice configuration mismatch$/.test(e.message) ? e.message : '계정 조회 실패; 비밀값·원시 응답은 저장하지 않음', network_code: e.cause?.code ?? null };
} finally {
  globalThis.fetch = originalFetch;
}
const s = captured['/v1/user/subscription'];
const v = captured['/v1/voices/' + cfg.voice_id];
const m = captured['/v1/models']?.find(x => x.model_id === cfg.model);
const safe = {
  checked_at_utc: new Date().toISOString(),
  status: helperPassed ? 'read_only_checks_passed' : 'read_only_checks_incomplete_or_failed',
  helper: { path: helperRel, sha256: crypto.createHash('sha256').update(await fs.readFile(helper)).digest('hex'), passed: helperPassed },
  requests, automatic_retries: 0, generation_started: false, paid_generation_calls: 0,
  configured: { provider: cfg.provider, model: cfg.model, voice_id: cfg.voice_id, voice_name: cfg.voice_name, style: cfg.style },
  subscription: s ? { tier: s.tier, status: s.status, character_count: s.character_count, character_limit: s.character_limit, included_remaining: s.character_limit - s.character_count, can_extend_character_limit: s.can_extend_character_limit, allowed_to_extend_character_limit: s.allowed_to_extend_character_limit, max_credit_limit_extension: s.max_credit_limit_extension } : null,
  voice: v ? { voice_id: v.voice_id, name: v.name, sharing_rate: v.sharing?.rate ?? null, credit_multiplier: v.credit_multiplier ?? v.sharing?.credit_multiplier ?? null, settings: v.settings ? { stability: v.settings.stability, similarity_boost: v.settings.similarity_boost, style: v.settings.style, use_speaker_boost: v.settings.use_speaker_boost, speed: v.settings.speed } : null, fine_tuning_state: v.fine_tuning?.state?.[cfg.model] ?? null } : null,
  model: m ? { model_id: m.model_id, can_do_text_to_speech: m.can_do_text_to_speech, model_rates: m.model_rates, token_cost_factor: m.token_cost_factor, maximum_text_length_per_request: m.maximum_text_length_per_request, can_use_style: m.can_use_style, can_use_speaker_boost: m.can_use_speaker_boost } : null,
  error
};
await fs.writeFile(path.join(outDir, 'account_readonly.json'), JSON.stringify(safe, null, 2) + '\n');
console.log(JSON.stringify({ status: safe.status, remaining: safe.subscription?.included_remaining ?? null, model: safe.model, voice: safe.voice, requests: requests.length, paid_generation_calls: 0, error }));
