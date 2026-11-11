# Données et provenance

## Source et version

L'analyse porte sur `creditcard.csv`, jeu « Credit Card Fraud Detection » attribué au Machine Learning Group de l'Université libre de Bruxelles et à Worldline, diffusé sur [Kaggle (mlg-ulb/creditcardfraud)](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud). Un dépôt pérenne, versionné `v1`, est archivé sur [Zenodo, DOI 10.5281/zenodo.7395559](https://doi.org/10.5281/zenodo.7395559) ; le descriptif Zenodo indique qu'il s'agit du jeu Kaggle et rapporte 284 807 transactions et 492 fraudes. Le CSV local fourni pour ce projet correspond au checksum attendu ci-dessous. Zenodo n'indique aucune licence dans ses métadonnées et la page Kaggle ne donne pas de licence explicite : la licence de redistribution reste donc **non confirmée**. Le fichier brut n'est ni commité ni redistribué.

Pour récupérer la version archivée : ouvrir [l'enregistrement Zenodo v1](https://zenodo.org/records/7395559), télécharger `creditcard.csv`, puis vérifier l'empreinte. La version, le nom de fichier et l'empreinte permettent d'identifier le contenu analysé sans dépendre d'une branche Git mutable.

```bash
shasum -a 256 data/creditcard.csv
# attendu : 76274b691b16a6c49d3f159c883398e03ccd6d1ee12d9d8ee38f4b4b98551a89
```

Le fichier analysé pèse 150 828 752 octets, contient 284 807 lignes et 31 colonnes. Son SHA-256 a été recalculé localement. `Time`, `Amount`, `Class` et `V1`–`V28` sont conservés tels que fournis. `Class=1` indique une fraude. L'unité monétaire de `Amount` n'est pas explicitée dans le fichier ; les visuels parlent donc de montant sans ajouter de symbole monétaire.

## Publication et confidentialité

Le fichier brut est ignoré par Git. Ne publiez pas le CSV, des échantillons de transactions ni des exports ligne à ligne. `python -m src.aggregates` produit, après contrôle de l'empreinte, les tables agrégées de `reports/aggregates/` : ce sont les seules données lues par le tableau de bord, en local comme en ligne. Aucune cellule publiée ne compte moins de 5 transactions.

## Référence

Machine Learning Group, Université libre de Bruxelles & Worldline. *Credit Card Fraud Detection*. Version Kaggle référencée par l'archive Zenodo v1, DOI [10.5281/zenodo.7395559](https://doi.org/10.5281/zenodo.7395559). Conditions de réutilisation à confirmer auprès des ayants droit avant toute redistribution.
