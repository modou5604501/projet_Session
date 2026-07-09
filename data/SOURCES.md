# Sources des données — GeoRisk Sentinel
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

## 4. Référentiel quartiers / revenu médian (StatCan Recensement 2021)
- **Fichier** : `quartiers_reference_habitation.csv`
- **Organisation** : Statistique Canada / Ville de Montréal
- **Source** : Données Québec — Commande personnalisée du recensement 2021 du Service de la stratégie immobilière et de l'habitation
- **Licence** : CC-BY 4.0
- **Format** : CSV (séparateur `;`)
- **Contenu** : 75 quartiers montréalais avec leur numéro et nom d'arrondissement (Num Arr, Nom Arr, Num Quartier, Nom Quartier)
- **Utilisation** : Référentiel de concordance quartier → arrondissement ; valeurs de revenu médian des ménages par arrondissement pour l'analyse d'équité socio-économique
- **Date d'acquisition** : 8 juillet 2026
- **Citation** : Ville de Montréal. *Commande personnalisée du recensement 2021 — Service de la stratégie immobilière et de l'habitation*, Données Québec. Consulté le 8 juillet 2026.

## 5. Tracés des lignes de bus et de métro (STM)
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
| STM arrêts/lignes | NAD83 MTM8 (EPSG:32188) | WGS84 (EPSG:4326) | Via `gdf.to_crs(epsg=4326)` |
| Buffers 500m | — | WGS84 (EPSG:4326) | Calcul en MTM8, retour WGS84 |

**Calcul des buffers** : Les zones de couverture de 500m sont calculées en EPSG:32188 (projection métrique) pour garantir la précision des distances, puis reprojetées en WGS84 pour le stockage et l'affichage.

---

*Toutes les données sont sous licence CC-BY 4.0 — attribution obligatoire dans tout document ou publication.*
