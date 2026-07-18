# Données — GeoCharge Montréal

Toutes les données sont sous licence **CC-BY 4.0** (Données Québec / Statistique Canada). Citations complètes : [SOURCES.md](SOURCES.md).

---

## Données socio-démographiques (StatCan Recensement 2021)

### [`demo_arrondissements.csv`](demo_arrondissements.csv)

Profil socio-démographique des **19 arrondissements** de la Ville de Montréal.

**Source officielle :** [Profil des ménages et des logements 2021 — Données de Montréal](https://donnees.montreal.ca/dataset/profils-menages-logements) · Statistique Canada, Recensement 2021 · Licence CC-BY 4.0

Les données ont été téléchargées automatiquement via le script [`src/preprocessing/download_demo_data.py`](../src/preprocessing/download_demo_data.py) qui lit les profils HTML de chaque arrondissement publiés sur le portail Données de Montréal.

| Variable | Description | Unité |
|---|---|---|
| `arrondissement` | Nom de l'arrondissement | — |
| `pop_2021` | Population totale | personnes |
| `densite_pop_km2` | Densité de population | hab./km² |
| `revenu_median_menage` | Revenu médian des ménages | $ CAD |
| `tx_propriete_pct` | Taux de ménages propriétaires | % |
| `tx_voiture_pct` | **Taux de ménages avec au moins un véhicule** — proxy calculé à partir du taux de propriété + type de logement (Données de Montréal 2021) | % |
| `tx_faible_revenu_pct` | % ménages avec revenu total < 40 000 $ (3 tranches de revenu, Données de Montréal 2021) | % |

**Comment ces données sont utilisées dans le projet :**

1. **Score de priorité composite** (`/api/priorite/`) — chaque arrondissement reçoit un score 0–100 combinant :
   - Déficit de couverture borne (35 %)
   - `densite_pop_km2` (25 %) — les zones denses ont plus d'usagers potentiels
   - `tx_voiture_pct` (15 %) — proxy de la demande en véhicules électriques
   - Équité de revenu (15 %) — les zones à faible revenu sont sous-pondérées dans l'offre actuelle
   - `tx_faible_revenu_pct` (10 %) — vulnérabilité socio-économique

2. **Corrélation Pearson** (`/api/correlation/`) — mesure le lien entre taux de couverture et chaque variable socio-démographique → sur les 19 arrondissements, le facteur dominant est la **densité de population** (r = 0,875), pas le revenu (r = -0,60, négatif) : ce sont les zones peu denses et dépendantes de l'auto qui sont sous-desservies, pas les zones pauvres

3. **Analyse d'équité** (`/api/equity/`) — scatter plot couverture vs revenu médian avec droite de régression

> Exemple (valeurs réelles Données de Montréal 2021, calculé en direct par l'app) : Le Plateau-Mont-Royal (`revenu_median = 60 000 $`, `tx_voiture_pct = 58 %`, `tx_faible_revenu_pct = 33.6 %`, densité = 16 212 hab/km² — la plus forte de l'île) obtient un **score de priorité de 49,9/100** malgré une couverture déjà quasi complète (97,8 %). L'Île-Bizard (`revenu_median = 98 000 $`, densité 441 hab/km²) ne score qu'à peine plus haut (**52,1/100**) malgré une couverture géographique bien plus faible (8,9 %) — car l'impact social par borne y serait bien moindre (très faible densité, revenu élevé).

---

## Données spatiales vectorielles (`vectors/`)

| Fichier | Contenu | Entités |
|---|---|---|
| [`bornes_recharge_montreal.geojson`](vectors/bornes_recharge_montreal.geojson) | Bornes de recharge publiques | 2 412 |
| [`arrondissements_montreal.geojson`](vectors/arrondissements_montreal.geojson) | Limites des arrondissements | 34 |
| [`stations_metro_stm.geojson`](vectors/stations_metro_stm.geojson) | Stations de métro STM (4 lignes) | 72 |
| [`parcs_montreal.geojson`](vectors/parcs_montreal.geojson) | Parcs et espaces verts | 1 541 |
| [`epiceries_montreal.geojson`](vectors/epiceries_montreal.geojson) | Établissements alimentaires | 3 010 |
| [`reseau_routier_montreal.geojson`](vectors/reseau_routier_montreal.geojson) | Réseau routier Géobase (CLASSE ≥ 5) | 17 540 tronçons |
| [`zones_sous_desservies.geojson`](vectors/zones_sous_desservies.geojson) | Zones sans couverture (résultat gap analysis) | variable |
| [`chargeurs_statistiques_2025.csv`](vectors/chargeurs_statistiques_2025.csv) | Statistiques d'utilisation 2025 | — |

---

*GMQ580 Géomatique Informatique 2 — Été 2026 — Université de Sherbrooke*
