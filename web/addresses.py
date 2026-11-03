"""Format stored road addresses without inventing missing building/lot numbers."""
import re

REGIONS = {'서울': '서울특별시', '경기': '경기도', '인천': '인천광역시'}


def full_road_address(info):
    road = (info.get('road_address') or '').strip()
    if not road:
        return ''
    road = re.sub(r'(?<=\s)0*(\d+)(?:-0*(\d+))?$',
                  lambda m: str(int(m[1])) + ('-' + str(int(m[2])) if m[2] else ''), road)
    region = REGIONS.get(info.get('region'), info.get('region') or '')
    district = re.sub(r'\([^)]*\)', '', info.get('sigungu_name') or '').strip()
    if road.startswith(tuple(REGIONS.values())):
        return road
    parts = [region]
    if district and not road.startswith(district + ' '):
        parts.append(district)
    parts.append(road)
    return ' '.join(p for p in parts if p)
