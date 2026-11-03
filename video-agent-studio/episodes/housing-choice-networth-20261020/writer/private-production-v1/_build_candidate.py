from pathlib import Path
import collections
import difflib
import hashlib
import json
import math
import re

OUT = Path(__file__).resolve().parent
EP = OUT.parent.parent
SRC = EP / 'outputs/cost-wording-v3/script_cost_v3.md'
AUTH = EP / 'director/two-episode-production-v1/authorization.json'
raw = SRC.read_bytes()
original = raw.decode('utf-8-sig').replace('\r\n', '\n')
pattern = r'^## (\d+)\. ([^\n]+)\n(.*?)(?=^## |\Z)'
chapters = []
for m in re.finditer(pattern, original, re.M | re.S):
    paragraphs = [p.strip() for p in m[3].strip().split('\n\n') if p.strip()]
    chapters.append({'number': int(m[1]), 'title': m[2], 'original': paragraphs, 'paragraphs': paragraphs.copy()})
assert [c['number'] for c in chapters] == list(range(1, 11))

edits = {}
def replace(ch, para, before, after, reason):
    key = (ch, para)
    row = chapters[ch - 1]['paragraphs']
    assert row[para - 1].count(before) == 1, (key, before)
    row[para - 1] = row[para - 1].replace(before, after)
    edits.setdefault(key, []).append(reason)

replace(2, 4, '배당과 환율 효과를 포함한 원화 연 6%', '배당과 환율 효과를 포함한 원화 총수익 연 6%', '배당·환율을 포함한 총수익 가정을 직접 표기')
replace(2, 5, '출발 자금이 많은 가구를 고르거나, 더 싼 집에 사는 가구를 섞으면 주거 방식보다 다른 조건의 차이가 결과에 들어갑니다. 같은 집과 같은 예산을 맞추는 이유가 여기에 있습니다.', '같은 집과 같은 예산을 맞춰 주거 방식에 따른 차이를 보겠습니다.', '잘못된 비교의 예시를 동일 조건의 목적 설명으로 압축')
replace(3, 1, '이번 비교에서는 이런 항목을 초기 부대비용으로 묶어 약 600만원으로 가정하겠습니다.', '이번 비교의 약 600만원은 이런 항목을 묶은 설명용 가정 금액입니다. 실제 거래의 항목별 비용은 거래 조건에 따라 따로 산정합니다.', '600만원이 실제 항목 합계가 아닌 비용 묶음의 설명용 가정임을 명확화')
replace(3, 2, '이때 집값 6억원 전체가 이 가구의 순자산은 아닙니다.', '이때 집값 6억원은 대출을 포함한 자산입니다.', '자산과 순자산의 차이를 긍정형으로 설명')
replace(3, 3, '이 비용을 약 100만원으로 잡으면', '이 비용 묶음에 설명용 가정 약 100만원을 적용하면', '전세 초기비용 100만원도 설명용 비용 묶음임을 명시')
replace(3, 4, '월세도 중개보수 등 초기 부대비용을 약 100만원으로 가정하겠습니다.', '월세도 중개보수 등 초기 부대비용 묶음에 설명용 가정 약 100만원을 적용하겠습니다.', '월세 초기비용 100만원도 설명용 비용 묶음임을 명시')
replace(3, 4, '처음부터 돈이 더 많아서가 아니라 주거 보증금에 묶인 자기자금이 적기 때문입니다.', '주거 보증금에 묶인 자기자금이 적기 때문입니다.', '초기 투자금 차이가 생기는 조건을 직접 설명')
replace(4, 2, '매매 가구는 집만 보유하고 임차 가구만 투자하도록 놓으면 실제 자산 배분의 한 부분이 빠집니다. 이번 비교에서는 세 가구 모두 같은 투자수익률을 적용합니다.', '세 가구 모두 주거 자산과 투자계좌를 함께 보유하고 같은 투자수익률을 적용합니다.', '세 가구의 공통 투자 규칙을 직접 설명')
replace(4, 4, ' 월세가 나간다는 사실 하나로 끝내거나 초기 투자금만 비교하면 이 두 흐름을 놓칩니다.', '', '앞 문장의 초기 투자금·월 적립금·수익 설명과 겹치는 회피 문장 삭제')
replace(4, 5, '두 가구의 차이는 25만원입니다.', '매매와 임차의 비용 가정 차이는 25만원입니다.', '비용 묶음의 비교 대상을 직접 표기')
replace(5, 3, chapters[4]['original'][2], '처음 빌린 3억6천만원에서 매달 갚은 원금을 차감해 대출잔액을 계산합니다. 마지막 순자산에서는 그 잔액을 한 번 뺍니다. 원금 상환의 효과는 줄어든 빚에 반영합니다.', '중복계상 경고 대신 원금 차감→남은 빚 반영 순서를 설명')
replace(5, 4, '돌려받은 원금 전체를 새 수익으로 더하지 않습니다.', '보증금 반환은 자산의 형태가 현금으로 바뀌는 과정입니다.', '보증금 반환을 현금 전환으로 직접 설명')
replace(5, 5, ' 여기서 포기한 투자수익을 다시 비용으로 빼면 같은 차이가 두 번 들어갑니다.', '', '기회비용을 초기 투자계좌 크기에 반영한다는 앞 설명 보존·중복 경고 삭제')
replace(6, 1, '배당이 들어 있는 수익률을 쓰면서 배당을 다시 더하면 실제보다 높아집니다.', '이 총수익으로 배당 효과까지 함께 계산합니다.', '배당을 포함하는 계산 범위를 직접 설명')
replace(6, 2, '이 값에 환율 상승을 한 번 더 붙이면 중복됩니다.', '이 원화 수익률로 환율 효과까지 함께 반영합니다.', '원화 수익률의 포함 범위를 직접 설명')
replace(6, 3, chapters[5]['original'][2], '이번 계산은 배당과 환율 효과를 포함한 원화 총수익을 연 6%로 가정합니다. 6%는 10년간 주거 방식에 따른 차이를 보기 위한 비교 조건입니다. 세 가구의 투자계좌에 이 원화 수익 6%를 같이 적용합니다. 배당의 세금과 매도 시 과세, 환전비용, 운용보수는 추가 반영 전이며, 실제 상품별 계산에서는 포함 범위를 맞춰야 합니다.', '예측·중복 관련 부정형을 가정의 용도·공통 적용·세금 및 비용 포함 범위로 전환')
replace(6, 4, '그달 말에 새로 넣은 돈이 한 달 수익을 미리 얻는 것으로 처리하지 않습니다.', '월말에 새로 넣은 돈은 다음 달부터 수익을 얻습니다.', '월말 납입금의 수익 발생 시점을 직접 설명')
replace(6, 4, '연 6%는 매달 0.5%를 단순 적용하지 않고, 12개월을 복리로 연결했을 때 연 6%가 되도록 바꿉니다.', '연 6%는 월 0.5%의 단순 배분과 구분해, 12개월을 복리로 연결했을 때 연 6%가 되도록 바꿉니다.', '연 수익률의 월 복리 변환 기준을 긍정형으로 정리')
replace(6, 5, '여기에 집에서 살며 얻는 가상의 임대료까지 현금수익으로 더하면 같은 주거 혜택이 겹칩니다.', '주거 혜택은 이 지출표에서 한 번 반영합니다.', '자가 거주 혜택의 반영 위치를 직접 설명')
replace(7, 3, '월세만 따로 누적한 표와 금융자산만 따로 본 표를 합쳐야 이 결과를 설명할 수 있습니다.', '주거비를 낸 뒤 남은 금융자산까지 함께 보는 이유입니다.', '표 읽기 지시를 주거비와 투자금의 관계 설명으로 압축')
replace(8, 5, '처음의 결과 하나가 세 가지 방식의 고정된 순위를 뜻하지 않는 이유입니다.', '조건에 따라 가장 크게 남는 방식도 달라집니다.', '고정 순위의 부정 대신 조건별 결과 변화를 직접 설명')
replace(8, 8, '각 화면은 기간 중 금리가 오르내리는 장면이 아니라, 처음부터 서로 다른 고정금리를 적용한 별도 조건입니다.', '각 화면은 처음부터 서로 다른 고정금리를 적용한 별도 조건입니다.', '고정금리 시나리오의 비교 조건을 직접 설명')
replace(8, 9, '아직 계산하지 않은 정확한 손익분기선을 임의로 그리기보다, 계산된 조건을 먼저 보여주고 경계 주변을 더 촘촘하게 계산하면 판단에 필요한 범위를 좁힐 수 있습니다.', '계산된 조건을 먼저 비교하고, 경계 주변을 더 촘촘하게 계산하면 판단에 필요한 범위를 좁힐 수 있습니다.', '미계산 경고 대신 현재 비교 범위와 다음 계산 방법을 설명')
replace(9, 2, '여기서 투자하지 않은 돈은 사라지지 않고 현금으로 남습니다. 따라서 이 실험은 저축을 하지 않는 경우와 다릅니다.', '여기서는 투자하지 않은 돈도 현금으로 남아 저축 원금에 포함됩니다.', '미투자 현금 보유와 소비의 차이를 직접 설명')
replace(10, 2, '그보다 높은 성과를 꾸준히 낼 수 있고,', '영상의 집값·금리·임대료 조건을 유지하면서 그보다 높은 성과를 꾸준히 낼 수 있고,', '6%를 보편적인 승리 기준으로 읽지 않도록 영상의 고정 조건에 연결')

candidate = '# 매매·전세·월세, 같은 집에서 10년을 비교합니다\n\n'
candidate += '버전: script-v4-candidate · 최종영상용 후보 · 독립 QA 대기 · 작성일 2026-10-26\n'
candidate += '길이와 장면별 시간은 estimate입니다. 실제 음성 생성·청취·시간 정렬 전입니다. 본문 소제목 아래 문단만 낭독합니다. 화면 주석은 scene_outline.json에 분리했습니다. 익명 가정 모형 illustrative-v1을 유지합니다.\n\n'
for c in chapters:
    candidate += f"## {c['number']}. {c['title']}\n\n" + '\n\n'.join(c['paragraphs']) + '\n\n'
candidate = candidate.rstrip() + '\n'

# 각 행은 해당 문단만의 메시지 / 화면의 구체적인 대상 / 재사용할 수 있는 내용이다.
# 기존 파일의 실제 프레임은 이 작업에서 확인하지 않았으므로 재사용은 모두 조건부다.
plan = {
1: [
('같은 집에 살아도 주거비와 자금 배분에 따라 남는 자산이 달라진다', '동일한 집 단면에 매매·전세·월세의 자금 경로를 나란히 연결', 'S001 동일 집·세 가구 비교 도식'),
('초기 순자산·월예산·집·기간과 투자 규칙을 동일하게 둔다', '초기자금·월예산·주거 수준·기간을 세 가구에 같은 크기로 정렬', 'S001의 동일 조건 비교 도식'),
('기본 결과를 예고하고 가정에 따라 순서가 바뀜을 제시한다', '세 순자산 막대와 집값·투자수익 조건 칸을 연결해 결과 예고', 'S002 결과 예고 차트'),
('교산의 입지 판단에서 주거 방식·예산·단지 선택으로 이어진다', '전편의 실제 교산 지도와 이번 시리즈 단계 경로를 짧게 연결', 'S003 전편 연결 제안; 승인 지도 파일은 담당 확인 필요'),
],
2: [
('동일 주거 서비스와 공통 생활비를 맞춘다', '집의 면적·위치·편의 열과 공통비용을 세 장부에 동일하게 배치', 'S004 동일 조건 장부'),
('기존 실거래 연결 결과는 지역과 기간에 따라 다르다', '기존 집계의 지역·관측기간·상승률을 연결하고 발화 지역만 강조', 'returns/regional-motion 기존 자료의 같은 기간·지역 화면만; 별도 QA 확인 후'),
('집값 연 2%는 상환 지속 가능성을 보는 보수적 계획 조건이다', '계획 가정 2%를 과거 관측 영역과 분리하고 같은 집의 조건별 경로를 연결', 'growth-explanation 보강 제안의 계획 가정·민감도 구간; 과거 평균 차트 재사용 금지'),
('투자·금리·고정 임대료와 비용·세금의 포함 범위를 밝힌다', '총수익·대출·월세·보증금·가정 비용을 자금 흐름에 붙이고 상품별 세금·운용비용 추가 반영 전을 짧게 표시', 'S004 구조만 활용; v4 포함 범위와 현재 문단에 맞춰 조건띠 갱신'),
('같은 집과 예산으로 주거 방식에 따른 차이를 분리한다', '같은 집·예산 축에 가격 변화와 월 저축 흐름을 분리해 배치', 'S004~S005 같은 조건 도식의 해당 요소'),
('세 가구 모두 같은 종료 시점의 자산과 부채를 평가한다', '세 자금 경로의 끝을 동일 120개월 선에 맞춤', 'S005 비교 기간 도식'),
],
3: [
('매매 초기자금을 자기자금·대출·가정 비용·투자잔액으로 나눈다', '집으로 들어가는 자기자금·대출과 밖으로 나가는 비용, 남는 투자금의 화살표를 분리', 'S006 매매 초기 배분; 비용 합계처럼 보이는 항목표는 설명용 비용 묶음으로 수정'),
('집과 투자계좌에서 대출을 차감한 금액이 거래 직후 순자산이다', '집+투자계좌−대출의 순서로 순자산 막대를 조합', 'S006 자산·부채 분해'),
('전세 보증금의 자금 출처와 금융자산 잔액을 구분한다', '보증금으로 가는 자기자금·대출과 설명용 초기비용·투자계좌를 연결', 'S007 전세 자금 도식; 100만원을 비용 묶음 가정으로 표기'),
('월세는 보증금에 적게 묶여 초기 투자계좌가 커진다', '월세 보증금의 자금 출처와 남는 투자금 면적을 분리', 'S008 월세 초기 배분; 100만원 비용 설명 갱신'),
('임차 대출은 이자만 납부하고 보증금 전액 반환으로 원금을 상환한다', '계약 시작·이자 납부·보증금 전액 정상 반환·대출 상환 경로를 연결', 'S008 반환 설명 부분만; 초기 배분 막대만 반복하지 않음'),
],
4: [
('매매 월예산은 원리금·보유비용·투자금으로 나뉜다', '월 300만원 흐름이 원리금과 비용으로 갈라지고 투자금이 남는 도식', 'S009 매매 월예산 도식'),
('매매도 남은 돈을 같은 투자 규칙으로 운용한다', '매매의 월 잔액이 다른 두 가구와 같은 투자계좌 규칙에 연결됨을 강조', 'S009의 투자계좌 유입 요소'),
('전세와 월세의 이자·월세·비용 차이가 월 투자금 차이를 만든다', '전세·월세 각각의 예산을 주거지출과 투자금으로 분해', 'S010 월 흐름 비교'),
('전세는 월 적립금, 월세는 초기 투자금이 크다', '초기 투자금과 매달 투자금을 서로 다른 두 축에 놓고 같은 수익 규칙에 연결', 'S010 구조; 월세 누적 지출만 보이는 차트는 사용하지 않음'),
('월별 추가비용은 가정 묶음이고 공통비용과 실제 부담 차이를 구분한다', '공통 관리비 영역과 매매·임차의 추가비용 묶음을 구분', 'S010 비용 항목 설명 부분; 숫자에 실제 항목별 합계 라벨 금지'),
],
5: [
('대출 상환액 중 이자는 비용, 원금은 부채 감소다', '첫 달 상환액을 이자와 원금으로 나눠 원금 부분만 대출잔액에서 차감', 'S011 원금·이자 분해'),
('상환이 이어지면 잔액과 이자 비중이 줄고 원금 비중이 늘어난다', '대출잔액 곡선과 원금·이자 구성 변화를 동일 월 축에 연결', 'S011 상환 경로'),
('갚은 원금은 줄어든 대출잔액으로 최종 순자산에 반영한다', '처음 대출에서 누적 상환 원금을 차감하고 마지막 잔액을 순자산 식에 한 번 연결', 'S012 회계 구조; 오류 예시 경고 대신 올바른 계산 순서로 수정'),
('보증금 반환은 자산의 현금 전환이며 대출도 함께 상환한다', '보증금 권리가 현금으로 바뀐 뒤 대출 상환과 잔액으로 갈라지는 흐름', 'S013 보증금 반환 구간'),
('보증금·집에 묶인 자기자금은 작은 초기 투자계좌로 반영한다', '처음 장부의 주거 자금과 투자금 비율에서 출발해 실제 투자수익만 누적', 'S013 기회비용 구간; 반환 화면과 다른 자금 배분 상태를 사용'),
],
6: [
('총수익은 가격 상승과 배당 재투자를 함께 포함한다', '가격 변화와 재투자 배당이 총수익으로 합쳐지는 도식', 'S014 총수익 구간'),
('원화 수익은 달러 자산 변화와 환율의 곱으로 연결된다', '달러 자산 변화와 환율 변화가 곱해지는 두 단계와 원화 결과를 연결', 'S014 환율 계산 구간'),
('연 6%는 원화 총수익 가정이며 상품별 세금·보수·환전비용 추가 반영 전이다', '원화 총수익 가정을 세 계좌에 공통 연결하고 세금·환전·운용비용의 포함 범위를 짧게 표시', 'S015 가정 설명; v4 세금·비용 문구 갱신'),
('기존 잔액에 월수익을 적용하고 새 납입금은 월말에 넣는다', '월초 잔액→수익 적용→월말 납입→다음 달의 단계와 연·월 복리 연결', 'S015 납입 시점·복리 구간'),
('집의 가격 변화와 자가 거주 지출 효과를 서로 다른 장부에 반영한다', '집 평가액의 가격 변화와 월 지출표의 주거 효과를 따로 연결', 'S016 주거 서비스 회계 도식'),
],
7: [
('집·금융자산에서 남은 대출을 빼 매매 순자산을 계산한다', '매매 집 평가액+금융자산−잔여대출의 분해 막대를 순서대로 조합', 'S017 매매 순자산 분해'),
('임차 순자산은 보증금·금융자산에서 대출을 차감한다', '전세와 월세의 보증금+금융자산−대출을 같은 축에서 조합', 'S017~S018 해당 임차 분해 구간'),
('기본 조건의 차이는 초기 투자금과 월 차액의 누적에서 생긴다', '최종 차이와 초기 투자금·월 적립금의 경로를 연결', 'S018 차이 설명; 결과 막대만 유지하지 않음'),
('평가 순자산과 바로 쓸 수 있는 돈의 역할을 구분한다', '집 지분·보증금·투자계좌를 현금 전환 경로와 함께 구분', 'S019 평가·유동성 도식'),
('현금 청산 비교에는 매도비용·세금과 이후 주거비를 함께 연결한다', '현재 계속거주 장부 옆에 청산 시 필요한 비용·다음 주거 연결만 표시', 'S019 청산 비교 구간; 새 청산 금액 계산 금지'),
],
8: [
('투자·금리·임대 조건을 고정하고 집값만 바꾼다', '고정 조건은 유지하고 집값 상승률 입력 칸만 선택', 'S020 민감도 구조; 기존 v1 문단 번호 대신 내용으로 대응'),
('집값 가정 변화로 매매의 순자산과 세 가구 순서가 달라진다', '집값 조건별 매매 결과를 동일 축에서 바꾸고 임차 결과는 고정', 'S020 같은 집값 민감도 구간'),
('대출은 집 전체 가격 변화를 자기자금과 연결하며 하락 위험도 키운다', '자기자금과 대출이 합쳐진 집 전체의 가격 변화·이자·원금 흐름을 연결', 'growth-explanation 레버리지 제안 중 같은 수치 구간; 상승 그래프를 하락 설명에 그대로 반복 금지'),
('집값 상승과 낮은 투자수익을 함께 놓으면 결과가 달라진다', '두 입력을 함께 고른 뒤 해당 조건의 세 결과를 강조', '기존 민감도 차트의 동일 조합만'),
('집값·투자수익 조합에 따라 임차 방식 사이의 순서도 달라진다', '본문의 두 조건 조합을 별도 상태로 전환하고 각 결과에 연결', '기존 민감도 차트의 동일 조합; 미계산 경계선 추가 금지'),
('월세 인상 가정은 월 투자금과 최종 순자산을 줄인다', '보증금 고정 상태에서 월세 차이가 투자금 감소를 거쳐 최종 결과로 연결', '기존 월세 민감도 구간만; 집값 차트에 제목만 바꿔 재활용 금지'),
('매매·전세의 대출금리 차이가 최종 결과를 바꾼다', '매매·전세 금리 입력의 두 조합을 각각 결과에 연결하고 월세 대출금리는 고정', 'S021 금리 차이 구간; 기존 문단 앵커가 아닌 내용 기준으로 선택'),
('각 금리 비교는 처음부터 서로 다른 고정금리를 적용한 조건이다', '별도 고정금리 경로를 나란히 두고 변동금리 설명에는 잔액·적용시점을 연결', 'S021 금리 조건 도식; 시간 중 변동인 듯 보이는 화면은 수정'),
('계산된 조건을 비교하고 경계 주변을 추가 계산해 판단 범위를 좁힌다', '이미 계산된 조건 칸만 표시하고 집값·수익·금리·월세의 이동 방향을 안내', '조건 격자 구조; 정확한 손익분기선·미계산 결과를 그리지 않음'),
],
9: [
('월 차액의 절반은 투자, 나머지는 현금으로 두는 경우를 비교한다', '월 잔액을 ETF와 현금으로 반씩 분기하고 최종 자산을 함께 누적', 'S022 실행률 구간'),
('현금 보유도 저축 원금이며 소비와 다른 경로다', '같은 월 잔액이 ETF·현금·소비로 가는 경로를 구분하되 소비 결과값은 추가하지 않음', 'S022 현금·저축 구간; 투자 손실 차트를 그대로 사용하지 않음'),
('월예산을 넘으면 모형 경로를 멈추며 다른 대응은 별도 계산이다', '주거지출과 월예산을 비교해 초과 지점에서 계산 경로 정지; 별도 대응은 분기만', 'S023 예산·유동성 구간'),
('계약 갱신·투자 하락·이사 시점과 자금 집중 위험을 함께 본다', '계약 갱신과 이사 일정에 보증금·월세·시장가격·필요 현금의 흐름을 연결', 'S023 유동성 도식; 원금·월세 비교 차트를 무관하게 반복하지 않음'),
],
10: [
('주거 방식은 가진 돈·월지출·거주기간과 자금 운용을 함께 비교한다', '같은 집을 중심으로 초기자금·월 흐름·거주기간을 선택 틀에 연결', '기존 비교 틀의 요소만; v1 S024의 실제시장 지도와 의미가 달라 그대로 재사용 금지'),
('임차의 유리함도 영상의 주거 조건과 꾸준한 차액 투자에 달려 있다', '영상의 집값·금리·임대료 조건을 유지한 채 투자 성과와 적립 지속 경로를 연결', '조건부 선택 도식 구조만; 6% 임계선이나 승자 배지 추가 금지'),
('실거주 매매는 자산 형성 기대와 주거 안정 가치를 함께 가진다', '집에 머무는 생활 일정과 원금 상환·자산 경로를 양쪽에 연결', '기존 주거 안정 설명 화면이 같은 의미일 때만; 자산 수익 차트 단독 반복 금지'),
('화자는 감당 가능한 매매와 오래 유지할 생활 터전에 가치를 둔다', '한 집에서 생활 계획을 이어가는 개념 화면에 생활비·비상자금·상환 지속 조건을 짧게 연결', '동일 주거 안정 소재만 조건부 활용; 다른 장의 지역 사진·이미지 재활용 금지'),
('기대 상승보다 보유를 지속할 수 있는 가격과 월 상환 여력을 먼저 본다', '소득·금리 변화에 월 상환과 생활비를 연결해 보유 지속 가능성 표시', '기존 감당 가능성 도식이 같은 조건을 설명할 때만; 새 가격 한도 계산 금지'),
('다음 편은 종자돈·소득·추가비용·비상자금·상환액으로 매매 가격 범위를 계산한다', '다음 편의 계산 입력이 차례로 이어지는 경로를 보여주며 마무리', 'S025 후속 편 연결 구조; 낡은 문단 앵커 대신 현재 예고에 맞춰 교체'),
],
}

def sha(data):
    return hashlib.sha256(data).hexdigest()

input_sha = sha(raw)
script_sha = sha(candidate.encode('utf-8'))
def dump(name, obj):
    path = OUT / name
    # 다른 작업자가 만든 기존 결과를 자동으로 덮어쓰지 않는다.
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write('\n')

old_scenes = { (1,1):'S001',(1,2):'S001',(1,3):'S002',(1,4):'S003',
 (2,1):'S004',(2,4):'S004',(2,5):'S005',(2,6):'S005',
 (3,1):'S006',(3,2):'S006',(3,3):'S007',(3,4):'S008',(3,5):'S008',
 (4,1):'S009',(4,2):'S009',(4,3):'S010',(4,4):'S010',(4,5):'S010',
 (5,1):'S011',(5,2):'S011',(5,3):'S012',(5,4):'S013',(5,5):'S013',
 (6,1):'S014',(6,2):'S014',(6,3):'S015',(6,4):'S015',(6,5):'S016',
 (7,1):'S017',(7,2):'S017/S018',(7,3):'S018',(7,4):'S019',(7,5):'S019',
 (8,1):'S020',(8,2):'S020',(8,7):'S021',(8,8):'S021',
 (9,1):'S022',(9,2):'S022',(9,3):'S023',(9,4):'S023',(10,6):'S025'}

outline_chapters = []
changes = []
for c in chapters:
    ch = c['number']
    assert len(plan[ch]) == len(c['paragraphs'])
    rows = []
    for p, (text, spec) in enumerate(zip(c['paragraphs'], plan[ch]), 1):
        message, visual, reuse = spec
        sid = f'W4-C{ch:02d}-P{p:02d}'
        kind = 'data_chart'
        purpose = '설명'
        if (ch,p) == (1,4): kind = 'map'
        if (ch,p) in {(10,3),(10,4)}: kind = 'ai_concept'; purpose = '분위기·가치 전달'
        claims = ['SIM01']
        if (ch,p) == (1,4) or ch == 10: claims = []
        if (ch,p) == (2,2): claims = []
        if (ch,p) in {(6,1),(6,2)}: claims = ['M08','M09','M10','M11']
        if (ch,p) == (6,5): claims = ['M06']
        basis = '기준 script_cost_v3.md의 해당 문단; 수치·원 모형 그대로 계승. 독립 사실·계산 검수는 별도 QA.'
        if (ch,p) == (2,2): basis += ' 기존 outputs/growth-explanation-v1/facts.json·regional-motion 자료는 QA 확인 대상; writer가 원자료를 재검수하지 않음.'
        if ch == 10: basis = '기준 대본의 화자 관점·조건부 선택 틀·다음 편 예고; 수익 보장이나 새 분석 결과가 아닌 관점 서술.'
        rows.append({
            'scene_id': sid, 'scene_id_scope': 'writer 문단 제안 ID; 공통 장면 ID를 교체하지 않음',
            'paragraph': p, 'narration_anchor': text[:65], 'narration_sha256': sha(text.encode()),
            'message': message, 'asset_types': [kind], 'screen_purpose': purpose,
            'visual_direction': visual,
            'emphasis_action': '발화에 맞춰 위 화면지시의 해당 대상만 강조하고, 무관한 이전 선택·라벨은 해제합니다.',
            'claim_ids': claims, 'claim_status': '기존 주장 연결의 제안이며 검수 통과를 승계하지 않음',
            'evidence': basis,
            'existing_screen_reuse': {'status':'내용 일치 시 조건부 가능; 실제 프레임 미확인', 'content':reuse, 'legacy_scene_hint':old_scenes.get((ch,p))},
            'changes': edits.get((ch,p), ['낭독 원문 유지; 문단별 화면 목적만 분리']),
            'asset_status':'후속 visual/editor가 실제 자산·기간·단위·강조 대상 확인 후 확정',
            'fallback': '동일 수치·메시지의 별도 자금 흐름 도식으로 구성; 개념 생활 화면은 동일 의미의 기존 자산이 없으면 신규 소재를 제안',
            'estimate_duration_seconds': [math.ceil(len(re.sub(r'\s','',text))/600*60), math.ceil(len(re.sub(r'\s','',text))/500*60)],
            'timing_basis': 'estimate; 공백 제외 문자/분 500~600의 임시 가정. 숫자·영문 읽기·쉼·브랜드 길이는 실제 TTS 후 재산정',
        })
        if (ch,p) in edits:
            changes.append({'scene_id':sid,'chapter':ch,'paragraph':p,'reason':edits[(ch,p)],'before':c['original'][p-1],'after':text,'numbers':'금액·비율·계산값 신규 추가 없음'})
    outline_chapters.append({'chapter':ch,'title':c['title'],'chapter_transition':{'asset_type':'ai_concept','purpose':'주제 전환 분위기','reuse':'같은 주제에 맞는 기존 배경만 조건부 사용. 주제와 무관한 공통 이미지 반복 금지. 제목은 별도 편집 레이어.','status':'실제 배경 프레임 미확인'},'paragraphs':rows})

source_narration = '\n\n'.join(p for c in chapters for p in c['original'])
target_narration = '\n\n'.join(p for c in chapters for p in c['paragraphs'])
numbers = lambda text: collections.Counter(re.findall(r'\d+(?:\.\d+)?', text))
old_num, new_num = numbers(source_narration), numbers(target_narration)
# 숫자의 값뿐 아니라 출현 횟수도 보존한다. 단순 모형 재계산 검수와 구분한다.
assert old_num == new_num, (old_num - new_num, new_num - old_num)
assert chapters[1]['original'][1] == chapters[1]['paragraphs'][1]
assert chapters[7]['original'][2] == chapters[7]['paragraphs'][2]
assert chapters[9]['original'][2:] == chapters[9]['paragraphs'][2:]
assert len([p for c in chapters for p in c['paragraphs']]) == 54
assert not re.search(r'아닙니다|아님|오해', target_narration)
assert all('<!--' not in p for c in chapters for p in c['paragraphs'])

common = {'source':'outputs/cost-wording-v3/script_cost_v3.md','source_sha256':input_sha,'target':'writer/private-production-v1/script_v4_candidate.md','target_sha256':script_sha}
with (OUT/'script_v4_candidate.md').open('x',encoding='utf-8',newline='\n') as f: f.write(candidate)
dump('changes.json',{
    'revision':'writer-private-production-v1-script-v4-candidate','status':'최종영상용 후보; 독립 QA 대기',**common,
    'scope':'10개 장·54문단·기존 수치와 원 모형·화자 관점 보존. 비용 묶음 설명 및 비교 조건의 직접 표현만 정리.',
    'authorization':'director/two-episode-production-v1/authorization.json','authorization_sha256':sha(AUTH.read_bytes()),
    'changed_paragraphs':len(changes),'unchanged_paragraphs':54-len(changes),
    'preserved':['10개 장 순서와 제목','초기 순자산 2.5억 / 월예산 300만원 / 집 6억 / 10년','집값 연 2% / 원화 총수익 연 6% / 대출 연 4%','모든 기존 금액·수익률·기간·민감도 결과','600만원·100만원·100만원의 설명용 비용 묶음 가정','임대료·보증금 고정 / 보증금 전액 정상 반환','초기·월별 비용 가정과 상품별 세금·운용비용 추가 반영 전','주거 안정에 가치를 두는 10장 화자 관점과 다음 편 예고'],
    'numbers_changed':False,'new_causes_added':False,'research_direction_changed':False,'common_files_modified':False,
    'review_boundary':'숫자 표기 계승만 확인. 지수·표본·계산의 독립 재검증, Claude 검수, 실제 음성·영상 검수는 수행하지 않음.',
    'changes':changes,
})
dump('scene_outline.json',{'revision':'scene-outline-script-v4-candidate',**common,
    'status':'문단별 제안; 공통 scenes.json 미수정',
    'style_basis':'제작_기본가이드.md 및 기존 채널 톤앤매너 계승. 설명 자료와 분위기 소재 구분. 제작 주석·AI 여부·프롬프트는 자산 기록에 남기고 시청자 화면에 불필요한 제작 배지·부정형 면책을 붙이지 않음.',
    'reuse_policy':'동일 대상·동일 의미·동일 수치/기간일 때만 재사용. 같은 차트나 이미지를 무관한 내용에 제목만 바꿔 사용하지 않음. 기존 화면을 실제 확인했다는 기록이 아님.',
    'legacy_mapping_note':'기존 scene_proposals v1의 2·8·10장 문단 앵커 일부는 v3와 다름. 재사용 힌트는 내용 기반이며 공통 장면ID의 확정 변경 제안은 director가 결정.',
    'claim_id_basis':'outputs/script-review-v1/scene_proposals.json의 기존 ID를 해당 의미에 한해 제안. research/facts.json 부재로 새 ID를 확정하지 않음. 기존 QA01은 현재 검수 증거로 승계하지 않음.',
    'chapters':outline_chapters})
dump('narration_handoff.json',{'revision':'script-v4-candidate',**common,'status':'후속 대본 검수 통과 후 무료 TTS 담당이 사용',
    'read_scope':'script_v4_candidate.md의 ## 소제목 아래 54개 본문 문단. 제목·메타데이터·scene_outline 주석은 비낭독.',
    'pronunciation':{'S&P500':'에스 앤드 피 오백','S&P':'에스 앤드 피','ETF':'이 티 에프','원리금균등':'원금과 이자를 합친 같은 금액을 갚는 방식','전용면적':'전용면적; 숫자·면적과 함께 유지','2억5천만원':'이억 오천만 원','600만원':'육백만 원','100만원':'백만 원','6%':'육 퍼센트','4.0%':'사 점 영 퍼센트','1.21배':'일 점 이일 배'},
    'emphasis':['같은 집','같은 예산','설명용 가정','남은 대출','원화 총수익','평가 순자산','조건','주거 안정','보유를 이어갈 수 있는 가격'],
    'preserve_voice_perspective':'10장 화자의 주거 안정 선호·관점과 다음 편 예고 유지. 숫자 나열만 강조하지 않고 비교 조건과 자금 흐름 강조.',
    'subtitle_rule':'숫자·단위·날짜·고유명사를 의미 단위로 보호. 발음 정규화와 화면 표기를 분리하고 원문 연결을 보존.',
    'timing_basis':'estimate; 실제 음성 생성·청취·정렬 미수행','paid_generation_authorized':False})
dump('issue_W4_QA_HANDOFF.json',{'issue_id':'W4-QA-HANDOFF','status':'별도 QA 확인 요청; 오류 판정 아님','scene_ids':['W4-C02-P02','W4-C02-P03','W4-C08-P01','W4-C08-P03','W4-C10-P02'],
    'problem':'기존 지역·기간 실거래 연결 수치와 조건별 결과의 최종 사용 범위는 진행 중인 별도 QA 결과에 연결해야 함.',
    'evidence':'writer는 v3 해당 문단·숫자 출현을 그대로 보존. 원자료·지수·표본·수식을 새로 검수하지 않았으며 최종 미디어도 확인하지 않음.',
    'proposal':'별도 QA가 2장 실거래 집계의 대상·기간·표본·집계방식과 기존 수치 및 8장 조건별 결과를 확인하고 정확한 입력 해시에 검수 기록을 연결. 2%는 보수적 계획 가정, 6%는 영상 조건의 원화 총수익 가정으로 유지.',
    'impact':'QA에서 수정이 필요하면 해당 문단·차트·음성·자막만 영향 추적. 현재 후보에 새 수치·새 원인을 삽입하지 않음.',
    'next_role':'director → 진행 중인 독립 QA; 이후 narration/visual/editor',
    'communication':'peer 직접 메시지 도구 미제공으로 지정 폴더 이슈 파일로 전달'})
dump('checks.json',{'revision':'writer-author-check-v4','review_type':'작성자 범위 보존 검사; 독립 QA와 구분',**common,
    'checks':{'chapter_count_and_order':True,'paragraph_counts_unchanged':True,'narration_paragraph_count':54,
      'numeric_tokens_and_counts_equal':True,'new_numeric_values':[],'removed_numeric_values':[],
      'regional_history_paragraph_verbatim':True,'leverage_paragraph_verbatim':True,'closing_perspective_and_teaser_verbatim':True,
      'cost_amounts_unchanged':True,'illustrative_cost_bundle_explicit':True,'no_negative_warning_keywords':True,
      'annotations_separate_from_narration':True,'source_unchanged_during_build':sha(SRC.read_bytes())==input_sha},
    'metrics':{'source_narration_characters':len(source_narration),'target_narration_characters':len(target_narration),'target_narration_nonspace_characters':len(re.sub(r'\s','',target_narration)),
      'wording_similarity':round(difflib.SequenceMatcher(None,source_narration,target_narration,autojunk=False).ratio(),4)},
    'not_performed':['지수·표본·원자료 재검수','모형·민감도 재계산','독립 Codex/Claude 검수','TTS 생성·청취·음성 정렬','기존 화면 프레임 확인·영상 재생'],
    'next':'지정 후보 해시에 독립 QA와 실제 무료 TTS·최종 미디어 검수 연결'})
dump('handoff.json',{'task_id':'writer-private-production-v1-script-v4','role':'writer','status':'담당 작성 완료; 최종영상용 후보·독립 QA 대기',
    'input_revisions':{'script_cost_v3':input_sha,'authorization':sha(AUTH.read_bytes())},
    'outputs':['script_v4_candidate.md','changes.json','scene_outline.json','narration_handoff.json','checks.json','issue_W4_QA_HANDOFF.json'],
    'affected_scene_ids':[x['scene_id'] for x in changes],
    'checks':[{'check':'10장·54문단·숫자 값과 횟수·결말 핵심 보존','result':'pass','evidence':'checks.json'},{'check':'독립 QA·실제 음성 및 미디어 검수','result':'pending','evidence':'issue_W4_QA_HANDOFF.json'}],
    'open_issue_ids':['W4-QA-HANDOFF'],'next_role':'director → 독립 QA → narration/visual/editor',
    'scope':'지정 writer/private-production-v1/만 작성. 원본·공통 상태·다른 담당 산출물 미수정.'})
print(json.dumps({'status':'created','chapters':len(chapters),'paragraphs':54,'changed_paragraphs':len(changes),'script_sha256':script_sha,'outputs':[p.name for p in OUT.iterdir() if p.suffix in {'.md','.json'}]},ensure_ascii=False))
