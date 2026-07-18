# GeoCharge Montréal
## Accessibilité aux bornes de recharge électrique à Montréal

**Cours :** GMQ580 — Géomatique Informatique 2 · Été 2026 · Université de Sherbrooke

| Nom | Courriel |
|---|---|
| Modou Khabane Mbaye | modou.khabane.mbaye@usherbrooke.ca |
| Rahina Djelila Sarah Bagre | rahina.bagre@usherbrooke.ca |

---

## Documents du projet

| Document | Contenu |
|---|---|
| [RAPPORT_FINAL.md](RAPPORT_FINAL.md) | Rapport technique — méthodologie, algorithme, résultats |
| [PRESENTATION_ORALE.md](PRESENTATION_ORALE.md) | Plan de la présentation orale (10 min + 2 min de questions) |
| [data/SOURCES.md](data/SOURCES.md) | Métadonnées de chaque couche (citation, CRS, filtrage) |

---

## Problématique

La distribution des bornes de recharge publiques à Montréal est inégale : certains arrondissements en ont beaucoup, d'autres presque pas. Il n'existe pas d'outil simple pour quantifier ces écarts ni pour orienter les décisions d'investissement.

**Question de recherche :** où faudrait-il installer de nouvelles bornes à Montréal pour réduire les zones sous-desservies ?

**Ce que le projet démontre concrètement d'ici la fin de la session :** une application web (`shiny_app/app.py`) qui calcule, à partir de données réelles, le taux de couverture en bornes de chaque arrondissement, identifie les parcs et épiceries mal desservis, calcule un score de priorité par arrondissement, et vérifie si cette distribution est liée au revenu, à la densité ou à d'autres facteurs démographiques.

---

## Données réellement utilisées

Toutes proviennent de sources ouvertes (Ville de Montréal, STM, Statistique Canada), licence CC-BY 4.0, et sont chargées directement par l'application. Détails et citations complètes : [data/SOURCES.md](data/SOURCES.md).

| Couche | Fichier | Utilisation dans l'app |
|---|---|---|
| Bornes de recharge publiques (2 412 bornes) | `data/vectors/bornes_recharge_montreal.geojson` | Carte, calcul de couverture (buffer 500 m) |
| Arrondissements et villes liées (34 unités) | `data/vectors/arrondissements_montreal.geojson` | Choroplèthe, base de tous les calculs par territoire |
| Parcs et espaces verts (1 541 parcs) | `data/vectors/parcs_montreal.geojson` | Outil G1 — parcs sans borne à proximité |
| Établissements alimentaires (3 010 épiceries) | `data/vectors/epiceries_montreal.geojson` | Outil G2 — épiceries sans borne à proximité |
| Stations de métro STM (72 stations, 4 lignes) | `data/vectors/stations_metro_stm.geojson` | Outil G5 — intermodalité park-and-charge |
| Profil socio-démographique (19 des 34 arrondissements) | `data/demo_arrondissements.csv` | Outils G3 (score de priorité), G4 (corrélation) et l'onglet équité |

Le dossier `data/` contient aussi d'autres fichiers récoltés en cours de route (statistiques d'utilisation 2025, réseau routier, référentiel de quartiers) qui ne sont **pas** utilisés par l'application actuelle — ils ne sont pas listés ci-dessus par souci d'exactitude.

---

## Démarche — des données brutes au résultat

1. **Chargement** : les 5 fichiers GeoJSON et le fichier démographique sont lus avec GeoPandas au démarrage de l'application (aucune base de données).
2. **Reprojection** : les coordonnées passent de WGS84 à EPSG:32188 (NAD83 / MTM zone 8), un système en mètres, pour que les distances soient exactes.
3. **Calcul de couverture** : un cercle (buffer) de 500 m — la distance de marche considérée accessible en urbanisme actif — est tracé autour de chaque borne. L'union de ces cercles, intersectée avec chaque arrondissement, donne le pourcentage de couverture.
4. **Jointures spatiales** : pour chaque parc, épicerie et station de métro, on vérifie si une borne se trouve à proximité (500 m, 300 m ou un rayon ajustable selon l'outil).
5. **Jointure démographique** : les 34 arrondissements sont associés au profil StatCan 2021 quand il existe (19 des 34 en disposent — les 15 autres sont des villes reconstituées sans profil publié par arrondissement).
6. **Résultat** : une application Shiny avec une carte, cinq outils de décision et un onglet d'équité — détaillés dans [RAPPORT_FINAL.md](RAPPORT_FINAL.md).

Un point trouvé en cours d'analyse, plutôt que supposé au départ : la couverture en bornes suit surtout la **densité de population** (r = 0,875) et beaucoup moins le revenu (r = −0,60, une corrélation négative). Détails en section Résultats de [RAPPORT_FINAL.md](RAPPORT_FINAL.md).

---

## Ce que l'application permet de faire

- **Carte interactive** : bornes en grappes, choroplèthe par arrondissement (couverture, revenu médian, motorisation, densité ou faible revenu)
- **G1 — Parcs** : quels parcs manquent de bornes à proximité (seuil ajustable)
- **G2 — Épiceries** : quelles épiceries n'ont aucune borne à 300 m
- **G3 — Score de priorité** : classement des 19 arrondissements selon un score pondéré (couverture, densité, motorisation, équité de revenu, faible revenu)
- **G4 — Corrélation** : lien entre couverture et six facteurs démographiques
- **G5 — Intermodalité STM** : stations de métro sans borne à proximité, par ligne
- **Onglet équité** : couverture vs revenu médian, avec interprétation automatique

---

## Technologies

| Technologie | Rôle |
|---|---|
| Python 3.10 | Langage principal |
| Shiny for Python | Application web réactive |
| GeoPandas + Shapely | Analyse spatiale (buffers, jointures spatiales) |
| Folium | Carte Leaflet interactive |
| PyProj | Reprojection de coordonnées |
| Matplotlib | Graphique de l'onglet équité |

Aucune base de données ni conteneur Docker : tout est chargé et calculé en mémoire au démarrage de l'application.

---

## Démarrage local

```bash
git clone https://github.com/modou5604501/projet_Session.git
cd projet_Session
python -m venv venv
venv\Scripts\activate          # Windows (ou : source venv/bin/activate sur Linux/Mac)
pip install -r shiny_app/requirements.txt
python -m shiny run shiny_app/app.py --reload
# Tableau de bord : http://127.0.0.1:8000
```

> Utiliser `python -m shiny run` plutôt que `shiny run` seul : sur certaines installations (notamment Windows), l'exécutable `shiny` n'est pas automatiquement sur le PATH après `pip install`.

---

## Références

- Ville de Montréal. *Bornes de recharge publiques*, Données Québec. CC-BY 4.0.
- Ville de Montréal. *Limites administratives de l'agglomération*, Données Québec. CC-BY 4.0.
- Société de transport de Montréal. *Tracés des lignes et arrêts STM*, Données Québec. CC-BY 4.0.
- Statistique Canada. *Recensement 2021* (commande personnalisée via Données Québec). CC-BY 4.0.

---

*GMQ580 — Géomatique Informatique 2 — Été 2026 — Université de Sherbrooke*
