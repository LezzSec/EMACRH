# Guide : Vérifier les formations assignées

Ce guide explique comment vérifier dans la base de données quels employés ont reçu des formations assignées (via bulk assignment ou manuellement).

## Méthode 1 : Script Python (Recommandé) ⚡

### Afficher les formations récentes

```bash
cd App
py scripts/check_formations.py --recent 20
```

### Rechercher par nom d'employé

```bash
py scripts/check_formations.py --nom DUPONT
py scripts/check_formations.py --nom DUPONT --prenom Jean
```

### Afficher les statistiques

```bash
py scripts/check_formations.py --stats
```

**Avantages** :
- Rapide et simple
- Pas besoin d'outils SQL externes
- Formatage lisible

---

## Méthode 2 : Requêtes SQL directes 🗄️

Ouvrez **MySQL Workbench**, **phpMyAdmin**, ou tout autre client SQL et utilisez les requêtes du fichier :

📁 `App/scripts/requetes_formations.sql`

### Requête la plus simple : Voir toutes les formations

```sql
SELECT
    f.id,
    CONCAT(p.nom, ' ', p.prenom) AS employe,
    f.intitule,
    f.organisme,
    f.date_debut,
    f.date_fin,
    f.statut,
    f.certificat_obtenu
FROM formation f
INNER JOIN personnel p ON f.operateur_id = p.id
ORDER BY f.id DESC;
```

### Voir qui a reçu une formation spécifique

```sql
SELECT
    CONCAT(p.nom, ' ', p.prenom) AS employe,
    p.statut,
    f.date_debut,
    f.statut AS statut_formation
FROM formation f
INNER JOIN personnel p ON f.operateur_id = p.id
WHERE f.intitule = 'Formation CACES'
ORDER BY p.nom;
```

---

## Méthode 3 : Interface EMAC (Future fonctionnalité) 🖥️

**Note** : Si vous souhaitez une interface graphique dans l'application EMAC pour consulter les formations, il faudrait développer un nouvel onglet ou dialog.

Fonctionnalités possibles :
- Liste de toutes les formations avec filtres
- Vue par employé
- Vue par type de formation
- Export Excel/PDF

---

## Structure de la table `formation`

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | int | Identifiant unique |
| `operateur_id` | int | ID de l'employé (FK → `personnel.id`) |
| `intitule` | varchar(255) | Nom de la formation |
| `organisme` | varchar(255) | Organisme formateur |
| `date_debut` | date | Date de début |
| `date_fin` | date | Date de fin |
| `duree_heures` | int | Durée en heures |
| `statut` | ENUM | 'Planifiée', 'En cours', 'Terminée', 'Annulée' |
| `certificat_obtenu` | tinyint(1) | 0 = Non, 1 = Oui |
| `cout` | decimal(10,2) | Coût de la formation |
| `commentaire` | text | Commentaire libre |

---

## Cas d'usage courants

### 1. Vérifier si un bulk assignment a fonctionné

```bash
# Via Python
py scripts/check_formations.py --recent 50

# Via SQL
SELECT COUNT(*) as total FROM formation;
```

### 2. Voir tous les employés formés à une compétence

```sql
SELECT
    CONCAT(p.nom, ' ', p.prenom) AS employe,
    f.statut,
    f.certificat_obtenu
FROM formation f
INNER JOIN personnel p ON f.operateur_id = p.id
WHERE f.intitule LIKE '%CACES%'
ORDER BY p.nom;
```

### 3. Trouver les employés sans formation

```sql
SELECT
    p.id,
    p.nom,
    p.prenom,
    p.statut
FROM personnel p
LEFT JOIN formation f ON p.id = f.operateur_id
WHERE f.id IS NULL AND p.statut = 'ACTIF'
ORDER BY p.nom;
```

### 4. Formations arrivant à expiration (certificats à renouveler)

```sql
SELECT
    CONCAT(p.nom, ' ', p.prenom) AS employe,
    f.intitule,
    f.date_fin,
    DATEDIFF(f.date_fin, CURDATE()) AS jours_restants
FROM formation f
INNER JOIN personnel p ON f.operateur_id = p.id
WHERE f.date_fin BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 60 DAY)
ORDER BY f.date_fin ASC;
```

---

## Dépannage

### Erreur : "Unknown column 'created_at'"

➜ Votre table `formation` n'a pas encore la colonne `created_at`.

**Solution** : Ajoutez-la avec cette migration SQL :

```sql
ALTER TABLE formation
ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;
```

### Aucune formation n'apparaît

➜ Vérifiez que :
1. La table `formation` existe : `SHOW TABLES LIKE 'formation';`
2. Les données ont été insérées : `SELECT COUNT(*) FROM formation;`
3. L'opération de bulk assignment a réussi (vérifiez les logs)

---

## Logs et traçabilité

Les opérations de bulk assignment sont tracées dans :

1. **Table `batch_operations`** : Suivi global de l'opération
   ```sql
   SELECT * FROM batch_operations ORDER BY created_at DESC LIMIT 10;
   ```

2. **Table `batch_operation_details`** : Détail par employé
   ```sql
   SELECT
       bod.personnel_id,
       CONCAT(p.nom, ' ', p.prenom) AS employe,
       bod.success,
       bod.error_message
   FROM batch_operation_details bod
   INNER JOIN personnel p ON bod.personnel_id = p.id
   WHERE bod.batch_id = <ID_BATCH>
   ORDER BY bod.created_at;
   ```

3. **Table `historique`** : Audit trail complet
   ```sql
   SELECT * FROM historique
   WHERE action LIKE '%FORMATION%'
   ORDER BY date_time DESC
   LIMIT 50;
   ```

---

## Fichiers de référence

- Script Python : [`App/scripts/check_formations.py`](../../App/scripts/check_formations.py)
- Requêtes SQL : [`App/scripts/requetes_formations.sql`](../../App/scripts/requetes_formations.sql)
- Schéma BDD : [`App/database/schema/bddemac.sql`](../../App/database/schema/bddemac.sql)
- Migration formations : [`App/database/migrations/003_add_rh_tables.sql`](../../App/database/migrations/003_add_rh_tables.sql)
