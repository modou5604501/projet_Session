# Plan de présentation — Soutenance
## Optimisation de l'accessibilité aux bornes de recharge électrique à Montréal

**GMQ580 — Géomatique Informatique 2 | Été 2026**  
**Durée : 15-20 minutes**

---

## Diapositive 1 — Titre

**GeoRisk Sentinel**  
Optimisation de l'accessibilité aux bornes de recharge électrique à Montréal

- Modou Khabane Mbaye
- Rahina Djelila Sarah Bagre
- Université de Sherbrooke | GMQ580 | Juillet 2026

---

## Diapositive 2 — Mise en contexte (2 min)

**La transition électrique au Québec**
- Croissance rapide du parc de véhicules électriques
- Montréal : des centaines de bornes publiques, mais distribuées inégalement
- Certains arrondissements bien couverts, d'autres en manque

**Le problème concret**
- Sans analyse spatiale : impossible de savoir où sont les vrais déficits
- Les investissements publics doivent être guidés par des données

---

## Diapositive 3 — Question de recherche (1 min)

> **Où faudrait-il installer de nouvelles bornes de recharge à Montréal afin de maximiser l'accessibilité des usagers tout en réduisant les zones sous-desservies ?**

**Périmètre :**
- Zone d'étude : agglomération de Montréal (19 arrondissements)
- Critère d'accessibilité : rayon de 500 m autour de chaque borne
- Seuil de sous-desserte : < 30 % du territoire couvert

---

## Diapositive 4 — Données (2 min)

| Couche | Source | Licence |
|---|---|---|
| Bornes de recharge publiques | Données Québec / Ville de Montréal | CC-BY 4.0 |
| Statistiques d'utilisation 2025 | Données Québec / Ville de Montréal | CC-BY 4.0 |
| Arrondissements de Montréal | Données Québec / Ville de Montréal | CC-BY 4.0 |
| Stations et arrêts STM | Données Québec / STM | CC-BY 4.0 |

**Points techniques :**
- Données STM en NAD83 MTM8 (EPSG:32188) → reprojetées en WGS84
- Buffers calculés en MTM8 (métrique) → stockés en WGS84

---

## Diapositive 5 — Architecture technique (2 min)

```
[Données brutes]          [PostGIS Docker]          [Application web]
GeoJSON + SHP   →  import_postgis.py  →  Django 5.2 + Leaflet
                →  buffer_analysis.py →  API REST GeoJSON
                →  gap_analysis.py    →  Tableau de bord interactif
```

**Stack :**
- Base de données : PostgreSQL 15 + PostGIS 3.3 (Docker)
- Backend : Python 3.10, Django 5.2, GeoDjango, DRF
- Frontend : Leaflet.js
- Conteneurisation : Docker Compose

---

## Diapositive 6 — Méthodologie : analyse de couverture (2 min)

**Buffer 500 m autour de chaque borne**
- Calculé en EPSG:32188 (projection métrique) pour la précision
- Retransformé en WGS84 pour le stockage
- `ST_Buffer(ST_Transform(geom, 32188), 500)`

**% de couverture par arrondissement**
- `ST_Intersection(union_buffers, polygone_arrondissement)`
- Rapport d'aire : superficie intersectée / superficie totale × 100

---

## Diapositive 7 — Démonstration du tableau de bord (5 min)

*[Montrer l'application en direct sur http://localhost:8000]*

**Couches affichées :**
1. **Bornes existantes** (points verts) — `/api/bornes/`
2. **Zones couvertes à 500 m** (bleu transparent) — `/api/couverture/`
3. **Stations de métro STM** (icônes orange) — `/api/metro/`
4. **Arrondissements** (contours violets) — `/api/arrondissements/`

**Panneau de statistiques :**
- Nombre total de bornes
- % de couverture par arrondissement
- Liste des arrondissements sous-desservis (< 30 %)

---

## Diapositive 8 — Résultats : zones sous-desservies (2 min)

**Constats :**
- Forte concentration de bornes dans les arrondissements centraux
- Périphérie de l'île (Rivière-des-Prairies, L'Île-Bizard, Pierrefonds) nettement moins couverte
- Taux d'utilisation moyen ~79-80 % → demande forte, infrastructure insuffisante

**Recommandations :**
- Prioriser les intersections principales dans les arrondissements à < 30 % de couverture
- Cibler les abords des stations de métro sans borne dans un rayon de 500 m
- Renforcer les secteurs résidentiels denses non couverts

---

## Diapositive 9 — Limites et perspectives (1 min)

**Limites :**
- Buffer circulaire (vs isochrone pédestre réel)
- Réseau privé non inclus
- Demande future non modélisée

**Perspectives :**
- Isochrones pédestres via pgRouting
- Intégration données population (StatCan)
- Optimisation algorithmique (modèle p-median)
- Mise à jour temps réel (API Données Québec)

---

## Diapositive 10 — Conclusion (1 min)

**Ce que nous avons livré :**
- Base de données spatiale PostGIS avec 4 couches
- Pipeline Python automatisé (import + analyse)
- API REST GeoJSON opérationnelle
- Tableau de bord Leaflet interactif
- Rapport technique complet

**Dépôt GitHub :** https://github.com/modou5604501/projet_Session

> L'analyse spatiale confirme des disparités importantes entre arrondissements et fournit une base objective pour guider les décisions de la Ville de Montréal.

---

*Merci — Questions ?*
