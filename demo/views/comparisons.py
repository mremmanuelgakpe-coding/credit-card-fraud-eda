"""Fraude vs normale : les 28 composantes anonymisées comparées entre les deux classes."""
import sys
from functools import partial
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import (CLASS_COLORS, GREEN, INK, MINT, card, chart_config, filtered, footer, fr, kpi_grid, load,  # noqa: E402
                    pca_view, pct, scope_note, section)

d, excluded, sel = filtered()
scope_note(d, excluded, sel)
L = load()
tests, edges = L["tests"], L["edges"]
ph = pca_view()


def ks_table(h: pd.DataFrame) -> pd.DataFrame:
    """Distance KS approchée sur les histogrammes filtrés (40 classes) : écart maximal entre les deux fonctions de
    répartition."""
    p = h.pivot_table(index=["variable", "bin"], columns="Class", values="n", aggfunc="sum", fill_value=0)
    p = p.reindex(columns=[0, 1], fill_value=0)
    rows = []
    for v, g in p.groupby(level=0):
        c0, c1 = g[0].cumsum() / max(g[0].sum(), 1), g[1].cumsum() / max(g[1].sum(), 1)
        rows.append({"variable": v, "ks": float((c0 - c1).abs().max()), "n_fraud": int(g[1].sum())})
    return pd.DataFrame(rows).sort_values("ks", ascending=False)


ks = ks_table(ph)
nf = int(ks["n_fraud"].max()) if len(ks) else 0
full = tests.set_index("variable")
pca_tests = tests[tests["variable"].str.startswith("V")]

section("Ce qui distingue les fraudes", "Tests sur le jeu complet (284 807 transactions), p-values corrigées par "
                                        "Benjamini-Hochberg.")
strong = (pca_tests["rank_biserial"].abs() >= 0.5).sum()
kpi_grid([
    ("Variables différentes", f"{(pca_tests['ks_p_bh'] < 0.05).sum()} / 28", "test KS significatif après correction"),
    ("Variable la plus discriminante", pca_tests.iloc[0]["variable"], f"distance KS {fr(pca_tests.iloc[0]['ks_statistic'], 2)}",
     "hl"),
    ("Effets forts", f"{strong} / 28", "taille d'effet rang-bisériale d'au moins 0,5 en valeur absolue", "orange"),
    ("Fraudes dans le périmètre", fr(nf, 0), "les distances ci-dessous suivent les filtres jour et tranche", "blue"),
])
if nf < 30:
    st.markdown("<div class='note'>Moins de 30 fraudes avec ces filtres : les distances sont peu fiables.</div>",
                unsafe_allow_html=True)


def _pick(key):
    rows = ((st.session_state.get(key) or {}).get("selection") or {}).get("pick") or []
    if rows and rows[0].get("variable"):
        st.session_state["pca_var"] = rows[0]["variable"]


if "pca_var" not in st.session_state or st.session_state["pca_var"] not in edges:
    st.session_state["pca_var"] = ks.iloc[0]["variable"] if len(ks) else "V14"
var = st.session_state["pca_var"]

section("Classement et distribution", "Cliquez sur une variable du classement pour afficher sa distribution.")
l, r = st.columns([1, 1.25], gap="medium")
k = card(l, "Distance KS (périmètre filtré)", "0 : distributions identiques ; 1 : totalement séparées. 15 premières.")
top = ks.head(15).copy()
top["sel"] = (top["variable"] == var).astype(int)
top["ks_fr"] = top["ks"].map(lambda v: fr(v, 2))
base = alt.Chart(top).encode(y=alt.Y("variable:N", sort=list(top["variable"]), title=None,
                                     axis=alt.Axis(labelFontSize=14, labelColor=INK, ticks=False, domain=False)))
bars = base.mark_bar(height=16, cornerRadiusEnd=4).encode(
    x=alt.X("ks:Q", title=None, axis=None, scale=alt.Scale(domain=[0, 1.08])),
    color=alt.condition(alt.datum.sel == 1, alt.value(GREEN), alt.value(MINT)),
    tooltip=[alt.Tooltip("variable:N", title="Variable"), alt.Tooltip("ks_fr:N", title="Distance KS")])
txt = base.mark_text(align="left", dx=6, fontSize=14, fontWeight=700, color=INK).encode(x="ks:Q", text="ks_fr:N")
chart = chart_config(alt.layer(bars.add_params(alt.selection_point(name="pick", fields=["variable"])), txt),
                     30 * len(top)).configure_mark(cursor="pointer")
k.altair_chart(chart, use_container_width=True, key="cmp_ks", on_select=partial(_pick, "cmp_ks"), selection_mode="pick")


def density(h, v):
    g = h[h["variable"] == v].groupby(["Class", "bin"])["n"].sum().reset_index()
    e = np.array(edges[v])
    g["x"] = (e[g["bin"]] + e[g["bin"] + 1]) / 2
    g["share"] = g["n"] / g.groupby("Class")["n"].transform("sum")
    g["Classe"] = g["Class"].map({0: "Normale", 1: "Fraude"})
    return g


def dist_chart(g, height, legend=True, title=True):
    return alt.Chart(g).mark_area(opacity=0.55, interpolate="monotone", line=True).encode(
        x=alt.X("x:Q", title="Valeur" if title else None),
        y=alt.Y("share:Q", title="Part" if title else None, stack=None,
                axis=alt.Axis(labelExpr="format(datum.value * 100, '.0f') + ' %'", tickCount=4)),
        color=alt.Color("Classe:N", scale=alt.Scale(domain=list(CLASS_COLORS), range=[MINT, GREEN]),
                        legend=alt.Legend(orient="top", title=None) if legend else None),
        tooltip=["Classe", alt.Tooltip("x:Q", title="Valeur", format=".2f"), alt.Tooltip("share:Q", title="Part", format=".1%")])


row = full.loc[var]
k = card(r, f"Distribution de {var}", f"Jeu complet : médiane {fr(row['median_nonfraud'], 2)} chez les normales, "
                                      f"{fr(row['median_fraud'], 2)} chez les fraudes ; taille d'effet "
                                      f"{fr(row['rank_biserial'], 2)}.")
k.altair_chart(chart_config(dist_chart(density(ph, var), 300), 300), use_container_width=True)

section("Les six variables les plus discriminantes", "Mêmes couleurs : vert clair = normales, vert foncé = fraudes.")
six = list(ks.head(6)["variable"])
for chunk in (six[:3], six[3:]):
    cols = st.columns(3, gap="medium")
    for c, v in zip(cols, chunk):
        k = card(c, v, f"KS {fr(float(ks.set_index('variable').loc[v, 'ks']), 2)}")
        k.altair_chart(chart_config(dist_chart(density(ph, v), 170, legend=False, title=False), 170),
                       use_container_width=True)

section("Tests complets (jeu entier)", "Médianes, taille d'effet rang-bisériale (positive : valeurs plus élevées chez les "
                                       "fraudes), distance et p-value KS corrigée.")
show = tests.copy()
show["Médiane normales"] = show["median_nonfraud"].map(lambda v: fr(v, 3))
show["Médiane fraudes"] = show["median_fraud"].map(lambda v: fr(v, 3))
show["Effet"] = show["rank_biserial"].map(lambda v: fr(v, 3))
show["KS"] = show["ks_statistic"].map(lambda v: fr(v, 3))
show["p KS corrigée"] = show["ks_p_bh"].map(lambda v: "< 0,001" if v < 0.001 else fr(v, 3))
st.dataframe(show.rename(columns={"variable": "Variable"})[["Variable", "Médiane normales", "Médiane fraudes", "Effet", "KS",
                                                             "p KS corrigée"]], hide_index=True, use_container_width=True,
             height=420)
st.markdown(f"<div class='note'>Avec {fr(284807, 0)} transactions, de très petites différences deviennent significatives : "
            "on lit d'abord la distance KS et la taille d'effet. V1 à V28 sont issues d'une ACP faite par la source pour "
            f"anonymiser les données : elles n'ont pas de sens métier connu. Exemple : {var} n'est ni un pays ni un "
            f"commerçant. Part des fraudes dans le jeu : {pct(492 / 284807, 3)}.</div>", unsafe_allow_html=True)
footer()
