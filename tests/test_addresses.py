import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from web.addresses import full_road_address


def test_complete_prefix_and_building_number():
    assert full_road_address(dict(region='서울',sigungu_name='서대문구',road_address='모래내로 00424')) == '서울특별시 서대문구 모래내로 424'
    assert full_road_address(dict(region='인천',sigungu_name='서구(인천)',road_address='청라로 00012-00003')) == '인천광역시 서구 청라로 12-3'


def test_missing_address_is_not_invented_and_full_address_not_duplicated():
    assert full_road_address(dict(region='서울',sigungu_name='서대문구')) == ''
    assert full_road_address(dict(region='서울',sigungu_name='서대문구',road_address='서울특별시 서대문구 모래내로 424')) == '서울특별시 서대문구 모래내로 424'
