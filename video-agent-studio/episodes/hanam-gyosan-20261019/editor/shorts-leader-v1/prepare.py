import pathlib,json,wave,hashlib,re
E=pathlib.Path(__file__).resolve().parent;EP=E.parents[1];ROOT=EP.parents[2];O=EP/'outputs/shorts-leader-v1';P=E/'public';P.mkdir(exist_ok=True)
def load(p):return json.loads(p.read_text(encoding='utf8'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
tim=load(EP/'outputs/production-v5-jun/timing_locked.json');ids=[212,213,218,219,221,222,223,224,225,226]
units=[tim['audio_units'][i] for i in ids];al=load(EP/'narration/jun-v5-final/M008.alignment.json')
groups=[['교산에서 가격을 이끌','후보를 고를 때 먼저 볼 곳은,'],['새 철도와 주요 상업·생활시설을','함께 이용할 수 있는 지역입니다.'],['그래서 오늘은 중앙 권역의 C2를','큰 평형 민간분양의','우선 관찰 후보로 두겠습니다.'],['C2는 최신 고시에서','전용 85㎡ 초과 민간분양','786호로 계획되어 있습니다.'],['중심 기능과 연결되는','큰 집을 찾는 수요라는 관점에서','먼저 볼 후보입니다.'],['중형 면적의 민간분양 대안으로는','B2를 함께 보겠습니다.'],['B2는 전용 60㎡에서 85㎡ 구간의','민간분양 281호가','계획되어 있습니다.'],['C2와 B2는 앞으로','민간분양이 계획된 후보입니다.'],['실제 분양가와 면적 구성,'],['역 출입구까지의 이동 경로가','공개되면 두 단지를 비교하겠습니다.']]
w=wave.open(str(EP/'outputs/production-v5-jun/audio/M008.wav'),'rb');par=w.getparams();sr=w.getframerate();stride=par.nchannels*par.sampwidth;raw=w.readframes(w.getnframes());buf=bytearray();caps=[];clips=[]
for i,(u,gs) in enumerate(zip(units,groups)):
 a=max(0,round((u['scene_local_start_s']-.025)*sr));b=round((u['scene_local_end_s']+.025)*sr);st=len(buf)/stride/sr;buf.extend(raw[a*stride:b*stride]);dur=(b-a)/sr
 for g in gs:
  idx=''.join(al['characters']).find(g,u['source_character_start'],u['source_character_end_exclusive'])
  assert idx>=0,g
  caps.append({'start':st+al['character_start_times_seconds'][idx]-a/sr,'end':st+al['character_end_times_seconds'][idx+len(g)-1]-a/sr,'text':g,'unit_id':u['unit_id']})
 clips.append(dict(u,start=st,end=st+dur,source_sample_start=a,source_sample_end=b,mode=i));buf.extend(bytes(round(.12*sr)*stride))
buf.extend(bytes(round(3*sr)*stride));duration=len(buf)/stride/sr
with wave.open(str(P/'voice.wav'),'wb') as z:z.setparams(par);z.writeframes(buf)
geo=load(ROOT/'video/src/gyosan-production-v1/data.json');r3=load(ROOT/'video/src/gyosan-production-v1/data_r3.json')
save(E/'data.json',dict(clips=clips,captions=caps,duration=duration,features=geo['features'],details=r3['details']))
save(E/'clip_plan.json',dict(title='3기 신도시 하남 교산의 대장단지는 어디가 될까?',duration=duration,clips=clips,source_video=str(EP/'outputs/production-v5-jun/gyosan_v5_jun.mp4'),source_sha256='13abf7fc0b873036ad72c0b578251cb08e64ef514ecfe09fa636e26905ed214e',new_paid_calls=0,disclosure='Official plan polygons and existing Jun PCM slices; no new AI media; candidate interpretation conditional'))
def ts(t):
 m=round(t*1000);return f'{m//3600000:02}:{m//60000%60:02}:{m//1000%60:02},{m%1000:03}'
(O/'gyosan_leader_short_v1.srt').write_text('\n\n'.join(f'{i+1}\n{ts(c["start"])} --> {ts(c["end"])}\n{c["text"]}' for i,c in enumerate(caps)),encoding='utf8')
(O/'script_excerpt.md').write_text('# 3기 신도시 하남 교산의 대장단지는 어디가 될까?\n\n기존 Jun 본편 낭독 원문 발췌. 새 음성·유료 생성 없음.\n\n'+'\n\n'.join(u['text'] for u in units)+'\n\n무음 마무리: 지도·교통·분양가 전체 비교는 본편에서 확인하세요.\n',encoding='utf8')
save(E/'input_manifest.json',{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [EP/'outputs/production-v5-jun/audio/M008.wav',EP/'narration/jun-v5-final/M008.alignment.json',EP/'outputs/production-v5-jun/timing_locked.json',ROOT/'video/src/gyosan-production-v1/data.json',ROOT/'video/src/gyosan-production-v1/data_r3.json']})
print(json.dumps(dict(duration=duration,clips=len(clips),captions=len(caps))))
s=(E/'entry.tsx').read_text(encoding='utf8').replace("txt('dummy','',0,0,1)",'null').replace('280,800,62','328,875,62').replace('625,660,62','738,700,62');(E/'entry.tsx').write_text(s,encoding='utf8')
m=(ROOT/'video-agent-studio/episodes/goyang-changneung-20261015/editor/shorts-leader-v1/measure.cjs').read_text(encoding='utf8')
m=m.replace("path.join(root,'video/src/changneung-shorts-leader-v1')",'__dirname').replace("n==='react'","n.endsWith('/react')||n==='react'").replace("n==='remotion'","n.endsWith('/remotion')||n==='remotion'").replace('safe_rect:[156,448,816,1160]','safe_rect:[140,260,840,1360]').replace('1340','1490')
(E/'measure.cjs').write_text(m,encoding='utf8')
