"""Prepare two Shorts from complete approved Jun sentence excerpts. Offline only."""
import hashlib,json,math,re,wave
from pathlib import Path
import numpy as np
from PIL import ImageFont

ROOT=Path(__file__).resolve().parents[5]
HERE=Path(__file__).resolve().parent;EP=HERE.parents[1]
OUT=EP/'narration/shorts-jun-v1';OUT.mkdir(exist_ok=True,parents=True)
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(ROOT).as_posix()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
R=44100;FRAME=R//30
prepared=read(EP/'narration/free-tts-v1/prepare-v6/prepared.json')
paras={p['paragraph_id']:p for c in prepared['chapters'] for p in c['paragraphs']}
ledger=read(EP/'narration/jun-production-v1/generation_ledger.json')
receipts={p['paragraph_id']:p for p in ledger['requests']}
auth=read(HERE/'shorts_authorization.json')
assert auth['new_ElevenLabs_credits_cap']==0 and len(receipts)==54
fontpath=EP/'outputs/intro-motion-v1/assets/fonts/Pretendard-Regular.woff2'
try:font=ImageFont.truetype(str(fontpath),54)
except OSError:
    fontpath=Path('C:/Windows/Fonts/malgun.ttf');font=ImageFont.truetype(str(fontpath),54)

def pcm(p):
    with wave.open(str(p),'rb') as w:
        assert (w.getnchannels(),w.getsampwidth(),w.getframerate())==(1,2,R)
        return np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').copy()
def write_wav(p,a):
    with wave.open(str(p),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(R);w.writeframes(a.astype('<i2').tobytes())
def mapped(p,n):
    for span in p['display_mapping']:
        if n==span['source_start']:return span['spoken_start']
        if n==span['source_end']:return span['spoken_end']
        if span['source_start']<n<span['source_end']:
            assert span['kind']=='literal','Split through protected numeric pronunciation span'
            return span['spoken_start']+n-span['source_start']
    raise ValueError(n)
def linebreak(words):
    text=' '.join(words)
    if font.getlength(text)<=680:return [text]
    opts=[]
    for j in range(1,len(words)):
        pair=[' '.join(words[:j]),' '.join(words[j:])];sizes=list(map(font.getlength,pair))
        if max(sizes)<=680:opts.append((abs(sizes[0]-sizes[1]),pair))
    return min(opts,key=lambda x:x[0])[1] if opts else None
def split_captions(p,source_a,source_b,align,cut_start,global_offset):
    tokens=list(re.finditer(r'\S+',p['text'][source_a:source_b]))
    starts=align['character_start_times_seconds'];ends=align['character_end_times_seconds']
    def interval(i,j):
        a=source_a+tokens[i].start();b=source_a+tokens[j-1].end()
        sa,sb=mapped(p,a),mapped(p,b)
        return a,b,min(starts[sa:sb]),max(ends[sa:sb])
    n=len(tokens);dp={n:(0,[])}
    for i in range(n-1,-1,-1):
        opts=[]
        for j in range(i+1,n+1):
            lines=linebreak([t.group() for t in tokens[i:j]])
            if not lines:continue
            a,b,s,e=interval(i,j);d=e-s
            cost=(d-3.2)**2*.4+(30 if d<1.1 else 0)+(12 if d>6 else 0)
            if j<n and not tokens[j-1].group().endswith((',','.','?','!')):cost+=2
            if j-i==1:cost+=30
            if j not in dp:continue
            opts.append((cost+dp[j][0],[(a,b,s,e,lines)]+dp[j][1]))
        assert opts,'No two-line caption layout'
        dp[i]=min(opts,key=lambda x:x[0])
    return [{'text':p['text'][a:b],'display_lines':lines,'source_start':a,'source_end':b,
             'start_s':global_offset+s-cut_start,'end_s':global_offset+e-cut_start,
             'native_start_s':s,'native_end_s':e,'widths_px_at_54':list(map(font.getlength,lines))}
            for a,b,s,e,lines in dp[0][1]]
def stamp(t):
    n=round(t*1000);h,n=divmod(n,3600000);m,n=divmod(n,60000);s,n=divmod(n,1000)
    return f'{h:02}:{m:02}:{s:02},{n:03}'

plans={
 'funnel':{'title':'같은 2억5천만원, 10년 뒤 자산이 갈리는 이유','goal':'조건별 순위가 바뀌는 장면으로 본편 유입',
           'selections':[('C01P01',[0]),('C01P02',[0,1]),('C01P03',[0]),('C08P01',[2]),('C08P02',[1]),('C08P02',[3])]},
 'analysis':{'title':'집값 상승률만으로 비교하면 놓치는 세 가지','goal':'초기 투자금·월 적립금·대출 효과의 구조 요약',
             'selections':[('C08P03',[1,2,3,4,5]),('C04P04',[0,1,2]),('C10P01',[0])]}
}
summary=[]
for name,plan in plans.items():
    dest=OUT/name;dest.mkdir(exist_ok=True);chunks=[np.zeros(round(.12*R),dtype='<i2')]
    cursor=len(chunks[0]);clips=[];cues=[];script=[]
    for index,(pid,wanted) in enumerate(plan['selections'],1):
        p=paras[pid];receipt=receipts[pid]
        assert receipt['status']=='complete'
        base=EP/'narration/jun-production-v1/paragraphs'/pid
        audio=base/'audio.wav';assert sha(audio)==receipt['artifact_sha256'][f'paragraphs/{pid}/audio.wav']
        align=read(base/'alignment.json');assert ''.join(align['characters'])==p['spoken_text']
        sentences=list(re.finditer(r'\S.*?(?:[.!?](?=\s|$)|$)',p['text']))
        assert wanted==list(range(min(wanted),max(wanted)+1))
        a=sentences[wanted[0]].start();b=sentences[wanted[-1]].end()
        sa,sb=mapped(p,a),mapped(p,b)
        source_start=max(0,min(align['character_start_times_seconds'][sa:sb])-.06)
        source_end=max(align['character_end_times_seconds'][sa:sb])+.08
        data=pcm(audio);ia=max(0,math.floor(source_start*R));ib=math.ceil(source_end*R)
        cut=data[ia:min(ib,len(data))].astype(np.float64)
        fade=min(round(.008*R),len(cut)//2)
        cut[:fade]*=np.linspace(0,1,fade);cut[-fade:]*=np.linspace(1,0,fade)
        cut=np.round(cut).astype('<i2')
        if ib>len(data):cut=np.concatenate([cut,np.zeros(ib-len(data),dtype='<i2')])
        offset=cursor/R;actual_start=ia/R
        native=split_captions(p,a,b,align,actual_start,offset)
        for q in native:q.update(id=f'{name.upper()}Q{len(cues)+1:03}',clip=index,paragraph_id=pid);cues.append(q)
        file=dest/f'clip_{index:02}_{pid}.wav';write_wav(file,cut)
        text=p['text'][a:b];script.append(text)
        clips.append({'clip':index,'paragraph_id':pid,'sentence_indices':wanted,'text':text,'spoken_text':p['spoken_text'][sa:sb],
                      'source_start':a,'source_end':b,'spoken_start':sa,'spoken_end':sb,
                      'source_audio':rel(audio),'source_audio_sha256':sha(audio),'provider_request_id':receipt['response_headers']['request-id'],
                      'raw_start_s':actual_start,'raw_end_s':ib/R,'start_s':offset,'end_s':offset+len(cut)/R,
                      'audio':rel(file),'audio_sha256':sha(file),'samples':len(cut),'edit':'complete sentences; 8ms edge fade; native voice speed'})
        chunks.append(cut);cursor+=len(cut)
        gap=round(.16*R);chunks.append(np.zeros(gap,dtype='<i2'));cursor+=gap
    last_speech=max(c['end_s'] for c in cues)
    total=math.ceil(max(cursor,(last_speech+3)*R)/FRAME)*FRAME
    chunks.append(np.zeros(total-cursor,dtype='<i2'));body=np.concatenate(chunks);assert len(body)==total
    file=dest/'narration.wav';write_wav(file,body)
    for q in cues:assert 0<=q['start_s']<q['end_s']<=len(body)/R and max(q['widths_px_at_54'])<=680
    for left,right in zip(cues,cues[1:]):assert left['end_s']<=right['start_s']
    srt='\n'.join(f'{i}\n{stamp(q["start_s"])} --> {stamp(q["end_s"])}\n'+ '\n'.join(q['display_lines'])+'\n' for i,q in enumerate(cues,1))
    (dest/'captions.srt').write_text(srt,encoding='utf8');(dest/'script.txt').write_text('\n\n'.join(script)+'\n',encoding='utf8')
    result={'id':name,'title':plan['title'],'goal':plan['goal'],'status':'local_excerpt_audio_prepared_not_final_video',
            'source_script_sha256':prepared['script_sha256'],'source_main_audio_revision':'jun-production-v1',
            'voice':'Jun / eleven_v4 / native speed0.97','audio':rel(file),'audio_sha256':sha(file),
            'duration_s':len(body)/R,'last_speech_end_s':last_speech,'tail_after_speech_s':len(body)/R-last_speech,
            'clips':clips,'cues':cues,'caption_font_metric':str(fontpath),'caption_metric_size_px':54,'caption_max_width_px':680,
            'new_TTS_calls':0,'new_paid_credits':0,'actual_listening':False,'final_caption_browser_bbox_check':'required after visual build'}
    save(dest/'timing.json',result);summary.append({k:result[k] for k in ['id','title','audio','audio_sha256','duration_s','last_speech_end_s','new_TTS_calls','new_paid_credits']})
save(OUT/'handoff.json',{'status':'completed_local_short_excerpt_preparation','outputs':summary,'originals_preserved':True,
                       'new_paid_TTS_calls':0,'video_render_started':False,'next_owner':'video_director/editor after main completion'})
print(json.dumps(summary,ensure_ascii=False))
