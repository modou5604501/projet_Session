# Données — GeoCharge Montréal

Toutes les données sont sous licence **CC-BY 4.0** (Données Québec / Statistique Canada). Citations complètes : [SOURCES.md](SOURCES.md).

---

## Données socio-démographiques (StatCan Recensement 2021)

### [`demo_arrondissements.csv`](demo_arrondissements.csv)

Profil socio-démographique des **19 arrondissements** de la Ville de Montréal, extrait du Recensement de la population 2021 de Statistique Canada.

| Variable | Description | Unité |
|---|---|---|
| `arrondissement` | Nom de l'arrondissement | — |
| `pop_2021` | Population totale | personnes |
| `densite_pop_km2` | Densité de population | hab./km² |
| `revenu_median_menage` | Revenu médian des ménages | $ CAD |
| `tx_propriete_pct` | Taux de ménages propriétaires | % |
| `tx_voiture_pct` | **Taux de ménages avec au moins un véhicule** (proxy demande VE) | % |
| `tx_faible_revenu_pct` | Taux de population sous le seuil de faible revenu (MBM 2021) | % |

**Comment ces données sont utilisées dans le projet :**

1. **Score de priorité composite** (`/api/priorite/`) — chaque arrondissement reçoit un score 0–100 combinant :
   - Déficit de couverture borne (35 %)
   - `densite_pop_km2` (25 %) — les zones denses ont plus d'usagers potentiels
   - `tx_voiture_pct` (15 %) — proxy de la demande en véhicules électriques
   - Équité de revenu (15 %) — les zones à faible revenu sont sous-pondérées dans l'offre actuelle
   - `tx_faible_revenu_pct` (10 %) — vulnérabilité socio-économique

2. **Corrélation Pearson** (`/api/correlation/`) — mesure le lien entre taux de couverture et chaque variable socio-démographique → confirme une corrélation positive entre revenu médian et couverture (inéquité structurelle)

3. **Analyse d'équité** (`/api/equity/`) — scatter plot couverture vs revenu médian avec droite de régression

> Exemple : Montréal-Nord (`revenu_median = 37 000 $`, `tx_voiture_pct = 60 %`, `tx_faible_revenu_pct = 38 %`) obtient un **score de priorité ≈ 72/100** malgré une couverture de 25 %. L'Île-Bizard (`revenu_median = 82 000 $`, densité 520 hab/km²) ne score que **≈ 50/100** malgré moins de couverture — car l'impact social par borne y serait bien moindre.

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
