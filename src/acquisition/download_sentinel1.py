"""
Téléchargement des images Sentinel-1 SAR pour Sainte-Marthe-sur-le-Lac
Période : avril 2019 (avant et après la rupture de digue du 27 avril 2019)
Source : Copernicus Data Space Ecosystem (CDSE)
"""

import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# Chargement des credentials depuis .env
load_dotenv(Path(__file__).resolve().parents[2] / ".env")
USERNAME = os.getenv("CDSE_USERNAME")
PASSWORD = os.getenv("CDSE_PASSWORD")

# Zone d'étude : Sainte-Marthe-sur-le-Lac
BBOX = (-74.10, 45.45, -73.80, 45.65)  # (lon_min, lat_min, lon_max, lat_max)

# Périodes : avant et après la rupture de digue (27 avril 2019)
PERIODS = [
    ("2019-04-01", "2019-04-26"),   # Avant l'inondation
    ("2019-04-28", "2019-05-15"),   # Après l'inondation
]

OUTPUT_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "sentinel1"
TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
SEARCH_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"


def get_token():
    """Obtenir le token d'accès CDSE."""
    response = requests.post(TOKEN_URL, data={
        "grant_type": "password",
        "username": USERNAME,
        "password": PASSWORD,
        "client_id": "cdse-public",
    })
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✅ Authentification réussie")
        return token
    else:
        print(f"❌ Erreur d'authentification : {response.status_code}")
        print(response.text)
        return None


def search_products(token, date_start, date_end):
    """Chercher les images Sentinel-1 GRD pour notre zone et période."""
    lon_min, lat_min, lon_max, lat_max = BBOX
    footprint = f"POLYGON(({lon_min} {lat_min},{lon_max} {lat_min},{lon_max} {lat_max},{lon_min} {lat_max},{lon_min} {lat_min}))"

    params = {
        "$filter": (
            f"Collection/Name eq 'SENTINEL-1' "
            f"and Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'productType' and att/OData.CSC.StringAttribute/Value eq 'GRD') "
            f"and ContentDate/Start gt {date_start}T00:00:00.000Z "
            f"and ContentDate/Start lt {date_end}T23:59:59.000Z "
            f"and OData.CSC.Intersects(area=geography'SRID=4326;{footprint}')"
        ),
        "$orderby": "ContentDate/Start asc",
        "$top": 5,
    }

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(SEARCH_URL, params=params, headers=headers)

    if response.status_code == 200:
        products = response.json().get("value", [])
        print(f"  {len(products)} image(s) trouvée(s) pour {date_start} → {date_end}")
        return products
    else:
        print(f"  ❌ Erreur de recherche : {response.status_code}")
        return []


def download_product(token, product, output_dir):
    """Télécharger un produit Sentinel-1."""
    product_id = product["Id"]
    product_name = product["Name"]
    output_file = output_dir / f"{product_name}.zip"

    if output_file.exists():
        print(f"  Déjà téléchargé : {product_name}")
        return

    url = f"https://zipper.dataspace.copernicus.eu/odata/v1/Products({product_id})/$value"
    headers = {"Authorization": f"Bearer {token}"}

    print(f"  Téléchargement : {product_name}")
    response = requests.get(url, headers=headers, stream=True, timeout=300)

    if response.status_code == 200:
        total = int(response.headers.get("content-length", 0))
        downloaded = 0

        with open(output_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=65536):
                f.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    pct = downloaded / total * 100
                    print(f"\r  Progression : {pct:.1f}%", end="", flush=True)

        size_mb = output_file.stat().st_size / 1024 / 1024
        print(f"\n  ✅ Téléchargé : {output_file.name} ({size_mb:.0f} Mo)")
    else:
        print(f"\n  ❌ Erreur de téléchargement : {response.status_code}")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=== Téléchargement Sentinel-1 — Sainte-Marthe-sur-le-Lac ===\n")

    if not USERNAME or not PASSWORD:
        print("❌ Fichier .env introuvable ou incomplet !")
        return

    token = get_token()
    if not token:
        return

    total_downloaded = 0
    for date_start, date_end in PERIODS:
        print(f"\nPériode : {date_start} → {date_end}")
        products = search_products(token, date_start, date_end)
        for product in products[:2]:  # Max 2 images par période
            download_product(token, product, OUTPUT_DIR)
            total_downloaded += 1

    print(f"\n=== Terminé — {total_downloaded} image(s) téléchargée(s) ===")
    print(f"Dossier : {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
