-- Migration 040: Ajout colonne date_prochaine_convocation dans medical_visite
ALTER TABLE `medical_visite`
    ADD COLUMN `date_prochaine_convocation` DATE DEFAULT NULL
        COMMENT 'Date à laquelle la convocation pour la prochaine visite est prévue'
    AFTER `prochaine_visite`;
