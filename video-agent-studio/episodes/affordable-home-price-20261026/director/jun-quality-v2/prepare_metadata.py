from pathlib import Path
import json
EP=Path(__file__).resolve().parents[2];ROOT=EP.parents[2]
OUT=EP/'outputs/jun-quality-v2/release';OUT.mkdir(parents=True,exist_ok=True)
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sch=read(EP/'editor/jun-quality-v2/main/schedule.json')
facts=read(EP/'research/jun-user-script-v1/reviewed_claims.json')
title=read(EP/'outputs/jun-quality-v2/thumbnail/metadata.json')['title']
intro='현금 1억부터 5억까지 모았다면, 어느 가격대의 집을 찾아보면 좋을까요?\n내 돈에서 준비금을 남기고, 대출 조건과 매달 갚을 돈까지 연결해 계산합니다. 집값 예산이 크게 늘어나는 구간과 개인 대출한도에 멈추는 구간, 현금이 같아도 월 부담을 줄이는 선택을 함께 살펴봅니다.'
conditions='계산 조건\n사례 LTV 70%, 집값과 담보평가액 동일, 기존 대출 0, 개인 소득·심사에 따른 대출한도 4억원, 연 4.5%·30년 원리금균등. 준비금은 현금 1~5억원에 각각 2000만~6000만원을 배정했습니다. 지역·상품·은행의 추가 제한이 예시 계산을 더 제한하지 않는 조건입니다.\n실제 구입 예산은 잔금일 현금·개별 견적·해당 주택의 대출 조건과 월 생활비를 넣어 다시 계산합니다. 정책 설명 기준은 2026년 10월 26일입니다.'
chapters=[]
for p in sch['placements']:
    if p['kind']!='chapter':continue
    sec=int(p['start']);chapters.append(f'{sec//60:02}:{sec%60:02} {p["asset"]["title"]}')
sources={s['source_id']:s for s in facts['sources']}
selected=['LTV2026','LTV','DSR','POLICY2026OCT','TAX11','TAX151','BROKER']
links='근거 자료\n'+'\n'.join(sources[k]['title']+'\n'+sources[k]['url'].replace('\\u0026','&') for k in selected)
music=(EP/'outputs/jun-user-script-v1/full-film-v1/music_credits.txt').read_text(encoding='utf-8-sig')
desc='\n\n'.join([intro,conditions,'챕터\n'+'\n'.join(chapters),links,music.strip(),'#내집마련 #주택담보대출 #집값예산'])
assert len(title)<=100 and len(desc.encode('utf-8'))<=5000
metadata={'channel_id':'UCr_mTC0x_Uobv6MrIsOkrXw','privacy':'private','title':title,'description':desc,'tags':['내집마련','주택담보대출','LTV','DSR','주택구입예산'],'category_id':'27','made_for_kids':False,'contains_synthetic_media':True,'notify_subscribers':False,'publish_at':None,'uploaded':False}
(OUT/'main_metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(OUT/'description.txt').write_text(desc+'\n',encoding='utf-8')
shorts=read(EP/'outputs/jun-quality-v2/shorts/publishing_metadata.json')
shorts['shorts'][0]['description']=shorts['shorts'][0]['description'].replace('기존 Jun 내레이션을 사용한 홍보형 쇼츠입니다.','').replace('  ',' ')
(OUT/'shorts_metadata.json').write_text(json.dumps(shorts,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'title_characters':len(title),'description_utf8_bytes':len(desc.encode('utf-8')),'chapters':chapters,'visibility':'private'},ensure_ascii=False))
