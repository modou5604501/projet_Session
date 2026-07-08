"""
Import des données Montréal dans PostGIS.
Couches : bornes de recharge, arrondissements, stations de métro STM.
"""

import os
import json
import geopandas as gpd
from sqlalchemy import create_engine, text

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://georisk_user:georisk2019@localhost:5433/georisk"
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "vectors")


def get_engine():
    return create_engine(DB_URL)


def import_bornes(engine):
    path = os.path.join(DATA_DIR, "bornes_recharge_montreal.geojson")
    gdf = gpd.read_file(path)
    gdf = gdf.to_crs(epsg=4326)

    # Normalisation des colonnes
    col_map = {}
    cols = [c.lower() for c in gdf.columns]
    for orig, lower in zip(gdf.columns, cols):
        col_map[orig] = lower
    gdf = gdf.rename(columns=col_map)

    keep = ["geometry"]
    for c in ["nom", "name", "type", "arrondissement", "nb_prises"]:
        if c in gdf.columns:
            keep.append(c)

    gdf = gdf[keep].copy()
    if "name" in gdf.columns and "nom" not in gdf.columns:
        gdf = gdf.rename(columns={"name": "nom"})

    gdf.to_postgis("bornes_recharge", engine, if_exists="replace",
                   index=False, chunksize=500)
    print(f"Bornes importées : {len(gdf)} entités")


def import_arrondissements(engine):
    path = os.path.join(DATA_DIR, "arrondissements_montreal.geojson")
    gdf = gpd.read_file(path)
    gdf = gdf.to_crs(epsg=4326)

    col_map = {c: c.lower() for c in gdf.columns}
    gdf = gdf.rename(columns=col_map)

    for c in ["nom", "name"]:
        if c in gdf.columns:
            gdf = gdf.rename(columns={c: "nom"}) if c != "nom" else gdf
            break

    gdf = gdf[["nom", "geometry"]].copy() if "nom" in gdf.columns else gdf[["geometry"]].copy()
    gdf["nb_bornes"]      = 0
    gdf["pct_couverture"] = 0.0

    gdf.to_postgis("arrondissements", engine, if_exists="replace",
                   index=False, chunksize=100)
    print(f"Arrondissements importés : {len(gdf)} entités")


def import_metro(engine):
    # Fichier arrêts STM (extrait dans stm_sig/)
    shp = os.path.join(DATA_DIR, "stm_sig", "stm_arrets_sig.shp")
    if not os.path.exists(shp):
        print("Fichier STM arrêts introuvable — import métro ignoré")
        return

    gdf = gpd.read_file(shp)
    gdf = gdf.to_crs(epsg=4326)

    # Filtrer stations de métro : stop_url contient "metro" + loc_type=0 (station principale)
    metro_mask = (
        gdf["stop_url"].fillna("").str.contains("metro", case=False) &
        (gdf["loc_type"] == 0)
    )
    gdf = gdf[metro_mask].copy()

    gdf = gdf.rename(columns={"stop_name": "nom"})
    gdf = gdf[["nom", "geometry"]].copy()
    gdf["ligne"] = None

    gdf.to_postgis("stations_metro", engine, if_exists="replace",
                   index=False, chunksize=200)
    print(f"Stations métro importées : {len(gdf)} entités")


def create_coverage_buffers(engine):
    """Génère les buffers 500m autour de chaque borne (en MTM8 pour précision)."""
    sql = """
    TRUNCATE zones_couverture;
    INSERT INTO zones_couverture (borne_id, rayon_m, geom)
    SELECT
        id,
        500,
        ST_Transform(
            ST_Buffer(ST_Transform(geom, 32188), 500),
            4326
        )
    FROM bornes_recharge;
    """
    with engine.connect() as conn:
        for stmt in sql.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                conn.execute(text(stmt))
        conn.commit()
    print("Buffers 500m générés")


def update_arrondissement_stats(engine):
    """Calcule nb_bornes et pct_couverture par arrondissement."""
    sql = """
    UPDATE arrondissements a
    SET nb_bornes = (
        SELECT COUNT(*) FROM bornes_recharge b
        WHERE ST_Within(b.geom, a.geom)
    );

    UPDATE arrondissements a
    SET pct_couverture = ROUND(
        100.0 * ST_Area(
            ST_Intersection(
                ST_Union(zc.geom),
                a.geom
            )
        ) / NULLIF(ST_Area(a.geom), 0),
        1
    )
    FROM zones_couverture zc
    WHERE ST_Intersects(zc.geom, a.geom)
    GROUP BY a.id, a.geom;
    """
    with engine.connect() as conn:
        for stmt in sql.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                try:
                    conn.execute(text(stmt))
                except Exception as e:
                    print(f"Stats arrondissement (partiel) : {e}")
        conn.commit()
    print("Statistiques arrondissements mises à jour")


if __name__ == "__main__":
    engine = get_engine()
    import_bornes(engine)
    import_arrondissements(engine)
    import_metro(engine)
    create_coverage_buffers(engine)
    update_arrondissement_stats(engine)
    print("Import terminé.")
