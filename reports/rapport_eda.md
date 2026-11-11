# Rapport EDA — transactions bancaires

Ce rapport est généré à partir du fichier brut présent localement, qui reste ignoré par Git. Pour le régénérer après contrôle du SHA-256 indiqué dans `data/README.md` : `python scripts/generate_report.py`. Les CSV de sortie sont des agrégats (descriptifs par variable, profils par heure et tests), sans transactions individuelles.

État du fichier local au 11 novembre 2026 : 284 807 lignes, 31 colonnes, SHA-256 `76274b691b16a6c49d3f159c883398e03ccd6d1ee12d9d8ee38f4b4b98551a89`. Vérification indépendante en lecture CSV : 492 fraudes sur 284 807 transactions (0,1727 %), 0 valeur vide et 1 081 lignes dupliquées exactement. Les doublons n'ont pas été retirés. La médiane d'Amount vaut 22,00 pour les 284 315 non-fraudes et 9,25 pour les 492 fraudes. Ces nombres sont cohérents avec l'enregistrement Zenodo v1 ; la médiane est calculée localement. L'unité d'Amount n'étant pas documentée, aucune devise n'est ajoutée.

## Résultats détaillés

Les tests ont été exécutés sur le fichier vérifié : voir [rapport_resultats.md](rapport_resultats.md) et les tables de
`aggregates/`. 27 des 28 composantes V diffèrent significativement entre fraudes et non-fraudes (KS, p corrigée BH
< 0,05) ; les plus discriminantes sont V14 (D = 0,84), V10 (0,80), V12 (0,78), V4 (0,77) et V11 (0,76). Le taux de
fraude atteint 1,71 % à l'heure relative 2, contre 0,17 % en moyenne.

## Règles de préparation

Les valeurs invalides des champs requis provoquent une erreur explicite. Les doublons sont mesurés et rapportés, sans suppression implicite. Aucune ligne n'est retirée pour calculer le rapport. Les tableaux exportés sont agrégés. Les p-values sont corrigées par Benjamini–Hochberg ; les effets et distributions doivent être lus conjointement à la significativité.

## Hypothèses à tester

1. Certaines composantes PCA et le montant ont des distributions distinctes selon la classe.
2. La fréquence de fraude varie selon le temps relatif.
3. Ces associations sont à confirmer sur des données plus récentes et chronologiques avant tout usage opérationnel.

## Limites

Le fichier documente deux jours de septembre 2013. `Time` n'est pas une heure civile, `Amount` n'a pas d'unité explicite et les composantes PCA ne sont pas interprétables par métier. Les résultats descriptifs ne démontrent aucune causalité et ne constituent pas un modèle.
