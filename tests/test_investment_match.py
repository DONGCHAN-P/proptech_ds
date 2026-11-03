import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from web import match as M


def test_api_defaults_to_long_term_without_relaxing_budget():
    a = M.Answers.from_payload({'budget':150000})
    assert a.objective == 'long_term'
    assert a.budget == 150000


def test_more_budget_does_not_reward_same_cheap_home():
    row = pd.DataFrame([dict(last_price=20000, rel_price_pct=1, trade_1y=12,
                            build_year=2010, walk_min=5, s_location=70,
                            s_value=60, s_liquidity=70, s_residential=70)])
    one = M.score(row, M.Answers(budget=50000, objective='long_term'))
    two = M.score(row, M.Answers(budget=150000, objective='long_term'))
    assert one['score'].iloc[0] == two['score'].iloc[0]


def test_quality_and_demand_outweigh_absolute_cheapness():
    rows = pd.DataFrame([
        dict(last_price=15000, rel_price_pct=1, trade_1y=4, build_year=1985, walk_min=4,
             s_location=20, s_value=80, s_liquidity=30, s_residential=30),
        dict(last_price=120000, rel_price_pct=60, trade_1y=25, build_year=2015, walk_min=6,
             s_location=90, s_value=60, s_liquidity=90, s_residential=85)])
    result = M.score(rows, M.Answers(budget=150000, objective='long_term'))
    assert result['score'].iloc[1] > result['score'].iloc[0]
