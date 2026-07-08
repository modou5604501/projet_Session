"""
Import des données Montréal dans PostGIS.
Couches : bornes de recharge, arrondissements, stations de métro STM.
"""

import os
import geopandas as gpd
from sqlalchemy import create_engine, text

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://georisk_user:georisk2019@localhost:5433/georisk"
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "vectors")


def get_engine():
    return create_engine(DB_URL)


def _truncate(engine, table, cascade=False):
    suffix = " CASCADE" if cascade else ""
    with engine.connect() as conn:
        conn.execute(text(f"TRUNCATE {table}{suffix}"))
        conn.commit()


def import_bornes(engine):
    path = os.path.join(DATA_DIR, "bornes_recharge_montreal.geojson")
    gdf = gpd.read_file(path)
    gdf = gdf.to_crs(epsg=4326)

    # Normaliser les noms de colonnes en minuscules
    gdf.columns = [c.lower() for c in gdf.columns]

    # Garder uniquement les colonnes du schéma SQL
    keep = []
    for c in ["nom", "name", "type", "arrondissement", "nb_prises"]:
        if c in gdf.columns:
            keep.append(c)
    gdf = gdf[keep + ["geometry"]].copy()

    if "name" in gdf.columns and "nom" not in gdf.columns:
        gdf = gdf.rename(columns={"name": "nom"})

    # Renommer geometry -> geom pour correspondre au schéma SQL
    gdf = gdf.rename_geometry("geom")

    _truncate(engine, "bornes_recharge", cascade=True)
    gdf.to_postgis("bornes_recharge", engine, if_exists="append",
                   index=False, chunksize=500)
    print(f"Bornes importées : {len(gdf)} entités")


def import_arrondissements(engine):
    path = os.path.join(DATA_DIR, "arrondissements_montreal.geojson")
    gdf = gpd.read_file(path)
    gdf = gdf.to_crs(epsg=4326)

    gdf.columns = [c.lower() for c in gdf.columns]

    if "name" in gdf.columns and "nom" not in gdf.columns:
        gdf = gdf.rename(columns={"name": "nom"})

    cols = ["geometry"]
    if "nom" in gdf.columns:
        cols = ["nom"] + cols
    gdf = gdf[cols].copy()
    gdf["nb_bornes"] = 0
    gdf["pct_couverture"] = 0.0

    gdf = gdf.rename_geometry("geom")

    _truncate(engine, "arrondissements")
    gdf.to_postgis("arrondissements", engine, if_exists="append",
                   index=False, chunksize=100)
    print(f"Arrondissements importés : {len(gdf)} entités")


def import_metro(engine):
    shp = os.path.join(DATA_DIR, "stm_sig", "stm_arrets_sig.shp")
    if not os.path.exists(shp):
        print("Fichier STM arrêts introuvable — import métro ignoré")
        return

    gdf = gpd.read_file(shp)
    gdf = gdf.to_crs(epsg=4326)

    # Stations de métro : stop_url contient "metro" + loc_type=0
    metro_mask = (
        gdf["stop_url"].fillna("").str.contains("metro", case=False) &
        (gdf["loc_type"] == 0)
    )
    gdf = gdf[metro_mask].copy()

    gdf = gdf.rename(columns={"stop_name": "nom"})
    gdf = gdf[["nom", "geometry"]].copy()
    gdf["ligne"] = None
    gdf = gdf.rename_geometry("geom")

    _truncate(engine, "stations_metro")
    gdf.to_postgis("stations_metro", engine, if_exists="append",
                   index=False, chunksize=200)
    print(f"Stations métro importées : {len(gdf)} entités")


def create_coverage_buffers(engine):
    """Génère les buffers 500m autour de chaque borne (MTM8 pour précision métrique)."""
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE zones_couverture"))
        conn.execute(text("""
            INSERT INTO zones_couverture (borne_id, rayon_m, geom)
            SELECT
                id,
                500,
                ST_Transform(
                    ST_Buffer(ST_Transform(geom, 32188), 500),
                    4326
                )
            FROM bornes_recharge
        """))
        conn.commit()
    print("Buffers 500m générés")


def update_arrondissement_stats(engine):
    """Calcule nb_bornes et pct_couverture par arrondissement."""
    with engine.connect() as conn:
        # Compter les bornes par arrondissement
        conn.execute(text("""
            UPDATE arrondissements a
            SET nb_bornes = (
                SELECT COUNT(*) FROM bornes_recharge b
                WHERE ST_Within(b.geom, a.geom)
            )
        """))
        conn.commit()

        # Calculer le % de couverture
        conn.execute(text("""
            UPDATE arrondissements a
            SET pct_couverture = ROUND(
                LEAST(
                    100.0 * ST_Area(
                        ST_Intersection(
                            COALESCE(
                                (SELECT ST_Union(zc.geom)
                                 FROM zones_couverture zc
                                 WHERE ST_Intersects(zc.geom, a.geom)),
                                ST_GeomFromText('GEOMETRYCOLLECTION EMPTY', 4326)
                            ),
                            a.geom
                        )::geography
                    ) / NULLIF(ST_Area(a.geom::geography), 0),
                    100
                )::numeric,
                1
            )
        """))
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
