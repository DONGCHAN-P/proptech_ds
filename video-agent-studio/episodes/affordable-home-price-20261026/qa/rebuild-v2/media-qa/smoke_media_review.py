"""로컬 합성 AV/DOM 도구 실증. 실제 본편·실제음성·미디어 승인 증거가 아니다."""
import json
import pathlib
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import media_review as qa


def main():
    base = qa.new_run(qa.HERE / sys.argv[1])
    def pin(path):
        return {'path': str(path.resolve()), 'sha256': qa.sha(path)}
    movie = base / 'synthetic.mp4'
    qa.command([qa.FFMPEG, '-n', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=ivory:s=1920x1080:r=30:d=3', '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo', '-shortest', '-c:v', 'libx264', '-preset', 'ultrafast', '-pix_fmt', 'yuv420p', '-c:a', 'aac', movie], base/'encode.stdout', base/'encode.log')
    ids = ['R001', 'R002', 'R003']
    script = base/'script.json'
    qa.dump(script, {'scenes': [{'id': sid, 'narration': '합성 도구 실증'} for sid in ids]})
    lock = base/'lock.json'
    qa.dump(lock, {'approved': True, 'script_sha256': qa.sha(script), 'tool_smoke_only': True})
    srt = base/'synthetic.srt'
    srt.write_text('1\n00:00:00,000 --> 00:00:00,100\n짧은 큐\n\n2\n00:00:00,100 --> 00:00:00,900\n둘째 큐\n', encoding='utf8')
    projects, files = [], []
    for sid in ids:
        html, model = base/(sid+'.html'), base/(sid+'.json')
        html.write_text('''<!doctype html><meta charset="utf-8"><style>body{margin:0}#graphic{position:absolute;inset:0}#amount,#result{position:absolute;left:100px;font:32px Arial}#amount{top:300px}#result{top:400px}#bar{position:absolute;left:100px;top:650px;width:500px;height:40px;background:blue}</style><div id="graphic"><div id="amount" data-object="text">250000000</div><div id="result" data-object="text">1700000</div><div id="bar" data-object="shape"></div></div><script>window.__sourceSeek=t=>{document.getElementById('amount').style.opacity=t>=.2?1:0;document.getElementById('result').style.opacity=t>=.5?1:0};__sourceSeek(0)</script>''', encoding='utf8')
        qa.dump(model, {'scene_id': sid, 'duration_s': 1, 'template_only': False, 'tool_smoke_only': True, 'beats': [{'start_s': .2, 'end_s': .3, 'reveal': ['amount']}, {'start_s': .5, 'end_s': .6, 'reveal': ['result']}]})
        row = {'scene_id': sid, 'html': pin(html), 'model': pin(model), 'allowed_text_shapes': []}
        projects.append(row)
        files.extend([pin(html), pin(model)])
    edl = base/'edl.json'
    scenes = [{'scene_id': sid, 'start_frame': i*30, 'end_frame': (i+1)*30} for i, sid in enumerate(ids)]
    qa.dump(edl, {'clock': 'global_frames', 'fps': 30, 'total_frames': 90, 'scenes': scenes, 'segments': [{'id':sid,'start_frame':i*30,'end_frame':(i+1)*30} for i,sid in enumerate(ids)], 'progressions': [{'kind': kind, 'scene_id': sid, 'beat_frames': [i*30+6,i*30+15], 'timing_basis':'native_word_boundary'} for i,(sid,kind) in enumerate(zip(ids,['funding_waterfall','ltv_dsr','monthly_budget']))], 'zoom': {'mode':'fixed','max_frames':[]}})
    manifest = base/'manifest.json'
    qa.dump(manifest, {'script_sha256': qa.sha(script), 'files': files, 'tool_smoke_only': True})
    render = base/'render.json'
    qa.dump(render, {'mp4': pin(movie), 'tool_smoke_only': True})
    packet = base/'packet.json'
    qa.dump(packet, {'evidence_kind':'tool_smoke','scope':'representatives','script_lock':pin(lock),'script':pin(script),'mp4':pin(movie),'srt':pin(srt),'edl':pin(edl),'render_receipt':pin(render),'source_manifest':pin(manifest),'source_projects':projects})
    receipt = qa.collect(packet, base/'collected')
    assert receipt['full_AV_decode'] == 'pass'
    assert receipt['geometry_status'] == 'pass'
    assert receipt['caption_midpoints'] == 2
    assert receipt['manual_frames_viewed'] == 0
    assert receipt['final_independent_media_approval'] == 'unchecked'
    rows = qa.read(base/'collected/frame_index.json')
    tags = {tag for row in rows for tag in row['reasons']}
    assert {'caption:1:mid','caption:2:mid','scene:R003:final','cut:30:before','cut:30:after'} <= tags
    bad_html = base/'collision.html'
    bad_html.write_text((base/'R001.html').read_text(encoding='utf8').replace('top:650px','top:300px'), encoding='utf8')
    geometry_input = base/'collision_input.json'
    qa.dump(geometry_input, {'projects': [{**projects[0], 'html':pin(bad_html),'times_s':[.6]}]})
    qa.command(['node',qa.HERE/'geometry_review.cjs',geometry_input,base/'collision_receipt.json'],base/'collision.stdout',base/'collision.log')
    collisions = qa.read(base/'collision_receipt.json')
    assert any(f['type']=='text_shape_collision' for f in collisions['findings'])
    qa.dump(base/'verification.json', {'status':'pass','scope':'tool_smoke_only','decoded_video_frames':90,'caption_midpoints':2,'extracted_frames':len(rows),'actual_character_range_collision_detected':True,'final_independent_media_approval':'unchecked','actual_listening':False,'continuous_playback':False})
    print(json.dumps(qa.read(base/'verification.json'),ensure_ascii=False))


if __name__ == '__main__':
    main()
