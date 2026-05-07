-- 057_add_feature_metadata.sql
-- Externalise les metadata UI des permissions hors de feature_puzzle.py.

ALTER TABLE features
    ADD COLUMN IF NOT EXISTS sensitivity ENUM('Standard', 'Sensible', 'Admin') NOT NULL DEFAULT 'Standard' AFTER description,
    ADD COLUMN IF NOT EXISTS screens VARCHAR(255) DEFAULT NULL AFTER sensitivity;

UPDATE features
SET sensitivity = CASE
        WHEN module = 'Admin' OR key_code LIKE 'admin.%' THEN 'Admin'
        WHEN key_code IN (
            'rh.bulk_operations',
            'rh.bulk_operations.formations',
            'rh.bulk_operations.absences',
            'rh.bulk_operations.medical',
            'rh.personnel.create',
            'rh.personnel.edit',
            'rh.personnel.delete',
            'rh.contrats.edit',
            'rh.contrats.delete',
            'rh.documents.edit',
            'rh.templates.edit',
            'rh.formations.edit',
            'rh.formations.delete',
            'rh.competences.catalogue',
            'rh.competences.edit',
            'rh.competences.delete',
            'rh.medical.edit',
            'rh.vie_salarie.edit',
            'rh.declarations.edit',
            'production.evaluations.edit',
            'production.polyvalence.edit',
            'production.postes.edit',
            'planning.absences.edit'
        ) THEN 'Sensible'
        ELSE 'Standard'
    END,
    screens = CASE key_code
        WHEN 'rh.view' THEN 'Menu RH principal'
        WHEN 'rh.bulk_operations' THEN 'Gestion du personnel > Operations en masse'
        WHEN 'rh.bulk_operations.formations' THEN 'Gestion du personnel > Formations en masse'
        WHEN 'rh.bulk_operations.absences' THEN 'Gestion du personnel > Absences en masse'
        WHEN 'rh.bulk_operations.medical' THEN 'Gestion du personnel > Visites medicales en masse'
        WHEN 'rh.personnel.view' THEN 'Gestion du personnel > liste'
        WHEN 'rh.personnel.create' THEN 'Gestion du personnel > Ajouter un employe'
        WHEN 'rh.personnel.edit' THEN 'Gestion du personnel > Modifier fiche'
        WHEN 'rh.personnel.delete' THEN 'Gestion du personnel > Desactiver / supprimer'
        WHEN 'rh.contrats.view' THEN 'Onglet Contrats > consultation'
        WHEN 'rh.contrats.edit' THEN 'Onglet Contrats > creer / modifier'
        WHEN 'rh.contrats.delete' THEN 'Onglet Contrats > supprimer'
        WHEN 'rh.documents.view' THEN 'Onglet Documents > consultation'
        WHEN 'rh.documents.edit' THEN 'Onglet Documents > ajouter / modifier'
        WHEN 'rh.documents.print' THEN 'Onglet Documents > generer / imprimer'
        WHEN 'rh.templates.view' THEN 'Modeles de documents > consultation'
        WHEN 'rh.templates.edit' THEN 'Modeles de documents > creer / modifier'
        WHEN 'rh.formations.view' THEN 'Formations > consultation'
        WHEN 'rh.formations.edit' THEN 'Formations > ajouter / modifier'
        WHEN 'rh.formations.delete' THEN 'Formations > supprimer'
        WHEN 'rh.competences.view' THEN 'Competences > consultation'
        WHEN 'rh.competences.catalogue' THEN 'Competences > catalogue'
        WHEN 'rh.competences.edit' THEN 'Competences > modifier niveaux'
        WHEN 'rh.competences.delete' THEN 'Competences > supprimer'
        WHEN 'rh.medical.edit' THEN 'Visites medicales > creer / modifier'
        WHEN 'rh.vie_salarie.edit' THEN 'Sanctions / entretiens > creer / modifier'
        WHEN 'rh.declarations.edit' THEN 'Declarations > creer / modifier'
        WHEN 'rh.mobilite.edit' THEN 'Mobilite / vehicule > modifier'
        WHEN 'production.view' THEN 'Menu Production principal'
        WHEN 'production.evaluations.view' THEN 'Evaluations > consultation'
        WHEN 'production.evaluations.edit' THEN 'Evaluations > planifier / modifier'
        WHEN 'production.polyvalence.view' THEN 'Matrice de polyvalence > consultation'
        WHEN 'production.polyvalence.edit' THEN 'Matrice de polyvalence > modifier niveaux'
        WHEN 'production.postes.view' THEN 'Postes de travail > consultation'
        WHEN 'production.postes.edit' THEN 'Postes de travail > creer / modifier / supprimer'
        WHEN 'production.grilles.view' THEN 'Grilles de competences > consultation'
        WHEN 'production.grilles.export' THEN 'Grilles de competences > export Excel / PDF'
        WHEN 'planning.view' THEN 'Menu Planning principal'
        WHEN 'planning.absences.view' THEN 'Absences > consultation'
        WHEN 'planning.absences.edit' THEN 'Absences > creer / modifier'
        WHEN 'admin.view' THEN 'Menu Administration principal'
        WHEN 'admin.users.view' THEN 'Gestion utilisateurs > liste'
        WHEN 'admin.users.create' THEN 'Gestion utilisateurs > creer un compte'
        WHEN 'admin.users.edit' THEN 'Gestion utilisateurs > modifier un compte'
        WHEN 'admin.users.delete' THEN 'Gestion utilisateurs > supprimer un compte'
        WHEN 'admin.permissions' THEN 'Gestion des permissions'
        WHEN 'admin.roles.edit' THEN 'Permissions > modifier droits des roles'
        WHEN 'admin.historique.view' THEN 'Historique / logs > consultation'
        WHEN 'admin.historique.export' THEN 'Historique / logs > export'
        ELSE screens
    END;
