# GeoRisk Sentinel
## Détection automatique des zones inondées affectant les infrastructures électriques à Sainte-Marthe-sur-le-Lac

**Cours :** GMQ580 — Géomatique Informatique 2
**Session :** Été 2026
**Établissement :** Université de Sherbrooke

### Équipe

| Nom | Courriel |
|---|---|
| Modou Khabane Mbaye | modou.khabane.mbaye@usherbrooke.ca |
| Rahina Djelila Sarah Bagre | rahina.bagre@usherbrooke.ca |

---

## Table des matières

1. [Présentation du projet](#1-présentation-du-projet)
2. [Problématique](#2-problématique)
3. [Zone d'étude](#3-zone-détude)
4. [Données](#4-données)
5. [Modèle de données](#5-modèle-de-données)
6. [Pipeline de traitement et Architecture](#6-pipeline-de-traitement-et-architecture)
7. [Schéma Mermaid — Draw.io](#7-schéma-mermaid--drawio)
8. [Bibliothèques principales (stack)](#8-bibliothèques-principales-stack)
9. [Livrables attendus](#9-livrables-attendus)
10. [État d'avancement](#10-état-davancement)
11. [Décisions méthodologiques](#11-décisions-méthodologiques)
12. [Difficultés rencontrées](#12-difficultés-rencontrées)
13. [Installation et démarrage](#13-installation-et-démarrage)
14. [Dépôts GitHub utilisés](#14-dépôts-github-utilisés)
15. [Références](#15-références)

---

## 1. Présentation du projet

**GeoRisk Sentinel** est une plateforme géospatiale intelligente développée dans le cadre du cours GMQ580 (Géomatique Informatique 2). Elle vise à **détecter automatiquement les zones inondées susceptibles d'affecter les infrastructures électriques** dans la municipalité de Sainte-Marthe-sur-le-Lac.

Le projet combine :

- l'analyse spatiale multicritère (SIG)
- les images satellites Sentinel-1 SAR
- la détection de changement et l'intelligence artificielle (modèle U-Net)
- une base de données spatiale PostGIS
- une carte web interactive (Django + Leaflet)

Le projet est entièrement **open source** : tout le code est versionné sur GitHub et l'environnement est conteneurisé avec Docker.

---

## 2. Problématique

### Contexte

Les inondations représentent une menace croissante pour les infrastructures critiques, en particulier les réseaux électriques. La municipalité de **Sainte-Marthe-sur-le-Lac** a connu une catastrophe majeure le **27 avril 2019** : la rupture de la digue principale a provoqué l'inondation de plus de **6 000 résidences** et forcé l'évacuation de la totalité de la population en quelques heures.

Cet événement a mis en évidence l'absence d'un système de surveillance géospatiale capable de :
- détecter automatiquement les zones inondées à partir d'images satellites
- identifier les infrastructures électriques à risque immédiat
- générer des alertes préventives
- produire des cartes de vulnérabilité à partir de données officielles

### Question de recherche

> Comment développer une plateforme géospatiale intelligente permettant la détection automatique des zones inondées et l'identification des infrastructures électriques vulnérables à Sainte-Marthe-sur-le-Lac, à partir d'images Sentinel-1 SAR, de données MRNF et d'analyses spatiales PostGIS ?

### Périmètre du projet (ce qui n'est PAS traité)

- Simulation hydrologique avancée (modèle 2D de propagation)
- Systèmes IoT ou capteurs en temps réel
- Application mobile
- Traitement des nuages (Sentinel-2 non utilisé à cause de la couverture nuageuse de 2019)
- Réentraînement du modèle U-Net (utilisation du modèle pré-entraîné Sen1Floods11)

### Utilisateurs visés

- Municipalité de Sainte-Marthe-sur-le-Lac
- Gestionnaires du réseau électrique (Hydro-Québec)
- Services de sécurité civile
- Chercheurs en géomatique et risques naturels

---

## 3. Zone d'étude

### Localisation

**Sainte-Marthe-sur-le-Lac** est une municipalité de la région des Laurentides, à 30 km au nord-ouest de Montréal.

Elle est délimitée par :
- le **Lac des Deux Montagnes** au sud
- la **Rivière des Mille-Îles** à l'est
- Saint-Eustache et Deux-Montagnes au nord

### Secteurs prioritaires

| Secteur | Description | Risque |
|---|---|---|
| Sud (22e Av. → lac) | Zone directement inondée en 2019 | Très élevé |
| Parc de la Frayère | Zone tampon naturelle en bordure du lac | Élevé |
| Parc Roland-Laliberté | Secteur résidentiel proche de l'eau | Élevé |
| Réseau d'avenues (17e–32e) | Infrastructure urbaine et électrique dense | Moyen à élevé |

### Paramètres techniques

| Paramètre | Valeur |
|---|---|
| Système de coordonnées | EPSG:32198 (NAD83 / Québec Lambert) |
| Résolution spatiale | 10 m (Sentinel-1 IW GRD) et 30 m (DEM Copernicus) |
| Emprise BBOX (WGS84) | (-74.05, 45.48, -73.85, 45.60) |
| Événement de référence | Rupture de digue du 27 avril 2019 |
| Échelle d'étude | Urbaine (municipalité entière) |

### Justification du choix

- Événement d'inondation réel, documenté et bien daté
- Données officielles disponibles (MRNF zones inondées 2017 et 2019)
- Réseau électrique urbain dense cartographié dans OpenStreetMap
- Données Sentinel-1 disponibles avant et après la rupture de digue

---

## 4. Données

### Sources utilisées

| Couche | Source | Format | CRS | Accès | Disponibilité |
|---|---|---|---|---|---|
| Zones inondées 2017 et 2019 | MRNF Québec (Données Québec) | GPKG | EPSG:3857 | Gratuit | Téléchargé localement (277 Mo — exclu du repo) |
| Images radar SAR | Sentinel-1 GRD (ESA/CDSE) | GeoTIFF | EPSG:4326 (GCPs) | Gratuit (compte CDSE requis) | Téléchargé localement (~6.5 GB — exclu du repo) |
| Réseau électrique haute tension | OpenStreetMap (Overpass Turbo) | GeoJSON | EPSG:4326 | Gratuit | ✅ Dans le repo : `data/vectors/electric_network_sainte_marthe.geojson` |
| Réseau électrique complet | OpenStreetMap (QuickOSM/QGIS) | GeoJSON | EPSG:4326 | Gratuit | ✅ Acquis le 7 juillet 2026 (888 entités) |
| Bâtiments résidentiels | OpenStreetMap (QuickOSM/QGIS) | GeoJSON | EPSG:4326 | Gratuit | ✅ Acquis le 7 juillet 2026 |
| Routes et rues | OpenStreetMap (QuickOSM/QGIS) | GeoJSON | EPSG:4326 | Gratuit | ✅ Acquis le 7 juillet 2026 |
| Modèle numérique d'élévation | Copernicus DEM GLO-30 (AWS) | GeoTIFF | EPSG:4326 | Gratuit (public) | Téléchargé localement (43.5 Mo — exclu du repo) |

### Comment obtenir les données volumineuses

Les fichiers dépassant 100 Mo sont exclus du dépôt GitHub via `.gitignore`. Voici comment les obtenir :

| Données | Commande / Source |
|---|---|
| Zones inondées MRNF | [Données Québec](https://www.donneesquebec.ca) → rechercher "Territoire inondé en 2017 et 2019" → télécharger le GPKG |
| DEM Copernicus | `python src/acquisition/download_dem.py` (téléchargement automatique depuis AWS S3 public) |
| Images Sentinel-1 | `python src/acquisition/download_sentinel1.py` (nécessite un compte CDSE gratuit et les variables `.env`) |

### Détail Sentinel-1 — 4 scènes acquises

| Fichier | Date | Période | Polarisation |
|---|---|---|---|
| S1A_IW_GRDH_1SDV_20190408... | 8 avril 2019 | Avant inondation | VV + VH |
| S1A_IW_GRDH_1SDH_20190420... | 20 avril 2019 | Avant inondation | HH + HV |
| S1A_IW_GRDH_1SDV_20190502... | 2 mai 2019 | Après inondation | VV + VH |
| S1A_IW_GRDH_1SDV_20190514... | 14 mai 2019 | Après inondation | VV + VH |

### Données produites (après prétraitement)

| Fichier | Description | Taille |
|---|---|---|
| `data/processed/dem_sainte_marthe_32198.tif` | DEM clip + EPSG:32198 (30m) | 1.0 Mo |
| `data/processed/slope_sainte_marthe.tif` | Pente calculée depuis DEM | 1.0 Mo |
| `data/processed/aspect_sainte_marthe.tif` | Aspect calculé depuis DEM | 1.0 Mo |
| `data/processed/sentinel1/s1_sainte_marthe_<date>_32198.tif` | Scènes SAR en dB, EPSG:32198 (10m) | 4 × 16.1 Mo |
| `data/processed/flood_masks/flood_<date>.tif` | Masques eau (méthode percentile) | 4 × ~100 Ko |
| `data/processed/flood_masks/flood_change.tif` | Carte de changement avant/après | 192 Ko |

---

## 5. Modèle de données

Le projet utilise PostgreSQL 15 avec l'extension PostGIS 3.3 pour gérer les données spatiales.

### Table `electric_network`

| Champ | Type | Description |
|---|---|---|
| id | SERIAL PRIMARY KEY | Identifiant unique |
| osm_id | BIGINT | Identifiant OpenStreetMap |
| type | VARCHAR(50) | line, substation, cable, transformer... |
| voltage | INT | Tension en volts |
| criticality | VARCHAR(20) | low, medium, high |
| geom | GEOMETRY(GEOMETRY, 32198) | Géométrie (point ou ligne) |

**Données importées :** 60 entités OSM — lignes, postes et pylônes

### Table `flood_zones`

| Champ | Type | Description |
|---|---|---|
| id | SERIAL PRIMARY KEY | Identifiant unique |
| source | VARCHAR(50) | MRNF, Sentinel, IA |
| date_detection | DATE | Date de détection |
| recurrence | INT | Période de retour (20 ou 100 ans) |
| surface_ha | FLOAT | Surface en hectares |
| geom | GEOMETRY(MULTIPOLYGON, 32198) | Polygones des zones inondées |

**Données importées :** 6 polygones MRNF (zones inondées 2017 et 2019, clip Sainte-Marthe)

### Table `risk_analysis`

| Champ | Type | Description |
|---|---|---|
| id | SERIAL PRIMARY KEY | Identifiant unique |
| infra_id | INT | Référence à electric_network |
| niveau_risque | VARCHAR(20) | low, medium, high, critical |
| distance_m | FLOAT | Distance à la zone inondée (m) |
| date_analyse | TIMESTAMP | Horodatage |

### Table `alertes`

| Champ | Type | Description |
|---|---|---|
| id | SERIAL PRIMARY KEY | Identifiant unique |
| niveau | VARCHAR(20) | info, warning, critical |
| message | TEXT | Contenu de l'alerte |
| infra_id | INT | Référence à electric_network |
| date_alerte | TIMESTAMP | Horodatage |
| acquittee | BOOLEAN | Alerte traitée ou non |

---

## 6. Pipeline de traitement et Architecture

### Pipeline complet

```
[Phase 1 — Acquisition]
    ├── download_dem.py         → DEM Copernicus GLO-30 (AWS S3, accès public)
    ├── download_sentinel1.py   → 4 scènes Sentinel-1 GRD via CDSE OData API
    └── Overpass Turbo (manuel) → Réseau électrique OSM (GeoJSON)

[Phase 2 — Prétraitement]
    ├── preprocess_dem.py
    │     ├── Clip sur BBOX Sainte-Marthe (shapely)
    │     ├── Reprojection → EPSG:32198 (rasterio.warp)
    │     └── Calcul pente et aspect (numpy.gradient)
    ├── preprocess_sentinel1.py
    │     ├── Extraction archives SAFE.zip
    │     ├── Lecture bandes VV/VH via GCPs (210 GCPs/scène)
    │     ├── Reprojection → EPSG:32198 sur BBOX cible
    │     └── Calibration dB : 20 × log10(DN / 65 535)
    └── import_postgis.py
          ├── OSM GeoJSON → table electric_network (60 entités)
          └── MRNF GPKG → table flood_zones (6 polygones)

[Phase 3 — Détection de zones inondées]
    └── flood_detection.py
          ├── Méthode 1 : percentile bas (12e) → masque eau par image
          ├── Méthode 2 : change detection SAR (après_dB − avant_dB)
          │     → seuil : −4 dB → 3 233 ha nouvellement inondés
          └── Carte de changement : flood_change.tif

[Phase 4 — Analyse spatiale (PostGIS / GeoDjango)]
    ├── ST_Intersects  → infras dans les zones inondées (critique)
    ├── ST_Buffer 500m → infras proches des zones (alerte)
    └── risk_summary   → résumé JSON via API DRF

[Phase 5 — Application web]
    └── Django 5.2 + GeoDjango
          ├── API REST : /api/electric/, /api/floods/, /api/risk-summary/
          ├── Carte Leaflet interactive (fond OSM + satellite Esri)
          └── Admin Django pour gestion des alertes
```

### Architecture des services Docker

```
┌─────────────────────────────────────────────────────────────┐
│                    GEORISK SENTINEL                          │
├──────────────────┬──────────────────┬────────────────────────┤
│  georisk_postgis │ georisk_pgadmin  │    georisk_web         │
│  (port 5433)     │ (port 5050)      │    (port 8000)         │
│                  │                  │                        │
│  PostGIS 15.3    │ pgAdmin 4        │ Django 5.2 + GeoDjango │
│  ─────────────── │  ─────────────── │ ──────────────────     │
│  electric_network│  Interface SQL   │ /api/electric/         │
│  flood_zones     │  graphique       │ /api/floods/           │
│  risk_analysis   │                  │ /api/risk-summary/     │
│  alertes         │                  │ /  → carte Leaflet     │
└──────────────────┴──────────────────┴────────────────────────┘
```

---

## 7. Schéma Mermaid — Draw.io

Voir le fichier [DIAGRAMME_MERMAID.md](DIAGRAMME_MERMAID.md) pour les diagrammes à coller dans Draw.io.

**Comment utiliser :**
1. Ouvrir [app.diagrams.net](https://app.diagrams.net)
2. Menu **Extras** → **Edit Diagram**
3. Coller le code Mermaid → cliquer **OK**

---

## 8. Bibliothèques principales (stack)

| Domaine | Technologie | Version | Rôle |
|---|---|---|---|
| Langage principal | Python | 3.10 | Traitement, IA, backend |
| Framework web | Django + GeoDjango | 5.2 LTS | Interface, API REST, requêtes spatiales |
| API REST | Django REST Framework | 3.17 | Sérialisation JSON/GeoJSON |
| SIG bureau | QGIS | 3.x | Visualisation et validation |
| Base de données | PostgreSQL + PostGIS | 15 + 3.3 | Stockage spatial (Docker) |
| Carte web | Leaflet.js | 1.9 | Carte interactive |
| Traitement raster | Rasterio | 1.4 | Images satellites |
| Analyse spatiale | GeoPandas | 0.14 | Vecteur SIG |
| Coordonnées | PyProj | 3.7 | Reprojection CRS |
| IA / Deep Learning | PyTorch | 2.x + U-Net | Détection inondations (structure prête) |
| Conteneurisation | Docker + Compose | — | Déploiement reproductible |
| Versionnement | Git + GitHub | — | Open source |

---

## 9. Livrables attendus

| Livrable | Description | Statut |
|---|---|---|
| Scripts d'acquisition | download_dem.py, download_sentinel1.py | ✅ Écrits et dans le repo |
| Scripts de prétraitement | preprocess_dem.py, preprocess_sentinel1.py, import_postgis.py | ✅ Écrits et dans le repo |
| Script détection IA | flood_detection.py (change detection SAR) | ✅ Écrit et dans le repo |
| Données OSM | Réseau électrique, bâtiments, routes (GeoJSON) | ✅ Acquis et validés dans QGIS |
| Données MRNF | Zones inondées 2017/2019 (GPKG 277 Mo) | ✅ Téléchargées et validées dans QGIS |
| flood_change.tif | Carte de changement avant/après inondation | ✅ Produit (192 Ko) |
| DEM prétraité | Clip + pente + aspect EPSG:32198 | ✅ Produit localement |
| Structure Django | Projet + app risk_map + templates Leaflet | ✅ Code écrit — ⏳ Tests à effectuer |
| API REST GeoJSON | /api/electric/, /api/floods/, /api/risk-summary/ | ✅ Code écrit — ⏳ Tests à effectuer |
| Base de données PostGIS | Tables SQL définies, docker-compose.yml prêt | ✅ Fichiers écrits — ⏳ Import à faire |
| Docker Compose | PostGIS + pgAdmin + Django | ✅ Fichier écrit — ⏳ Tests à effectuer |
| Dépôt GitHub | Code versionné (phases 1 et 2 publiées) | ✅ En ligne |
| Rapport technique final | Document PDF | ⏳ En cours de rédaction |
| Présentation (soutenance) | Slides + démonstration | ⏳ À faire |

---

## 10. État d'avancement

| Phase | Tâche | Statut | Date |
|---|---|---|---|
| Phase 1 | Recherche documentaire et choix des technologies | ✅ Complété | 24 juin 2026 |
| Phase 1 | Définition zone d'étude (Sainte-Marthe-sur-le-Lac) | ✅ Complété | 24 juin 2026 |
| Phase 1 | Documentation initiale (README, CHRONOGRAMME, MERMAID) | ✅ Complété | 24 juin 2026 |
| Phase 2 | Acquisition réseau électrique haute tension OSM (60 entités) | ✅ Complété | 25 juin 2026 |
| Phase 2 | Acquisition zones inondées MRNF 2017/2019 (GPKG 277 Mo) | ✅ Complété | 25 juin 2026 |
| Phase 2 | Acquisition DEM Copernicus GLO-30 (AWS S3, 43.5 Mo) | ✅ Complété | 26 juin 2026 |
| Phase 2 | Acquisition Sentinel-1 SAR x4 (CDSE, ~6.5 GB) | ✅ Complété | 26 juin 2026 |
| Phase 2 | Acquisition réseau électrique complet OSM via QuickOSM (888 entités) | ✅ Complété | 7 juillet 2026 |
| Phase 2 | Acquisition bâtiments résidentiels OSM (QuickOSM) | ✅ Complété | 7 juillet 2026 |
| Phase 2 | Acquisition réseau routier OSM (QuickOSM) | ✅ Complété | 7 juillet 2026 |
| Phase 2 | Validation de toutes les données dans QGIS | ✅ Complété | 7 juillet 2026 |
| Phase 3 | Écriture scripts prétraitement DEM et Sentinel-1 | ✅ Scripts écrits | 27 juin 2026 |
| Phase 3 | Écriture script import PostGIS | ✅ Script écrit | 27 juin 2026 |
| Phase 3 | Définition tables SQL (docker-compose + sql/) | ✅ Fichiers écrits | 27 juin 2026 |
| Phase 3 | Exécution prétraitement DEM (résultats locaux) | ✅ Complété | 27 juin 2026 |
| Phase 3 | Exécution prétraitement Sentinel-1 (résultats locaux) | ✅ Complété | 27 juin 2026 |
| Phase 3 | Démarrage Docker PostGIS + import données | ⏳ À faire | Avant 9 juill. |
| Phase 4 | Détection zones inondées — change detection SAR (flood_change.tif) | ✅ Complété | 27 juin 2026 |
| Phase 4 | Analyse spatiale ST_Intersects PostGIS | ⏳ À faire | Avant 9 juill. |
| Phase 5 | Structure projet Django + GeoDjango + templates Leaflet | ✅ Code écrit | 27 juin 2026 |
| Phase 5 | API REST (code views.py, serializers.py) | ✅ Code écrit | 27 juin 2026 |
| Phase 5 | Tests et validation de l'application web | ⏳ À faire | Avant 12 juill. |
| Phase 6 | Docker Compose (fichier écrit, services configurés) | ✅ Fichier écrit | 27 juin 2026 |
| Phase 6 | Tests Docker Compose end-to-end | ⏳ À faire | Avant 12 juill. |
| Phase 6 | Dépôt GitHub (phases 1 et 2 publiées) | ✅ Complété | 27 juin 2026 |
| Phase 6 | Rapport technique final | ⏳ En cours | Avant 14 juill. |
| Phase 6 | Présentation de soutenance | ⏳ À faire | Avant 14 juill. |

---

## 11. Décisions méthodologiques

| Décision | Justification |
|---|---|
| Sainte-Marthe-sur-le-Lac (pas Sherbrooke) | Événement réel 2019 documenté, données MRNF officielles disponibles |
| Django (pas FastAPI) | Plus complet pour une app web : admin, templates, GeoDjango natif |
| Sentinel-1 SAR (pas Sentinel-2) | Insensible aux nuages — indispensable pour avril 2019 (temps couvert) |
| Modèle U-Net pré-entraîné (pas réentraîné) | Délai serré — inférence sur Sen1Floods11 suffisante pour démonstration |
| Change detection (pas seuil absolu) | Calibration SAR non résolue → détection relative avant/après fiable |
| DEM Copernicus (pas LiDAR) | Accès public AWS, 43.5 Mo, sans authentification, 30m suffisant |
| Port 5433 (pas 5432) | Conflit avec PostgreSQL 16 local déjà installé |
| PostGIS dans Docker (pas local) | Isolation, reproductibilité, données persistantes via volume |
| GDAL/GEOS via rasterio.libs | Résout le conflit entre PostgreSQL 16 et les librairies du venv Python |
| GCPs pour Sentinel-1 | Les fichiers SAFE Sentinel-1 n'ont pas de transform affine natif |

---

## 12. Difficultés rencontrées

| Difficulté | Solution appliquée |
|---|---|
| Port Docker 5432 occupé par PostgreSQL 16 local | Changement du mapping : `5433:5432` dans docker-compose.yml |
| Variable système `PROJ_LIB` pointe vers PostgreSQL 16 | Override `PROJ_DATA` + `PROJ_LIB` vers `rasterio.libs/` avant import rasterio |
| GDAL/GEOS manquants pour Django sur Windows | `GDAL_LIBRARY_PATH` + `GEOS_LIBRARY_PATH` pointés vers DLL hashées de `shapely.libs/` |
| Sentinel-1 SAFE sans CRS affine (GCPs seulement) | Lecture des 210 GCPs, `from_gcps()` pour la reprojection `reproject()` |
| Calibration SAR — valeurs hors plage | Formule 20×log10(DN/65535) ; change detection pour s'affranchir du biais absolu |
| GeoPandas `to_postgis` avec clés étrangères | `TRUNCATE ... CASCADE` + `if_exists="append"` au lieu de `replace` |
| MRNF GPKG géométries 3D (MultiPolygon Z) | `shapely.force_2d()` avant import |
| Emojis dans print() — terminal Windows CP1252 | Remplacés par du texte ASCII dans tous les scripts |
| djangorestframework-gis remplace Django 4.2 par 5.2 | Accepté — Django 5.2 est la version LTS actuelle |

---

## 13. Installation et démarrage

### Prérequis

- Docker Desktop (Engine en cours d'exécution)
- Python 3.10 avec venv
- Git
- Compte Copernicus CDSE (gratuit) pour Sentinel-1

### Démarrage rapide

```bash
# 1. Cloner le dépôt
git clone https://github.com/<votre-compte>/georisk-sentinel.git
cd georisk-sentinel

# 2. Créer le fichier de credentials (NE PAS COMMITTER)
cp .env.example .env
# Remplir CDSE_USERNAME et CDSE_PASSWORD

# 3. Démarrer PostGIS + pgAdmin
docker-compose up -d postgis pgadmin

# 4. Installer les dépendances Python
python -m venv venv
pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org

# 5. Importer les données
python src/preprocessing/import_postgis.py

# 6. Lancer Django
cd src/web
python manage.py runserver 0.0.0.0:8000
```

**OU — Script tout-en-un (Windows) :**
```
demarrer.bat
```

### Services et ports

| Service | Port hôte | Description |
|---|---|---|
| PostGIS | 5433 | Base de données spatiale (port hôte 5433 → conteneur 5432) |
| pgAdmin | 5050 | Interface d'administration BD |
| Django (carte) | 8000 | Application web + API |

### Accès

```
Carte interactive :   http://localhost:8000
API réseau élec. :   http://localhost:8000/api/electric/
API zones inond. :   http://localhost:8000/api/floods/
Résumé des risques : http://localhost:8000/api/risk-summary/
pgAdmin :            http://localhost:5050
  Email    : modou.khabane.mbaye@usherbrooke.ca
  Password : georisk2019
  Serveur  : georisk_postgis / port 5432 / db georisk
```

---

## 14. Dépôts GitHub utilisés

| Dépôt | Utilisation |
|---|---|
| [cloudtostreet/Sen1Floods11](https://github.com/cloudtostreet/Sen1Floods11) | Modèle U-Net pré-entraîné + dataset inondations Sentinel-1 |
| [postgis/postgis](https://hub.docker.com/r/postgis/postgis) | Image Docker PostGIS 15-3.3 |
| [dpage/pgadmin4](https://hub.docker.com/r/dpage/pgadmin4) | Image Docker pgAdmin 4 |
| [Leaflet.js](https://github.com/Leaflet/Leaflet) | Carte web interactive |
| [djangorestframework-gis](https://github.com/openwisp/django-rest-framework-gis) | Sérialisation GeoJSON pour DRF |
| [geopandas](https://github.com/geopandas/geopandas) | Analyse géospatiale Python |

---

## 15. Références

- Documentation Django / GeoDjango : https://docs.djangoproject.com
- Documentation PostGIS : https://postgis.net/documentation
- Documentation Rasterio : https://rasterio.readthedocs.io
- Documentation GeoPandas : https://geopandas.org/docs
- Portail zones inondables — MRNF Québec : https://zonesinondables.mrnf.gouv.qc.ca
- Données Québec (zones inondées 2017-2019) : https://www.donneesquebec.ca
- OpenStreetMap : https://www.openstreetmap.org
- Copernicus DEM GLO-30 (AWS) : https://registry.opendata.aws/copernicus-dem
- Copernicus Data Space Ecosystem : https://dataspace.copernicus.eu
- Sen1Floods11 (dataset IA) : https://github.com/cloudtostreet/Sen1Floods11
- Leaflet : https://leafletjs.com

---

*Projet académique — GMQ580 Géomatique Informatique 2 — Été 2026 — Université de Sherbrooke*
