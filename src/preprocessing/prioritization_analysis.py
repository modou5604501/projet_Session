"""
Analyse de priorisation des zones a developper pour de nouvelles bornes.

Le score combine 5 indicateurs:
- deficit de couverture
- distance reseau routier au chargeur le plus proche
- demographie (population + densite)
- pression d'equipement (peu de bornes = score plus eleve)
- potentiel de demande (proxy: nombre de stations metro)
- criticite (< 30% de couverture)

Sorties:
- data/vectors/priorites_arrondissements.csv
- data/vectors/priorites_arrondissements.geojson
"""

import os
from pathlib import Path

import geopandas as gpd
import networkx as nx
import osmnx as ox
import pandas as pd
from sqlalchemy import create_engine


DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://georisk_user:georisk2019@localhost:5433/georisk",
)

ROOT_DIR = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT_DIR / "data" / "vectors"
OUT_CSV = OUT_DIR / "priorites_arrondissements.csv"
OUT_GEOJSON = OUT_DIR / "priorites_arrondissements.geojson"
DEMO_GEOJSON = OUT_DIR / "demographie_quebec.geojson"


def _minmax(series: pd.Series) -> pd.Series:
    lo = float(series.min())
    hi = float(series.max())
    if hi == lo:
        return pd.Series([0.0] * len(series), index=series.index)
    return (series - lo) / (hi - lo)


def _priority_label(score: float) -> str:
    if score >= 0.67:
        return "elevee"
    if score >= 0.34:
        return "moyenne"
    return "faible"


def _build_demography_index(arr_gdf: gpd.GeoDataFrame) -> tuple[pd.Series, str]:
    """Construit un indice demographique [0,1] par arrondissement."""
    if not DEMO_GEOJSON.exists():
        raise FileNotFoundError(
            f"Fichier demographique manquant: {DEMO_GEOJSON}. "
            "Generez-le d'abord avec src/acquisition/download_demographie_quebec.R."
        )

    demo = gpd.read_file(DEMO_GEOJSON)
    if demo.empty:
        raise ValueError("Le fichier demographique est vide")

    pop_col = None
    dens_col = None
    for candidate in [
        "population_totale",
        "population",
        "pop_total",
        "pop",
        "value",
    ]:
        if candidate in demo.columns:
            pop_col = candidate
            break

    for candidate in ["densite_hab_km2", "Habkm2", "densite", "density"]:
        if candidate in demo.columns:
            dens_col = candidate
            break

    if pop_col is None and dens_col is None:
        raise ValueError(
            "Colonnes demographiques introuvables dans demographie_quebec.geojson "
            "(attendu population_totale|population|... et/ou densite_hab_km2|Habkm2)"
        )

    arr4326 = arr_gdf.to_crs(epsg=4326).copy()
    demo4326 = demo.to_crs(epsg=4326).copy()

    select_cols = ["geometry"]
    if pop_col is not None:
        select_cols.append(pop_col)
    if dens_col is not None:
        select_cols.append(dens_col)

    joined = gpd.overlay(demo4326[select_cols], arr4326[["id", "geometry"]], how="intersection")
    if joined.empty:
        raise ValueError("Aucun recouvrement spatial entre demographie et arrondissements")

    joined_m = joined.to_crs(epsg=32188)
    joined_m["area_m2"] = joined_m.geometry.area
    if pop_col is not None:
        joined_m["pop_weighted"] = joined_m[pop_col].astype(float) * joined_m["area_m2"]
    if dens_col is not None:
        joined_m["dens_weighted"] = joined_m[dens_col].astype(float) * joined_m["area_m2"]

    agg_dict = {"overlap_area_m2": ("area_m2", "sum")}
    if pop_col is not None:
        agg_dict["pop_weighted"] = ("pop_weighted", "sum")
    if dens_col is not None:
        agg_dict["dens_weighted"] = ("dens_weighted", "sum")
    agg = joined_m.groupby("id", as_index=False).agg(**agg_dict)

    arr_m = arr4326.to_crs(epsg=32188).copy()
    arr_m["arr_area_m2"] = arr_m.geometry.area
    arr_m = arr_m.merge(agg, on="id", how="left")
    if arr_m["overlap_area_m2"].isna().any():
        missing_ids = arr_m.loc[arr_m["overlap_area_m2"].isna(), "id"].tolist()
        raise ValueError(
            "Demographie incomplete: aucun recouvrement pour certains arrondissements "
            f"(ids={missing_ids})"
        )

    if pop_col is not None:
        if arr_m["pop_weighted"].isna().any():
            missing_ids = arr_m.loc[arr_m["pop_weighted"].isna(), "id"].tolist()
            raise ValueError(
                "Demographie incomplete: population absente pour certains arrondissements "
                f"(ids={missing_ids})"
            )
        arr_m["population_estimee"] = arr_m["pop_weighted"] / arr_m["arr_area_m2"]
    else:
        arr_m["population_estimee"] = pd.NA

    if dens_col is not None:
        if arr_m["dens_weighted"].isna().any():
            missing_ids = arr_m.loc[arr_m["dens_weighted"].isna(), "id"].tolist()
            raise ValueError(
                "Demographie incomplete: densite absente pour certains arrondissements "
                f"(ids={missing_ids})"
            )
        arr_m["densite_pop_km2"] = arr_m["dens_weighted"] / arr_m["arr_area_m2"]
    elif pop_col is not None:
        arr_m["densite_pop_km2"] = arr_m["population_estimee"] / (arr_m["arr_area_m2"] / 1_000_000.0)
    else:
        raise ValueError("Impossible de calculer un indicateur demographique exploitable")

    if pop_col is not None:
        pop_n = _minmax(arr_m["population_estimee"].astype(float))
        dens_n = _minmax(arr_m["densite_pop_km2"].astype(float))
        demo_index = 0.6 * pop_n + 0.4 * dens_n
    else:
        demo_index = _minmax(arr_m["densite_pop_km2"].astype(float))
    demo_index.index = arr_gdf.index

    arr_gdf["population_estimee"] = arr_m["population_estimee"].values
    arr_gdf["densite_pop_km2"] = arr_m["densite_pop_km2"].values

    if pop_col is not None and dens_col is not None:
        src = "population_plus_densite"
    elif pop_col is not None:
        src = "population_only"
    else:
        src = "densite_only"
    return demo_index, f"demographie_quebec_geojson:{src}"


def _compute_road_distance_km(arr_gdf: gpd.GeoDataFrame, bornes_gdf: gpd.GeoDataFrame) -> pd.Series:
    """Distance route (km) entre centroides d'arrondissements et chargeur le plus proche."""
    if bornes_gdf.empty:
        return pd.Series([None] * len(arr_gdf), index=arr_gdf.index, dtype="float64")

    minx, miny, maxx, maxy = arr_gdf.total_bounds
    graph = ox.graph_from_bbox(maxy, miny, maxx, minx, network_type="drive", simplify=True)
    graph = ox.project_graph(graph)
    graph_crs = graph.graph.get("crs")

    arr_proj = arr_gdf.to_crs(graph_crs).copy()
    bornes_proj = bornes_gdf.to_crs(graph_crs).copy()

    # Representative point pour rester dans le polygone.
    arr_pts = arr_proj.geometry.representative_point()
    borne_pts = bornes_proj.geometry

    arr_nodes = ox.distance.nearest_nodes(graph, arr_pts.x.values, arr_pts.y.values)
    borne_nodes = ox.distance.nearest_nodes(graph, borne_pts.x.values, borne_pts.y.values)
    borne_nodes = list(set(borne_nodes))

    # Distance minimale de chaque noeud vers l'ensemble des chargeurs.
    dist_map = nx.multi_source_dijkstra_path_length(graph, sources=borne_nodes, weight="length")

    values_km = []
    for node in arr_nodes:
        dist_m = dist_map.get(node)
        values_km.append((dist_m / 1000.0) if dist_m is not None else None)

    return pd.Series(values_km, index=arr_gdf.index, dtype="float64")


def run() -> dict:
    engine = create_engine(DB_URL)

    sql = """
        SELECT
            a.id,
            a.nom,
            COALESCE(a.nb_bornes, 0) AS nb_bornes,
            COALESCE(a.pct_couverture, 0.0) AS pct_couverture,
            COALESCE(m.metro_count, 0) AS metro_count,
            a.geom
        FROM arrondissements a
        LEFT JOIN (
            SELECT a2.id, COUNT(sm.id) AS metro_count
            FROM arrondissements a2
            LEFT JOIN stations_metro sm
                ON ST_Within(sm.geom, a2.geom)
            GROUP BY a2.id
        ) m ON m.id = a.id
        ORDER BY a.nom
    """

    gdf = gpd.read_postgis(sql, engine, geom_col="geom")
    if gdf.empty:
        return {"status": "error", "message": "Aucun arrondissement trouve"}

    bornes_sql = "SELECT id, geom FROM bornes_recharge"
    bornes_gdf = gpd.read_postgis(bornes_sql, engine, geom_col="geom")

    try:
        gdf["distance_reseau_km"] = _compute_road_distance_km(gdf, bornes_gdf)
        road_source = "osm_road_network"
    except Exception as exc:
        # Fallback pour garder un resultat exploitable si OSM indisponible.
        arr_m = gdf.to_crs(epsg=32188).copy()
        br_m = bornes_gdf.to_crs(epsg=32188).copy() if not bornes_gdf.empty else bornes_gdf
        if br_m.empty:
            gdf["distance_reseau_km"] = None
        else:
            arr_points = arr_m.geometry.representative_point()
            nearest = []
            for pt in arr_points:
                nearest.append(br_m.distance(pt).min() / 1000.0)
            gdf["distance_reseau_km"] = nearest
        road_source = f"fallback_euclidean:{exc.__class__.__name__}"

    demo_index, demography_source = _build_demography_index(gdf)

    # Indicateurs bruts
    gdf["deficit_couverture"] = 100.0 - gdf["pct_couverture"].astype(float)
    gdf["distance_reseau_km"] = gdf["distance_reseau_km"].fillna(gdf["distance_reseau_km"].max())
    gdf["indice_demographie"] = demo_index
    gdf["pression_equipement"] = 1.0 / (gdf["nb_bornes"].astype(float) + 1.0)
    gdf["potentiel_demande"] = gdf["metro_count"].astype(float)
    gdf["criticite"] = ((30.0 - gdf["pct_couverture"].astype(float)).clip(lower=0.0) / 30.0)

    # Normalisation [0,1]
    gdf["n_deficit"] = _minmax(gdf["deficit_couverture"])
    gdf["n_distance_reseau"] = _minmax(gdf["distance_reseau_km"])
    gdf["n_demographie"] = _minmax(gdf["indice_demographie"])
    gdf["n_pression"] = _minmax(gdf["pression_equipement"])
    gdf["n_demande"] = _minmax(gdf["potentiel_demande"])
    gdf["n_criticite"] = _minmax(gdf["criticite"])

    # Score multicritere
    gdf["score_priorite"] = (
        0.25 * gdf["n_deficit"]
        + 0.25 * gdf["n_distance_reseau"]
        + 0.20 * gdf["n_demographie"]
        + 0.15 * gdf["n_demande"]
        + 0.10 * gdf["n_pression"]
        + 0.05 * gdf["n_criticite"]
    )

    gdf["priorite"] = gdf["score_priorite"].apply(_priority_label)
    gdf = gdf.sort_values("score_priorite", ascending=False).reset_index(drop=True)
    gdf["rang"] = gdf.index + 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    csv_cols = [
        "rang",
        "nom",
        "priorite",
        "score_priorite",
        "pct_couverture",
        "nb_bornes",
        "metro_count",
        "distance_reseau_km",
        "population_estimee",
        "densite_pop_km2",
        "deficit_couverture",
    ]
    gdf[csv_cols].to_csv(OUT_CSV, index=False)

    gdf.to_file(OUT_GEOJSON, driver="GeoJSON")

    top5 = gdf[["rang", "nom", "score_priorite", "priorite"]].head(5)
    print("Top 5 zones prioritaires:")
    for _, row in top5.iterrows():
        print(
            f"  #{int(row['rang']):02d} {row['nom']:<35} "
            f"score={row['score_priorite']:.3f}  priorite={row['priorite']}"
        )

    engine.dispose()
    return {
        "status": "ok",
        "csv": str(OUT_CSV),
        "geojson": str(OUT_GEOJSON),
        "rows": int(len(gdf)),
        "road_source": road_source,
        "demography_source": demography_source,
        "weights": {
            "deficit_couverture": 0.25,
            "distance_reseau": 0.25,
            "demographie": 0.20,
            "potentiel_demande": 0.15,
            "pression_equipement": 0.10,
            "criticite": 0.05,
        },
    }


if __name__ == "__main__":
    result = run()
    print(result)
