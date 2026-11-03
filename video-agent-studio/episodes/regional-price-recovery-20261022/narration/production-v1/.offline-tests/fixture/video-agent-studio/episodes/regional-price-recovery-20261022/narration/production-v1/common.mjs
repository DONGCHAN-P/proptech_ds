import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';

export const DIR = path.dirname(fileURLToPath(import.meta.url));
export const EP = path.resolve(DIR, '../..');
export const ROOT = path.resolve(EP, '../../..');
export const SCRIPT_SHA = '99b40e8730ee0f8fdf74402cffbe04b5b418540344e6d2a7175e6a01c3054664';
export const MANIFEST_SHA = '92ee18d1477d7d513516682e6eacc70e7788f3240e5d7ad36169a5789dc1c322';
export const VOICE = '4p6UA7mnodF5q7JFFrnW';
export const MODEL = 'eleven_v4';
export const CAP = 5807;
export const RATE = 44100;
export const COMPLETE = 'complete_alignment_validated_listening_unverified';
export const sha = x => crypto.createHash('sha256').update(x).digest('hex');
export const readJSON = async p => JSON.parse((await fs.readFile(p, 'utf8')).replace(/^\uFEFF/, ''));
export const exists = async p => {try {await fs.access(p); return true;} catch(e) {if(e.code === 'ENOENT') return false; throw e;}};
export const rel = p => path.relative(ROOT, p).replaceAll('\\', '/');
export async function saveJSON(p, data, exclusive = false) {
  // Same-directory rename is atomic; initial per-request receipt uses exclusive creation + fsync.
  const out = JSON.stringify(data, null, 2) + '\n';
  if (exclusive) {const h = await fs.open(p, 'wx'); try {await h.writeFile(out); await h.sync();} finally {await h.close();} return;}
  const tmp = p + '.' + process.pid + '.tmp';
  const h = await fs.open(tmp, 'w'); try {await h.writeFile(out); await h.sync();} finally {await h.close();}
  await fs.rename(tmp, p);
}
export async function loadInputs() {
  const manifestPath = path.join(DIR, 'manifest.json');
  const scriptPath = path.join(EP, 'outputs/script-review-v3/script_v3.md');
  const configPath = path.join(ROOT, 'config/tts.json');
  const quotePath = path.join(EP, 'outputs/production-v1-budget/budget_proposal.json');
  const [mb, sb, cb, qb] = await Promise.all([manifestPath, scriptPath, configPath, quotePath].map(p => fs.readFile(p)));
  const manifest = JSON.parse(mb.toString().replace(/^\uFEFF/, ''));
  const cfg = JSON.parse(cb.toString().replace(/^\uFEFF/, ''));
  const quote = JSON.parse(qb.toString().replace(/^\uFEFF/, ''));
  assert.equal(sha(mb), MANIFEST_SHA, 'Frozen manifest changed');
  assert.equal(sha(sb), SCRIPT_SHA, 'Approved script changed');
  assert.equal(manifest.script_sha256, SCRIPT_SHA);
  assert.equal(manifest.config_sha256, sha(cb), 'Jun config changed');
  assert.equal(cfg.provider, 'elevenlabs'); assert.equal(cfg.voice_id, VOICE); assert.equal(cfg.model, MODEL);
  assert.equal(manifest.voice_id, VOICE); assert.equal(manifest.model, MODEL); assert.equal(manifest.script_revision, 'v3');
  assert.equal(quote.script_sha256, SCRIPT_SHA); assert.equal(quote.narration_manifest_sha256, MANIFEST_SHA);
  assert.equal(quote.included_credit_cap, CAP); assert.equal(quote.additional_cash_usd_cap, 0);
  assert.equal(quote.automatic_retry, false); assert.equal(quote.topup_or_overage_authorized, false);
  assert.equal(quote.model, MODEL); assert.equal(quote.input_characters, 4839); assert.equal(quote.paragraph_requests, 39);
  // Extract only approved 낭독 blocks; never send screen directions or added tags to TTS.
  const originals = [...sb.toString('utf8').matchAll(/### (S\d{3})\.[\s\S]*?\*\*낭독\*\*\s*([\s\S]*?)\s*\*\*화면\*\*/g)]
    .flatMap(m => m[2].trim().split(/\r?\n\s*\r?\n/).map((text, i) => ({scene_id: m[1], beat_id: m[1] + '-P' + (i + 1), text: text.trim()})));
  assert.equal(originals.length, 39); assert.equal(manifest.paragraphs.length, 39);
  let characters = 0;
  for (const [i, b] of manifest.paragraphs.entries()) {
    assert.match(b.beat_id, /^S\d{3}-P\d+$/); assert.equal(b.path, b.beat_id + '.txt');
    assert.deepEqual({scene_id: b.scene_id, beat_id: b.beat_id, text: b.text}, originals[i], 'Original paragraph/order mismatch');
    const bytes = await fs.readFile(path.join(DIR, b.path));
    assert.equal(bytes.toString('utf8'), b.text); assert.equal(sha(bytes), b.sha256);
    assert.equal([...b.text].length, b.characters); characters += b.characters;
  }
  assert.equal(characters, 4839); assert.equal(manifest.characters, characters);
  const codeFiles = ['common.mjs', 'generate.mjs'];
  const code = Object.fromEntries(await Promise.all(codeFiles.map(async f => [f, sha(await fs.readFile(path.join(DIR, f)))])));
  const accountPath = path.join(ROOT, 'video-agent-studio/episodes/namyangju-wangsuk-20261014/narration/series-hook-v6/preflight.mjs');
  return {manifest, cfg, quote, scriptPath, quote_sha256: sha(qb), config_sha256: sha(cb), code,
    account_module_sha256: sha(await fs.readFile(accountPath)), characters};
}
export function identity(inputs, beat) {
  return {beat_id: beat.beat_id, scene_id: beat.scene_id, script_sha256: SCRIPT_SHA, manifest_sha256: MANIFEST_SHA,
    config_sha256: inputs.config_sha256, quote_sha256: inputs.quote_sha256, generator_sha256: sha(JSON.stringify(inputs.code)),
    account_module_sha256: inputs.account_module_sha256, text_sha256: beat.sha256, voice_id: VOICE, model: MODEL,
    output_format: 'mp3_44100_128'};
}
export function validateAlignment(a, original, duration) {
  assert.ok(a && Array.isArray(a.characters) && a.characters.length > 0, 'Missing alignment');
  if (original !== null) assert.equal(a.characters.join(''), original, 'Alignment must equal original text exactly');
  const ss = a.character_start_times_seconds, es = a.character_end_times_seconds;
  assert.equal(ss?.length, a.characters.length); assert.equal(es?.length, a.characters.length);
  for (let i = 0; i < ss.length; i++) {
    assert.equal(typeof a.characters[i], 'string');
    assert.ok(Number.isFinite(ss[i]) && Number.isFinite(es[i]) && ss[i] >= 0 && es[i] >= ss[i], 'Invalid timestamp');
    if (i) assert.ok(ss[i] >= ss[i-1] && es[i] >= es[i-1], 'Nonmonotonic alignment');
    assert.ok(es[i] <= duration + 1e-6, 'Alignment extends beyond decoded audio');
  }
}
export function checkAccount(s, needed) {
  assert.ok(s.status === 'active' && s.tier !== 'free');
  assert.ok(Number.isFinite(s.character_limit) && Number.isFinite(s.character_count));
  assert.ok(s.character_limit - s.character_count >= needed, 'Insufficient included credits');
  assert.equal(s.can_extend_character_limit, false); assert.equal(s.allowed_to_extend_character_limit, false);
  assert.equal(s.max_credit_limit_extension, 0);
}
export function checkRates(safe) {
  assert.equal(safe.passed, true); assert.equal(safe.overage_enabled, false); assert.equal(safe.allowed_to_extend, false);
  assert.equal(safe.max_extension, 0);
  for (const v of [safe.voice_rate, safe.model_rates?.character_cost_multiplier, safe.model_rates?.cost_discount_multiplier])
    assert.ok(Number.isFinite(v) && v > 0 && v <= 1, 'Voice/model rate must be known and <= 1');
}
export function costHeader(raw, reserved) {
  assert.ok(typeof raw === 'string' && /^\d+(?:\.\d+)?$/.test(raw), 'Missing/unknown character-cost; stop, no retry');
  const n = Number(raw); assert.ok(Number.isFinite(n) && n >= 0 && n <= reserved, 'Charge exceeds reservation'); return n;
}
export function checkBudget(actual, pending, remaining) {
  assert.ok([actual, pending, remaining].every(n => Number.isFinite(n) && n >= 0));
  assert.ok(actual + pending + remaining <= CAP, 'Total actual + reserved exceeds 5807');
}
export function findFFmpeg() {
  const known = 'C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin/ffmpeg.exe';
  for (const p of [process.env.FFMPEG_PATH, 'ffmpeg', known].filter(Boolean)) {
    const r = spawnSync(p, ['-version'], {encoding: 'utf8', windowsHide: true});
    if (!r.error && r.status === 0) return p;
  }
  throw Error('Local ffmpeg unavailable; set FFMPEG_PATH to an accessible existing binary. No API request made.');
}
export function decode(ff, p) {
  const r = spawnSync(ff, ['-v', 'error', '-i', p, '-f', 's16le', '-ac', '1', '-ar', String(RATE), 'pipe:1'],
    {maxBuffer: 128 * 1024 * 1024, windowsHide: true});
  assert.ok(!r.error && r.status === 0, 'Local ffmpeg audio decode failed');
  assert.ok(r.stdout.length > 0 && r.stdout.length % 2 === 0);
  return r.stdout;
}
export async function verifyComplete(inputs, beat, r, ff, base = DIR) {
  assert.equal(r.status, COMPLETE, 'Pending/failed request blocks all continuation; no automatic retry');
  assert.deepEqual(r.identity, identity(inputs, beat), 'Receipt identity changed');
  assert.equal(r.reserved_credits, beat.characters); assert.equal(r.actual_credits, costHeader(r.character_cost_header, r.reserved_credits));
  assert.ok(r.http_status >= 200 && r.http_status < 300); assert.ok(r.budget_decision_sha256); assert.ok(r.authorization_sha256);
  assert.equal(r.request?.text, beat.text); assert.equal(r.request?.model_id, MODEL);
  const names = [beat.beat_id + '.mp3', beat.beat_id + '.alignment.json', beat.beat_id + '.normalized_alignment.json'];
  for (const name of names) assert.equal(sha(await fs.readFile(path.join(base, name))), r.artifact_sha256?.[name], 'Missing/corrupt output: ' + name);
  const pcm = decode(ff, path.join(base, names[0])), duration = pcm.length / 2 / RATE;
  assert.equal(duration, r.pcm_duration_s); assert.equal(pcm.length / 2, r.pcm_samples);
  const alignment = await readJSON(path.join(base, names[1])), normalized = await readJSON(path.join(base, names[2]));
  validateAlignment(alignment, beat.text, duration); validateAlignment(normalized, null, duration);
  return {pcm, duration, alignment, normalized};
}
export async function loadReceipts(inputs) {
  const rd = path.join(DIR, 'receipts'); if (!await exists(rd)) return new Map();
  const expected = new Set(inputs.manifest.paragraphs.map(b => b.beat_id + '.json'));
  const files = await fs.readdir(rd); assert.ok(files.every(f => expected.has(f)), 'Unexpected receipt file; manual audit required');
  const result = new Map(); let gap = false;
  for (const b of inputs.manifest.paragraphs) {
    if (!files.includes(b.beat_id + '.json')) {gap = true; continue;}
    assert.ok(!gap, 'Receipts out of sequence');
    const r = await readJSON(path.join(rd, b.beat_id + '.json'));
    assert.equal(r.status, COMPLETE, b.beat_id + ': pending/failed, no retry or duplicate');
    result.set(b.beat_id, r);
  }
  return result;
}
