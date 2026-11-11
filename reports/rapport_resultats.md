# Résultats EDA calculés

Source : CSV local vérifié, SHA-256 `76274b691b16a6c49d3f159c883398e03ccd6d1ee12d9d8ee38f4b4b98551a89`. Les CSV produits ne contiennent que des statistiques agrégées.

## Résumé

- Transactions : 284,807
- Fraudes : 492 (0.1727 %)
- Valeur médiane de Amount (unité source non documentée) : 22.00
- Lignes dupliquées exactes (signalées, non retirées) : 1,081
- Valeurs manquantes : 0
- Empreinte : `76274b691b16a6c49d3f159c883398e03ccd6d1ee12d9d8ee38f4b4b98551a89`

## Variables classées par distance KS

| Variable | D KS | Effet rank-bisérial | p KS ajustée BH |
|---|---:|---:|---:|
| V14 | 0.8428 | -0.8983 | 0 |
| V10 | 0.8043 | -0.8281 | 0 |
| V12 | 0.7839 | -0.8741 | 8.61e-320 |
| V4 | 0.7664 | 0.8765 | 1.53e-301 |
| V11 | 0.7561 | 0.8362 | 2.61e-291 |
| V17 | 0.7452 | -0.6164 | 6.94e-281 |
| V3 | 0.7037 | -0.8241 | 4.25e-244 |
| V16 | 0.6865 | -0.6943 | 3.51e-230 |
| V7 | 0.6606 | -0.6716 | 2.26e-210 |
| V2 | 0.6332 | 0.7099 | 6.49e-191 |

## Qualité

Dimensions : 284,807 lignes × 31 colonnes. Types et variables atypiques : `descriptifs_agreges.csv`. Profil horaire relatif : `profil_temporel_agrege.csv`. Comparaisons complètes (Mann–Whitney, KS, effets et p-values ajustées) : `comparaisons_agregees.csv`.

Les composantes PCA sont anonymisées et les associations ne démontrent pas de causalité. `Time` est un temps relatif; l'unité monétaire n'est pas connue. L'analyse ne construit aucun modèle.
