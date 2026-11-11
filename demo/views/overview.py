"""Synthèse : volumes, fraudes, montants et premiers signaux."""
import sys
from pathlib import Path

import altair as alt
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import (BAND_NAMES, BANDS, GREEN, MINT, NEUTRAL, amount_view, card, click_bars, clickable, amount_quantile, donut,  # noqa: E402
                    filtered, footer, fr, insights, kpi_grid, lab, load, money, pct, scope_note,
                    section, view, _on)

d, excluded, sel = filtered()
scope_note(d, excluded, sel)
S = d.sum(numeric_only=True)
n, f = S["transactions"], S["frauds"]
m = load()["manifest"]
ah = amount_view()
med_n, med_f = amount_quantile(ah, 0, 0.5), amount_quantile(ah, 1, 0.5)

section("Volume et fraude")
kpi_grid([
    ("Transactions", fr(n, 0), f"sur {fr(m['rows'], 0)} au total"),
    ("Fraudes étiquetées", fr(f, 0), f"{pct(f / n, 3)} des transactions", "hl"),
    ("Montant total", money(S["amount"]), "unité source non documentée"),
    ("Montant fraudé", money(S["fraud_amount"]), f"{pct(S['fraud_amount'] / max(S['amount'], 1), 2)} du montant", "orange"),
])
section("Profil des montants")
kpi_grid([
    ("Montant médian, normales", med_n, "50 % des transactions normales en dessous"),
    ("Montant médian, fraudes", med_f if f else "—", "les fraudes portent souvent sur de petits montants",
     "orange"),
    ("Montant moyen d'une fraude", fr(S["fraud_amount"] / f, 2) if f else "—",
     f"contre {fr((S['amount'] - S['fraud_amount']) / max(n - f, 1), 2)} pour une transaction normale"),
    ("Doublons exacts", fr(S["duplicates"], 0), f"dont {fr(S['duplicate_frauds'], 0)} fraudes, signalés et conservés", "blue"),
])

section("Où se concentrent les fraudes")
c1, c2, c3 = st.columns(3, gap="medium")
dd = view("day").groupby("day")[["transactions", "frauds"]].sum().reindex(["J1", "J2"]).dropna()
k = card(c1, "Fraudes par jour", "Cliquez pour filtrer sur un jour.")
donut(k, [lab("day", x) for x in dd.index], list(dd["frauds"]), [GREEN, MINT], fr(dd["frauds"].sum(), 0), "fraudes",
      dim="day", codes=list(dd.index), key="ov_donut_day")
bd = view("band").groupby("band")[["transactions", "frauds", "amount", "fraud_amount"]].sum().reindex(BANDS).dropna()
k = card(c2, "Fraudes par tranche de montant", "Petits montants, montants moyens et montants élevés.")
groups = {"Moins de 1": ["0", "0-1"], "1 à 100": ["1-10", "10-50", "50-100"], "Plus de 100": ["100-500", "500-1000", "1000+"]}
vals = [bd.loc[[b for b in v if b in bd.index], "frauds"].sum() for v in groups.values()]
donut(k, list(groups), vals, [GREEN, MINT, NEUTRAL], fr(sum(vals), 0), "fraudes")
k = card(c3, "Montant fraudé par tranche", "Part du montant fraudé portée par chaque groupe de tranches.")
vals_a = [bd.loc[[b for b in v if b in bd.index], "fraud_amount"].sum() for v in groups.values()]
donut(k, list(groups), vals_a, [GREEN, MINT, NEUTRAL], money(sum(vals_a)), "montant fraudé", fmt=money)

l, r = st.columns([1.25, 1], gap="medium")
hv = view("hour")
hh = hv.groupby("hour")[["transactions", "frauds"]].sum().reindex([h for h in map(str, range(24))]).dropna().reset_index()
hh["rate"] = hh["frauds"] / hh["transactions"]
hh["rate_fr"] = hh["rate"].map(lambda v: pct(v, 2))
hh["n_fr"] = hh["transactions"].map(lambda v: fr(v, 0))
hh["h"] = hh["hour"].astype(int)
hh["on"] = _on(hh, ["hour"])
k = card(l, "Taux de fraude par heure relative", "Barres : taux de fraude. Cliquez sur une heure pour filtrer.")
bars = alt.Chart(hh).mark_bar(color=GREEN, cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
    x=alt.X("hour:N", sort=list(map(str, range(24))), title="Heure relative", axis=alt.Axis(labelAngle=0)),
    y=alt.Y("rate:Q", title="Taux de fraude", axis=alt.Axis(labelExpr="replace(format(datum.value * 100, '.1f'), '.', ',') + ' %'")),
    opacity=alt.Opacity("on:Q", scale=alt.Scale(domain=[0, 1], range=[0.25, 1]), legend=None),
    tooltip=[alt.Tooltip("hour:N", title="Heure"), alt.Tooltip("rate_fr:N", title="Taux de fraude"),
             alt.Tooltip("frauds:Q", title="Fraudes"), alt.Tooltip("n_fr:N", title="Transactions")])
clickable(k, bars.add_params(alt.selection_point(name="pick", fields=["hour"])), ["hour"], "ov_hour", 280)
bt = bd.assign(rate=bd["frauds"] / bd["transactions"])
k = card(r, "Taux de fraude par tranche de montant", "Cliquez sur une tranche pour filtrer.")
click_bars(k, "band", bt, sub=lambda row: f"{fr(row['frauds'], 0)} fraudes", key="ov_bars_band",
           fmt=lambda v: pct(v, 2))

section("Points d'attention")
k = card()
items = []
if len(hh) > 3:
    top = hh.sort_values("rate", ascending=False).iloc[0]
    items.append(f"Heure relative la plus exposée : <b>{int(top['hour']):02d} h</b>, avec <b>{pct(top['rate'], 2)}</b> de "
                 f"fraudes contre <b>{pct(f / n, 3)}</b> en moyenne, sur un volume faible ({fr(top['transactions'], 0)} "
                 "transactions) : la nuit relative concentre moins d'activité mais plus de fraudes.")
if f and med_f != "—":
    items.append(f"Montant médian d'une fraude : <b>{med_f}</b> contre <b>{med_n}</b> pour une transaction "
                 "normale : beaucoup de fraudes testent la carte avec de petits montants.")
if len(bt) > 2:
    tb = bt.sort_values("rate", ascending=False).iloc[0]
    items.append(f"Tranche la plus exposée : <b>{BAND_NAMES[tb.name]}</b> ({pct(tb['rate'], 2)} de fraudes).")
t = load()["tests"].iloc[0]
items.append(f"Variable la plus discriminante sur le jeu complet : <b>{t['variable']}</b> (distance KS "
             f"{fr(t['ks_statistic'], 2)}) ; voir la page « Fraude vs normale ».")
items.append("Avec 0,17 % de fraudes, la précision globale n'a pas de sens pour un futur modèle : il faudra suivre le "
             "rappel, la précision sur les fraudes et l'aire sous la courbe précision-rappel.")
insights(k, items)
footer()
