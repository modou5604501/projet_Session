# Sources des données — GeoCharge Montréal
## Projet : Accessibilité aux bornes de recharge électrique à Montréal

---

## 1. Bornes de recharge publiques
- **Fichier** : `vectors/bornes_recharge_montreal.geojson`
- **Organisation** : Ville de Montréal
- **Source** : Données Québec
- **Licence** : CC-BY 4.0 — attribution obligatoire
- **Projection** : WGS84 (CRS84 / EPSG:4326)
- **Mise à jour** : Continue
- **Date d'acquisition** : 7 juillet 2026
- **Citation** : Ville de Montréal. *Bornes de recharge publiques*, Données Québec. Consulté le 7 juillet 2026.

## 2. Statistiques d'utilisation des bornes 2025
- **Fichier** : `vectors/chargeurs_statistiques_2025.csv`
- **Organisation** : Ville de Montréal
- **Source** : Données Québec
- **Licence** : CC-BY 4.0
- **Format** : CSV
- **Contenu** : Nombre de recharges, kWh consommés, taux d'utilisation (~79-80%), moyenne usagers/jour par borne
- **Date d'acquisition** : 7 juillet 2026
- **Citation** : Ville de Montréal. *Statistiques d'utilisation des bornes de recharge*, Données Québec, 2025.

## 3. Limites administratives — Arrondissements de Montréal
- **Fichier** : `vectors/arrondissements_montreal.geojson`
- **Organisation** : Ville de Montréal
- **Source** : Données Québec
- **Licence** : CC-BY 4.0
- **Projection** : WGS84 (EPSG:4326)
- **Dernière modification** : 2026-06-30
- **Date d'acquisition** : 7 juillet 2026
- **Citation** : Ville de Montréal. *Limites administratives de l'agglomération de Montréal*, Données Québec, mis à jour le 30 juin 2026.

## 4. Référentiel quartiers (StatCan Recensement 2021 — concordance)
- **Fichier** : `quartiers_reference_habitation.csv`
- **Organisation** : Statistique Canada / Ville de Montréal
- **Source** : Données Québec — Commande personnalisée du recensement 2021 du Service de la stratégie immobilière et de l'habitation
- **Licence** : CC-BY 4.0
- **Format** : CSV (séparateur `;`)
- **Contenu** : 91 quartiers montréalais avec leur numéro et nom d'arrondissement (Num Quartier, Nom Quartier, Num Arr, Nom Arr, nom_mun)
- **Utilisation** : Référentiel de concordance quartier → arrondissement
- **Date d'acquisition** : 8 juillet 2026
- **Citation** : Ville de Montréal. *Commande personnalisée du recensement 2021 — Service de la stratégie immobilière et de l'habitation*, Données Québec. Consulté le 8 juillet 2026.

## 4b. Profil socio-démographique par arrondissement (StatCan Recensement 2021)
- **Fichier** : `demo_arrondissements.csv`
- **Organisation** : Statistique Canada
- **Source** : Recensement de la population 2021 — tableaux thématiques par subdivision de recensement (arrondissement)
- **Licence** : CC-BY 4.0
- **Format** : CSV (séparateur `;`)
- **Contenu** : 19 arrondissements de la Ville de Montréal avec 6 variables socio-démographiques :
  - `pop_2021` — population totale (personnes)
  - `densite_pop_km2` — densité de population (hab./km²)
  - `revenu_median_menage` — revenu médian des ménages ($)
  - `tx_propriete_pct` — taux de ménages propriétaires (%)
  - `tx_voiture_pct` — taux de ménages avec au moins un véhicule (proxy demande EV) (%)
  - `tx_faible_revenu_pct` — taux de population sous le seuil de faible revenu MBM 2021 (%)
- **Utilisation** : Corrélation Pearson (couverture ↔ 4 variables), score de priorité composite, analyse d'équité socio-économique
- **Intégration** : Valeurs lues dans le backend Django (`_DEMO_DATA` dict, `views.py`) ; endpoints `/api/equity/`, `/api/correlation/`, `/api/priorite/`
- **Date d'acquisition** : Recensement 2021 (données publiées février 2022)
- **Note** : Les 15 villes reconstituées (Beaconsfield, Kirkland, Pointe-Claire, etc.) ne sont pas incluses car leurs données socio-démographiques ne font pas partie des tableaux d'arrondissements de la Ville de Montréal.
- **Citation** : Statistique Canada. *Recensement de la population 2021 — Profil des subdivisions de recensement*. Gouvernement du Canada. CC-BY 4.0.

## 5. Parcs et espaces verts de Montréal
- **Fichier** : `vectors/parcs_montreal.geojson`
- **Organisation** : Ville de Montréal — Direction des grands parcs et de la nature en ville
- **Source** : Données Québec — *Grands parcs, parcs d'arrondissements et espaces publics*
- **Licence** : CC-BY 4.0
- **Projection** : WGS84 (EPSG:4326) — centroïdes des polygones sources
- **Contenu original** : Polygones de tous les parcs de l'île, incluant les grands parcs, parcs d'arrondissements et espaces publics
- **Filtrage appliqué** : superficie > 0.1 ha ; exclusion des entités sans coordonnées valides
- **Contenu retenu** : 1 541 parcs avec `nom`, `superficie_ha`, `typo` (type de parc), coordonnées point (centroïde)
- **Utilisation** : Requête spatiale « parcs sans couverture adéquate » (< N bornes à 500 m) via LEFT JOIN PostGIS
- **Date d'acquisition** : 10 juillet 2026
- **Citation** : Ville de Montréal. *Grands parcs, parcs d'arrondissements et espaces publics*, Données Québec. CC-BY 4.0. Consulté le 10 juillet 2026.

## 6. Établissements alimentaires (épiceries, marchés, supermarchés)
- **Fichier** : `vectors/epiceries_montreal.geojson`
- **Organisation** : Ville de Montréal — Direction de la santé environnementale et des affaires réglementaires
- **Source** : Données Québec — *Établissements alimentaires*
- **Licence** : CC-BY 4.0
- **Projection** : WGS84 (EPSG:4326)
- **Contenu original** : Tous les établissements alimentaires déclarés à Montréal (épiceries, boucheries, marchés, supermarchés, dépanneurs, etc.)
- **Filtrage appliqué** : type contenant 'picerie', 'march' ou 'Aliments' ; statut = 'Ouvert' ; coordonnées valides dans les limites de l'île
- **Contenu retenu** : 3 010 établissements avec `nom`, `type`, `adresse`, coordonnées point
- **Utilisation** : Requête spatiale « épiceries sans borne à proximité » (NOT EXISTS + CROSS JOIN LATERAL / KNN `<->`) via PostGIS
- **Date d'acquisition** : 10 juillet 2026
- **Citation** : Ville de Montréal. *Établissements alimentaires*, Données Québec. CC-BY 4.0. Consulté le 10 juillet 2026.

## 7. Tracés des lignes de bus et de métro (STM)
- **Fichiers** : `vectors/stm_sig/stm_arrets_sig.shp`, `vectors/stm_sig/stm_lignes_sig.shp`
- **Organisation** : Société de transport de Montréal (STM)
- **Source** : Données Québec
- **Licence** : CC-BY 4.0 — **attribution obligatoire à la STM**
- **Projection** : NAD83 / MTM zone 8 (EPSG:32188) → **reprojetée en WGS84 lors de l'import**
- **Mise à jour** : Trimestrielle
- **Contenu** : 8 789 arrêts (bus + métro), tracés des lignes
- **Filtrage métro** : arrêts avec `stop_url` contenant "metro" et `loc_type = 0`
- **Date d'acquisition** : 7 juillet 2026
- **Citation** : SOCIÉTÉ DE TRANSPORT DE MONTRÉAL. *Tracés des lignes de bus et de métro*, Données Québec, 2016, mis à jour le 06 juillet 2026.

---

## Notes techniques

| Donnée | CRS source | CRS stockage | Conversion |
|---|---|---|---|
| Bornes de recharge | WGS84 | WGS84 (EPSG:4326) | Aucune |
| Arrondissements | WGS84 | WGS84 (EPSG:4326) | Aucune |
| Parcs (centroïdes) | WGS84 | WGS84 (EPSG:4326) | Centroïde calculé depuis polygone source |
| Épiceries | WGS84 | WGS84 (EPSG:4326) | Aucune |
| STM arrêts/lignes | NAD83 MTM8 (EPSG:32188) | WGS84 (EPSG:4326) | Via `gdf.to_crs(epsg=4326)` |
| Buffers 500m | — | WGS84 (EPSG:4326) | Calcul en MTM8, retour WGS84 |

**Calcul des buffers** : Les zones de couverture de 500m sont calculées en EPSG:32188 (projection métrique) pour garantir la précision des distances, puis reprojetées en WGS84 pour le stockage et l'affichage.

---

*Toutes les données sont sous licence CC-BY 4.0 — attribution obligatoire dans tout document ou publication.*
