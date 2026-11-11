"""Generate aggregate-only EDA outputs from the locally ignored ULB CSV."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.analysis import (  # noqa: E402
    class_comparison, hourly_profile, load_csv, quality_report,
    sha256_file, summary, univariate_report,
)

DATA = ROOT / "data" / "creditcard.csv"
OUT = ROOT / "reports"
EXPECTED_SHA256 = "76274b691b16a6c49d3f159c883398e03ccd6d1ee12d9d8ee38f4b4b98551a89"


def main() -> None:
    if not DATA.exists():
        raise SystemExit("CSV réel absent. Placez le fichier validé dans data/creditcard.csv ; le jeu synthétique ne sert pas aux résultats du rapport.")
    digest = sha256_file(DATA)
    if digest != EXPECTED_SHA256:
        raise SystemExit(f"SHA-256 inattendu ({digest}); vérifiez data/README.md avant de produire les résultats.")
    df = load_csv(DATA)
    quality = quality_report(df)
    stats = summary(df)
    OUT.mkdir(exist_ok=True)
    univariate_report(df).to_csv(OUT / "descriptifs_agreges.csv", index=False)
    hourly_profile(df).to_csv(OUT / "profil_temporel_agrege.csv", index=False)
    comparisons = class_comparison(df)
    comparisons.to_csv(OUT / "comparaisons_agregees.csv", index=False)
    top = comparisons.head(10)
    top_text = "\n".join(
        f"| {r.variable} | {r.ks_statistic:.4f} | {r.rank_biserial:.4f} | {r.ks_p_bh:.3g} |"
        for r in top.itertuples()
    )
    report = f"""# Résultats EDA calculés

Source : CSV local vérifié, SHA-256 `{digest}`. Les CSV produits ne contiennent que des statistiques agrégées.

## Résumé

- Transactions : {stats['transactions']:,}
- Fraudes : {stats['frauds']:,} ({stats['rate']:.4f} %)
- Valeur médiane de Amount (unité source non documentée) : {stats['median_amount']:.2f}
- Lignes dupliquées exactes (signalées, non retirées) : {quality['duplicate_rows']:,}
- Valeurs manquantes : {sum(quality['missing_by_column'].values()):,}
- Empreinte : `{digest}`

## Variables classées par distance KS

| Variable | D KS | Effet rank-bisérial | p KS ajustée BH |
|---|---:|---:|---:|
{top_text}

## Qualité

Dimensions : {quality['rows']:,} lignes × {quality['columns']} colonnes. Types et variables atypiques : `descriptifs_agreges.csv`. Profil horaire relatif : `profil_temporel_agrege.csv`. Comparaisons complètes (Mann–Whitney, KS, effets et p-values ajustées) : `comparaisons_agregees.csv`.

Les composantes PCA sont anonymisées et les associations ne démontrent pas de causalité. `Time` est un temps relatif; l'unité monétaire n'est pas connue. L'analyse ne construit aucun modèle.
"""
    (OUT / "rapport_resultats.md").write_text(report, encoding="utf-8")
    print(f"Rapport agrégé généré dans {OUT}; {stats['transactions']} lignes analysées.")


if __name__ == "__main__":
    main()
