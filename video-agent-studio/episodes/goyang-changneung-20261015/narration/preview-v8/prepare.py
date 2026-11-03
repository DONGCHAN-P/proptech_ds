import pathlib,re,json,hashlib
root=pathlib.Path(__file__).resolve().parents[2]
out=root/'narration/preview-v8'
script=root/'outputs/script-review-v8/script_v8.md'
text=script.read_text(encoding='utf-8-sig')
parts=re.findall(r'^## (M\d+) · ([^\n]+)\n+### 낭독\n+(.*?)\n+### 화면 지시',text,re.M|re.S)
replacements={'GTX-A':'지티엑스 에이','MBC':'엠비씨','LG':'엘지','LH':'엘에이치','LX':'엘엑스','S-클래스':'에스 클래스','S1':'에스 원','S3':'에스 쓰리','S4':'에스 포','S5':'에스 파이브','S6':'에스 식스','㎡':'제곱미터'}
packet_path=root/'writer/revision-v8/narration_packet.json'
packet=json.loads(packet_path.read_text(encoding='utf-8-sig'))
assert hashlib.sha256(script.read_bytes()).hexdigest()=='6ffc9fc4819460d4cf6f03fd3b28102e2864402b9965ca14e158230474963982'
assert [(a,re.sub(r'\s+','',c)) for a,b,c in parts]==[(s['scene_id'],re.sub(r'\s+','',s['text'])) for s in packet['scenes']]
replacements.update(packet['pronunciations'])
replacements['DMC']='디엠씨'
units=[]
for scene,title,body in parts:
    sentences=re.split(r'(?<=[.?!])\s+',body.strip())
    for sentence in sentences:
        chunks=re.split(r'(?<=,)\s+|(?<=입니다.)\s+',sentence) if len(sentence)>110 else [sentence]
        for chunk in chunks:
            spoken=chunk
            for a,b in sorted(replacements.items(),key=lambda x:-len(x[0])): spoken=spoken.replace(a,b)
            units.append(dict(scene_id=scene,title=title,text=chunk,spoken_text=spoken,file=f'{scene}_{sum(u["scene_id"]==scene for u in units)+1:03}.wav'))
(out/'units.json').write_text(json.dumps(units,ensure_ascii=False,indent=2),encoding='utf-8')
(out/'input_hashes.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [script,packet_path]},indent=2),encoding='utf-8')
(out/'pronunciation.json').write_text(json.dumps(replacements,ensure_ascii=False,indent=2),encoding='utf-8')
print(len(parts),'scenes',len(units),'units',sum(len(u['text']) for u in units),'characters')
