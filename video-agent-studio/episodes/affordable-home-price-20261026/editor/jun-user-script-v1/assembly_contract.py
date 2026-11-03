"""Validate forthcoming S01..S31 Jun timings and emit a normalized local EDL.
This deliberately cannot render an unfinished 31-scene film or call TTS.
"""
import argparse,hashlib,json,math
from pathlib import Path
HERE=Path(__file__).resolve().parent;EP=HERE.parents[1];ROOT=EP.parents[2]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def resolve(p):
    p=Path(p);return p if p.is_absolute() else ROOT/p
def valid_time(v):return isinstance(v,(float,int)) and not isinstance(v,bool) and math.isfinite(v) and v>=0
def validate(p):
    d=read(p);plan=read(EP/'director/user-recording-v1/scene_plan.json');caps=read(EP/'narration/jun-user-script-v1/caption_plan.json')
    assert d['schema_version']=='jun-scene-alignment-v1'
    assert d['timing_locked'] is True and d['timing_basis'] in ['provider_character_alignment_verified','forced_alignment_verified']
    assert d['source_doc_sha256']==plan['source_sha256']
    for k in ['manifest','caption_plan','scene_plan']:
        f=resolve(d[k]['path']);assert f.is_file() and sha(f)==d[k]['sha256'],k+' hash mismatch'
    manifest=read(resolve(d['manifest']['path']));assert manifest['source_doc_sha256']==plan['source_sha256']
    assert d['voice']['name']=='Jun' and d['voice']['revision']
    units={a['audio_unit_id']:a for a in d['audio_units']}
    for a in units.values():
        f=resolve(a['path']);assert f.is_file() and sha(f)==a['sha256'],'audio hash mismatch'
        assert valid_time(a['duration_s']) and a['duration_s']>0
    expected=[s['scene_id'] for s in plan['scenes']];assert [s['scene_id'] for s in d['scenes']]==expected,'Expected exactly ordered S01..S31'
    paragraphs={p['paragraph_id']:p for p in manifest['paragraphs']};global_t=0;edl=[];seen=[]
    for s,original in zip(d['scenes'],plan['scenes']):
        a=units[s['audio_unit_id']];start,end=s['audio_start_s'],s['audio_end_s'];assert valid_time(start) and valid_time(end) and start<end<=a['duration_s']+.001
        duration=end-start;assert s['paragraph_ids']==original['paragraph_ids']
        for item in s['characters']:
            p=paragraphs[item['paragraph_id']];n=len(p['spoken_text']);assert len(item['start_s'])==len(item['end_s'])==n,'Python Unicode codepoint indices, spoken_text only'
            assert item['spoken_sha256']==p['spoken_sha256'];previous=-1
            for st,en in zip(item['start_s'],item['end_s']):
                assert valid_time(st) and valid_time(en) and previous<=st<=en<=duration+.001;previous=st
        assert sorted(p['paragraph_id'] for p in s['characters'])==sorted(original['paragraph_ids'])
        want=[f'{s["scene_id"]}.b{i+1:02}' for i in range(len(original['beats']))]
        assert [b['beat_id'] for b in s['beats']]==want
        for b,ob in zip(s['beats'],original['beats']):
            assert b['anchor_original']==ob['anchor'] and valid_time(b['start_s']) and valid_time(b['end_s']) and b['start_s']<=b['end_s']<=duration
        cc=[c for c in caps['cues'] if c['scene_id']==s['scene_id']];assert [c['cue_id'] for c in s['captions']]==[c['cue_id'] for c in cc]
        for c,oc in zip(s['captions'],cc):
            assert c['display_lines']==oc['display_lines'],'Use narration caption_plan display_lines verbatim'
            assert valid_time(c['start_s']) and valid_time(c['end_s']) and c['start_s']<c['end_s']<=duration
        edl.append(dict(s,global_start_s=global_t,global_end_s=global_t+duration));global_t+=duration;seen.extend(s['paragraph_ids'])
    assert len(seen)==len(set(seen))==48
    return {'status':'timing_contract_validated_not_rendered','output_kind':'body_edl','renders_video':False,'timing_locked':True,'scene_count':31,'paragraph_count':48,'body_duration_s':global_t,'scenes':edl,'chapter_cards_and_brand_insertions':'apply parent edit schedule after this body EDL; preserve scene-local timings','final_outro':'actual last spoken word + 3 seconds, including existing tail silence'}
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('input');parser.add_argument('--out',default=str(HERE/'incoming/normalized_edl.json'));args=parser.parse_args()
    result=validate(resolve(args.input));out=Path(args.out).resolve();assert out.is_relative_to(HERE.resolve()),'Editor-owned output only'
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(result['status'])
