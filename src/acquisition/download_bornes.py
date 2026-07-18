"""
Téléchargement des bornes de recharge électrique publiques — Montréal
Source : Ville de Montréal via l'API CKAN de Données Québec
Licence : CC-BY 4.0

Ce script est autonome. Il télécharge le fichier GeoJSON le plus récent
et le sauvegarde dans data/vectors/bornes_recharge_montreal.geojson,
utilisé directement par shiny_app/app.py.
"""

import os
import requests
from pathlib import Path

CKAN_API   = "https://donnees.montreal.ca/api/3/action/package_show"
DATASET_ID = "bornes-de-recharge-electrique"
OUTPUT     = Path(__file__).resolve().parents[2] / "data/vectors/bornes_recharge_montreal.geojson"


def get_download_url() -> str | None:
    resp = requests.get(CKAN_API, params={"id": DATASET_ID}, timeout=30)
    resp.raise_for_status()
    pkg = resp.json()
    for resource in pkg["result"]["resources"]:
        if resource.get("format", "").upper() in ("GEOJSON", "JSON"):
            return resource["url"]
    return None


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"Téléchargement : {url}")
    r = requests.get(url, timeout=120, stream=True)
    r.raise_for_status()
    with open(dest, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
    size_mb = dest.stat().st_size / 1_048_576
    print(f"Sauvegardé : {dest}  ({size_mb:.1f} Mo)")


if __name__ == "__main__":
    url = get_download_url()
    if url:
        download(url, OUTPUT)
    else:
        print("URL non trouvée dans le catalogue CKAN.")
