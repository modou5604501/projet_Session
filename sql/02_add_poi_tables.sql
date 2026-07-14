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

-- Index spatiaux
CREATE INDEX IF NOT EXISTS idx_parcs_geom    ON parcs     USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_epiceries_geom ON epiceries USING GIST(geom);
