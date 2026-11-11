"""Montants : distributions comparées des transactions normales et frauduleuses."""
import sys
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import (BAND_NAMES, BANDS, CLASS_COLORS, amount_quantile, amount_view, card, chart_config, click_bars, filtered, footer,  # noqa: E402
                    fr, heatmap, kpi_grid, pct, scope_note, section, view)

d, excluded, sel = filtered()
scope_note(d, excluded, sel)
ah = amount_view()
nf = d["frauds"].sum()


# parts exactes à partir du cube (bornes des tranches : 1 et 500)
cb = d.groupby("band")[["transactions", "frauds"]].sum()
cb["normal"] = cb["transactions"] - cb["frauds"]
tot_f, tot_n = max(cb["frauds"].sum(), 1), max(cb["normal"].sum(), 1)
low, high = [b for b in ("0", "0-1") if b in cb.index], [b for b in ("500-1000", "1000+") if b in cb.index]
small_f, small_n = cb.loc[low, "frauds"].sum() / tot_f, cb.loc[low, "normal"].sum() / tot_n
big_f, big_n = cb.loc[high, "frauds"].sum() / tot_f, cb.loc[high, "normal"].sum() / tot_n


section("Montants comparés", "Sans filtre : quantiles exacts du jeu complet. Avec filtres : valeurs approchées "
        "(≈) à partir de l'histogramme des montants.")
kpi_grid([
    ("Médiane, normales", amount_quantile(ah, 0, 0.5), f"75 % sous {amount_quantile(ah, 0, 0.75)}"),
    ("Médiane, fraudes", amount_quantile(ah, 1, 0.5) if nf else "—",
     f"75 % sous {amount_quantile(ah, 1, 0.75)}" if nf else "aucune fraude dans le périmètre", "hl"),
    ("Fraudes de 1 ou moins", pct(small_f, 0) if nf else "—",
     f"contre {pct(small_n, 0)} des transactions normales", "orange"),
    ("Fraudes de plus de 500", pct(big_f, 1) if nf else "—", f"contre {pct(big_n, 1)} des normales"),
])

section("Distribution des montants", "Part de chaque classe de transactions dans chaque intervalle de montant "
                                     "(échelle logarithmique). Les deux courbes ont la même surface.")
# classes regroupées par 4 pour la courbe (492 fraudes : une courbe trop fine serait bruitée)
g = (ah.assign(cbin=ah["bin"] // 4).groupby(["Class", "cbin"])
     .agg(n=("n", "sum"), lo=("lo", "min"), hi=("hi", "max")).reset_index())
g = g[g["hi"] > 0.006]
g["share"] = g["n"] / g.groupby("Class")["n"].transform("sum")
g["mid"] = np.sqrt(g["lo"].clip(lower=0.01) * g["hi"])
g["Classe"] = g["Class"].map({0: "Normale", 1: "Fraude"})
g["share_fr"] = g["share"].map(lambda v: pct(v, 1))
g["range"] = [f"{fr(a, 2)} – {fr(b, 2)}" for a, b in zip(g["lo"], g["hi"])]
k = card(None, "Montants : transactions normales et fraudes", "Les montants nuls (0) sont exclus de la courbe.")
area = alt.Chart(g).mark_area(opacity=0.35, interpolate="monotone").encode(
    x=alt.X("mid:Q", scale=alt.Scale(type="log", domain=[0.01, 30000]), title="Montant (échelle log)",
            axis=alt.Axis(values=[0.01, 0.1, 1, 10, 100, 1000, 10000], labelExpr="replace(replace(format(datum.value, ','), /,/g, ' '), '.', ',')")),
    y=alt.Y("share:Q", title="Part des transactions", stack=None,
            axis=alt.Axis(labelExpr="replace(format(datum.value * 100, '.0f'), '.', ',') + ' %'")),
    color=alt.Color("Classe:N", scale=alt.Scale(domain=list(CLASS_COLORS), range=list(CLASS_COLORS.values())),
                    legend=alt.Legend(orient="top", title=None)))
line = area.mark_line(strokeWidth=2.5, interpolate="monotone").encode(
    tooltip=[alt.Tooltip("Classe:N"), alt.Tooltip("range:N", title="Montant"), alt.Tooltip("share_fr:N", title="Part")])
k.altair_chart(chart_config(area + line, 300), use_container_width=True)

section("Tranches de montant", "Cliquez sur une tranche ou une case pour filtrer.")
l, r = st.columns([1, 1.3], gap="medium")
bd = view("band").groupby("band")[["transactions", "frauds"]].sum().reindex(BANDS).dropna()
bd["rate"] = bd["frauds"] / bd["transactions"]
k = card(l, "Taux de fraude par tranche")
click_bars(k, "band", bd, sub=lambda row: f"{fr(row['transactions'], 0)} transactions", key="am_bars_band",
           fmt=lambda v: pct(v, 2))
hv = view("band", "hour")
hv = hv[hv["day"] != "Regroupé"].copy()
hv["hgroup"] = pd.cut(hv["hour"].astype(int), [-1, 5, 11, 17, 23], labels=["00-05 h", "06-11 h", "12-17 h", "18-23 h"]).astype(str)
t = hv.groupby(["band", "hgroup"])[["transactions", "frauds"]].sum().reset_index()
t["rate"] = t["frauds"] / t["transactions"]
t["Tranche"] = t["band"].map(BAND_NAMES)
k = card(r, "Taux de fraude : tranche × moment de la journée", "Heures relatives regroupées par six. Valeurs en %.")
heatmap(k, t, "hgroup", "Tranche", "rate", ["00-05 h", "06-11 h", "12-17 h", "18-23 h"], [BAND_NAMES[b] for b in BANDS],
        t["rate"].map(lambda v: fr(100 * v, 2)), scale_max=0.02, dims=("band",), key="am_heat")
st.markdown("<div class='note'>L'unité de « Amount » n'est pas documentée par la source (vraisemblablement l'euro) : "
            "aucun symbole monétaire n'est affiché. Les tranches servent à la lecture, elles ne sont pas des seuils de "
            "décision.</div>", unsafe_allow_html=True)
footer()
