from pathlib import Path
import json,hashlib
E=Path(__file__).resolve().parents[1];R=E.parents[2];O=E/'outputs/release-prep-v5-jun';O.mkdir(exist_ok=True)
old=json.loads((E/'outputs/release-prep-v1/upload_job.json').read_text(encoding='utf8'))
description='''하남 교산의 대장 후보는 어디일까요? C2·B2·A2를 토지이용계획도 위에서 비교합니다.
일자리·교통·분양가·생활시설·공급과 주변 실거래를 연결해 주거·투자 가치를 살펴봅니다.
자족5 AI 혁신클러스터 참여계획과 사업기간, 자족7 산업단지 지정 추진, 주변 상업·업무 계획도 함께 정리했습니다.

이전 편
남양주 왕숙 https://youtu.be/T_GBxTRgRSc
고양 창릉 https://youtu.be/eLF3-1ZaraQ

가격·자료 기준
• A2는 2025년 본청약 정정 공고의 51A·59A, 5층 이상 기본가와 발코니 확장비 사례입니다. 다른 옵션·세금은 별도입니다.
• 기존 아파트는 2026년 7~9월 계약분, 전용 83㎡ 이상 85㎡ 미만·5층 이상·해제표시 제외·중개/직거래 포함 실거래 중위값입니다. 거래건수를 함께 표시했습니다.
• 교산 59㎡와 기존 84㎡는 면적·상품 조건이 다르므로 같은 예산의 주거 선택지로 비교했습니다.
• 주택계획은 2026.10.08 고시 기준, 신규 기업·시설 계획은 2026.10.20 확인 기준입니다. 참여계획·지정 추진·사업기간·입주 예정·철도 목표를 구분했습니다.
• 후보 분석은 공개된 입지와 가격 조건에 근거하며, 미래 가격·수익률 보장을 의미하지 않습니다.

주요 자료
A2 정정 모집공고 https://www.prugio.com/hb/2025/gyosan/
토지이용계획·도형: LH 내집어디 https://wherehome.lh.or.kr/
실거래: 국토교통부 https://rt.molit.go.kr/
하남시 AI 클러스터 참여계획 https://www.hanam.go.kr/sosik/selectBbsNttView.do?bbsNo=1164&key=10048&nttNo=495607
사업기간·캠프콜번 개발계획 https://www.hanam.go.kr/cleanh/cleanhBbsNttWebView.do?key=8364&nttNo=3495
자족7 추진: 하남시의회 2026.07.16 회의록 https://council.hanam.go.kr/minutes/svc/web/cms/mnts/SvcMntsViewer.php?schSn=3208
스타필드 하남 공식 주소 https://www.starfield.co.kr/hanam/main.do
지도: © OpenStreetMap contributors / ODbL https://www.openstreetmap.org/copyright
시설 주소 대표점: VWorld 주소 API. 사업경계·출입구·계산된 도보 경로와 구분했습니다.

ElevenLabs Jun AI 음성을 사용했습니다. 썸네일·챕터·브랜드의 AI 개념 이미지는 실제 교산 현장이나 공식 조감도와 구분합니다.

#하남교산 #교산신도시 #3기신도시 #교산분양가 #대장아파트
'''
(O/'description_draft.txt').write_text(description,encoding='utf8')
draft={'status':'metadata_draft_pending_final_timing_and_artifact_gates','title':old['title'],'description':description,'tags':old['tags'],'privacy':'private','channel_id':old['channel_id'],'thumbnail':old['thumbnail'],'thumbnail_sha256':old['thumbnail_sha256'],'no_schedule':True,'retain_previous_private_video':True,'previous_video_id':'aeuQbsbRnEY','script_sha256':hashlib.sha256((E/'outputs/script-review-v5/script_v5.md').read_bytes()).hexdigest()}
(O/'metadata_draft.json').write_text(json.dumps(draft,ensure_ascii=False,indent=2),encoding='utf8')
assert len(description.encode('utf8'))<4500
print(json.dumps({'draft_ready':True,'description_bytes':len(description.encode('utf8')),'privacy':'private','uploaded':False}))
