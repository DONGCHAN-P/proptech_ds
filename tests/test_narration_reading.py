"""Regression cases from real narration; ordinary numbers remain caller-owned."""
from pathlib import Path
import importlib.util
import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('narration_reading', ROOT / 'video-agent-studio/lib/narration_reading.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


@pytest.mark.parametrize('source', [
    '상계2차중앙하이츠 주변을 보겠습니다.',
    '상계2차 중앙하이츠 주변을 보겠습니다.',
    '상계이 차중앙하이츠 주변을 보겠습니다.',
])
def test_real_complex_name_keeps_ordinal_and_separates_words(source):
    assert MODULE.apply_name_readings(source) == '상계 이차 중앙 하이츠 주변을 보겠습니다.'


def test_other_prices_and_official_train_types_are_unchanged():
    source = 'KTX 역과 6억원 아파트, 2024년 통계를 살펴봅니다.'
    assert MODULE.apply_name_readings(source) == source


def test_reading_is_idempotent_and_original_entity_is_not_mutated():
    source = '상계2차중앙하이츠'
    first = MODULE.apply_name_readings(source)
    assert MODULE.apply_name_readings(first) == first == '상계 이차 중앙 하이츠'
    assert source == '상계2차중앙하이츠'
