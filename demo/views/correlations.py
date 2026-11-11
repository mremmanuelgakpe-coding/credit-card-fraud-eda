"""Corrélations : analyse multivariée des variables les plus discriminantes."""
import sys
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import GREEN, INK, card, chart_config, footer, fr, kpi_grid, load, section  # noqa: E402

L = load()
sp, tests = L["spearman"], L["tests"]


def off_diag(m):
    a = m.to_numpy()
    return a[~np.eye(len(a), dtype=bool)]


section("Structure des corrélations", "Corrélation de Spearman (rangs) entre les 10 variables les plus discriminantes, "
                                      "le montant et le temps. Calculée sur le jeu complet.")
pca10 = [c for c in sp["all"].columns if c.startswith("V")]
mean_abs = {k: float(np.abs(off_diag(v.loc[pca10, pca10])).mean()) for k, v in sp.items()}
kpi_grid([
    ("Corrélation moyenne, normales", fr(mean_abs["normal"], 2), "entre composantes, en valeur absolue"),
    ("Corrélation moyenne, fraudes", fr(mean_abs["fraud"], 2), "les fraudes forment un profil cohérent", "hl"),
    ("Le plus lié au montant", sp["all"]["Amount"].drop(["Amount", "Time"]).abs().idxmax(),
     f"corrélation {fr(sp['all']['Amount'].drop(['Amount', 'Time']).loc[sp['all']['Amount'].drop(['Amount', 'Time']).abs().idxmax()], 2)}"),
    ("Le plus lié au temps", sp["all"]["Time"].drop(["Amount", "Time"]).abs().idxmax(),
     f"corrélation {fr(sp['all']['Time'].drop(['Amount', 'Time']).loc[sp['all']['Time'].drop(['Amount', 'Time']).abs().idxmax()], 2)}",
     "blue"),
])

who = st.segmented_control("Population", ["Ensemble", "Fraudes", "Normales"], default="Fraudes", key="corr_pop")
key = {"Ensemble": "all", "Fraudes": "fraud", "Normales": "normal"}[who or "Fraudes"]
m = sp[key]
order = list(m.columns)
long = m.reset_index(names="a").melt("a", var_name="b", value_name="r")
long["txt"] = long["r"].map(lambda v: fr(v, 2))
l, r = st.columns([1.45, 1], gap="medium")
k = card(l, f"Matrice de Spearman : {who.lower() if who else 'fraudes'}", "Vert : corrélation positive ; gris foncé : "
                                                                          "négative ; blanc : pas de lien.")
rect = alt.Chart(long).mark_rect(stroke="#FFFFFF", strokeWidth=2, cornerRadius=4).encode(
    x=alt.X("b:N", sort=order, title=None, axis=alt.Axis(orient="top", labelAngle=-40, labelFontSize=14, ticks=False,
                                                         domain=False, labelOverlap=False)),
    y=alt.Y("a:N", sort=order, title=None, axis=alt.Axis(labelFontSize=14, ticks=False, domain=False)),
    color=alt.Color("r:Q", scale=alt.Scale(domain=[-1, 0, 1], range=["#2C3038", "#FFFFFF", GREEN]), legend=None),
    tooltip=[alt.Tooltip("a:N", title=" "), alt.Tooltip("b:N", title="  "), alt.Tooltip("txt:N", title="Spearman")])
txt = alt.Chart(long).mark_text(fontSize=14, fontWeight=600).encode(
    x=alt.X("b:N", sort=order), y=alt.Y("a:N", sort=order), text="txt:N",
    color=alt.condition("abs(datum.r) > 0.55", alt.value("#FFFFFF"), alt.value(INK)))
k.altair_chart(chart_config(rect + txt, 44 * len(order)).configure_axis(grid=False), use_container_width=True)

k = card(r, "Lien de chaque variable avec la fraude", "Taille d'effet rang-bisériale sur le jeu complet : à droite, "
                                                      "valeurs plus élevées chez les fraudes ; à gauche, plus basses.")
t = tests[tests["variable"].str.startswith("V")].copy().sort_values("rank_biserial")
t["eff"] = t["rank_biserial"].map(lambda v: fr(v, 2))
t["sign"] = np.where(t["rank_biserial"] >= 0, "pos", "neg")
bars = alt.Chart(t).mark_bar(height=12, cornerRadius=3).encode(
    y=alt.Y("variable:N", sort=list(t["variable"]), title=None,
            axis=alt.Axis(labelFontSize=14, ticks=False, domain=False, labelOverlap=False)),
    x=alt.X("rank_biserial:Q", title="Taille d'effet", scale=alt.Scale(domain=[-1, 1]),
            axis=alt.Axis(labelExpr="replace(format(datum.value, '.1f'), '.', ',')")),
    color=alt.Color("sign:N", scale=alt.Scale(domain=["pos", "neg"], range=[GREEN, "#2C3038"]), legend=None),
    tooltip=[alt.Tooltip("variable:N", title="Variable"), alt.Tooltip("eff:N", title="Effet")])
k.altair_chart(chart_config(bars, 22 * len(t)), use_container_width=True)

pairs = []
mf = sp["fraud"].loc[pca10, pca10]
for i, a in enumerate(pca10):
    for b in pca10[i + 1:]:
        pairs.append((a, b, float(mf.loc[a, b]), float(sp["normal"].loc[a, b])))
p = pd.DataFrame(pairs, columns=["a", "b", "fraud", "normal"]).assign(gap=lambda x: (x["fraud"] - x["normal"]).abs())
p = p.sort_values("gap", ascending=False).head(3)
st.markdown("<div class='note'><b>Lecture.</b> Les composantes d'une ACP sont décorrélées par construction sur l'ensemble "
            "des données ; chez les fraudes, elles bougent ensemble. Plus forts écarts fraudes / normales : "
            + " ; ".join(f"{r.a} et {r.b} ({fr(r.fraud, 2)} contre {fr(r.normal, 2)})" for r in p.itertuples())
            + ". Une corrélation n'est pas une causalité.</div>", unsafe_allow_html=True)
footer()
