"""Analyse de couverture locale (sans PostGIS).

Calcule :
- buffers 500 m autour des bornes
- nombre de bornes par arrondissement
- nombre de stations de metro par arrondissement
- pourcentage de couverture par arrondissement

Sorties :
- data/vectors/zones_couverture.geojson
- data/vectors/arrondissements_analyse.geojson
"""

from pathlib import Path

import geopandas as gpd


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data" / "vectors"

BORNES_PATH = DATA_DIR / "bornes_recharge_montreal.geojson"
ARR_PATH = DATA_DIR / "arrondissements_montreal.geojson"
STM_PATH = DATA_DIR / "stm_sig" / "stm_arrets_sig.shp"

OUT_COVERAGE = DATA_DIR / "zones_couverture.geojson"
OUT_ARR = DATA_DIR / "arrondissements_analyse.geojson"


def _get_name_column(gdf: gpd.GeoDataFrame) -> str:
    for candidate in ["nom", "name", "arrondissement", "NOM"]:
        if candidate in gdf.columns:
            return candidate
    raise ValueError("Colonne de nom introuvable dans les arrondissements")


def _metro_points() -> gpd.GeoDataFrame:
    if not STM_PATH.exists():
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")

    stm = gpd.read_file(STM_PATH)
    stm = stm.to_crs(epsg=4326)
    if "stop_url" not in stm.columns or "loc_type" not in stm.columns:
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")

    metro_mask = (
        stm["stop_url"].fillna("").str.contains("metro", case=False)
        & (stm["loc_type"] == 0)
    )
    return stm.loc[metro_mask, ["geometry"]].copy()


def run() -> dict:
    if not BORNES_PATH.exists() or not ARR_PATH.exists():
        raise FileNotFoundError("Fichiers sources manquants dans data/vectors")

    bornes = gpd.read_file(BORNES_PATH).to_crs(epsg=4326)
    arr = gpd.read_file(ARR_PATH).to_crs(epsg=4326)
    name_col = _get_name_column(arr)

    arr = arr[[name_col, "geometry"]].copy()
    arr = arr.rename(columns={name_col: "nom"})
    arr["id"] = range(1, len(arr) + 1)

    bornes_m = bornes.to_crs(epsg=32188).copy()
    arr_m = arr.to_crs(epsg=32188).copy()

    coverage = bornes_m[["geometry"]].copy()
    coverage["rayon_m"] = 500
    coverage["geometry"] = coverage.geometry.buffer(500)
    coverage = coverage.set_crs(epsg=32188).to_crs(epsg=4326)
    coverage.to_file(OUT_COVERAGE, driver="GeoJSON")

    bornes_in_arr = gpd.sjoin(
        bornes_m[["geometry"]],
        arr_m[["id", "geometry"]],
        how="left",
        predicate="within",
    )
    nb_bornes = bornes_in_arr.groupby("id").size()
    arr["nb_bornes"] = arr["id"].map(nb_bornes).fillna(0).astype(int)

    metro = _metro_points().to_crs(epsg=32188)
    if metro.empty:
        arr["metro_count"] = 0
    else:
        metro_in_arr = gpd.sjoin(
            metro[["geometry"]],
            arr_m[["id", "geometry"]],
            how="left",
            predicate="within",
        )
        metro_count = metro_in_arr.groupby("id").size()
        arr["metro_count"] = arr["id"].map(metro_count).fillna(0).astype(int)

    union_geom = coverage.to_crs(epsg=32188).geometry.union_all()
    arr_m["arr_area_m2"] = arr_m.geometry.area
    arr_m["cov_area_m2"] = arr_m.geometry.intersection(union_geom).area
    arr["pct_couverture"] = ((arr_m["cov_area_m2"] / arr_m["arr_area_m2"]) * 100.0).round(1).clip(0, 100)

    arr.to_file(OUT_ARR, driver="GeoJSON")

    sous_desservis = int((arr["pct_couverture"] < 30).sum())
    print("Analyse de couverture locale terminee")
    print(f"Total bornes       : {len(bornes)}")
    print(f"Arrond. <30%       : {sous_desservis}")
    print(f"Couverture moyenne : {arr['pct_couverture'].mean():.1f}%")
    print(f"Sortie couverture  : {OUT_COVERAGE}")
    print(f"Sortie arrond.     : {OUT_ARR}")

    return {
        "status": "ok",
        "zones_couverture": str(OUT_COVERAGE),
        "arrondissements": str(OUT_ARR),
        "rows_arrondissements": int(len(arr)),
    }


if __name__ == "__main__":
    print(run())
