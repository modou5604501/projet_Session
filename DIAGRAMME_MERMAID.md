# Diagrammes Mermaid — GeoCharge Montréal
## Pour utilisation dans Draw.io / GitHub

**Comment utiliser dans Draw.io :**
1. Ouvrir [app.diagrams.net](https://app.diagrams.net)
2. Menu **Extras** → **Edit Diagram**
3. Coller le code du diagramme voulu → cliquer **OK**

> Ces diagrammes sont aussi rendus automatiquement dans GitHub (Mermaid natif).
> Ils décrivent l'application **Shiny for Python autonome** (`shiny_app/app.py`) — sans Django, sans PostGIS, sans Docker.

---

## Diagramme 1 — Pipeline de traitement complet

```mermaid
flowchart TD
    subgraph ACQ["PHASE 1 — ACQUISITION DES DONNÉES OUVERTES (Données Québec · CC-BY 4.0)"]
        A1[("Bornes de recharge\n2 412 bornes GeoJSON\nVille de Montréal")]
        A2[("Arrondissements\n34 polygones GeoJSON\nVille de Montréal")]
        A3[("Stations de métro STM\nGeoJSON · 72 stations\n4 lignes")]
        A5[("Parcs et espaces verts\n1 541 parcs GeoJSON\nVille de Montréal")]
        A6[("Établissements alimentaires\n3 010 épiceries GeoJSON\nVille de Montréal")]
        A8[("Profil socio-démographique\n19 arrondissements CSV\nStatCan Recensement 2021")]
    end

    subgraph CALC["PHASE 2 — CALCULS EN MÉMOIRE (au démarrage de shiny_app/app.py, GeoPandas)"]
        B1["Lecture GeoJSON/CSV\nGeoPandas + Shapely\nValidation géométries"]
        B2["Reprojection EPSG:32188\n(NAD83 MTM8) pour calculs métriques"]
        B3["ST_Buffer 500 m + union\n→ pct_couverture par arrondissement"]
        B4["Jointures spatiales (sjoin)\nparcs/épiceries/stations ↔ bornes"]
        B5["Jointure démographique\narrondissements ↔ CSV StatCan"]
    end

    subgraph WEB["PHASE 3 — APPLICATION WEB Shiny for Python + Folium"]
        D1["Carte interactive\nFolium/Leaflet · CARTO Dark Matter\nChoroplèthe · Clusters de bornes"]
        D2["Outils gestionnaire G1–G5\nParcs · Épiceries · Score priorité\nCorrélation · Intermodalité STM"]
        D3["Onglet équité\nScatter plot · Pearson r"]
    end

    A1 & A2 & A3 & A5 & A6 --> B1
    A8 --> B5
    B1 --> B2
    B2 --> B3 & B4
    B3 --> D1
    B4 & B5 --> D2
    B5 --> D3
```

---

## Diagramme 2 — Architecture technique

```mermaid
flowchart LR
    subgraph HOST["Machine locale (Windows/Linux/Mac) — un seul processus Python"]
        DATA["data/vectors/*.geojson\ndata/demo_arrondissements.csv\n(chargés en mémoire)"]
        APP["shiny_app/app.py\nShiny for Python + Uvicorn\nPort 8000"]
        DATA --> APP
    end

    subgraph CLIENT["Navigateur"]
        MAP["127.0.0.1:8000\nCarte interactive\nOutils gestionnaire\nOnglet équité"]
    end

    APP -- "sert la page + websocket réactif" --> MAP
```

Aucun conteneur Docker, aucune base de données, aucun service externe requis pour faire tourner l'app —
c'est la principale simplification par rapport à l'architecture Django + PostGIS + Docker envisagée initialement.

---

## Diagramme 3 — Modèle de données logique

> Ce schéma décrit la structure des couches sources et leurs relations spatiales. Dans l'app Shiny,
> ces relations sont calculées **en mémoire avec GeoPandas** à chaque démarrage — `ZONES_COUVERTURE`
> et `RESEAU_ROUTIER` représentent le modèle conceptuel des données, pas des tables réellement matérialisées
> (le réseau routier est disponible dans `data/vectors/` mais n'est pas chargé par l'app actuelle).

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
    RESEAU_ROUTIER {
        int id PK
        int classe
        varchar type_route
        varchar nom_voie
        varchar arrondissement
        geometry geom "LINESTRING EPSG:4326"
    }

    BORNES_RECHARGE ||--o{ ZONES_COUVERTURE : "1 borne → 1 buffer 500m"
    ARRONDISSEMENTS ||--o{ BORNES_RECHARGE : "contient"
    PARCS }o--o{ BORNES_RECHARGE : "sjoin 500m"
    EPICERIES }o--o{ BORNES_RECHARGE : "sjoin 300m"
    STATIONS_METRO }o--o{ BORNES_RECHARGE : "sjoin (rayon paramétrable)"
    RESEAU_ROUTIER }o--o{ BORNES_RECHARGE : "non implémenté dans l'app"
```

---

## Diagramme 4 — Flux réactif des outils gestionnaire (G1–G5)

```mermaid
flowchart TD
    USER["Utilisateur clique\n▶ Analyser"]

    USER --> G1["G1 — Parcs\ninput: seuil N bornes\nfiltre nb_bornes_500m < N"]
    USER --> G2["G2 — Épiceries\nfiltre has_borne_300m == False"]
    USER --> G3["G3 — Score priorité\nformule pondérée pré-calculée\n(19 arrondissements)"]
    USER --> G4["G4 — Corrélation\nPearson r sur 6 facteurs\nvs pct_couverture"]
    USER --> G5["G5 — Intermodalité STM\ninput: rayon (m)\nsjoin stations ↔ bornes par ligne"]

    G1 --> OUT["Tableau + résumé\nrendu réactif Shiny\n(@render.table / @render.ui)"]
    G2 --> OUT
    G3 --> OUT
    G4 --> OUT
    G5 --> OUT
```

> Contrairement à l'ancienne architecture Django (API REST + JS côté client), toute la logique
> réactive est ici gérée côté serveur Python par Shiny — pas d'endpoints REST, pas de JavaScript custom.

---

*GeoCharge Montréal — GMQ580 Géomatique Informatique 2 — Été 2026 — Université de Sherbrooke*
*Équipe : Modou Khabane Mbaye & Rahina Djelila Sarah Bagre*
