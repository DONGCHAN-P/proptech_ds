import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from web.complex_facts import lookup


def test_unknown_complex_does_not_invent_household_count():
    value=lookup('not-an-existing-complex')
    assert value['household_count'] is None
    assert value['building_count'] is None


def test_household_snapshot_has_positive_counts_and_unique_complexes():
    from web.complex_facts import facts
    data=facts()
    assert data
    assert all(isinstance(row['household_count'],int) and row['household_count']>0 for row in data.values())
