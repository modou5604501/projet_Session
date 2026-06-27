# Diagrammes Mermaid — GeoRisk Sentinel
## Pour utilisation dans Draw.io

**Comment utiliser :**
1. Ouvrir [app.diagrams.net](https://app.diagrams.net)
2. Menu **Extras** → **Edit Diagram**
3. Coller le code du diagramme voulu → cliquer **OK**

---

## Diagramme 1 — Pipeline de traitement complet (flowchart)

```mermaid
flowchart TD
    subgraph ACQ["PHASE 1 — ACQUISITION DES DONNÉES"]
        A1[("Sentinel-1 SAR\n4 scènes SAFE.zip\nESA / CDSE\n08-avr, 20-avr, 02-mai, 14-mai 2019")]
        A2[("DEM Copernicus GLO-30\n43.5 Mo\nAWS S3 open data")]
        A3[("Réseau électrique OSM\n60 entités GeoJSON\nOverpass Turbo")]
        A4[("Zones inondées MRNF\n277 Mo GPKG\nDonnées Québec 2017/2019")]
    end

    subgraph PRE["PHASE 2 — PRÉTRAITEMENT"]
        B1["preprocess_sentinel1.py\n• Extraction SAFE.zip\n• Lecture 210 GCPs / scène\n• Reprojection EPSG:32198\n• Calibration dB : 20xlog10(DN/65535)\n→ 4 x GeoTIFF 1661x1212 @ 10m"]
        B2["preprocess_dem.py\n• Clip BBOX Sainte-Marthe\n• Reprojection EPSG:32198\n• Calcul pente et aspect\n→ 3 x GeoTIFF 554x484 @ 30m"]
        B3["import_postgis.py\n• OSM → electric_network (60 entités)\n• MRNF clip + force_2d → flood_zones (6)\n• EPSG:32198, TRUNCATE CASCADE"]
    end

    subgraph DET["PHASE 3 — DÉTECTION D'INONDATIONS"]
        C1["flood_detection.py\n\nMéthode 1 — Percentile\n• 12e percentile par image\n• Masque eau permanent\n• 2 416 ha eau permanente\n\nMéthode 2 — Change Detection\n• after_dB - before_dB\n• Seuil : -4 dB\n• 3 233 ha nouvellement inondés\n• flood_change.tif"]
    end

    subgraph SIG["PHASE 4 — ANALYSE SPATIALE POSTGIS"]
        D1[("PostGIS 15 / Docker\nport hôte 5433\n4 tables spatiales\nEPSG:32198")]
        D2["GeoDjango SQL\n• ST_Intersects → risque critique\n• ST_Buffer 500m → risque élevé\n• ST_Distance → distance en m\n• risk_analysis remplie"]
    end

    subgraph WEB["PHASE 5 — APPLICATION WEB"]
        E1["Django 5.2 + GeoDjango\nsrc/web/\nPort 8000"]
        E2["API REST DRF\n/api/electric/\n/api/floods/\n/api/risk-summary/\n/api/infra/pk/risk/"]
        E3["Carte Leaflet 1.9\nFond OSM + Esri Satellite\nRéseau élec. (bleu)\nZones inondées (rouge)\nInfo au clic\nSidebar résumé"]
    end

    A1 --> B1
    A2 --> B2
    A3 --> B3
    A4 --> B3
    B1 --> C1
    B3 --> D1
    B2 --> D2
    C1 --> D1
    D1 --> D2
    D2 --> D1
    D1 --> E1
    E1 --> E2
    E2 --> E3
```

---

## Diagramme 2 — Architecture Docker et services

```mermaid
flowchart LR
    subgraph HOST["Machine hôte (Windows 11)"]
        subgraph DC["docker-compose.yml"]
            PG["georisk_postgis\nImage: postgis/postgis:15-3.3\nPort: 5433:5432\nVolume: postgis_data\n\n• DB: georisk\n• User: georisk_user\n• 4 tables spatiales"]
            PGA["georisk_pgadmin\nImage: dpage/pgadmin4\nPort: 5050:80\n\n• Interface admin BD\n• Mot de passe: georisk2019"]
            WEB["georisk_web\nImage: python:3.10-slim\nPort: 8000:8000\n\n• Django 5.2 + GeoDjango\n• DRF + rest_framework_gis"]
        end
        BAT["demarrer.bat\n• Set PROJ_LIB/PROJ_DATA\n• docker-compose up -d\n• python manage.py runserver"]
        ENV[".env  GITIGNORE\n• CDSE_USERNAME\n• CDSE_PASSWORD"]
    end

    subgraph USER["Navigateur"]
        UI1["localhost:8000\nCarte Leaflet"]
        UI2["localhost:5050\npgAdmin 4"]
    end

    WEB -- depends_on healthy --> PG
    PGA -- depends_on --> PG
    BAT --> DC
    ENV -. variables .-> WEB
    WEB --> UI1
    PGA --> UI2
```

---

## Diagramme 3 — Méthode change detection SAR

```mermaid
flowchart TD
    subgraph AVANT["AVANT l'inondation"]
        S1["S1A_IW_GRDH_1SDH_20190420\nPolarisation HH\nDate : 20 avril 2019\n7 jours avant la rupture"]
        CAL1["Calibration dB\n20 x log10(DN / 65535)\nValeurs entre -50 dB et -20 dB"]
    end

    subgraph APRES["APRES l'inondation"]
        S2["S1A_IW_GRDH_1SDV_20190502\nPolarisation VV + VH\nDate : 2 mai 2019\n5 jours apres la rupture"]
        CAL2["Calibration dB\n20 x log10(DN / 65535)\nValeurs entre -50 dB et -20 dB"]
    end

    DIFF["Carte de différence\ndiff = after_dB - before_dB\nSignal radar chute sur l'eau\nréflexion spéculaire"]

    SEUIL{"Seuil : diff < -4 dB ?"}

    FLOODED["Pixel = INONDÉ\nNouvellement couvert d'eau\nvaleur = 1 dans flood_change.tif"]
    DRY["Pixel = SEC\nPas de changement\nvaleur = 0 dans flood_change.tif"]

    RESULT["Résultats\n• 2 416 ha eau permanente\n• 3 233 ha nouvellement inondés\n• Fichier : flood_change.tif"]

    S1 --> CAL1
    S2 --> CAL2
    CAL1 --> DIFF
    CAL2 --> DIFF
    DIFF --> SEUIL
    SEUIL -- Oui --> FLOODED
    SEUIL -- Non --> DRY
    FLOODED --> RESULT
    DRY --> RESULT
```

---

## Diagramme 4 — Analyse des risques et API Django

```mermaid
flowchart LR
    DB1[("electric_network\n60 entités OSM")] --> API1["GET /api/electric/\nGeoJSON"] --> LAY1["Couche carte\nRéseau électrique\nlignes bleues"]
    DB2[("flood_zones\n6 polygones MRNF")] --> API2["GET /api/floods/\nGeoJSON"] --> LAY2["Couche carte\nZones inondées\npolygones rouges"]
    DB1 --> API3["GET /api/risk-summary/\nST_Union + ST_Buffer\ncompte par niveau"] --> SIDE["Sidebar\nRésumé des risques"]
    DB2 --> API3
    DB1 --> API4["GET /api/infra/pk/risk/\nST_Distance\nzone la plus proche"] --> POP["Info au clic\nType, tension\nDistance en m"]
    DB2 --> API4
    DB3[("alertes\nInfo/Warning/Critical")] --> ADM["Django Admin /admin/\nGestion des alertes\nMarquer acquittée"]

    LAY1 --> MAP["Carte Leaflet\nlocalhost:8000"]
    LAY2 --> MAP
    SIDE --> MAP
    POP --> MAP
```

---

## Diagramme 5 — Structure des fichiers du projet

```mermaid
flowchart TD
    ROOT["GMQ580_projetsession/"]
    DC["docker-compose.yml\nPostGIS 5433, pgAdmin 5050, Django 8000"]
    ENV[".env   GITIGNORE\ncredentials CDSE"]
    BAT["demarrer.bat\nscript démarrage Windows"]
    REQ["requirements.txt\nDjango 5.2, rasterio, geopandas..."]
    CI[".github/workflows/ci.yml\nflake8 + django check"]
    SQL["sql/init.sql\nCREATE TABLE + PostGIS extensions"]
    DATA["data/\n├── raw/\n│   ├── dem/  43.5 Mo\n│   ├── sentinel1/  4 SAFE.zip\n│   └── vectors/  OSM + MRNF\n└── processed/\n    ├── dem_sainte_marthe_32198.tif\n    ├── sentinel1/  4 x 16.1 Mo\n    └── flood_masks/flood_change.tif"]
    SRC["src/"]
    ACQ["src/acquisition/\n├── download_dem.py\n└── download_sentinel1.py"]
    PRE["src/preprocessing/\n├── preprocess_dem.py\n├── preprocess_sentinel1.py\n└── import_postgis.py"]
    AI["src/ai_model/\n└── flood_detection.py"]
    WEB["src/web/\n├── manage.py\n├── Dockerfile\n├── georisk_web/\n│   ├── settings.py\n│   └── urls.py\n└── risk_map/\n    ├── models.py\n    ├── serializers.py\n    ├── views.py\n    ├── admin.py\n    └── templates/risk_map/map.html"]

    ROOT --> DC
    ROOT --> ENV
    ROOT --> BAT
    ROOT --> REQ
    ROOT --> CI
    ROOT --> SQL
    ROOT --> DATA
    ROOT --> SRC
    SRC --> ACQ
    SRC --> PRE
    SRC --> AI
    SRC --> WEB
```

---

*GeoRisk Sentinel — GMQ580 Géomatique Informatique 2 — Été 2026 — Université de Sherbrooke*
*Equipe : Modou Khabane Mbaye & Rahina Djelila Sarah Bagre*
