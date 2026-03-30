-- Migration 038: Renommage code categorie T (Technicien) -> L (Leader)
-- Date: 2026-03-30

UPDATE personnel_infos SET categorie = 'L' WHERE categorie = 'T';
