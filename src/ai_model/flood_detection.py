"""
Détection de zones inondées — GeoRisk Sentinel
Méthode principale : Détection de changement SAR (avant vs après inondation)
  - Ratio VH(après)/VH(avant) en dB → baisse significative = inondation
  - Approche calibration-indépendante (annule les offsets absolus)
Méthode alternative : U-Net (structure prête, poids Sen1Floods11 en option)

Entrées  : data/processed/sentinel1/s1_sainte_marthe_<date>_32198.tif
Sorties  : data/processed/flood_masks/flood_<date>.tif
           data/processed/flood_masks/flood_change.tif (carte de changement)

Usage    : python src/ai_model/flood_detection.py
"""

import os
import sys
import numpy as np
from pathlib import Path
import rasterio

# Fix PROJ conflit PostgreSQL local
_proj_data = os.path.join(sys.prefix, "Lib", "site-packages", "rasterio", "proj_data")
if os.path.isdir(_proj_data):
    os.environ["PROJ_DATA"] = _proj_data
    os.environ["PROJ_LIB"]  = _proj_data

PROJECT_ROOT = Path(__file__).resolve().parents[2]
S1_PROC_DIR  = PROJECT_ROOT / "data" / "processed" / "sentinel1"
MASK_DIR     = PROJECT_ROOT / "data" / "processed" / "flood_masks"

# Seuil de changement (dB) : une baisse de plus de CHANGE_THRESHOLD dB
# entre avant et après = zone nouvellement inondée.
# L'eau libre crée une baisse de 5-15 dB en SAR.
CHANGE_THRESHOLD_DB = 4.0


def read_vh_band(scene_path: Path) -> tuple:
    """
    Lit la bande VH/HV (bande 2 si disponible).
    Les fichiers sont déjà en dB (20*log10) — valeurs toutes négatives.
    Les pixels nodata (hors scène) sont en NaN.
    """
    with rasterio.open(scene_path) as src:
        count = src.count
        bi = 2 if count >= 2 else 1
        data = src.read(bi).astype(np.float64)
        nodata = src.nodata
        meta = src.meta.copy()

    # Marquer le nodata comme NaN (peut être np.nan ou 0 selon l'écriture)
    if nodata is not None and not np.isnan(nodata):
        data[data == nodata] = np.nan

    # Masquer aussi les 0 résiduels (hors zone après reprojection)
    data[data == 0.0] = np.nan

    return data, meta


def detect_change(before_db: np.ndarray, after_db: np.ndarray,
                  threshold_db: float = CHANGE_THRESHOLD_DB) -> np.ndarray:
    """
    Détecte les zones nouvellement inondées par changement de rétrodiffusion.
    Retourne un masque uint8 : 0=sec, 1=inondé, 255=nodata.
    """
    diff = after_db - before_db   # négatif = baisse de backscatter = inondation
    mask = np.full(diff.shape, 255, dtype=np.uint8)
    valid = np.isfinite(diff)
    mask[valid & (diff < -threshold_db)] = 1   # pixels inondés
    mask[valid & (diff >= -threshold_db)] = 0  # pixels secs
    return mask


def detect_water_percentile(band_db: np.ndarray, percentile: float = 12.0) -> np.ndarray:
    """
    Détecte l'eau par seuil au percentile bas (méthode mono-image).
    Les pixels les plus sombres sont l'eau.
    Retourne un masque uint8 : 0=sec, 1=eau, 255=nodata.
    """
    valid = band_db[np.isfinite(band_db)]
    threshold = np.percentile(valid, percentile)
    mask = np.full(band_db.shape, 255, dtype=np.uint8)
    finite = np.isfinite(band_db)
    mask[finite & (band_db < threshold)] = 1
    mask[finite & (band_db >= threshold)] = 0
    return mask


def save_mask(mask: np.ndarray, meta: dict, out_path: Path):
    out_meta = meta.copy()
    out_meta.update({
        "count":    1,
        "dtype":    "uint8",
        "nodata":   255,
        "compress": "lzw",
    })
    with rasterio.open(out_path, "w", **out_meta) as dst:
        dst.write(mask, 1)


def main():
    print("=== Detection de zones inondees -- GeoRisk Sentinel ===\n")
    MASK_DIR.mkdir(parents=True, exist_ok=True)

    scenes = sorted(S1_PROC_DIR.glob("*.tif"))
    if not scenes:
        print(f"ERREUR: aucune scene dans {S1_PROC_DIR}")
        return

    # Séparer avant et après l'inondation du 27 avril 2019
    before_scenes = [s for s in scenes if s.stem.split("_")[3] < "20190427"]
    after_scenes  = [s for s in scenes if s.stem.split("_")[3] >= "20190427"]

    print(f"Scenes avant inondation : {[s.stem.split('_')[3] for s in before_scenes]}")
    print(f"Scenes apres inondation  : {[s.stem.split('_')[3] for s in after_scenes]}")

    # ── Masques eau par méthode mono-image (toutes les scènes) ──
    print("\n--- Masques eau (methode percentile) ---")
    for scene in scenes:
        date = scene.stem.split("_")[3]
        out_path = MASK_DIR / f"flood_{date}.tif"
        band_db, meta = read_vh_band(scene)
        mask = detect_water_percentile(band_db)
        save_mask(mask, meta, out_path)
        n_water = int((mask == 1).sum())
        area_ha = n_water * 10 * 10 / 10_000
        pct = n_water / np.isfinite(band_db).sum() * 100
        print(f"  {date}: {n_water} px eau  ({area_ha:.0f} ha, {pct:.1f}% de la scene)")

    # ── Carte de changement (détection principale) ──
    print("\n--- Carte de changement avant/apres ---")
    if before_scenes and after_scenes:
        # Utiliser la scène juste avant et juste après
        scene_b = before_scenes[-1]
        scene_a = after_scenes[0]
        date_b  = scene_b.stem.split("_")[3]
        date_a  = scene_a.stem.split("_")[3]

        print(f"  Avant : {date_b}  |  Apres : {date_a}")
        before_db, meta = read_vh_band(scene_b)
        after_db,  _    = read_vh_band(scene_a)

        change = detect_change(before_db, after_db, CHANGE_THRESHOLD_DB)
        change_path = MASK_DIR / "flood_change.tif"
        save_mask(change, meta, change_path)

        n_new  = int((change == 1).sum())
        area_ha = n_new * 10 * 10 / 10_000
        print(f"  Nouveaux pixels inondes : {n_new}  ({area_ha:.0f} ha)")
        print(f"  Sauvegarde : {change_path.name}")

        # Statistiques de changement
        diff = after_db - before_db
        valid_diff = diff[np.isfinite(diff)]
        print(f"  Changement dB - mean: {valid_diff.mean():.2f}  std: {valid_diff.std():.2f}")
        print(f"  Seuil utilise : <-{CHANGE_THRESHOLD_DB} dB")
    else:
        print("  ATTENTION: scenes avant OU apres manquantes — carte de changement ignoree")

    print("\n=== Termine ===")
    print("Fichiers dans data/processed/flood_masks/:")
    for f in sorted(MASK_DIR.glob("*.tif")):
        size_kb = f.stat().st_size / 1024
        print(f"  {f.name:35s} {size_kb:5.0f} Ko")

    weights_path = PROJECT_ROOT / "models" / "sen1floods11_unet.pt"
    if not weights_path.exists():
        print("\nNOTE U-Net: telecharger les poids pour activer l'inference deep learning")
        print("  https://github.com/cloudtostreet/Sen1Floods11")
        print(f"  Destination: {weights_path}")


if __name__ == "__main__":
    main()
