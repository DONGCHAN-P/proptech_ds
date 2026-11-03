"""Publish local QA packet from actual completed render receipts only."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw,ImageFont
H=Path(__file__).resolve().parent;E=H.parents[1];R=E.parents[2]
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def clock(s):
 ms=round(s*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000);return f'{h:02}:{m:02}:{s:02},{ms:03}'
delivered=[]
for k in ['main','promo','analysis']:
 rp=H/f'render_receipt_{k}_v1.json'
 if not rp.exists():continue
 r=read(rp)
 if not r.get('full_decode_passed'):continue
 file=Path(r['output']);assert file.exists() and sha(file)==r['output_sha256']
 project=H/'main' if k=='main' else H/'shorts'/k
 cm=read(project/'caption_mapping.json');srt='\n\n'.join(f'{i+1}\n{clock(c["start_s"])} --> {clock(c["end_s"])}\n{c["text"]}' for i,c in enumerate(cm['cues']))+'\n'
 sp=file.with_suffix('.srt');sp.write_text(srt,encoding='utf-8')
 sheets=[]
 fm=Path(r.get('decoded_frame_manifest',''))
 if fm.is_file():
  frames=read(fm)
  for page in range(0,len(frames),12):
   group=frames[page:page+12];canvas=Image.new('RGB',(1280,4*264),'#edf0ef');d=ImageDraw.Draw(canvas)
   for j,f in enumerate(group):
    im=Image.open(f['file']).convert('RGB');im.thumbnail((420,236));x=(j%3)*426;y=(j//3)*264;canvas.paste(im,(x,y+24));d.text((x+6,y+5),f'{f["time_s"]:.3f}s',fill='#173348')
   dest=fm.parent/f'contact_{page//12+1:02d}.jpg';canvas.save(dest,quality=90);sheets.append(str(dest))
 delivered.append({'id':k,'file':str(file),'sha256':r['output_sha256'],'size_bytes':r['bytes'],'probe':r['probe'],'full_decode_passed':True,'render_receipt':str(rp),'srt':str(sp),'srt_sha256':sha(sp),'decoded_frame_manifest':r.get('decoded_frame_manifest'),'decoded_contact_sheets':sheets,'actual_listening':False,'continuous_playback':False})
packet={'task_id':'top20-hf-production-v1','status':'three_encoded_files_technically_verified' if len(delivered)==3 else 'partial_encoded_files_ready_for_independent_QA','files':delivered,'source_script':'director/top20-production-v1/scene_proposals_v4.json','source_timing':'director/top20-production-v1/locked_timing.json','source_timing_sha256':sha(E/'director/top20-production-v1/locked_timing.json'),'audio_revision':read(E/'director/top20-production-v1/locked_timing.json')['audio_revision'],'canonical_carve_receipt':'audio_carve_receipt.json','independent_QA_required':['encoded main/shorts text and all cut boundaries','caption/number speech anchors','actual speech/ending consonants, music balance, pronunciation/naturalness','portrait UI simulation at final encoded frame times'],'new_paid_calls':0,'uploads_performed_by_editor':0,'notes':['原本v3/표시v4/사진20장/지도 원본 보존','8개 핵심 장면 ASR은 총괄 수행 범위, 실제 청취로 기록하지 않음','Studio preview EPERM; local snapshots and encoded file verification are separate evidence']}
save(H/'encoded_qa_packet.json',packet)
handoff=read(H/'handoff.json');handoff.update(status=packet['status'],rendered_files=delivered,input_versions={'script':'director/top20-production-v1/scene_proposals_v4.json','timing':'director/top20-production-v1/locked_timing.json','timing_sha256':packet['source_timing_sha256'],'audio_revision':packet['audio_revision'],'photos':'photo_assets_v2','map':'2024 actual SVG geometry'},verification={'project_checks':'all three passed; lint/runtime/layout/contrast no findings','snapshot_scope':'main32, promo9, analysis10 actual timing samples; main27 scenes plus brand boundary samples','full_render_count':len(delivered),'full_decode_count':len(delivered),'actual_listening':False,'continuous_playback':False,'independent_QA':'representative3 passed parent report; final encoded review delegated'},unresolved=['final independent encoded visual/audio QA and private upload by director'],next_role='independent QA -> director private upload')
handoff['tools'].update(FFmpeg='7.1 essentials (full select/psnr build)',canonical_core='0.8.181');save(H/'handoff.json',handoff)
print(json.dumps({'ready':[{'id':v['id'],'file':v['file'],'sha256':v['sha256'],'duration_s':v['probe']['format']['duration']} for v in delivered],'qa_packet':str(H/'encoded_qa_packet.json')},ensure_ascii=False))
