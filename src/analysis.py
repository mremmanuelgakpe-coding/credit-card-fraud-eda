"""Reproducible, memory-conscious EDA helpers for the ULB credit-card dataset."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import BinaryIO

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp, mannwhitneyu

REQUIRED = {"Time", "Amount", "Class"}
EXPECTED_COLUMNS = {"Time", "Amount", "Class", *(f"V{i}" for i in range(1, 29))}


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_csv(file: str | Path | BinaryIO, chunksize: int | None = None) -> pd.DataFrame:
    """Read and validate CSV; malformed required values are reported, never silently dropped."""
    df = pd.read_csv(file, low_memory=False) if chunksize is None else pd.concat(
        pd.read_csv(file, low_memory=False, chunksize=chunksize), ignore_index=True
    )
    missing = REQUIRED - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes requises absentes : {', '.join(sorted(missing))}")
    for column in REQUIRED:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    invalid = df[list(REQUIRED)].isna().any(axis=1)
    if invalid.any():
        raise ValueError(f"{int(invalid.sum())} ligne(s) ont une valeur requise absente ou invalide.")
    if not set(df["Class"].unique()).issubset({0, 1}):
        raise ValueError("Class doit contenir uniquement 0 (non-fraude) et 1 (fraude).")
    if (df["Amount"] < 0).any() or (df["Time"] < 0).any():
        raise ValueError("Amount et Time doivent être positifs ou nuls.")
    df["Class"] = df["Class"].astype("int8")
    return df


def quality_report(df: pd.DataFrame) -> dict:
    return {
        "rows": int(len(df)), "columns": int(len(df.columns)),
        "missing_by_column": {k: int(v) for k, v in df.isna().sum().items() if v},
        "duplicate_rows": int(df.duplicated().sum()),
        "duplicate_rate_pct": float(df.duplicated().mean() * 100) if len(df) else 0.0,
        "dtypes": {k: str(v) for k, v in df.dtypes.items()},
        "unexpected_columns": sorted(set(df.columns) - EXPECTED_COLUMNS),
        "missing_expected_columns": sorted(EXPECTED_COLUMNS - set(df.columns)),
        "invalid_class_count": int((~df.Class.isin([0, 1])).sum()),
        "negative_amount_count": int((df.Amount < 0).sum()),
    }


def summary(df: pd.DataFrame) -> dict:
    fraud = df[df.Class == 1]
    return {
        "transactions": len(df), "frauds": int(df.Class.sum()),
        "rate": float(df.Class.mean() * 100) if len(df) else 0.0,
        "amount_total": float(df.Amount.sum()),
        "median_amount": float(df.Amount.median()) if len(df) else 0.0,
        "fraud_amount": float(fraud.Amount.sum()), "duplicates": int(df.duplicated().sum()),
        "missing": int(df.isna().sum().sum()),
    }


def univariate_report(df: pd.DataFrame) -> pd.DataFrame:
    """Descriptive shape and tail diagnostics for every numeric variable."""
    rows = []
    for col in df.select_dtypes(include=np.number):
        x = df[col].dropna()
        q1, q3 = x.quantile([.25, .75])
        iqr = q3 - q1
        rows.append({"variable": col, "n": len(x), "mean": x.mean(), "std": x.std(),
                     "median": x.median(), "q1": q1, "q3": q3, "min": x.min(), "max": x.max(),
                     "skewness": x.skew(), "outlier_iqr_count": int(((x < q1-1.5*iqr)|(x > q3+1.5*iqr)).sum())})
    return pd.DataFrame(rows)


def class_comparison(df: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
    """Mann–Whitney + KS tests with rank-biserial effect and KS distance."""
    columns = columns or [c for c in df.select_dtypes(include=np.number) if c != "Class"]
    normal, fraud = df.loc[df.Class == 0], df.loc[df.Class == 1]
    if not len(normal) or not len(fraud):
        raise ValueError("Les deux classes doivent être présentes pour la comparaison.")
    result = []
    for col in columns:
        a, b = normal[col].dropna().to_numpy(), fraud[col].dropna().to_numpy()
        if len(a) == 0 or len(b) == 0:
            continue
        mw = mannwhitneyu(a, b, alternative="two-sided", method="auto")
        ks = ks_2samp(a, b, alternative="two-sided", method="auto")
        # U porte sur le premier échantillon (non-fraude) : on inverse pour que l'effet soit positif quand les
        # valeurs sont plus élevées parmi les fraudes (corrélation rang-bisériale, de -1 à 1).
        rbc = 1 - 2 * mw.statistic / (len(a) * len(b))
        result.append({"variable": col, "n_nonfraud": len(a), "n_fraud": len(b),
                       "median_nonfraud": float(np.median(a)), "median_fraud": float(np.median(b)),
                       "mann_whitney_p": float(mw.pvalue), "rank_biserial": float(rbc),
                       "ks_p": float(ks.pvalue), "ks_statistic": float(ks.statistic)})
    out = pd.DataFrame(result)
    if len(out):
        out["mann_whitney_p_bh"] = _bh_adjust(out.mann_whitney_p.to_numpy())
        out["ks_p_bh"] = _bh_adjust(out.ks_p.to_numpy())
        out = out.sort_values("ks_statistic", ascending=False).reset_index(drop=True)
    return out


def _bh_adjust(p_values: np.ndarray) -> np.ndarray:
    p = np.asarray(p_values, dtype=float)
    order = np.argsort(p)
    ranked = p[order] * len(p) / np.arange(1, len(p) + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1].clip(0, 1)
    adjusted = np.empty_like(ranked)
    adjusted[order] = ranked
    return adjusted


def hourly_profile(df: pd.DataFrame) -> pd.DataFrame:
    out = df.assign(hour=(df.Time // 3600).astype(int) % 24).groupby("hour").agg(
        transactions=("Class", "size"), frauds=("Class", "sum"),
        fraud_rate_pct=("Class", lambda x: x.mean() * 100), amount_median=("Amount", "median")
    ).reset_index()
    return out
