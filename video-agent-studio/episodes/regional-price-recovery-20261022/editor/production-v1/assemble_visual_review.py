"""BGM-only review assembly. No actual speech, TTS/API, upload or final approval."""
import hashlib,json,subprocess
from pathlib import Path
ED=Path(__file__).resolve().parent;EP=ED.parent.parent;REPO=EP.parents[2];OUT=EP/'outputs/production-v1-jun';P=OUT/'project';C=OUT/'checks/visual-review'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
def probe(ff,p):return json.loads(subprocess.check_output([ff,'-v','error','-show_streams','-show_format','-of','json',str(p)],text=True,encoding='utf-8'))
def resolve(p):
    p=Path(p);return p if p.is_absolute() else REPO/p
def main():
    plan=read(P/'visual_review_plan.json');assert plan['mode']=='visual-review' and plan['provisional'] and not plan['timing_locked'] and plan['voice']==0
    lock=read(P/'timing_resolved.json');assert lock['timing_locked'] is False
    assert sha(P/'index.html')==plan['protected_original_actual_Jun_entry_sha256'],'Actual-Jun entry changed'
    if (C/'render_exit.json').exists():assert read(C/'render_exit.json')['render_exit_code']==0
    m=read(OUT/'reusable_assets/manifest.json');assets={a['asset_id']:a for a in m['assets']};inputs=[];reused=[]
    for name in ['channel_brand_intro_clean_v7','channel_brand_outro_clean_v7','existing_channel_bgm']:
        a=assets[name];p=resolve(a['actual_file']);assert sha(p)==a['sha256'];inputs.append(p);reused.append({'asset_id':name,'path':str(p),'sha256':a['sha256']})
    intro,outro,music=inputs;body=OUT/'previews/full_visual_review_body_v1.mp4';dest=OUT/'previews/full_visual_review_v1.mp4';assert body.is_file() and not dest.exists(),'Body required; preserve existing output'
    ff,fp=m['ffmpeg'],m['ffprobe'];bm=probe(fp,body);bv=next(s for s in bm['streams'] if s['codec_type']=='video');assert not any(s['codec_type']=='audio' for s in bm['streams'])
    assert (bv['width'],bv['height'],bv['avg_frame_rate'])==(1920,1080,'30/1') and abs(float(bv['duration'])-plan['body_duration_including_CTA_hold'])<.035
    dur=plan['body_duration_including_CTA_hold'];fadeout=dur-.75
    filt=(f'[0:v]fps=30,trim=end_frame=150,setpts=PTS-STARTPTS,setsar=1,format=yuv420p[v0];'
          f'[1:v]fps=30,trim=end_frame={plan["body_frames"]},setpts=PTS-STARTPTS,setsar=1,format=yuv420p[v1];'
          '[2:v]fps=30,trim=end_frame=300,setpts=PTS-STARTPTS,setsar=1,format=yuv420p[v2];'
          '[0:a]atrim=end=5,asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo[a0];'
          f'[3:a]atrim=end={dur:.6f},asetpts=PTS-STARTPTS,volume=0.20,afade=t=in:st=0:d=0.35,afade=t=out:st={fadeout:.6f}:d=0.75,aformat=sample_rates=48000:channel_layouts=stereo[a1];'
          '[2:a]atrim=end=10,asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo[a2];'
          '[v0][a0][v1][a1][v2][a2]concat=n=3:v=1:a=1[v][a]')
    cmd=[ff,'-y','-i',str(intro),'-i',str(body),'-i',str(outro),'-stream_loop','-1','-i',str(music),'-filter_complex',filt,'-map','[v]','-map','[a]','-c:v','libx264','-preset','veryfast','-crf','16','-c:a','aac','-b:a','192k','-metadata','title=음성 없는 전체 검토본 / 임시 타이밍','-metadata','comment=provisional=true; timing_locked=false; voice=0; no actual speech timing','-movflags','+faststart',str(dest)]
    credit=assets['existing_channel_bgm']['license'];(OUT/'previews/full_visual_review_v1_music_credit.txt').write_text(credit['credit']+'\n'+credit['license_url']+'\n검토본은 새 음성 생성 없이 기존 브랜드 음악과 Thinking Music만 재사용. 본문 BGM gain0.20,0.35s fade-in/0.75s fade-out.\n',encoding='utf-8')
    manifest={'status':'assembly_running','review_only':True,'final_video_or_upload_approval':False,'mode':'visual-review','provisional':True,'timing_locked':False,'voice':0,'voice_generation_API_calls':0,'narration_present':False,'actual_last_spoken_end':None,'hold_basis':'provisional caption end, not actual speech','body_path':str(body),'body_sha256':sha(body),'body_offset':5,'last_caption_end':plan['last_caption_end'],'outro_start':plan['outro_start'],'caption_CTA_hold_seconds':3,'expected_duration':plan['expected_total_duration'],'reused_assets':reused,'intro_frames':150,'outro_frames':300,'fps':'30/1','resolution':[1920,1080],'caption_SRT':str(OUT/'previews/full_visual_review_v1.srt'),'caption_SRT_sha256':sha(OUT/'previews/full_visual_review_v1.srt'),'music_license':credit,'BGM_only_mix':{'gain':.20,'fade_in':.35,'fade_out':.75,'brand_original_music_retained':True},'command':cmd,'full_decode_and_continuous_review':'director performs after assembly; not claimed here'}
    path=OUT/'previews/full_visual_review_v1_manifest.json';dump(path,manifest)
    with (C/'assemble_ffmpeg.log').open('w',encoding='utf-8') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
    assert r.returncode==0,'Assembly failed; see assemble_ffmpeg.log'
    final=probe(fp,dest);v=next(s for s in final['streams'] if s['codec_type']=='video');assert (v['width'],v['height'],v['avg_frame_rate'])==(1920,1080,'30/1');assert abs(float(v['duration'])-plan['expected_total_duration'])<.035
    manifest.update(status='assembled_pending_director_technical_and_QA',video_path=str(dest),sha256=sha(dest),duration=float(final['format']['duration']),video_duration=float(v['duration']),audio_streams=sum(s['codec_type']=='audio' for s in final['streams']),ffprobe=final)
    dump(path,manifest);dump(C/'assembly_receipt.json',manifest);print(json.dumps({k:manifest[k] for k in ['status','video_path','sha256','duration','body_offset','last_caption_end','outro_start','provisional','voice']},ensure_ascii=False))
if __name__=='__main__':main()
