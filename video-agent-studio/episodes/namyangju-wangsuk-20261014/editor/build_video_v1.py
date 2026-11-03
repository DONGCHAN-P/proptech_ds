"""Local, reproducible edit. --prepare is safe before timing lock; --render requires lock."""
import argparse, base64, hashlib, html, json, math, pathlib, re, subprocess
ROOT=pathlib.Path(__file__).resolve().parent.parent
ED=ROOT/'editor'; REPO=ROOT.parents[2]
FF=pathlib.Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin/ffmpeg.exe')
PROBE=FF.with_name('ffprobe.exe')
CHROME=REPO/'video/node_modules/.remotion/chrome-headless-shell/win64/chrome-headless-shell-win64/chrome-headless-shell.exe'
FPS=30
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def save(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def run(args): subprocess.run([str(x) for x in args],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
def read_probe(p): return json.loads(subprocess.check_output([str(PROBE),'-v','error','-show_streams','-show_format','-of','json',str(p)],text=True,encoding='utf-8'))
FONT=base64.b64encode((REPO/'video/public/fonts/Pretendard-Regular.woff2').read_bytes()).decode()
def raster(name,body):
    hp=ED/'render_v1'/f'{name}.html'; png=hp.with_suffix('.png')
    hp.write_text('<!doctype html><meta charset="utf-8"><style>@font-face{font-family:EditFont;src:url(data:font/woff2;base64,'+FONT+')}*{box-sizing:border-box}body{margin:0;background:#F6F4EF;color:#111;font-family:EditFont}h1{position:absolute;left:100px;top:56px;margin:0;font-size:52px}svg{position:absolute;left:100px;top:30px;width:1720px;height:820px}.rows{position:absolute;left:100px;top:190px;width:1720px}.row{background:white;border-radius:16px;padding:24px 35px;margin:20px 0;font-size:38px;line-height:1.4}.note{position:absolute;left:100px;top:830px;font-size:25px;color:#6E6E6E}.top{position:absolute;right:100px;top:18px;font-size:20px;color:#6E6E6E}</style>'+body,encoding='utf-8')
    run([CHROME,'--headless','--no-sandbox','--disable-gpu','--hide-scrollbars','--allow-file-access-from-files','--window-size=1920,1080','--virtual-time-budget=1500',f'--screenshot={png}',hp.as_uri()]);return png
def card(scene,title,rows,note):return raster(scene,'<h1>'+html.escape(title)+'</h1><div class="rows">'+''.join('<div class="row">'+html.escape(x)+'</div>'for x in rows)+'</div><div class="note">'+html.escape(note)+'</div>')
def ass_time(s):
    c=round(s*100);return f'{c//360000}:{c//6000%60:02}:{c//100%60:02}.{c%100:02}'
def chunks(text):
    words=text.split();out=[];current=''
    for word in words:
        if len(current)+len(word)+1>42 and current:out.append(current);current=''
        current=(current+' '+word).strip()
    if current:out.append(current)
    return out
def subtitle(scene,dur,path):
    texts=chunks(scene['narration_text']); weights=[len(re.sub(r'\s','',x)) for x in texts];total=sum(weights);cursor=0
    header='[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\nWrapStyle: 2\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,Malgun Gothic,42,&H00111111,&H00111111,&H00FFFFFF,&H00FFFFFF,0,0,0,0,100,100,0,0,3,16,0,2,110,110,50,1\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n'
    events=[];proposal=[]
    for text,w in zip(texts,weights):
        start=cursor;cursor+=dur*w/total
        events.append(f'Dialogue: 0,{ass_time(start)},{ass_time(cursor)},Default,,0,0,0,,{text}')
        proposal.append({'start_s':start,'end_s':cursor,'text':text,'basis':'character_weight_estimate_within_measured_scene_audio_NOT_forced_alignment'})
    path.write_text(header+'\n'.join(events)+'\n',encoding='utf-8-sig');return proposal
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--prepare',action='store_true');ap.add_argument('--render',action='store_true');a=ap.parse_args()
    out=ED/'render_v1';out.mkdir(exist_ok=True)
    scenes=read(ROOT/'scenes.json')['scenes'];av=ROOT/'visual/assets_v3.json';av=av if av.exists()else ROOT/'visual/assets_v2.json';assets=read(av)['assets']; backgrounds={}
    for s in scenes:
        sid=s['scene_id']; candidates=[x for x in assets if sid in x['scene_ids'] and x['actual_file'].endswith('.svg')]
        if sid=='S008':candidates=[x for x in candidates if 'S008' in x['actual_file']]
        if candidates:
            svg=(ROOT/candidates[0]['actual_file']).read_text(encoding='utf-8').replace('Noto Sans KR, Malgun Gothic, sans-serif','EditFont, Malgun Gothic, sans-serif');backgrounds[sid]=[raster(sid,svg)]
    backgrounds['S002']=[card('S002','남양주는 하나의 생활권이 아닙니다',['별내·다산 / 진접·오남 / 호평·평내 / 화도','별내역: 8호선과 경춘선 · 별내별가람역: 4호선','내 집·직장·학교를 잇는 실제 동선부터 확인'], '출처: 철도 운영기관·남양주시 | 생활권의 단일 경계를 확정하지 않음')]
    if 'S005' not in backgrounds:backgrounds['S005']=[card('S005','기업 이름 다음에 진행 단계를 봅니다',['기존 기반: 진관·금곡·광릉테크노밸리 조성 완료','왕숙 도시첨단산단: 개발실시계획 승인·고시','기업 입주 예정 / 건축허가 / 준공 목표 / 실제 운영을 구분'], '출처: 남양주시 2026년 발표·산업단지 현황 | 실제 고용·운영 확인과 구분')]
    regional=ROOT/'visual/outputs/S002_namyangju_regional_osm_v3.png'
    if regional.exists():
        im=base64.b64encode(regional.read_bytes()).decode()
        backgrounds['S002'].insert(0,raster('S002_map',f'<img src="data:image/png;base64,{im}" style="position:absolute;left:100px;top:30px;width:1720px;height:820px;object-fit:contain"><div class="note">© OpenStreetMap contributors · openstreetmap.org/copyright · 지형 설명용</div>'))
    for district in (1,2):
        asset=next(x for x in assets if x['asset_id']==f'S003_wangsuk{district}_official_plan');jpg=base64.b64encode((ROOT/asset['actual_file']).read_bytes()).decode()
        png=raster(f'S003_map{district}',f'<h1>왕숙{district if district==2 else "1"} · 남양주시 제공 계획도</h1><img src="data:image/jpeg;base64,{jpg}" style="position:absolute;left:550px;top:155px;width:820px;height:630px;object-fit:contain"><div class="note">출처: 남양주시 key3039 · 공공누리 제3유형 · 원본 전체 표시<br>페이지 최종수정 2026.3.4 · 최신 변경차수 전수대조 미완료</div>')
        backgrounds['S003'].append(png)
    save(out/'backgrounds.json',{k:[str(x.relative_to(ROOT)) for x in v]for k,v in backgrounds.items()})
    if not a.render:print('prepared');return
    lock=ED/'timing_locked_v1.json'
    if not lock.exists()or not read(lock).get('timing_locked'):raise RuntimeError('director timing lock required')
    lockdata=read(lock);timing=[];parts=[];subtitles={};elapsed=0;inputs=[]
    for s in scenes:
        apath=ROOT/'narration/audio-v1'/f"{s['scene_id']}.mp3"
        meta=read(apath.with_suffix('.json'))
        assert hashlib.sha256(apath.read_bytes()).hexdigest()==meta['sha256'], 'audio hash changed'
        assert hashlib.sha256(s['narration_text'].encode()).hexdigest()==meta['text_sha256'], 'approved text/audio mismatch'
        inputs.append({'scene_id':s['scene_id'],'audio_sha256':meta['sha256'],'text_sha256':meta['text_sha256']})
    save(out/'inputs_verified.json',inputs)
    for scene in scenes:
        sid=scene['scene_id'];audio=ROOT/'narration/audio-v1'/f'{sid}.mp3'
        actual=float(read_probe(audio)['format']['duration']);frames=math.ceil(actual*FPS);dur=frames/FPS
        ass=out/f'{sid}.ass';subtitles[sid]=subtitle(scene,actual,ass)
        cuts=backgrounds[sid]; cutlist=out/f'{sid}_images.txt'; each=dur/len(cuts)
        cutlist.write_text(''.join(f"file '{p.as_posix()}'\nduration {each:.9f}\n"for p in cuts)+f"file '{cuts[-1].as_posix()}'\n",encoding='utf-8')
        clip=out/f'{sid}.mp4';escaped=ass.as_posix().replace(':','\\:')
        cmd=[FF,'-y','-f','concat','-safe','0','-i',cutlist,'-i',audio,'-vf',f"fps=30,subtitles=filename='{escaped}',format=yuv420p",'-af','apad','-t',str(dur),'-c:v','libx264','-preset','veryfast','-crf','20','-threads','4','-c:a','aac','-b:a','192k','-ar','48000','-ac','2',clip]
        save(out/f'{sid}_command.json',[str(x)for x in cmd]);run(cmd);parts.append(clip);timing.append({'scene_id':sid,'start_s':elapsed,'end_s':elapsed+dur,'actual_audio_duration_s':actual,'encoded_frames':frames});elapsed+=dur;print('rendered',sid,flush=True)
    lst=out/'concat.txt';lst.write_text(''.join(f"file '{p.as_posix()}'\n"for p in parts),encoding='utf-8');final=out/'namyangju-wangsuk_v1.mp4'
    run([FF,'-y','-f','concat','-safe','0','-i',lst,'-c','copy','-movflags','+faststart',final]);save(out/'technical.json',read_probe(final));save(out/'timing_actual.json',timing);save(out/'caption_estimates.json',subtitles)
    run([FF,'-v','error','-i',final,'-f','null','-']);save(out/'decode_check.json',{'passed':True,'audio_listened':False,'continuous_playback':False})
    print('complete',str(final),flush=True)
if __name__=='__main__':main()
