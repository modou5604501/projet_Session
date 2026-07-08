"""
Mise à jour automatique des données depuis Données Québec.
Télécharge les bornes de recharge les plus récentes et met à jour PostGIS.
"""

import os
import sys
import json
import logging
import urllib.request
import tempfile
import geopandas as gpd
from sqlalchemy import create_engine, text
from datetime import datetime

logger = logging.getLogger(__name__)

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://georisk_user:georisk2019@localhost:5433/georisk"
)

# URL CKAN API — Données Québec / Ville de Montréal
CKAN_API = "https://donnees.montreal.ca/api/3/action/package_show?id=bornes-de-recharge-electrique"
FALLBACK_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "vectors",
    "bornes_recharge_montreal.geojson"
)


def get_download_url():
    """Interroge l'API CKAN pour obtenir l'URL de téléchargement du GeoJSON."""
    try:
        with urllib.request.urlopen(CKAN_API, timeout=15) as resp:
            data = json.loads(resp.read())
        for resource in data["result"]["resources"]:
            fmt = resource.get("format", "").upper()
            url = resource.get("url", "")
            if fmt in ("GEOJSON", "JSON") or url.endswith(".geojson"):
                return url
    except Exception as e:
        logger.warning(f"CKAN API inaccessible : {e}")
    return None


def download_bornes(url):
    """Télécharge le GeoJSON depuis l'URL donnée."""
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            content = resp.read()
        tmp = tempfile.NamedTemporaryFile(suffix=".geojson", delete=False)
        tmp.write(content)
        tmp.close()
        return tmp.name
    except Exception as e:
        logger.error(f"Téléchargement échoué ({url}) : {e}")
        return None


def import_bornes_from_file(path, engine):
    """Importe les bornes depuis un fichier GeoJSON dans PostGIS."""
    gdf = gpd.read_file(path)
    gdf = gdf.to_crs(epsg=4326)
    gdf.columns = [c.lower() for c in gdf.columns]

    keep = []
    for c in ["nom", "name", "type", "arrondissement", "nb_prises"]:
        if c in gdf.columns:
            keep.append(c)
    gdf = gdf[keep + ["geometry"]].copy()
    if "name" in gdf.columns and "nom" not in gdf.columns:
        gdf = gdf.rename(columns={"name": "nom"})
    gdf = gdf.rename_geometry("geom")

    with engine.connect() as conn:
        conn.execute(text("TRUNCATE bornes_recharge CASCADE"))
        conn.commit()
    gdf.to_postgis("bornes_recharge", engine, if_exists="append",
                   index=False, chunksize=500)
    return len(gdf)


def create_buffers(engine):
    """Recalcule les buffers 500m et les statistiques."""
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE zones_couverture"))
        conn.execute(text("""
            INSERT INTO zones_couverture (borne_id, rayon_m, geom)
            SELECT id, 500,
                ST_Transform(ST_Buffer(ST_Transform(geom, 32188), 500), 4326)
            FROM bornes_recharge
        """))
        conn.commit()

        conn.execute(text("""
            UPDATE arrondissements a
            SET nb_bornes = (
                SELECT COUNT(*) FROM bornes_recharge b
                WHERE ST_Within(b.geom, a.geom)
            )
        """))
        conn.commit()

        conn.execute(text("""
            UPDATE arrondissements a
            SET pct_couverture = ROUND(
                LEAST(
                    100.0 * ST_Area(
                        ST_Intersection(
                            COALESCE(
                                (SELECT ST_Union(zc.geom) FROM zones_couverture zc
                                 WHERE ST_Intersects(zc.geom, a.geom)),
                                ST_GeomFromText('GEOMETRYCOLLECTION EMPTY', 4326)
                            ),
                            a.geom
                        )::geography
                    ) / NULLIF(ST_Area(a.geom::geography), 0),
                    100
                )::numeric, 1
            )
        """))
        conn.commit()


def run_refresh():
    """Pipeline complet : téléchargement → import → buffers → stats."""
    start = datetime.now()
    logger.info(f"[{start}] Démarrage mise à jour automatique...")

    engine = create_engine(DB_URL)
    tmp_file = None

    try:
        url = get_download_url()
        if url:
            logger.info(f"URL trouvée : {url}")
            tmp_file = download_bornes(url)

        if tmp_file:
            nb = import_bornes_from_file(tmp_file, engine)
            # Sauvegarder la version locale
            import shutil
            shutil.copy(tmp_file, FALLBACK_PATH)
            logger.info(f"{nb} bornes importées depuis Données Québec")
        else:
            logger.warning("Téléchargement impossible — utilisation des données locales")
            nb = import_bornes_from_file(FALLBACK_PATH, engine)
            logger.info(f"{nb} bornes importées depuis fichier local")

        create_buffers(engine)
        elapsed = (datetime.now() - start).seconds
        logger.info(f"Mise à jour terminée en {elapsed}s")
        return {"status": "ok", "bornes": nb, "elapsed_s": elapsed}

    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour : {e}")
        return {"status": "error", "message": str(e)}
    finally:
        if tmp_file and os.path.exists(tmp_file):
            os.unlink(tmp_file)
        engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    result = run_refresh()
    print(result)
