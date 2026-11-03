"""Pin the formal v7 source and every changed cue-group image for independent QA."""
import hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent;EP=HERE.parents[1];OUT=EP/'outputs/private-production-v3'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,r):p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
build=read(HERE/'build_receipt.json');plan=read(OUT/'render_plan.json');cli=read(HERE/'checks/summary.json');bbox=read(OUT/'preview/bbox_report.json');mix=read(HERE/'mix_receipt.json')
assert not build['candidate'] and not plan['caption_candidate']
assert cli['status']=='pass' and bbox['status']=='sampled_bbox_pass'
assert sha(EP/plan['caption_timing_path'])==build['caption_timing_sha256']
for ch in plan['chapters']:
    h=sha(OUT/ch['project']/'index.html')
    for rows in [cli['chapters'],bbox['checked_chapters'],mix['chapters']]:assert next(r['html_sha256'] for r in rows if r['chapter']==ch['chapter'])==h
groups=read(OUT/'cue_change_groups.json')['groups'];frames=[]
for group in groups:
    for cue in group['new_cues']:
        p=OUT/f'preview_captions/{group["group_id"]}_{cue["id"]}.png'
        with Image.open(p) as im:assert im.size==(1920,1080)
        frames.append({'group_id':group['group_id'],'chapter':group['chapter'],'cue_id':cue['id'],'text':cue['text'],'display_lines':cue.get('display_lines') or [cue['text']],
             'time_s':(cue['start_s']+cue['end_s'])/2,'file':p.relative_to(OUT).as_posix(),'sha256':sha(p),'html_sha256':sha(OUT/f'ch{group["chapter"]:02d}/index.html')})
contacts=[];font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)
for start in range(0,len(frames),8):
    sheet=Image.new('RGB',(1728,8*154),'#eeeae3');draw=ImageDraw.Draw(sheet)
    for slot,row in enumerate(frames[start:start+8]):
        y=slot*154
        with Image.open(OUT/row['file']) as im:sheet.paste(im.crop((96,876,1824,1000)),(0,y+28))
        draw.text((8,y+3),f'{row["group_id"]} / {row["cue_id"]} / {row["time_s"]:.3f}s',font=font,fill='#102333')
    p=OUT/f'preview_captions/contact_{start//8+1:02d}.jpg';sheet.save(p,quality=95);contacts.append({'file':p.relative_to(OUT).as_posix(),'sha256':sha(p)})
pins={'CLI_summary_sha256':sha(HERE/'checks/summary.json'),'BBox_report_sha256':sha(OUT/'preview/bbox_report.json'),'mix_receipt_sha256':sha(HERE/'mix_receipt.json'),
      'narration_handoff_sha256':build['narrator_receipt_sha256'],'caption_timing_sha256':build['caption_timing_sha256'],'authorization_sha256':build['authorization_sha256'],
      'visual_audio_reuse_manifest_sha256':sha(HERE/'visual_audio_reuse_manifest.json')}
metrics_path=HERE/'caption_fit_metrics.json';metrics=read(metrics_path)
assert metrics['status']=='pass' and metrics['caption_timing_sha256']==build['caption_timing_sha256']
pins['caption_fit_metrics_sha256']=sha(metrics_path)
packet={'status':'formal_caption_v7_source_ready_for_independent_QA','script_sha256':plan['script_sha256'],'caption_revision':'caption-v7','caption_timing_sha256':build['caption_timing_sha256'],
        'input_revisions':pins,'cue_count':build['cue_count'],'changed_group_count':len(groups),'frames':frames,'caption_crop_contacts':contacts,
        'groups_file':'cue_change_groups.json','source_CLI_BBox':'pass','visual_audio_invariance':'all 10 chapters exact non-caption HTML, original T/GSAP, audio tags and assets',
        'SRT_sha256':sha(OUT/'captions_measured.srt'),'EDL_sha256':sha(OUT/'assembly_edl.json'),'required_current_source_QA':'qa/private-production-v1/source_v7_pass_receipt.json',
        'glyph_metrics':'editor/private-production-v3/caption_fit_metrics.json','actual_max_line_width_px':metrics['max_line_width_px'],'glyph_vertical_bounds':[metrics['min_glyph_top_px'],metrics['max_glyph_bottom_px']],'target_frames':metrics['target_frames'],
        'actual_listening':False,'continuous_playback':False,'final_MP4_exists':False}
dump(OUT/'preview_captions/handoff.json',packet)
dump(HERE/'static_checks.json',{'status':'pass','script_sha256':plan['script_sha256'],'caption_timing_sha256':build['caption_timing_sha256'],'chapters':10,'cues':build['cue_count'],
     'scope':'exact caption-only conservation and current source receipts; prior fixed financial/visual QA reused','full_rendered':False,'actual_listening':False})
dump(HERE/'handoff.json',{'role':'editor','status':packet['status'],'source_packet':'outputs/private-production-v3/preview_captions/handoff.json','caption_timing_sha256':build['caption_timing_sha256'],'script_sha256':plan['script_sha256'],
     'validation':{'CLI_BBox':'pass','narrator':'formal 206-cue conservation/native pass','caption_groups':len(groups),'captured_changed_cues':len(frames),'visual_audio_T_anchors':'exact reuse'},
     'next_owner':'main forwards current source packet to QA; editor renders all affected chapters after source_v7_pass_receipt.json and caption-v7 EDL/SRT review','paid_calls':0,'prior_versions_readonly':True})
print(json.dumps({'status':packet['status'],'cues':build['cue_count'],'groups':len(groups),'changed_cue_PNGs':len(frames),'contacts':len(contacts),'caption_timing_sha256':build['caption_timing_sha256'],'SRT_sha256':packet['SRT_sha256'],'source_packet':str(OUT/'preview_captions/handoff.json')}))
