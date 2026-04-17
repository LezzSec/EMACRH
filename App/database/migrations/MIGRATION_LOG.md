# MIGRATION_LOG — EMAC

## Système de tracking

Les migrations sont tracées **par nom de fichier** dans la table `schema_migrations`.
Seuls les fichiers correspondant au pattern `^\d{3}_.*\.sql$` sont pris en compte par le CLI.

```bash
python -m cli migrate --status        # Voir le statut de chaque migration
python -m cli migrate --apply-all     # Appliquer toutes les migrations en attente
python -m cli migrate --mark-applied-all  # Marquer comme appliquées sans exécuter
python -m cli migrate --apply 047_add_document_id_to_formation.sql
```

---

## Migrations numérotées (001 – 050)

> Les préfixes 001, 002 et 003 sont dupliqués (voir section "Doublons"). Le tracking par nom de fichier rend cela non-problématique.

| Fichier | Date | Description |
|---------|------|-------------|
| `001_add_performance_indexes.sql` | 2026-01-07 | Ajout de 29 index de performance sur 9 tables |
| `001_add_user_management.sql` | 2025-12-17 | Tables roles, utilisateurs, permissions, logs_connexion |
| `002_add_document_entity_links.sql` | 2026-01-19 | Colonnes pour lier un document à une entité |
| `002_add_document_event_rules.sql` | 2026-01-27 | Système de règles pour le déclenchement automatique de documents |
| `002_rename_contrat_operateur_id.sql` | 2026-02-26 | Renommage operateur_id dans la table contrat |
| `003_add_rh_tables.sql` | 2026-01-19 | Tables RH (validite, personnel_infos, etc.) |
| `003_add_user_permission_overrides.sql` | 2026-01-20 | Overrides de permissions par utilisateur (système puzzle) |
| `004_add_unique_matricule.sql` | — | Contrainte UNIQUE sur personnel.matricule |
| `005_complete_personnel_infos.sql` | 2026-01-21 | Colonnes complémentaires pour personnel_infos |
| `006_complete_contrat.sql` | 2026-01-21 | Colonnes complémentaires pour la table contrat |
| `007_add_medical_tables.sql` | 2026-01-21 | Tables suivi médical (medical, medical_visite, accidents) |
| `008_add_vie_salarie_tables.sql` | 2026-01-21 | Tables vie du salarié (sanctions, alcoolémie, entretiens) |
| `010_add_features_system.sql` | 2026-01-27 | Nouveau système de permissions granulaire avec features atomiques |
| `011_add_batch_operations.sql` | 2026-01-28 | Tables pour tracker les opérations batch |
| `012_add_failed_login_attempts.sql` | 2026-01-30 | Table logs_tentatives_connexion |
| `013_add_competences_transversales.sql` | 2026-02-02 | Tables compétences transversales et assignations |
| `014_add_formations_features.sql` | 2026-02-03 | Permissions pour la gestion des formations |
| `015_add_numero_ss.sql` | 2026-02-05 | Ajout du numéro de sécurité sociale dans personnel_infos |
| `016_rename_operateur_id_to_personnel_id.sql` | 2026-02-05 | Renommage operateur_id → personnel_id dans personnel_infos |
| `017_fix_missing_columns.sql` | 2026-02-12 | Colonnes details et source dans historique ; table logs_tentatives_connexion |
| `018_documents_blob_storage.sql` | 2026-02-16 | Colonne LONGBLOB contenu_fichier dans la table documents |
| `019_templates_blob_storage.sql` | 2026-02-16 | Colonne LONGBLOB dans documents_templates |
| `020_add_rh_domain_features.sql` | 2026-02-17 | Features déclarations, médical et vie salarié |
| `021_create_app_user.sql` | 2026-02-18 | Compte MySQL applicatif (remplace root) |
| `022_add_niveau2_document_rules.sql` | 2026-02-23 | Règles document déclenchées au passage niveau 2 |
| `023_add_evaluation_overdue_rules.sql` | 2026-02-24 | Règles alerte évaluation en retard |
| `024_add_evaluation_planned_rules.sql` | 2026-02-24 | Règles alerte évaluation à planifier |
| `025_add_niveau1_document_rules.sql` | 2026-02-24 | Règles document niveau 1 |
| `026_niveau1_add_nouvel_operateur_docs.sql` | 2026-02-24 | Documents "nouvel opérateur" au retour niveau 1 |
| `027_conditionner_nouvel_operateur_niveau1.sql` | 2026-03-02 | Conditionnement documents Consignes générales / Formation initiale |
| `028_add_documents_formation_polyvalence.sql` | 2026-03-05 | Table pour stocker les documents de formation associés à polyvalence |
| `029_add_absence_document_category.sql` | 2026-03-10 | Catégorie Absence dans le système de documents |
| `030_rename_operateur_id_to_personnel_id.sql` | 2026-03-16 | Renommage complet operateur_id → personnel_id dans 14 tables et 6 vues |
| `031_add_categorie_service_personnel_infos.sql` | 2026-03-18 | Colonnes categorie et service dans personnel_infos |
| `032_add_mutuelle_table.sql` | — | Table mutuelle (complémentaire santé) |
| `033_add_formation_fields.sql` | 2026-03-23 | Champs complémentaires dans la table formation |
| `034_add_taux_horaire_personnel_infos.sql` | 2026-03-25 | Colonne taux_horaire dans personnel_infos |
| `035_add_type_formation.sql` | 2026-03-25 | Table type_formation |
| `036_add_tranche_formation.sql` | 2026-03-25 | Table tranche_formation |
| `037_add_catalogue_formation.sql` | 2026-03-25 | Table catalogue_formation |
| `038_rename_categorie_T_to_L.sql` | 2026-03-30 | Renommage de la valeur catégorie T → L |
| `039_add_lieu_accident.sql` | — | Colonne lieu_accident dans medical_accident_travail |
| `040_add_prochaine_convocation_visite.sql` | — | Colonne prochaine_convocation dans medical_visite |
| `041_fix_mutuelle_missing_columns.sql` | — | Colonnes manquantes dans la table mutuelle |
| `042_add_mobilite_tables.sql` | 2026-04-13 | Tables mobilité (véhicule, trajets, remboursements) |
| `043_update_mobilite_tables.sql` | 2026-04-13 | Mises à jour des tables mobilité |
| `044_add_vehicule_table.sql` | 2026-04-13 | Table véhicule |
| `045_add_mobilite_feature.sql` | 2026-04-13 | Feature permission mobilité |
| `046_add_app_modules.sql` | — | Table app_modules (menu dynamique) |
| `047_add_document_id_to_formation.sql` | 2026-01-14 | FK document_id dans la table formation (attestations) |
| `048_create_all_missing_views.sql` | 2026-02-09 | Vues v_contrat_anciennete, v_contrats_fin_proche, v_suivi_medical, v_vie_salarie_recap |
| `049_schema_absences_conges.sql` | — | Tables type_absence, solde_conges, demande_absence, jours_feries ; vues absences |
| `050_schema_gestion_documentaire.sql` | 2025-12-05 | Tables documents_rh, documents_metadata, documents_acces_log ; vues documents |
| `051_add_distance_domicile.sql` | 2026-04-16 | Colonnes latitude, longitude, distance_domicile_km, duree_trajet_min, distance_calculee_at dans personnel_infos ; index idx_personnel_distance |

---

## Trou dans la numérotation

Il n'y a pas de `009_*.sql`. La séquence passe directement de 008 à 010. Le numéro 9 n'a jamais été attribué.

---

## Doublons de préfixes

Les préfixes 001, 002 et 003 sont partagés entre plusieurs fichiers. Cela n'est **pas un problème** : le CLI trace les migrations par **nom de fichier complet**, pas par numéro seul. Chaque fichier a sa propre entrée dans `schema_migrations`.

| Préfixe | Fichiers concernés | Raison du doublon |
|---------|--------------------|-------------------|
| 001 | `001_add_performance_indexes.sql`, `001_add_user_management.sql` | Deux séries de migrations créées indépendamment en début de projet |
| 002 | `002_add_document_entity_links.sql`, `002_add_document_event_rules.sql`, `002_rename_contrat_operateur_id.sql` | Idem — ajouts concurrents sur des domaines distincts |
| 003 | `003_add_rh_tables.sql`, `003_add_user_permission_overrides.sql` | Idem |

**Règle** : ne pas renommer ces fichiers — ils sont déjà tracés en production sous leur nom actuel. Toute nouvelle migration doit utiliser le prochain numéro disponible (**052**).

---

## Fichiers archivés (`archive/`)

Ces fichiers ont été déplacés dans `archive/` car leur contenu est redondant avec les migrations numérotées ou n'a plus d'utilité opérationnelle.

| Fichier | Raison de l'archivage |
|---------|-----------------------|
| `add_documents_templates.sql` | Crée la table `documents_templates` (déjà en base) ; migrations 002/019/022-027 s'appuient dessus |
| `add_historique_columns.sql` | Colonnes `table_name`, `record_id`, `utilisateur` déjà présentes en base live (confirmé par 017) ; `details` et `source` couverts par `017_fix_missing_columns.sql` |
| `apply_sirh_migrations.sql` | Script agrégateur des migrations 006, 007, 008 — déjà couvertes par leurs fichiers numérotés respectifs |
| `create_missing_views.sql` | Crée `v_alertes_medicales` et `v_alertes_entretiens` — version partielle, vues créées séparément dans le code applicatif si nécessaire |
| `migrate_operateurs_to_personnel.sql` | Version simple du renommage operateurs → personnel, remplacée par la version safe |
| `migrate_operateurs_to_personnel_safe.sql` | Migration one-shot déjà appliquée ; renommage complet couvert par `030_rename_operateur_id_to_personnel_id.sql` |
| `README_MIGRATION.md` | Guide spécifique à la migration operateurs → personnel, opération terminée |

> **Note** : `create_missing_views.sql` (archivé) crée des vues *différentes* de `048_create_all_missing_views.sql` (v_alertes_medicales, v_alertes_entretiens). Ces vues ne sont pas couvertes par une migration numérotée. Si elles sont nécessaires, les intégrer dans une migration 051+.

---

## Scripts de rollback (`rollback/`)

| Fichier | Description |
|---------|-------------|
| `rollback_personnel_to_operateurs.sql` | Annule la migration operateurs → personnel (usage exceptionnel uniquement) |

---

## Commandes utiles

```bash
# Voir le statut des migrations
python -m cli migrate --status

# Appliquer toutes les migrations en attente
python -m cli migrate --apply-all

# Marquer comme appliquées sans exécuter (base existante)
python -m cli migrate --mark-applied-all

# Appliquer une migration spécifique
python -m cli migrate --apply 047_add_document_id_to_formation.sql
```

---

## Créer une nouvelle migration

1. Numéroter à partir de **051**
2. Nommer : `051_description_courte.sql`
3. Utiliser `CREATE TABLE IF NOT EXISTS` / `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`
4. Ajouter en en-tête :
   ```sql
   -- Migration NNN : Titre
   -- Date : YYYY-MM-DD
   -- Description : Ce que fait cette migration
   ```
5. Documenter dans ce fichier (tableau "Migrations numérotées")
