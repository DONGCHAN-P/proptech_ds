"""31 scenes: inner visual HTML and native-beat animation descriptions only.

The assembler owns fonts, canvas, captions, chapter inserts, audio and GSAP.
No I/O is performed except reading the two frozen director inputs. IDs are
scene-prefixed; animation targets are bare IDs, not CSS selectors. Money bars
carry their KRW value and scale so the assembled film can audit proportions.
S24/S26 retain their planned purpose and also recap the requested comparisons.
"""
from __future__ import annotations

from functools import lru_cache
from html import escape
import json
from pathlib import Path

EPISODE = Path(__file__).resolve().parents[3]
BLUE, GOLD, GREEN = 'var(--blue)', 'var(--gold)', 'var(--green)'
INK, MUTED, PALE = 'var(--ink)', 'var(--muted)', '#e1e5df'


@lru_cache(maxsize=1)
def _inputs():
    base = EPISODE / 'director/user-recording-v1'
    plan = json.loads((base / 'scene_plan.json').read_text(encoding='utf-8-sig'))
    calc = json.loads((base / 'calculation_check.json').read_text(encoding='utf-8-sig'))
    return {s['scene_id']: s for s in plan['scenes']}, calc


def _money(won):
    """Compact exact display, without introducing fractional rounding."""
    won = int(won)
    eok, rest = divmod(won, 100_000_000)
    man = rest // 10_000
    return (f'{eok}억' if eok else '') + (f'{man:,}만' if man else '') + '원'


class _Scene:
    def __init__(self, sid, timing, assets, plan):
        self.sid, self.timing, self.assets, self.plan = sid, timing, assets, plan
        self.parts, self.animations = [], []

    def id(self, key):
        return f'{self.sid}_{key}'

    def t(self, key, text, x, y, w, size=32, color=INK, weight=400, extra=''):
        return (f'<div id="{self.id(key)}" class="txt" data-text="true" '
                f'style="position:absolute;box-sizing:border-box;left:{x}px;top:{y}px;'
                f'width:{w}px;font-size:{size}px;font-weight:{weight};color:{color};'
                f'line-height:1.26;white-space:normal;{extra}">{escape(str(text))}</div>')

    def r(self, key, x, y, w, h, color, extra='', value=None, scale=None):
        attrs = '' if value is None else f' data-money-won="{int(value)}" data-px-per-won="{scale:.12g}"'
        return (f'<div id="{self.id(key)}" class="shape"{attrs} style="position:absolute;'
                f'box-sizing:border-box;left:{x}px;top:{y}px;width:{w:.4f}px;height:{h}px;'
                f'background:{color};border-radius:3px;transform-origin:left center;{extra}"></div>')

    def add(self, body):
        self.parts.append(body)

    def show(self, key, beat, body):
        self.parts.append(f'<div id="{self.id(key)}" style="position:absolute;inset:0">{body}</div>')
        self.animations.append({'targets': [self.id(key)], 'beat': beat, 'kind': 'show', 'duration': .4})

    def fill(self, key, beat, x, y, w, h, color, value=None, scale=None):
        self.add(self.r(key, x, y, w, h, color, value=value, scale=scale))
        self.animations.append({'targets': [self.id(key)], 'beat': beat, 'kind': 'fill', 'duration': .4})

    def note(self, text):
        self.add(self.t('condition', text, 80, 220, 1760, 25, MUTED))

    def source(self, text):
        self.add(self.t('source', text, 80, 810, 1760, 20, MUTED))

    def node(self, key, title, detail, x, y, w=460, h=172, color=BLUE):
        return (self.r(key + '_base', x, y, w, h, '#ffffff', 'border-radius:18px;box-shadow:0 10px 26px #17334808;')
                + self.r(key + '_edge', x, y, 6, h, color)
                + self.t(key + '_title', title, x + 26, y + 22, w - 50, 34, color, 700)
                + self.t(key + '_detail', detail, x + 26, y + 83, w - 50, 28, MUTED))

    def icon(self,key,kind,x,y,size=80,color=BLUE):
        paths={
          'bank':'M10 28 L40 9 L70 28 Z M17 33V62 M32 33V62 M48 33V62 M63 33V62 M10 69H70',
          'wallet':'M9 24H65V67H9Z M9 24L57 12V24 M46 39H71V55H46Z M55 47H59',
          'calendar':'M13 17H67V69H13Z M13 32H67 M25 10V24 M55 10V24 M26 44H34 M46 44H54 M26 57H34',
          'home':'M8 35L40 10L72 35 M17 30V70H63V30 M33 70V45H49V70',
          'bill':'M18 8H62V72L51 66L40 72L29 66L18 72Z M28 24H52 M28 36H52 M28 48H44',
          'shield':'M40 9L66 19V39Q66 59 40 73Q14 59 14 39V19Z M27 39L36 48L55 29',
          'work':'M10 27H70V68H10Z M28 27V15H52V27 M10 42Q40 59 70 42 M36 47H44',
          'family':'M29 18A9 9 0 1 0 29 36A9 9 0 1 0 29 18 M54 24A7 7 0 1 0 54 38A7 7 0 1 0 54 24 M12 68V55Q12 41 29 41Q44 41 44 55V68 M48 44Q66 42 68 59V68',
          'scale':'M40 12V68 M15 68H65 M13 24H67 M20 24L8 48H32Z M60 24L48 48H72Z',
          'check':'M12 41L30 59L68 20',
        }
        return f'<svg id="{self.id(key)}" viewBox="0 0 80 80" style="position:absolute;left:{x}px;top:{y}px;width:{size}px;height:{size}px" fill="none" stroke="{color}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"><path d="{paths[kind]}"/></svg>'

    def arrow(self,key,x1,y1,x2,y2,color=BLUE):
        # One coordinate system locks the line and arrowhead to their endpoints.
        dx,dy=x2-x1,y2-y1
        import math
        length=math.hypot(dx,dy);ux,uy=dx/length,dy/length
        ax,ay=x2-14*ux,y2-14*uy
        points=f'{ax-8*uy},{ay+8*ux} {x2},{y2} {ax+8*uy},{ay-8*ux}'
        return f'<svg id="{self.id(key)}" viewBox="0 0 1920 1080" style="position:absolute;inset:0;width:100%;height:100%;pointer-events:none"><path d="M{x1} {y1} L{x2} {y2}" stroke="{color}" stroke-width="4" fill="none"/><polyline points="{points}" stroke="{color}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>'

    def house(self, key, x, y, width=260):
        src = self.assets.get('house_cutout_src')
        if src:
            return (f'<img id="{self.id(key)}" src="{escape(str(src), quote=True)}" alt="" '
                    f'style="position:absolute;left:{x}px;top:{y}px;width:{width}px;'
                    f'height:{width * .8664:.3f}px;object-fit:contain">')
        # Identical schematic at every price; footprint conveys no price/area.
        h = width * .80
        return (self.r(key + '_roof', x, y, width, h * .38, INK,
                       'clip-path:polygon(50% 0,100% 100%,0 100%);')
                + self.r(key + '_walls', x + width * .12, y + h * .36,
                         width * .76, h * .62, '#dce6e5')
                + self.r(key + '_door', x + width * .43, y + h * .62,
                         width * .14, h * .36, BLUE))

    def bar(self, key, x, y, equity, loan, px_per_eok=150, h=52):
        scale = px_per_eok / 100_000_000
        ew, lw = equity * scale, loan * scale
        return (self.r(key + '_equity', x, y, ew, h, BLUE, value=equity, scale=scale)
                + self.r(key + '_loan', x + ew, y, lw, h, GOLD, value=loan, scale=scale))

    def loan_note(self):
        self.note('사례 가정 · LTV 70% · 개인 대출한도 4억원 · 기존 대출 0 · 연 4.5% · 30년 원리금균등')


def _s01(b, c):
    b.add(b.t('question', '돈을 모은 다음에는?', 80, 285, 1250, 64, weight=700))
    b.add(b.r('baseline', 140, 700, 1640, 3, '#ced6d3'))
    for i, value in enumerate((1, 2, 5, 10)):
        x, y = 160 + i * 420, 595 - i * 83
        # Equal-size cash tokens trace a sequence, not a quantitative bar chart.
        body = b.r(f'step{i}', x, y, 270, 100, '#e4eceb')
        body += b.t(f'value{i}', f'{value}억', x + 25, y + 15, 220, 48, BLUE, 700)
        b.show(f'cash{i}', 1 if i == 0 else 2, body)
    b.add(b.t('cash_label', '모아둔 현금', 140, 742, 500, 30, MUTED))


def _s02(b, c):
    b.show('balance', 1, b.node('bank', '내 통장', '모아둔 현금', 80, 380, 420, 240)
           + b.t('gap', '?', 545, 435, 140, 88, GOLD, 700))
    for i, price in enumerate(('6억', '10억', '15억')):
        x = 735 + i * 365
        b.add(b.house(f'house{i}', x, 320, 245))
        b.show(f'listing{i}', 2, b.t(f'price{i}', price, x, 590, 290, 58, weight=700))
    b.add(b.t('listings_label', '매물의 가격과 내 자금 사이', 735, 714, 1060, 36, MUTED))


def _s03(b, c):
    b.add(b.t('price_label', '집값의 구성', 80, 290, 600, 34, weight=700))
    b.show('funding', 1, b.node('equity', '내 돈', '집값에 넣는 자기자금', 80, 355, 570)
           + b.node('loan', '빌린 돈', '앞으로 갚을 원금과 이자', 680, 355, 570, color=GOLD))
    b.show('scope', 2, b.node('reserve', '따로 남길 돈', '세금 · 이사 · 비상금', 80, 568, 570, color=MUTED)
           + b.node('monthly', '매달 갚을 돈', '월 원리금과 생활 예산', 680, 568, 570, color=GREEN))
    b.show('conditions', 3, b.t('condition_title', '현금 1~5억원의 계산 예시', 1320, 345, 500, 38, weight=700)
           + b.t('condition_list', '소득 / 기존 대출 / 지역 / 월 여력', 1320, 465, 490, 34, MUTED)
           + b.t('condition_check', '개인 조건에 맞춰 확인', 1320, 650, 490, 34, GREEN, 600))


def _s04(b, c):
    b.add(b.t('calendar_title', '잔금일에 쓸 수 있는 돈', 80, 295, 1400, 56, weight=700))
    b.add(b.r('calendar', 100, 470, 1670, 4, '#c4ceca'))
    for i in range(8):
        b.add(b.r(f'tick{i}', 150 + i * 225, 452, 2, 40, '#c4ceca'))
    b.show('settlement', 1, b.r('settlement_line', 1460, 380, 4, 340, GOLD)
           + b.t('settlement_label', '잔금일', 1390, 320, 350, 42, GOLD, 700)
           + b.t('available', '현금 사용 가능', 1250, 725, 500, 34, weight=600))
    b.show('deposit', 2, b.node('return', '전세보증금 반환일', '입금 날짜와 잔금 일정 맞추기', 285, 545, 690)
           + b.arrow('return_to_settlement',975,631,1462,631,BLUE))


def _s05(b, c):
    b.add(b.r('receipt_paper', 180, 290, 1110, 490, '#ffffff')
          + b.t('receipt_title', '집값 외 거래비용', 225, 315, 980, 42, weight=700))
    rows = [('취득세 · 지방교육세', 1), ('중개보수', 2),
            ('법무사 · 채권 할인 부담 · 인지세', 3)]
    for i, (text, beat) in enumerate(rows):
        y = 420 + i * 105
        b.show(f'item{i}', beat, b.t(f'item_label{i}', text, 225, y, 980, 36)
               + b.r(f'item_rule{i}', 225, y + 67, 1000, 2, PALE))
    b.add(b.t('outside_price', '집값', 1410, 350, 380, 56, BLUE, 700)
          + b.t('plus', '+', 1520, 445, 100, 80, GOLD)
          + b.t('outside_cost', '거래비용', 1360, 565, 440, 50, GOLD, 700))
    b.source('세금·중개보수·등기 비용은 주택과 거래 조건별로 견적 확인')


def _s06(b, c):
    b.add(b.r('room_floor', 100, 685, 1110, 26, '#dbe4df')
          + b.r('room_wall', 100, 300, 5, 410, '#bdcdc6'))
    b.show('moving', 1, b.r('box', 170, 500, 260, 185, '#e1d3b7')
           + b.r('tape', 286, 500, 25, 185, GOLD)
           + b.t('box_label', '이사 · 수리', 150, 735, 440, 33, MUTED))
    b.show('furniture', 2, b.r('sofa_back', 590, 480, 440, 140, '#bbd3cd')
           + b.r('sofa_seat', 570, 605, 480, 72, GREEN)
           + b.t('furniture_label', '가전 · 가구', 625, 735, 480, 33, MUTED))
    b.show('emergency', 3, b.node('emergency_box', '남겨둘 비상금', '입주 후 생활을 위한 별도 예산', 1290, 330, 520, 240, GREEN))
    b.show('estimate', 4, b.t('estimate_label', '항목별 견적으로 채우기', 1290, 625, 520, 34, weight=600)
           + b.t('estimate_blank', '이사  ______   가전  ______', 1290, 695, 520, 30, MUTED))


def _s07(b, c):
    b.note('원고에서 정한 준비금 예산 · 세금·거래비용·이사·가전·비상금 포함')
    b.add(b.t('legend', '파랑: 집값 투입금     회색: 별도 준비금', 650, 280, 1150, 28, MUTED))
    for i, row in enumerate(c['rows']):
        y, scale = 360 + i * 80, 200 / 100_000_000
        ew = row['equity_won'] * scale
        body = b.t(f'cash{i}', f"현금 {i+1}억", 90, y - 5, 280, 34, weight=600)
        body += b.r(f'equity{i}', 390, y, ew, 42, BLUE, value=row['equity_won'], scale=scale)
        body += b.r(f'reserve{i}', 390 + ew, y, row['reserve_won'] * scale, 42,
                    '#c4ccc7', value=row['reserve_won'], scale=scale)
        body += b.t(f'reserve_label{i}', f"준비금 {_money(row['reserve_won'])}", 1430, y, 410, 30, MUTED)
        b.show(f'row{i}', i + 1, body)
    b.show('equity_summary', 6, b.t('equity_summary_text', '집값 투입금  0.8 / 1.7 / 2.6 / 3.5 / 4.4억원',
                                  390, 772, 1430, 34, BLUE, 700))


def _s08(b, c):
    b.note('설명 가정 · 집값 = 담보평가액 · LTV 70%')
    b.show('house_value', 1, b.house('house', 100, 310, 370)
           + b.t('collateral', '담보평가액 5억원', 80, 690, 610, 44, weight=700))
    b.add(b.r('collateral_track', 720, 405, 1000, 100, PALE))
    b.show('loan', 2, b.r('loan_bar', 720, 405, 700, 100, GOLD, value=350_000_000, scale=2e-6)
           + b.t('loan_text', '대출 70% · 3억5000만원', 720, 555, 1080, 43, GOLD, 700))
    b.show('equity', 3, b.r('equity_bar', 1420, 405, 300, 100, BLUE, value=150_000_000, scale=2e-6)
           + b.t('equity_text', '내 돈 30% · 1억5000만원', 720, 650, 1080, 43, BLUE, 700))


def _s09(b, c):
    b.note('DSR = 연간 모든 대출 원리금 상환액 ÷ 연 소득 · 구조 설명')
    b.add(b.node('income', '연 소득', '상환능력을 판단하는 기준', 100, 320, 460, 260))
    b.show('repayment', 1, b.t('fraction_top', '1년간 갚는 원금 + 이자', 720, 320, 1070, 48, weight=700)
           + b.r('fraction_line', 720, 402, 1000, 3, INK)
           + b.t('fraction_bottom', '연 소득', 1030, 430, 550, 44, BLUE, 700))
    b.show('existing', 2, b.node('old_debt', '기존 신용대출 등', '다른 빚의 원리금도 함께 반영', 680, 580, 550, 185, GOLD))
    b.show('new_capacity', 3, b.node('new_debt', '새 주담대', '소득과 기존 빚에 따라 한도 조정', 1270, 580, 550, 185, GREEN))


def _s10(b, c):
    b.add(b.t('common', '금리가 오를 가능성까지 살펴보기', 80, 290, 1740, 50, weight=700))
    b.show('screening', 1, b.node('screening_node', '심사 경로', '스트레스금리 반영 → 상환능력 점검', 100, 420, 790, 260, GOLD))
    b.show('payment', 2, b.node('payment_node', '실제 납부 경로', '약정 대출금리 → 매달 내는 원리금', 990, 420, 790, 260, GREEN))
    b.source('금융위원회 스트레스 DSR 설명 · 심사 기준과 약정금리의 역할 구분')


def _s11(b, c):
    b.note('일반 차주 · 무주택자 / 처분조건부 1주택자의 주택구입 목적 기준')
    for i, (label, value, beat) in enumerate((('비규제지역', 70, 1), ('규제지역', 40, 2))):
        y = 350 + i * 165
        b.show(f'region{i}', beat, b.t(f'region_label{i}', label, 100, y, 440, 41, weight=600)
               + b.r(f'ltv_bar{i}', 600, y + 4, value * 12, 62, BLUE if i == 0 else GOLD)
               + b.t(f'ltv_value{i}', f'{value}%', 1530, y - 4, 280, 60, weight=700))
    b.show('first_purchase', 3, b.t('first_purchase_text', '생애최초 구입 → 주택 보유 이력과 별도 요건 확인',
                                 100, 730, 1700, 36, GREEN, 600))
    b.source('적용 시점 2026-10-26 · 금융위원회 LTV 기준 · 지역·상품·차주별 최종 요건 확인')


def _s12(b, c):
    b.add(b.t('assumption_title', '이후 계산에서 고정할 조건', 80, 290, 1700, 48, weight=700))
    b.show('ltv', 1, b.node('ltv_gate', 'LTV 70%', '담보평가액 = 집값', 80, 390, 520, 220))
    b.show('cap', 2, b.node('cap_gate', '개인 대출한도 4억원', '소득·심사 조건 / 기존 대출 0', 650, 390, 560, 220, GOLD))
    b.show('repayment', 3, b.node('repayment_gate', '월 원리금 계산', '예시 연 4.5% / 30년 원리금균등', 1260, 390, 580, 220, GREEN))
    b.add(b.t('additional_limits', '사례 계산에서는 지역·상품·은행의 추가 제한이 없는 것으로 가정',
              80, 705, 1740, 31, MUTED))


def _s13(b, c):
    r = c['rows'][0]
    b.loan_note()
    b.add(b.t('cash_label', '보유현금', 110, 290, 480, 30, MUTED)
          + b.t('cash', '1억원', 110, 340, 480, 80, weight=700)
          + b.r('cash_track', 110, 475, 250, 50, PALE))
    b.show('reserve', 1, b.r('reserve_bar', 310, 475, 50, 50, '#c4ccc7', value=20_000_000, scale=2.5e-6)
           + b.t('reserve_label', '별도 준비금 2000만원', 110, 575, 620, 34, MUTED))
    b.show('equity', 2, b.r('equity_bar', 110, 475, 200, 50, BLUE, value=80_000_000, scale=2.5e-6)
           + b.t('equity_label', '집값 투입금', 430, 325, 450, 30, MUTED)
           + b.t('equity_value', '8000만원', 430, 375, 450, 60, BLUE, 700))
    b.show('division', 3, b.t('formula', '8000만원 ÷ 30%', 430, 650, 490, 39, weight=600)
           + b.t('ceiling', '계산상 약 2억6667만원', 430, 712, 520, 29, MUTED))
    b.add(b.r('divider', 970, 290, 2, 470, '#d4dad4'))
    b.show('result', 4, b.t('result_label', '이번 예시의 집값', 1030, 325, 760, 30, MUTED)
           + b.t('price', _money(r['price_won']), 1030, 390, 790, 68, weight=700)
           + b.bar('price_bar', 1030, 520, r['equity_won'], r['loan_won'], 250, 64)
           + b.t('result_equity', '내 돈 8000만원', 1030, 625, 730, 34, BLUE, 600)
           + b.t('result_loan', '대출 1억8600만원', 1030, 690, 730, 34, GOLD, 600))


def _s14(b, c):
    r = c['rows'][0]
    b.loan_note()
    b.show('funding', 1, b.t('price', '집값 2억6600만원', 100, 310, 1030, 50, weight=700)
           + b.bar('funding_bar', 100, 415, r['equity_won'], r['loan_won'], 300, 70)
           + b.t('funding_labels', '내 돈 8000만원 + 대출 1억8600만원', 100, 525, 1100, 34))
    b.show('monthly', 2, b.node('bill', '월 원리금 약 94만원', '관리비 · 보유세 · 생활비 별도', 1230, 305, 580, 270, GREEN))
    b.show('options', 3, b.t('choices', '탐색 지역 확대   /   필요한 면적 조정   /   추가 저축   /   다른 주거 선택',
                           100, 700, 1710, 34, BLUE, 600))


def _s15(b, c):
    r = c['rows'][1]
    b.loan_note()
    b.add(b.t('cash_title', '보유현금 2억원', 100, 300, 1100, 54, weight=700))
    b.show('reserve', 1, b.t('reserve_text', '준비금 3000만원 → 집값 투입금 1억7000만원', 100, 395, 1700, 38, BLUE, 600))
    b.show('price', 2, b.bar('price_bar', 100, 500, r['equity_won'], r['loan_won'], 190, 70)
           + b.t('price_total', '집값 5억6600만원', 1260, 490, 570, 52, weight=700)
           + b.t('loan_label', '대출 3억9600만원 · 개인 한도 4억원 이내', 100, 615, 1700, 35, GOLD, 600))
    b.show('monthly', 3, b.t('monthly_text', '월 원리금 약 201만원', 100, 725, 1650, 50, GREEN, 700))


def _s16(b, c):
    insight = c['insights']
    b.note('현금 1억 → 2억원 · 같은 LTV 70% 사례의 변화')
    b.add(b.t('before_after', '집값 예산 2.66억 → 5.66억원', 80, 295, 1700, 50, weight=700))
    b.show('increase', 1, b.t('increase_title', '집값 예산 증가', 80, 410, 570, 36, MUTED)
           + b.t('increase_value', '+3억원', 80, 470, 570, 86, weight=700))
    scale = 350 / 100_000_000
    b.show('composition', 2,
           b.r('equity_increase', 720, 440, 315, 90, BLUE, value=insight['equity_increase_won'], scale=scale)
           + b.r('loan_increase', 1035, 440, 735, 90, GOLD, value=insight['loan_increase_won'], scale=scale)
           + b.t('equity_label', '자기자금 +0.9억원', 720, 585, 1050, 43, BLUE, 700)
           + b.t('loan_label', '대출 +2.1억원', 720, 665, 1050, 43, GOLD, 700)
           + b.t('insight', '증가분의 70%는 더 빌린 돈', 720, 745, 1080, 34, MUTED))


def _s17(b, c):
    b.note('같은 현금 2억원 · 준비금 3000만원 · 집값 투입 자기자금 1억7000만원')
    for i, (loan, price, label, beat) in enumerate(((396_000_000, 566_000_000, '앞선 사례', 1),
                                                  (200_000_000, 370_000_000, '내 한도가 2억원이면', 2))):
        y = 340 + i * 235
        b.show(f'option{i}', beat, b.t(f'label{i}', label, 100, y, 730, 34, MUTED)
               + b.bar(f'bar{i}', 100, y + 65, 170_000_000, loan, 200, 60)
               + b.t(f'price{i}', f'집값 {_money(price)}', 1330, y + 45, 500, 45, weight=700)
               + b.t(f'loan{i}', f'대출 {_money(loan)}', 620, y + 145, 650, 33, GOLD, 600))


def _s18(b, c):
    b.loan_note()
    b.show('equity', 1, b.t('cash', '현금 3억원 − 준비금 4000만원', 100, 300, 1600, 39)
           + b.t('equity_text', '집값 투입금 2억6000만원', 100, 385, 1600, 51, BLUE, 700))
    b.show('cap', 2, b.node('cap_gate', '개인 대출한도 4억원', '이 사례에서 먼저 걸리는 한도', 1210, 480, 610, 220, GOLD)
           + b.r('cap_line', 1096, 480, 4, 210, GOLD))
    b.show('total', 3, b.bar('total_bar', 100, 510, 260_000_000, 400_000_000, 150, 66)
           + b.t('sum', '2.6억 + 4억 = 6.6억원', 100, 620, 1050, 52, weight=700))
    b.show('gate_choice', 4, b.t('gate_choice_text', '담보비율 70%보다 개인별 대출한도가 먼저 제한', 100, 740, 1700, 36, GOLD, 600))


def _s19(b, c):
    b.loan_note()
    b.add(b.t('legend', '파랑: 집값 투입 자기자금     골드: 사용 대출', 100, 280, 1700, 28, MUTED))
    # Independent loan column: same origin and exactly the same 4억원 length.
    for i, r in enumerate(c['rows'][2:]):
        y = 390 + i * 130
        body = b.t(f'cash{i}', f'현금 {i+3}억', 100, y - 28, 270, 34, weight=600)
        body += b.r(f'equity{i}', 380, y, r['equity_won'] * 120 / 1e8, 45, BLUE,
                    value=r['equity_won'], scale=1.2e-6)
        body += b.r(f'loan{i}', 965, y, 480, 45, GOLD, value=400_000_000, scale=1.2e-6)
        body += b.t(f'loan_label{i}', '4억원', 1110, y - 45, 300, 30, GOLD, 600)
        body += b.t(f'price{i}', _money(r['price_won']), 1495, y - 15, 330, 47, weight=700)
        if i == 0:
            b.add(body)
        else:
            b.show(f'row{i}', i, body)
    b.add(b.r('loan_stop', 1445, 320, 4, 400, GOLD))
    b.show('monthly', 3, b.t('monthly_text', '세 사례 모두 월 원리금 약 203만원', 100, 750, 1690, 44, GREEN, 700))


def _choice_pair(b, prefix, y=310, beats=(1, 2, 3), compact=False):
    """Same-size house markers; the money bars alone encode price differences."""
    for i, (price, loan, monthly) in enumerate(((840_000_000, 400_000_000, 203),
                                               (700_000_000, 260_000_000, 132))):
        x = 100 + i * 890
        if not compact:
            b.add(b.house(f'{prefix}_house{i}', x, y, 200))
        tx = x if compact else x + 255
        b.show(f'{prefix}_price{i}', beats[0], b.t(f'{prefix}_price_text{i}', _money(price), tx, y + 5, 570, 50, weight=700))
        by = y + (140 if compact else 225)
        b.show(f'{prefix}_funding{i}', beats[1], b.bar(f'{prefix}_bar{i}', x, by, 440_000_000, loan, 88, 42)
               + b.t(f'{prefix}_loan{i}', f'내 돈 4.4억 + 대출 {loan / 1e8:g}억', x, by + 65, 810, 30, GOLD, 600))
        b.show(f'{prefix}_monthly{i}', beats[2], b.t(f'{prefix}_monthly_text{i}', f'월 약 {monthly}만원', tx, y + (70 if compact else 105),
                                                  560, 39, GREEN, 700))


def _s20(b, c):
    b.note('같은 현금 5억원 · 준비금 6000만원 · 연 4.5% · 30년 원리금균등')
    _choice_pair(b, 'choice')
    b.show('saving', 3, b.t('saving_text', '대출 1억4000만원 감소 → 월 원리금 약 71만원 절감',
                          100, 735, 1700, 40, GREEN, 700))


def _s21(b, c):
    cost = c['cost_example']
    b.note('6.6억원 · 일반적인 1주택 취득 · 전용 85㎡ 이하 · 감면 없음 · 일반과세 중개사')
    b.add(b.r('paper', 100, 290, 910, 500, '#ffffff')
          + b.t('receipt_title', '거래비용 계산서', 135, 310, 800, 37, weight=700))
    b.show('tax', 1, b.t('tax_label', '취득세', 135, 385, 440, 32)
           + b.t('tax_value', '924만원', 650, 385, 340, 34, weight=600)
           + b.t('edu_label', '지방교육세', 135, 441, 440, 32)
           + b.t('edu_value', '92만4000원', 650, 441, 340, 34, weight=600)
           + b.t('tax_sum', '세금 소계 1016만4000원', 135, 510, 830, 35, weight=700))
    b.show('broker', 2, b.t('broker_label', '중개보수·부가세', 135, 580, 500, 32)
           + b.t('broker_value', '290만4000원', 650, 580, 340, 34, weight=700))
    b.show('sum', 3, b.t('sum_label', '두 항목 합계', 135, 705, 440, 33, weight=600)
           + b.t('sum_value', '1306만8000원', 615, 705, 380, 37, weight=700))
    b.add(b.t('reserve_title', '별도 준비금 4000만원', 1070, 310, 750, 43, weight=700)
          + b.r('reserve_track', 1070, 585, 720, 48, PALE))
    b.fill('cost_bar', 3, 1070, 585, 235.224, 48, GOLD, cost['total_won'], 1.8e-5)
    b.show('remainder', 4, b.t('remainder_label', '다른 항목에 배분할 잔여', 1070, 405, 750, 31, MUTED)
           + b.t('remainder_value', '2693만2000원', 1070, 465, 750, 57, GREEN, 700)
           + b.r('remainder_bar', 1305.224, 585, 484.776, 48, GREEN,
                 value=cost['unallocated_remainder_won'], scale=1.8e-5)
           + b.t('allocation', '등기 · 이사 · 수리 · 가전 · 가구 · 비상금', 1070, 680, 750, 32, GREEN, 600))
    b.show('broker_basis', 5, b.t('broker_basis_text', '보수 상한요율 0.4% · VAT 10% 가정 · 상한 안에서 협의', 135, 642, 850, 24, MUTED))
    b.source('계산 근거: 지방세법 제11·151조 · 서울시 중개보수 요율표 · 나머지 항목은 개별 견적')


def _s22(b, c):
    b.note('같은 준비금 · 개인 대출한도 4억원 · 집값 = 담보평가액 · 금액 단위: 억원')
    b.show('legend', 1, b.t('legend_text', 'LTV 70%  파랑     LTV 40%  골드', 580, 280, 1200, 30, MUTED))
    for i, r in enumerate(c['rows']):
        y = 370 + i * 83
        b.add(b.t(f'cash{i}', f'현금 {i+1}억', 90, y, 280, 33, weight=600))
        scale = 120 / 100_000_000
        high, low = r['price_won'], r['LTV40_price_won']
        b.add(b.r(f'high{i}', 400, y, high * scale, 24, BLUE, value=high, scale=scale))
        body = b.r(f'low{i}', 400, y + 32, low * scale, 24, GOLD, value=low, scale=scale)
        body += b.t(f'values{i}', f'{high/1e8:g}  /  {low/1e8:g}', 1470, y + 3, 350, 34, weight=700)
        b.show(f'comparison{i}', i + 2, body)


def _s23(b, c):
    b.add(b.t('question', '내게 적용되는 조건부터', 80, 285, 1700, 54, weight=700))
    b.show('history', 1, b.node('history_node', '주택 보유 이력', '생애최초 해당 여부 / 처분 조건', 100, 410, 750, 240))
    b.show('property', 2, b.node('property_node', '대상 주택과 대출 상품', '정확한 주소 / 담보평가 / 상품 요건', 980, 410, 820, 240, GOLD)
           + b.t('verify', '시·도 이름보다 해당 주택과 차주 조건을 구체적으로 확인', 100, 730, 1700, 35, GREEN, 600))


def _s24(b, c):
    b.note('상담 → 담보·상품 확인 → 최종 실행 조건 확인 → 계약 전 자금 일정 협의')
    steps = [('현금 확정', '잔금일 현금 − 준비금'), ('은행 상담', '인정소득 · 기존 채무'),
             ('주택 확인', '담보평가 · 적용 LTV'), ('계약 전 검토', '실행 조건 · 자금 일정')]
    for i, (title, detail) in enumerate(steps):
        b.show(f'step{i}', i + 1, b.node(f'node{i}', title, detail, 80 + i * 445, 330, 420, 210,
                                        GREEN if i == 3 else BLUE))
    # Requested LTV recap supplements, rather than replaces, the planned flow.
    b.show('ltv_recap', 3, b.t('ltv_recap_title', '현금 2억 · 준비금 3000만원이면', 100, 600, 1680, 34, MUTED)
           + b.t('ltv70', 'LTV 70% → 집값 5.66억원', 100, 670, 820, 40, BLUE, 700)
           + b.t('ltv40', 'LTV 40% → 집값 2.83억원', 990, 670, 820, 40, GOLD, 700))
    b.show('final_check', 4, b.t('final_check_text', '상담 금액과 최종 실행 금액을 구체적으로 대조', 100, 755, 1700, 32, GREEN, 600))


def _s25(b, c):
    b.add(b.t('monthly_question', '월 200만원을 내고도 생활이 이어질까?', 80, 290, 1730, 52, weight=700))
    b.show('repayment', 1, b.node('monthly_node', '월 원리금', '내가 편하게 갚을 수 있는 범위', 100, 410, 520, 245, GOLD))
    b.show('living', 2, b.node('living_node', '현재 생활 예산', '생활비 · 교육비 · 부모님 지원', 680, 410, 530, 245, BLUE))
    b.show('future', 3, b.node('future_node', '예정된 변화', '출산 · 이직 · 소득 공백에 대비', 1270, 410, 550, 245, GREEN)
           + b.t('budget_rule', '월 소득 − 원리금 − 생활비 − 계획 저축 = 남는 여력', 100, 735, 1710, 38, GREEN, 600))


def _s26(b, c):
    b.note('현금 5억 · 준비금 6000만원 · 예시 연 4.5% · 30년 원리금균등')
    # Recap the actual choices, while preserving this scene's resilience check.
    _choice_pair(b, 'resilience', y=295, beats=(1, 1, 1), compact=True)
    b.show('rate_test', 1, b.t('rate_test_text', '금리 상승 → 원리금 부담 점검', 100, 550, 820, 33, GOLD, 600))
    b.show('income_test', 2, b.t('income_test_text', '소득 감소 → 생활·저축 예산 점검', 990, 550, 820, 33, BLUE, 600))
    b.show('buffer', 3, b.t('saving', '7억 선택 시 월 약 71만원의 여유', 100, 655, 1700, 54, GREEN, 700)
           + b.t('test_result', '지금 소득으로 원리금·생활비·비상 예산을 유지할 수 있는지 확인', 100, 755, 1720, 32, MUTED))


def _s27(b, c):
    b.loan_note()
    b.add(b.t('col_cash', '보유현금', 100, 285, 330, 31, MUTED)
          + b.t('col_funding', '집값 투입금 + 사용 대출', 440, 285, 1000, 31, MUTED)
          + b.t('col_price', '예시 집값', 1510, 285, 320, 31, MUTED))
    for i, r in enumerate(c['rows']):
        y = 365 + i * 85
        b.show(f'row{i}', i + 1, b.t(f'cash{i}', f'{i+1}억원', 100, y, 300, 38, weight=600)
               + b.bar(f'bar{i}', 440, y + 4, r['equity_won'], r['loan_won'], 115, 46)
               + b.t(f'price{i}', f"{r['price_won']/1e8:g}억원", 1510, y - 2, 320, 43, weight=700))
    b.source('회색 준비금은 제외한 집값 투입 자기자금 · 모든 금액 막대는 동일 축척')


def _s28(b, c):
    src = b.assets.get('budget_cutout_src')
    if src:
        b.add(f'<img id="{b.id("notebook")}" src="{escape(str(src), quote=True)}" alt="" '
              'style="position:absolute;left:90px;top:370px;width:520px;height:347px;object-fit:contain">')
    else:
        b.add(b.r('notebook_paper', 110, 340, 450, 400, '#ffffff')
              + b.t('notebook_title', '내 집 예산', 160, 410, 350, 46, BLUE, 700))
    rows = [('집값 투입 자기자금', '잔금현금 ______ − 준비금 ______'),
            ('확인한 대출', '은행·주택 조건 확인 금액 ______'),
            ('매달 갚을 수 있는 돈', '월 원리금 여력 ______')]
    for i, (title, blank) in enumerate(rows):
        b.show(f'field{i}', i + 1, b.node(f'budget_field{i}', title, blank, 690, 295 + i * 167, 1110, 145,
                                         GREEN if i == 2 else BLUE))


def _s29(b, c):
    b.show('opinion', 1, b.t('opinion_label', '화자의 정책 해석', 100, 290, 1650, 38, GOLD, 700))
    b.show('policy', 2, b.node('demand', '수요 관리', '과도한 차입 투자 수요 억제', 100, 380, 800, 200, GOLD)
           + b.node('support', '청년·실수요 지원', '지원 대상과 조건을 구분', 1000, 380, 800, 200, BLUE))
    b.show('borrower', 3, b.t('borrower_text', '실거주도 차주·주택별 대출 조건 확인', 100, 635, 1700, 36, weight=600))
    b.show('holding', 4, b.t('holding_text', '가격 변동 위험 + 세금 + 유지비', 100, 720, 1700, 43, GREEN, 700))


def _s30(b, c):
    b.add(b.house('home', 100, 340, 350))
    b.show('life', 1, b.node('commute', '출퇴근', '일자리와 이동 동선', 550, 310, 390, 180)
           + b.node('family', '가족 계획', '필요한 생활 공간', 980, 310, 390, 180)
           + b.node('area', '면적', '실제로 필요한 크기', 1410, 310, 410, 180))
    b.show('monthly', 2, b.t('monthly_link', '월 상환액과 생활 예산 안에서 선택', 550, 570, 1250, 49, GREEN, 700))
    b.show('options', 3, b.t('options_text', '지금 매수     /     더 준비하기     /     임차로 지내기', 550, 725, 1270, 34, BLUE, 600))


def _s31(b, c):
    b.add(b.t('next', '다음 편 · 같은 가격대, 다른 선택', 100, 285, 1660, 46, weight=700))
    b.show('homes', 1, b.house('home_a', 150, 390, 240) + b.house('home_b', 690, 390, 240)
           + b.t('choice_a', '입지 A', 190, 615, 340, 36, BLUE, 700)
           + b.t('choice_b', '입지 B', 730, 615, 340, 36, BLUE, 700))
    b.show('same_price', 2, b.t('same_price_text', '같은 5억대 · 같은 7억대', 100, 700, 1000, 40, GOLD, 700)
           + b.t('route_a', '통근 동선 / 생활 시설', 100, 760, 500, 28, MUTED)
           + b.t('route_b', '입지와 단지를 함께 비교', 650, 760, 500, 28, MUTED))
    b.show('cta', 3, b.node('write', '먼저 내 예산 적어보기', '자기자금 ______\n확인한 대출 ______\n월 상환 여력 ______',
                          1220, 390, 600, 350, GREEN).replace('white-space:normal;', 'white-space:pre-line;'))


def _s03(b,c):
    b.add(b.house('resident_home',815,310,280))
    b.add(b.t('house_total','집값',860,560,260,44,weight=700))
    b.show('funding',1,b.icon('cash_icon','wallet',175,350,104)
        +b.t('cash_label','내 돈',315,340,370,52,BLUE,700)
        +b.t('cash_detail','집값에 넣는 자기자금',315,420,430,29,MUTED)
        +b.arrow('cash_to_home',650,450,805,450)
        +b.icon('bank_icon','bank',1290,350,104,GOLD)
        +b.t('bank_label','빌린 돈',1420,340,380,52,GOLD,700)
        +b.t('bank_detail','갚을 원금과 이자',1420,420,380,29,MUTED)
        +b.arrow('loan_to_home',1270,450,1120,450,GOLD))
    b.show('scope',2,b.r('reserve_zone',100,650,800,135,'#e5ece8','border-radius:22px;')
        +b.icon('shield_icon','shield',125,678,68,GREEN)
        +b.t('reserve_label','따로 남길 돈',220,674,640,34,GREEN,700)
        +b.t('reserve_detail','세금 · 이사 · 가전 · 비상금',220,727,640,27,MUTED)
        +b.r('monthly_zone',1000,650,800,135,'#e7edf5','border-radius:22px;')
        +b.icon('bill_icon','bill',1025,678,68)
        +b.t('monthly_label','매달 갚을 돈',1120,674,640,34,BLUE,700)
        +b.t('monthly_detail','원리금 + 생활비를 함께 계산',1120,727,640,27,MUTED))
    b.show('conditions',3,b.t('conditions_text','현금 1~5억원의 사례 · 소득 / 기존 대출 / 지역 / 월 여력',100,243,1700,29,MUTED))

def _s09(b,c):
    b.note('DSR = 연간 모든 대출 원리금 상환액 ÷ 연 소득')
    b.add(b.icon('income_icon','work',155,355,120))
    b.add(b.t('income_label','연 소득',120,530,420,49,BLUE,700))
    b.add(b.arrow('income_to_capacity',520,470,700,470))
    b.show('repayment',1,b.r('denominator',740,550,1050,115,'#e4ebf5','border-radius:20px;')
        +b.t('denominator_text','연 소득',740,577,1050,44,BLUE,700,extra='text-align:center;')
        +b.r('fraction',740,523,1050,4,INK)
        +b.t('numerator','1년간 갚는 원금 + 이자',740,370,1050,46,weight=700,extra='text-align:center;')
        +b.t('period','소득에 비해 얼마나 갚는가',100,737,1650,40,GREEN,700))
    b.show('existing',2,b.icon('old_icon','bill',800,440,58,GOLD)
        +b.t('old_label','기존 대출',880,448,350,32,GOLD,700))
    b.show('new_capacity',3,b.icon('new_icon','home',1285,440,58,GREEN)
        +b.t('new_label','새 주담대',1365,448,350,32,GREEN,700)
        +b.t('plus','+',1218,443,80,40,MUTED))

def _s10(b,c):
    b.add(b.t('common','같은 대출, 두 가지 금리의 역할',100,270,1700,48,weight=700))
    b.add(b.r('left_panel',100,360,800,390,'#ece8dd','border-radius:24px;'))
    b.add(b.r('right_panel',1020,360,800,390,'#e4ece8','border-radius:24px;'))
    b.add(b.icon('screen_icon','shield',150,390,96,GOLD)+b.icon('payment_icon','bill',1070,390,96,GREEN))
    b.add(b.t('left_title','심사할 때',280,405,570,48,GOLD,700)+b.t('right_title','갚을 때',1200,405,570,48,GREEN,700))
    b.show('screening',1,b.t('left_rate','스트레스금리 반영',160,540,690,40,weight=700)
        +b.arrow('left_down',490,605,490,650,GOLD)+b.t('left_result','상환능력 점검',265,680,590,34,GOLD,600))
    b.show('payment',2,b.t('right_rate','약정 대출금리',1080,540,690,40,weight=700)
        +b.arrow('right_down',1410,605,1410,650,GREEN)+b.t('right_result','매달 납부할 원리금',1175,680,590,34,GREEN,600))
    b.source('금융위원회 스트레스 DSR 설명 · 심사 기준과 약정금리')

def _s12(b,c):
    b.add(b.house('model_home',140,350,370))
    b.add(b.t('scenario','오늘 계산의 설정',100,735,650,37,weight=700))
    specs=[('LTV','70%','담보평가액 = 집값','home',BLUE,1),
           ('개인 대출한도','4억원','소득·심사 조건 / 기존 대출 0','bank',GOLD,2),
           ('월 원리금 계산','연 4.5% · 30년','원리금균등 상환','calendar',GREEN,3)]
    for i,(title,value,detail,icon,color,beat) in enumerate(specs):
        y=285+i*165
        b.add(b.r(f'rail{i}',650,y,1160,145,'#ffffff','border-radius:20px;'))
        b.add(b.icon(f'icon{i}',icon,680,y+30,78,color))
        b.add(b.t(f'label{i}',title,800,y+22,930,30,MUTED))
        b.show(f'spec{i}',beat,b.t(f'value{i}',value,800,y+62,600,49,color,700)
               +b.t(f'detail{i}',detail,1350,y+65,420,27,MUTED))
    b.source('사례 조건 고정 · 지역·상품·은행의 추가 제한이 없는 조건으로 계산')

def _s23(b,c):
    b.add(b.t('question','내게 적용되는 대출 조건',100,275,1700,50,weight=700))
    b.add(b.r('left',100,380,750,390,'#e5ecf6','border-radius:26px;')
          +b.r('right',1000,380,800,390,'#eee8d9','border-radius:26px;'))
    b.add(b.icon('history_icon','wallet',150,420,106)+b.icon('property_icon','home',1050,420,106,GOLD))
    b.show('history',1,b.t('history_title','나의 보유 이력',300,440,500,43,BLUE,700)
        +b.t('history_detail','생애최초 해당 여부',160,610,630,37)
        +b.t('history_detail2','처분 조건 확인',160,675,630,32,MUTED))
    b.show('property',2,b.t('property_title','구입할 주택',1200,440,550,43,GOLD,700)
        +b.t('property_detail','정확한 주소 · 담보평가',1060,610,690,37)
        +b.t('property_detail2','상품별 요건 확인',1060,675,690,32,MUTED)
        +b.arrow('conditions_match',875,575,975,575))

def _s24(b,c):
    b.add(b.t('sequence','계약 전에 자금 흐름을 완성하기',100,265,1700,48,weight=700))
    items=[('현금 확정','잔금일 현금 − 준비금','wallet'),('은행 상담','인정소득 · 기존 채무','bank'),
           ('주택 확인','담보평가 · 적용 LTV','home'),('계약 전 검토','실행 조건 · 자금 일정','check')]
    for i,(title,detail,icon) in enumerate(items):
        x=100+i*440
        b.add(b.r(f'circle{i}',x+80,370,190,190,'#e4ebf5' if i<3 else '#dcebe5','border-radius:95px;'))
        b.add(b.icon(f'icon{i}',icon,x+125,415,100,BLUE if i<3 else GREEN))
        b.add(b.t(f'step_number{i}',f'0{i+1}',x,338,100,29,MUTED,600))
        b.show(f'step{i}',i+1,b.t(f'title{i}',title,x,602,395,39,BLUE if i<3 else GREEN,700)
            +b.t(f'detail{i}',detail,x,674,395,29,MUTED))
        if i<3:b.add(b.arrow(f'connector{i}',x+295,465,x+410,465))
    b.show('ltv_recap',3,b.t('bottom','현금 2억 · 준비금 3000만원  |  LTV 70%: 5.66억  /  40%: 2.83억',100,775,1700,33,GREEN,600))

def _s25(b,c):
    b.add(b.t('question','월 200만원, 갚은 뒤의 생활은?',100,270,1700,50,weight=700))
    b.add(b.r('income_envelope',100,385,330,360,'#173348','border-radius:25px;'))
    b.add(b.icon('income_icon','wallet',210,415,105,'#ffffff'))
    b.add(b.t('income_title','월 소득',155,575,260,48,'#ffffff',700))
    b.add(b.arrow('split',455,560,585,560))
    items=[('월 원리금','편하게 갚을 금액','home',GOLD,1),('생활비·교육비','부모님 지원까지','family',BLUE,2),('앞으로의 계획','출산 · 이직 · 소득 공백','calendar',GREEN,3)]
    for i,(title,detail,icon,color,beat) in enumerate(items):
        x=630+i*405
        b.add(b.r(f'budget_base{i}',x,385,375,360,'#ffffff','border-radius:25px;'))
        b.add(b.icon(f'budget_icon{i}',icon,x+130,420,95,color))
        b.show(f'budget{i}',beat,b.t(f'budget_title{i}',title,x+25,567,325,36,color,700)
            +b.t(f'budget_detail{i}',detail,x+25,642,325,28,MUTED))
    b.add(b.t('formula','월 소득 − 원리금 − 생활비 − 계획 저축 = 남는 여력',100,785,1700,34,GREEN,600))

def _s29(b,c):
    b.add(b.t('label','화자의 정책 해석',100,260,1700,31,MUTED))
    b.add(b.icon('policy_balance','scale',775,315,340,INK))
    b.show('opinion',1,b.t('title','수요 관리와 실수요 지원을 함께 보기',100,715,1700,44,weight=700))
    b.show('policy',2,b.r('manage_base',100,360,570,230,'#eee8d9','border-radius:26px;')
        +b.t('manage_title','수요 관리',140,405,490,47,GOLD,700)
        +b.t('manage_detail','과도한 차입 투자 수요 억제',140,505,490,29,MUTED)
        +b.r('support_base',1230,360,570,230,'#e4ebf5','border-radius:26px;')
        +b.t('support_title','청년·실수요 지원',1270,405,490,43,BLUE,700)
        +b.t('support_detail','지원 대상과 조건 구분',1270,505,490,29,MUTED))
    b.show('borrower',3,b.t('borrower_text','실거주도 차주·주택별 대출 조건 확인',100,650,1700,33,BLUE,600))
    b.show('holding',4,b.t('burden','가격 변동 · 세금 · 유지비까지 계산',100,790,1700,33,GREEN,600))

_s21_detail_builder=_s21
def _s21(b,c):
    before=len(b.parts)
    _s21_detail_builder(b,c)
    detail=''.join(b.parts[before:]);del b.parts[before:]
    b.parts.append(f'<div id="{b.id("detail_phase")}" style="position:absolute;inset:0">{detail}</div>')
    transition=25.60
    b.animations.append({'targets':[b.id('detail_phase')],'kind':'hide','beat':4,'at_s':transition})
    cost=c['cost_example']
    body=b.t('allocation_title','준비금 4000만원의 구성',100,285,1700,56,weight=700)
    body+=b.r('allocation_track',100,430,1700,100,PALE)
    scale=1700/40_000_000
    body+=b.r('cost_share',100,430,cost['total_won']*scale,100,GOLD,value=cost['total_won'],scale=scale)
    body+=b.r('other_share',100+cost['total_won']*scale,430,cost['unallocated_remainder_won']*scale,100,GREEN,value=cost['unallocated_remainder_won'],scale=scale)
    body+=b.t('cost_title','취득세·교육세 + 복비·부가세',100,575,850,33,GOLD,600)
    body+=b.t('cost_value','1306만8000원',100,640,850,63,GOLD,700)
    body+=b.t('other_title','다른 비용과 비상금에 배분',1010,575,800,33,GREEN,600)
    body+=b.t('other_value','2693만2000원',1010,640,800,63,GREEN,700)
    body+=b.t('other_uses','등기 · 이사 · 수리 · 가전 · 가구 · 비상금',100,765,1700,36,MUTED)
    b.show('allocation_phase',4,body)
    b.animations[-1]['at_s']=transition

_BUILDERS = {f'S{i:02}': globals()[f'_s{i:02}'] for i in range(1, 32)}


def build_scene(scene_id: str, timing: dict, assets: dict) -> dict:
    """Build one scene using its native alignment entry, without setting time.

    ``timing`` is the scene object from scene_alignment.json. ``beat`` in the
    result indexes that object's beats, starting at one. The parent resolves
    the actual seconds; this module neither estimates nor redistributes them.
    Asset paths supplied by the parent are used verbatim and HTML-escaped.
    """
    plans, calc = _inputs()
    if scene_id not in _BUILDERS:
        raise ValueError(f'Unknown scene_id: {scene_id}')
    if timing.get('scene_id', scene_id) != scene_id:
        raise ValueError(f'Timing belongs to a different scene: {scene_id}')
    beats = timing.get('beats')
    expected = len(plans[scene_id]['beats'])
    if not isinstance(beats, list) or len(beats) != expected:
        raise ValueError(f'{scene_id} requires its {expected} native beats')
    for i, beat in enumerate(beats, 1):
        if not isinstance(beat.get('start_s'), (int, float)) or beat['start_s'] < 0:
            raise ValueError(f'{scene_id} beat {i} has no valid native start_s')
    b = _Scene(scene_id, timing, assets, plans[scene_id])
    b.add(b.t('heading', plans[scene_id]['message'], 80, 140, 1760, 43, weight=700))
    _BUILDERS[scene_id](b, calc)
    return {'html': '\n'.join(b.parts), 'animations': b.animations}
