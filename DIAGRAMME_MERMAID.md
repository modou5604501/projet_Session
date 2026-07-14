# Diagrammes Mermaid — GeoCharge Montréal
## Pour utilisation dans Draw.io / GitHub

**Comment utiliser dans Draw.io :**
1. Ouvrir [app.diagrams.net](https://app.diagrams.net)
2. Menu **Extras** → **Edit Diagram**
3. Coller le code du diagramme voulu → cliquer **OK**

> Ces diagrammes sont aussi rendus automatiquement dans GitHub (Mermaid natif).

---

## Diagramme 1 — Pipeline de traitement complet

```mermaid
flowchart TD
    subgraph ACQ["PHASE 1 — ACQUISITION DES DONNÉES OUVERTES (Données Québec · CC-BY 4.0)"]
        A1[("Bornes de recharge\n2 412 bornes GeoJSON\nVille de Montréal")]
        A2[("Arrondissements\n34 polygones GeoJSON\nVille de Montréal")]
        A3[("Stations de métro\nShapefile STM\n68 stations")]
        A4[("Statistiques 2025\nCSV utilisation bornes")]
        A5[("Parcs et espaces verts\n1 541 parcs GeoJSON\nVille de Montréal")]
        A6[("Établissements alimentaires\n3 010 épiceries GeoJSON\nVille de Montréal")]
    end

    subgraph PRE["PHASE 2 — PRÉTRAITEMENT (import_postgis.py)"]
        B1["Lecture GeoJSON/SHP\nGeoPandas + Shapely\nValidation géométries"]
        B2["Reprojection STM\nNAD83 MTM8 → WGS84\nPyProj / GeoPandas"]
        B3["Import PostGIS\nTRUNCATE + append\n6 tables spatiales"]
    end

    subgraph ANA["PHASE 3 — ANALYSE SPATIALE PostGIS (EPSG:32188)"]
        C1["buffer_analysis.py\nST_Buffer(geom, 500m)\n→ zones_couverture"]
        C2["ST_Area(ST_Intersection)\n/ ST_Area(arrondissement)\n→ pct_couverture %"]
        C3["gap_analysis.py\nST_Difference(arrond, union_buffers)\n→ zones_sous_desservies.geojson"]
    end

    subgraph WEB["PHASE 4 — APPLICATION WEB Django 5.2 + Leaflet.js"]
        D1["API REST · 16 endpoints GeoJSON\nDjango REST Framework + DRF-GIS"]
        D2["Dashboard Leaflet\nCARTO Dark Matter\nChoroplèthe · Couches · Requêtes"]
        D3["Panel gestionnaire\nParcs · Épiceries · Score priorité\nCorrélation démographique"]
        D4["APScheduler hebdo\nAPI CKAN Données Québec\nPWA tablette"]
    end

    A1 & A2 & A4 & A5 & A6 --> B1
    A3 --> B2
    B1 & B2 --> B3
    B3 --> C1 --> C2 --> C3
    B3 & C1 & C2 & C3 --> D1
    D1 --> D2 & D3 & D4
```

---

## Diagramme 2 — Architecture technique

```mermaid
flowchart LR
    subgraph HOST["Machine locale (Windows 11) / Railway (Linux)"]
        subgraph DC["docker-compose.yml"]
            PG["georisk_postgis\nPostGIS 15-3.3\nPort 5433:5432\n\n• bornes_recharge (2 412)\n• zones_couverture (2 412)\n• arrondissements (34)\n• stations_metro (68)"]
            PGA["georisk_pgadmin\ndpage/pgadmin4\nPort 5050:80\n\nInterface admin BD"]
            WEB["georisk_web\npython:3.10-slim\nPort 8000:8000\n\nDjango 5.2 + Gunicorn"]
        end
        PRE["Prétraitement\nimport_postgis.py\nbuffer_analysis.py\ngap_analysis.py\nrefresh_data.py"]
    end

    subgraph CLIENT["Navigateur / Tablette (PWA)"]
        MAP["localhost:8000\nDashboard Leaflet\nDark theme\nCARTO Dark Matter"]
        ADMIN["localhost:5050\npgAdmin 4\nInspection BD"]
        PWA["App PWA\nInstallable\niPad / Android\nHors-ligne partiel"]
    end

    subgraph EXT["Sources externes"]
        CKAN["API CKAN\ndonnees.montreal.ca\nMise à jour auto\nhebdomadaire"]
    end

    WEB -- depends_on healthy --> PG
    PGA -- depends_on --> PG
    PRE --> PG
    CKAN --> PRE
    WEB --> MAP
    PGA --> ADMIN
    MAP --> PWA
```

---

## Diagramme 3 — Modèle de données PostGIS

```mermaid
erDiagram
    BORNES_RECHARGE {
        bigint id PK
        varchar nom
        varchar type
        varchar arrondissement
        int nb_prises
        geometry geom "POINT EPSG:4326"
    }
    ZONES_COUVERTURE {
        bigint id PK
        bigint borne_id FK
        int rayon_m
        geometry geom "POLYGON EPSG:4326"
    }
    ARRONDISSEMENTS {
        bigint id PK
        varchar nom
        int nb_bornes
        float pct_couverture
        geometry geom "MULTIPOLYGON EPSG:4326"
    }
    STATIONS_METRO {
        bigint id PK
        varchar nom
        varchar ligne
        geometry geom "POINT EPSG:4326"
    }
    PARCS {
        bigint id PK
        varchar nom
        float superficie_ha
        varchar typo
        geometry geom "POINT EPSG:4326"
    }
    EPICERIES {
        bigint id PK
        varchar nom
        varchar type
        varchar adresse
        geometry geom "POINT EPSG:4326"
    }

    BORNES_RECHARGE ||--o{ ZONES_COUVERTURE : "1 borne → 1 buffer 500m"
    ARRONDISSEMENTS ||--o{ BORNES_RECHARGE : "contient"
    PARCS }o--o{ BORNES_RECHARGE : "ST_DWithin 500m"
    EPICERIES }o--o{ BORNES_RECHARGE : "KNN / ST_DWithin"
```

---

## Diagramme 4 — Workflow de mise à jour automatique

```mermaid
flowchart TD
    TRIGGER{"Déclencheur"}

    TRIGGER -- "Hebdomadaire\n(APScheduler)" --> SCHED["scheduler.py\nBackgroundScheduler\nweeks=1"]
    TRIGGER -- "Manuel\n(bouton dashboard)" --> BTN["POST /api/refresh/\ntrigger_refresh()"]

    SCHED --> REFRESH["refresh_data.py\nrun_refresh()"]
    BTN   --> REFRESH

    REFRESH --> CKAN["API CKAN\ndonnees.montreal.ca\npackage_show?id=bornes-de-recharge"]
    CKAN -- "URL download" --> DL["Téléchargement GeoJSON\n(fallback fichier local)"]
    DL --> IMP["import_postgis.py\nTRUNCATE bornes_recharge CASCADE\n+ import 2 412 bornes"]
    IMP --> BUF["buffer_analysis.py\nST_Buffer 500m\n+ MAJ pct_couverture"]
    BUF --> DONE["✅ Données à jour\nTemps écoulé : ~30s"]

    BTN --> POLL["pollRefreshStatus()\ntoutes les 3 secondes"]
    POLL --> STATUS["GET /api/refresh/status/\n{running: false, bornes: 2412}"]
    STATUS --> UI["Dashboard rechargé\n✅ 2412 bornes mises à jour"]
```

---

## Diagramme 5 — API REST et dashboard

```mermaid
flowchart LR
    DB1[("bornes_recharge\n2 412 points")] --> E1["GET /api/bornes/\nGeoJSON FeatureCollection"] --> L1["Points cyan\nrayon 4px\nclic → info"]
    DB2[("zones_couverture\n2 412 polygones")] --> E2["GET /api/couverture/\nGeoJSON FeatureCollection"] --> L2["Zones bleues\nopacité 0.1\n500m de rayon"]
    DB3[("arrondissements\n34 polygones")] --> E3["GET /api/arrondissements/\nGeoJSON FeatureCollection"] --> L3["Choroplèthe\nvert/jaune/orange/rouge\n% couverture"]
    DB4[("stations_metro\n68 points")] --> E4["GET /api/metro/\nGeoJSON FeatureCollection"] --> L4["Points orange\ntooltip nom station"]
    DB3 --> E5["GET /api/coverage-summary/\nJSON stats globales"] --> SIDE["Barre de stats\nBornes | Critiques\nCouverture | Horloge"]

    L1 --> MAP["Dashboard Leaflet\nCARTO Dark Matter\nEN DIRECT"]
    L2 --> MAP
    L3 --> MAP
    L4 --> MAP
    SIDE --> MAP
```

---

*GeoCharge Montréal — GMQ580 Géomatique Informatique 2 — Été 2026 — Université de Sherbrooke*
*Équipe : Modou Khabane Mbaye & Rahina Djelila Sarah Bagre*
