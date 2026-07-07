"""
Prétraitement du DEM Copernicus GLO-30 pour GeoRisk Sentinel
  1. Clip sur la zone d'étude Sainte-Marthe-sur-le-Lac
  2. Reprojection EPSG:4326 -> EPSG:32198 (NAD83 / Quebec Lambert)
  3. Calcul des dérivés : pente (slope), direction d'écoulement (aspect)

Entrée  : data/raw/dem_sainte_marthe_N45W074.tif
Sorties : data/processed/dem_sainte_marthe_32198.tif
          data/processed/slope_sainte_marthe.tif
          data/processed/aspect_sainte_marthe.tif
"""

import os
import sys

# Forcer PROJ_DATA vers rasterio pour éviter le conflit avec PostgreSQL local
_proj_data = os.path.join(sys.prefix, "Lib", "site-packages", "rasterio", "proj_data")
if os.path.isdir(_proj_data):
    os.environ["PROJ_DATA"] = _proj_data
    os.environ["PROJ_LIB"]  = _proj_data

import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.mask import mask
from rasterio.crs import CRS
from shapely.geometry import box, mapping
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_DEM   = PROJECT_ROOT / "data" / "raw" / "dem_sainte_marthe_N45W074.tif"
PROC_DIR    = PROJECT_ROOT / "data" / "processed"
OUT_DEM     = PROC_DIR / "dem_sainte_marthe_32198.tif"
OUT_SLOPE   = PROC_DIR / "slope_sainte_marthe.tif"
OUT_ASPECT  = PROC_DIR / "aspect_sainte_marthe.tif"

# Zone d'étude Sainte-Marthe-sur-le-Lac (EPSG:4326)
BBOX_WGS84 = (-74.05, 45.48, -73.85, 45.60)
TARGET_CRS = CRS.from_epsg(32198)
TARGET_RES = 30  # résolution cible 30m (identique au DEM source)


def clip_and_reproject():
    """Découpe le DEM sur la zone d'étude et reprojette en EPSG:32198."""
    PROC_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Lecture: {INPUT_DEM.name}")
    with rasterio.open(INPUT_DEM) as src:
        print(f"  CRS source  : {src.crs}")
        print(f"  Resolution  : {src.res}")
        print(f"  Dimensions  : {src.width} x {src.height}")

        # 1. Clip sur la bounding box de Sainte-Marthe
        geom = mapping(box(*BBOX_WGS84))

        clipped, clipped_transform = mask(src, [geom], crop=True)
        clipped_meta = src.meta.copy()
        clipped_meta.update({
            "height": clipped.shape[1],
            "width":  clipped.shape[2],
            "transform": clipped_transform,
        })

        print(f"  Apres clip  : {clipped.shape[2]} x {clipped.shape[1]} pixels")

        # 2. Reprojection EPSG:4326 -> EPSG:32198
        transform_32198, width_32198, height_32198 = calculate_default_transform(
            src.crs, TARGET_CRS,
            clipped.shape[2], clipped.shape[1],
            left=BBOX_WGS84[0], bottom=BBOX_WGS84[1],
            right=BBOX_WGS84[2], top=BBOX_WGS84[3],
            resolution=TARGET_RES,
        )

        out_meta = clipped_meta.copy()
        out_meta.update({
            "crs":       TARGET_CRS,
            "transform": transform_32198,
            "width":     width_32198,
            "height":    height_32198,
            "dtype":     "float32",
        })

        dem_32198 = np.zeros((1, height_32198, width_32198), dtype=np.float32)

        reproject(
            source=clipped,
            destination=dem_32198,
            src_transform=clipped_transform,
            src_crs=src.crs,
            dst_transform=transform_32198,
            dst_crs=TARGET_CRS,
            resampling=Resampling.bilinear,
        )

        with rasterio.open(OUT_DEM, "w", **out_meta) as dst:
            dst.write(dem_32198)

        print(f"  DEM reprojete: {OUT_DEM.name}")
        print(f"  Dimensions   : {width_32198} x {height_32198} pixels @ 30m")
        print(f"  Elev. min/max: {dem_32198[dem_32198 > -9999].min():.1f} / {dem_32198.max():.1f} m")

    return dem_32198[0], transform_32198, out_meta


def compute_slope_aspect(dem_array, transform, meta):
    """Calcule la pente (en degrés) et l'aspect depuis le DEM."""
    res = abs(transform.a)  # résolution en mètres

    # Gradients par différences finies centrées (mode edge pour conserver les bords)
    dy, dx = np.gradient(dem_array, res, res)

    # Pente en degrés
    slope = np.degrees(np.arctan(np.sqrt(dx**2 + dy**2)))

    # Aspect en degrés (0=N, sens horaire)
    aspect = np.degrees(np.arctan2(-dx, dy)) % 360

    raster_meta = meta.copy()
    raster_meta.update({"count": 1, "dtype": "float32"})

    with rasterio.open(OUT_SLOPE, "w", **raster_meta) as dst:
        dst.write(slope.astype(np.float32), 1)
    print(f"  Pente calculee: {OUT_SLOPE.name}")
    print(f"  Pente max     : {slope.max():.1f} deg")

    with rasterio.open(OUT_ASPECT, "w", **raster_meta) as dst:
        dst.write(aspect.astype(np.float32), 1)
    print(f"  Aspect calcule: {OUT_ASPECT.name}")


def main():
    print("=== Pretraitement DEM -- GeoRisk Sentinel ===\n")
    dem_array, transform, meta = clip_and_reproject()

    print("\nCalcul pente et aspect...")
    compute_slope_aspect(dem_array, transform, meta)

    print("\n=== Termine ===")
    print("Fichiers dans data/processed/:")
    for f in PROC_DIR.glob("*.tif"):
        size_mb = f.stat().st_size / 1024 / 1024
        print(f"  {f.name:45s} {size_mb:6.1f} Mo")


if __name__ == "__main__":
    main()
