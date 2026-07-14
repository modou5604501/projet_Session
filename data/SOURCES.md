# Sources des données — GeoCharge Montréal
## Projet : Accessibilité aux bornes de recharge électrique à Montréal

Toutes les données sont sous licence **CC-BY 4.0** et disponibles publiquement.
Les fichiers sont dans le dossier [`data/`](.) de ce dépôt GitHub.

---

## 1. Bornes de recharge publiques

- **Fichier GitHub** : [`vectors/bornes_recharge_montreal.geojson`](vectors/bornes_recharge_montreal.geojson)
- **URL source** : https://donnees.montreal.ca/dataset/bornes-de-recharge-electrique
- **Organisation** : Ville de Montréal
- **Portail** : Données de Montréal (CKAN, CC-BY 4.0)
- **Mise à jour** : Continue — re-téléchargement automatique hebdomadaire (`src/preprocessing/refresh_data.py`)
- **Projection** : WGS84 (CRS84 / EPSG:4326)
- **Date d'acquisition** : 7 juillet 2026
- **Citation** : Ville de Montréal. *Bornes de recharge publiques*, Données Québec. CC-BY 4.0. Consulté le 7 juillet 2026.

---

## 2. Statistiques d'utilisation des bornes 2025

- **Fichier GitHub** : [`vectors/chargeurs_statistiques_2025.csv`](vectors/chargeurs_statistiques_2025.csv)
- **URL source** : https://donnees.montreal.ca/dataset/bornes-de-recharge-electrique
- **Organisation** : Ville de Montréal
- **Portail** : Données de Montréal (CC-BY 4.0)
- **Format** : CSV — recharges, kWh, taux d'utilisation (~79-80%), usagers/jour par borne
- **Date d'acquisition** : 7 juillet 2026
- **Citation** : Ville de Montréal. *Statistiques d'utilisation des bornes de recharge*, Données Québec, 2025.

---

## 3. Limites administratives — Arrondissements de Montréal

- **Fichier GitHub** : [`vectors/arrondissements_montreal.geojson`](vectors/arrondissements_montreal.geojson)
- **URL source** : https://donnees.montreal.ca/dataset/limites-administratives-agglomeration
- **Organisation** : Ville de Montréal
- **Portail** : Données de Montréal (CC-BY 4.0)
- **Projection** : WGS84 (EPSG:4326)
- **Dernière modification** : 2026-06-30
- **Date d'acquisition** : 7 juillet 2026
- **Citation** : Ville de Montréal. *Limites administratives de l'agglomération de Montréal*, Données Québec, mis à jour le 30 juin 2026.

---

## 4. Référentiel quartiers (StatCan Recensement 2021 — concordance)

- **Fichier GitHub** : [`quartiers_reference_habitation.csv`](quartiers_reference_habitation.csv)
- **URL source** : https://donnees.montreal.ca/dataset/recensement-2021-strategie-immobiliere
- **Organisation** : Statistique Canada / Ville de Montréal — Service de la stratégie immobilière et de l'habitation
- **Portail** : Données de Montréal (CC-BY 4.0)
- **Format** : CSV — 91 quartiers avec numéro et nom d'arrondissement (concordance quartier → arrondissement)
- **Date d'acquisition** : 8 juillet 2026
- **Citation** : Ville de Montréal. *Commande personnalisée du recensement 2021 — Service de la stratégie immobilière et de l'habitation*, Données Québec. CC-BY 4.0.

---

## 4b. Profil socio-démographique par arrondissement (StatCan Recensement 2021)

- **Fichier GitHub** : [`demo_arrondissements.csv`](demo_arrondissements.csv)
- **URL source** : https://donnees.montreal.ca/dataset/8e35e633-cec1-44c2-9a88-8aca9f41e3fd
  *(= Profil des ménages et des logements 2021 — Données de Montréal)*
- **Organisation** : Statistique Canada — Recensement 2021
- **Portail** : Données de Montréal (CC-BY 4.0)
- **Script de téléchargement** : [`src/preprocessing/download_demo_data.py`](../src/preprocessing/download_demo_data.py)
- **Contenu** : 19 arrondissements, 7 variables — revenu médian, densité, taux de propriété, taux de motorisation (proxy), taux de faible revenu
- **Méthode d'extraction** : Les profils HTML par arrondissement sont téléchargés depuis Données de Montréal et les valeurs extraites des blocs JSON (`<script type="application/json">`) via BeautifulSoup. La population et la densité sont estimées à partir du nombre de ménages × 2,28 (taille moyenne des ménages au Québec, StatCan 2021) / superficie (GeoJSON).
- **Utilisation** : Endpoints `/api/equity/`, `/api/correlation/`, `/api/priorite/`
- **Date d'acquisition** : 13–14 juillet 2026
- **Citation** : Statistique Canada. *Recensement de la population 2021 — Profil des ménages et des logements*. Données de Montréal, CC-BY 4.0.

---

## 5. Parcs et espaces verts de Montréal

- **Fichier GitHub** : [`vectors/parcs_montreal.geojson`](vectors/parcs_montreal.geojson)
- **URL source** : https://donnees.montreal.ca/dataset/grands-parcs-parcs-arrondissements-espaces-publics
- **Organisation** : Ville de Montréal — Direction des grands parcs et de la nature en ville
- **Portail** : Données de Montréal (CC-BY 4.0)
- **Projection** : WGS84 (EPSG:4326) — centroïdes des polygones sources
- **Filtrage** : superficie > 0,1 ha ; 1 541 parcs retenus sur total île de Montréal
- **Utilisation** : Requête spatiale « parcs sans couverture adéquate » (`LEFT JOIN + ST_DWithin`)
- **Date d'acquisition** : 10 juillet 2026
- **Citation** : Ville de Montréal. *Grands parcs, parcs d'arrondissements et espaces publics*, Données Québec. CC-BY 4.0. Consulté le 10 juillet 2026.

---

## 6. Établissements alimentaires (épiceries, marchés, supermarchés)

- **Fichier GitHub** : [`vectors/epiceries_montreal.geojson`](vectors/epiceries_montreal.geojson)
- **URL source** : https://donnees.montreal.ca/dataset/etablissements-alimentaires
- **Organisation** : Ville de Montréal — Direction de la santé environnementale et des affaires réglementaires
- **Portail** : Données de Montréal (CC-BY 4.0)
- **Projection** : WGS84 (EPSG:4326)
- **Filtrage** : types épicerie/marché/aliments, statut = Ouvert, coordonnées valides → 3 010 établissements
- **Utilisation** : Requête « épiceries sans borne à proximité » (`NOT EXISTS + CROSS JOIN LATERAL + KNN`)
- **Date d'acquisition** : 10 juillet 2026
- **Citation** : Ville de Montréal. *Établissements alimentaires*, Données Québec. CC-BY 4.0. Consulté le 10 juillet 2026.

---

## 7. Réseau routier de Montréal (Géobase)

- **Fichier GitHub** : [`vectors/reseau_routier_montreal.geojson`](vectors/reseau_routier_montreal.geojson)
- **URL source** : https://donnees.montreal.ca/dataset/geobase-reseau-routier
- **Organisation** : Ville de Montréal
- **Portail** : Données de Montréal (CC-BY 4.0)
- **Projection** : WGS84 (EPSG:4326)
- **Mise à jour** : Périodique (dernier dépôt : 08 juillet 2026)
- **Filtrage** : CLASSE ≥ 5 (collectrices, artères, autoroutes) → 17 540 tronçons sur 47 983 totaux
- **Utilisation** : Couche visuelle toggleable — contexte des axes de circulation majeurs
- **Date d'acquisition** : 13 juillet 2026
- **Citation** : VILLE DE MONTRÉAL. *Géobase - réseau routier*, Données Québec, 2013, mis à jour 08 juillet 2026. CC-BY 4.0.

---

## 8. Tracés des lignes de bus et de métro (STM)

- **Fichiers GitHub** : [`vectors/stm_sig/`](vectors/stm_sig/) (Shapefile) + [`vectors/stations_metro_stm.geojson`](vectors/stations_metro_stm.geojson)
- **URL source** : https://www.donneesquebec.ca/recherche/dataset/gtfs-stm
- **Organisation** : Société de transport de Montréal (STM)
- **Portail** : Données Québec (CC-BY 4.0)
- **Projection source** : NAD83 / MTM zone 8 (EPSG:32188) → **reprojetée en WGS84 lors de l'import**
- **Filtrage** : 72 stations de métro uniquement (lignes Verte, Orange, Bleue, Jaune), issues du fichier GTFS complet
- **Utilisation** : Requête intermodalité `NOT EXISTS + ST_DWithin` (stations sans borne à 500 m)
- **Date d'acquisition** : 7 juillet 2026
- **Citation** : SOCIÉTÉ DE TRANSPORT DE MONTRÉAL. *Tracés des lignes de bus et de métro*, Données Québec, mis à jour le 06 juillet 2026. CC-BY 4.0.

---

## Récapitulatif — Accès direct aux sources

| Couche | Fichier dans ce dépôt | Lien source |
|---|---|---|
| Bornes de recharge (2 412) | [`bornes_recharge_montreal.geojson`](vectors/bornes_recharge_montreal.geojson) | [donnees.montreal.ca/dataset/bornes-de-recharge-electrique](https://donnees.montreal.ca/dataset/bornes-de-recharge-electrique) |
| Arrondissements (34) | [`arrondissements_montreal.geojson`](vectors/arrondissements_montreal.geojson) | [donnees.montreal.ca/dataset/limites-administratives-agglomeration](https://donnees.montreal.ca/dataset/limites-administratives-agglomeration) |
| Stations de métro STM (72) | [`stations_metro_stm.geojson`](vectors/stations_metro_stm.geojson) | [donneesquebec.ca/recherche/dataset/gtfs-stm](https://www.donneesquebec.ca/recherche/dataset/gtfs-stm) |
| Parcs (1 541) | [`parcs_montreal.geojson`](vectors/parcs_montreal.geojson) | [donnees.montreal.ca/dataset/grands-parcs-parcs-arrondissements-espaces-publics](https://donnees.montreal.ca/dataset/grands-parcs-parcs-arrondissements-espaces-publics) |
| Épiceries (3 010) | [`epiceries_montreal.geojson`](vectors/epiceries_montreal.geojson) | [donnees.montreal.ca/dataset/etablissements-alimentaires](https://donnees.montreal.ca/dataset/etablissements-alimentaires) |
| Réseau routier (17 540) | [`reseau_routier_montreal.geojson`](vectors/reseau_routier_montreal.geojson) | [donnees.montreal.ca/dataset/geobase-reseau-routier](https://donnees.montreal.ca/dataset/geobase-reseau-routier) |
| Profil socio-démographique | [`demo_arrondissements.csv`](demo_arrondissements.csv) | [donnees.montreal.ca/dataset/…profils-menages-logements](https://donnees.montreal.ca/dataset/8e35e633-cec1-44c2-9a88-8aca9f41e3fd) |

---

## Notes techniques

| Donnée | CRS source | CRS stockage | Conversion |
|---|---|---|---|
| Bornes de recharge | WGS84 | WGS84 (EPSG:4326) | Aucune |
| Arrondissements | WGS84 | WGS84 (EPSG:4326) | Aucune |
| Parcs (centroïdes) | WGS84 | WGS84 (EPSG:4326) | Centroïde calculé depuis polygone source |
| Épiceries | WGS84 | WGS84 (EPSG:4326) | Aucune |
| STM arrêts/lignes | NAD83 MTM8 (EPSG:32188) | WGS84 (EPSG:4326) | Via `gdf.to_crs(epsg=4326)` |
| Réseau routier | WGS84 | WGS84 (EPSG:4326) | Aucune (déjà en WGS84) |
| Buffers 500m | — | WGS84 (EPSG:4326) | Calcul en EPSG:32188, retour WGS84 |

**Calcul des buffers** : Les zones de couverture de 500 m sont calculées en EPSG:32188 (projection métrique NAD83/MTM zone 8) pour garantir la précision des distances, puis reprojetées en WGS84 pour le stockage et l'affichage.

---

*Toutes les données sont sous licence CC-BY 4.0 — attribution obligatoire dans tout document ou publication.*

*GMQ580 Géomatique Informatique 2 — Été 2026 — Université de Sherbrooke*
