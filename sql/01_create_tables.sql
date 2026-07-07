-- GeoRisk Sentinel — Création des tables PostGIS
-- Zone d'étude : Sainte-Marthe-sur-le-Lac

-- Extension PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Table réseau électrique
CREATE TABLE IF NOT EXISTS electric_network (
    id SERIAL PRIMARY KEY,
    osm_id BIGINT,
    type VARCHAR(50),
    voltage INT,
    criticality VARCHAR(20) DEFAULT 'medium',
    geom GEOMETRY(GEOMETRY, 32198)
);

-- Table zones inondées
CREATE TABLE IF NOT EXISTS flood_zones (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50),
    date_detection DATE,
    recurrence INT,
    surface_ha FLOAT,
    geom GEOMETRY(MULTIPOLYGON, 32198)
);

-- Table analyse des risques
CREATE TABLE IF NOT EXISTS risk_analysis (
    id SERIAL PRIMARY KEY,
    infra_id INT REFERENCES electric_network(id),
    niveau_risque VARCHAR(20),
    distance_m FLOAT,
    date_analyse TIMESTAMP DEFAULT NOW()
);

-- Table alertes
CREATE TABLE IF NOT EXISTS alertes (
    id SERIAL PRIMARY KEY,
    niveau VARCHAR(20),
    message TEXT,
    infra_id INT REFERENCES electric_network(id),
    date_alerte TIMESTAMP DEFAULT NOW(),
    acquittee BOOLEAN DEFAULT FALSE
);

-- Index spatiaux
CREATE INDEX IF NOT EXISTS idx_electric_geom ON electric_network USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_flood_geom ON flood_zones USING GIST(geom);
