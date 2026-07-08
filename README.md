# GeoRisk Sentinel
## Optimisation de l'accessibilité aux bornes de recharge électrique à Montréal

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
7. [Bibliothèques principales (stack)](#7-bibliothèques-principales-stack)
8. [Livrables attendus](#8-livrables-attendus)
9. [État d'avancement](#9-état-davancement)
10. [Décisions méthodologiques](#10-décisions-méthodologiques)
11. [Installation et démarrage](#11-installation-et-démarrage)
12. [Références](#12-références)

---

## 1. Présentation du projet

**GeoRisk Sentinel** est une plateforme géospatiale développée dans le cadre du cours GMQ580 (Géomatique Informatique 2). Elle vise à **identifier les zones sous-desservies en bornes de recharge électrique à Montréal** et à proposer des emplacements optimaux pour de nouvelles installations.

Le projet combine :

- l'analyse spatiale (buffer 500 m, zones de couverture, gaps géographiques)
- les données ouvertes de la Ville de Montréal et de la STM
- une base de données spatiale PostGIS
- une carte web interactive mise à jour dynamiquement (Django + Leaflet)

L'environnement est entièrement conteneurisé avec Docker et le code est versionné sur GitHub.

---

## 2. Problématique

### Contexte

La transition vers les véhicules électriques s'accélère au Québec. Montréal compte plusieurs centaines de bornes de recharge publiques réparties inégalement sur son territoire. Certains arrondissements sont bien desservis, d'autres en manquent cruellement.

Sans analyse spatiale rigoureuse, il est impossible de savoir :
- quelles zones sont actuellement couvertes dans un rayon accessible à pied (500 m)
- quels arrondissements présentent les plus grands vides de couverture
- où installer en priorité de nouvelles bornes pour maximiser l'accessibilité

### Question de recherche

> Où faudrait-il installer de nouvelles bornes de recharge à Montréal afin de maximiser l'accessibilité des usagers tout en réduisant les zones sous-desservies ?

### Périmètre du projet (ce qui n'est PAS traité)

- Optimisation par algorithme (modèle de localisation-allocation)
- Données temps réel (disponibilité des bornes en direct)
- Analyse de la demande future (projections de ventes de VE)
- Réseau privé (stationnements d'immeubles, entreprises)

### Utilisateurs visés

- Ville de Montréal (planification urbaine)
- Arrondissements souhaitant investir en mobilité durable
- Citoyens cherchant une borne accessible
- Chercheurs en géomatique et mobilité

---

## 3. Zone d'étude

### Localisation

**Montréal** — métropole du Québec, territoire de l'agglomération incluant 19 arrondissements et les villes liées.

### Paramètres techniques

| Paramètre | Valeur |
|---|---|
| Système de coordonnées (stockage) | EPSG:4326 (WGS84) |
| Système de coordonnées (analyse buffer) | EPSG:32188 (NAD83 / MTM zone 8) |
| Rayon de couverture | 500 m autour de chaque borne |
| Échelle d'étude | Métropolitaine (arrondissement) |

### Justification du choix

- Données ouvertes disponibles et à jour (Données Québec, STM)
- Problématique concrète et d'actualité (transition énergétique)
- Résultats visualisables et interprétables sur un tableau de bord web
- Possibilité de mise à jour dynamique à chaque nouvelle installation

---

## 4. Données

> Toutes les données utilisées dans ce projet sont **disponibles directement dans ce dépôt** dans le dossier [`data/vectors/`](data/vectors/). Les fichiers GeoJSON sont visualisables interactivement sur GitHub (carte automatique).

### Données disponibles dans le dépôt

| Couche | Fichier (cliquable) | Format | CRS | Licence | Mise à jour |
|---|---|---|---|---|---|
| Bornes de recharge publiques | [`data/vectors/bornes_recharge_montreal.geojson`](data/vectors/bornes_recharge_montreal.geojson) | GeoJSON | WGS84 | CC-BY 4.0 | Continue |
| Statistiques d'utilisation 2025 | [`data/vectors/chargeurs_statistiques_2025.csv`](data/vectors/chargeurs_statistiques_2025.csv) | CSV | — | CC-BY 4.0 | Annuelle |
| Arrondissements de Montréal | [`data/vectors/arrondissements_montreal.geojson`](data/vectors/arrondissements_montreal.geojson) | GeoJSON | WGS84 | CC-BY 4.0 | 2026-06-30 |
| Arrêts et stations STM (bus + métro) | [`data/vectors/stm_sig/`](data/vectors/stm_sig/) | SHP | NAD83 MTM8 | CC-BY 4.0 | Trimestrielle |

### Contenu des fichiers

**`bornes_recharge_montreal.geojson`** — localisation de toutes les bornes de recharge publiques de Montréal (coordonnées GPS, adresse, type de borne, arrondissement)

**`chargeurs_statistiques_2025.csv`** — statistiques mensuelles par borne : nombre de recharges, kWh consommés, taux d'utilisation (~79-80%), moyenne d'usagers/jour

**`arrondissements_montreal.geojson`** — polygones des 19 arrondissements et villes liées de l'agglomération de Montréal (WGS84, source officielle Ville de Montréal)

**`stm_sig/stm_arrets_sig.shp`** — 8 789 arrêts STM dont les stations de métro (identifiées par `stop_url` contenant "metro"), projection NAD83 MTM8

### Notes techniques

- Les données STM sont en **NAD83 / MTM zone 8** (EPSG:32188) → reprojetées en WGS84 lors de l'import PostGIS
- Le script [`src/preprocessing/import_postgis.py`](src/preprocessing/import_postgis.py) gère l'import automatique de toutes les couches

### Citations obligatoires (CC-BY 4.0)

- Ville de Montréal. *Bornes de recharge publiques*, Données Québec. Consulté le 7 juillet 2026.
- Ville de Montréal. *Limites administratives de l'agglomération de Montréal*, Données Québec, mis à jour le 30 juin 2026.
- SOCIÉTÉ DE TRANSPORT DE MONTRÉAL. *Tracés des lignes de bus et de métro*, Données Québec, 2016, mis à jour le 06 juillet 2026.

---

## 5. Modèle de données

Le projet utilise PostgreSQL 15 avec l'extension PostGIS 3.3.

### Table `bornes_recharge`

| Champ | Type | Description |
|---|---|---|
| id | SERIAL PRIMARY KEY | Identifiant unique |
| nom | VARCHAR(200) | Nom de la borne |
| type | VARCHAR(50) | Niveau 2, Niveau 3 (DC rapide) |
| arrondissement | VARCHAR(100) | Arrondissement de Montréal |
| nb_prises | INT | Nombre de prises disponibles |
| geom | GEOMETRY(POINT, 4326) | Localisation WGS84 |

### Table `zones_couverture`

| Champ | Type | Description |
|---|---|---|
| id | SERIAL PRIMARY KEY | Identifiant unique |
| borne_id | INT | Référence à bornes_recharge |
| rayon_m | INT | Rayon du buffer (défaut : 500 m) |
| geom | GEOMETRY(POLYGON, 4326) | Zone de couverture |

### Table `arrondissements`

| Champ | Type | Description |
|---|---|---|
| id | SERIAL PRIMARY KEY | Identifiant unique |
| nom | VARCHAR(100) | Nom de l'arrondissement |
| nb_bornes | INT | Nombre de bornes (calculé) |
| pct_couverture | FLOAT | % du territoire couvert à 500 m |
| geom | GEOMETRY(MULTIPOLYGON, 4326) | Polygone arrondissement |

### Table `stations_metro`

| Champ | Type | Description |
|---|---|---|
| id | SERIAL PRIMARY KEY | Identifiant unique |
| nom | VARCHAR(100) | Nom de la station |
| ligne | VARCHAR(10) | Ligne de métro (verte, orange, jaune, bleue) |
| geom | GEOMETRY(POINT, 4326) | Localisation WGS84 |

---

## 6. Pipeline de traitement et Architecture

### Pipeline complet

```
[Phase 1 — Acquisition]
    ├── bornes_recharge_montreal.geojson  → Données Québec (Ville de Montréal)
    ├── arrondissements_montreal.geojson  → Données Québec (Ville de Montréal)
    ├── chargeurs_statistiques_2025.csv   → Données Québec (Ville de Montréal)
    └── stm_traces_arrets.zip             → Données Québec (STM)

[Phase 2 — Prétraitement]
    ├── Reprojection STM : NAD83 MTM8 → WGS84 (EPSG:4326)
    └── import_postgis.py
          ├── bornes_recharge_montreal.geojson → table bornes_recharge
          ├── arrondissements_montreal.geojson → table arrondissements
          └── stations métro (STM SHP filtré)  → table stations_metro

[Phase 3 — Analyse spatiale (PostGIS)]
    ├── ST_Buffer(500m) → zones de couverture par borne
    ├── ST_Union        → zone couverte totale par arrondissement
    ├── ST_Difference   → zones NON couvertes (sous-desservies)
    └── Calcul % couverture par arrondissement

[Phase 4 — Application web (Django + Leaflet)]
    ├── API REST : /api/bornes/, /api/couverture/, /api/arrondissements/
    ├── Carte Leaflet interactive :
    │     ├── Couche 1 : bornes existantes (points verts)
    │     ├── Couche 2 : zones couvertes à 500m (bleu transparent)
    │     ├── Couche 3 : zones sous-desservies (rouge)
    │     └── Couche 4 : stations de métro (icônes M)
    ├── Panneau stats par arrondissement (% couverture, nb bornes)
    └── Django Admin : ajout de nouvelles bornes → mise à jour automatique
```

### Architecture des services Docker

```
┌─────────────────────────────────────────────────────────────────┐
│                    GEORISK SENTINEL                              │
├──────────────────┬──────────────────┬──────────────────────────┤
│  georisk_postgis │ georisk_pgadmin  │    georisk_web            │
│  (port 5433)     │ (port 5050)      │    (port 8000)            │
│                  │                  │                            │
│  PostGIS 15.3    │ pgAdmin 4        │ Django 5.2 + GeoDjango    │
│  ─────────────── │ ─────────────── │ ──────────────────────    │
│  bornes_recharge │ Interface SQL    │ /api/bornes/              │
│  zones_couverture│ graphique        │ /api/couverture/          │
│  arrondissements │                  │ /api/arrondissements/     │
│  stations_metro  │                  │ /  → carte Leaflet        │
└──────────────────┴──────────────────┴──────────────────────────┘
```

---

## 7. Bibliothèques principales (stack)

| Domaine | Technologie | Version | Rôle |
|---|---|---|---|
| Langage principal | Python | 3.10 | Traitement et backend |
| Framework web | Django + GeoDjango | 5.2 LTS | Interface, API REST, requêtes spatiales |
| API REST | Django REST Framework | 3.17 | Sérialisation JSON/GeoJSON |
| Base de données | PostgreSQL + PostGIS | 15 + 3.3 | Stockage spatial (Docker) |
| Carte web | Leaflet.js | 1.9 | Carte interactive |
| Analyse spatiale | GeoPandas | 0.14 | Import et traitement vecteur |
| Coordonnées | PyProj | 3.7 | Reprojection CRS |
| Conteneurisation | Docker + Compose | — | Déploiement reproductible |
| Versionnement | Git + GitHub | — | Open source |

---

## 8. Livrables attendus

| Livrable | Fichier dans le repo | Statut |
|---|---|---|
| Données bornes de recharge | [`data/vectors/bornes_recharge_montreal.geojson`](data/vectors/bornes_recharge_montreal.geojson) | ✅ Dans le repo |
| Données arrondissements | [`data/vectors/arrondissements_montreal.geojson`](data/vectors/arrondissements_montreal.geojson) | ✅ Dans le repo |
| Données STM (métro + bus) | [`data/vectors/stm_sig/`](data/vectors/stm_sig/) | ✅ Dans le repo |
| Statistiques utilisation 2025 | [`data/vectors/chargeurs_statistiques_2025.csv`](data/vectors/chargeurs_statistiques_2025.csv) | ✅ Dans le repo |
| Script import PostGIS | [`src/preprocessing/import_postgis.py`](src/preprocessing/import_postgis.py) | ✅ Écrit |
| Script analyse buffer 500m | [`src/preprocessing/buffer_analysis.py`](src/preprocessing/buffer_analysis.py) | ✅ Écrit |
| Script zones sous-desservies | [`src/preprocessing/gap_analysis.py`](src/preprocessing/gap_analysis.py) | ✅ Écrit |
| Modèles Django (4 tables) | [`src/web/risk_map/models.py`](src/web/risk_map/models.py) | ✅ Écrit |
| API REST GeoJSON | [`src/web/risk_map/views.py`](src/web/risk_map/views.py) | ✅ Écrit |
| Carte Leaflet interactive | [`src/web/templates/risk_map/map.html`](src/web/templates/risk_map/map.html) | ✅ Écrite |
| Docker Compose (PostGIS + pgAdmin + Django) | [`docker-compose.yml`](docker-compose.yml) | ✅ Configuré |
| Rapport technique final | [`RAPPORT_FINAL.md`](RAPPORT_FINAL.md) | ✅ Rédigé |
| Présentation orale | [`PRESENTATION_ORALE.md`](PRESENTATION_ORALE.md) | ✅ Rédigée |

---

## 9. État d'avancement

| Phase | Tâche | Statut | Date |
|---|---|---|---|
| Phase 1 | Définition du sujet (bornes de recharge Montréal) | ✅ Complété | 7 juillet 2026 |
| Phase 1 | Validation du sujet par le professeur | ✅ Complété | 7 juillet 2026 |
| Phase 2 | Téléchargement bornes de recharge (GeoJSON) | ✅ Complété | 7 juillet 2026 |
| Phase 2 | Téléchargement statistiques utilisation 2025 (CSV) | ✅ Complété | 7 juillet 2026 |
| Phase 2 | Téléchargement arrondissements Montréal WGS84 (GeoJSON) | ✅ Complété | 7 juillet 2026 |
| Phase 2 | Téléchargement tracés STM bus+métro (SHP) | ✅ Complété | 7 juillet 2026 |
| Phase 2 | Documentation des sources (SOURCES.md) | ✅ Complété | 7 juillet 2026 |
| Phase 3 | Reprojection STM NAD83→WGS84 (dans import_postgis.py) | ✅ Script écrit | 7 juillet 2026 |
| Phase 3 | Script import PostGIS — toutes les couches | ✅ Script écrit | 7 juillet 2026 |
| Phase 3 | Création tables SQL (bornes, arrondissements, métro, couverture) | ✅ SQL écrit | 7 juillet 2026 |
| Phase 3 | Démarrage Docker + import données réelles en BD | ✅ Complété | 7 juillet 2026 |
| Phase 4 | Script analyse buffer 500m (PostGIS) | ✅ Complété | 7 juillet 2026 |
| Phase 4 | Script zones sous-desservies (gap analysis + export GeoJSON) | ✅ Complété | 7 juillet 2026 |
| Phase 4 | Exécution de l'analyse sur les données réelles | ✅ Complété | 7 juillet 2026 |
| Phase 5 | Modèles Django (4 tables : bornes, couverture, arrondissements, métro) | ✅ Complété | 7 juillet 2026 |
| Phase 5 | API REST GeoJSON (bornes, couverture, arrondissements, métro) | ✅ Complété | 7 juillet 2026 |
| Phase 5 | Dashboard dark theme (choroplèthe, EN DIRECT, slider simulation) | ✅ Complété | 7 juillet 2026 |
| Phase 5 | Mise à jour automatique depuis Données Québec (APScheduler) | ✅ Complété | 7 juillet 2026 |
| Phase 5 | Tests et validation avec données réelles en BD | ✅ Validé (2 412 bornes, 34 arrond.) | 7 juillet 2026 |
| Phase 6 | Push GitHub complet (code + données) | ✅ Complété | 7 juillet 2026 |
| Phase 6 | Rapport technique final | ✅ Rédigé | 7 juillet 2026 |
| Phase 6 | Présentation orale | ✅ Rédigée | 7 juillet 2026 |

---

## 10. Décisions méthodologiques

| Décision | Justification |
|---|---|
| Montréal (pas Sainte-Marthe-sur-le-Lac) | Réseau électrique local non disponible en open data — pivot vers sujet avec données ouvertes complètes |
| Buffer 500 m | Distance de marche acceptable pour un usager (norme urbanisme actif) |
| WGS84 pour stockage | Compatible Leaflet nativement, évite les conversions à la volée |
| MTM8 pour les calculs de buffer | Projection métrique locale = distances en mètres précises |
| Django Admin pour les mises à jour | Permet d'ajouter une borne sans toucher au code → dashboard se met à jour automatiquement |
| GeoJSON pour bornes + arrondissements | Format web natif, pas de conversion nécessaire |
| STM SHP (pas QuickOSM) | Données officielles STM plus fiables que l'extraction OSM manuelle |
| Port 5433 (pas 5432) | Conflit avec PostgreSQL local déjà installé |

---

## 11. Installation et démarrage

### Prérequis

- Docker Desktop (Engine en cours d'exécution)
- Python 3.10 avec venv
- Git

### Démarrage rapide

```bash
# 1. Cloner le dépôt
git clone https://github.com/modou5604501/projet_Session.git
cd projet_Session

# 2. Démarrer PostGIS + pgAdmin
docker-compose up -d postgis pgadmin

# 3. Installer les dépendances Python
python -m venv venv
pip install -r requirements.txt

# 4. Importer les données
python src/preprocessing/import_postgis.py

# 5. Lancer le serveur Django
cd src/web
python manage.py runserver 0.0.0.0:8000
```

**OU — Script tout-en-un (Windows) :**
```
demarrer.bat
```

### Services et ports

| Service | Port | Description |
|---|---|---|
| PostGIS | 5433 | Base de données spatiale |
| pgAdmin | 5050 | Interface d'administration BD |
| Django | 8000 | Application web + API |

### Accès

```
Carte interactive :        http://localhost:8000
API bornes :               http://localhost:8000/api/bornes/
API zones couverture :     http://localhost:8000/api/couverture/
API arrondissements :      http://localhost:8000/api/arrondissements/
pgAdmin :                  http://localhost:5050
```

---

## 12. Références

- Ville de Montréal — Données ouvertes : https://donnees.montreal.ca
- Données Québec : https://www.donneesquebec.ca
- STM — Données ouvertes : https://www.stm.info/fr/a-propos/developers
- Documentation Django / GeoDjango : https://docs.djangoproject.com
- Documentation PostGIS : https://postgis.net/documentation
- Documentation GeoPandas : https://geopandas.org/docs
- Leaflet.js : https://leafletjs.com

---

*Projet académique — GMQ580 Géomatique Informatique 2 — Été 2026 — Université de Sherbrooke*
