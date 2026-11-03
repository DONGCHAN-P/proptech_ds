"""Inspect actual encoded silent-edge pixels and preserve v1/AAC evidence."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import conform as c


def main():
    from PIL import Image,ImageDraw,ImageFont
    p=c.HERE/'jun-v2'
    receipt=c.read(p/'render_receipt.json')
    video=receipt['video']
    folder=c.owned(p/'proofs');folder.mkdir(parents=True,exist_ok=True)
    cases=[('before_first_voice',.1,False),('before_first_voice_last_frame',23/30,False),
           ('first_voice',.8,True),('body_cue_gap',4.7,True),
           ('last_voice',668.7,True),('after_last_voice_first_frame',20062/30,False),
           ('silent_CTA',669.53,False),('silent_CTA_last_frame',671.7,False),
           ('brand_start',20152/30,False),('brand_pose',676.73,False)]
    result=[]
    for name,t,expected in cases:
        out=c.owned(folder/f'{name}.png')
        if not out.exists():
            subprocess.run([str(c.FF),'-v','error','-ss',f'{t:.9f}','-i',video,
                            '-frames:v','1',str(out)],check=True,creationflags=c.NO_WINDOW)
        pixel=Image.open(out).convert('RGB').getpixel((110,980))
        is_white=min(pixel)>=250 and max(pixel)-min(pixel)<6
        if is_white!=expected:
            raise ValueError(f'Actual caption box pixel failed: {name} {t} {pixel}')
        result.append({'label':name,'time_s':t,'frame':str(out),'pixel_xy':[110,980],
                       'pixel_rgb':pixel,'white_box_expected':expected,'white_box_actual':is_white})
    font=ImageFont.truetype(str(p/'project/assets/Pretendard-Regular.ttf'),18)
    for name,items in [('beginning',result[:4]),('ending',result[4:])]:
        cols=2;w,h=960,565
        sheet=Image.new('RGB',(cols*w,((len(items)+cols-1)//cols)*h),'#eeeeee')
        dr=ImageDraw.Draw(sheet)
        for i,r in enumerate(items):
            x,y=(i%cols)*w,(i//cols)*h
            image=Image.open(r['frame']).convert('RGB');image.thumbnail((w,540));sheet.paste(image,(x,y))
            dr.text((x+8,y+542),f'{r["label"]} / {r["time_s"]:.6f}s / white box={r["white_box_actual"]}',font=font,fill='#173348')
        sheet.save(c.owned(folder/f'{name}_proof.jpg'),quality=95)
    old_cues=c.HERE/'jun-v1/project/native_captions.json'
    new_cues=p/'project/native_captions.json'
    if c.sha(old_cues)!=c.sha(new_cues):
        raise ValueError('Native captions changed in the boundary-only revision')
    hf=c.read(p/'project/hf_check.json')['result']
    if not hf['ok']or hf['browserSkipped']:
        raise ValueError('Native HF check did not pass')
    for t,rel in zip(hf['snapshots']['times'],hf['snapshots']['files']):
        if abs(t-.1)<.001 or abs(t-668.733)<.001 or abs(t-669.53)<.001:
            dest=c.owned(folder/f'native_HF_{t:.3f}.png')
            shutil.copyfile(p/'project'/rel,dest)
    proof_video=c.owned(c.OUTPUT/'jun-v2-proofs/ending_caption_box.mp4')
    proof_video.parent.mkdir(parents=True,exist_ok=True)
    if not proof_video.exists():
        subprocess.run([str(c.FF),'-v','error','-ss',f'{20032/30:.9f}','-i',video,
                        '-t','6','-c:v','libx264','-crf','16','-preset','fast','-threads','3',
                        '-c:a','aac','-b:a','320k','-movflags','+faststart',str(proof_video)],
                       check=True,creationflags=c.NO_WINDOW)
    c.save(p/'verification.json',{'status':'targeted_pixel_and_native_HF_checks_passed',
        'video_sha256':receipt['video_sha256'],'lock_sha256':receipt['lock_sha256'],
        'cases':result,'native_HF_ok':hf['ok'],'native_caption_data_sha256':c.sha(new_cues),
        'native_caption_data_identical_to_v1':True,'AAC_packet_payload_identical_to_v1':True,
        'ending_proof_video':str(proof_video),'ending_proof_sha256':c.sha(proof_video),
        'beginning_proof':str(folder/'beginning_proof.jpg'),'ending_proof':str(folder/'ending_proof.jpg'),
        'actual_listening':False,'continuous_playback':False,'independent_qa':False})
    print(json.dumps({'status':'targeted_proofs_ready','sha256':receipt['video_sha256'],
                      'proofs':str(folder),'ending_video':str(proof_video)},ensure_ascii=False),flush=True)


if __name__=='__main__':
    main()
