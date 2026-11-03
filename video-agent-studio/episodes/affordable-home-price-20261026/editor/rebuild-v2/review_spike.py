"""Contact sheets from actual decoded spike frames, not HTML screenshots."""
import json
import sys
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pipeline as p
from PIL import Image,ImageDraw


def main():
    run=p.OUT/'design-spike-v1';receipt=p.read(run/'render_receipt.json');result=[]
    for row in receipt['scenes']:
        frames=row['frame_evidence'];model=p.read(Path(row['folder'])/'scene.json')
        chosen=[]
        for b in model['beats']:
            chosen.append(min(frames,key=lambda r:abs(r['pts_s']-(b['start_s']+.55))))
        canvas=Image.new('RGB',(1920,math_rows(len(chosen))*390),'#dfe2e5');draw=ImageDraw.Draw(canvas)
        for i,f in enumerate(chosen):
            x=i%3*640;y=i//3*390;im=Image.open(f['path']).convert('RGB').resize((640,360));canvas.paste(im,(x,y));draw.text((x+10,y+366),f"design-only / frame {f['frame_index']} / {f['pts_s']:.3f}s",fill='#172f43')
        target=run/(row['kind']+'_progression.png');canvas.save(target)
        last=frames[-1]
        full=run/(row['kind']+'_final_encoded.png');Image.open(last['path']).save(full)
        result.append({'kind':row['kind'],'progression':str(target),'final_fullres':str(full),'frame_plan':[{'path':f['path'],'frame_index':f['frame_index'],'pts_s':f['pts_s']} for f in chosen],'provisional_design_only':True})
    baseline=p.EP/'qa/comparison-housing-choice-v1'
    for row in result:
        base=baseline/('baseline_04m45_full.png' if row['kind']=='funding_waterfall' else 'progression/baseline_s4b_3.png')
        if not base.exists():base=baseline/'baseline_04m45_full.png'
        canvas=Image.new('RGB',(1920,570),'#dfe2e5')
        for i,file in enumerate([base,Path(row['final_fullres'])]):canvas.paste(Image.open(file).convert('RGB').resize((960,540)),(i*960,0))
        draw=ImageDraw.Draw(canvas);draw.text((15,546),'Approved Jun baseline (encoded sample)',fill='#172f43');draw.text((975,546),'Rebuild-v2 provisional silent design only (encoded)',fill='#172f43')
        target=run/(row['kind']+'_baseline_comparison.png');canvas.save(target);row['baseline_comparison']=str(target)
    p.dump(run/'visual_review_packet.json',{'status':'encoded_samples_prepared','provisional_design_only':True,'continuous_playback':False,'actual_listening':False,'scenes':result})
    print(json.dumps({'status':'encoded_review_packet_ready','scenes':len(result)}))


def math_rows(n):return (n+2)//3
if __name__=='__main__':main()
