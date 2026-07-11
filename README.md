# GeoRisk Sentinel
## Accessibilité aux bornes de recharge électrique à Montréal

**Cours :** GMQ580 — Géomatique Informatique 2 · Été 2026 · Université de Sherbrooke

| Nom | Courriel |
|---|---|
| Modou Khabane Mbaye | modou.khabane.mbaye@usherbrooke.ca |
| Rahina Djelila Sarah Bagre | rahina.bagre@usherbrooke.ca |

---

## Problématique

La distribution des bornes de recharge publiques à Montréal est inégale : les arrondissements centraux concentrent la majorité des installations tandis que les secteurs périphériques en manquent. Il n'existe pas d'outil permettant de quantifier ces disparités ni d'orienter les décisions d'investissement.

**Question de recherche :** Où faudrait-il installer de nouvelles bornes de recharge à Montréal afin de maximiser l'accessibilité des usagers tout en réduisant les zones sous-desservies ?

---

## Données

Toutes les données sont disponibles dans le dossier [`data/`](data/) de ce dépôt, sous licence CC-BY 4.0.

| Couche | Fichier | Source |
|---|---|---|
| Bornes de recharge publiques (2 412 bornes) | [`data/vectors/bornes_recharge_montreal.geojson`](data/vectors/bornes_recharge_montreal.geojson) | Données Québec — Ville de Montréal |
| Statistiques d'utilisation 2025 | [`data/vectors/chargeurs_statistiques_2025.csv`](data/vectors/chargeurs_statistiques_2025.csv) | Données Québec — Ville de Montréal |
| Limites des arrondissements | [`data/vectors/arrondissements_montreal.geojson`](data/vectors/arrondissements_montreal.geojson) | Données Québec — Ville de Montréal |
| Stations de métro (STM) | [`data/vectors/stm_sig/`](data/vectors/stm_sig/) | Données Québec — STM |
| Référentiel quartiers / revenu médian | [`data/quartiers_reference_habitation.csv`](data/quartiers_reference_habitation.csv) | Données Québec — StatCan Recensement 2021 |

Les zones sous-desservies calculées par l'analyse sont disponibles dans [`data/vectors/zones_sous_desservies.geojson`](data/vectors/zones_sous_desservies.geojson).

---

## Pipeline de traitement

```
Données Québec (GeoJSON, CSV, SHP)
      ↓  src/preprocessing/import_postgis.py   (import + reprojection STM MTM8→WGS84)
      ↓  src/preprocessing/buffer_analysis.py  (ST_Buffer 500m en EPSG:32188, ST_Union, %couverture)
      ↓  src/preprocessing/gap_analysis.py     (ST_Difference → zones_sous_desservies.geojson)
PostGIS 15.3 · 4 tables : bornes_recharge · zones_couverture · arrondissements · stations_metro
      ↓  Django 5.2 + GeoDjango · API REST GeoJSON
Tableau de bord Leaflet.js → http://localhost:8000
```

Le rayon de 500 m correspond à la distance de marche accessible recommandée en urbanisme actif.
La reprojection en EPSG:32188 (NAD83 / MTM zone 8) garantit la précision métrique des buffers.

---

## Fonctionnalités du tableau de bord

- **Choroplèthe** : taux de couverture à 500 m par arrondissement (vert ≥ 60 % · jaune 30-60 % · orange 15-30 % · rouge < 15 %)
- **Couche zones non couvertes** : zones géographiques sans borne issues de `gap_analysis.py`
- **Requêtes spatiales PostGIS** (4 requêtes interactives) : N bornes les plus proches (KNN `<->`), bornes dans un rayon (`ST_DWithin`), stations de métro sans borne (`NOT EXISTS`), arrondissements peu équipés
- **Analyse d'équité** : scatter plot couverture vs revenu médian (StatCan 2021), coefficient de Pearson, droite de régression, interprétation automatique
- **Simulation** : slider de seuil de sous-desserte avec recoloration de la carte en temps réel
- **Mise à jour automatique** : re-téléchargement hebdomadaire depuis Données Québec (APScheduler + API CKAN)
- **PWA** : installable sur tablette (manifest.json + service worker)

---

## Technologies

| Technologie | Rôle |
|---|---|
| Python 3.10 | Traitement des données, backend |
| Django 5.2 + GeoDjango | API REST GeoJSON, vue carte, scheduler |
| PostgreSQL 15 + PostGIS 3.3 | Stockage spatial, requêtes géographiques |
| GeoPandas 1.0 + PyProj 3.7 | Import vecteur, reprojection CRS |
| Leaflet.js 1.9 | Carte web interactive |
| Docker Compose | Environnement reproductible (PostGIS + pgAdmin) |
| Railway | Déploiement production (voir [DEPLOIEMENT.md](DEPLOIEMENT.md)) |

---

## Démarrage local

```bash
git clone https://github.com/modou5604501/projet_Session.git
cd projet_Session
docker-compose up -d postgis
python -m venv venv && pip install -r requirements.txt
python src/preprocessing/import_postgis.py
cd src/web && python manage.py runserver
# Tableau de bord : http://localhost:8000
```

---

## Références

- Ville de Montréal. *Bornes de recharge publiques*, Données Québec. CC-BY 4.0. Consulté le 7 juillet 2026.
- Ville de Montréal. *Limites administratives de l'agglomération*, Données Québec. CC-BY 4.0. Mis à jour le 30 juin 2026.
- Société de transport de Montréal. *Tracés des lignes et arrêts STM*, Données Québec. CC-BY 4.0. Mis à jour le 6 juillet 2026.
- Statistique Canada. *Commande personnalisée du recensement 2021*, Données Québec. CC-BY 4.0. Consulté le 8 juillet 2026.
- PostGIS Documentation : https://postgis.net/documentation

---

*GMQ580 Géomatique Informatique 2 — Été 2026 — Université de Sherbrooke*
