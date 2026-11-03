"""Read-only v4 inspection; all persistent outputs stay in this QA directory."""
from pathlib import Path
import hashlib, json, subprocess, wave
from datetime import datetime, timezone
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
EP = HERE.parents[1]
ROOT = EP.parents[2]
FF = ROOT / 'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
PROBE = ROOT / 'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'
EDITOR = EP / 'editor/jun-quality-v2/shorts'
DIRECTOR = EP / 'director/shorts-ending-fix-v1'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def load(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def save(p, data):
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def level(x):
    rms = float(np.sqrt(np.mean(np.asarray(x, dtype=float)**2)))
    return round(float(20*np.log10(max(1e-10, rms))), 3)

def readwav(p):
    with wave.open(str(p), 'rb') as w:
        assert w.getnchannels() == 1 and w.getsampwidth() == 2
        return w.getframerate(), np.frombuffer(w.readframes(w.getnframes()), dtype='<i2')

tracked = [EDITOR/'edit_plan.json', EDITOR/'build_shorts.py', DIRECTOR/'diagnosis.json',
           DIRECTOR/'asr_boundaries.json', DIRECTOR/'quiet_candidates.json',
           EP/'state.json', EP/'brief.json', EP/'narration/jun-user-script-v1/scene_alignment.json']
fingerprints = []
for p in tracked:
    data = p.read_bytes()
    fingerprints.append(dict(path=str(p), sha256=hashlib.sha256(data).hexdigest(), bytes=len(data)))
    if p.parent in [EDITOR, DIRECTOR]:
        (HERE/('input_'+p.name)).write_bytes(data)
plan = load(HERE/'input_edit_plan.json')
assert [p['name'] for p in plan['shorts']] == ['01_promo_jun_v4', '02_summary_jun_v4']
quiet = {(q['id'], q['scene_id']): q for q in load(HERE/'input_quiet_candidates.json')}
latest_cuts = {('promo','S02'):24.345, ('promo','S03'):50.430, ('promo','S25'):83.525,
               ('summary','S13'):21.7075, ('summary','S14'):34.390, ('summary','S28'):31.090}
asr = {q['id']: q for q in load(HERE/'input_asr_boundaries.json')}
pcm = {}
rows, media = [], []
fig, axes = plt.subplots(6, 1, figsize=(12, 15), constrained_layout=True)
for p in plan['shorts']:
    video = EP/'outputs/jun-quality-v2/shorts'/(p['name']+'.mp4')
    expected = {'promo':'215968608a3a6d5159f35195e65378de4d6b9f8ed63f19e5d00bc97059997953',
                'summary':'cd72bb6c827b6695c2f24d6ed2474f7c6901943114443fe639c33168bcc703c9'}[p['id']]
    digest = sha(video)
    assert digest == expected
    probe = json.loads(subprocess.check_output([str(PROBE), '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(video)]))
    sr, assembled = readwav(EDITOR/(p['name']+'_audio.wav'))
    encoded = np.frombuffer(subprocess.check_output([str(FF), '-v', 'error', '-i', str(video), '-vn', '-ac', '1', '-ar', str(sr), '-c:a', 'pcm_f32le', '-f', 'f32le', 'pipe:1']), dtype='<f4')
    save(HERE/(p['id']+'_ffprobe.json'), probe)
    for r in p['ranges']:
        src = Path(r['path'])
        if src not in pcm:
            rate, samples = readwav(src)
            pcm[src] = rate, samples
            fingerprints.append(dict(path=str(src), sha256=sha(src), bytes=src.stat().st_size))
        rate, samples = pcm[src]
        assert sha(src) == r['sha256'] and rate == sr
        x = samples.astype(float)/32768
        cut, start = r['source_out_s'], r['source_in_s']
        q = quiet[(p['id'],r['scene_id'])]
        candidate = latest_cuts[(p['id'],r['scene_id'])]
        t = np.arange(round((cut-.65)*rate), round((cut+.25)*rate), round(.005*rate), dtype=int)
        energy = np.array([level(x[i:i+round(.005*rate)]) for i in t])
        spans=[]; first=None
        for i, db in enumerate(np.append(energy, 0)):
            current=t[i]/rate if i<len(t) else t[-1]/rate+.005
            if db < -55:
                if first is None: first=current
            elif first is not None:
                if current-first >= .1: spans.append([round(first,6), round(current,6)])
                first=None
        span=next(s for s in spans if s[0] < candidate < s[1])
        first, last = round(start*rate), round(cut*rate)
        at=round(r['output_start_s']*rate)
        edge=round(.003*rate)
        preserved=np.array_equal(samples[first+edge:last-edge],assembled[at+edge:at+last-first-edge])
        slot_end=r['output_start_s']+r['output_duration_s']
        sample_end=r['output_start_s']+(last-first)/rate
        ax=axes[len(rows)]
        ax.plot(t/rate, energy, color='#286cda', lw=1)
        ax.axvspan(*span, color='#267b69', alpha=.13)
        ax.axvline(cut, color='#a63232', label='v4 source cut')
        ax.axvline(candidate, color='#267b69', linestyle='--', label='proposed quiet boundary (S13: diagnostic only)')
        ax.axhline(-55, color='gray', linestyle=':', lw=.7)
        ax.set(title=f"{p['id']} {r['scene_id']} | original PCM | source seconds", ylabel='5 ms RMS dBFS', ylim=(-100,0))
        ax.legend(loc='lower left', fontsize=8)
        near=x[round((cut-.05)*rate):round(cut*rate)]
        ca=x[round((candidate-.01)*rate):round((candidate+.01)*rate)]
        row=dict(short_id=p['id'], scene_id=r['scene_id'], source_path=str(src), source_sha256=r['sha256'], sample_rate=rate,
                 source_in_s=start, old_source_out_s=cut, output_start_s=r['output_start_s'], output_slot_end_s=slot_end,
                 output_pcm_cut_s=sample_end, frame_rounding_pad_s=slot_end-sample_end,
                 independent_5ms_quiet_span_dbfs_lt_minus55=span, parent_quiet_span_s=q['quiet_intervals'],
                 proposed_source_out_s=candidate, candidate_20ms_rms_dbfs=level(ca), candidate_20ms_peak_dbfs=round(float(20*np.log10(max(1e-10,np.abs(ca).max()))),3),
                 before_cut_50ms_rms_dbfs=level(near), onset_activity_retained_until_cut_ms=round(1000*(cut-span[1]),3),
                 assembled_matches_source_except_3ms_edges=bool(preserved),
                 encoded_last50ms_before_pcm_cut_rms_dbfs=level(encoded[round((sample_end-.05)*rate):round(sample_end*rate)]),
                 inherited_local_medium_asr=asr[p['id']+'_source_'+r['scene_id']],
                 actual_listening=False, continuous_playback=False)
        rows.append(row)
    tail=encoded[round((p['speech_cut_end_s']+.1)*sr):round((p['duration_s']-.1)*sr)]
    # Decode only the last 0.5 s to a small grayscale array for EOF fade evidence.
    frames=np.frombuffer(subprocess.check_output([str(FF), '-v', 'error', '-sseof', '-0.5', '-i', str(video), '-an', '-vf', 'scale=180:320', '-pix_fmt', 'gray', '-f', 'rawvideo', 'pipe:1']),dtype=np.uint8).reshape(-1,320,180)
    media.append(dict(short_id=p['id'], path=str(video), sha256=digest, duration_s=p['duration_s'], frames=p['frames'],
                      speech_slot_end_s=p['speech_cut_end_s'], cta_hold_s=p['tail'], source_wav_sha256=sha(EDITOR/(p['name']+'_audio.wav')),
                      encoded_tail_rms_dbfs=level(tail), eof_sampled_frame_count=len(frames), eof_frame_mean_gray=[round(float(f.mean()),4) for f in frames],
                      eof_first_last_mean_absolute_pixel_difference=round(float(np.abs(frames[0].astype(float)-frames[-1]).mean()),4),
                      inherited_encoded_asr=asr[p['id']+'_encoded_end']))
    # Exact final frame plus both sides of the CTA entry; source remains untouched.
    for label, frame in [('before_cta',round(p['speech_cut_end_s']*30)-1),('at_cta',round(p['speech_cut_end_s']*30)),('last_frame',p['frames']-1)]:
        subprocess.run([str(FF), '-v', 'error', '-n', '-ss', f'{frame/30:.9f}', '-i', str(video), '-frames:v', '1', str(HERE/(p['id']+'_'+label+'.png'))],check=True)
    fingerprints.append(dict(path=str(video),sha256=digest,bytes=video.stat().st_size))
fig.savefig(HERE/'pcm_boundary_energy.png', dpi=150)
plt.close(fig)
save(HERE/'measurements.json',dict(created_at_utc=datetime.now(timezone.utc).isoformat(), method='44.1 kHz original 16-bit mono PCM; independent 5 ms RMS bins; 20 ms candidate windows; AAC decoded separately',
                                inherited_asr='Parent local faster-whisper medium int8; not rerun by QA; timestamps are not phoneme endpoints',
                                boundaries=rows, media=media, actual_listening=False, continuous_playback=False))
save(HERE/'input_fingerprints.json',fingerprints)
print(json.dumps(dict(status='measured',boundaries=len(rows),media=[{k:m[k] for k in ['short_id','sha256','duration_s','encoded_tail_rms_dbfs','eof_first_last_mean_absolute_pixel_difference']} for m in media],
                      candidates=[{k:r[k] for k in ['short_id','scene_id','proposed_source_out_s','candidate_20ms_rms_dbfs','before_cut_50ms_rms_dbfs','assembled_matches_source_except_3ms_edges']} for r in rows]),ensure_ascii=False))
