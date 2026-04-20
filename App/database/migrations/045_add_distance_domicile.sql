-- Migration 045 : Distance domicile/entreprise (mairie OSM + centroïde commune)
-- Date : 2026-04-20
-- Description : Ajoute les coordonnées de la commune du personnel,
--               la mairie (OSM townhall), et les deux distances
--               domicile-entreprise associées.
--
-- Deux distances sont calculées :
--   1. distance_commune_km  : centroïde commune → centroïde commune entreprise
--      (données agrégées / exports RH)
--   2. distance_mairie_km   : mairie commune → mairie commune entreprise
--      (affichage fiche individuelle)
--
-- RGPD : l'adresse précise du personnel n'est jamais géocodée.
--        Seule la commune (CP + ville) alimente ces calculs.

-- ── Commune (centroïde geo.api.gouv.fr, pour les stats) ──────────────
ALTER TABLE personnel_infos
    ADD COLUMN IF NOT EXISTS code_insee_commune VARCHAR(5) DEFAULT NULL
        COMMENT 'Code INSEE de la commune de domicile',
    ADD COLUMN IF NOT EXISTS commune_lat DECIMAL(10,7) DEFAULT NULL
        COMMENT 'Latitude du centroïde commune domicile',
    ADD COLUMN IF NOT EXISTS commune_lon DECIMAL(10,7) DEFAULT NULL
        COMMENT 'Longitude du centroïde commune domicile',
    ADD COLUMN IF NOT EXISTS distance_commune_km DECIMAL(6,2) DEFAULT NULL
        COMMENT 'Distance routière centroïde-à-centroïde en km (stats)',
    ADD COLUMN IF NOT EXISTS duree_trajet_commune_min INT DEFAULT NULL
        COMMENT 'Durée de trajet entre centroïdes en minutes';

-- ── Mairie (OSM Overpass, pour affichage utilisateur) ────────────────
ALTER TABLE personnel_infos
    ADD COLUMN IF NOT EXISTS mairie_lat DECIMAL(10,7) DEFAULT NULL
        COMMENT 'Latitude de la mairie de la commune (OSM townhall)',
    ADD COLUMN IF NOT EXISTS mairie_lon DECIMAL(10,7) DEFAULT NULL
        COMMENT 'Longitude de la mairie (OSM townhall)',
    ADD COLUMN IF NOT EXISTS distance_mairie_km DECIMAL(6,2) DEFAULT NULL
        COMMENT 'Distance routière mairie-à-mairie en km (affichage fiche)',
    ADD COLUMN IF NOT EXISTS duree_trajet_mairie_min INT DEFAULT NULL
        COMMENT 'Durée de trajet entre mairies en minutes';

-- ── Index ─────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_personnel_distance_commune
    ON personnel_infos(distance_commune_km);
CREATE INDEX IF NOT EXISTS idx_personnel_distance_mairie
    ON personnel_infos(distance_mairie_km);
CREATE INDEX IF NOT EXISTS idx_personnel_code_insee
    ON personnel_infos(code_insee_commune);
