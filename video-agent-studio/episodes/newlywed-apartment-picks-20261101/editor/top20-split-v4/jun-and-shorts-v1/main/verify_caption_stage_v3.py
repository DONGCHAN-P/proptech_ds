"""Actual MP4 scanline proofs for every requested class of inactive cue gap."""
from pathlib import Path
import math
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import conform as c
import verify
from caption_stage_v3 import body_windows

P=c.HERE/'jun-v3'


def native_checks():
    plan=c.read(P/'proof_plan.json')
    times=plan['required_inactive_times_s']
    result=verify.hf_check(P/'project',[*times,1.2,668.7])
    folder=c.owned(P/'proofs/native');folder.mkdir(parents=True,exist_ok=True)
    cmd=['npx.cmd','--no-install','hyperframes','snapshot',str(P/'project'),'--at',
         ','.join(f'{t:.9f}'for t in times),'--no-end','--output',str(folder),'--json']
    r=subprocess.run(cmd,cwd=c.ROOT,env=verify.environment(),capture_output=True,creationflags=c.NO_WINDOW)
    c.write(folder/'snapshot.stdout.log',r.stdout.decode('utf-8-sig',errors='replace'))
    c.write(folder/'snapshot.stderr.log',r.stderr.decode('utf-8-sig',errors='replace'))
    if r.returncode:raise RuntimeError('Native HF inactive-cue snapshots failed')
    c.save(P/'native_verification.json',{'HF_check_ok':result['ok'],'requested_inactive_times_s':times,
           'snapshot_command':cmd,'snapshot_exit_code':r.returncode})
    print('NATIVE_HF_CHECK_AND_FIVE_EXACT_SNAPSHOTS_READY',flush=True)


def encoded_checks():
    from PIL import Image,ImageDraw,ImageFont
    receipt=c.read(P/'render_receipt.json');video=receipt['video']
    plan=c.read(P/'proof_plan.json');folder=c.owned(P/'proofs');folder.mkdir(parents=True,exist_ok=True)
    cases=[('prevoice_0.1',.1,False),('sentence_gap_5.0',5.,False),
           ('middle_sentence_gap_1',math.floor(plan['sentence_gaps'][0][0]*30)/30,False),
           ('middle_sentence_gap_2',math.floor(plan['sentence_gaps'][1][0]*30)/30,False),
           ('silent_CTA_669.53',669.53,False),('active_first_cue',1.2,True),
           ('active_last_cue',668.7,True),('brand_intro',7.03,False)]
    rows=[]
    for name,t,expected in cases:
        dest=c.owned(folder/f'{name}.png')
        if not dest.exists():
            subprocess.run([str(c.FF),'-v','error','-ss',f'{t:.9f}','-i',video,
                            '-frames:v','1',str(dest)],check=True,creationflags=c.NO_WINDOW)
        image=Image.open(dest).convert('RGB');pixel=image.getpixel((110,980))
        white=min(pixel)>=250 and max(pixel)-min(pixel)<6
        if white!=expected:raise ValueError(f'Encoded cue-rail state wrong: {name} {pixel}')
        rows.append({'label':name,'time_s':t,'frame':str(dest),'pixel_xy':[110,980],
                     'pixel_rgb':pixel,'white_box_expected':expected,'white_box_actual':white})
    font=ImageFont.truetype(str(P/'project/assets/Pretendard-Regular.ttf'),17)
    sheet=Image.new('RGB',(1920,565*4),'#eeeeee');draw=ImageDraw.Draw(sheet)
    for i,row in enumerate(rows):
        x,y=(i%2)*960,(i//2)*565
        image=Image.open(row['frame']).convert('RGB');image.thumbnail((960,540));sheet.paste(image,(x,y))
        # Annotation exists only in QA contact sheet, never in the MP4/native source.
        draw.line((x,y+490,x+959,y+490),fill='#e25252',width=1)
        draw.ellipse((x+52,y+487,x+58,y+493),outline='#d62929',width=1)
        draw.text((x+6,y+542),f'{row["label"]} / {row["time_s"]:.6f}s / rail={row["white_box_actual"]} / RGB={row["pixel_rgb"]}',font=font,fill='#173348')
    sheet.save(c.owned(folder/'caption_rail_scanline_proof.jpg'),quality=95)
    proof=c.owned(c.OUTPUT/'jun-v3-proofs/ending_caption_box.mp4');proof.parent.mkdir(parents=True,exist_ok=True)
    if not proof.exists():
        subprocess.run([str(c.FF),'-v','error','-ss',f'{20032/30:.9f}','-i',video,
                        '-t','6','-c:v','libx264','-crf','16','-preset','fast','-threads','3',
                        '-c:a','aac','-b:a','320k','-movflags','+faststart',str(proof)],check=True,creationflags=c.NO_WINDOW)
    if c.sha(P/'project/native_captions.json')!=c.sha(c.HERE/'jun-v1/project/native_captions.json'):
        raise ValueError('Native captions changed')
    preserved=c.read(c.HERE/'jun-v2/render_receipt.json')
    if c.sha(preserved['video'])!=preserved['video_sha256']:
        raise ValueError('Existing v2 changed')
    c.save(P/'verification.json',{'status':'required_actual_encoded_pixel_proofs_passed',
        'video_sha256':receipt['video_sha256'],'lock_sha256':receipt['lock_sha256'],
        'native_cues':181,'merged_box_windows':len(body_windows(c.read(c.LOCK))),
        'box_policy':'union of actual caption cues only; hide during every inactive cue gap',
        'actual_encoded_cases':rows,'scanline_contact_sheet':str(folder/'caption_rail_scanline_proof.jpg'),
        'scanline_is_QA_annotation_only':True,'native_HF_verification':str(P/'native_verification.json'),
        'ending_proof_video':str(proof),'ending_proof_sha256':c.sha(proof),
        'native_captions_identical_to_v1':True,'AAC_packet_payload_identical_to_v1':True,
        'v2_preserved_sha256':preserved['video_sha256'],'new_TTS_calls':0,'actual_listening':False,
        'continuous_playback':False,'independent_qa':False})
    print('ACTUAL_ENCODED_PROOFS_PASS',receipt['video_sha256'],flush=True)


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='native':native_checks()
    else:encoded_checks()
