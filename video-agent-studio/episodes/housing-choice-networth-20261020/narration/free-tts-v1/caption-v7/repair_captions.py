"""Offline, caption-only v7. Source, speech and all audio anchors are immutable."""
import copy
from functools import lru_cache
import importlib.util
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
SIDE = HERE.parent
EP = SIDE.parents[1]
SOURCE = SIDE / 'final_timing.v6.json'
SCRIPT_SHA = '0368c9e08b8a2447ed429d9e78ab9a8238b2d823c27467362174600876a797b7'
SOURCE_SHA = 'b1fdcb5025e326df80b7b0c6296e89d0fa526007427c69e5688205f579d0493b'
spec = importlib.util.spec_from_file_location('production_narration_readonly', SIDE/'production_narration.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
PREPARED = p.load(SIDE/'prepare-v6/prepared.json')
PARAGRAPHS = {q['paragraph']: q for ch in PREPARED['chapters'] for q in ch['paragraphs']}
CONTRACT_PATH = EP/'editor/private-production-v3/caption_renderer_contract.json'
CONTRACT = p.load(CONTRACT_PATH)


def paragraph(number):
    return PARAGRAPHS[number]


def compact(text):
    return re.sub(r'\s+', '', text)


def is_short(cue):
    return len(compact(cue['text'])) <= 9


def width_ceiling(text):
    # Deliberately conservative: every source character, including ASCII and
    # spaces, is charged a full 40 px em. Actual glyph BBox remains editor QA.
    return len(text) * CONTRACT['font']['size_px']


def phrase_score(left, right):
    """Prefer grammatical clauses, then intact noun/verb phrases; never a lone verb."""
    token = left.split()[-1]
    score = 0
    if token.endswith(','):
        score += 110
    if re.search(r'(?:으면|다면|하면|지만|이지만|으므로|이므로|때문에|하면서|어도|아도|더라도|으며|이며|하고|이고|했고|됐고|려면|하면|나면|보면|고르면|되면|바꾸면|넣으면|오르면|줄어|끝나|보다|뒤|때는|때|따라|대신|함께|나란히|먼저|이후에는)$', token):
        score += 65
    elif token.endswith('면'):
        score += 65
    if token in ('연','월','약','최소','최대','제','한','두','세','네','다섯','여섯','일곱','여덟','아홉','열','서른','수','더','덜','같은','다른','새로','그','이','그런','이런','어떤','모든'):
        score -= 250
    if re.search(r'(?:하는|되는|있는|없는|남는|갚는|시키는|움직이는|보이는|바뀌는|들어가는|모은|넣은|갚은|지난|들어간|줄어든|쓸|할|낼|볼|될|살|남은|많은|높은|작은|큰|중요한|필요한|가능한|고정한|포함한|동일한|적절한|보유한|적용한|정한|빼야|갚아야|실거주)$', token):
        score -= 140
    if len(right.split()) <= 2 or len(compact(right)) <= 9:
        score -= 220
    return score


def valid_phrase_cut(left,right):
    if phrase_score(left,right)<0:
        return False
    joined=left+' '+right;cut=len(left)
    protected=r'실거주 매매|한국 돈으로 환산한 자산은|원화 총수익|연평균 상승률|원금 상환|초기 순자산|평가 순자산|저축 습관|자산 형성|\d+년 후|\d{4}년\s+\d분기(?:부터|까지의)?'
    return not any(m.start()<cut<m.end() for m in re.finditer(protected,joined))


@lru_cache(None)
def display_lines(text):
    if width_ceiling(text) <= 1440:
        return (text,)
    choices = []
    for m in re.finditer(r'\s+', text):
        left, right = text[:m.start()], text[m.end():]
        if max(len(left), len(right)) > 40 or min(len(compact(left)),len(compact(right))) < 10:
            continue
        if not valid_phrase_cut(left,right):
            continue
        score = phrase_score(left,right) - abs(len(left)-len(right))*2
        choices.append((score,left,right))
    if choices:
        _,left,right = max(choices)
        return (left,right)
    if width_ceiling(text) <= 1600:
        return (text,)
    return ()


@lru_cache(None)
def native(number):
    ch = next(ch for ch in p.load(SOURCE)['chapters'] if any(q['paragraph']==number for q in ch['paragraphs']))
    placement = next(q for q in ch['paragraphs'] if q['paragraph']==number)
    events = p.load(Path(placement['wave_file']).parent/'native_boundaries.json')
    if isinstance(events,dict):
        events = events.get('events',events.get('boundaries'))
    assert all(e['type']=='WordBoundary' for e in events)
    q = paragraph(number)
    assert p.norm(''.join(e['text'] for e in events)) == p.norm(q['spoken_text'])
    intervals=[]; cursor=0
    for e in events:
        length=len(p.norm(e['text']))
        assert length and e['duration'] > 0
        intervals.append((cursor,cursor+length));cursor+=length
    return events,intervals,placement


def normalized_position(q, position):
    return len(p.norm(q['spoken_text'][:p.spoken_position(q['display_mapping'],position)]))


def allowed_cut(q, position):
    normalized = normalized_position(q,position)
    _,intervals,_ = native(q['paragraph'])
    return normalized in {0,intervals[-1][1],*(y for x,y in intervals)}


def sentence_spans(q):
    text=q['text'];start=0;result=[]
    for m in re.finditer(r'[.!?。！？](?:\s+|$)',text):
        end=m.start()+1
        if allowed_cut(q,end):
            result.append((start,end));start=m.end()
    if start<len(text):
        result.append((start,len(text)))
    return result


def split_sentence(q, start, end):
    text=q['text']
    if display_lines(text[start:end]):
        return [(start,end)]
    # Dynamic programming over actual word-boundary cuts, with lookahead for
    # complete clauses and a minimum meaningful tail. No timing interpolation.
    cuts=[(start,start)]
    for m in re.finditer(r'\s+',text[start:end]):
        left=start+m.start();right=start+m.end()
        if allowed_cut(q,left) and allowed_cut(q,right): cuts.append((left,right))
    cuts.append((end,end))
    @lru_cache(None)
    def solve(i):
        best=None
        for j in range(i+1,len(cuts)):
            a,b=cuts[i][1],cuts[j][0];part=text[a:b]
            if len(compact(part))<10 or not display_lines(part):continue
            rest=solve(j) if j<len(cuts)-1 else (0,[])
            if rest is None:continue
            score=rest[0]-180-abs(len(part)-52)*0.5
            if j<len(cuts)-1:
                if not valid_phrase_cut(part,text[cuts[j][1]:end]):continue
                score+=phrase_score(part,text[cuts[j][1]:end])
            candidate=(score,[(a,b)]+rest[1])
            if best is None or candidate[0]>best[0]:best=candidate
        return best
    result=solve(0)
    if not result:raise ValueError(f'Cannot safely split paragraph {q["paragraph"]}: {text[start:end]}')
    return result[1]


def make_cue(chapter,q,start,end,index):
    events,intervals,placement=native(q['paragraph'])
    a,b=p.spoken_position(q['display_mapping'],start),p.spoken_position(q['display_mapping'],end)
    left,right=len(p.norm(q['spoken_text'][:a])),len(p.norm(q['spoken_text'][:b]))
    touched=[i for i,(x,y) in enumerate(intervals) if x<right and y>left]
    assert intervals[touched[0]][0]==left and intervals[touched[-1]][1]==right
    first,last=touched[0],touched[-1]
    beginning=placement['offset_s']+events[first]['offset']/1e7
    ending=placement['offset_s']+(events[last]['offset']+events[last]['duration'])/1e7
    return {'id':f'C{chapter:02}_P{q["paragraph"]:03}V7Q{index:03}',
        'paragraph':q['paragraph'],'text':q['text'][start:end],'spoken_text':q['spoken_text'][a:b],
        'display_lines':list(display_lines(q['text'][start:end])),
        'start_s':beginning,'end_s':ending,'native_start_s':beginning,'native_end_s':ending,
        'source_start':start,'source_end':end,'first_word_index':first,'last_word_index':last,
        'timing_basis':'actual provider WordBoundary; v7 complete sentence/clause grouping; no interpolation'}


def check_word_timing(ch,c):
    events,intervals,placement=native(c['paragraph'])
    first,last=c['first_word_index'],c['last_word_index']
    a=placement['offset_s']+events[first]['offset']/1e7
    b=placement['offset_s']+(events[last]['offset']+events[last]['duration'])/1e7
    assert abs(c['start_s']-a)<1e-8 and abs(c['native_start_s']-a)<1e-8
    assert abs(c['native_end_s']-b)<1e-8 and c['end_s']<=b+1e-8
    q=paragraph(c['paragraph'])
    assert intervals[first][0]==normalized_position(q,c['source_start'])
    assert intervals[last][1]==normalized_position(q,c['source_end'])


def build():
    assert p.digest(SOURCE)==SOURCE_SHA
    old=p.load(SOURCE)
    assert old['script_sha256']==SCRIPT_SHA==CONTRACT['script_sha256']
    new=copy.deepcopy(old);changes=[]
    for ch in new['chapters']:
        original=copy.deepcopy(ch['cues']);cues=[]
        for placement in ch['paragraphs']:
            q=paragraph(placement['paragraph']);spans=[]
            for a,b in sentence_spans(q):spans+=split_sentence(q,a,b)
            for i,(a,b) in enumerate(spans,1):
                c=make_cue(ch['chapter'],q,a,b,i)
                matches=[x for x in original if x['paragraph']==q['paragraph'] and x['source_start']==a and x['source_end']==b]
                if matches:c={**matches[0],'display_lines':c['display_lines']}
                else:
                    before=[x for x in original if x['paragraph']==q['paragraph'] and x['source_start']<b and x['source_end']>a]
                    c['source_v6_cue_ids']=[x['id'] for x in before]
                    changes.append({'chapter':ch['chapter'],'paragraph':q['paragraph'],
                        'before':[{k:x[k] for k in ('id','text','spoken_text','source_start','source_end','start_s','end_s')} for x in before],
                        'after':copy.deepcopy(c)})
                cues.append(c)
        for c,following in zip(cues,cues[1:]):
            c['end_s']=min(c['native_end_s'],following['start_s'])
        ch['cues']=cues
    new['caption_revision']='caption-v7'
    new['caption_renderer_contract']='editor/private-production-v3/caption_renderer_contract.json'
    new['caption_scope']='caption grouping/display_lines only; v6 script, audio, paragraph/chapter anchors frozen'
    final_cues={c['id']:c for ch in new['chapters'] for c in ch['cues']}
    for change in changes:change['after']=copy.deepcopy(final_cues[change['after']['id']])
    return new,changes


def validate(new):
    old=p.load(SOURCE)
    root=SIDE/'final_timing.json'
    assert p.digest(root)==SOURCE_SHA,'Common root is no longer frozen v6; do not overwrite or accept silently'
    assert p.digest(EP/'outputs/script-final-v6/script_v6.md')==SCRIPT_SHA
    audio=[];paragraphs=[];cue_audit=[]
    ids=set()
    for a,b in zip(old['chapters'],new['chapters']):
        assert {k:v for k,v in a.items() if k!='cues'}=={k:v for k,v in b.items() if k!='cues'}
        path=p.ROOT/b['audio_file']
        actual=p.digest(path)
        assert actual==a['audio_sha256']==b['audio_sha256']
        audio.append({'chapter':b['chapter'],'audio_file':b['audio_file'],'sha256':actual,'total_seconds':b['total_seconds'],'unchanged':True})
        previous=0
        for c in b['cues']:
            assert c['id'] not in ids;ids.add(c['id'])
            assert not is_short(c)
            assert len(c['display_lines']) in (1,2)
            assert ' '.join(' '.join(c['display_lines']).split())==' '.join(c['text'].split())
            assert all(width_ceiling(line)<=1600 for line in c['display_lines'])
            if len(c['display_lines'])==2:assert valid_phrase_cut(*c['display_lines'])
            assert previous-1e-8<=c['start_s']<c['end_s']<=b['total_seconds']
            previous=c['end_s'];check_word_timing(b,c)
            cue_audit.append({'id':c['id'],'paragraph':c['paragraph'],'text':c['text'],
                'display_lines':c['display_lines'],'unit':'sentence' if re.search(r'[.!?。！？]$',c['text']) else 'clause',
                'orphan_predicate':False,'actual_word_boundary':True,
                'max_conservative_line_width_px':max(map(width_ceiling,c['display_lines']))})
        for placement in b['paragraphs']:
            number=placement['paragraph'];q=paragraph(number)
            cues=[c for c in b['cues'] if c['paragraph']==number]
            for key in ('text','spoken_text'):assert compact(''.join(c[key] for c in cues))==compact(q[key])
            event_indices=[i for c in cues for i in range(c['first_word_index'],c['last_word_index']+1)]
            assert event_indices==list(range(len(native(number)[0]))),'Native word loss/duplication'
            for match in p.TOKEN.finditer(q['text']):
                assert sum(c['source_start']<=match.start() and c['source_end']>=match.end() for c in cues)==1
            cursor=0
            for c in cues:
                assert not q['text'][cursor:c['source_start']].strip()
                assert q['text'][c['source_start']:c['source_end']]==c['text']
                cursor=c['source_end']
            assert not q['text'][cursor:].strip()
            paragraphs.append({'paragraph':number,'source_and_spoken_exact_whitespace_normalized':True,
                'protected_atoms_intact':True,'word_events_exactly_once':len(event_indices)})
    return {'passed':True,'script_sha256':SCRIPT_SHA,'source_v6_sha256':SOURCE_SHA,
        'root_sha256_before_and_after':p.digest(root),'audio_files_verified':audio,
        'total_seconds':sum(ch['total_seconds'] for ch in new['chapters']),
        'cues':len(cue_audit),'short_cues':0,'native_words':sum(x['word_events_exactly_once'] for x in paragraphs),
        'paragraph_checks':paragraphs,'cue_meaning_audit':cue_audit,
        'meaning_review_scope':'all cue/display-line source text reviewed by Codex; offline text and native metadata only',
        'rendered_glyph_Range_BBox_verified':False,'actual_listening':False,
        'pending_owner':'editor: actual Pretendard Range BBox and new render QA; main: common-state adoption'}


def write(name,value):
    (HERE/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def main():
    new,changes=build()
    checks=validate(new)
    old=p.load(SOURCE)
    mappings=[]
    for old_ch,new_ch in zip(old['chapters'],new['chapters']):
        for c in old_ch['cues']:
            following=[n for n in new_ch['cues'] if n['paragraph']==c['paragraph'] and n['source_start']<c['source_end'] and n['source_end']>c['source_start']]
            mappings.append({'v6_id':c['id'],'v6_text':c['text'],'was_short':is_short(c),
                'v7_ids':[n['id'] for n in following],'v7_texts':[n['text'] for n in following]})
    write('final_timing.json',new)
    write('checks.json',checks)
    write('source_paragraphs.json',{'script_sha256':SCRIPT_SHA,'paragraphs':list(PARAGRAPHS.values())})
    write('change_manifest.json',{'source':str(SOURCE),'source_sha256':SOURCE_SHA,
        'script_sha256':SCRIPT_SHA,'diagnosis':'production_narration.meaning_spans fills 36 characters greedily without sentence-tail lookahead; predicates become independent cues',
        'repair':'complete sentences where two explicit lines fit; longer sentences split into balanced clauses at actual WordBoundary cuts; immutable pronunciation atoms',
        'renderer_contract':str(CONTRACT_PATH),'renderer_contract_sha256':p.digest(CONTRACT_PATH),
        'before_cues':sum(len(ch['cues']) for ch in old['chapters']),
        'after_cues':sum(len(ch['cues']) for ch in new['chapters']),
        'short_before':47,'short_after':sum(is_short(c) for ch in new['chapters'] for c in ch['cues']),
        'audio_revision':new['audio_revision'],'audio_changed':False,'TTS_calls':0,'model_calls':0,'paid_calls':0,
        'line_fit':'conservative 40px per character bound <=1600px; actual Pretendard glyph Range BBox remains editor gate',
        'chapter_diffs':[{'chapter':a['chapter'],'before_cues':len(a['cues']),'after_cues':len(b['cues']),
            'duration_delta_s':b['total_seconds']-a['total_seconds'],'audio_sha256_unchanged':a['audio_sha256']==b['audio_sha256']} for a,b in zip(old['chapters'],new['chapters'])],
        'v6_to_v7_cue_mapping':mappings,'changes':changes,
        'final_timing_sha256':p.digest(HERE/'final_timing.json')})
    rows=['id\tparagraph\tstart_s\tend_s\ttext\tdisplay_lines']
    for ch in new['chapters']:
        for c in ch['cues']:rows.append('\t'.join([c['id'],str(c['paragraph']),str(c['start_s']),str(c['end_s']),c['text'],' / '.join(c['display_lines'])]))
    (HERE/'meaning_audit.tsv').write_text('\n'.join(rows)+'\n',encoding='utf-8')
    write('handoff.json',{'task_id':'narration-caption-v7','status':'caption_only_source_and_timing_checks_passed',
        'input_script_sha256':SCRIPT_SHA,'input_timing':'../final_timing.v6.json',
        'deliverable':'final_timing.json','change_manifest':'change_manifest.json','checks':'checks.json',
        'all_cue_text_audit':'meaning_audit.tsv','exact_original_and_reading_map':'source_paragraphs.json',
        'test_command':'tools/python311/python.exe -B -X utf8 '+str((HERE/'test_caption_v7.py').relative_to(p.ROOT)).replace('\\','/'),
        'cues_before':342,'cues_after':checks['cues'],'short_cues_before':47,'short_cues_after':0,
        'native_words_exactly_once':checks['native_words'],'paragraphs':54,
        'unchanged_audio_chapters':10,'duration_delta_s':0,'body_seconds':checks['total_seconds'],
        'required_narration_errors':[],'TTS_model_paid_calls':0,'actual_listening':False,
        'root_v6_preserved':True,'next_role':'main forwards to editor Carson: use display_lines as explicit lines, preserve font/anchors/audio; run actual Pretendard Range BBox/render QA before adoption',
        'direct_peer_message_tool_available':False,
        'changed_files':['repair_captions.py','test_caption_v7.py','final_timing.json','source_paragraphs.json','change_manifest.json','checks.json','meaning_audit.tsv','handoff.json','tests.log']})
    print(json.dumps({'cues':sum(len(ch['cues']) for ch in new['chapters']),'short_cues':sum(is_short(c) for ch in new['chapters'] for c in ch['cues']),'changed_groups':len(changes)},ensure_ascii=False))


if __name__=='__main__':main()
