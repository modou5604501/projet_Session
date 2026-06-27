# GeoRisk Sentinel
## Détection automatique des zones inondées affectant les infrastructures électriques à Sainte-Marthe-sur-le-Lac

**Cours :** GMQ580 — Géomatique Informatique 2  
**Session :** Été 2026  
**Étudiant :** Modou Khabane Mbaye  
**Établissement :** Université de Sherbrooke  

---

## Table des matières

1. [Présentation du projet](#1-présentation-du-projet)
2. [Problématique](#2-problématique)
3. [Zone d'étude](#3-zone-détude)
4. [Objectifs](#4-objectifs)
5. [Architecture technique](#5-architecture-technique)
6. [Données utilisées](#6-données-utilisées)
7. [Modèle de données PostGIS](#7-modèle-de-données-postgis)
8. [Modèle IA — U-Net](#8-modèle-ia--u-net)
9. [Pipeline de traitement](#9-pipeline-de-traitement)
10. [Stack technologique](#10-stack-technologique)
11. [Structure du projet](#11-structure-du-projet)
12. [Installation et déploiement](#12-installation-et-déploiement)
13. [État d'avancement](#13-état-davancement)
14. [Chronogramme](#14-chronogramme)
15. [Références](#15-références)

---

## 1. Présentation du projet

**GeoRisk Sentinel** est une plateforme géospatiale intelligente développée dans le cadre du cours GMQ580 (Géomatique Informatique 2). Elle vise à **détecter automatiquement les zones inondées susceptibles d'affecter les infrastructures électriques** dans la municipalité de Sainte-Marthe-sur-le-Lac, en s'appuyant sur :

- l'analyse spatiale multicritère (SIG)
- les images satellites Sentinel-1 et Sentinel-2
- l'intelligence artificielle (modèle U-Net)
- une base de données spatiale PostGIS
- une carte web interactive (Django + Leaflet)

Le projet s'inscrit dans une démarche **open source** : tout le code est versionné sur GitHub et l'environnement est conteneurisé avec Docker.

---

## 2. Problématique

### Contexte

Les inondations représentent une menace croissante pour les infrastructures critiques, en particulier les réseaux électriques. La municipalité de **Sainte-Marthe-sur-le-Lac** a connu une catastrophe majeure le **27 avril 2019** : la rupture de la digue principale a provoqué l'inondation de plus de **6 000 résidences** et forcé l'évacuation de la totalité de la population.

Cet événement a mis en évidence l'absence de système de surveillance géospatiale en temps réel capable de :
- détecter automatiquement les zones inondées
- identifier les infrastructures électriques à risque
- générer des alertes préventives
- produire des cartes de vulnérabilité actualisées

### Question de recherche

> Comment développer une plateforme géospatiale intelligente permettant la détection automatique des zones inondées et l'identification des infrastructures électriques vulnérables à Sainte-Marthe-sur-le-Lac, à partir d'images satellites, d'analyses spatiales et de l'intelligence artificielle ?

---

## 3. Zone d'étude

### Localisation

**Sainte-Marthe-sur-le-Lac** est une municipalité de la région des Laurentides, située à environ 30 km au nord-ouest de Montréal.

Elle est délimitée par :
- le **Lac des Deux Montagnes** au sud
- la **Rivière des Mille-Îles** à l'est
- les municipalités de Saint-Eustache et Deux-Montagnes au nord et à l'est

### Secteurs prioritaires d'analyse

| Secteur | Description | Risque |
|---|---|---|
| Sud (22e Av. → lac) | Zone directement inondée en 2019 | Très élevé |
| Parc de la Frayère | Zone tampon naturelle en bordure du lac | Élevé |
| Parc Roland-Laliberté | Secteur résidentiel proche de l'eau | Élevé |
| Réseau d'avenues (17e–32e) | Infrastructure urbaine et électrique dense | Moyen à élevé |

### Paramètres techniques

- **Système de coordonnées :** EPSG:32198 (NAD83 / Québec Lambert)
- **Résolution spatiale :** 10 mètres (Sentinel-2) et 20 mètres (Sentinel-1)
- **Emprise :** Ensemble du territoire municipal de Sainte-Marthe-sur-le-Lac
- **Référence événement :** Crue et rupture de digue du 27 avril 2019

### Justification du choix

- Événement d'inondation réel, documenté et bien daté (2019)
- Données officielles disponibles sur le portail des zones inondables du MRNF
- Réseau électrique urbain dense → plusieurs infrastructures à cartographier
- Proximité avec Montréal → richesse des données ouvertes disponibles

---

## 4. Objectifs

### Objectif général

Développer une plateforme géospatiale intelligente capable de détecter automatiquement les zones inondées et d'identifier les infrastructures électriques vulnérables à Sainte-Marthe-sur-le-Lac, à partir d'images satellites et d'analyses SIG.

### Objectifs spécifiques

| # | Objectif | Livrable attendu |
|---|---|---|
| O1 | Cartographier les infrastructures électriques | Couche PostGIS vectorielle |
| O2 | Acquérir et prétraiter les images Sentinel | Rasters GeoTIFF reprojettés |
| O3 | Entraîner un modèle U-Net de détection des inondations | Modèle PyTorch exporté |
| O4 | Analyser les croisements spatiaux (zones inondées × réseau électrique) | Requêtes PostGIS |
| O5 | Développer une carte web interactive | Application Django + Leaflet |
| O6 | Publier les couches SIG via GeoServer | Services WMS/WFS |
| O7 | Conteneuriser l'application avec Docker | Fichiers docker-compose |
| O8 | Produire un rapport technique final | Document PDF |

---

## 5. Architecture technique

### Vue d'ensemble

```
┌─────────────────────────────────────────────────────────┐
│                    GEORISK SENTINEL                      │
├──────────────┬──────────────┬──────────────┬────────────┤
│   DONNÉES    │   TRAITEMENT │   STOCKAGE   │    WEB     │
│              │              │              │            │
│ Sentinel-1   │   Python     │  PostgreSQL  │  Django    │
│ Sentinel-2   │   Rasterio   │  + PostGIS   │  Leaflet   │
│ OSM (réseau  │   GeoPandas  │              │  GeoServer │
│  électrique) │   U-Net IA   │              │            │
│ MRNF zones   │              │              │            │
│ inondables   │              │              │            │
└──────────────┴──────────────┴──────────────┴────────────┘
                        │
               Docker Compose
                        │
                   GitHub (OSS)
```

### Composants principaux

#### Backend — Django

Django constitue le cœur de l'application. Il gère :
- les interfaces utilisateur (templates HTML)
- les requêtes à la base de données PostGIS via GeoDjango
- l'exécution des scripts de traitement Python
- la génération dynamique des cartes
- les alertes automatiques

#### Base de données — PostgreSQL + PostGIS

Stockage de toutes les données géospatiales vectorielles et des résultats d'analyse.

#### Traitement raster — Python (Rasterio + GeoPandas)

Prétraitement des images satellites, calcul des indices spectraux (NDWI, SAR ratio), export des zones inondées en vecteur.

#### Intelligence artificielle — U-Net (PyTorch)

Segmentation sémantique des surfaces d'eau à partir des images Sentinel.

#### Carte web — Leaflet

Visualisation interactive des couches géospatiales servies par GeoServer (WMS/WFS).

#### Conteneurisation — Docker + Docker Compose

Tous les services sont isolés dans des conteneurs pour garantir la reproductibilité.

---

## 6. Données utilisées

### Sources de données

| Couche | Source | Format | CRS |
|---|---|---|---|
| Zones inondables officielles | MRNF Québec (zonesinondables.mrnf.gouv.qc.ca) | SHP / GeoJSON | EPSG:32198 |
| Images radar SAR | Sentinel-1 (ESA Copernicus) | GeoTIFF | EPSG:4326 |
| Images optiques | Sentinel-2 (ESA Copernicus) | GeoTIFF | EPSG:4326 |
| Réseau électrique | OpenStreetMap (tags power=*) | GeoJSON | EPSG:4326 |
| Modèle numérique d'élévation | SRTM / Copernicus DEM | GeoTIFF | EPSG:32198 |
| Réseau hydrographique | Gouvernement du Québec (données ouvertes) | SHP | EPSG:32198 |
| Limites municipales | Données ouvertes du Québec | SHP | EPSG:32198 |
| Données météo historiques | Environnement Canada | CSV | — |

### Données satellites — détail

**Sentinel-1 (SAR)**
- Bandes : VV, VH (polarisation double)
- Résolution : 10 m (mode IW)
- Utilisation : détection des surfaces d'eau (insensible aux nuages)
- Période cible : avant/après l'événement d'avril 2019

**Sentinel-2 (optique)**
- Bandes utilisées : B3 (vert), B4 (rouge), B8 (NIR), B11 (SWIR)
- Résolution : 10 m (bandes B2-B4, B8)
- Utilisation : calcul NDWI, validation visuelle

### Portail des zones inondables — MRNF

Source principale pour les données de référence :
- Zones à risque 0-20 ans (risque élevé)
- Zones à risque 0-100 ans (risque modéré)
- Cotes de crues officielles
- Historique des événements

---

## 7. Modèle de données PostGIS

### Table `electric_network`

| Champ | Type | Description |
|---|---|---|
| id | SERIAL PRIMARY KEY | Identifiant unique |
| type | VARCHAR | pole, line, transformer, substation |
| voltage | INT | Tension (kV) |
| criticality | VARCHAR | low, medium, high |
| geom | GEOMETRY(GEOMETRY, 32198) | Géométrie (point ou ligne) |

### Table `flood_zones`

| Champ | Type | Description |
|---|---|---|
| id | SERIAL PRIMARY KEY | Identifiant unique |
| source | VARCHAR | MRNF, Sentinel, modèle IA |
| date_detection | DATE | Date de détection |
| recurrence | INT | Période de retour (20 ou 100 ans) |
| surface_ha | FLOAT | Surface en hectares |
| geom | GEOMETRY(POLYGON, 32198) | Polygone de la zone |

### Table `hydro_features`

| Champ | Type | Description |
|---|---|---|
| id | SERIAL PRIMARY KEY | Identifiant unique |
| type | VARCHAR | river, lake, ditch |
| nom | VARCHAR | Nom du cours d'eau |
| geom | GEOMETRY(GEOMETRY, 32198) | Géométrie |

### Table `risk_analysis`

| Champ | Type | Description |
|---|---|---|
| id | SERIAL PRIMARY KEY | Identifiant unique |
| infra_id | INT | Référence à electric_network |
| flood_zone_id | INT | Référence à flood_zones |
| niveau_risque | VARCHAR | faible, moyen, élevé, critique |
| distance_m | FLOAT | Distance à la zone inondée (m) |
| date_analyse | TIMESTAMP | Horodatage de l'analyse |

### Table `alertes`

| Champ | Type | Description |
|---|---|---|
| id | SERIAL PRIMARY KEY | Identifiant unique |
| niveau | VARCHAR | INFO, AVERTISSEMENT, CRITIQUE |
| message | TEXT | Contenu de l'alerte |
| infrastructure | INT | Référence à electric_network |
| date_alerte | TIMESTAMP | Horodatage |
| acquittee | BOOLEAN | Alerte traitée ou non |

---

## 8. Modèle IA — U-Net

### Architecture

Le modèle **U-Net** est retenu pour la segmentation sémantique des surfaces d'eau. Il est adapté à :
- la segmentation d'images satellites à faible nombre d'exemples
- la détection de frontières fines (berges, digues)
- l'entraînement sur données SAR et optiques

### Données d'entraînement

- Dataset **Sen1Floods11** (cloud-to-street, GitHub open source)
- Images Sentinel-1 SAR annotées pour la détection d'inondations

### Métriques d'évaluation

| Métrique | Description | Seuil cible |
|---|---|---|
| Accuracy | Précision globale de classification | > 90% |
| Recall | Capacité à détecter toutes les zones inondées | > 85% |
| IoU | Qualité de délimitation des polygones | > 0.75 |
| F1-score | Équilibre précision / rappel | > 0.85 |

---

## 9. Pipeline de traitement

```
[1] Acquisition
     ├── Téléchargement Sentinel-1 / Sentinel-2 (API Copernicus)
     ├── Téléchargement données OSM (osmium / overpy)
     └── Téléchargement zones inondables MRNF

[2] Prétraitement
     ├── Reprojection → EPSG:32198
     ├── Découpage sur emprise Sainte-Marthe-sur-le-Lac
     ├── Calibration radiométrique (SAR)
     └── Calcul NDWI (Sentinel-2)

[3] Détection IA
     ├── Inférence U-Net sur images SAR
     ├── Post-traitement (morphologie mathématique)
     └── Vectorisation → polygones zones inondées

[4] Analyse spatiale (PostGIS)
     ├── ST_Intersects (zones inondées × réseau électrique)
     ├── ST_Distance (distance infrastructure → zone inondée)
     ├── ST_Buffer (zones tampons 50 m, 100 m, 200 m)
     └── Calcul du niveau de risque multicritère

[5] Publication cartographique
     ├── Chargement dans PostGIS
     ├── Publication GeoServer (WMS / WFS)
     └── Mise à jour Django (carte Leaflet)

[6] Alertes
     └── Génération automatique si niveau_risque = élevé ou critique
```

---

## 10. Stack technologique

| Domaine | Technologie | Rôle |
|---|---|---|
| Langage principal | Python 3.11 | Traitement, IA, backend |
| Framework web | Django 4.2 + GeoDjango | Interface, API, carte |
| SIG bureau | QGIS 3.x | Visualisation, validation |
| Base de données | PostgreSQL 15 + PostGIS 3.3 | Stockage spatial |
| Carte web | Leaflet.js | Carte interactive |
| Serveur carto | GeoServer 2.24 | Publication WMS/WFS |
| IA / Deep Learning | PyTorch 2.x + U-Net | Détection inondations |
| Traitement raster | Rasterio + NumPy | Images satellites |
| Analyse spatiale | GeoPandas + Shapely | Vecteur SIG |
| Vision par ordinateur | OpenCV | Post-traitement images |
| Traitement images | scikit-image | Morphologie |
| Coordonnées | PyProj | Reprojection CRS |
| Conteneurisation | Docker + Docker Compose | Déploiement |
| Versionnement | Git + GitHub | Open source |

---

## 11. Structure du projet

```
georisk-sentinel/
│
├── docker-compose.yml          # Orchestration des services
├── README.md                   # Ce fichier
│
├── data/                       # Données brutes (ignorées par git)
│   ├── raw/                    # Images satellites originales
│   ├── processed/              # Données prétraitées
│   └── vectors/                # Couches vectorielles
│
├── src/
│   ├── acquisition/            # Scripts de téléchargement
│   │   ├── sentinel_download.py
│   │   └── osm_extract.py
│   │
│   ├── preprocessing/          # Prétraitement raster
│   │   ├── reproject.py
│   │   ├── clip.py
│   │   └── ndwi.py
│   │
│   ├── ai_model/               # Modèle U-Net
│   │   ├── model.py
│   │   ├── train.py
│   │   ├── predict.py
│   │   └── evaluate.py
│   │
│   ├── spatial_analysis/       # Analyse spatiale PostGIS
│   │   ├── risk_scoring.py
│   │   └── intersect.py
│   │
│   └── web/                    # Application Django
│       ├── manage.py
│       ├── georisk/            # App principale Django
│       │   ├── models.py       # Modèles GeoDjango
│       │   ├── views.py        # Vues et API
│       │   ├── urls.py
│       │   └── templates/
│       │       └── map.html    # Carte Leaflet
│       └── requirements.txt
│
├── sql/                        # Scripts PostGIS
│   ├── create_tables.sql
│   └── risk_analysis.sql
│
├── notebooks/                  # Jupyter notebooks d'exploration
│
└── docs/                       # Documentation
    ├── rapport_technique.pdf
    └── diagrammes/
```

---

## 12. Installation et déploiement

### Prérequis

- Docker Desktop installé
- Git installé
- Compte Copernicus (gratuit) pour l'accès aux images Sentinel

### Démarrage rapide

```bash
# Cloner le dépôt
git clone https://github.com/<votre-compte>/georisk-sentinel.git
cd georisk-sentinel

# Lancer tous les services
docker-compose up -d

# Vérifier que les conteneurs sont actifs
docker-compose ps
```

### Services démarrés par Docker Compose

| Service | Port | Description |
|---|---|---|
| Django (web) | 8000 | Interface principale + carte |
| PostgreSQL + PostGIS | 5432 | Base de données spatiale |
| GeoServer | 8080 | Publication cartographique WMS/WFS |
| pgAdmin (optionnel) | 5050 | Interface d'administration BD |

### Accès à l'application

```
Carte web :     http://localhost:8000
Admin Django :  http://localhost:8000/admin
GeoServer :     http://localhost:8080/geoserver
```

---

## 13. État d'avancement

| Phase | Tâche | Statut |
|---|---|---|
| Phase 1 | Recherche documentaire | ✅ Complété |
| Phase 1 | Choix des technologies | ✅ Complété |
| Phase 1 | Définition de la zone d'étude | ✅ Complété |
| Phase 2 | Acquisition données OSM | 🔄 En cours |
| Phase 2 | Acquisition images Sentinel | 🔄 En cours |
| Phase 2 | Acquisition données MRNF | 🔄 En cours |
| Phase 3 | Prétraitement raster | ⏳ À faire |
| Phase 3 | Configuration PostGIS | ⏳ À faire |
| Phase 4 | Entraînement modèle U-Net | ⏳ À faire |
| Phase 5 | Développement Django | ⏳ À faire |
| Phase 5 | Intégration Leaflet | ⏳ À faire |
| Phase 6 | Configuration Docker Compose | ⏳ À faire |
| Phase 6 | Tests et validation | ⏳ À faire |
| Phase 7 | Rapport technique final | ⏳ À faire |

---

## 14. Chronogramme

Voir le fichier [CHRONOGRAMME.md](CHRONOGRAMME.md) pour le détail des tâches et des dates.

---

## 15. Références

- Documentation Django / GeoDjango : https://docs.djangoproject.com
- Documentation PostGIS : https://postgis.net/documentation
- Documentation PyTorch : https://pytorch.org/docs
- Documentation Rasterio : https://rasterio.readthedocs.io
- Documentation GeoPandas : https://geopandas.org/docs
- Sentinel Hub (images satellites) : https://www.sentinel-hub.com
- Portail des zones inondables — MRNF Québec : https://zonesinondables.mrnf.gouv.qc.ca
- Données ouvertes du Québec : https://www.donneesquebec.ca
- OpenStreetMap : https://www.openstreetmap.org
- Sen1Floods11 (dataset IA) : https://github.com/cloudtostreet/Sen1Floods11
- Pytorch-UNet : https://github.com/milesial/Pytorch-UNet
- GeoServer : https://geoserver.org
- Leaflet : https://leafletjs.com

---

*Projet académique — GMQ580 Géomatique Informatique 2 — Été 2026*
