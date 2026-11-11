"""Données et méthode : source, qualité, statistiques univariées, hypothèses et limites."""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import GITHUB_URL, card, footer, fr, kpi_grid, load, pct, section  # noqa: E402

L = load()
m, u = L["manifest"], L["univariate"]

section("Qualité des données", f"Fichier source vérifié par empreinte SHA-256 : {m['source_sha256'][:16]}…")
kpi_grid([
    ("Transactions", fr(m["rows"], 0), f"{m['columns']} colonnes : Time, Amount, Class, V1 à V28"),
    ("Valeurs manquantes", fr(m["missing_values"], 0), "aucune imputation nécessaire", "hl"),
    ("Doublons exacts", fr(m["duplicate_rows"], 0), f"dont {m['duplicate_frauds']} fraudes : signalés, non supprimés", "orange"),
    ("Durée couverte", f"{fr(m['time_max_seconds'] / 3600, 1)} h", "deux jours de septembre 2013", "blue"),
])

section("La démarche")
st.markdown("""<div class='steps'>
<div class='step'><b>1 · Contrôle</b><p>Schéma, types, valeurs manquantes, doublons, classes 0/1, montants et temps
positifs. Rien n'est supprimé en silence : une anomalie bloque le chargement.</p></div>
<div class='step'><b>2 · Univarié</b><p>Médiane, quartiles, asymétrie et valeurs atypiques (règle de l'écart
interquartile) pour chaque variable.</p></div>
<div class='step'><b>3 · Bivarié</b><p>Fraudes contre normales : tests de Mann-Whitney et de Kolmogorov-Smirnov, taille
d'effet, correction de Benjamini-Hochberg pour 30 tests.</p></div>
<div class='step'><b>4 · Multivarié</b><p>Corrélations de Spearman, profils temporels et croisements jour × heure ×
montant, publiés uniquement sous forme agrégée.</p></div>
</div>""", unsafe_allow_html=True)

section("Statistique univariée", "Les variables V sont centrées par la source ; leur forte asymétrie et leurs queues "
                                 "longues viennent en grande partie des fraudes.")
t = u[u["variable"] != "Class"].copy()
t["Variable"] = t["variable"]
t["Médiane"] = t["median"].map(lambda v: fr(v, 3))
t["Écart interquartile"] = (t["q3"] - t["q1"]).map(lambda v: fr(v, 3))
t["Asymétrie"] = t["skewness"].map(lambda v: fr(v, 2))
t["Valeurs atypiques"] = (t["outlier_iqr_count"] / t["n"]).map(lambda v: pct(v, 1))
t["Min"], t["Max"] = t["min"].map(lambda v: fr(v, 2)), t["max"].map(lambda v: fr(v, 2))
st.dataframe(t[["Variable", "Médiane", "Écart interquartile", "Asymétrie", "Valeurs atypiques", "Min", "Max"]],
             hide_index=True, use_container_width=True, height=380)

l, r = st.columns(2, gap="medium")
k = card(l, "Hypothèses pour un futur modèle")
k.markdown("""<div class='ins'><span class='ins-dot'></span><div>V14, V10, V12, V4 et V11 séparent le mieux les fraudes :
elles devraient porter l'essentiel du signal d'un modèle.</div></div>
<div class='ins'><span class='ins-dot'></span><div>Le taux de fraude varie fortement selon l'heure relative : une variable
cyclique (heure) peut aider, à valider sur une période plus longue.</div></div>
<div class='ins'><span class='ins-dot'></span><div>Les petits montants (1 ou moins) sont surreprésentés parmi les fraudes :
à croiser avec la fréquence des transactions par carte, absente de ce jeu.</div></div>
<div class='ins'><span class='ins-dot'></span><div>Avec 0,17 % de fraudes, il faudra un découpage chronologique, des
métriques adaptées (précision-rappel) et un coût d'erreur explicite.</div></div>""", unsafe_allow_html=True)
k = card(r, "Limites")
k.markdown(f"""<div class='ins'><span class='ins-dot'></span><div>Jeu historique : deux jours de septembre 2013, porteurs
européens. Les fraudes ont évolué depuis.</div></div>
<div class='ins'><span class='ins-dot'></span><div>V1 à V28 sont des composantes d'ACP anonymisées : aucune interprétation
métier possible.</div></div>
<div class='ins'><span class='ins-dot'></span><div>« Time » est relatif à la première transaction ; « Amount » n'a pas
d'unité documentée.</div></div>
<div class='ins'><span class='ins-dot'></span><div>Des écarts significatifs ne prouvent aucune causalité. Aucun modèle n'est
entraîné dans ce projet.</div></div>
<div class='ins'><span class='ins-dot'></span><div>Code, tests et tables agrégées :
<a href='{GITHUB_URL}' target='_blank' rel='noopener noreferrer'>dépôt GitHub</a>.</div></div>""", unsafe_allow_html=True)
footer()
