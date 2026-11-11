"""Temps : activité et fraude selon l'heure relative et le jour de collecte."""
import sys
from pathlib import Path

import altair as alt
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import (GREEN, HOURS, INK_RAMP, MINT, card, clickable, filtered, footer, fr, heatmap, kpi_grid,  # noqa: E402
                    pct, scope_note, section, view, _on)

d, excluded, sel = filtered()
scope_note(d, excluded, sel)
S = d.sum(numeric_only=True)
n, f = S["transactions"], S["frauds"]
hv = view("hour")
hh = hv.groupby("hour")[["transactions", "frauds"]].sum().reindex(HOURS).dropna().reset_index()
hh["rate"] = hh["frauds"] / hh["transactions"]
night = hh[hh["hour"].astype(int) <= 6]

section("Rythme de l'activité")
peak = hh.sort_values("transactions", ascending=False).iloc[0] if len(hh) else None
risk = hh[hh["transactions"] >= 500].sort_values("rate", ascending=False)
risk = risk.iloc[0] if len(risk) else None
kpi_grid([
    ("Transactions par heure", fr(n / max(len(hh), 1), 0), f"en moyenne, sur {len(hh)} heures relatives"),
    ("Heure de pointe", f"{int(peak['hour']):02d} h" if peak is not None else "—",
     f"{fr(peak['transactions'], 0)} transactions" if peak is not None else ""),
    ("Heure la plus risquée", f"{int(risk['hour']):02d} h" if risk is not None else "—",
     f"{pct(risk['rate'], 2)} de fraudes (heures d'au moins 500 transactions)" if risk is not None else "", "hl"),
    ("Fraudes entre 0 h et 6 h", pct(night["frauds"].sum() / max(f, 1), 0) if f else "—",
     f"pour {pct(night['transactions'].sum() / max(n, 1), 0)} des transactions", "orange"),
])

section("Volume et taux de fraude par heure relative", "Cliquez sur une barre pour filtrer une heure.")
l, r = st.columns(2, gap="medium")
hh["on"] = _on(hh, ["hour"])
hh["n_fr"], hh["rate_fr"] = hh["transactions"].map(lambda v: fr(v, 0)), hh["rate"].map(lambda v: pct(v, 2))
base = alt.Chart(hh).encode(x=alt.X("hour:N", sort=HOURS, title="Heure relative", axis=alt.Axis(labelAngle=0)))
tip = [alt.Tooltip("hour:N", title="Heure"), alt.Tooltip("n_fr:N", title="Transactions"),
       alt.Tooltip("frauds:Q", title="Fraudes"), alt.Tooltip("rate_fr:N", title="Taux de fraude")]
k = card(l, "Transactions", "Volume de transactions par heure relative.")
vol = base.mark_bar(color=MINT, cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
    y=alt.Y("transactions:Q", title="Transactions", axis=alt.Axis(labelExpr="replace(format(datum.value, ',.0f'), /,/g, ' ')")),
    opacity=alt.Opacity("on:Q", scale=alt.Scale(domain=[0, 1], range=[0.3, 1]), legend=None), tooltip=tip)
clickable(k, vol.add_params(alt.selection_point(name="pick", fields=["hour"])), ["hour"], "tm_vol", 280)
k = card(r, "Taux de fraude", "Part des transactions frauduleuses, même découpage.")
rate = base.mark_bar(color=GREEN, cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
    y=alt.Y("rate:Q", title="Taux de fraude", axis=alt.Axis(labelExpr="replace(format(datum.value * 100, '.1f'), '.', ',') + ' %'")),
    opacity=alt.Opacity("on:Q", scale=alt.Scale(domain=[0, 1], range=[0.25, 1]), legend=None), tooltip=tip)
clickable(k, rate.add_params(alt.selection_point(name="pick", fields=["hour"])), ["hour"], "tm_rate", 280)

section("Grilles jour × heure", "Chaque case : une heure relative d'un jour de collecte. Cliquez sur une case pour "
                                "filtrer le jour et l'heure.")
g = view("day", "hour")
g = g[g["day"] != "Regroupé"].groupby(["day", "hour"])[["transactions", "frauds"]].sum().reset_index()
g["rate"] = g["frauds"] / g["transactions"]
g["Jour"], g["Heure"] = g["day"].map({"J1": "Jour 1", "J2": "Jour 2"}), g["hour"].map(lambda h: f"{int(h):02d}")
order_h = [f"{h:02d}" for h in range(24)]
k = card(None, "Taux de fraude", "Plus la case est foncée, plus la part de fraudes est élevée.")
heatmap(k, g, "Heure", "Jour", "rate", order_h, ["Jour 1", "Jour 2"], g["rate"].map(lambda v: fr(100 * v, 1)),
        scale_max=0.02, dims=("hour", "day"), key="tm_heat_rate")
k = card(None, "Nombre de fraudes", "Fraudes étiquetées dans chaque heure relative.")
heatmap(k, g, "Heure", "Jour", "frauds", order_h, ["Jour 1", "Jour 2"], g["frauds"].map(lambda v: fr(v, 0)),
        ramp=INK_RAMP, dims=("hour", "day"), key="tm_heat_n")
st.markdown("<div class='note'>Valeurs du taux en %. « Time » compte les secondes depuis la première transaction : "
            "l'heure relative 0 n'est pas forcément minuit. Le creux d'activité vers les heures 1 à 6 évoque la nuit, sans "
            "certitude sur le fuseau ni sur l'heure de départ.</div>", unsafe_allow_html=True)
footer()
