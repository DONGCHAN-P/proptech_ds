"""핵심 함수 회귀 테스트.

실행:
    cd C:\\projects\\realestate_reco
    python -m pytest tests -v
"""
import sys
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from common import (
    SIGUNGU_CODES, SIGUNGU_LEGACY_MAP, DIRS,
    sigungu_canonical, sigungu_all_codes,
    to_pyeong_bucket, normalize_apt_name,
    make_apt_id, make_legal_dong_code,
)


# ──────────────────────────────────────────────────────────
# 1. apt_id 멱등성: 같은 입력은 항상 같은 hash
# ──────────────────────────────────────────────────────────
def test_make_apt_id_idempotent():
    a = make_apt_id('1168010600', '대치동부센트레빌', '도산대로 83')
    b = make_apt_id('1168010600', '대치동부센트레빌', '도산대로 83')
    assert a == b
    assert len(a) == 16


def test_make_apt_id_normalizes_name():
    """단지명 표기가 달라도 정규화 후 같은 단지면 같은 apt_id."""
    a = make_apt_id('1168010600', '대치 동부센트레빌(101동)', '도산대로 83')
    b = make_apt_id('1168010600', '대치동부센트레빌', '도산대로 83')
    assert a == b


def test_make_apt_id_different_for_different_apts():
    a = make_apt_id('1168010600', '대치동부센트레빌', '도산대로 83')
    b = make_apt_id('1168010600', '대치동부센트레빌2차', '도산대로 83')
    assert a != b


# ──────────────────────────────────────────────────────────
# 2. to_pyeong_bucket 경계값
# ──────────────────────────────────────────────────────────
def test_pyeong_bucket_boundaries():
    cases = [
        (32.99, '10P'),
        (33.00, '15P'),
        (49.99, '15P'),
        (50.00, '20P'),
        (82.99, '25P'),
        (83.00, '30P'),
        (84.99, '30P'),    # 흔한 '34평형'
        (98.99, '30P'),
        (99.00, '35P'),
        (165.0, '60P+'),
        (300.0, '60P+'),
    ]
    for m2, expected in cases:
        got = to_pyeong_bucket(m2)
        assert got == expected, f'{m2}㎡ → got {got}, expected {expected}'


# ──────────────────────────────────────────────────────────
# 3. normalize_apt_name: 한글→아라비아 숫자 / APT→아파트
# ──────────────────────────────────────────────────────────
def test_normalize_apt_name_basic():
    assert normalize_apt_name('대치 동부센트레빌(101동)') == '대치동부센트레빌'
    assert normalize_apt_name('래미안 일차') == '래미안1차'
    assert normalize_apt_name('힐스테이트APT') == '힐스테이트아파트'
    assert normalize_apt_name('자이[A동]') == '자이'
    assert normalize_apt_name(None) == ''
    assert normalize_apt_name('') == ''


# ──────────────────────────────────────────────────────────
# 4. 시군구 legacy 매핑 (부천·화성 분구)
# ──────────────────────────────────────────────────────────
def test_sigungu_legacy_bucheon():
    """부천: 옛 분구(41192/4/6) → 현재 통합(41190)으로 정규화."""
    assert sigungu_canonical('41192') == '41190'
    assert sigungu_canonical('41194') == '41190'
    assert sigungu_canonical('41196') == '41190'


def test_sigungu_all_codes_bucheon():
    """41190으로 모든 부천 시계열을 합산 가능."""
    codes = sigungu_all_codes('41190')
    assert set(codes) >= {'41190', '41192', '41194', '41196'}


def test_sigungu_legacy_hwaseong():
    codes = sigungu_all_codes('41590')
    assert set(codes) >= {'41590', '41591', '41593', '41595', '41597'}


# ──────────────────────────────────────────────────────────
# 5. 진짜 법정동코드(시군구5+umdCd5) 생성
# ──────────────────────────────────────────────────────────
def test_make_legal_dong_code():
    # 강남구 청담동
    code = make_legal_dong_code('11680', '10400')
    assert code == '1168010400'
    assert len(code) == 10


def test_make_legal_dong_code_pads():
    code = make_legal_dong_code('11680', '400')   # 짧은 입력 → zero-pad
    assert code == '1168000400'


def test_make_legal_dong_code_missing_umd():
    # umdCd 없으면 NA 표식 → 인구·학군 join에서 노출됨
    code = make_legal_dong_code('11680', '')
    assert '_NA' in code
    code = make_legal_dong_code('11680', '00000')
    assert '_NA' in code


def test_apt_id_with_real_legal_dong_code():
    """v1.1 패치: 진짜 행정코드 기반 apt_id가 같은 단지에 일관되게 나오는지."""
    legal = make_legal_dong_code('11680', '10400')
    a = make_apt_id(legal, '청담로얄카운티', '도산대로83길 27')
    b = make_apt_id(legal, '청담로얄카운티', '도산대로83길 27')
    assert a == b
    # umdCd가 다르면 apt_id도 달라야 함
    legal2 = make_legal_dong_code('11680', '11800')  # 도곡동
    c = make_apt_id(legal2, '청담로얄카운티', '도산대로83길 27')
    assert a != c


# ──────────────────────────────────────────────────────────
# 6. DIRS sanity (인구·학군·상권 누락 체크)
# ──────────────────────────────────────────────────────────
def test_dirs_complete():
    required = ['raw_pop', 'staged_pop', 'raw_school', 'raw_shop',
                'staged_school', 'staged_shop',
                'raw_trade', 'staged_trade', 'master']
    for k in required:
        assert k in DIRS, f'DIRS에 {k} 없음 — common.py 패치 누락'


def test_sigungu_count():
    """수도권 시군구 코드. v1.1: legacy 41190(부천 통합), 41590(화성 통합) 포함.
    25 서울 + 10 인천 + 약 47 경기(분구+legacy) = 약 80~85개."""
    assert 70 <= len(SIGUNGU_CODES) <= 90
    # 핵심 키 포함
    assert '11680' in SIGUNGU_CODES   # 강남
    assert '41135' in SIGUNGU_CODES   # 분당
    assert '41192' in SIGUNGU_CODES   # 부천 원미
    assert '41190' in SIGUNGU_CODES   # 부천 통합 (legacy/canonical)
