-- GeoCharge Montréal — Tables des points d'intérêt (POI)
-- Phase 2 : parcs, épiceries, score de priorité

CREATE TABLE IF NOT EXISTS parcs (
    id          SERIAL PRIMARY KEY,
    nom         VARCHAR(200),
    superficie_ha FLOAT DEFAULT 0,
    typo        VARCHAR(100),
    geom        GEOMETRY(POINT, 4326)
);

CREATE TABLE IF NOT EXISTS epiceries (
    id      SERIAL PRIMARY KEY,
    nom     VARCHAR(200),
    type    VARCHAR(100),
    adresse VARCHAR(300),
    geom    GEOMETRY(POINT, 4326)
);

CREATE TABLE IF NOT EXISTS reseau_routier (
    id          INTEGER PRIMARY KEY,
    classe      INTEGER,
    type_route  VARCHAR(50),
    nom_voie    VARCHAR(200),
    type_voie   VARCHAR(50),
    arrondissement VARCHAR(100),
    sens_circulation INTEGER,
    geom        GEOMETRY(LINESTRING, 4326)
);

-- Index spatiaux
CREATE INDEX IF NOT EXISTS idx_parcs_geom        ON parcs          USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_epiceries_geom    ON epiceries       USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_reseau_geom       ON reseau_routier  USING GIST(geom);
