globalThis.fetch = async () => { await fs.appendFile("C:\\projects\\realestate_reco\\video-agent-studio\\episodes\\regional-price-recovery-20261022\\narration\\production-v1\\.offline-tests\\network_attempts.jsonl", "ATTEMPT\n"); throw Error("OFFLINE TEST: NETWORK DISABLED"); };
// Offline by default. Only --execute-approved enables the existing ElevenLabs account/request pattern.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import {DIR, ROOT, EP, SCRIPT_SHA, MANIFEST_SHA, VOICE, MODEL, CAP, RATE, COMPLETE, sha, readJSON,
  exists, saveJSON, rel, loadInputs, identity, validateAlignment, checkAccount, checkRates, costHeader,
  checkBudget, findFFmpeg, decode, verifyComplete, loadReceipts} from './common.mjs';

export function validateAuthorization(a, d, inputs, decisionSha, now = Date.now()) {
  assert.equal(a.root_execution_authorized, true); assert.equal(a.paid_api_authorized, true);
  assert.equal(a.external_transmission_authorized, true); assert.equal(a.episode_id, 'regional-price-recovery-20261022');
  assert.equal(a.production_revision, 'production-v1-jun'); assert.equal(a.script_revision, 'v3');
  assert.equal(a.script_sha256, SCRIPT_SHA); assert.equal(a.narration_manifest_sha256, MANIFEST_SHA);
  assert.equal(a.config_sha256, inputs.config_sha256); assert.equal(a.budget_proposal_sha256, inputs.quote_sha256);
  assert.equal(a.voice_id, VOICE); assert.equal(a.model, MODEL); assert.deepEqual(a.generator_code_sha256, inputs.code);
  assert.equal(a.included_credit_cap, CAP); assert.equal(a.additional_cash_usd_cap, 0);
  assert.equal(a.automatic_retry, false); assert.equal(a.topup_or_overage_authorized, false);
  assert.match(a.budget_decision_id, /^[a-f0-9]{12}$/); assert.equal(a.budget_decision_sha256, decisionSha);
  const issued = Date.parse(a.issued_at), expires = Date.parse(a.expires_at);
  assert.ok(Number.isFinite(issued) && Number.isFinite(expires) && issued <= now && expires > now);
  assert.ok(now - issued <= 86400000 && expires - issued <= 86400000, 'Fresh authorization required (maximum 24 hours)');
  assert.equal(d.id, a.budget_decision_id); assert.equal(d.gate, 'budget'); assert.equal(d.episode, a.episode_id);
  assert.equal(d.status, 'approved', 'Budget decision is not approved');
  assert.equal(d.artifact_hashes?.['script_v3.md'], SCRIPT_SHA);
  assert.equal(d.artifact_hashes?.narration_manifest, MANIFEST_SHA);
  assert.equal(d.included_credit_cap, CAP); assert.equal(d.additional_cash_usd_cap, 0); assert.equal(d.automatic_retry, false);
  assert.ok(Date.parse(d.created_at) <= issued && Date.parse(d.expires_at) > now, 'Decision expired or authorization predates decision');
}
async function getAuthorization(inputs) {
  const bytes = await fs.readFile(path.join(DIR, 'authorization.json'));
  const a = JSON.parse(bytes.toString().replace(/^\uFEFF/, ''));
  assert.match(a.budget_decision_id ?? '', /^[a-f0-9]{12}$/);
  const decision = await fs.readFile(path.join(ROOT, 'output/video_decisions/decisions', a.budget_decision_id + '.json'));
  const d = JSON.parse(decision.toString().replace(/^\uFEFF/, ''));
  validateAuthorization(a, d, inputs, sha(decision));
  return {a, authorization_sha256: sha(bytes), budget_decision_sha256: sha(decision)};
}
export async function main(args = process.argv.slice(2)) {
  assert.ok(args.length === 0 || (args.length === 1 && args[0] === '--execute-approved'), 'Unknown argument');
  const inputs = await loadInputs();
  if (!args.includes('--execute-approved')) {
    let ffmpeg; try {ffmpeg = findFFmpeg();} catch {ffmpeg = null;}
    const result = {status: 'prepared_offline_only', script_sha256: SCRIPT_SHA, manifest_sha256: MANIFEST_SHA,
      config_sha256: inputs.config_sha256, budget_proposal_sha256: inputs.quote_sha256, generator_code_sha256: inputs.code,
      characters: inputs.characters, sequential_requests: 39, included_credit_cap: CAP,
      ffmpeg_path: ffmpeg, ffmpeg_ready: !!ffmpeg, network_calls: 0, paid_calls: 0, authorization_checked: false,
      audio_generated: false, actual_listening: false};
    await saveJSON(path.join(DIR, 'offline_preflight.json'), result);
    console.log(JSON.stringify(result)); return result;
  }
  // Authorization and local decode readiness must pass BEFORE account GETs or any POST.
  const auth = await getAuthorization(inputs);
  await loadReceipts(inputs); // Reject pending/failed receipts before ffmpeg or any network access.
  const ff = findFFmpeg();
  const lockPath = path.join(DIR, '.generation.lock');
  await saveJSON(lockPath, {pid: process.pid, at: new Date().toISOString(), authorization_sha256: auth.authorization_sha256}, true);
  try {
    process.chdir(ROOT); // Read-only proven account() resolves config/.env relative to workspace.
    const receipts = await loadReceipts(inputs); let actual = 0;
    for (const beat of inputs.manifest.paragraphs) {
      const r = receipts.get(beat.beat_id); if (!r) continue;
      assert.equal(r.budget_decision_sha256, auth.budget_decision_sha256, 'Prior receipt uses a different budget decision');
      await verifyComplete(inputs, beat, r, ff); actual += r.actual_credits;
    }
    for (const beat of inputs.manifest.paragraphs.filter(b => !receipts.has(b.beat_id))) {
      for (const suffix of ['.mp3', '.alignment.json', '.normalized_alignment.json'])
        assert.equal(await exists(path.join(DIR, beat.beat_id + suffix)), false, 'Orphan output blocks a new charge');
    }
    let remaining = inputs.manifest.paragraphs.filter(b => !receipts.has(b.beat_id)).reduce((n, b) => n + b.characters, 0);
    checkBudget(actual, 0, remaining);
    if (remaining) {
      const {account} = await import(pathToFileURL(path.join(ROOT,
        'video-agent-studio/episodes/namyangju-wangsuk-20261014/narration/series-hook-v6/preflight.mjs')).href);
      const accountData = await account(); checkRates(accountData.safe);
      assert.ok(accountData.safe.included_remaining >= remaining, 'Insufficient live included credits');
      await saveJSON(path.join(DIR, 'account_preflight.json'), accountData.safe);
      await fs.mkdir(path.join(DIR, 'receipts'), {recursive: true});
      for (const beat of inputs.manifest.paragraphs) {
        if (receipts.has(beat.beat_id)) continue;
        // Recheck authorization, frozen files, and included-only account before every charge.
        const currentInputs = await loadInputs(); assert.deepEqual(currentInputs.code, inputs.code);
        const currentAuth = await getAuthorization(currentInputs); assert.deepEqual(currentAuth, auth);
        const subscription = await accountData.get('/v1/user/subscription'); checkAccount(subscription, remaining);
        checkBudget(actual, beat.characters, remaining - beat.characters);
        const rp = path.join(DIR, 'receipts', beat.beat_id + '.json');
        const receipt = {status: 'pending_no_automatic_retry', identity: identity(inputs, beat),
          started_at: new Date().toISOString(), authorization_sha256: auth.authorization_sha256,
          budget_decision_id: auth.a.budget_decision_id, budget_decision_sha256: auth.budget_decision_sha256,
          reserved_credits: beat.characters, actual_credits: null, charge_known: false, actual_listening: false,
          account_before: {character_count: subscription.character_count, character_limit: subscription.character_limit,
            included_remaining: subscription.character_limit - subscription.character_count},
          request: {text: beat.text, model_id: MODEL},
          request_url: 'https://api.elevenlabs.io/v1/text-to-speech/' + VOICE + '/with-timestamps?output_format=mp3_44100_128'};
        // Durable receipt precedes POST. Any ambiguous result remains a permanent stop for this version.
        await saveJSON(rp, receipt, true);
        try {
          const response = await fetch(receipt.request_url, {method: 'POST', redirect: 'error',
            headers: {...accountData.headers, 'Content-Type': 'application/json'},
            body: JSON.stringify(receipt.request), signal: AbortSignal.timeout(180000)});
          receipt.http_status = response.status;
          receipt.request_id = response.headers.get('request-id') ?? response.headers.get('x-request-id');
          receipt.character_cost_header = response.headers.get('character-cost');
          // Allowlist headers only; never serialize credentials, SDK objects or raw network errors.
          receipt.response_headers = Object.fromEntries(['request-id', 'x-request-id', 'character-cost', 'content-type', 'date']
            .map(k => [k, response.headers.get(k)]));
          await saveJSON(rp, receipt);
          assert.ok(response.ok, 'TTS HTTP ' + response.status);
          const body = await response.json();
          assert.ok(typeof body.audio_base64 === 'string' && /^[A-Za-z0-9+/=\r\n]+$/.test(body.audio_base64), 'Missing audio');
          const bytes = Buffer.from(body.audio_base64, 'base64'); assert.ok(bytes.length > 100);
          const audio = beat.beat_id + '.mp3', alignment = beat.beat_id + '.alignment.json';
          const normalized = beat.beat_id + '.normalized_alignment.json';
          await fs.writeFile(path.join(DIR, audio), bytes, {flag: 'wx'});
          await saveJSON(path.join(DIR, alignment), body.alignment ?? null, true);
          await saveJSON(path.join(DIR, normalized), body.normalized_alignment ?? null, true);
          receipt.artifact_sha256 = Object.fromEntries(await Promise.all([audio, alignment, normalized]
            .map(async f => [f, sha(await fs.readFile(path.join(DIR, f)))])));
          // Unknown charge fails even when valid audio was delivered. Never retry it automatically.
          receipt.actual_credits = costHeader(receipt.character_cost_header, receipt.reserved_credits);
          receipt.charge_known = true; checkBudget(actual + receipt.actual_credits, 0, remaining - beat.characters);
          const pcm = decode(ff, path.join(DIR, audio)); receipt.pcm_samples = pcm.length / 2;
          receipt.pcm_duration_s = receipt.pcm_samples / RATE;
          validateAlignment(body.alignment, beat.text, receipt.pcm_duration_s);
          validateAlignment(body.normalized_alignment, null, receipt.pcm_duration_s);
          const after = await accountData.get('/v1/user/subscription');
          checkAccount(after, remaining - beat.characters);
          receipt.account_after = {character_count: after.character_count, character_limit: after.character_limit,
            included_remaining: after.character_limit - after.character_count, overage_enabled: false};
          receipt.status = COMPLETE; receipt.completed_at = new Date().toISOString();
          await saveJSON(rp, receipt); await verifyComplete(inputs, beat, receipt, ff);
          receipts.set(beat.beat_id, receipt); actual += receipt.actual_credits; remaining -= beat.characters;
          console.log(JSON.stringify({beat_id: beat.beat_id, status: COMPLETE, actual_credits: receipt.actual_credits,
            total_credits: actual, duration_s: receipt.pcm_duration_s}));
        } catch (e) {
          receipt.status = 'failed_no_automatic_retry';
          receipt.error = e instanceof assert.AssertionError ? String(e.message).slice(0, 600) : 'Network, response, permission or local I/O failure; inspect safe receipts and artifacts';
          receipt.failed_at = new Date().toISOString(); await saveJSON(rp, receipt); throw Error(beat.beat_id + ': failed; no retry or duplicate');
        }
      }
    }
    assert.equal(receipts.size, 39); checkBudget(actual, 0, 0);
    const result = {status: COMPLETE, script_sha256: SCRIPT_SHA, manifest_sha256: MANIFEST_SHA,
      actual_credits: actual, reserved_credits: 0, included_credit_cap: CAP, additional_cash_usd: 0,
      beats: [...receipts.keys()], actual_listening: false, timing_locked: false};
    await saveJSON(path.join(DIR, 'generation_receipt.json'), result); return result;
  } finally {await fs.unlink(lockPath);}
}
if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(DIR, 'generate.mjs'))
  main().catch(e => {console.error(e.code === 'ENOENT' ? 'Required local input/authorization missing; no API call authorized.' : e.message); process.exitCode = 1;});
