"""Read-only adapter for Feynman's measured scene-once output. No TTS/network.

Provider word edges, source/spoken mappings, natural pauses and native cue windows
are preserved. A measured output is not promoted to parent timing lock by itself.
"""
import argparse
import sys
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pipeline as p


NATIVE='actual_provider_WordBoundary_covering_anchor_no_interpolation'


def normalize_payload(script,raw):
    if [s['id'] for s in raw['scenes']]!=[s['id'] for s in script['scenes']]:
        raise ValueError('Use approved scene array order; narrator scene IDs differ')
    if raw['status']!='measured_pending_independent_QA' or raw['rate']!='+0%':
        raise ValueError('Actual measured InJoon +0% scene-once output required')
    if raw.get('brand_and_chapter_cards_included') is not False:
        raise ValueError('Narrator clock must be body-only; editor adds brand/chapter cards')
    scenes=[]
    for writer,scene in zip(script['scenes'],raw['scenes']):
        sid=writer['id']
        if scene['narration']!=writer['narration'] or scene['title']!=writer['title']:
            raise ValueError(sid+': exact current narration/title differs')
        if len(scene['beats'])!=len(writer['beats']):raise ValueError(sid+': beat count differs')
        cues=scene['cues'];beats=[]
        for c in cues:
            if writer['narration'][c['source_start']:c['source_end']]!=c['text']:
                raise ValueError(sid+': cue original source span differs')
            if 'actual_provider_WordBoundary' not in c['timing_basis']:
                raise ValueError(sid+': estimated cue timing is forbidden')
        for i,(expected,b) in enumerate(zip(writer['beats'],scene['beats'])):
            if b['anchor']!=expected['anchor'] or b['action']!=expected['action'] or b['timing_basis']!=NATIVE:
                raise ValueError(sid+': changed anchor/action or estimated timing')
            if writer['narration'][b['source_start']:b['source_end']]!=expected['anchor']:
                raise ValueError(sid+': anchor original span differs')
            covered=[c for c in cues if c['first_word_index']<=b['last_word_index'] and b['first_word_index']<=c['last_word_index']]
            if not covered:raise ValueError(sid+': no actual cue evidence for beat')
            if not all(any(c['first_word_index']<=w<=c['last_word_index'] for c in covered) for w in range(b['first_word_index'],b['last_word_index']+1)):
                raise ValueError(sid+': actual anchor word coverage is incomplete')
            beats.append({**b,'beat_index':i,'char_start':b['source_start'],'char_end':b['source_end'],'cue_ids':[c['id'] for c in covered],'timing_basis':'native_word_boundary','provider_timing_basis':b['timing_basis']})
        result={'scene_id':sid,'audio_path':scene['audio_48k_path'],'audio_sha256':scene['audio_48k_sha256'],'original_audio24_path':scene['audio_path'],'original_audio24_sha256':scene['audio_sha256'],'duration_s':scene['duration_s'],'last_speech_end_s':scene['last_speech_end_s'],'last_speech_basis':scene['last_speech_basis'],'gap_after_s':scene['gap_after_s'],'body_proposed_start_s':scene['scene_start_s'],'body_proposed_end_s':scene['scene_end_s'],'cues':cues,'beatanchors':beats,'words':scene['words'],'display_mapping':scene['display_mapping'],'transforms':scene['transforms'],'segments':scene['segments'],'native_clock_modified':False,'actual_listening':False}
        p.validate_voice(writer,result);scenes.append(result)
    return {'status':'measured_adapter_ready_parent_lock_pending','clock':'scene_local_seconds','script_sha256':raw['script_sha256'],'audio_revision':raw['audio_revision'],'voice':raw['voice'],'rate':'0%','provider_rate':raw['rate'],'scenes':scenes,'native_timing_scope':raw['timing_scope'],'cut_gap_s':raw['cut_gap_s'],'final_hold_from_last_speech_s':raw['final_hold_from_last_speech_s'],'final_hold_already_in_last_WAV':True,'brand_and_chapter_cards_included':False,'actual_listening':False,'continuous_playback':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--script',required=True);parser.add_argument('--timing',required=True);parser.add_argument('--out',required=True);parser.add_argument('--timing-lock')
    args=parser.parse_args();sf=p.source(args.script);tf=p.source(args.timing);raw=p.read(tf)
    if raw['script_sha256']!=p.sha(sf):raise ValueError('Narrator output is for another script version')
    result=normalize_payload(p.read(sf),raw)
    for s in result['scenes']:
        for path_key,sha_key in [('audio_path','audio_sha256'),('original_audio24_path','original_audio24_sha256')]:
            file=p.source(s[path_key])
            if p.sha(file)!=s[sha_key]:raise ValueError('Changed actual audio: '+s['scene_id'])
        info=p.probe(p.source(s['audio_path']));streams=[v for v in info['streams'] if v['codec_type']=='audio']
        if len(streams)!=1 or streams[0]['sample_rate']!='48000' or abs(float(info['format']['duration'])-s['duration_s'])>.001:
            raise ValueError('Actual 48k PCM metadata differs: '+s['scene_id'])
    if args.timing_lock:
        lock_path=p.source(args.timing_lock);lock=p.read(lock_path)
        if not lock_path.is_relative_to((p.EP/'director').resolve()) or lock.get('approved') is not True or lock['timing_sha256']!=p.sha(tf) or lock['script_sha256']!=p.sha(sf):
            raise ValueError('Exact parent timing lock mismatch')
        result.update(status='timing_locked',parent_timing_lock=p.pin(lock_path))
    result.update(source_script=p.pin(sf),native_timing=p.pin(tf),adapter=p.pin(Path(__file__)))
    p.dump(p.owned(args.out),result)
    print({'status':result['status'],'scenes':len(result['scenes']),'native_timing_modified':False})


if __name__=='__main__':main()
