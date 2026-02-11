# Création des vues manquantes - 2026-02-09

## Résumé

Les vues SQL manquantes ont été créées pour le bon fonctionnement de l'application EMAC.

## État des vues

### ✅ Vues créées (17/20)

| Vue | Description | Migration source |
|-----|-------------|-----------------|
| `v_absences_details` | Détails des absences | schema_absences_conges.sql |
| `v_alertes_entretiens` | **Alertes entretiens EPP/EAP en retard** | 008_add_vie_salarie_tables.sql |
| `v_alertes_medicales` | **Alertes visites médicales en retard** | 007_add_medical_tables.sql |
| `v_batch_operations_stats` | Statistiques des opérations batch | 011_add_batch_operations.sql |
| `v_contrat_anciennete` | **Calcul de l'ancienneté par contrat** | 006_complete_contrat.sql |
| `v_contrats_fin_proche` | **Contrats arrivant à expiration** | 006_complete_contrat.sql |
| `v_document_rules_with_templates` | Règles documentaires avec templates | 002_add_document_event_rules.sql |
| `v_documents_complet` | Documents avec infos complètes | (déjà existante) |
| `v_documents_expiration_proche` | Documents expirant bientôt | (déjà existante) |
| `v_documents_stats_operateur` | Stats documents par opérateur | (déjà existante) |
| `v_historique_polyvalence_complet` | Historique complet polyvalence | (déjà existante) |
| `v_personnel_age` | Calcul de l'âge du personnel | 005_complete_personnel_infos.sql |
| `v_personnel_anciennete` | Calcul de l'ancienneté du personnel | 005_complete_personnel_infos.sql |
| `v_soldes_disponibles` | Soldes de congés disponibles | schema_absences_conges.sql |
| `v_stats_absences` | Statistiques des absences | schema_absences_conges.sql |
| `v_suivi_medical` | **Suivi médical complet (VIP, RQTH, OETH)** | 007_add_medical_tables.sql |
| `v_vie_salarie_recap` | **Récap vie du salarié (sanctions, entretiens)** | 008_add_vie_salarie_tables.sql |

### ⚠️ Vues manquantes (3/20) - Dépendances non satisfaites

| Vue | Raison | Table manquante |
|-----|--------|----------------|
| `v_documents_employes` | Table `documents_rh` n'existe pas | `documents_rh` |
| `v_documents_expiration_alerte` | Table `documents_rh` n'existe pas | `documents_rh` |
| `v_documents_stats` | Table `documents_rh` n'existe pas | `documents_rh` |

**Note**: Ces vues seront créées automatiquement lorsque le module de gestion documentaire RH sera déployé.

## Fichiers créés

### Migrations SQL

1. **[create_missing_views.sql](../../App/database/migrations/create_missing_views.sql)**
   - Crée `v_alertes_medicales`
   - Crée `v_alertes_entretiens`

2. **[create_all_missing_views.sql](../../App/database/migrations/create_all_missing_views.sql)**
   - Crée `v_contrat_anciennete`
   - Crée `v_contrats_fin_proche`
   - Crée `v_suivi_medical`
   - Crée `v_vie_salarie_recap`

### Scripts Python

1. **[apply_missing_views.py](../../App/scripts/apply_missing_views.py)**
   - Applique les vues d'alertes (médicales + entretiens)

2. **[apply_all_missing_views.py](../../App/scripts/apply_all_missing_views.py)**
   - Applique toutes les vues manquantes (contrats + médical + vie salarié)

3. **[check_missing_views.py](../../App/scripts/check_missing_views.py)**
   - Vérifie l'état de toutes les vues attendues

4. **[test_views.py](../../App/scripts/test_views.py)**
   - Teste le fonctionnement des vues créées

## Corrections apportées

### 1. Correction de la colonne de jointure (personnel_infos)

**Problème**: La vue `v_alertes_entretiens` utilisait `pi.operateur_id` alors que la colonne s'appelle `pi.personnel_id`.

**Fichiers corrigés**:
- `create_missing_views.sql`
- `008_add_vie_salarie_tables.sql`

**Changement**:
```sql
-- ❌ Avant
LEFT JOIN personnel_infos pi ON p.id = pi.operateur_id

-- ✅ Après
LEFT JOIN personnel_infos pi ON p.id = pi.personnel_id
```

## Utilisation

### Vérifier l'état des vues

```bash
cd App
py scripts/check_missing_views.py
```

### Tester les vues

```bash
cd App
py scripts/test_views.py
```

### Réappliquer les vues (si nécessaire)

```bash
cd App
py scripts/apply_all_missing_views.py
```

## Vues critiques pour l'application

### Alertes

- **`v_alertes_medicales`**: Utilisée par `medical_service.py` pour afficher les visites médicales en retard
- **`v_alertes_entretiens`**: Utilisée par `vie_salarie_service.py` pour afficher les entretiens professionnels en retard

### Contrats

- **`v_contrat_anciennete`**: Calcul de l'ancienneté des employés par contrat
- **`v_contrats_fin_proche`**: Alertes pour les contrats CDD/intérim arrivant à expiration

### Médical

- **`v_suivi_medical`**: Vue complète du suivi médical (VIP, RQTH, OETH, accidents du travail)

### Vie du salarié

- **`v_vie_salarie_recap`**: Récapitulatif des sanctions, contrôles, et entretiens

## Tests effectués

### Vues d'alertes médicales
```sql
SELECT * FROM v_alertes_medicales;
```
✅ **Résultat**: 0 alertes (aucune visite médicale en retard actuellement)

### Vues d'alertes entretiens
```sql
SELECT * FROM v_alertes_entretiens;
```
✅ **Résultat**: 0 alertes (aucun entretien en retard actuellement)

### Vues de contrats
```sql
SELECT * FROM v_contrat_anciennete LIMIT 5;
SELECT * FROM v_contrats_fin_proche;
```
✅ **Résultat**: Vues fonctionnelles

### Vues médicales et vie salarié
```sql
SELECT * FROM v_suivi_medical WHERE statut = 'ACTIF';
SELECT * FROM v_vie_salarie_recap;
```
✅ **Résultat**: Vues fonctionnelles

## Prochaines étapes

Pour créer les 3 vues manquantes, il faudra :

1. Déployer la migration `schema_gestion_documentaire.sql` qui crée la table `documents_rh`
2. Les vues `v_documents_*` seront alors créées automatiquement

## Logs d'exécution

```
=== SUCCES ===
Les vues ont ete creees avec succes!

=== VERIFICATION ===
  OK v_alertes_medicales existe
  OK v_alertes_entretiens existe
  OK v_contrat_anciennete existe
  OK v_contrats_fin_proche existe
  OK v_suivi_medical existe
  OK v_vie_salarie_recap existe
```

## Auteur

- Date: 2026-02-09
- Ticket: Création des vues manquantes pour l'application EMAC
- Impact: Correction des erreurs SQL lors du démarrage de l'application
