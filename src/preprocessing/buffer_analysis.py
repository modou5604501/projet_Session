"""
Analyse de couverture — buffer 500m autour des bornes de recharge.
Génère les zones de couverture dans PostGIS et calcule les statistiques
par arrondissement.
"""

import os
from sqlalchemy import create_engine, text

_raw_db_url = os.getenv(
    "DATABASE_URL",
    "postgresql://georisk_user:georisk2019@localhost:5433/georisk"
)
DB_URL = _raw_db_url.replace("postgres://", "postgresql://", 1) \
    if _raw_db_url.startswith("postgres://") else _raw_db_url


def run(engine):
    sql_statements = [
        # 1. Vider les zones de couverture existantes
        "TRUNCATE zones_couverture;",

        # 2. Générer les buffers 500m (en MTM8 pour précision métrique, retour WGS84)
        """
        INSERT INTO zones_couverture (borne_id, rayon_m, geom)
        SELECT
            id,
            500,
            ST_Transform(
                ST_Buffer(ST_Transform(geom, 32188), 500),
                4326
            )
        FROM bornes_recharge;
        """,

        # 3. Compter les bornes par arrondissement
        """
        UPDATE arrondissements a
        SET nb_bornes = (
            SELECT COUNT(*)
            FROM bornes_recharge b
            WHERE ST_Within(b.geom, a.geom)
        );
        """,

        # 4. Calculer le pourcentage de couverture par arrondissement
        """
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
        );
        """,
    ]

    with engine.connect() as conn:
        for stmt in sql_statements:
            stmt = stmt.strip()
            if stmt:
                try:
                    conn.execute(text(stmt))
                    conn.commit()
                except Exception as e:
                    print(f"Erreur SQL : {e}")
                    conn.rollback()

    print("Analyse de couverture terminée.")
    print_stats(engine)


def print_stats(engine):
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT
                (SELECT COUNT(*) FROM bornes_recharge) AS total_bornes,
                (SELECT COUNT(*) FROM arrondissements WHERE pct_couverture < 30) AS sous_desservis,
                (SELECT ROUND(AVG(pct_couverture)::numeric, 1) FROM arrondissements) AS couverture_moyenne
        """))
        row = result.fetchone()
        print(f"Total bornes       : {row[0]}")
        print(f"Arrond. <30%       : {row[1]}")
        print(f"Couverture moyenne : {row[2]}%")

        top = conn.execute(text("""
            SELECT nom, nb_bornes, pct_couverture
            FROM arrondissements
            ORDER BY pct_couverture ASC
            LIMIT 5
        """))
        print("\nTop 5 arrondissements sous-desservis :")
        for r in top:
            print(f"  {r[0]:<35} {r[1]} bornes  {r[2]}%")


if __name__ == "__main__":
    engine = create_engine(DB_URL)
    run(engine)
