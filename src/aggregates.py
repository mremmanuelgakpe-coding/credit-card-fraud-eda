"""Tables agrégées du tableau de bord, calculées une fois sur le CSV local vérifié.

Le CSV brut (284 807 transactions) n'est jamais publié. Le tableau de bord, en local comme sur Streamlit Cloud, ne lit
que ces tables, qui ne contiennent aucune transaction individuelle :

- ``cube.csv`` : transactions, fraudes, montants et doublons par jour × heure relative × tranche de montant.
  Les cellules de moins de 5 transactions sont fusionnées en une ligne « Regroupé » ; les totaux restent exacts.
- ``amount_hist.csv`` : histogramme des montants (classes logarithmiques) par jour × heure × classe.
- ``pca_hist.csv`` : histogramme de V1 à V28 (40 classes communes) par jour × tranche de montant × classe.
- ``tests.csv`` : comparaison fraude / non-fraude de chaque variable sur le jeu complet (Mann–Whitney, KS, effets,
  correction de Benjamini–Hochberg), ``spearman_*.csv`` : corrélations, ``univariate.csv`` : descriptifs.
- ``manifest.json`` : empreinte du CSV source, contrôles de cohérence.

Usage : python -m src.aggregates
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.analysis import class_comparison, load_csv, quality_report, sha256_file, univariate_report

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "creditcard.csv"
OUT = ROOT / "reports" / "aggregates"
EXPECTED_SHA256 = "76274b691b16a6c49d3f159c883398e03ccd6d1ee12d9d8ee38f4b4b98551a89"
K_MIN = 5
GROUPED = "Regroupé"
BANDS = ([-0.01, 0, 1, 10, 50, 100, 500, 1000, np.inf],
         ["0", "0-1", "1-10", "10-50", "50-100", "100-500", "500-1000", "1000+"])
PCA = [f"V{i}" for i in range(1, 29)]
# Classes de montant logarithmiques : 0, puis de 0,01 à 30 000
AMOUNT_EDGES = np.concatenate([[-0.01, 0.005], np.logspace(np.log10(0.01), np.log10(30000), 151)])


def enrich(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["day"] = np.where(out["Time"] < 86_400, "J1", "J2")       # 172 792 s : deux journées de collecte
    out["hour"] = (out["Time"] // 3600).astype(int) % 24             # heure relative au début de la collecte
    out["band"] = pd.cut(out["Amount"], BANDS[0], labels=BANDS[1]).astype(str)
    out["dup"] = out.duplicated(subset=[c for c in df.columns]).astype(int)
    return out


def build_cube(d: pd.DataFrame) -> pd.DataFrame:
    g = d.assign(fraud_amount=d["Amount"] * d["Class"], dup_fraud=d["dup"] * d["Class"]).groupby(
        ["day", "hour", "band"], observed=True).agg(
        transactions=("Class", "size"), frauds=("Class", "sum"), amount=("Amount", "sum"),
        fraud_amount=("fraud_amount", "sum"), duplicates=("dup", "sum"), duplicate_frauds=("dup_fraud", "sum")
    ).reset_index()
    g["hour"] = g["hour"].astype(str)
    small = g["transactions"] < K_MIN
    # cellules trop petites : fusionnées en une seule ligne « Regroupé » (jour, heure et tranche masqués)
    grouped = g[small].assign(day=GROUPED, hour=GROUPED, band=GROUPED).groupby(["day", "hour", "band"]).sum(numeric_only=True)
    cube = pd.concat([g[~small], grouped.reset_index()], ignore_index=True)
    assert (cube["transactions"] >= K_MIN).all()
    for c in ("amount", "fraud_amount"):
        cube[c] = cube[c].round(2)
    return cube


def build_amount_hist(d: pd.DataFrame) -> pd.DataFrame:
    d = d.assign(bin=pd.cut(d["Amount"], AMOUNT_EDGES, labels=False, include_lowest=True))
    h = d.groupby(["day", "hour", "Class", "bin"]).size().rename("n").reset_index()
    h["lo"], h["hi"] = AMOUNT_EDGES[h["bin"]].clip(0), AMOUNT_EDGES[h["bin"] + 1]
    return h


def build_pca_hist(d: pd.DataFrame, n_bins: int = 40) -> tuple[pd.DataFrame, dict]:
    rows, edges = [], {}
    for v in PCA:
        # bornes couvrant 99,8 % des normales ET 98 % des fraudes (les fraudes sont souvent dans les extrêmes) ;
        # les rares valeurs au-delà sont ramenées dans la classe du bord
        qn = d.loc[d["Class"] == 0, v].quantile([0.001, 0.999])
        qf = d.loc[d["Class"] == 1, v].quantile([0.01, 0.99])
        lo, hi = min(qn.iloc[0], qf.iloc[0]), max(qn.iloc[1], qf.iloc[1])
        e = np.linspace(lo, hi, n_bins + 1)
        edges[v] = e.round(6).tolist()
        b = np.clip(np.digitize(d[v], e[1:-1]), 0, n_bins - 1)
        h = d.assign(bin=b).groupby(["day", "band", "Class", "bin"]).size().rename("n").reset_index()
        h["variable"] = v
        rows.append(h)
    return pd.concat(rows, ignore_index=True), edges


def main() -> dict:
    if not RAW.exists():
        raise SystemExit("data/creditcard.csv absent : voir data/README.md.")
    digest = sha256_file(RAW)
    if digest != EXPECTED_SHA256:
        raise SystemExit(f"SHA-256 inattendu ({digest}).")
    df = load_csv(RAW)
    d = enrich(df)
    OUT.mkdir(parents=True, exist_ok=True)
    cube = build_cube(d)
    cube.to_csv(OUT / "cube.csv", index=False)
    build_amount_hist(d).to_csv(OUT / "amount_hist.csv", index=False)
    pca_hist, edges = build_pca_hist(d)
    pca_hist.to_csv(OUT / "pca_hist.csv", index=False)
    (OUT / "pca_edges.json").write_text(json.dumps(edges))
    tests = class_comparison(df, PCA + ["Amount", "Time"])
    tests.to_csv(OUT / "tests.csv", index=False)
    univariate_report(df).to_csv(OUT / "univariate.csv", index=False)
    top = tests["variable"].head(10).tolist()
    for name, part in (("all", df), ("fraud", df[df["Class"] == 1]), ("normal", df[df["Class"] == 0])):
        part[top + ["Amount", "Time"]].corr(method="spearman").round(4).to_csv(OUT / f"spearman_{name}.csv")
    q = quality_report(df)
    fraud = df[df["Class"] == 1]
    manifest = {
        "source_sha256": digest, "rows": int(len(df)), "columns": int(df.shape[1]), "frauds": int(df["Class"].sum()),
        "amount": round(float(df["Amount"].sum()), 2), "fraud_amount": round(float(fraud["Amount"].sum()), 2),
        "median_amount_normal": float(df.loc[df["Class"] == 0, "Amount"].median()),
        "median_amount_fraud": float(fraud["Amount"].median()),
        "amount_quantiles": {str(c): {str(q): float(df.loc[df["Class"] == c, "Amount"].quantile(q)) for q in (0.25, 0.5, 0.75)}
                             for c in (0, 1)},
        "missing_values": int(df.isna().sum().sum()), "duplicate_rows": q["duplicate_rows"],
        "duplicate_frauds": int(d.loc[d["dup"] == 1, "Class"].sum()),
        "time_max_seconds": float(df["Time"].max()), "cube_cells": int(len(cube)), "k_min": K_MIN,
        "grouped_transactions": int(cube.loc[cube["hour"] == GROUPED, "transactions"].sum()),
        "significant_variables_ks_bh": int((tests["ks_p_bh"] < 0.05).sum()),
    }
    assert int(cube["transactions"].sum()) == manifest["rows"] and int(cube["frauds"].sum()) == manifest["frauds"]
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    return manifest


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, ensure_ascii=False))
