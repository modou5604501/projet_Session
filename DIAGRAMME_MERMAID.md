# Diagramme Mermaid — GeoRisk Sentinel

## Comment utiliser ce diagramme dans Draw.io

1. Ouvrir **Draw.io** (app.diagrams.net)
2. Menu **Extras** → **Edit Diagram**
3. Copier-coller le code ci-dessous
4. Cliquer **OK**
5. OU : Menu **Organiser** → **Insérer** → **Mermaid** → coller et confirmer

---

## Diagramme 1 — Pipeline de traitement complet

```mermaid
flowchart TD

    %% === SOURCES DE DONNÉES ===
    subgraph SOURCES["🗂️ SOURCES DE DONNÉES"]
        S1["🛰️ Sentinel-1 SAR\n(images radar)"]
        S2["🛰️ Sentinel-2 Optique\n(images multibandes)"]
        S3["⚡ OpenStreetMap\n(réseau électrique)"]
        S4["🌊 MRNF Québec\n(zones inondables)"]
        S5["🗺️ DEM Copernicus\n(modèle d'élévation)"]
    end

    %% === ACQUISITION ===
    subgraph ACQ["📥 ACQUISITION (Python)"]
        A1["Script\nsentinel_download.py"]
        A2["Script\nosm_extract.py"]
    end

    %% === PRÉTRAITEMENT ===
    subgraph PREP["⚙️ PRÉTRAITEMENT (Rasterio + GeoPandas)"]
        P1["Reprojection\nEPSG:32198"]
        P2["Découpage\nSainte-Marthe-sur-le-Lac"]
        P3["Calibration SAR\n+ Calcul NDWI"]
        P4["Nettoyage\nTopologie vectorielle"]
    end

    %% === MODÈLE IA ===
    subgraph AI["🤖 INTELLIGENCE ARTIFICIELLE (PyTorch)"]
        AI1["Modèle U-Net\n(Sen1Floods11)"]
        AI2["Inférence\nDétection surfaces d'eau"]
        AI3["Vectorisation\nZones inondées"]
    end

    %% === BASE DE DONNÉES ===
    subgraph DB["🗄️ BASE DE DONNÉES (PostgreSQL + PostGIS)"]
        DB1["Table\nelectric_network"]
        DB2["Table\nflood_zones"]
        DB3["Table\nrisk_analysis"]
        DB4["Table\nalertes"]
    end

    %% === ANALYSE SPATIALE ===
    subgraph SIG["📐 ANALYSE SPATIALE (PostGIS)"]
        G1["ST_Intersects\nZones inondées × Réseau électrique"]
        G2["ST_Buffer\n50m / 100m / 200m"]
        G3["Calcul du\nniveau de risque"]
    end

    %% === PUBLICATION ===
    subgraph PUB["🌐 PUBLICATION (GeoServer)"]
        GS["GeoServer\nServices WMS / WFS"]
    end

    %% === WEB ===
    subgraph WEB["💻 APPLICATION WEB (Django + Leaflet)"]
        DJ["Django\n(GeoDjango)"]
        LF["Carte interactive\nLeaflet.js"]
        AL["Alertes\nautomatiques"]
    end

    %% === CONNEXIONS ===
    S1 --> A1
    S2 --> A1
    S3 --> A2
    S4 --> A2
    S5 --> A2

    A1 --> P1
    A2 --> P4

    P1 --> P2
    P2 --> P3
    P4 --> DB1

    P3 --> AI1
    AI1 --> AI2
    AI2 --> AI3

    AI3 --> DB2
    P3 --> DB2
    S4 --> DB2

    DB1 --> G1
    DB2 --> G1
    G1 --> G2
    G2 --> G3
    G3 --> DB3
    DB3 --> DB4

    DB1 --> GS
    DB2 --> GS
    DB3 --> GS

    GS --> LF
    DB4 --> AL
    AL --> DJ
    LF --> DJ
```

---

## Diagramme 2 — Architecture des services Docker

```mermaid
graph TB

    subgraph DOCKER["🐳 Docker Compose — GeoRisk Sentinel"]

        subgraph CLIENT["Navigateur"]
            BR["Utilisateur\n(carte web)"]
        end

        subgraph APP["Service : web (port 8000)"]
            DJ["Django\n+ GeoDjango\n+ Leaflet"]
        end

        subgraph CARTO["Service : geoserver (port 8080)"]
            GS["GeoServer\nWMS / WFS"]
        end

        subgraph BD["Service : postgis (port 5432)"]
            PG["PostgreSQL\n+ PostGIS"]
        end

        subgraph ADMIN["Service : pgadmin (port 5050)"]
            PGA["pgAdmin\n(optionnel)"]
        end

        BR -->|HTTP| DJ
        DJ -->|WMS/WFS| GS
        DJ -->|SQL géospatial| PG
        GS -->|lecture couches| PG
        PGA -->|admin| PG

    end
```

---

## Diagramme 3 — Modèle de risque multicritère

```mermaid
flowchart LR

    subgraph ENTREES["Entrées du modèle"]
        E1["Niveau d'eau\nSentinel-1 SAR"]
        E2["Distance\nà la rivière / lac"]
        E3["Altitude\nDEM Copernicus"]
        E4["Pente\nDEM dérivé"]
        E5["Criticité\nde l'infrastructure"]
        E6["Historique\nd'inondations 2019"]
    end

    subgraph CALCUL["Calcul du risque"]
        R["Risque = W1×niveau_eau\n+ W2×distance_rivière\n+ W3×altitude\n+ W4×pente\n+ W5×criticité\n+ W6×historique"]
    end

    subgraph CLASSES["Classification"]
        C1["🟢 Risque FAIBLE"]
        C2["🟡 Risque MOYEN"]
        C3["🟠 Risque ÉLEVÉ"]
        C4["🔴 Risque CRITIQUE"]
    end

    E1 --> R
    E2 --> R
    E3 --> R
    E4 --> R
    E5 --> R
    E6 --> R

    R --> C1
    R --> C2
    R --> C3
    R --> C4
```

---

## Diagramme 4 — Flux des données dans Django (GeoDjango)

```mermaid
sequenceDiagram
    participant U as Utilisateur
    participant DJ as Django (views.py)
    participant PG as PostGIS
    participant GS as GeoServer
    participant LF as Leaflet (carte)

    U->>DJ: Ouvre la carte web
    DJ->>PG: SELECT * FROM risk_analysis WHERE niveau='élevé'
    PG-->>DJ: Résultats (GeoJSON)
    DJ->>GS: Requête WMS (couches fond de carte)
    GS-->>DJ: Tuiles cartographiques
    DJ-->>LF: Données JSON + tuiles
    LF-->>U: Carte interactive affichée

    U->>DJ: Clique sur une infrastructure
    DJ->>PG: SELECT * FROM alertes WHERE infra_id = X
    PG-->>DJ: Alertes actives
    DJ-->>U: Popup avec niveau de risque + alertes
```

---

*Fichier à utiliser avec Draw.io — Coller le code Mermaid dans Extras → Edit Diagram*
