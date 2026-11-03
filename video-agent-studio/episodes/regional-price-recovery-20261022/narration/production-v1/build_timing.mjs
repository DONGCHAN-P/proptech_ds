import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {DIR, EP, ROOT, SCRIPT_SHA, MANIFEST_SHA, RATE, sha, readJSON, saveJSON, exists, rel,
  loadInputs, loadReceipts, verifyComplete, findFFmpeg, decode} from './common.mjs';

const PAUSE_SAMPLES = Math.round(0.35 * RATE);
const len = s => [...s].length;
// All offsets are Unicode code-point indices in the untouched paragraph, half-open.
const numeric = /^(?:[+-]?[\d,.]+(?:만|억|천)?|[영공일이삼사오육칠팔구십백천만억조두세네한몇]+|점|삼분기|사분기|일분기|이분기)$/u;
const unit = /^(?:년|해|월|개월|분기|퍼센트|배|호|건|채|곳|세대|만|억|천|원|평|제곱미터|㎡|%|분|초)(?:[은는이가을를에의와과도부터까지]|으로|에서|부터|까지|입니다|였습니다|이|였|,|\.)*/u;
const attachedNumberUnit = /^(?:[+-]?[\d,.]+[만억천]?|[영공일이삼사오육칠팔구십백천만억조두세네한몇]+)(?:년|해|월|개월|분기|퍼센트|배|호|건|채|곳|세대|원|평|㎡|%|분|초)(?:은|는|이|가|을|를|에|의|와|과|도|으로|에서|부터|까지|입니다|였습니다)*$/u;
export function atomsFor(text) {
  const tokens = [...text.matchAll(/\S+\s*/gu)].map(m => ({text: m[0], start: len(text.slice(0, m.index)), end: len(text.slice(0, m.index + m[0].length))}));
  const atoms = [];
  for (let i = 0; i < tokens.length; i++) {
    let a = {...tokens[i]}; const bare = s => s.trim().replace(/[,.;!?]$/u, '');
    if (/^(?:약|최대|최소)$/u.test(a.text.trim()) && i + 1 < tokens.length &&
      (numeric.test(bare(tokens[i+1].text)) || attachedNumberUnit.test(bare(tokens[i+1].text)))) {
      a.text += tokens[++i].text; a.end = tokens[i].end;
    }
    // Preserve spoken number + decimal + unit chains and multi-part dates/amounts.
    const numericPart = bare(a.text).replace(/^(?:약|최대|최소)\s+/u,'');
    if (numeric.test(numericPart) || attachedNumberUnit.test(numericPart)) {
      while (i + 1 < tokens.length) {
        const next = tokens[i+1].text.trim();
        if (!numeric.test(bare(next)) && !unit.test(next) && !attachedNumberUnit.test(bare(next))) break;
        a.text += tokens[++i].text; a.end = tokens[i].end;
        if (/[.!?,]$/u.test(next)) break;
      }
    }
    assert.ok(len(a.text.trim()) <= 28, 'Protected phrase needs manual caption handling: ' + a.text.trim());
    atoms.push(a);
  }
  return atoms;
}
function linesFor(atoms) {
  const text = atoms.map(a => a.text).join('').trim(); if (len(text) > 55) return null;
  if (len(text) <= 28) return [text];
  let best = null;
  for (let k = 1; k < atoms.length; k++) {
    const a = atoms.slice(0,k).map(x => x.text).join('').trim(), b = atoms.slice(k).map(x => x.text).join('').trim();
    const score = Math.abs(len(a)-len(b)) + (/(?:의|약|각각|그리고|또는)$/u.test(a) ? 40 : 0);
    if (len(a) <= 28 && len(b) <= 28 && (!best || score < best.score)) best = {lines: [a,b], score};
  }
  return best?.lines ?? null;
}
export function captionPlan(text) {
  const atoms = atomsFor(text), n = atoms.length, dp = Array(n+1).fill(Infinity), choices = [];
  dp[n] = 0;
  for (let i = n-1; i >= 0; i--) {
    for (let j = i+1; j <= n; j++) {
      const group = atoms.slice(i,j), raw = group.map(a => a.text).join(''), clean = raw.trim();
      if (len(clean) > 55) break;
      const lines = linesFor(group); if (!lines) continue;
      const boundary = /[.!?]$/u.test(clean) ? 0 : /[,;:]$/u.test(clean) ? 6 : /(?:고|며|면|뒤에|뒤|동안|때|것은|점은|이유는|그래서|보면|하지만|보다|위해|부터|까지)$/u.test(clean) ? 12 : 24;
      const internalSentence = /[.!?]\s+\S/u.test(clean) ? 35 : 0;
      const danglingPhrase = /(?:의|약|각각|그리고|또는)$/u.test(clean) ? 70 : 0;
      const score = 20 + boundary + internalSentence + danglingPhrase + Math.pow((len(clean)-38)/12,2) + dp[j];
      if (score < dp[i]) {dp[i] = score; choices[i] = {j, lines, raw, clean};}
    }
  }
  assert.ok(Number.isFinite(dp[0]), 'Cannot safely split caption');
  const result = [];
  for (let i = 0; i < n;) {
    const c = choices[i], first = atoms[i], last = atoms[c.j-1];
    result.push({source_start: first.start, source_end: last.end, spoken_text: c.raw, text: c.clean,
      display_text: c.clean, lines: c.lines, transformation: 'identity', boundary_basis: 'sentence_clause_then_whole_words'}); i = c.j;
  }
  assert.equal(result.map(c => c.spoken_text).join(''), text);
  return result;
}
export function timedCaptions(text, alignment, beatStart) {
  const chars = [...text]; assert.equal(alignment.characters.length, chars.length, 'Caption adapter requires one alignment item per code point');
  return captionPlan(text).map(c => {
    let a = c.source_start, b = c.source_end;
    while (a < b && /\s/u.test(chars[a])) a++;
    while (b > a && /\s/u.test(chars[b-1])) b--;
    const start = alignment.character_start_times_seconds[a], end = alignment.character_end_times_seconds[b-1];
    assert.ok(end > start, 'Zero-duration caption requires review');
    return {...c, start: beatStart + start, end: beatStart + end, local_start: start, local_end: end,
      timing_basis: 'provider_original_character_alignment', time_origin: 'body', source_index_unit: 'unicode_code_point'};
  });
}
function wavHeader(samples) {
  const b = Buffer.alloc(44), bytes = samples * 2;
  assert.ok(bytes < 0xffffffff - 36);
  b.write('RIFF',0); b.writeUInt32LE(bytes+36,4); b.write('WAVEfmt ',8); b.writeUInt32LE(16,16);
  b.writeUInt16LE(1,20); b.writeUInt16LE(1,22); b.writeUInt32LE(RATE,24); b.writeUInt32LE(RATE*2,28);
  b.writeUInt16LE(2,32); b.writeUInt16LE(16,34); b.write('data',36); b.writeUInt32LE(bytes,40); return b;
}
const stamp = t => {const ms = Math.round(t*1000); return String(Math.floor(ms/3600000)).padStart(2,'0') + ':' + String(Math.floor(ms/60000)%60).padStart(2,'0') + ':' + String(Math.floor(ms/1000)%60).padStart(2,'0') + ',' + String(ms%1000).padStart(3,'0');};
export async function main(args = process.argv.slice(2)) {
  assert.equal(args.length, 0, 'Timing command accepts no arguments; needs actual completed receipts');
  const inputs = await loadInputs(), receipts = await loadReceipts(inputs);
  assert.equal(receipts.size, 39, 'No actual timing lock until all 39 verified complete audio receipts exist');
  assert.equal(await exists(path.join(DIR, '.generation.lock')), false, 'Generation still active/stale lock; director audit required');
  const ff = findFFmpeg(), beats = [], buffers = [], proposals = []; let cursor = 0, narrationSamples = 0;
  const receiptHashes = {};
  for (const [i, beat] of inputs.manifest.paragraphs.entries()) {
    const r = receipts.get(beat.beat_id), v = await verifyComplete(inputs, beat, r, ff);
    receiptHashes[beat.beat_id] = sha(await fs.readFile(path.join(DIR, 'receipts', beat.beat_id+'.json')));
    const start = cursor / RATE, end = (cursor + r.pcm_samples) / RATE;
    const captions = timedCaptions(beat.text, v.alignment, start);
    for (let k = 1; k < captions.length; k++) assert.ok(captions[k].start >= captions[k-1].end, 'Caption overlap requires review');
    assert.ok(captions.every(c => c.start >= start && c.end <= end));
    const lastSpoken = Math.max(...v.alignment.character_end_times_seconds.filter((_, k) => /\S/u.test(v.alignment.characters[k])));
    beats.push({beat_id: beat.beat_id, scene_id: beat.scene_id, audio_path: rel(path.join(DIR, beat.beat_id+'.mp3')),
      duration: v.duration, start, end, start_sample: cursor, duration_samples: r.pcm_samples,
      narration_duration_s: v.duration, pause_after_s: i === 38 ? 0 : PAUSE_SAMPLES/RATE,
      spoken_end: start + lastSpoken, captions, text_sha256: beat.sha256, audio_sha256: r.artifact_sha256[beat.beat_id+'.mp3'],
      timing_basis: 'decoded_pcm_duration_and_provider_original_character_alignment', confidence: 'technical_verified_listening_unverified',
      audio_revision: 'production-v1-jun', actual_listening: false});
    buffers.push(v.pcm); cursor += r.pcm_samples; narrationSamples += r.pcm_samples;
    if (i !== 38) {buffers.push(Buffer.alloc(PAUSE_SAMPLES * 2)); cursor += PAUSE_SAMPLES;}
  }
  for (const scene_id of [...new Set(beats.map(b => b.scene_id))]) {
    const rows = beats.filter(b => b.scene_id === scene_id);
    proposals.push({scene_id, start_s: rows[0].start, end_s: rows.at(-1).end,
      timing_basis: 'actual_decoded_pcm_plus_0.35s_between_paragraphs', confidence: 'technical_verified_listening_unverified', audio_revision: 'production-v1-jun'});
  }
  const timingCode = Object.fromEntries(await Promise.all(['common.mjs','build_timing.mjs'].map(async f => [f,sha(await fs.readFile(path.join(DIR,f)))])));
  const signature = sha(JSON.stringify({script: SCRIPT_SHA, manifest: MANIFEST_SHA, receiptHashes, timingCode, pause_samples: PAUSE_SAMPLES}));
  const lockPath = path.join(DIR, 'timing_lock.json');
  if (await exists(lockPath)) {
    const old = await readJSON(lockPath); assert.equal(old.input_signature, signature, 'Timing inputs changed; preserve old version and ask director for a new output revision');
    for (const [f,h] of Object.entries(old.artifact_sha256)) assert.equal(sha(await fs.readFile(path.join(DIR,f))), h);
    console.log(JSON.stringify({status: 'verified_existing_timing', body_duration_s: old.body_duration_s})); return old;
  }
  const outputNames = ['full_narration.wav','full_narration.mp3','body_captions.srt','timing_proposals.json','caption_mapping.json'];
  for (const f of outputNames) assert.equal(await exists(path.join(DIR,f)), false, 'Existing output without timing lock; manual audit required');
  const staging = path.join(DIR, '.timing-build-' + process.pid); await fs.mkdir(staging);
  const wav = path.join(staging, 'full_narration.wav');
  const handle = await fs.open(wav, 'wx');
  try {await handle.writeFile(wavHeader(cursor)); for (const pcm of buffers) await handle.writeFile(pcm); await handle.sync();} finally {await handle.close();}
  assert.equal(decode(ff, wav).length/2, cursor, 'Combined PCM duration mismatch');
  const mp3 = path.join(staging, 'full_narration.mp3');
  const enc = spawnSync(ff,['-v','error','-i',wav,'-c:a','libmp3lame','-b:a','128k',mp3],{windowsHide:true});
  assert.ok(!enc.error && enc.status === 0, 'Local MP3 encoding failed');
  assert.ok(Math.abs(decode(ff,mp3).length/2 - cursor) <= 1, 'Combined MP3 duration drift');
  const cues = beats.flatMap(b => b.captions.map(c => ({...c, beat_id: b.beat_id, scene_id: b.scene_id})));
  const srt = cues.map((c,i) => (i+1)+'\n'+stamp(c.start)+' --> '+stamp(c.end)+'\n'+c.lines.join('\n')+'\n').join('\n');
  await fs.writeFile(path.join(staging,'body_captions.srt'),srt);
  await saveJSON(path.join(staging,'timing_proposals.json'),{audio_revision:'production-v1-jun', time_origin:'body', proposals});
  await saveJSON(path.join(staging,'caption_mapping.json'),{script_sha256:SCRIPT_SHA, source_index_unit:'unicode_code_point',
    display_policy:'original_text_identity_per_task_RPR-PROD1-JUN-PREP', cues});
  const artifact_sha256 = Object.fromEntries(await Promise.all(outputNames.map(async f => [f,sha(await fs.readFile(path.join(staging,f)))])));
  const result = {script_sha256: SCRIPT_SHA, narration_manifest_sha256: MANIFEST_SHA, script_revision:'v3', audio_revision:'production-v1-jun',
    timing_locked:true, common_timeline_approval:'director_pending', time_origin:'body', caption_time_origin:'global_body',
    intro_offset_s:0, final_assembly_intro_s:5, chapter_transition_owner:'editor', chapter_transition_s_included:0,
    chapter_transition_recommendation_s:1, chapter_transition_note:'Editor must supply a separate time remap if adding chapter gaps; do not add gaps on top of this body timing silently.',
    narration_duration_s:narrationSamples/RATE, pause_duration_s:(38*PAUSE_SAMPLES)/RATE, body_duration_s:cursor/RATE,
    outro_start_body_s:beats.at(-1).spoken_end+3, outro_basis:'provider_original_alignment_last_nonspace_character_end_plus_3s',
    last_audio_end_body_s:beats.at(-1).end, pcm_format:{sample_rate:RATE, channels:1, bits:16},
    actual_listening:false, continuous_playback:false, caption_semantic_review:'automatic_candidate_needs_editor_review',
    changed_scene_ids:proposals.map(p=>p.scene_id), timing_delta:'No previous actual audio; delta not measurable', changed_sentences:[],
    input_signature:signature, receipt_sha256:receiptHashes, timing_code_sha256:timingCode, artifact_sha256, beats};
  assert.ok(result.last_audio_end_body_s <= result.outro_start_body_s, 'Audio tail exceeds the agreed 3s outro gap; editor/director review required');
  for (const f of outputNames) await fs.rename(path.join(staging,f),path.join(DIR,f));
  await saveJSON(lockPath,result,true); // Publish the lock only after all actual outputs have verified hashes.
  console.log(JSON.stringify({status:'actual_timing_built_listening_unverified', beats:39, captions:cues.length, body_duration_s:result.body_duration_s}));
  return result;
}
if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(DIR,'build_timing.mjs'))
  main().catch(e=>{console.error(e.message);process.exitCode=1;});
