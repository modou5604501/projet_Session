# Sources des données — GeoRisk Sentinel (Bornes de recharge Montréal)

## 1. Bornes de recharge publiques
- **Fichier** : `vectors/bornes_recharge_montreal.geojson`
- **Organisation** : Ville de Montréal
- **Source** : Données Québec
- **Licence** : Ouverte (CC-BY 4.0)
- **Projection** : WGS84 (CRS84)
- **Mise à jour** : En continu
- **Citation** : Ville de Montréal. *Bornes de recharge publiques*, Données Québec.

## 2. Statistiques d'utilisation des bornes 2025
- **Fichier** : `vectors/chargeurs_statistiques_2025.csv`
- **Organisation** : Ville de Montréal
- **Source** : Données Québec
- **Licence** : Ouverte (CC-BY 4.0)
- **Format** : CSV
- **Citation** : Ville de Montréal. *Statistiques d'utilisation des bornes de recharge*, Données Québec, 2025.

## 3. Limites administratives de l'agglomération de Montréal (arrondissements)
- **Fichier** : `vectors/arrondissements_montreal.geojson`
- **Organisation** : Ville de Montréal
- **Source** : Données Québec
- **Licence** : CC-BY 4.0
- **Projection** : WGS84 (GeoJSON WGS 84)
- **Dernière modification** : 2026-06-30
- **Citation** : Ville de Montréal. *Limites administratives de l'agglomération de Montréal*, Données Québec, mis à jour le 30 juin 2026.

## 4. Tracés des lignes de bus et de métro (STM)
- **Fichier** : `vectors/stm/` (ZIP extrait)
- **Organisation** : Société de transport de Montréal (STM)
- **Source** : Données Québec
- **Licence** : CC-BY 4.0 — **attribution obligatoire à la STM**
- **Projection** : NAD83 / MTM zone 8 → **à convertir en WGS84**
- **Mise à jour** : Trimestrielle
- **Contenu** : Tracés des lignes + arrêts (bus et métro)
- **Citation** : SOCIÉTÉ DE TRANSPORT DE MONTRÉAL. *Tracés des lignes de bus et de métro*, Données Québec, 2016, mis à jour le 06 juillet 2026.

---
*Note : Toutes les données en NAD83/MTM8 doivent être reprojetées en WGS84 (EPSG:4326) avant import dans PostGIS/Leaflet.*
