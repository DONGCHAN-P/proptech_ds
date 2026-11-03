from pathlib import Path
import json, re, hashlib

p=Path(__file__).resolve().parents[1]
f=p/'writer/script_v1.md'
s=f.read_text(encoding='utf-8')
repls={'6억1천437만원':'6억1천400만원','6억5천873만원':'6억5천900만원','6억8천864만원':'6억8천900만원','7억3천140만원':'7억3천100만원','1억6천660만원':'1억6천700만원','2억8천362만원':'2억8천400만원','4억5천873만원':'4억5천900만원','6억864만원':'6억900만원','7천427만원':'7천400만원','2천991만원':'3천만원','7억3천952만원':'7억4천만원','5억6천249만원':'5억6천200만원','5억3천573만원':'5억3천600만원','5억178만원':'5억200만원','7억1천707만원':'7억1천700만원','7억8천409만원':'7억8천400만원','7억1천289만원':'7억1천300만원','5억2천529만원':'5억2천500만원','6억9천802만원':'6억9천800만원','5억9천353만원':'5억9천400만원','6억1천24만원':'6억1천만원','6억4천865만원':'6억4천900만원','171만9천원':'172만원','201만9천원':'202만원','98만1천원':'98만원','66만7천원':'67만원','71만7천원':'72만원','228만3천원':'228만원','6만7천원':'7만원','111만7천원':'112만원','188만3천원':'188만원','51만9천원':'52만원','3억5천948만원':'3억5천950만원','7천638만원':'7천600만원'}
for a,b in repls.items(): s=s.replace(a,b)
s=s.replace('월 30만원과 5만원은 설명을 위한 비용 묶음입니다.','월 30만원과 5만원은 설명을 위한 비용 묶음이며, 두 가구의 차이는 25만원입니다.')
s=s.replace('달러 기준 총수익을 원화로 바꿀 때는 달러 수익과 원·달러 환율 변화를 곱해서 계산합니다.','달러 자산이 10% 오르고 원·달러 환율도 10% 오르면, 원화 자산은 1.1배에 1.1배를 곱한 1.21배가 됩니다. 원화 수익률은 원금을 제외한 21%입니다.')
addition='월세 수준만 바꿔도 결과가 달라집니다. 같은 보증금에서 월세를 100만원 대신 120만원으로 높이면 월세 가구의 순자산은 약 6억5천600만원으로 줄어, 전세의 약 6억5천900만원보다 작아집니다. 실제 같은 집에서 가능한 계약 조건인지는 시장 자료로 확인해야 하며, 이 비교는 임대료 가정의 영향을 보여줍니다.\n\n'
if addition not in s: s=s.replace('금리도 경계를 움직입니다.',addition+'금리도 경계를 움직입니다.')
f.write_text(s,encoding='utf-8')
b=p/'writer/visual_storyboard.md';t=b.read_text(encoding='utf-8').replace('달러총수익×환율비율→원화','(1+달러총수익률)×(기말원/달러÷기초원/달러)−1=원화수익률; +10%/+10%→+21%')
t=t.replace('8장 3~5문단','8장 3~6문단').replace('월세대출4%는 고정 회색.','월세100→120만원만 바꾼 별도 보조차트에 6.5615억/전세6.5873억을 표시. 월세대출4%는 고정 회색.')
b.write_text(t,encoding='utf-8')
d=p/'director/claude-story-v1';packet=json.loads((d/'packet.json').read_text(encoding='utf-8'));packet['revised_script']=s;packet['changes']='Rounded narration amounts; rent 1.0M to 1.2M KRW changes rentNW to 656150200 versus jeonse 658732600; owner30/tenant5 difference25 in ten-thousand KRW units; FX example +10% and +10% ->+21%.'
(d/'packet.json').write_text(json.dumps(packet,ensure_ascii=False,indent=2),encoding='utf-8')
run=d/'run.cjs';r=run.read_text(encoding='utf-8');a=r.index('const prompt=');z=r.index('\nfs.writeFileSync',a)
r=r[:a]+"const prompt='한국어 비평입니다. 단순 요약 금지. 허용 packet.json의 revised_script와 key_questions만 검토하고 각 질문에 동의/수정필요/판단불가 및 이유를 답하세요. 1차 Claude가 비평 대신 요약하고 독립QA 미수행이라는 낡은 내용을 반복했습니다. 이를 교정하세요. 핵심 오류 없으면 없다고 하되 시장임대료 적합성/세금/대출가능성 미검증의 제한적 합의인지 밝히세요. 원금/보증금/기회비용/환율중복과 편향을 실제로 비판하세요. 700단어 이내, 다른파일/검색금지. 파일: '+path.join(dir,'packet.json');"+r[z:]
run.write_text(r,encoding='utf-8')
text=''.join(x for x in s.splitlines() if x and not x.startswith('#') and not x.startswith('버전:') and not x.startswith('낭독 분량'))
print(json.dumps({'narration_chars':len(text),'script_sha256':hashlib.sha256(f.read_bytes()).hexdigest()},ensure_ascii=False))
