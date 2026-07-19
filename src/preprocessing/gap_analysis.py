"""Analyse des zones sous-desservies (locale, sans PostGIS)."""

from pathlib import Path

import geopandas as gpd


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data" / "vectors"

ARR_ANALYSE = DATA_DIR / "arrondissements_analyse.geojson"
COVERAGE = DATA_DIR / "zones_couverture.geojson"
OUT_GAPS = DATA_DIR / "zones_sous_desservies.geojson"


def run() -> dict:
    if not ARR_ANALYSE.exists() or not COVERAGE.exists():
        raise FileNotFoundError(
            "Sorties de la phase buffer manquantes. Executez d'abord src/preprocessing/buffer_analysis.py"
        )

    arr = gpd.read_file(ARR_ANALYSE).to_crs(epsg=32188)
    coverage = gpd.read_file(COVERAGE).to_crs(epsg=32188)

    union_geom = coverage.geometry.union_all()
    arr["geometry"] = arr.geometry.difference(union_geom)

    gaps = arr[~arr.geometry.is_empty].copy()
    gaps = gaps.to_crs(epsg=4326)
    gaps.to_file(OUT_GAPS, driver="GeoJSON")

    print(f"Zones sous-desservies exportees : {OUT_GAPS}")
    print(f"Arrondissements avec gaps : {len(gaps)}")

    top = (
        arr[["nom", "nb_bornes", "pct_couverture"]]
        .sort_values("pct_couverture", ascending=True)
        .head(10)
    )
    print("\nArrondissements les moins couverts :")
    print(f"{'Arrondissement':<35} {'Bornes':>6} {'Couverture':>10}")
    print("-" * 55)
    for _, row in top.iterrows():
        print(f"{row['nom']:<35} {int(row['nb_bornes']):>6} {float(row['pct_couverture']):>9.1f}%")

    return {
        "status": "ok",
        "zones_sous_desservies": str(OUT_GAPS),
        "rows": int(len(gaps)),
    }


if __name__ == "__main__":
    print(run())
