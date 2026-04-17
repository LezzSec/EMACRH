-- Migration 051 : Distance domicile/entreprise
-- Date : 2026-04-16
-- Description : Ajoute les coordonnées GPS et la distance routière
--               domicile-entreprise dans personnel_infos.

ALTER TABLE personnel_infos
    ADD COLUMN IF NOT EXISTS latitude DECIMAL(10,7) DEFAULT NULL
        COMMENT 'Latitude du domicile (géocodage)',
    ADD COLUMN IF NOT EXISTS longitude DECIMAL(10,7) DEFAULT NULL
        COMMENT 'Longitude du domicile (géocodage)',
    ADD COLUMN IF NOT EXISTS distance_domicile_km DECIMAL(6,2) DEFAULT NULL
        COMMENT 'Distance routière domicile-entreprise en km',
    ADD COLUMN IF NOT EXISTS duree_trajet_min INT DEFAULT NULL
        COMMENT 'Durée de trajet routier en minutes',
    ADD COLUMN IF NOT EXISTS distance_calculee_at TIMESTAMP NULL DEFAULT NULL
        COMMENT 'Date du dernier calcul de distance';

-- Index pour les requêtes de statistiques (filtrer par distance)
CREATE INDEX IF NOT EXISTS idx_personnel_distance
    ON personnel_infos(distance_domicile_km);
