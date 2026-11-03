"""Decode verified chapter renders and extract the approved representative frames locally."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
EP=HERE.parents[1]
ROOT=EP.parents[2]
OUT=EP/'outputs/private-production-v1'
DEST=OUT/'renders/measured-v5'

def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,obj): p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--chapters',default='1,2,3')
    args=parser.parse_args()
    chapters=[int(c) for c in args.chapters.split(',')]
    provision=read(EP/'director/two-episode-production-v1/ffmpeg_receipt.json')
    ffmpeg=ROOT/provision['binary']
    if sha(ffmpeg)!=provision['binary_sha256']: raise ValueError('FFmpeg lock mismatch')
    frames=read(OUT/'preview/final_review_selection.json')['frames']
    evidence=DEST/'encoded-preview'
    evidence.mkdir(exist_ok=True)
    result={'status':'running','chapters':[],'frames':[], 'actual_listening':False,
            'continuous_playback':False,'visual_inspection':'pending','final_assembled':False}
    for number in chapters:
        video=DEST/f'ch{number:02d}.mp4'
        receipt=read(DEST/f'ch{number:02d}.receipt.json')
        if receipt['output_sha256']!=sha(video): raise ValueError('Encoded chapter SHA mismatch')
        if receipt['html_sha256']!=sha(OUT/f'ch{number:02d}/index.html'): raise ValueError('Rendered source has changed')
        argv=[str(ffmpeg),'-v','error','-nostdin','-threads','2','-i',str(video),'-map','0:v:0','-map','0:a:0','-f','null','-']
        checked=subprocess.run(argv,capture_output=True,text=True,encoding='utf8',errors='replace')
        (evidence/f'ch{number:02d}.decode.log').write_text(checked.stderr,encoding='utf8')
        if checked.returncode or checked.stderr.strip(): raise ValueError('Encoded chapter decode errors')
        result['chapters'].append({'chapter':number,'file':str(video),'output_sha256':receipt['output_sha256'],
                                   'html_sha256':receipt['html_sha256'],'decode_returncode':checked.returncode,
                                   'ffprobe_receipt':str(DEST/f'ch{number:02d}.receipt.json')})
        for row in [r for r in frames if r['chapter']==number]:
            index=round(row['time_s']*30)
            target=evidence/f'ch{number:02d}_{row["scene_id"]}_{index:06d}.png'
            argv=[str(ffmpeg),'-v','error','-nostdin','-threads','2','-ss',f'{index/30:.9f}',
                  '-i',str(video),'-frames:v','1','-update','1','-y',str(target)]
            subprocess.run(argv,check=True,capture_output=True)
            result['frames'].append({'chapter':number,'scene_id':row['scene_id'],'requested_time_s':row['time_s'],
                                     'frame_index':index,'sample_time_s':index/30,'file':str(target),'sha256':sha(target),
                                     'source_preview_file':str(OUT/row['file']), 'source_preview_sha256':row['sha256']})
        dump(HERE/'encoded_batch_review.json',result)
        print(f'decoded chapter {number} and extracted representative frames',flush=True)
    result['status']='encoded_batch_decode_pass_representative_visual_review_pending'
    dump(HERE/'encoded_batch_review.json',result)
    print(json.dumps({'status':result['status'],'chapters':chapters,'frames':len(result['frames'])}))

if __name__=='__main__': main()
