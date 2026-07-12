"""
Analyse des zones sous-desservies (gap analysis).
Identifie les zones de Montréal à plus de 500m de toute borne de recharge.
"""

import os
import geopandas as gpd
from sqlalchemy import create_engine, text

_raw_db_url = os.getenv(
    "DATABASE_URL",
    "postgresql://georisk_user:georisk2019@localhost:5433/georisk"
)
DB_URL = _raw_db_url.replace("postgres://", "postgresql://", 1) \
    if _raw_db_url.startswith("postgres://") else _raw_db_url

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "vectors")


def run(engine):
    # 1. Zones non couvertes = territoire Montréal MOINS les buffers 500m
    sql_gaps = """
    SELECT
        a.nom AS arrondissement,
        ST_Difference(
            a.geom,
            COALESCE(
                (SELECT ST_Union(zc.geom)
                 FROM zones_couverture zc
                 WHERE ST_Intersects(zc.geom, a.geom)),
                ST_GeomFromText('GEOMETRYCOLLECTION EMPTY', 4326)
            )
        ) AS geom_gap,
        a.pct_couverture,
        a.nb_bornes
    FROM arrondissements a
    WHERE a.pct_couverture < 100
    ORDER BY a.pct_couverture ASC;
    """

    gdf_gaps = gpd.read_postgis(sql_gaps, engine, geom_col="geom_gap")
    gdf_gaps = gdf_gaps[~gdf_gaps.geometry.is_empty]

    output_path = os.path.join(OUTPUT_DIR, "zones_sous_desservies.geojson")
    gdf_gaps.to_file(output_path, driver="GeoJSON")
    print(f"Zones sous-desservies exportées : {output_path}")
    print(f"Arrondissements avec gaps : {len(gdf_gaps)}")

    # 2. Résumé par arrondissement
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT nom, nb_bornes, pct_couverture
            FROM arrondissements
            ORDER BY pct_couverture ASC
            LIMIT 10
        """))
        print("\nArrondissements les moins couverts :")
        print(f"{'Arrondissement':<35} {'Bornes':>6} {'Couverture':>10}")
        print("-" * 55)
        for r in result:
            print(f"{r[0]:<35} {r[1]:>6} {r[2]:>9.1f}%")


if __name__ == "__main__":
    engine = create_engine(DB_URL)
    run(engine)
