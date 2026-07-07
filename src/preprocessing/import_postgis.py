"""
Importation des données vectorielles dans PostGIS — GeoRisk Sentinel
  - Réseau électrique OSM (GeoJSON EPSG:4326) → electric_network (EPSG:32198)
  - Zones inondées MRNF 2017/2019 (GPKG) → flood_zones (EPSG:32198)

Connexion : localhost:5433 (port hôte Docker)
"""

import os
import sys

_proj_data = os.path.join(sys.prefix, "Lib", "site-packages", "rasterio", "proj_data")
if os.path.isdir(_proj_data):
    os.environ["PROJ_DATA"] = _proj_data
    os.environ["PROJ_LIB"]  = _proj_data

import geopandas as gpd
from sqlalchemy import create_engine, text
from pathlib import Path

# === CONFIGURATION ===
PROJECT_ROOT = Path(__file__).resolve().parents[2]

OSM_GEOJSON   = PROJECT_ROOT / "data" / "vectors" / "electric_network_sainte_marthe.geojson"
MRNF_GPKG     = PROJECT_ROOT / "data" / "vectors" / "territoire_inonde_2017_2019.gpkg"

# Zone d'étude Sainte-Marthe-sur-le-Lac (EPSG:4326)
BBOX_WGS84 = (-74.05, 45.48, -73.85, 45.60)

CRS_TARGET = "EPSG:32198"   # NAD83 / Québec Lambert

# Connexion PostGIS (port 5433 = port hôte Docker → 5432 interne)
DB_URL = "postgresql://georisk_user:georisk2019@localhost:5433/georisk"


def get_engine():
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        conn.execute(text("SELECT PostGIS_Version()"))
    print("Connexion PostGIS OK")
    return engine


def import_electric_network(engine):
    print("\n--- Réseau électrique OSM ---")
    gdf = gpd.read_file(OSM_GEOJSON)
    print(f"  Lignes chargées : {len(gdf)}  CRS source : {gdf.crs}")

    # Reprojection
    gdf = gdf.to_crs(CRS_TARGET)

    # Sélection et renommage des colonnes utiles
    cols_keep = ["geometry"]
    rename_map = {}

    for col in ["osm_id", "power", "voltage"]:
        if col in gdf.columns:
            cols_keep.append(col)

    gdf = gdf[cols_keep].copy()

    if "power" in gdf.columns:
        gdf = gdf.rename(columns={"power": "type"})

    if "voltage" in gdf.columns:
        gdf["voltage"] = gpd.pd.to_numeric(gdf["voltage"], errors="coerce").astype("Int64")

    if "osm_id" not in gdf.columns:
        gdf["osm_id"] = None

    if "type" not in gdf.columns:
        gdf["type"] = "unknown"

    if "voltage" not in gdf.columns:
        gdf["voltage"] = None

    gdf["criticality"] = "medium"

    # Suppression des géométries nulles
    gdf = gdf[gdf.geometry.notna()].reset_index(drop=True)
    print(f"  Géométries valides : {len(gdf)}")

    # Renommer la colonne géométrie pour correspondre au schéma SQL (geom)
    gdf = gdf.rename_geometry("geom")

    # Vider la table existante (TRUNCATE respecte les FK, pas DROP)
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE electric_network CASCADE"))

    # Écriture dans PostGIS (append sur table vide)
    gdf.to_postgis(
        name="electric_network",
        con=engine,
        if_exists="append",
        index=False,
    )
    print(f"  OK: {len(gdf)} entites importees -> electric_network")


def import_flood_zones(engine):
    print("\n--- Zones inondées MRNF 2017/2019 ---")

    # Lister les couches disponibles dans le GPKG
    import fiona
    layers = fiona.listlayers(str(MRNF_GPKG))
    print(f"  Couches disponibles : {layers}")

    # Charger la première couche (ou la bonne si plusieurs)
    target_layer = layers[0]
    for lyr in layers:
        if "2019" in lyr or "inond" in lyr.lower() or "territoire" in lyr.lower():
            target_layer = lyr
            break

    print(f"  Couche sélectionnée : {target_layer}")
    gdf = gpd.read_file(MRNF_GPKG, layer=target_layer)
    print(f"  Lignes chargées : {len(gdf)}  CRS source : {gdf.crs}")

    # Clip sur la zone d'étude (en WGS84 d'abord)
    if gdf.crs and gdf.crs.to_epsg() != 4326:
        gdf_wgs = gdf.to_crs("EPSG:4326")
    else:
        gdf_wgs = gdf

    lon_min, lat_min, lon_max, lat_max = BBOX_WGS84
    gdf_clip = gdf_wgs.cx[lon_min:lon_max, lat_min:lat_max].copy()
    print(f"  Après clip sur Sainte-Marthe : {len(gdf_clip)} entités")

    if len(gdf_clip) == 0:
        print("  ATTENTION: Aucune entite dans la zone -- import du jeu complet")
        gdf_clip = gdf_wgs.copy()

    # Reprojection vers EPSG:32198
    gdf_clip = gdf_clip.to_crs(CRS_TARGET)

    # Forcer la géométrie en 2D (le GPKG MRNF contient des MultiPolygon Z)
    import shapely
    gdf_clip["geometry"] = gdf_clip["geometry"].apply(
        lambda g: shapely.force_2d(g) if g is not None else None
    )

    # Colonnes PostGIS
    gdf_out = gpd.GeoDataFrame(geometry=gdf_clip.geometry, crs=CRS_TARGET)
    gdf_out["source"] = "MRNF"
    gdf_out["date_detection"] = None
    gdf_out["recurrence"] = None
    gdf_out["surface_ha"] = gdf_out.geometry.area / 10_000  # m² → ha

    # Détection date depuis colonnes source
    for col in gdf_clip.columns:
        if "date" in col.lower() or "annee" in col.lower() or "year" in col.lower():
            gdf_out["date_detection"] = gpd.pd.to_datetime(gdf_clip[col], errors="coerce")
            break

    # Suppression des géométries nulles
    gdf_out = gdf_out[gdf_out.geometry.notna()].reset_index(drop=True)

    # Renommer la colonne géométrie pour correspondre au schéma SQL (geom)
    gdf_out = gdf_out.rename_geometry("geom")

    # Vider et réimporter
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE flood_zones CASCADE"))

    gdf_out.to_postgis(
        name="flood_zones",
        con=engine,
        if_exists="append",
        index=False,
    )
    print(f"  OK: {len(gdf_out)} entites importees -> flood_zones")


def verify_import(engine):
    print("\n--- Vérification dans PostGIS ---")
    with engine.connect() as conn:
        for table in ("electric_network", "flood_zones"):
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"  {table:25s} : {count} enregistrements")


def main():
    print("=== Import PostGIS — GeoRisk Sentinel ===")
    engine = get_engine()
    import_electric_network(engine)
    import_flood_zones(engine)
    verify_import(engine)
    print("\n=== Terminé ===")
    print("Accès pgAdmin : http://localhost:5050")
    print("  Email    : modou.khabane.mbaye@usherbrooke.ca")
    print("  Password : georisk2019")
    print("  Serveur  : georisk_postgis / port 5432 / db georisk")


if __name__ == "__main__":
    main()
