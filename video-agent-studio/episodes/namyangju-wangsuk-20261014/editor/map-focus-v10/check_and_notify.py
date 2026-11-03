from pathlib import Path
import hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[5]
EP=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from notify import telegram
stage=sys.argv[1]
intervals={'1':(165,273),'2':(273,369),'3':(369,525),'front':(0,525)}
a,b=intervals[stage]
out=EP/'outputs/map-focus-v10'
v=out/f'map-focus_v10_{stage}.mp4'
sha=hashlib.sha256(v.read_bytes()).hexdigest()
bin=Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin')
probe=json.loads(subprocess.check_output([str(bin/'ffprobe.exe'),'-v','error','-show_streams','-show_format','-of','json',str(v)]))
vs=next(s for s in probe['streams'] if s['codec_type']=='video')
assert int(vs['nb_frames'])==(b-a)*30 and vs['width']==1920 and vs['height']==1080
q=subprocess.run([str(bin/'ffmpeg.exe'),'-v','error','-i',str(v),'-f','null','-'],capture_output=True,text=True)
assert q.returncode==0 and not q.stderr.strip(),q.stderr
samples=[0,60,300,(b-a)*30-1]
for n in samples:
 subprocess.run([str(bin/'ffmpeg.exe'),'-v','error','-ss',str(n/30),'-i',str(v),'-frames:v','1','-y',str(out/f'actual_{stage}_{n}.png')],check=True)
record={'file':str(v),'sha256':sha,'bytes':v.stat().st_size,'original_start_s':a,'original_end_s':b,'probe':probe,'whole_decode_passed':True,'actual_listening':False,'continuous_playback':False}
(out/f'technical_{stage}.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
receipt=out/f'telegram_receipt_{stage}.json'
if receipt.exists():
 old=json.loads(receipt.read_text(encoding='utf-8'))
 if old.get('message_sent') and old.get('sha256')==sha:
  print(json.dumps({'duplicate_skipped':True,'stage':stage}));sys.exit(0)
fmt=lambda n:f'{n//60:02}:{n%60:02}'
update='학교 라벨 가림 수정본으로 갱신 · 기존 1·2단계는 동일\n' if stage in ['3','front'] and (EP/'editor/map-focus-v10/label_fix.json').exists() else ''
text=(update+f'남양주 지도 집중 수정 v10 · {"앞부분 통합" if stage=="front" else "부분 검토본 "+stage} 완성\n'
 f'원본 시간 {fmt(a)}~{fmt(b)} / 1080p30\n'
 '우측 설명 패널을 없애 지도를 넓히고, 설명 대상의 강조와 권역 위치 확인→확대를 연결했습니다. 예정역은 계획 위치로 구분합니다.\n'
 f'영상 경로: {v}\n안내: {out / "README.md"}\n'
 '실제 파일 기술 검사·전체 디코드 통과. 독립 시각 검수 결과는 별도 기록하며 실제 청취·연속 재생은 미확인입니다. 파일은 전송하지 않았습니다.')
sent=telegram.send(text,quiet=True)
receipt.write_text(json.dumps({'message_sent':bool(sent),'file_sent':False,'sha256':sha,'stage':stage,'original_interval_s':[a,b]},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'stage':stage,'message_sent':bool(sent),'file_sent':False,'sha256':sha}))
