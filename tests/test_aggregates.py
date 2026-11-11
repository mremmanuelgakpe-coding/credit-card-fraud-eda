"""Tables agrégées publiées : cohérence des totaux et absence de données ligne à ligne."""
import json
from pathlib import Path

import pandas as pd

AGG = Path(__file__).resolve().parents[1] / "reports" / "aggregates"


def test_cube_totals_match_manifest():
    m = json.loads((AGG / "manifest.json").read_text())
    cube = pd.read_csv(AGG / "cube.csv")
    assert int(cube["transactions"].sum()) == m["rows"] == 284807
    assert int(cube["frauds"].sum()) == m["frauds"] == 492
    assert abs(cube["amount"].sum() - m["amount"]) < 1
    assert int(cube["duplicates"].sum()) == m["duplicate_rows"]


def test_no_small_cells_and_no_raw_columns():
    cube = pd.read_csv(AGG / "cube.csv")
    assert cube["transactions"].min() >= 5
    for f in AGG.glob("*.csv"):
        cols = set(pd.read_csv(f, nrows=1, index_col=None).columns)
        assert not {"Time", "Amount", "Class"} <= cols, f"{f.name} ressemble à des données brutes"


def test_histograms_are_complete():
    amount = pd.read_csv(AGG / "amount_hist.csv")
    assert amount["n"].sum() == 284807 and amount.loc[amount["Class"] == 1, "n"].sum() == 492
    pca = pd.read_csv(AGG / "pca_hist.csv")
    per_var = pca.groupby("variable")["n"].sum()
    assert len(per_var) == 28 and (per_var == 284807).all()


def test_tests_table():
    t = pd.read_csv(AGG / "tests.csv")
    assert len(t) == 30 and t.iloc[0]["variable"] == "V14"
    assert t["ks_statistic"].between(0, 1).all() and t["rank_biserial"].between(-1, 1).all()
