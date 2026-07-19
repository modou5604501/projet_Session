# Diagrammes Mermaid — GeoCharge Montréal
## Pour utilisation dans Draw.io / GitHub

**Comment utiliser dans Draw.io :**
1. Ouvrir [app.diagrams.net](https://app.diagrams.net)
2. Menu **Extras** → **Edit Diagram**
3. Coller le code du diagramme voulu → cliquer **OK**

> Ces diagrammes sont aussi rendus automatiquement dans GitHub (Mermaid natif).
> Ils décrivent l'application **Shiny for Python autonome** (`shiny app/app_bornes_recharges.py`) — sans Django, sans PostGIS, sans Docker.

---

## Diagramme 1 — Pipeline de traitement complet

```mermaid
flowchart TD
    subgraph ACQ["PHASE 1 — ACQUISITION DES DONNÉES OUVERTES (Données Québec · CC-BY 4.0)"]
        A1[("Bornes de recharge\n2 412 bornes GeoJSON\nVille de Montréal")]
        A2[("Arrondissements\n34 polygones GeoJSON\nVille de Montréal")]
        A5[("Parcs et espaces verts\n1 541 parcs GeoJSON\nVille de Montréal")]
        A6[("Établissements alimentaires\n3 010 épiceries GeoJSON\nVille de Montréal")]
        A7[("Statistiques d'utilisation 2025\nCSV · Ville de Montréal")]
        A8[("Profil socio-démographique\n19 arrondissements CSV\nStatCan Recensement 2021")]
    end

    subgraph CALC["PHASE 2 — CALCULS EN MÉMOIRE (au démarrage de l'app, GeoPandas)"]
        B1["Lecture GeoJSON/CSV\nGeoPandas + Shapely\nValidation géométries"]
        B2["Reprojection EPSG:32188\n(NAD83 MTM8) pour calculs métriques"]
        B3["Buffer 500 m + union\n→ pct_couverture par arrondissement"]
        B4["Jointures spatiales (sjoin)\nparcs/épiceries ↔ bornes"]
        B5["Jointure démographique\narrondissements ↔ CSV StatCan"]
    end

    subgraph WEB["PHASE 3 — APPLICATION WEB Shiny for Python + Folium"]
        D1["Carte interactive\nFolium/Leaflet\nBornes · zones prioritaires · zones sous-desservies"]
        D2["Questions gestionnaire ①②③\nParcs · Épiceries · Corrélation Pearson"]
        D3["Statistiques d'utilisation 2025\nRecharges · kWh · taux d'utilisation"]
    end

    A1 & A2 & A5 & A6 --> B1
    A7 --> D3
    A8 --> B5
    B1 --> B2
    B2 --> B3 & B4
    B3 --> D1
    B4 & B5 --> D2
```

---

## Diagramme 2 — Architecture technique

```mermaid
flowchart LR
    subgraph HOST["Machine locale (Windows/Linux/Mac) — un seul processus Python"]
        DATA["data/vectors/*.geojson\ndata/demo_arrondissements.csv\n(chargés en mémoire)"]
        APP["shiny app/app_bornes_recharges.py\nShiny for Python + Uvicorn\nPort 8000"]
        DATA --> APP
    end

    subgraph CLIENT["Navigateur"]
        MAP["127.0.0.1:8000\nCarte interactive\nQuestions gestionnaire ①②③"]
    end

    APP -- "sert la page + websocket réactif" --> MAP
```

Aucun conteneur Docker, aucune base de données, aucun service externe requis pour faire tourner l'app —
c'est la principale simplification par rapport à l'architecture Django + PostGIS + Docker envisagée initialement.

---

## Diagramme 3 — Modèle de données logique

> Ce schéma décrit la structure des couches sources et leurs relations spatiales. Dans l'app Shiny,
> ces relations sont calculées **en mémoire avec GeoPandas** à chaque démarrage — `ZONES_COUVERTURE`
> représente le modèle conceptuel des données, pas une table réellement matérialisée.

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
    DEMO_ARRONDISSEMENT {
        varchar arrondissement PK
        float densite_pop_km2
        float revenu_median_menage
        float tx_voiture_pct
        float tx_faible_revenu_pct
    }

    BORNES_RECHARGE ||--o{ ZONES_COUVERTURE : "1 borne → 1 buffer"
    ARRONDISSEMENTS ||--o{ BORNES_RECHARGE : "contient"
    ARRONDISSEMENTS ||--o| DEMO_ARRONDISSEMENT : "profil socio-démographique (19/34)"
    PARCS }o--o{ BORNES_RECHARGE : "sjoin 500m"
    EPICERIES }o--o{ BORNES_RECHARGE : "sjoin 300m"
```

---

## Diagramme 4 — Flux réactif des questions de gestionnaire

```mermaid
flowchart TD
    USER["Utilisateur ouvre l'onglet\n« Questions des gestionnaires »"]

    USER --> Q1["① Parcs\ninput: seuil N bornes à 500 m\nfiltre nb_bornes_500m < N"]
    USER --> Q2["② Épiceries\nfiltre has_borne_300m == False"]
    USER --> Q3["③ Corrélation\nPearson r sur 6 facteurs\nvs pct_couverture (19 arrondissements)"]

    Q1 --> OUT["Résumé + tableau\nrendu réactif Shiny\n(@render.ui / @render.data_frame)"]
    Q2 --> OUT
    Q3 --> OUT2["Graphique en barres\n(Matplotlib) + interprétation"]
```

> Contrairement à l'ancienne architecture Django (API REST + JS côté client), toute la logique
> réactive est ici gérée côté serveur Python par Shiny — pas d'endpoints REST, pas de JavaScript custom.

---

*GeoCharge Montréal — GMQ580 Géomatique Informatique 2 — Été 2026 — Université de Sherbrooke*
*Équipe : Modou Khabane Mbaye & Rahina Djelila Sarah Bagre*
