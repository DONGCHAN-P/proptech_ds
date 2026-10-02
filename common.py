"""common utils - imported by all step1~3 notebooks/scripts.

Patch v1.1 (2026-05-03):
  - DIRS: added raw/staged keys for pop/school/shop
  - SIGUNGU_LEGACY_MAP: Bucheon (41190 <-> 41192/4/6), Hwaseong (41590 <-> 41591/3/5/7)
  - sigungu_canonical(): legacy -> canonical
  - sigungu_all_codes(): all historical codes
  - make_legal_dong_code(sigungu, umd_cd): real 10-digit admin code
"""
import re
import hashlib
import json
import sys
from pathlib import Path


def _is_colab() -> bool:
    return 'google.colab' in sys.modules


if _is_colab():
    DATA_DIR = '/content/drive/MyDrive/realestate_reco'
else:
    DATA_DIR = str(Path(__file__).resolve().parent)

BASE = Path(DATA_DIR)

DIRS = {
    'raw_trade':       BASE / 'raw' / 'rtms_trade',
    'raw_rent':        BASE / 'raw' / 'rtms_rent',
    'raw_apt_info':    BASE / 'raw' / 'apt_info',
    'raw_pop':         BASE / 'raw' / 'pop',
    'raw_school':      BASE / 'raw' / 'school',
    'raw_shop':        BASE / 'raw' / 'shop',
    'staged_trade':    BASE / 'staged' / 'trade',
    'staged_rent':     BASE / 'staged' / 'rent',
    'staged_apt_info': BASE / 'staged' / 'apt_info_snapshots',
    'staged_pop':      BASE / 'staged' / 'pop_snapshots',
    'staged_school':   BASE / 'staged' / 'school_snapshots',
    'staged_shop':     BASE / 'staged' / 'shop_snapshots',
    'master':          BASE / 'master',
    'exports_daily':   BASE / 'exports' / 'daily',
    'exports_weekly':  BASE / 'exports' / 'weekly',
    'exports_monthly': BASE / 'exports' / 'monthly',
    'logs':            BASE / 'logs',
    'config':          BASE / 'config',
}

def _resolve_db_path():
    """외부데이터 SQLite 경로.

    realestate.db 는 2026-08-28 정리 때 legacy/ 로 옮겨졌는데 스크립트들은
    루트를 보고 있었다. sqlite3.connect 는 없는 파일을 빈 DB로 만들어버려
    조용히 깨지므로, 양쪽을 확인해 실제 존재하는 쪽을 쓴다.
    """
    for p in (BASE / 'legacy' / 'realestate.db', BASE / 'realestate.db'):
        if p.exists():
            return p
    return BASE / 'legacy' / 'realestate.db'


DB_PATH = _resolve_db_path()

SIGUNGU_CODES = {'11110': '종로구', '11140': '중구', '11170': '용산구', '11200': '성동구', '11215': '광진구', '11230': '동대문구', '11260': '중랑구', '11290': '성북구', '11305': '강북구', '11320': '도봉구', '11350': '노원구', '11380': '은평구', '11410': '서대문구', '11440': '마포구', '11470': '양천구', '11500': '강서구', '11530': '구로구', '11545': '금천구', '11560': '영등포구', '11590': '동작구', '11620': '관악구', '11650': '서초구', '11680': '강남구', '11710': '송파구', '11740': '강동구', '28110': '중구(인천)', '28140': '동구(인천)', '28177': '미추홀구', '28185': '연수구', '28200': '남동구', '28237': '부평구', '28245': '계양구', '28260': '서구(인천)', '28710': '강화군', '28720': '옥진군', '41111': '수원장안구', '41113': '수원권선구', '41115': '수원팔달구', '41117': '수원영통구', '41131': '성남수정구', '41133': '성남중원구', '41135': '성남분당구', '41150': '의정부시', '41171': '안양만안구', '41173': '안양동안구', '41192': '부천원미구', '41194': '부천소사구', '41196': '부천오정구', '41210': '광명시', '41220': '평택시', '41250': '동두천시', '41271': '안산상록구', '41273': '안산단원구', '41281': '고양덕양구', '41285': '고양일산동구', '41287': '고양일산서구', '41290': '과천시', '41310': '구리시', '41360': '남양주시', '41370': '오산시', '41390': '시흥시', '41410': '군포시', '41430': '의왕시', '41450': '하남시', '41461': '용인처인구', '41463': '용인기흥구', '41465': '용인수지구', '41480': '파주시', '41500': '이천시', '41550': '안성시', '41570': '김포시', '41591': '화성만세구', '41593': '화성효행구', '41595': '화성병점구', '41597': '화성동탄구', '41610': '광주시(경기)', '41630': '양주시', '41650': '포천시', '41670': '여주시', '41800': '연천군', '41820': '가평군', '41830': '양평군', '41190': '부천시', '41590': '화성시'}


SIGUNGU_LEGACY_MAP = {
    '41190': ['41192', '41194', '41196'],
    '41192': ['41190'], '41194': ['41190'], '41196': ['41190'],
    '41590': ['41591', '41593', '41595', '41597'],
    '41591': ['41590'], '41593': ['41590'], '41595': ['41590'], '41597': ['41590'],
}


def sigungu_canonical(code):
    code = str(code)
    if code in {'41192', '41194', '41196'}:
        return '41190'
    return code


def sigungu_all_codes(code):
    code = str(code)
    out = [code]
    out.extend(SIGUNGU_LEGACY_MAP.get(code, []))
    return list(dict.fromkeys(out))


def sigungu_kr(code):
    return SIGUNGU_CODES.get(str(code), str(code))


def load_secrets():
    p = BASE / 'config' / 'secrets.json'
    return json.loads(p.read_text(encoding='utf-8'))


def to_pyeong_bucket(area_m2):
    if area_m2 < 33:    return '10P'
    if area_m2 < 50:    return '15P'
    if area_m2 < 66:    return '20P'
    if area_m2 < 83:    return '25P'
    if area_m2 < 99:    return '30P'
    if area_m2 < 116:   return '35P'
    if area_m2 < 132:   return '40P'
    if area_m2 < 165:   return '50P'
    return '60P+'


def normalize_apt_name(name):
    if name is None:
        return ''
    s = str(name).strip()
    s = re.sub(r'\([^)]*\)', '', s)
    s = re.sub(r'\[[^\]]*\]', '', s)
    s = re.sub(r'\s+', '', s)
    s = re.sub(r'(?i)apt$', '아파트', s)
    s = s.replace('아파트아파트', '아파트')
    han2num = {'일':'1','이':'2','삼':'3','사':'4','오':'5','육':'6','칠':'7','팔':'8','구':'9','십':'10'}
    for han, num in han2num.items():
        s = s.replace(han + '차', num + '차')
        s = s.replace(han + '단지', num + '단지')
    return s


def make_apt_id(legal_dong_code, apt_name, road_address=''):
    norm = normalize_apt_name(apt_name)
    addr = (road_address or '')[:30]
    raw = f'{legal_dong_code}|{norm}|{addr}'
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]


def make_legal_dong_code(sigungu_code, umd_cd):
    """Real 10-digit legal admin code = sigungu(5) + umdCd(5).
    v1.1: replaced fake sha256[:5] with RTMS umdCd."""
    sigungu = str(sigungu_code or '').strip()[:5].zfill(5)
    umd = str(umd_cd or '').strip()[:5].zfill(5)
    if not sigungu or not umd or umd == '00000':
        return f'{sigungu}_NA'
    return sigungu + umd
