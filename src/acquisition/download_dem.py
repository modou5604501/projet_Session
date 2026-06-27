"""
Téléchargement du DEM (Modèle Numérique d'Élévation) pour Sainte-Marthe-sur-le-Lac
Source : Copernicus DEM GLO-30 (30m) — AWS Open Data (accès public, sans authentification)
"""

import os
import requests
from pathlib import Path

# === CONFIGURATION ===
OUTPUT_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
OUTPUT_FILE = OUTPUT_DIR / "dem_sainte_marthe_N45W074.tif"

# Tuile Copernicus DEM couvrant Sainte-Marthe-sur-le-Lac (45.5°N, 73.9°W)
DEM_URL = (
    "https://copernicus-dem-30m.s3.amazonaws.com/"
    "Copernicus_DSM_COG_10_N45_00_W074_00_DEM/"
    "Copernicus_DSM_COG_10_N45_00_W074_00_DEM.tif"
)


def download_dem():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if OUTPUT_FILE.exists():
        print(f"DEM déjà téléchargé : {OUTPUT_FILE}")
        return

    print("Téléchargement du DEM Copernicus (30m) pour Sainte-Marthe-sur-le-Lac...")
    print(f"URL : {DEM_URL}")

    response = requests.get(DEM_URL, stream=True, timeout=120)

    if response.status_code == 200:
        total = int(response.headers.get("content-length", 0))
        downloaded = 0

        with open(OUTPUT_FILE, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    pct = downloaded / total * 100
                    print(f"\rProgression : {pct:.1f}%", end="", flush=True)

        print(f"\n✅ DEM téléchargé : {OUTPUT_FILE}")
        print(f"   Taille : {OUTPUT_FILE.stat().st_size / 1024 / 1024:.1f} Mo")

    else:
        print(f"❌ Erreur HTTP {response.status_code}")
        print("Vérifiez votre connexion internet.")


if __name__ == "__main__":
    download_dem()
