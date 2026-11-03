"""Public reference download, no cookies, no cloud video/ASR upload."""
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
EP=Path(__file__).resolve().parents[1]
import yt_dlp

IDS=['UguOzeTENco','rMKZ1AYdS78','Kmfn_lWwfUQ','xrPYY7tQvG8']
FF=ROOT/'video-agent-studio/episodes/housing-choice-networth-20261020/outputs/private-production-v1/media-bin/ffmpeg.exe'


def main():
    out=EP/'research/references';out.mkdir(parents=True,exist_ok=True)
    results=[]
    for vid in IDS:
        folder=out/vid;folder.mkdir(exist_ok=True)
        try:
            opts={'format':'bestvideo[height<=1280]+bestaudio/best[height<=1280]/best', 'outtmpl':str(folder/'source.%(ext)s'), 'merge_output_format':'mp4', 'ffmpeg_location':str(FF.parent), 'quiet':True,'no_warnings':True,'noplaylist':True,'retries':0,'fragment_retries':0,'socket_timeout':30,'cachedir':False}
            with yt_dlp.YoutubeDL(opts) as dl:
                info=dl.extract_info('https://www.youtube.com/shorts/'+vid,download=True)
            selected={k:info.get(k) for k in ['id','title','description','uploader','channel','channel_id','upload_date','duration','view_count','like_count','width','height','webpage_url']}
            selected['manual_caption_languages']=list(info.get('subtitles',{}))
            selected['automatic_caption_languages']=list(info.get('automatic_captions',{}))
            selected['downloaded_media']=[str(p.relative_to(EP)) for p in folder.glob('source.*') if p.suffix in ['.mp4','.webm','.mkv']]
            selected['status']='downloaded';(folder/'metadata.json').write_text(json.dumps(selected,ensure_ascii=False,indent=2),encoding='utf-8')
            results.append(selected)
            print(json.dumps({'id':vid,'title':selected['title'],'duration':selected['duration'],'status':'downloaded'},ensure_ascii=False),flush=True)
        except Exception as e:
            results.append({'id':vid,'status':'failed','error_type':type(e).__name__})
            print(json.dumps(results[-1]),flush=True)
    (out/'manifest.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')


if __name__=='__main__':main()
