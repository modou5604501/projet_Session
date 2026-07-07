-- GeoRisk Sentinel — Création des tables PostGIS
-- Projet : Bornes de recharge électrique à Montréal

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Bornes de recharge existantes
CREATE TABLE IF NOT EXISTS bornes_recharge (
    id              SERIAL PRIMARY KEY,
    nom             VARCHAR(200),
    type            VARCHAR(50),
    arrondissement  VARCHAR(100),
    nb_prises       INT DEFAULT 1,
    geom            GEOMETRY(POINT, 4326)
);

-- Zones de couverture (buffer 500m autour de chaque borne)
CREATE TABLE IF NOT EXISTS zones_couverture (
    id       SERIAL PRIMARY KEY,
    borne_id INT REFERENCES bornes_recharge(id) ON DELETE CASCADE,
    rayon_m  INT DEFAULT 500,
    geom     GEOMETRY(POLYGON, 4326)
);

-- Arrondissements de Montréal
CREATE TABLE IF NOT EXISTS arrondissements (
    id              SERIAL PRIMARY KEY,
    nom             VARCHAR(100),
    nb_bornes       INT DEFAULT 0,
    pct_couverture  FLOAT DEFAULT 0,
    geom            GEOMETRY(MULTIPOLYGON, 4326)
);

-- Stations de métro STM
CREATE TABLE IF NOT EXISTS stations_metro (
    id    SERIAL PRIMARY KEY,
    nom   VARCHAR(100),
    ligne VARCHAR(10),
    geom  GEOMETRY(POINT, 4326)
);

-- Index spatiaux
CREATE INDEX IF NOT EXISTS idx_bornes_geom     ON bornes_recharge  USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_couverture_geom ON zones_couverture USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_arrond_geom     ON arrondissements  USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_metro_geom      ON stations_metro   USING GIST(geom);
