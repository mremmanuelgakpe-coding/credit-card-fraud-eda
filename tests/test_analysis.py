import pandas as pd
import pytest

from src.analysis import class_comparison, load_csv, quality_report, summary


def sample():
    return pd.DataFrame({"Time":[0, 1, 2, 3], "Amount":[2., 3., 10., 12.],
                         "Class":[0, 0, 1, 1], "V1":[0., .1, 2., 3.]})


def test_summary_and_quality():
    df = sample()
    assert summary(df)["frauds"] == 2
    assert summary(df)["rate"] == 50
    assert quality_report(df)["rows"] == 4


def test_class_comparison_has_effect_sizes_and_adjusted_pvalues():
    result = class_comparison(sample(), ["Amount", "V1"])
    assert set(["rank_biserial", "ks_statistic", "mann_whitney_p_bh", "ks_p_bh"]).issubset(result)
    assert result.ks_statistic.between(0, 1).all()


def test_load_rejects_invalid_class():
    with pytest.raises(ValueError, match="Class"):
        load_csv(pd.io.common.BytesIO(b"Time,Amount,Class\n0,2,3\n"))


def test_rank_biserial_sign_points_to_fraud():
    df = pd.DataFrame({"Time": range(8), "Amount": [1.] * 8, "Class": [0, 0, 0, 0, 1, 1, 1, 1],
                       "V1": [0., 1., 2., 3., 10., 11., 12., 13.]})
    r = class_comparison(df, ["V1"]).iloc[0]
    assert r.rank_biserial == 1.0          # valeurs toutes plus élevées chez les fraudes
