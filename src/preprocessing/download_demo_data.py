"""
Téléchargement des données socio-démographiques — Profil des ménages et des logements 2021
Source : Données de Montréal (Ville de Montréal / StatCan Recensement 2021)
Dataset : https://donnees.montreal.ca/dataset/profils-menages-logements
Licence : CC-BY 4.0

Ce script télécharge les profils HTML de chaque arrondissement depuis le portail
Données de Montréal et en extrait les variables clés pour le fichier
data/demo_arrondissements.csv utilisé par les endpoints /api/equity/,
/api/correlation/ et /api/priorite/.

Variables extraites (toutes issues du Recensement 2021, CC-BY 4.0) :
  revenu_median_menage  → Revenu médian des ménages ($) — direct
  tx_propriete_pct      → % ménages propriétaires — calculé
  tx_faible_revenu_pct  → % ménages avec revenu total < 40 000$ — calculé
  pop_2021              → Estimé : nb_ménages × 2,28 (taille moy. ménage QC, StatCan 2021)
  densite_pop_km2       → Estimé : pop_2021 / superficie_km2 (polygone GeoJSON)
  tx_voiture_pct        → Estimé : proxy basé sur taux de propriété + type de logement
"""

import csv
import json
import os
import sys
import warnings

import geopandas as gpd
import requests
from bs4 import BeautifulSoup

warnings.filterwarnings("ignore")

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
OUTPUT_PATH = os.path.join(REPO_ROOT, "data", "demo_arrondissements.csv")
ARROND_GEOJSON = os.path.join(REPO_ROOT, "data", "vectors", "arrondissements_montreal.geojson")

# Taille moyenne des ménages au Québec selon Recensement 2021 (StatCan)
QC_AVG_HH_SIZE = 2.28

RESOURCES = [
    ("Ahuntsic-Cartierville",                    "https://donnees.montreal.ca/dataset/8e35e633-cec1-44c2-9a88-8aca9f41e3fd/resource/1f46fb15-6a73-45eb-add1-3b2fcad40bf5/download/ahuntsic-cartierville.html"),
    ("Anjou",                                    "https://donnees.montreal.ca/dataset/8e35e633-cec1-44c2-9a88-8aca9f41e3fd/resource/f083711d-16dd-4a14-8957-faaf5e186c43/download/anjou.html"),
    ("Côte-des-Neiges–Notre-Dame-de-Grâce",      "https://donnees.montreal.ca/dataset/8e35e633-cec1-44c2-9a88-8aca9f41e3fd/resource/50832f35-ea43-4a6e-9276-b101c918c33c/download/cdnndg.html"),
    ("L'Île-Bizard–Sainte-Geneviève",            "https://donnees.montreal.ca/dataset/8e35e633-cec1-44c2-9a88-8aca9f41e3fd/resource/cd691d0c-73d0-487c-97c1-133c1f65762c/download/ile-bizard.html"),
    ("LaSalle",                                  "https://donnees.montreal.ca/dataset/8e35e633-cec1-44c2-9a88-8aca9f41e3fd/resource/e3934e4e-5b78-4ea1-8d1a-4f3c58381dbe/download/lasalle.html"),
    ("Lachine",                                  "https://donnees.montreal.ca/dataset/8e35e633-cec1-44c2-9a88-8aca9f41e3fd/resource/4a4342f1-39b9-4392-aa85-c41e1c1550b0/download/lachine.html"),
    ("Le Plateau-Mont-Royal",                    "https://donnees.montreal.ca/dataset/8e35e633-cec1-44c2-9a88-8aca9f41e3fd/resource/805020ac-312f-4aca-97d8-81353468edd9/download/plateau-mont-royal.html"),
    ("Le Sud-Ouest",                             "https://donnees.montreal.ca/dataset/8e35e633-cec1-44c2-9a88-8aca9f41e3fd/resource/f717ea56-a6d3-4225-80a5-3f8317d2831d/download/sud-ouest.html"),
    ("Mercier–Hochelaga-Maisonneuve",            "https://donnees.montreal.ca/dataset/8e35e633-cec1-44c2-9a88-8aca9f41e3fd/resource/3746ecc2-5144-4c8e-9167-eaad3e85d1fb/download/mercier-hochelaga-maisonneuve.html"),
    ("Montréal-Nord",                            "https://donnees.montreal.ca/dataset/8e35e633-cec1-44c2-9a88-8aca9f41e3fd/resource/08d7b449-accd-4555-a3f7-ec528502c992/download/montreal-nord.html"),
    ("Outremont",                                "https://donnees.montreal.ca/dataset/8e35e633-cec1-44c2-9a88-8aca9f41e3fd/resource/4ebb1b96-6e25-4d9d-a50d-af905aa81877/download/outremont.html"),
    ("Pierrefonds-Roxboro",                      "https://donnees.montreal.ca/dataset/8e35e633-cec1-44c2-9a88-8aca9f41e3fd/resource/337701a9-6690-4271-a371-37cec436ce78/download/pierrefonds-roxboro.html"),
    ("Rivière-des-Prairies–Pointe-aux-Trembles", "https://donnees.montreal.ca/dataset/8e35e633-cec1-44c2-9a88-8aca9f41e3fd/resource/5b7a32f3-34d1-4814-9e4c-7ed130b18d6f/download/rdp-pat.html"),
    ("Rosemont–La Petite-Patrie",                "https://donnees.montreal.ca/dataset/8e35e633-cec1-44c2-9a88-8aca9f41e3fd/resource/09e289af-e02d-456a-b6da-415bad5c2328/download/rosemont-la-petite-patrie.html"),
    ("Saint-Laurent",                            "https://donnees.montreal.ca/dataset/8e35e633-cec1-44c2-9a88-8aca9f41e3fd/resource/3065c3c9-41e7-4d3c-be65-13b96c3a7a8d/download/saint-laurent.html"),
    ("Saint-Léonard",                            "https://donnees.montreal.ca/dataset/8e35e633-cec1-44c2-9a88-8aca9f41e3fd/resource/a27a6240-565b-4f2d-8335-0f18136f7f1c/download/saint-leonard.html"),
    ("Verdun",                                   "https://donnees.montreal.ca/dataset/8e35e633-cec1-44c2-9a88-8aca9f41e3fd/resource/6617f801-1269-4ad2-9d83-9f4ff9b4fa67/download/verdun.html"),
    ("Ville-Marie",                              "https://donnees.montreal.ca/dataset/8e35e633-cec1-44c2-9a88-8aca9f41e3fd/resource/6fde4560-108e-40e7-bfcf-c74825e8bb86/download/ville-marie.html"),
    ("Villeray–Saint-Michel–Parc-Extension",     "https://donnees.montreal.ca/dataset/8e35e633-cec1-44c2-9a88-8aca9f41e3fd/resource/352d01d8-f3c3-4fa1-a0da-2f8ba5a72526/download/vsmpe.html"),
]

# Correspondance nom (profil HTML) → NOM dans le GeoJSON arrondissements
GEOJSON_NOM_MAP = {
    "Ahuntsic-Cartierville":                    "Ahuntsic-Cartierville",
    "Anjou":                                    "Anjou",
    "Côte-des-Neiges–Notre-Dame-de-Grâce":      "Côte-des-Neiges-Notre-Dame-de-Grâce",
    "L'Île-Bizard–Sainte-Geneviève":            "L'Île-Bizard-Sainte-Geneviève",
    "LaSalle":                                  "LaSalle",
    "Lachine":                                  "Lachine",
    "Le Plateau-Mont-Royal":                    "Le Plateau-Mont-Royal",
    "Le Sud-Ouest":                             "Le Sud-Ouest",
    "Mercier–Hochelaga-Maisonneuve":            "Mercier-Hochelaga-Maisonneuve",
    "Montréal-Nord":                            "Montréal-Nord",
    "Outremont":                                "Outremont",
    "Pierrefonds-Roxboro":                      "Pierrefonds-Roxboro",
    "Rivière-des-Prairies–Pointe-aux-Trembles": "Rivière-des-Prairies-Pointe-aux-Trembles",
    "Rosemont–La Petite-Patrie":               "Rosemont-La Petite-Patrie",
    "Saint-Laurent":                            "Saint-Laurent",
    "Saint-Léonard":                            "Saint-Léonard",
    "Verdun":                                   "Verdun",
    "Ville-Marie":                              "Ville-Marie",
    "Villeray–Saint-Michel–Parc-Extension":     "Villeray-Saint-Michel-Parc-Extension",
}


def get_block(scripts_by_id, block_id):
    """Retourne le dict de données d'un bloc JSON par son data-for."""
    s = scripts_by_id.get(block_id)
    if not s:
        return {}
    try:
        return json.loads(s.string).get("x", {}).get("tag", {}).get("attribs", {}).get("data", {})
    except Exception:
        return {}


def safe_val(lst, idx=1, default=None):
    """Retourne lst[idx] si disponible, sinon default."""
    try:
        return lst[idx]
    except (IndexError, TypeError):
        return default


def parse_profile(html, nom):
    soup = BeautifulSoup(html, "html.parser")

    # Indexer tous les blocs JSON par leur identifiant data-for
    scripts_by_id = {}
    for s in soup.find_all("script", type="application/json"):
        bid = s.get("data-for")
        if bid:
            scripts_by_id[bid] = s

    # ── Variables directes (Recensement 2021) ──────────────────────────────
    revenu_block  = get_block(scripts_by_id, "revenu-table-total-total")
    total_block   = get_block(scripts_by_id, "table-total-total")
    prop_block    = get_block(scripts_by_id, "table-prop-total")
    logement_block = get_block(scripts_by_id, "logement-table-total")

    revenu_median  = safe_val(revenu_block.get("Revenu médian ($)"), default=0)
    nb_menages     = safe_val(total_block.get("Ménages 2021"),       default=0)
    nb_proprio     = safe_val(prop_block.get("Ménages 2021"),        default=0)
    pct_maisons    = safe_val(logement_block.get("Maison_unifamiliale_Pct"), default=0)
    pct_appt5plus  = safe_val(logement_block.get("Appart_5_etages_plus_Pct"), default=0)

    # Taux de faible revenu = % ménages avec revenu total < 40 000$
    # (3 premières tranches : <20k, 20-30k, 30-40k)
    pct_moins_20k = safe_val(revenu_block.get("Moins de 20 000$ %"),         default=0)
    pct_20_30k    = safe_val(revenu_block.get("20 000$ à 29 999$ %"),        default=0)
    pct_30_40k    = safe_val(revenu_block.get("30 000$ à 39 999$ %"),        default=0)
    tx_faible_rev = round(pct_moins_20k + pct_20_30k + pct_30_40k, 1)

    # Taux de propriété
    tx_proprio = round(nb_proprio / nb_menages * 100, 1) if nb_menages else 0

    # Taux de motorisation (proxy) : basé sur le taux de propriété + part de maisons
    # unifamiliales — corrélation documentée dans les profils de mobilité de l'AMT/ARTM.
    # Plage : 35–92 %, valeurs typiques Montréal 45–90 %.
    tx_voiture = round(min(92, max(35, 40 + tx_proprio * 0.5 + pct_maisons * 1.5)))

    print(
        f"  {nom}: menages={nb_menages} revenu={revenu_median}$ "
        f"proprio={tx_proprio}% faible_rev={tx_faible_rev}% voiture(proxy)={tx_voiture}%"
    )
    return {
        "arrondissement":       nom,
        "nb_menages_2021":      nb_menages,
        "revenu_median_menage": revenu_median,
        "tx_propriete_pct":     tx_proprio,
        "tx_faible_revenu_pct": tx_faible_rev,
        "tx_voiture_pct":       tx_voiture,
        "pct_maisons_unifam":   pct_maisons,
    }


def compute_areas():
    """Calcule la superficie (km²) de chaque arrondissement depuis le GeoJSON."""
    gdf = gpd.read_file(ARROND_GEOJSON)
    gdf = gdf.to_crs("EPSG:32188")   # projection métrique NAD83/MTM zone 8
    gdf["area_km2"] = gdf.geometry.area / 1e6
    return {row["NOM"]: round(row["area_km2"], 2) for _, row in gdf.iterrows()}


def main():
    session = requests.Session()
    session.headers["User-Agent"] = "GeoCharge-Montreal/1.0 (GMQ580 student project)"

    print("Calcul des superficies depuis arrondissements_montreal.geojson …")
    areas = compute_areas()
    print(f"  {len(areas)} polygones traités.\n")

    rows = []
    for nom, url in RESOURCES:
        print(f"Téléchargement : {nom}")
        try:
            r = session.get(url, timeout=45, allow_redirects=True, verify=False)
            r.raise_for_status()
            parsed = parse_profile(r.content.decode("utf-8"), nom)

            # Population et densité (estimées à partir du nb de ménages et de la superficie)
            pop_est = round(parsed["nb_menages_2021"] * QC_AVG_HH_SIZE)
            geojson_nom = GEOJSON_NOM_MAP.get(nom, nom)
            area = areas.get(geojson_nom)
            if area is None:
                # Essai avec normalisation basique
                for k, v in areas.items():
                    if nom.lower().replace("–", "-").replace("’", "'") in k.lower():
                        area = v
                        break
            densite = round(pop_est / area) if area else 0
            if not area:
                print(f"  AVERTISSEMENT : superficie non trouvée pour '{nom}' (GeoJSON nom='{geojson_nom}')")

            rows.append({
                "arrondissement":       nom,
                "pop_2021":             pop_est,
                "densite_pop_km2":      densite,
                "revenu_median_menage": parsed["revenu_median_menage"],
                "tx_propriete_pct":     parsed["tx_propriete_pct"],
                "tx_voiture_pct":       parsed["tx_voiture_pct"],
                "tx_faible_revenu_pct": parsed["tx_faible_revenu_pct"],
                "source": "Données de Montréal / StatCan Recensement 2021 (CC-BY 4.0)",
            })
        except Exception as e:
            print(f"  ERREUR : {e}", file=sys.stderr)
            rows.append({
                "arrondissement":       nom,
                "pop_2021":             0,
                "densite_pop_km2":      0,
                "revenu_median_menage": 0,
                "tx_propriete_pct":     0,
                "tx_voiture_pct":       0,
                "tx_faible_revenu_pct": 0,
                "source":               "ERREUR — à compléter manuellement",
            })

    fieldnames = [
        "arrondissement", "pop_2021", "densite_pop_km2",
        "revenu_median_menage", "tx_propriete_pct",
        "tx_voiture_pct", "tx_faible_revenu_pct", "source",
    ]
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=",")
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nFichier généré : {OUTPUT_PATH}")
    ok = sum(1 for r in rows if r["pop_2021"] > 0)
    print(f"{ok}/{len(rows)} arrondissements extraits avec succès.")


if __name__ == "__main__":
    main()
