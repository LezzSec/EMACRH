-- Migration 039: Ajout colonne lieu_accident dans medical_accident_travail
ALTER TABLE `medical_accident_travail`
    ADD COLUMN `lieu_accident` VARCHAR(255) DEFAULT NULL
        COMMENT 'Lieu / localisation / poste de travail au moment de l''accident'
    AFTER `jour_semaine`;
