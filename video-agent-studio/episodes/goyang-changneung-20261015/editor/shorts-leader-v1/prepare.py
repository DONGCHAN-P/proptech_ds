import json,pathlib,wave,hashlib,shutil,re,math
R=pathlib.Path.cwd(); ep=R/'video-agent-studio/episodes/goyang-changneung-20261015'; ed=ep/'editor/shorts-leader-v1'; out=ep/'outputs/shorts-leader-v1'; src=R/'video/src/changneung-shorts-leader-v1'; pub=ed/'public';pub.mkdir(exist_ok=True)
def load(p):return json.loads(p.read_text(encoding='utf8'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
ids=[2,3,6,9,10,11,14,15]; units=[x for x in load(ep/'narration/jun-v8-final/segments.json') if x['unit_id'] in [f'M009_{i:03}' for i in ids]]
al=load(ep/'narration/jun-v8-final/M009.alignment.json');print('alignment',list(al))
w=wave.open(str(ep/'outputs/production-v8-jun/audio/M009.wav'),'rb');rate=w.getframerate();params=w.getparams();raw=w.readframes(w.getnframes());stride=params.nchannels*params.sampwidth
buf=bytearray(); cursor=0; clips=[];caps=[]
for n,u in enumerate(units):
 a=max(0,round((u['scene_local_start_s']-.035)*rate));b=round((u['scene_local_end_s']+.035)*rate);dur=(b-a)/rate;start=cursor/rate
 buf.extend(raw[a*stride:b*stride]);pad=round(.15*rate);buf.extend(bytes(pad*stride));cursor+=b-a+pad
 # Display exact written semantic phrase groups, aligned to original character span proportion when spoken aliases differ.
 text=u['text'];manual={2:['현재 자료로 대장 후보를 먼저 고르라면','저는 S4부터 보겠습니다.'],3:['기존 원흥 생활권의 수요와','만나는 접점이 있고,','1,024세대 규모의','새 단지가 들어서는 후보입니다.'],6:['다만 S4는 비교한 공고가격도','가장 높았습니다.'],9:['그래서 S4는 가격수준을 이끌','후보로 먼저 보는 것이고,','세 후보 중 상승률이 가장 높다는','결론은 아닙니다.'],10:['가격 부담과 도시가 채워지는','여력을 같이 보면','S5가 경쟁 후보입니다.'],11:['공고 사례가 가장 낮고,','세 곳 중 입주 예정이 빨라','먼저 수요를 만날 수 있습니다.'],14:['S1은 관찰 후보로 두겠습니다.'],15:['공고가격은 S5와 가깝고,','이번 현재 경로 조회에서는','상암 쪽 연결이 상대적으로 짧았습니다.']};groups=manual[int(u['unit_id'][-3:])]
 total=sum(len(g) for g in groups);pos=0
 for g in groups:
  idx=''.join(al['characters']).find(g,u['source_character_start'],u['source_character_end_exclusive']);cs=start+al['character_start_times_seconds'][idx]-a/rate;ce=start+al['character_end_times_seconds'][idx+len(g)-1]-a/rate;pos+=len(g);caps.append({'start':cs,'end':ce,'text':g,'unit_id':u['unit_id']})
 clips.append(dict(u,clip_start=start,clip_end=start+dur,source_sample_start=a,source_sample_end=b,mode=n))
buf.extend(bytes(round(3*rate)*stride));duration=len(buf)/stride/rate
with wave.open(str(pub/'voice.wav'),'wb') as z:z.setparams(params);z.writeframes(buf)
geo=load(R/'video/src/changneung-v5/data.json');work=load(R/'video/src/changneung-v6/data.json')
save(src/'data.json',{'clips':clips,'captions':caps,'duration':duration,'geo':geo['blocks'],'work':work})
save(ed/'clip_plan.json',{'title':'3기 신도시 창릉의 대장단지는 어디가 될까?','status':'local_review_unapproved_new_cut','duration':duration,'units':clips,'audio':'unaltered PCM slices with 35ms handles; 150ms silence between units; no speed change','new_paid_calls':0})
for id in ['S-4','S-5','S-1']:
 p=ep/f'editor/production-v8-labels/public/changneung-v5/plan_geometry/{id}_detail.svg'
 shutil.copy2(p,pub/f'{id}.svg')
shutil.copy2(ep/'editor/production-v8-labels/public/changneung-v5/workplace_basemap.svg',pub/'workplace.svg')
def st(t):
 ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
(out/'changneung_leader_short_v1.srt').write_text('\n\n'.join(f"{i+1}\n{st(x['start'])} --> {st(x['end'])}\n{x['text']}" for i,x in enumerate(caps)),encoding='utf8')
print('duration',duration,'caps',len(caps))
