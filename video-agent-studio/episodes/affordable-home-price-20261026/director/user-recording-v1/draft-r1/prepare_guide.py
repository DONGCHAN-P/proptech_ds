"""Freeze the user-authored DOCX and build a local, untimed production guide pack."""
from pathlib import Path
import hashlib
import json
import shutil
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

ROOT = Path(__file__).resolve().parents[5]
PACK = Path(__file__).resolve().parent
EP = PACK.parents[1]
EXPECTED_SHA = "f28deb75e0a271e30e3d29dbe52291ef30e28b0ef0bfc2648ad98bbd652e6a73"
SOURCE = Path.home() / "Downloads" / "현금_1억부터_5억까지_내집마련_유튜브_대본.docx"
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

# One design scene may have several successive visual states. Paragraph numbers
# refer to direct body paragraphs in the frozen DOCX, including empty paragraphs.
# Every literal anchor is checked against the assigned user-authored paragraphs.
SCENES = [
    ("S01", 1, [7], "첫 1억 다음의 질문", "현금 단계", [("일단 1억부터 모아라", "현금 1억 한 칸"), ("2억, 5억, 10억", "현금 눈금을 추가하고 집값 결과는 미노출")], "M01", ["DOC"], "동일 눈금의 현금 토큰을 코드로 제작"),
    ("S02", 1, [8], "통장과 매물 가격 연결", "집·가격 비교", [("그래서 이 돈으로 무슨 집을 살 수 있는데?", "통장 잔액과 집 세 개를 분리"), ("6억, 10억, 15억", "가격별 매물 모형에 금액 표시")], "M02", ["DOC"], "실제 앱 화면을 쓰지 않고 집 실루엣과 가격으로 제작"),
    ("S03", 1, [9, 10, 11], "오늘 계산의 범위", "자금 분해", [("갚아야 할 돈이 같이 늘어나는", "주택가격 막대를 자기자금·대출로 분리"), ("집값에 들어가는 돈", "집값 투입금→준비금→월 상환액의 세 영역"), ("소득과 기존 대출", "현금·대출조건·월 여력 조건행")], "M03", ["DOC", "CALC"], "세 영역을 도형으로 설명하며 긴 면책 문구는 추가하지 않음"),
    ("S04", 2, [14], "잔금일의 현금", "가로 자금 달력", [("잔금일에 실제로 쓸 수 있는 현금", "잔금일 세로 기준선"), ("전세보증금을 돌려받아야", "보증금 반환일과 잔금일을 연결")], "M04", ["DOC"], "개인 계좌나 실제 개인정보 없이 날짜 기호로 제작"),
    ("S05", 2, [15], "집값 밖의 거래비용", "영수증 분해", [("취득세와 지방교육세", "취득세·교육세 행"), ("중개보수", "중개보수 행"), ("법무사 비용이나 국민주택채권 할인 부담, 인지세", "등기 관련 항목을 한 행씩 표시")], "M05", ["DOC", "TAX", "BROKER", "BOND"], "실제 견적서 대신 항목별 영수증 모션"),
    ("S06", 2, [16, 17], "생활에 남길 돈", "집 내부·생활 소품", [("이사비, 도배나 수리비", "이삿짐·벽지·수리 도구"), ("가전과 가구", "생활 소품을 교체"), ("비상금도 별도로", "비상금 영역을 집값 영역 밖에 보존")], "M06", ["DOC"], "보행 인물 없이 공간과 소품 조각으로 제작"),
    ("S07", 2, [18, 19], "다섯 준비금", "현금 분리 막대", [("현금 1억이면 2천만 원", "1억−2000만원→8000만원"), ("2억이면 3천만 원", "2억−3000만원→1억7000만원"), ("5억이면 6천만 원", "3·4·5억의 나머지 행 완성"), ("준비금을 제외한 돈만 집값에", "주택 투입금 0.8·1.7·2.6·3.5·4.4억만 남김")], "M07", ["DOC", "CALC"], "금액을 실제 길이에 맞춘 가로 막대로 제작"),
    ("S08", 3, [22, 23], "LTV의 분모", "담보 분할 막대", [("집의 담보가치를 기준", "집값=담보평가액 5억"), ("3억 5천만 원", "70% 대출 영역"), ("1억 5천만 원", "30% 자기자금 영역")], "M08", ["DOC", "FSC_LTV", "CALC"], "고정 담보 막대 70:30 분할로 제작"),
    ("S09", 3, [24, 25], "DSR과 기존 빚", "연 소득·상환 예산", [("1년에 갚는 대출 원금과 이자", "연 소득과 연 상환액의 범위 비교"), ("기존 신용대출", "기존 빚 상환액이 가용 범위를 차지"), ("대출한도는 줄어듭니다", "새 주담대 공간 축소")], "M09", ["DOC", "FSC_LTV"], "특정 소득·승인금액을 추가 가정하지 않는 비율 도식"),
    ("S10", 3, [26], "심사와 실제 납부", "금리 두 경로", [("금리가 올라갈 상황", "심사용 금리의 여유 공간"), ("실제 이자로 청구", "실제 납부액 경로와 심사 경로를 나란히 구분")], "M10", ["DOC", "STRESS"], "심사용 금리 수치를 임의로 덧붙이지 않는 구조 도식"),
    ("S11", 3, [27], "조건별 LTV", "기준표의 해당 행", [("비규제지역은 70퍼센트", "일반 차주 비규제 70% 행"), ("규제지역은 40퍼센트", "일반 차주 규제 40% 행"), ("생애최초 구입자는 별도 조건", "생애최초를 별도 가지로 분리")], "M11", ["DOC", "FSC_LTV"], "공식 표를 출처로 삼은 큰 글씨 재작성 표"),
    ("S12", 3, [28, 29], "이후 사례의 공통 조건", "대출 한도 게이트", [("LTV 70퍼센트", "LTV 게이트 70%"), ("최대 4억 원", "사례 개인 한도 4억 게이트"), ("연 4.5퍼센트, 30년 원리금균등", "월 원리금 계산 조건 고정")], "M12", ["DOC", "CALC"], "LTV·개인한도·월납부 조건을 한 문장씩 구성"),
    ("S13", 4, [32, 33], "현금 1억의 가격", "현금→가격 계산", [("준비금 2천만 원", "1억에서 2000만원 분리"), ("8천만 원", "집값 투입 8000만원"), ("30퍼센트로 나누면", "8000만원÷30%"), ("2억 6천6백만 원짜리", "집값 2억6600만원 결과")], "M13", ["DOC", "CALC"], "워터폴에서 70:30 막대로 이어지는 실제 수치 모션"),
    ("S14", 4, [34, 35], "대출과 월 부담", "구입자금·월 청구서", [("대출 1억 8천6백만 원", "8000만+1억8600만=2억6600만"), ("월 원리금은 약 94만 원", "월 청구서 94만원"), ("지역의 범위를 넓히거나 면적을 줄여볼지", "탐색 범위·면적·추가저축 선택 분기")], "M14", ["DOC", "CALC"], "실제 단지·평면을 특정하지 않는 검색 범위 모형"),
    ("S15", 4, [36, 37], "현금 2억의 가격", "두 사례의 공통축", [("준비금 3천만 원", "2억에서 3000만원 분리"), ("5억 6천6백만 원", "자기자금 1.7억+대출 3.96억"), ("약 201만 원", "월 원리금 201만원")], "M15", ["DOC", "CALC"], "S13의 숫자만 교체하지 않고 두 사례를 같은 축에서 비교"),
    ("S16", 4, [38], "집값 증가의 구성", "증가분 분해", [("집값이 많이 올라갔죠", "주택 예산 증가 3억"), ("대출이 더 늘어나서", "자기자금 증가 9000만원·대출 증가 2억1000만원으로 분해")], "M16", ["DOC", "CALC"], "3억 증가 막대를 0.9:2.1로 분할; 보유 순자산 증가로 표기하지 않음"),
    ("S17", 4, [39], "같은 현금과 다른 한도", "소득 한도 시나리오", [("대출이 2억 원까지만", "대출 블록 3.96억→2억"), ("집값 예산은 3억 7천만 원", "자기자금 1.7억 유지·집값 3.7억")], "M17", ["DOC", "CALC"], "두 승인한도 시나리오를 동일 축에 정렬"),
    ("S18", 5, [42, 43], "3억에서 걸리는 한도", "대출 한도에 닿는 막대", [("2억 6천만 원", "주택 투입금 2.6억"), ("대출한도가 4억 원", "담보상 한도와 개인 한도 4억을 비교"), ("6억 6천만 원", "2.6억+4억=6.6억"), ("개인별 대출한도가 먼저", "개인 한도 게이트 선택")], "M18", ["DOC", "CALC"], "대출 상한 4억을 유지하고 자기자금만 늘림"),
    ("S19", 5, [44, 45], "4·5억과 월 부담의 평탄화", "금액 막대+월 원리금 점", [("7억 5천만 원", "3.5억+4억=7.5억"), ("8억 4천만 원", "4.4억+4억=8.4억"), ("약 203만 원으로 같습니다", "현금 3·4·5억의 월 원리금 점을 같은 높이에 배치")], "M19", ["DOC", "CALC"], "단위가 다른 집값·월 원리금은 별도 패널로 분리"),
    ("S20", 5, [46], "현금 5억의 두 선택", "같은 현금·다른 주택 예산", [("7억 원짜리 집", "8.4억과 7억을 같은 집 크기 아이콘으로 비교"), ("대출은 2억 6천만 원", "자기자금 4.4억 유지·대출 4억→2.6억"), ("약 132만 원", "월 203→132만원; 줄어든 부담 약71만원")], "M20", ["DOC", "CALC"], "가격 차이를 면적이나 품질 차이처럼 보이지 않게 금액 막대 중심"),
    ("S21", 5, [47, 48, 49], "준비금 4000만원의 내부", "정확한 비용 영수증", [("취득세와 지방교육세가 합쳐서", "924만원+92.4만원=1016.4만원"), ("약 290만 원", "중개보수·VAT 290.4만원"), ("약 1천307만 원", "비용 합계1306.8만원"), ("남은 약 2천693만 원", "잔여2693.2만원에 등기·이사·가전·비상금 배분"), ("상한 안에서 협의", "복비 상한과 별도 견적 항목 라벨")], "M21", ["DOC", "TAX", "BROKER", "BOND", "CALC"], "불특정 등기비·이사비에 임의 금액을 배정하지 않음"),
    ("S22", 6, [52, 53], "LTV 70%와 40%", "현금별 두 곡선", [("40퍼센트가 적용되면", "70%·40% 두 시나리오 범례"), ("현금 1억 원은", "1억의 2.66↔1.33억"), ("2억 원은", "2억의 5.66↔2.83억"), ("5억 원은", "3·4·5억 점 순서로 완성")], "M22", ["DOC", "FSC_LTV", "CALC"], "가로축 보유현금·세로축 집값 예산; 시간축처럼 연출하지 않음"),
    ("S23", 6, [54], "적용 조건 확인", "주택·차주 조건 가지", [("생애최초인지", "주택 이력 가지"), ("해당 지역과 주택", "주소·담보·상품 조건 가지")], "M23", ["DOC", "FSC_LTV"], "현행 지역 지도를 임의로 색칠하지 않고 확인 항목을 연결"),
    ("S24", 6, [55, 56], "계약 전 확인 순서", "자금 일정 가로축", [("잔금일에 쓸 수 있는 현금", "현금 확정"), ("은행에서 상담", "인정소득·기존채무 점검"), ("담보평가와 대출 조건", "대상주택 확인"), ("계약 전에", "계약 전 검토 구간을 강조")], "M24", ["DOC"], "상담→최종실행의 시간 차이를 날짜 확정 없이 단계로 표현"),
    ("S25", 6, [57], "월 상환과 생활", "생활비 배분", [("내가 편하게 갚을 수 있는 금액", "월 상환 여력 별도 공간"), ("생활비와 교육비, 부모님 지원", "생활 항목이 예산을 점유"), ("출산이나 이직 계획", "해당 시 필요한 예비 공간")], "M25", ["DOC"], "모든 시청자에게 자녀·부모지원 비용을 동일하게 가정하지 않음"),
    ("S26", 6, [58], "버틸 수 있는 예산", "두 스트레스 방향", [("금리가 올라가거나", "원리금 부담 증가 방향"), ("소득이 잠시 줄어도", "소득 범위 감소 방향"), ("지금 소득으로 이 집을 유지", "남는 월 예산의 경계")], "M26", ["DOC"], "새 금리·소득 숫자는 넣지 않고 검토 방향만 표현"),
    ("S27", 7, [61], "다섯 결과를 한 번에", "최종 예산 비교", [("현금 1억 원이면", "첫 행 2.66억"), ("2억 원이면", "둘째 행 5.66억"), ("3억 원이면", "셋째 행 6.6억"), ("5억 원이면", "4·5억 행까지 완성")], "M27", ["DOC", "CALC"], "앞 장의 두 LTV 그래프를 재생하지 않고 자기자금·대출 최종 막대"),
    ("S28", 7, [62], "시청자가 적을 세 숫자", "빈 예산 작성지", [("현금에서 준비금을 빼고", "잔금현금−준비금 입력칸"), ("실제로 가능한 대출", "확인한 대출칸"), ("매달 갚을 수 있는지", "월 상환 여력칸")], "M28", ["DOC"], "시청자 자신의 숫자를 적도록 빈칸3개만 남김"),
    ("S29", 7, [63, 64], "정책 해석과 부담", "정책 원자료+생활 비용", [("제 생각을 덧붙여", "정책에 대한 해석 라벨"), ("실수요자 지원", "공식 발표의 공급·수요관리·지원 항목"), ("대출 규제를 받고", "차주·주택 조건"), ("세금과 유지비", "보유기간 비용 구간")], "M29", ["DOC", "POLICY"], "해석을 정책 목표나 가격 보장으로 시각화하지 않음"),
    ("S30", 7, [65], "내 생활에 맞는 선택", "집 공간과 생활 동선", [("출퇴근, 가족 계획, 필요한 면적", "일자리·생활공간·면적의 세 시각 요소"), ("월 상환액", "월 예산 영역 연결"), ("더 준비하거나 임차", "매수·준비·임차 선택 갈래")], "M30", ["DOC"], "구체적 지역 가격이나 실제 평형으로 오인될 평면을 넣지 않음"),
    ("S31", 7, [66], "다음 편으로 연결", "같은 예산·다른 입지", [("실제로 어떤 아파트를 골라야", "같은 가격표의 두 입지 구조"), ("같은 5억대, 같은 7억대", "가격이 같아도 다른 통근·생활 동선"), ("내 예산부터 한번 적어", "세 숫자 작성지 CTA; 발화 끝 뒤3초 유지")], "M31", ["DOC"], "정확한 장소 없이 입지 비교 질문을 남기는 도형; 다음 편에 실제 데이터로 확장"),
]

SOURCE_CHECKS = [
    {"id": "FSC_LTV", "url": "https://www.fsc.go.kr/po020201/85466", "checked": "2026-10-26", "scope": "2025-10-17 FAQ의 차주별 LTV 비교표를 열람. 일반/생애최초/정책상품 행을 구별.", "status": "primary_page_opened"},
    {"id": "FSC_CAP", "url": "https://fsc.go.kr/po020201/85518", "checked": "2026-10-26", "scope": "15억·25억 경계의 주담대 상한과 DSR 관련 설명 확인. 본 영상의 개인별 4억 가정과 분리.", "status": "primary_page_opened"},
    {"id": "STRESS", "url": "https://better.fsc.go.kr/fsc_new/status/adminMap/OpertnDetail.do?muNo=145&postNo=4215&stNo=11", "checked": "2026-10-26", "scope": "2026-07-01~12-31 행정지도 페이지의 시행 상태 확인. 첨부 PDF 재열람은 미실시.", "status": "primary_page_opened_attachment_not_reviewed"},
    {"id": "POLICY", "url": "https://www.fsc.go.kr/no010101/87517", "checked": "2026-10-26", "scope": "2026-08-13 공급·수요관리·실수요자 지원 발표 본문 열람. P063은 발표를 바탕으로 한 화자의 해석.", "status": "primary_page_opened"},
    {"id": "TAX", "url": "https://law.go.kr/법령/지방세법", "checked": "2026-10-26", "scope": "원문 주소가 동적 페이지라 전체 조문 추출 안 됨. 제151조 공식 검색결과 보조 확인. 세금 산술은 재계산; 촬영 전 제11·151조 및 해당 면적/감면 요건 재대조 필요.", "status": "partial_not_final_policy_clearance"},
    {"id": "BROKER", "url": "https://land.seoul.go.kr/land/broker/brokerageCommission.do", "checked": "2026-10-26", "scope": "원 DOCX의 부산 서구 링크 timeout. 서울시 공식 요율 페이지로 보완. 2억~9억 미만 매매 상한0.4% 확인용; VAT는 일반과세 가정.", "status": "supplement_primary_page_opened"},
    {"id": "BOND", "url": "https://nhuf.molit.go.kr/FP/FP07/FP0705/FP070509.jsp", "checked": "2026-10-26", "scope": "이번 조회 timeout. 채권 할인액은 산정하지 않았으며 등기 견적에 포함할 항목으로만 계획.", "status": "fetch_failed_no_value_asserted"},
]


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save(name, obj):
    p = PACK / name
    if p.exists():
        raise FileExistsError(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def payment(won):
    r = Decimal("0.045") / 12
    n = 360
    return Decimal(won) * r / (1 - (1 + r) ** -n)


def main():
    assert digest(SOURCE) == EXPECTED_SHA, "The source changed; create a new version."
    snapshot = PACK / "source" / SOURCE.name
    assert not snapshot.exists(), "Immutable input snapshot already exists."
    snapshot.parent.mkdir(parents=True)
    shutil.copyfile(SOURCE, snapshot)
    assert digest(snapshot) == EXPECTED_SHA
    with zipfile.ZipFile(snapshot) as z:
        document = ET.fromstring(z.read("word/document.xml"))
        ps = document.findall("w:body/w:p", NS)
        paras = {i: "".join(t.text or "" for t in q.findall(".//w:t", NS)) for i, q in enumerate(ps, 1)}
        tables = [[["".join(t.text or "" for t in c.findall(".//w:t", NS)) for c in row.findall("w:tc", NS)] for row in tb.findall("w:tr", NS)] for tb in document.findall(".//w:tbl", NS)]
        rels = ET.fromstring(z.read("word/_rels/document.xml.rels"))
        links = [{"id": r.attrib["Id"], "url": r.attrib["Target"]} for r in rels if r.attrib.get("TargetMode") == "External"]
    save("source_extracted.json", {"source": str(SOURCE), "sha256": EXPECTED_SHA, "method": "Local ZIP/XML; no macros executed, no external upload.", "paragraphs": [{"id": f"P{i:03}", "text": v} for i, v in paras.items()], "tables": tables, "links": links})

    rows = []
    for i, row in enumerate(tables[0][1:], 1):
        cash, reserve, price, cap, debt, monthly = map(Decimal, row)
        cash_w, reserve_w, price_w, debt_w = [int(v * 100_000_000) for v in [cash, reserve, price, debt]]
        available = cash_w - reserve_w
        assert available + debt_w == price_w
        assert Decimal(debt_w) <= Decimal(price_w) * Decimal("0.7")
        assert debt_w <= 400_000_000
        pmt = payment(debt_w)
        rounded = (pmt / 10_000).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        assert rounded == monthly, (i, rounded, monthly)
        upper = min(Decimal(available) / Decimal("0.3"), Decimal(available + 400_000_000))
        rows.append({"cash_won": cash_w, "reserve_won": reserve_w, "equity_won": available, "price_won": price_w, "loan_won": debt_w, "LTV_cap_won": int(cap * 100_000_000), "theoretical_price_upper_won": str(upper), "monthly_payment_won": str(pmt), "monthly_payment_10k_display": str(monthly), "narration_monthly_10k": int(monthly.quantize(Decimal("1"), rounding=ROUND_HALF_UP))})
    low = [133_000_000, 283_000_000, 433_000_000, 583_000_000, 733_000_000]
    for row, price in zip(rows, low):
        loan = price - row["equity_won"]
        assert loan >= 0 and Decimal(loan) <= Decimal(price) * Decimal("0.4") and loan <= 400_000_000
        row["LTV40_price_won"] = price
        row["LTV40_loan_won"] = loan
    tax_price = Decimal(660_000_000)
    tax_rate = (tax_price / 100_000_000 * Decimal(2) / 3 - 3) / 100
    tax = tax_price * tax_rate
    education = tax / 10
    broker = tax_price * Decimal("0.004") * Decimal("1.1")
    assert [tax, education, broker, tax + education + broker] == list(map(Decimal, [9_240_000, 924_000, 2_904_000, 13_068_000]))
    cost = {"price_won": int(tax_price), "assumptions": "일반적인 1주택 취득·전용85㎡이하·감면없음·일반과세 중개사·상한보수 적용", "acquisition_tax_won": int(tax), "local_education_tax_won": int(education), "broker_with_VAT_won": int(broker), "total_won": int(tax + education + broker), "reserve_won": 40_000_000, "unallocated_remainder_won": int(40_000_000 - tax - education - broker)}
    extra = {"cash1_to_cash2_price_increase_won": rows[1]["price_won"] - rows[0]["price_won"], "equity_increase_won": rows[1]["equity_won"] - rows[0]["equity_won"], "loan_increase_won": rows[1]["loan_won"] - rows[0]["loan_won"], "cash5_cheaper_home_price_won": 700_000_000, "cash5_cheaper_home_loan_won": 260_000_000, "cash5_cheaper_home_payment_10k": str((payment(260_000_000) / 10_000).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)), "savings_between_cash5_choices_10k": str(((payment(400_000_000) - payment(260_000_000)) / 10_000).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))}
    save("calculation_check.json", {"status": "passed_arithmetic_only", "policy_clearance": "not_equivalent_to_arithmetic_pass", "units": "Amounts in KRW; precise strings retain Decimal precision. Display prices are chosen below mathematical ceilings.", "rate": "4.5%", "months": 360, "individual_loan_cap_won": 400_000_000, "reserve_origin": "User-authored hypothetical budget, not measured average cost.", "rows": rows, "cost_example": cost, "insights": extra})
    save("source_checks.json", {"status": "guide_stage_partial_policy_check", "items": SOURCE_CHECKS, "not_cleared": ["latest_area_designations", "full_article11_151_tax_review", "2026_stress_attachment", "final_product_or_bank_approval"], "scope": "Guide drafting and source planning; no statement of universal credit approval or full policy re-verification."})

    scenes, used = [], []
    for sid, chapter, pids, message, typ, beats, asset, sources, fallback in SCENES:
        text = "\n\n".join(paras[i] for i in pids)
        for anchor, action in beats:
            assert anchor in text, (sid, anchor)
        used.extend(pids)
        scenes.append({"scene_id": sid, "chapter": chapter, "message": message, "narration_text": text, "paragraph_ids": [f"P{i:03}" for i in pids], "claim_ids": sources, "material_type": typ, "asset_ids": [asset], "script_revision": EXPECTED_SHA, "audio_revision": None, "start": None, "end": None, "timing_basis": "literal_user_script_anchors_pending_recording", "beats": [{"anchor": a, "action": b, "start": None, "end": None} for a, b in beats], "status": "designed_not_rendered", "preparation_status": "graphic_to_author; source text and arithmetic available; conditional sources tracked separately", "fallback": fallback})
    expected = list(range(7, 12)) + list(range(14, 20)) + list(range(22, 30)) + list(range(32, 40)) + list(range(42, 50)) + list(range(52, 59)) + list(range(61, 67))
    assert sorted(used) == expected and len(used) == len(set(used))
    save("scene_plan.json", {"status": "design_proposal", "source_sha256": EXPECTED_SHA, "scene_count": len(scenes), "covered_narration_paragraphs": len(expected), "audio_received": False, "measured_duration_s": None, "source_runtime_estimate_minutes": [10, 13], "scenes": scenes})

    chapter_names = {1: "돈을 모은 다음의 질문", 2: "집값 밖의 비용", 3: "대출의 기준", 4: "현금 1억과 2억", 5: "현금 3억부터 5억", 6: "지역과 월 상환", 7: "내 예산 정리"}
    sheet = ["# 직접 녹음용 문단표 — 원문 보존", "", "원 DOCX의 낭독 본문 48문단만 순서대로 옮겼습니다. 원문의 단어·어미는 바꾸지 않았습니다. 화면 지시·제작 참고표·출처는 읽지 않습니다. 아래 대괄호·장면 ID·원문 문단 번호도 읽지 않습니다.", "", "본문의 간결화 제안은 별도 영상 가이드의 ‘녹음 전 문장 제안’에 있습니다. 이 문단표는 수정안이 아닌 원문입니다.", "", "장마다 파일을 나누어도 됩니다. 틀린 문장은 2~3초 쉬고 문장 처음부터 다시 읽으면 됩니다. 숫자 뒤 그래프 시간을 맞추려 애쓰지 말고 자연스럽게 읽습니다.", ""]
    current = None
    for s in scenes:
        if s["chapter"] != current:
            current = s["chapter"]
            sheet += [f"## {current:02d} {chapter_names[current]}", "", f"권장 파일명: `CH{current:02d}_take01.wav` 또는 `.mp3`", ""]
        sheet += [f"### {s['scene_id']} · {s['message']}", "", "[화면이 반응할 말] " + " / ".join(b["anchor"] for b in s["beats"]), ""]
        for pid in s["paragraph_ids"]:
            sheet += [f"[{pid} · 아래 문장만 낭독]", "", paras[int(pid[1:])], ""]
    (PACK / "녹음용_문단표.md").write_text("\n".join(sheet), encoding="utf-8")

    template = json.loads((ROOT / "video-agent-studio/templates/episode_preflight.json").read_text(encoding="utf-8"))
    template.update({"status": "guide_only_pending_recording", "episode_id": EP.name})
    template["baseline"].update({"previous_video": "housing-choice-networth-20261020/outputs/jun-production-v1/renders/measured-jun-v1/housing_choice_jun_v1.mp4", "current_video": "outputs/rebuild-v2/full-film-r2-v1/affordable_home_price_rebuild_r2_v1.mp4", "sha256": "55d8626a5eff6ea43da064a44d9999133e09dc635a6b3f6e67a6f5025b64b761", "script_revision": EXPECTED_SHA, "audio_revision": None})
    template["story"] = {"opening_question": "현금1억~5억으로 어느 가격대의 집을 볼 수 있을까", "previous_episode_reference": "매매·전세·월세의 자산 비교 다음 선택", "next_episode_promise": "예산 안에서 실제 지역·단지 비교", "order": list(chapter_names.values()), "each_section_answers": ["주택 투입금", "적용 대출한도", "월 원리금", "생활 선택"], "candidate_scope": "hypothetical_cash_scenarios_not_apartment_recommendations"}
    template["representative_previews"] = ["S13_cash_to_house_price", "S18_S19_personal_cap_binds", "S21_exact_cost_receipt"]
    template["facts_required"] = ["scenario_vs_policy_limits", "current_LTV_scope", "purchase_tax_assumptions", "broker_ceiling_and_VAT", "reserve_as_budget", "all_payment_calculations"]
    template["change_control"].update({"superseded_rules": ["이번 버전은 사용자가 직접 녹음한다. 기존 합성음성 및 타임코드 승인은 새 녹음에 승계하지 않는다.", "사용자 제공 DOCX의 말투를 원문 기준으로 보존한다.", "최신 공통 지시로 화면 AI 배지 및 반복 부정형 면책 문구 제외."], "changed_scene_ids": [s["scene_id"] for s in scenes], "single_timing_lock": None})
    template["visual_defaults"]["ai_placeholder_requires_resolution_before_delivery"] = True
    template["qa"]["station_locations"] = "not_applicable_no_geographic_map_planned"
    template["qa"]["actual_block_plan_and_locator"] = "not_applicable"
    template["qa"]["district_area_vs_planned_station_distinguished"] = "not_applicable"
    template["vertical_video"]["status"] = "not_applicable_16_9_longform_guide"
    save("episode_preflight.json", template)
    files = [snapshot, PACK / "source_extracted.json", PACK / "calculation_check.json", PACK / "source_checks.json", PACK / "scene_plan.json", PACK / "녹음용_문단표.md", PACK / "episode_preflight.json"]
    save("preparation_receipt.json", {"completed_at_utc": datetime.now(timezone.utc).isoformat(), "status": "local_guide_inputs_prepared", "source_unchanged": digest(SOURCE) == EXPECTED_SHA, "source_sha256": EXPECTED_SHA, "narration_paragraphs": len(expected), "scenes": len(scenes), "literal_anchors": sum(len(s["beats"]) for s in scenes), "arithmetic_checks": "pass_5_main_5_ltv40_cost_and_two_cash5_choices", "audio_received": False, "voice_generation_calls": 0, "paid_generation_calls": 0, "render_performed": False, "external_audio_transfer": False, "files": [{"path": str(p.relative_to(ROOT)), "sha256": digest(p)} for p in files]})
    print(json.dumps({"status": "prepared", "scene_count": len(scenes), "paragraphs": len(expected), "anchors": sum(len(s["beats"]) for s in scenes), "source_unchanged": digest(SOURCE) == EXPECTED_SHA}, ensure_ascii=False))


if __name__ == "__main__":
    main()
