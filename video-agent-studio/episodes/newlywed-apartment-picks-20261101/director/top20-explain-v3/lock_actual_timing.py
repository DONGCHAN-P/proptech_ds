"""Director validates PCM/provider coverage and adapts words for the editor contract."""
from pathlib import Path
from collections import defaultdict
from datetime import datetime,timezone
import copy,hashlib,json,re,wave
D=Path(__file__).resolve().parent;E=D.parents[1];R=E.parents[2];N=E/'narration/top20-explain-v3'
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
norm=lambda s:re.sub('[^0-9a-z가-힣]','',s.lower())
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def resolve(p):p=Path(p);return p if p.is_absolute()else R/p
def wav(p):
    with wave.open(str(p),'rb')as w:return {'frames':w.getnframes(),'rate':w.getframerate(),'channels':w.getnchannels(),'width':w.getsampwidth(),'duration':w.getnframes()/w.getframerate()}
def main():
    proposal=N/'timing_proposals.json';t=read(proposal);wpath=resolve(t['words_file']);w=read(wpath);source=read(E/'writer/top20-explain-v3/scene_proposals_v6.json')
    approval=read(D/'script_approval.json');assert t['script_sha256']==approval['script_md_sha256'] and t['scene_json_sha256']==approval['scene_json_sha256']
    assert t['timing_basis']=='actual_audio' and not t['character_proportional_alignment_used'] and not t['old_timing_fallback_used']
    assert sha(wpath)==t['words_file_sha256'] and sha(resolve(t['audio_file']))==t['audio_sha256']
    audio=wav(resolve(t['audio_file']));assert(audio['rate'],audio['channels'],audio['width'])==(44100,1,2)
    assert audio['duration']>480 and abs(audio['duration']-t['total_duration_with_brand_and_hold_s'])<1e-7
    expected={s['scene_id']:s for s in source['scenes']};assert list(expected)==[s['scene_id']for s in t['scenes']]
    words=copy.deepcopy(w['words']);groups=defaultdict(list)
    for row in words:groups[row['sentence_id']].append(row)
    count=0;checks=[]
    for scene in t['scenes']:
        ss=expected[scene['scene_id']]['sentences'];assert [s['sentence_id']for s in ss]==[s['sentence_id']for s in scene['sentences']]
        assert [s['text']for s in ss]==[s['text']for s in scene['sentences']]
        if not ss:continue
        info=wav(resolve(scene['audio_path']));assert sha(resolve(scene['audio_path']))==scene['audio_sha256']
        assert abs(info['duration']-scene['duration_s'])<1e-7
        for s in scene['sentences']:
            g=groups[s['sentence_id']];assert g and all(x['scene_id']==scene['scene_id']for x in g)
            assert ''.join(norm(x.get('provider_text',x['text']))for x in g)==norm(s['reading_text']),s['sentence_id']
            cursor=0
            for row in g:
                token=norm(row.get('provider_text',row['text']));row['sentence_normalized_char_start']=cursor;cursor+=len(token);row['sentence_normalized_char_end']=cursor
                assert abs(row['start_s']-scene['start_s']-row['local_start_s'])<1e-6
                assert 0<=row['local_start_s']<row['local_end_s']<=info['duration']+.002
            assert abs(s['start_s']-scene['start_s']-s['local_start_s'])<1e-6
            count+=1
        scene['sentence_times']=[dict(s,start_s=s['local_start_s'],end_s=s['local_end_s'])for s in scene['sentences']]
        checks.append({'scene_id':scene['scene_id'],'pcm_samples':info['frames'],'sentences':len(ss),'reading_word_coverage':'exact'})
    assert count==133 and len(groups)==133
    adapter=copy.deepcopy(w);adapter.update(words=words,source_words_file=wpath.relative_to(R).as_posix(),source_words_sha256=sha(wpath),
       editor_contract='sentence_normalized_char_* are cumulative normalized provider chars per sentence; provider/local/global times unchanged')
    save(D/'words_for_editor.json',adapter)
    for brand in t['brand_visuals']:assert sha(resolve(brand['path']))==brand['sha256']
    assert abs(t['brand_outro']['start_s']-t['last_spoken_end_s']-3)<1e-7
    for key in ['brand_intro','brand_outro']:
        b=t[key];b['audio_sha256']=b['sha256'];b['visual_sha256']=next(v['sha256']for v in t['brand_visuals']if v['id']==key);b['sha256']=b['visual_sha256']
    t.update(timing_locked=True,status='director_actual_audio_locked',lock_owner='director',
       locked_at=datetime.now(timezone.utc).isoformat(),duration_s=audio['duration'],total_duration_s=audio['duration'],last_speech_end_s=t['last_spoken_end_s'],
       words_file=str(D/'words_for_editor.json'),words_file_sha256=sha(D/'words_for_editor.json'),
       source_words_file=str(wpath),source_words_sha256=sha(wpath),source_timing=str(proposal),source_timing_sha256=sha(proposal),
       script_proposals_file=str(E/'writer/top20-explain-v3/scene_proposals_v6.json'),script_approval_receipt=str(D/'script_approval.json'),
       actual_listening_performed=False,continuous_playback_performed=False)
    t.update(revision='top20-explain-v3',script_md_sha256=t['script_sha256'],sentence_time_base='scene_local',
       sentence_times_time_base='scene_local',sentences_time_base='global',audio_time_base='global',
       audio_includes_brand=True,brand_audio_policy='full PCM includes exactly one copy of clean brand audio; inserted brand videos must be muted',
       inserts=[{'kind':'intro'if b['id']=='brand_intro'else'outro','start_s':b['start_s'],'duration_s':b['duration_s'],
                 'source_file':str(resolve(b['path'])),'sha256':b['sha256']}for b in t['brand_visuals']])
    save(D/'locked_timing.json',t)
    report={'status':'passed','sentences':count,'words':len(words),'duration_s':audio['duration'],'wave':audio,
       'source_proposal_sha256':sha(proposal),'source_words_sha256':sha(wpath),'editor_words_sha256':sha(D/'words_for_editor.json'),
       'locked_timing_sha256':sha(D/'locked_timing.json'),'price_or_script_values_changed':False,'checks':checks,
       'actual_listening_performed':False,'ASR_status':'separate supporting evidence pending'}
    save(D/'actual_timing_verification.json',report)
    print(json.dumps({k:report[k]for k in ['status','sentences','words','duration_s','locked_timing_sha256']},ensure_ascii=False))
if __name__=='__main__':main()
