# RAPPORT D'AUDIT DE SÉCURITÉ MASSIF - EMAC

**Date:** 2026-01-30
**Version Application:** 2.x
**Auditeur:** Claude Code Security Scanner
**Classification:** CONFIDENTIEL

---

## RÉSUMÉ EXÉCUTIF

| Catégorie | Critique | Haute | Moyenne | Basse | Total |
|-----------|----------|-------|---------|-------|-------|
| Injection SQL | 1 | 4 | 3 | 0 | 8 |
| Permissions | 4 | 3 | 2 | 1 | 10 |
| Validation Entrées | 2 | 4 | 5 | 3 | 14 |
| Authentification | 2 | 2 | 4 | 2 | 10 |
| Données Sensibles | 2 | 1 | 4 | 1 | 8 |
| Audit Trail | 2 | 3 | 4 | 2 | 11 |
| **TOTAL** | **13** | **17** | **22** | **9** | **61** |

### Score de Sécurité Global: 45/100 ⚠️

---

## VULNÉRABILITÉS CRITIQUES (13)

### C1. Injection SQL Dynamique
**Fichier:** [rh_service.py:633-642](App/core/services/rh_service.py#L633-L642)

```python
cur.execute(f"""
    SELECT d.*, ...
    WHERE d.{column} = %s  # ← VULNÉRABLE
""", (entite_id,))
```

**Risque:** Injection SQL via manipulation de `entite_type`
**Impact:** Lecture/modification non autorisée de données
**Remédiation:** Utiliser une whitelist stricte avec validation avant l'exécution

---

### C2. Credentials par Défaut Non-Forcés
**Fichier:** [001_add_user_management.sql:100-103](App/database/migrations/001_add_user_management.sql#L100-L103)

```sql
-- admin/admin123 par défaut
INSERT INTO utilisateurs (username, password_hash, ...) VALUES ('admin', '$2b$12$LQv...', ...);
```

**Risque:** Compte admin avec mot de passe connu
**Impact:** Accès total au système si non changé
**Remédiation:** Forcer le changement de mot de passe à la première connexion

---

### C3. Clé de Chiffrement Codée en Dur
**Fichier:** [config_crypter.py:14](App/core/utils/config_crypter.py#L14)

```python
ENCRYPTION_KEY = b'yAfLTI6GpL1rMBdtCXUOoq-NfYquO5tyo_8TB27bGOY='
```

**Risque:** Clé visible dans le code source et l'historique Git
**Impact:** Déchiffrement de tous les fichiers `.env.encrypted`
**Remédiation:** Charger la clé depuis une variable d'environnement ou un HSM

---

### C4. Mot de Passe par Défaut dans Script
**Fichier:** [configure_db.bat:36,39](App/config/configure_db.bat#L36)

```batch
set db_password=emacViodos$13
```

**Risque:** Mot de passe MySQL visible dans le script
**Impact:** Accès non autorisé à la base de données
**Remédiation:** Supprimer le mot de passe par défaut, exiger une saisie obligatoire

---

### C5-C7. Permissions Manquantes - Services Critiques

| Service | Fonctions | Fichier:Lignes |
|---------|-----------|----------------|
| RH | `update_infos_generales`, `create/update/delete_contrat` | [rh_service.py:1004-1343](App/core/services/rh_service.py#L1004) |
| Medical | 12 fonctions CRUD (visites, accidents, maladies) | [medical_service.py:171-918](App/core/services/medical_service.py#L171) |
| Vie Salarié | 10 fonctions (sanctions, tests, entretiens) | [vie_salarie_service.py:132-443](App/core/services/vie_salarie_service.py#L132) |

**Risque:** Modification de données RH/médicales sans vérification de permission
**Impact:** Escalade de privilèges, modification de données sensibles
**Remédiation:** Ajouter `require('feature.action')` à toutes les fonctions de modification

---

### C8. Suppression d'Audit Trail Sans Protection
**Fichier:** [historique.py:867-876](App/core/gui/historique.py#L867-L876)

```python
cur.execute("DELETE FROM historique WHERE date_time >= %s AND date_time <= %s", ...)
```

**Risque:** Effacement des traces d'audit
**Impact:** Impossibilité de retracer les actions malveillantes
**Remédiation:** Archivage obligatoire avant suppression, ou logs immuables

---

### C9-C10. Données Médicales Sans Audit
**Fichiers:**
- [medical_service.py:320](App/core/services/medical_service.py#L320) (DELETE visite)
- [medical_service.py:459](App/core/services/medical_service.py#L459) (DELETE accident)

**Risque:** Suppression de données médicales non tracée
**Impact:** Violation RGPD, perte de traçabilité
**Remédiation:** Ajouter `log_hist()` à toutes les opérations CRUD médicales

---

### C11-C13. Aucune Protection Brute Force
**Fichier:** [auth_service.py](App/core/services/auth_service.py) (absent)

**Manquant:**
- Compteur de tentatives échouées
- Verrouillage de compte après N échecs
- Rate limiting
- CAPTCHA

**Risque:** Attaque par force brute sur les mots de passe
**Impact:** Compromission de comptes
**Remédiation:** Implémenter verrouillage après 5 échecs pendant 15 minutes

---

## VULNÉRABILITÉS HAUTES (17)

### H1-H4. Colonnes Dynamiques dans UPDATE
**Fichiers Affectés:**

| Repository | Lignes | Pattern |
|------------|--------|---------|
| [poste_repo.py](App/core/repositories/poste_repo.py#L219-L225) | 219-225 | `f"UPDATE postes SET {col} = %s"` |
| [contrat_repo.py](App/core/repositories/contrat_repo.py#L273-L279) | 273-279 | `f"UPDATE contrats SET {col} = %s"` |
| [personnel_repo.py](App/core/repositories/personnel_repo.py#L311-L320) | 311-320 | `f"UPDATE personnel SET {col} = %s"` |
| [absence_repo.py](App/core/repositories/absence_repo.py#L297-L303) | 297-303 | `f"UPDATE absences SET {col} = %s"` |

**Remédiation:** Utiliser `SafeQueryBuilder` ou validation stricte des noms de colonnes

---

### H5. Fichiers Uploadés Sans Validation
**Fichier:** [bulk_assignment.py:532-1055](App/core/gui/bulk_assignment.py#L532)

```python
file_path, _ = QFileDialog.getOpenFileName(...)
self._document_path = file_path  # Aucune validation
```

**Manquant:**
- Limite de taille fichier
- Validation extension
- Vérification MIME type
- Protection path traversal

**Remédiation:** Valider extension contre whitelist, limiter taille à 10MB

---

### H6. Pas de Timeout Session
**Fichier:** [auth_service.py:81-126](App/core/services/auth_service.py#L81-L126)

**Risque:** Sessions actives indéfiniment
**Remédiation:** Timeout après 30 minutes d'inactivité

---

### H7. IP Non Tracée à la Connexion
**Fichier:** [auth_service.py:205-210](App/core/services/auth_service.py#L205-L210)

Le champ `ip_address` existe dans `logs_connexion` mais n'est jamais peuplé.
**Remédiation:** Capturer et logger l'IP source

---

### H8. Tentatives de Connexion Échouées Non Loggées
**Fichier:** [auth_service.py:181,190](App/core/services/auth_service.py#L181)

**Risque:** Impossible de détecter les attaques
**Remédiation:** Logger chaque tentative échouée avec timestamp et IP

---

### H9-H12. Changements de Permissions Non Audités
**Fichier:** [permission_manager.py:375-496](App/core/services/permission_manager.py#L375)

| Opération | Ligne | Status |
|-----------|-------|--------|
| DELETE role_features | 375-376 | ❌ Non logué |
| UPDATE role_features | 378-382 | ❌ Non logué |
| DELETE user_features | 439-442 | ❌ Non logué |
| UPDATE user_features | 437-448 | ❌ Non logué |

**Remédiation:** Ajouter `log_hist()` pour chaque modification de permission

---

### H13-H17. Formation/Document Services Sans Permissions

| Service | Fonction | Feature Requise |
|---------|----------|-----------------|
| formation_service | add_formation | `rh.formations.edit` |
| formation_service | delete_formation | `rh.formations.delete` |
| document_service | add_document | `rh.documents.edit` |
| document_service | delete_document | `rh.documents.delete` |
| document_service | update_document_info | `rh.documents.edit` |

---

## VULNÉRABILITÉS MOYENNES (22)

### M1-M5. Validation d'Entrées Manquante

| Champ | Fichier:Ligne | Validation Manquante |
|-------|---------------|---------------------|
| Email | [gestion_rh.py:208](App/core/gui/gestion_rh.py#L208) | Format RFC 5322 |
| Téléphone | [gestion_rh.py:207](App/core/gui/gestion_rh.py#L207) | Format français |
| Code Postal | [gestion_rh.py:205](App/core/gui/gestion_rh.py#L205) | 5 chiffres |
| Nom/Prénom | [manage_operateur.py:372](App/core/gui/manage_operateur.py#L372) | Longueur max, caractères |
| Matricule | [gestion_rh.py:172](App/core/gui/gestion_rh.py#L172) | Format entreprise |

---

### M6. Injection LIKE dans Recherche
**Fichier:** [rh_service.py:98](App/core/services/rh_service.py#L98)

```python
recherche_like = f"%{recherche}%"  # % et _ non échappés
```

**Remédiation:** Échapper `%` et `_` dans l'entrée utilisateur

---

### M7. JSON Sans Sanitization
**Fichier:** [manage_operateur.py:484-500](App/core/gui/manage_operateur.py#L484-L500)

```python
desc_json = json.dumps(description_data, ensure_ascii=False)  # Input non validé
```

---

### M8-M10. Dates Non Validées Métier

- Date fin < Date début (contrats)
- Date évaluation dans le passé
- Plages incohérentes

---

### M11. Import CSV Sans Limite
**Fichier:** [import_historique_polyvalence.py:431](App/core/gui/import_historique_polyvalence.py#L431)

**Remédiation:** Limiter à 10MB et 10000 lignes

---

### M12-M15. Logging Inconsistant

| Service | Pattern | Problème |
|---------|---------|----------|
| auth_service | `log_hist_async()` | ✅ Async |
| evaluation_service | `log_hist()` | ❌ Sync bloquant |
| bulk_service | `log_hist()` | ❌ Sync bloquant |
| medical_service | Aucun | ❌ Absent |

---

### M16-M22. Autres Problèmes Moyens

- Pas de politique de rétention des logs
- Historique des mots de passe non tracé
- Schema audit trail incomplet
- Print statements avec données personnelles
- Absence de masquage PII dans les logs
- Documents stockés non chiffrés
- ComboBox non validées

---

## VULNÉRABILITÉS BASSES (9)

| # | Description | Fichier |
|---|-------------|---------|
| L1 | Assert utilisé pour sécurité | rh_service.py:716-718 |
| L2 | Messages d'erreur révélant structure | Multiples |
| L3 | Pas de "Remember me" (acceptable desktop) | login_dialog.py |
| L4 | Permissions fichier logs non spécifiées | logging_config.py:202 |
| L5 | Print() debug en production | emac_ui_kit.py:721 |
| L6 | Algorithme hash non documenté | auth_service.py:128 |
| L7-L9 | Conventions de code mineures | Multiples |

---

## ✅ POINTS POSITIFS

| Domaine | Implémentation | Statut |
|---------|----------------|--------|
| Hachage mots de passe | bcrypt avec sel automatique | ✅ Excellent |
| Complexité mot de passe | 8 car, maj/min/chiffre/spécial | ✅ Excellent |
| Requêtes SQL | Paramétrisées (`%s`) | ✅ Bon |
| Credentials DB | Variables d'environnement | ✅ Bon |
| Protection dernier admin | Empêche verrouillage système | ✅ Bon |
| Tests unitaires auth | 50+ cas de test | ✅ Bon |
| Message erreur login | Générique (pas d'énumération) | ✅ Bon |
| Nettoyage fichiers temp | Suppression immédiate | ✅ Bon |

---

## PLAN DE REMÉDIATION

### Phase 1 - Critique (Semaine 1)

| # | Action | Effort | Fichier |
|---|--------|--------|---------|
| 1 | Forcer changement mdp admin | 2h | auth_service.py |
| 2 | Retirer clé chiffrement du code | 1h | config_crypter.py |
| 3 | Supprimer mdp défaut batch | 0.5h | configure_db.bat |
| 4 | Ajouter permissions rh_service | 4h | rh_service.py |
| 5 | Ajouter permissions medical | 4h | medical_service.py |
| 6 | Implémenter verrouillage compte | 4h | auth_service.py |

### Phase 2 - Haute (Semaine 2-3)

| # | Action | Effort | Fichier |
|---|--------|--------|---------|
| 7 | Corriger colonnes dynamiques UPDATE | 8h | Repositories |
| 8 | Valider fichiers uploadés | 4h | bulk_assignment.py |
| 9 | Ajouter timeout session | 3h | auth_service.py |
| 10 | Logger IP connexion | 2h | auth_service.py |
| 11 | Logger tentatives échouées | 3h | auth_service.py |
| 12 | Auditer changements permissions | 4h | permission_manager.py |

### Phase 3 - Moyenne (Mois 1)

| # | Action | Effort |
|---|--------|--------|
| 13 | Validation email/téléphone/CP | 4h |
| 14 | Échapper LIKE injection | 1h |
| 15 | Limiter import CSV | 2h |
| 16 | Migrer vers log_hist_async | 4h |
| 17 | Politique rétention logs | 4h |
| 18 | Archivage avant suppression audit | 4h |

### Phase 4 - Basse (Mois 2)

| # | Action | Effort |
|---|--------|--------|
| 19 | Supprimer print() debug | 2h |
| 20 | Permissions fichiers logs | 1h |
| 21 | Documentation sécurité | 8h |

---

## EXEMPLES DE CORRECTIFS

### Correctif C1 - Injection SQL Dynamique

```python
# AVANT (vulnérable)
cur.execute(f"SELECT * FROM documents WHERE d.{column} = %s", (id,))

# APRÈS (sécurisé)
ALLOWED_COLUMNS = frozenset(['contrat_id', 'formation_id', 'declaration_id'])

def get_documents_by_entity(entite_type: str, entite_id: int):
    column = {
        'contrat': 'contrat_id',
        'formation': 'formation_id',
        'declaration': 'declaration_id'
    }.get(entite_type)

    if column not in ALLOWED_COLUMNS:
        raise ValueError(f"Type d'entité invalide: {entite_type}")

    # Utiliser une requête distincte pour chaque colonne
    queries = {
        'contrat_id': "SELECT * FROM documents WHERE contrat_id = %s",
        'formation_id': "SELECT * FROM documents WHERE formation_id = %s",
        'declaration_id': "SELECT * FROM documents WHERE declaration_id = %s"
    }
    cur.execute(queries[column], (entite_id,))
```

### Correctif C6 - Verrouillage de Compte

```python
# Dans auth_service.py
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION = timedelta(minutes=15)

def authenticate(username: str, password: str) -> tuple[bool, str]:
    user = get_user_by_username(username)

    if not user:
        log_failed_attempt(username, "Utilisateur inconnu")
        return False, "Identifiants incorrects"

    # Vérifier verrouillage
    if user.get('locked_until') and user['locked_until'] > datetime.now():
        remaining = (user['locked_until'] - datetime.now()).seconds // 60
        return False, f"Compte verrouillé. Réessayez dans {remaining} minutes"

    if not verify_password(password, user['password_hash']):
        increment_failed_attempts(user['id'])

        if get_failed_attempts(user['id']) >= MAX_FAILED_ATTEMPTS:
            lock_account(user['id'], LOCKOUT_DURATION)
            log_hist("ACCOUNT_LOCKED", f"Compte {username} verrouillé après {MAX_FAILED_ATTEMPTS} échecs")

        log_failed_attempt(username, "Mot de passe incorrect")
        return False, "Identifiants incorrects"

    # Réinitialiser compteur sur succès
    reset_failed_attempts(user['id'])
    return True, "Authentification réussie"
```

### Correctif H5 - Validation Upload

```python
# Dans bulk_assignment.py
ALLOWED_EXTENSIONS = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.png', '.jpg'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

def validate_upload(file_path: str) -> tuple[bool, str]:
    if not os.path.exists(file_path):
        return False, "Fichier non trouvé"

    ext = os.path.splitext(file_path)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Extension {ext} non autorisée"

    size = os.path.getsize(file_path)
    if size > MAX_FILE_SIZE:
        return False, f"Fichier trop volumineux ({size // 1024 // 1024}MB > 10MB)"

    # Vérifier MIME type réel
    import magic
    mime = magic.from_file(file_path, mime=True)
    if not mime.startswith(('application/', 'image/')):
        return False, f"Type MIME non autorisé: {mime}"

    return True, "OK"
```

---

## MÉTRIQUES DE SUIVI

### KPIs Sécurité à Implémenter

| Métrique | Cible | Fréquence |
|----------|-------|-----------|
| Vulnérabilités critiques ouvertes | 0 | Temps réel |
| Tentatives de connexion échouées | < 10/jour/user | Quotidien |
| Comptes verrouillés | Alerte si > 5/jour | Quotidien |
| Couverture tests sécurité | > 80% | Hebdomadaire |
| Temps moyen correction critique | < 24h | Par incident |

---

## ANNEXES

### A. Outils de Test Recommandés

- **SQLMap** - Tests injection SQL
- **Bandit** - Analyse statique Python
- **Safety** - Vulnérabilités dépendances
- **OWASP ZAP** - Tests dynamiques

### B. Standards de Référence

- OWASP Top 10 2021
- CWE/SANS Top 25
- RGPD (données personnelles/médicales)
- ISO 27001 (audit trail)

### C. Prochains Audits

- Revue de code manuelle : Q2 2026
- Test de pénétration : Q3 2026
- Audit conformité RGPD : Q4 2026

---

**Document généré automatiquement le 2026-01-30**
**Classification: CONFIDENTIEL - Usage interne uniquement**
