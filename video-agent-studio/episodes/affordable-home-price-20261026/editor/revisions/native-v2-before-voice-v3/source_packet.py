"""Package actual source snapshots; audio-delta gate stays closed."""
import json,shutil,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
sys.dont_write_bytecode=True;sys.path.insert(0,str(Path(__file__).resolve().parent))
from build import EP,OUT,HERE,read,sha,dump
def main():
    bbox=read(HERE/'bbox_measured_v2.json');cli=read(HERE/'checks/native-v2/summary.json');sources=read(OUT/'scene_source_manifest.json');plan=read(OUT/'render_plan.json')
    assert bbox['status']==cli['status']=='pass' and sources['scene_count']==45 and sources['cue_count']==150
    frames=[]
    for chapter in bbox['chapters']:
        file=OUT/f'ch{chapter["chapter"]:02}/index.html';assert sha(file)==chapter['html_sha256']==next(c['html_sha256'] for c in cli['chapters'] if c['chapter']==chapter['chapter'])
        for frame in chapter['frames']:
            assert sha(OUT/frame['file'])==frame['sha256'];frames.append({'chapter':chapter['chapter'],**frame})
    body=[f for f in frames if not f['scene_id'].startswith('CH')];assert len(body)==45
    folder=OUT/'preview-measured-v2';font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20);sheets=[]
    for page,start in enumerate(range(0,len(body),10),1):
        sheet=Image.new('RGB',(1280,1950),'white');draw=ImageDraw.Draw(sheet)
        for i,frame in enumerate(body[start:start+10]):
            x=i%2*640;y=i//2*390
            with Image.open(OUT/frame['file']) as im:sheet.paste(im.convert('RGB').resize((640,360)),(x,y))
            draw.text((x+8,y+362),f'CH{frame["chapter"]:02} / {frame["scene_id"]} / {frame["time_s"]:.3f}s',font=font,fill='#173348')
        file=folder/f'contact_{page:02}.jpg';sheet.save(file,quality=94);sheets.append({'file':file.relative_to(OUT).as_posix(),'sha256':sha(file),'scope':'source overview only; fullres PNGs retained'})
    receipt={'status':'45_scene_review_source_CLI_BBox_pass_voice_v3_pending','script_sha256':sources['script_sha256'],'timing_sha256':sources['timing_sha256'],'central_scenes_sha256':sources['central_scenes_sha256'],'native_revision':'production-injoon-v2; review-only reference, v3 repair pending','scene_count':45,'meaning_cues':150,'graphic_kinds':sources['different_native_graphic_kinds'],'body_representatives':body,'chapter_title_frames':[f for f in frames if f['scene_id'].startswith('CH')],'contact_sheets':sheets,'CLI_receipt':'editor/checks/native-v2/summary.json','CLI_sha256':sha(HERE/'checks/native-v2/summary.json'),'BBox_receipt':'editor/bbox_measured_v2.json','BBox_sha256':sha(HERE/'bbox_measured_v2.json'),'text_checks':bbox['text_checks'],'findings':len(bbox['failures']),'semantic_cue_mapping':'all150 authored phrase-matched visual targets; no time-zero fallback','font_shrink':False,'actual_encoded_frames':False,'canonical_carve':'not executed; explicitly held for approved actual v3 audio','full_film_render_authorized':False,'audio_delta_scene_ids':['S014','S019','S024','S030'],'independent_source_QA':'main will resume after v3 source','no_other_owner_writes':True}
    dump(HERE/'source_build_handoff.json',receipt)
    archive=OUT/'source-archive/native-v2-complete-review'
    if not archive.exists():
        archive.mkdir(parents=True)
        for name in ['assembly_edl.json','captions_measured.srt','global_captions.json','render_plan.json','scene_bindings.json','snapshot_times.json','scene_source_manifest.json']:shutil.copy2(OUT/name,archive/name)
        for ch in range(1,11):shutil.copytree(OUT/f'ch{ch:02}',archive/f'ch{ch:02}',ignore=shutil.ignore_patterns('.hyperframes','frames-cache'))
        shutil.copy2(HERE/'source_build_handoff.json',archive/'source_build_handoff.json')
        hashes={p.relative_to(archive).as_posix():sha(p) for p in archive.rglob('*') if p.is_file()}
        dump(archive/'preservation_manifest.json',{'revision':'v2_complete_review_source_before_phonetic_v3','files_sha256':hashes,'original_narration_v2_preserved_readonly':True})
    dump(HERE/'handoff.json',{'role':'editor','status':receipt['status'],'source_handoff':'editor/source_build_handoff.json','source_handoff_sha256':sha(HERE/'source_build_handoff.json'),'script_sha256':sources['script_sha256'],'native_v2_timing_sha256':sources['timing_sha256'],'EDL':'outputs/private-production-v1/assembly_edl.json','EDL_scope':'v2 preserved; cumulative offsets must be rebuilt after actual v3 handoff','v2_archive':archive.relative_to(EP).as_posix(),'45_scene_graphics_ready':True,'CLI':'10 pass current SHA','BBox':{'status':'pass','text_checks':bbox['text_checks'],'findings':len(bbox['failures'])},'canonical_carve_executed':False,'final_timing_frozen':False,'full_render_executed':False,'full_render_authorized':False,'waiting_for':'formal actual voice v3 technical handoff + ASR delta approval; then measured source and canonical carve gates','other_owner_files_modified':False})
    print(json.dumps({'status':receipt['status'],'scenes':45,'frames':len(frames),'contact_sheets':len(sheets),'text_checks':bbox['text_checks'],'findings':len(bbox['failures']),'v2_source_archive':archive.relative_to(EP).as_posix()}))
if __name__=='__main__':main()
