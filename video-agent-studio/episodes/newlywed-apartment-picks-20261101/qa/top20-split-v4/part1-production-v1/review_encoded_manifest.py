"""실제 MP4/프레임 packet 수신 후 실행할 QA 준비기. 렌더 조회·대기 기능 없음.

예: tools/python311/python.exe -Xutf8 .../review_encoded_manifest.py
    --manifest MANIFEST --video MP4 --sha256 ACTUAL_SHA

manifest는 배열 또는 {"frames": [...]} 형식. 기본 행 키는 file/seconds.
다른 스키마이면 --path-key/--time-key/--scene-key/--phase-key로 명시한다.
이 스크립트는 눈으로 프레임을 보거나 실제 음성을 듣지 않는다.
"""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
from html import escape
import argparse,hashlib,json,subprocess

Q=Path(__file__).resolve().parent
E=Q.parents[2];ROOT=E.parents[2]
D=E/'director/top20-split-v4/part1-production-v1'

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def save(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--manifest',type=Path,required=True)
    ap.add_argument('--video',type=Path,required=True)
    ap.add_argument('--sha256',required=True)
    ap.add_argument('--path-key',default='file')
    ap.add_argument('--time-key',default='seconds')
    ap.add_argument('--scene-key',default='scene_id')
    ap.add_argument('--phase-key',default='phase')
    ap.add_argument('--frame-root',type=Path,help='명시하지 않으면 manifest 부모 폴더 기준')
    ap.add_argument('--out-name',default='encoded_packet_v4',help='QA 폴더에 새로 만들 하위 폴더 이름')
    ap.add_argument('--full-decode',action='store_true',help='총괄의 현재SHA decode 증거를 재사용할 수 없을 때만 실행')
    a=ap.parse_args()
    if Path(a.out_name).name!=a.out_name or a.out_name in ['.','..']:
        ap.error('--out-name은 단일 새 폴더 이름이어야 합니다')
    out=Q/a.out_name
    if out.exists():ap.error('기존 QA 산출물 보존: 다른 --out-name 사용')
    video=a.video.resolve(strict=True);manifest=a.manifest.resolve(strict=True)
    actual_sha=sha(video)
    if actual_sha.lower()!=a.sha256.lower():raise ValueError('실제 MP4 SHA가 packet SHA와 다릅니다')
    raw=read(manifest);rows=raw if isinstance(raw,list) else raw['frames']
    if not isinstance(rows,list) or not rows:raise ValueError('manifest frames 배열이 비어 있습니다')
    for label,value in [('video_sha256',raw.get('video_sha256') if isinstance(raw,dict) else None),('mp4_sha256',raw.get('mp4_sha256') if isinstance(raw,dict) else None)]:
        if value and value.lower()!=actual_sha.lower():raise ValueError(label+' 불일치')
    probe=ROOT/'video/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe'
    cmd=[str(probe),'-v','error','-show_streams','-show_format','-of','json',str(video)]
    pr=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace')
    if pr.returncode:raise RuntimeError(pr.stderr)
    metadata=json.loads(pr.stdout)
    vs=[s for s in metadata['streams'] if s.get('codec_type')=='video']
    aud=[s for s in metadata['streams'] if s.get('codec_type')=='audio']
    if len(vs)!=1:raise ValueError('예상과 다른 영상 스트림 수')
    stream=vs[0];num,den=map(int,stream['avg_frame_rate'].split('/'));fps=num/den
    duration=float(metadata['format']['duration']);lock=read(D/'locked_timing.json')
    scenes=lock['scenes'];scene_ids=[s['scene_id'] for s in scenes]
    base=(a.frame_root or manifest.parent).resolve()
    from PIL import Image
    evidence=[];problems=[]
    for i,r in enumerate(rows):
        p=Path(r[a.path_key]);p=p.resolve(strict=True) if p.is_absolute() else (base/p).resolve(strict=True)
        sec=float(r[a.time_key])
        if not 0<=sec<=duration:raise ValueError('표본 시간 범위 오류: '+str(sec))
        with Image.open(p) as im:
            im.load();dims=list(im.size);fmt=im.format
        phash=sha(p)
        declared_hash=r.get('sha256')
        if declared_hash and phash!=declared_hash:raise ValueError('프레임 SHA 불일치: '+str(p))
        inferred=next((s['scene_id'] for s in scenes if s['start_s']<=sec<s['end_s']),None)
        sid=r.get(a.scene_key) or inferred
        phase=r.get(a.phase_key)
        if dims!=[stream['width'],stream['height']]:
            problems.append(dict(index=i,problem='full_resolution_frame_dimensions_differ',dimensions=dims))
        evidence.append(dict(index=i,path=str(p),seconds=sec,scene_id=sid,inferred_scene_id=inferred,phase=phase,sha256=phash,bytes=p.stat().st_size,dimensions=dims,image_format=fmt,visually_viewed=False,pixel_findings='unchecked',parent_row=r))
    times=[f['seconds'] for f in evidence]
    tolerance=1.1/fps
    cuts=[dict(time_s=s['start_s'],before=any(0<s['start_s']-t<=tolerance for t in times),after=any(0<=t-s['start_s']<=tolerance for t in times)) for s in scenes[1:]]
    phases=[]
    for s in scenes:
        grouped={}
        for sen in s['sentences']:grouped.setdefault(sen.get('map_phase','unspecified'),[]).append(sen)
        for phase,items in grouped.items():
            sampled=[f['index'] for f in evidence if any(v['start_s']<=f['seconds']<=v['end_s'] for v in items)]
            phases.append(dict(scene_id=s['scene_id'],phase=phase,sampled_frame_indices=sampled))
    longcaps=sorted(enumerate(lock['captions']),key=lambda c:len(c[1]['text']),reverse=True)[:8]
    longcoverage=[dict(cue_index=i,text=c['text'],sampled_frame_indices=[f['index'] for f in evidence if c['start_s']<=f['seconds']<c['end_s']]) for i,c in longcaps]
    brand=[dict(kind=b['kind'],sampled_frame_indices=[f['index'] for f in evidence if b['start_s']<=f['seconds']<b['start_s']+b['duration_s']]) for b in lock['brand_inserts']]
    scripted_cards=[dict(sentence_id=v['sentence_id'],sampled_frame_indices=[f['index'] for f in evidence if v['start_s']<=f['seconds']<=v['end_s']]) for s in scenes if s['scene_id'] in ['P01-INTRO','P01-OUTRO'] for v in s['sentences']]
    hold_start=lock['last_spoken_end_s'];hold_end=next(b['start_s'] for b in lock['brand_inserts'] if b['kind']=='outro')
    technical=dict(video_sha256=actual_sha,bytes=video.stat().st_size,codec=stream.get('codec_name'),pixel_format=stream.get('pix_fmt'),dimensions=[stream['width'],stream['height']],fps=fps,duration_s=duration,locked_audio_duration_s=lock['total_s'],duration_delta_s=duration-lock['total_s'],audio_stream_count=len(aud),last_frame_sampled=any(0<=duration-t<=tolerance for t in times))
    if abs(duration-lock['total_s'])>1/fps+0.05:problems.append(dict(problem='MP4_duration_differs_from_lock',delta_s=duration-lock['total_s']))
    if [stream['width'],stream['height']]!=[1920,1080] or fps!=30 or not aud:problems.append(dict(problem='unexpected_delivery_stream_spec'))
    out.mkdir()
    save(out/'ffprobe.json',metadata)
    decode={'status':'unchecked_or_reuse_parent_current_SHA_decode_receipt','actual_listening':False}
    if a.full_decode:
        ffmpeg=ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'
        with (out/'full_decode.stderr.txt').open('w',encoding='utf-8') as log:
            dc=subprocess.run([str(ffmpeg),'-v','error','-xerror','-i',str(video),'-f','null','-'],stdout=subprocess.DEVNULL,stderr=log)
        decode={'status':'checked' if dc.returncode==0 else 'failed','exit_code':dc.returncode,'actual_listening':False}
        if dc.returncode:problems.append(dict(problem='actual_MP4_full_decode_failed'))
    packet=dict(status='packet_indexed_pending_visual_review',generated_at=datetime.now(timezone.utc).isoformat(),manifest_path=str(manifest),manifest_sha256=sha(manifest),video_path=str(video),technical=technical,frames=evidence,coverage=dict(frame_count=len(evidence),unique_frame_files=len({f['path'] for f in evidence}),by_scene=dict(Counter(f['scene_id'] for f in evidence)),scene_ids_without_samples=[sid for sid in scene_ids if sid not in {f['scene_id'] for f in evidence}],phases=phases,cuts=cuts,intro_outro_sentences=scripted_cards,longest8captions=longcoverage,brand=brand,last_silent_hold_frame_indices=[f['index'] for f in evidence if hold_start<=f['seconds']<hold_end]),decode=decode,technical_problems=problems,provenance_scope='parent-provided extraction manifest tied to independently hashed actual MP4; original frame extraction not independently repeated',actual_listening=False,continuous_playback=False,visually_viewed_frame_count=0,reviewer_decision='pending; this script does not approve quality')
    save(out/'packet_checks.json',packet)
    rows_html=[]
    for f in evidence:
        rel=Path(f['path']).as_uri()
        rows_html.append('<figure><img src="'+escape(rel,quote=True)+'"><figcaption>'+escape(str(f['index'])+' · '+format(f['seconds'],'.3f')+'s · '+str(f['scene_id'])+' · '+str(f['phase']))+'</figcaption></figure>')
    (out/'frame_index.html').write_text('<!doctype html><meta charset="utf-8"><title>실제 MP4 표본 프레임 QA 색인</title><style>body{font:18px sans-serif;background:#eee}main{display:grid;grid-template-columns:repeat(2,1fr);gap:16px}figure{margin:0}img{width:100%;height:auto}figcaption{padding:8px}</style><p>자동 생성 색인. 시각 검수·청취 완료를 뜻하지 않습니다.</p><main>'+''.join(rows_html)+'</main>',encoding='utf-8')
    print(json.dumps(dict(status=packet['status'],output=str(out/'packet_checks.json'),frame_count=len(evidence),technical_problem_count=len(problems),first_problems=problems[:5],visually_viewed=0,actual_listening=False,continuous_playback=False),ensure_ascii=False))

if __name__=='__main__':main()
