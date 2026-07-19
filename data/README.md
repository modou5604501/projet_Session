# Données — GeoCharge Montréal

Toutes les données sont sous licence **CC-BY 4.0** (Données Québec / Statistique Canada). Citations complètes : [SOURCES.md](SOURCES.md).

---

## Données socio-démographiques (StatCan Recensement 2021)

### [`demo_arrondissements.csv`](demo_arrondissements.csv)

Profil socio-démographique des **19 arrondissements** de la Ville de Montréal.

**Source officielle :** [Profil des ménages et des logements 2021 — Données de Montréal](https://donnees.montreal.ca/dataset/profils-menages-logements) · Statistique Canada, Recensement 2021 · Licence CC-BY 4.0

Les données ont été extraites des profils publiés par arrondissement sur le portail Données de Montréal.

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

1. **Score de priorité** (carte interactive) — chaque arrondissement reçoit un score combinant le déficit de couverture en bornes (60 %) et `densite_pop_km2` normalisée (40 %) : `score = 0,6 × déficit_couverture + 0,4 × densité_population`. Les arrondissements aux scores les plus élevés (Beaconsfield, Dollard-des-Ormeaux, Senneville) combinent une couverture faible et une densité relativement forte pour leur secteur.

2. **Corrélation Pearson** (onglet « ③ Corrélation ») — mesure le lien entre le taux de couverture en bornes et chaque variable socio-démographique, sur les 19 arrondissements disposant d'un profil complet. Le facteur dominant est la **densité de population** (r = 0,875), pas le revenu médian (r = -0,60, négatif) : ce sont les zones peu denses et dépendantes de l'auto qui sont sous-desservies, pas les zones pauvres.

---

## Données spatiales vectorielles (`vectors/`)

| Fichier | Contenu | Entités |
|---|---|---|
| [`bornes_recharge_montreal.geojson`](vectors/bornes_recharge_montreal.geojson) | Bornes de recharge publiques | 2 412 |
| [`arrondissements_montreal.geojson`](vectors/arrondissements_montreal.geojson) | Limites des arrondissements | 34 |
| [`parcs_montreal.geojson`](vectors/parcs_montreal.geojson) | Parcs et espaces verts | 1 541 |
| [`epiceries_montreal.geojson`](vectors/epiceries_montreal.geojson) | Établissements alimentaires | 3 010 |
| [`reseau_routier_montreal.geojson`](vectors/reseau_routier_montreal.geojson) | Réseau routier Géobase (CLASSE ≥ 5) | 17 540 tronçons |
| [`zones_sous_desservies.geojson`](vectors/zones_sous_desservies.geojson) | Zones sans couverture (résultat gap analysis) | variable |
| [`chargeurs_statistiques_2025.csv`](vectors/chargeurs_statistiques_2025.csv) | Statistiques d'utilisation 2025 | — |

---

*GMQ580 Géomatique Informatique 2 — Été 2026 — Université de Sherbrooke*
