"""Tableau de bord EDA fraude carte bancaire : navigation, en-tête, filtres communs.

Lancer : streamlit run app.py
"""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent / "demo"))
from common import apply_styles, hero, sidebar_filters  # noqa: E402

st.set_page_config(page_title="Fraude carte bancaire", page_icon="💳", layout="wide", initial_sidebar_state="auto")
apply_styles()

PAGES = {
    "Pilotage": [
        st.Page("demo/views/overview.py", title="Synthèse", icon=":material/dashboard:", default=True),
    ],
    "Analyse": [
        st.Page("demo/views/temporal.py", title="Temps", icon=":material/schedule:"),
        st.Page("demo/views/distributions.py", title="Montants", icon=":material/payments:"),
        st.Page("demo/views/comparisons.py", title="Fraude vs normale", icon=":material/compare_arrows:"),
        st.Page("demo/views/correlations.py", title="Corrélations", icon=":material/grid_on:"),
    ],
    "Qualité": [
        st.Page("demo/views/method.py", title="Données et méthode", icon=":material/verified:"),
    ],
}
SUB = {
    "Synthèse": "284 807 transactions par carte sur deux jours (septembre 2013), dont 492 fraudes. Tout est "
                "interactif : cliquez sur un graphique ou utilisez les filtres de gauche.",
    "Temps": "Volume et taux de fraude selon l'heure relative et le jour de collecte. Le temps est compté depuis la "
             "première transaction : ce n'est pas une heure civile.",
    "Montants": "Distribution des montants des transactions normales et frauduleuses, par tranche et selon l'heure.",
    "Fraude vs normale": "Les 28 variables anonymisées (V1 à V28) comparées entre fraudes et transactions normales : "
                         "distance de Kolmogorov-Smirnov, taille d'effet et distributions.",
    "Corrélations": "Corrélations de Spearman entre les variables les plus discriminantes, le montant et le temps, "
                    "pour l'ensemble, les fraudes et les transactions normales.",
    "Données et méthode": "Source, contrôles de qualité, statistiques univariées, tests et limites de l'analyse.",
}
page = st.navigation(PAGES, position="sidebar")
group = next(g for g, items in PAGES.items() for p in items if p.title == page.title)
if page.title not in ("Corrélations", "Données et méthode"):
    sidebar_filters()
    with st.sidebar:
        st.markdown("<div class='sbnote'>Données publiques ULB / Worldline. Le tableau de bord lit uniquement des tables "
                    "agrégées : aucune transaction individuelle n'est affichée.</div>", unsafe_allow_html=True)
hero(f"{group} · Analyse exploratoire de la fraude", page.title, SUB[page.title])
page.run()
