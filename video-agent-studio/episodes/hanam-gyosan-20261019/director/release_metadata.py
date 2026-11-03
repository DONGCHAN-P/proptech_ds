from pathlib import Path
import json
EP=Path(__file__).resolve().parents[1];O=EP/'outputs/release-prep-v1';O.mkdir(parents=True,exist_ok=True)
p=json.loads((EP/'outputs/production-v1/project.json').read_text(encoding='utf8'));sc=json.loads((EP/'writer/scenes_v1.json').read_text(encoding='utf8'))
chap=[]
for s in sc:
 n=next(x['start_frame'] for x in p['visual_intervals']if x['scene_id']==s['scene_id']);sec=n//30;chap.append(f'{sec//60:02}:{sec%60:02} {s["title"]}')
sources=json.loads((EP/'research/sources.json').read_text(encoding='utf8'))
urls=[]
def walk(x):
 if isinstance(x,dict):
  for k,v in x.items():
   if k in ['url','source_url','entry_url'] and isinstance(v,str)and v.startswith('http')and v not in urls:urls.append(v)
   else:walk(v)
 elif isinstance(x,list):
  for v in x:walk(v)
walk(sources)
description='''하남 교산을 일자리·교통·가격·생활시설·공급의 다섯 기준으로 살펴봅니다.
창릉 편과 같은 지도·가격 비교 포맷으로, 중앙 C2·B2의 조건부 관찰 후보와 A2의 공개된 본청약 가격을 구분했습니다.

이 영상은 무료 Microsoft Heami TTS로 만든 비공개 검토본입니다. 새 유료 이미지·TTS·영상 API는 사용하지 않았습니다. 기존 채널의 AI 개념 챕터/브랜드 자산을 재사용했으며 실제 교산 현장 모습과는 구분합니다.

■ 가격 기준
교산 A2: 2025년 본청약 정정 모집공고의 특정51A·59A/5층 이상 기본가+발코니 확장 사례. 다른 옵션·세금 별도. 현재 청약 접수/현재 매매가/교산 전체 평균이 아닙니다.
기존 아파트: 2026.7~9 신고 매매, 전용83㎡ 이상85㎡ 미만,5층 이상, 해제표시 제외, 중개·직거래 포함 중위값. 거래건수는 화면 표기. A2 59㎡와 기존84㎡는 면적·상품이 달라 가격차를 미래차익으로 해석하지 않습니다.

■ 계획 기준
2026.10.08 지구계획5차 고시 및 2026.10.19 확인 자료 기준. 송파하남선2032년은 목표, A2 2029.6은 입주 예정입니다. 역 출입구·개교월 등 미확인은 업데이트 대상입니다. C2/B2는 공식 공급계획을 바탕으로 한 조건부 관찰 후보이며 확정 시세·수익률 순위가 아닙니다.

■ 챕터
'''+ '\n'.join(chap)+'\n\n■ 주요 원문 출처\n'+'\n'.join(urls)+'\n\n지도: LH 공개토지계획, ©OpenStreetMap 기여자/ODbL, SGIS/MIT, KRIC 역정보. 단지대표좌표는 한국부동산원 공개데이터. 자료별 기준시점은 화면 출처와 조사기록을 참고하세요.\n\n#하남교산 #교산신도시 #3기신도시'
d=dict(title='하남 교산, 대장 후보는 어디? C2·B2·A2 분양가·교통·주변 시세 비교',description=description,tags=['하남교산','교산신도시','3기신도시','하남부동산','교산분양가','송파하남선','C2','B2','교산푸르지오더퍼스트','부동산분석'],privacy='private',made_for_kids=False,paid_product_placement=False,language='ko',chapters=chap,source_urls=urls)
(O/'metadata.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8');print('private metadata ready; title chars',len(d['title']),'description chars',len(description))
