"""
Prétraitement des images Sentinel-1 GRD pour GeoRisk Sentinel
  1. Extraction des archives .SAFE.zip
  2. Lecture des bandes VV/VH (ou HH/HV pour la scène DH)
  3. Conversion en décibels (10 * log10)
  4. Clip sur Sainte-Marthe-sur-le-Lac + reprojection EPSG:32198
  5. Sauvegarde en GeoTIFF 2 bandes (B1=VV, B2=VH)

Utilisation : python src/preprocessing/preprocess_sentinel1.py
"""

import os
import sys
import zipfile
import numpy as np
from pathlib import Path
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.mask import mask
from rasterio.crs import CRS
from shapely.geometry import box, mapping

# Fix PROJ conflit PostgreSQL local
_proj_data = os.path.join(sys.prefix, "Lib", "site-packages", "rasterio", "proj_data")
if os.path.isdir(_proj_data):
    os.environ["PROJ_DATA"] = _proj_data
    os.environ["PROJ_LIB"]  = _proj_data

PROJECT_ROOT = Path(__file__).resolve().parents[2]
S1_RAW_DIR   = PROJECT_ROOT / "data" / "raw" / "sentinel1"
S1_PROC_DIR  = PROJECT_ROOT / "data" / "processed" / "sentinel1"

# Zone d'étude Sainte-Marthe-sur-le-Lac (WGS84)
BBOX_WGS84  = (-74.05, 45.48, -73.85, 45.60)
TARGET_CRS  = CRS.from_epsg(32198)
TARGET_RES  = 10   # résolution Sentinel-1 GRD IW = 10m


def extract_safe(zip_path: Path) -> Path:
    """Extrait le SAFE si pas encore fait, retourne le dossier SAFE."""
    safe_dir = zip_path.parent / zip_path.name.replace(".zip", "")
    if safe_dir.exists():
        print(f"  Deja extrait : {safe_dir.name}")
        return safe_dir

    print(f"  Extraction : {zip_path.name}")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(zip_path.parent)

    # Le SAFE doit correspondre au nom du zip
    if safe_dir.exists():
        return safe_dir

    # Chercher le SAFE extrait si le nom diffère légèrement
    stem = zip_path.stem  # nom sans la dernière extension (.zip)
    candidates = list(zip_path.parent.glob(f"{stem[:30]}*.SAFE"))
    return candidates[0] if candidates else safe_dir


def find_bands(safe_dir: Path) -> dict:
    """Trouve les fichiers GeoTIFF des bandes dans le dossier SAFE."""
    measurement_dir = safe_dir / "measurement"
    bands = {}
    for tif in measurement_dir.glob("*.tiff"):
        name = tif.stem.lower()
        if "-vv-" in name:
            bands["VV"] = tif
        elif "-vh-" in name:
            bands["VH"] = tif
        elif "-hh-" in name:
            bands["HH"] = tif
        elif "-hv-" in name:
            bands["HV"] = tif
    return bands


def to_db(array: np.ndarray) -> np.ndarray:
    """
    Conversion amplitude Sentinel-1 uint16 → sigma0 en dB.
    Formule : 20 * log10(DN / 65535) donne des valeurs physiques
    (~-30 dB pour l'eau, ~-10 dB pour la végétation, ~0 dB pour urban).
    """
    arr = array.astype(np.float32)
    arr[arr <= 0] = np.nan
    return (20.0 * np.log10(arr / 65535.0)).astype(np.float32)


def clip_reproject_band(src_path: Path, geom) -> tuple:
    """
    Lit une bande Sentinel-1 avec GCPs, reprojette en EPSG:32198
    et découpe sur la zone d'étude.
    Les fichiers SAFE n'ont pas de transform affine — seulement des GCPs.
    """
    from rasterio.transform import from_gcps, from_bounds
    from pyproj import Transformer

    with rasterio.open(src_path) as src:
        data = src.read(1).astype(np.float32)
        gcps, gcp_crs = src.gcps

    if not gcps:
        raise RuntimeError(f"Pas de GCPs dans {src_path.name}")

    # Transform affine approx pour la source (depuis les GCPs)
    gcp_transform = from_gcps(gcps)

    # Calculer l'emprise cible en EPSG:32198 depuis notre bbox WGS84
    proj = Transformer.from_crs("EPSG:4326", TARGET_CRS, always_xy=True)
    x_min, y_min = proj.transform(BBOX_WGS84[0], BBOX_WGS84[1])
    x_max, y_max = proj.transform(BBOX_WGS84[2], BBOX_WGS84[3])

    width_dst  = int(round((x_max - x_min) / TARGET_RES))
    height_dst = int(round((y_max - y_min) / TARGET_RES))
    transform_dst = from_bounds(x_min, y_min, x_max, y_max, width_dst, height_dst)

    dst_array = np.full((height_dst, width_dst), np.nan, dtype=np.float32)
    reproject(
        source=data,
        destination=dst_array,
        src_transform=gcp_transform,
        src_crs=gcp_crs,
        dst_transform=transform_dst,
        dst_crs=TARGET_CRS,
        resampling=Resampling.bilinear,
        src_nodata=0,
        dst_nodata=np.nan,
    )
    return dst_array, transform_dst, width_dst, height_dst


def process_scene(zip_path: Path):
    """Traite une scène Sentinel-1 complète."""
    print(f"\nScene : {zip_path.stem[:40]}")
    S1_PROC_DIR.mkdir(parents=True, exist_ok=True)

    # Nom de sortie basé sur la date d'acquisition (token 4 dans le nom SAFE)
    tokens = zip_path.stem.split("_")
    date_str = tokens[4][:8]  # YYYYMMDD
    out_name = f"s1_sainte_marthe_{date_str}_32198.tif"
    out_path = S1_PROC_DIR / out_name

    if out_path.exists():
        print(f"  Deja traite : {out_name}")
        return out_path

    safe_dir = extract_safe(zip_path)
    bands = find_bands(safe_dir)

    if not bands:
        print(f"  ERREUR: aucune bande trouvee dans {safe_dir}")
        return None

    print(f"  Bandes trouvees : {list(bands.keys())}")

    geom = mapping(box(*BBOX_WGS84))

    band_arrays = {}
    transform_dst = width_dst = height_dst = None

    for pol, path in bands.items():
        arr, transform_dst, width_dst, height_dst = clip_reproject_band(path, geom)
        band_arrays[pol] = to_db(arr)

    # Ordre canonique : B1=pol1 (VV ou HH), B2=pol2 (VH ou HV)
    pol_order = ["VV", "VH"] if "VV" in band_arrays else ["HH", "HV"]
    available = [p for p in pol_order if p in band_arrays]

    meta = {
        "driver": "GTiff",
        "dtype":  "float32",
        "crs":    TARGET_CRS,
        "transform": transform_dst,
        "width":  width_dst,
        "height": height_dst,
        "count":  len(available),
        "nodata": np.nan,
        "compress": "lzw",
    }

    with rasterio.open(out_path, "w", **meta) as dst:
        for i, pol in enumerate(available, start=1):
            dst.write(band_arrays[pol], i)
            dst.update_tags(i, polarization=pol)

    size_mb = out_path.stat().st_size / 1024 / 1024
    print(f"  OK: {out_name} ({size_mb:.1f} Mo) | bandes={available}")
    print(f"  Dimensions : {width_dst} x {height_dst} px @ {TARGET_RES}m")
    return out_path


def main():
    print("=== Pretraitement Sentinel-1 -- GeoRisk Sentinel ===\n")

    zips = sorted(S1_RAW_DIR.glob("*.SAFE.zip"))
    if not zips:
        print(f"ERREUR: aucune archive dans {S1_RAW_DIR}")
        return

    print(f"Archives trouvees : {len(zips)}\n")
    outputs = []
    for z in zips:
        out = process_scene(z)
        if out:
            outputs.append(out)

    print(f"\n=== Termine === {len(outputs)} scenes traitees")
    print(f"Fichiers dans data/processed/sentinel1/:")
    for f in S1_PROC_DIR.glob("*.tif"):
        size_mb = f.stat().st_size / 1024 / 1024
        print(f"  {f.name}  {size_mb:.1f} Mo")


if __name__ == "__main__":
    main()
