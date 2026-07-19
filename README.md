# GeoCharge Montréal
## Accessibilité aux bornes de recharge électrique à Montréal

**Cours :** GMQ580 — Géomatique Informatique 2 · Été 2026 · Université de Sherbrooke

| Nom | Courriel |
|---|---|
| Modou Khabane Mbaye | modou.khabane.mbaye@usherbrooke.ca |
| Rahina Djelila Sarah Bagre | rahina.bagre@usherbrooke.ca |

---

## Problématique

La distribution des bornes de recharge publiques à Montréal est inégale : certains secteurs en ont beaucoup, d'autres presque pas. La position spatiale des bornes seule ne suffit pas à comprendre la situation — il faut aussi savoir si elle est liée au profil de la population, à la présence de parcs ou de commerces alimentaires.

**Question de recherche :** où faudrait-il installer de nouvelles bornes à Montréal, et qu'est-ce qui explique leur répartition actuelle ?

**Ce que l'application fait concrètement :** un tableau de bord qui cartographie les 2 412 bornes de Montréal, identifie les zones prioritaires pour en ajouter, et répond à trois questions concrètes de gestionnaire : les parcs ont-ils assez de bornes à proximité ? les épiceries en ont-elles ? la répartition des bornes est-elle liée au profil socio-démographique ?

---

## Données utilisées

Toutes proviennent de sources ouvertes (Ville de Montréal, Statistique Canada), licence CC-BY 4.0. Détails et citations complètes : [data/SOURCES.md](data/SOURCES.md).

| Couche | Fichier | Utilisation |
|---|---|---|
| Bornes de recharge (2 412) | `data/vectors/bornes_recharge_montreal.geojson` | Carte, tous les calculs de proximité |
| Arrondissements (34) | `data/vectors/arrondissements_montreal.geojson` | Choroplèthe, filtres |
| Zones sous-desservies | `data/vectors/zones_sous_desservies.geojson` | Carte, priorisation |
| Parcs (1 541) | `data/vectors/parcs_montreal.geojson` | Question « les parcs ont-ils assez de bornes ? » |
| Épiceries (3 010) | `data/vectors/epiceries_montreal.geojson` | Question « les épiceries ont-elles une borne à proximité ? » |
| Profil socio-démographique par arrondissement | `data/demo_arrondissements.csv` | Question « lien avec le profil de la population ? » |
| Densité de population par secteur | `data/vectors/demographie_quebec.geojson` | Score de priorité des nouvelles bornes |
| Statistiques d'utilisation 2025 | `data/vectors/chargeurs_statistiques_2025.csv` | Recharges, kWh, taux d'utilisation |

---

## Ce que l'application permet de faire

- **Carte interactive** — bornes par niveau de recharge, zones prioritaires pour de nouvelles bornes, zones sous-desservies, filtres par niveau/tarification/emplacement/arrondissement
- **Indicateurs clés** — bornes totales, répartition Niveau 2 / recharge rapide (BRCC), arrondissements couverts
- **① Parcs** — combien de parcs ont moins de bornes que le seuil choisi à 500 m
- **② Épiceries** — combien d'épiceries n'ont aucune borne à 300 m
- **③ Corrélation** — quel facteur (densité, revenu, motorisation, parcs, épiceries) explique le mieux la répartition des bornes
- **Statistiques d'utilisation 2025** — recharges totales, kWh consommés, taux d'utilisation, usagers par jour
- **Tableaux** — synthèse par arrondissement, zones prioritaires, zones sous-desservies, données complètes
- **Signalement citoyen** — formulaire pour signaler une borne manquante ou hors service

**Résultat principal :** la couverture en bornes suit surtout la **densité de population** (r = 0,875), beaucoup plus que le revenu médian (r = −0,60, une corrélation négative). Le manque de bornes touche surtout les parcs (1 413 sur 1 541 sous le seuil de 20 bornes à 500 m) et, dans une moindre mesure, les épiceries (819 sur 3 010 sans borne à 300 m).

---

## Technologies

| Technologie | Rôle |
|---|---|
| Python 3.10 | Langage principal |
| Shiny for Python | Application web réactive |
| GeoPandas + Shapely | Analyse spatiale (buffers, jointures spatiales) |
| Folium | Carte Leaflet interactive |
| Matplotlib | Graphiques |
| Pandas | Traitement des données |

Aucune base de données ni conteneur : tout est chargé et calculé en mémoire au démarrage de l'application.

---

## Démarrage local

```bash
git clone https://github.com/modou5604501/projet_Session.git
cd projet_Session
python -m venv venv
venv\Scripts\activate          # Windows (ou : source venv/bin/activate sur Linux/Mac)
pip install -r requirements_bornes_recharges.txt
python -m shiny run --port 8000 "shiny app/app_bornes_recharges.py"
# Tableau de bord : http://127.0.0.1:8000
```

> Le premier chargement prend une quinzaine de secondes (calculs spatiaux + carte). Utiliser `python -m shiny run` plutôt que `shiny run` seul : sur certaines installations (notamment Windows), l'exécutable `shiny` n'est pas automatiquement sur le PATH après `pip install`.

---

## Références

- Ville de Montréal. *Bornes de recharge publiques*, Données Québec. CC-BY 4.0.
- Ville de Montréal. *Limites administratives de l'agglomération*, Données Québec. CC-BY 4.0.
- Ville de Montréal. *Grands parcs, parcs d'arrondissements et espaces publics*, Données Québec. CC-BY 4.0.
- Ville de Montréal. *Établissements alimentaires*, Données Québec. CC-BY 4.0.
- Statistique Canada. *Recensement 2021* (commande personnalisée via Données Québec). CC-BY 4.0.

---

*GMQ580 — Géomatique Informatique 2 — Été 2026 — Université de Sherbrooke*
