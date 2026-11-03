"""Freeze approved local brand/music and three prior-channel reference frames."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[1]
EP=ROOT/'video-agent-studio/episodes/regional-price-recovery-20261022'
OUT=EP/'outputs/production-v1-jun/reusable_assets'
OUT.mkdir(parents=True,exist_ok=True)
FFBIN=Path('C:/Users/e2ken/AppData/Local/Microsoft/WinGet/Packages/yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-N-124716-g054dffd133-win64-gpl/bin')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text(encoding='utf8'))
assets=[]
brand=read(ROOT/'video-agent-studio/episodes/goyang-changneung-20261015/outputs/production-v7-preview/reusable_brand_assets.json')
for item in brand['preferred_reuse_assets']:
    source=Path(item['path']);assert sha(source)==item['sha256']
    dest=OUT/source.name
    if not dest.exists(): shutil.copy2(source,dest)
    assert sha(dest)==item['sha256']
    probe=json.loads(subprocess.check_output([str(FFBIN/'ffprobe.exe'),'-v','error','-show_format','-show_streams','-of','json',str(dest)],text=True,encoding='utf8'))
    duration=float(probe['format']['duration'])
    expected=5 if 'intro' in item['asset_id'] else 10
    assert abs(duration-expected)<0.1
    assets.append(dict(item,actual_file=dest.relative_to(ROOT).as_posix(),actual_duration=duration,source_type='reused_existing_AI_concept_brand_city_footage_not_regional_evidence'))
source=ROOT/'assets/music/thinking_music.mp3';dest=OUT/source.name
if not dest.exists(): shutil.copy2(source,dest)
assert sha(source)==sha(dest)
license=read(ROOT/'assets/music/thinking_music.license.json')
(OUT/'thinking_music.license.json').write_text(json.dumps(license,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
assets.append({'asset_id':'existing_channel_bgm','actual_file':dest.relative_to(ROOT).as_posix(),'source':source.relative_to(ROOT).as_posix(),'sha256':sha(dest),'license':license,'new_purchase':False})
for name,meaning in [('집','실제 거래 구성'),('달력','고점부터 기다린 시간'),('돋보기','비교 조건 확인')]:
    source=ROOT/'assets/emoji'/f'{name}.png';dest=OUT/source.name
    if not dest.exists(): shutil.copy2(source,dest)
    assert sha(source)==sha(dest)
    assets.append({'asset_id':'existing_emoji_'+name,'actual_file':dest.relative_to(ROOT).as_posix(),
                   'source':source.relative_to(ROOT).as_posix(),'sha256':sha(dest),
                   'license':'Microsoft Fluent Emoji / MIT; bundled LICENSE.md','meaning':meaning,'not_regional_evidence':True})
shutil.copy2(ROOT/'assets/emoji/LICENSE.md',OUT/'emoji_LICENSE.md')
baseline=read(ROOT/'config/current_video.json');source=ROOT/baseline['video']
assert sha(source)==baseline['sha256']
refs=[]
for sec in [45,430,850]:
    target=OUT/f'baseline_gyosan_{sec}s.png'
    if not target.exists():
        subprocess.run([str(FFBIN/'ffmpeg.exe'),'-v','error','-ss',str(sec),'-i',str(source),'-frames:v','1','-vf','scale=960:-1',str(target)],check=True)
    refs.append({'source':baseline['video'],'time_seconds':sec,'path':target.relative_to(ROOT).as_posix(),'sha256':sha(target),'visual_review':'pending_static_reference_comparison'})
record={'at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'assets':assets,'reference_frames':refs,'ffmpeg':str(FFBIN/'ffmpeg.exe'),'ffprobe':str(FFBIN/'ffprobe.exe'),'new_paid_calls':0,'actual_listening':False,'continuous_playback':False}
(OUT/'manifest.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'brand_assets':2,'durations_seconds':[a.get('actual_duration') for a in assets[:2]],'bgm':'existing Thinking Music, CC BY4.0 credit required','existing_emoji':3,'baseline_reference_frames':len(refs),'new_paid_calls':0},ensure_ascii=False))
