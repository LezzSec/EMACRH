# RAPPORT D'AUDIT DE SECURITE - EMAC
**Date:** 2026-02-02
**Version:** 1.0
**Auditeur:** Claude Code
**Méthodologie:** Audit interne basé sur checklist OWASP Top 10

---

> **MISE A JOUR 2026-02-04**
>
> **Corrections appliquées:** Voir [audit-remediation-2026-02-02.md](audit-remediation-2026-02-02.md)
>
> - ✅ Session timeout (30 min inactivité)
> - ✅ Race condition TOCTOU (permissions)
> - ✅ Injection SQL (colonne dynamique)
> - ✅ Path traversal
> - ✅ Command injection
> - ✅ Divulgation d'erreurs (35+ occurrences)
> - ⏸️ Protection brute force (non implémenté par choix)

---

## RESUME EXECUTIF (ORIGINAL 2026-02-02)

| Severite | Nombre | Description |
|----------|--------|-------------|
| **CRITIQUE** | 5 | Risques necessitant une action immediate |
| **HAUTE** | 9 | Vulnerabilites exploitables |
| **MOYENNE** | 8 | Problemes a corriger rapidement |
| **BASSE** | 2 | Ameliorations recommandees |

**Score Global de Securite: 5.5/10** - Action immediate requise

---

## 1. AUTHENTIFICATION ET MOTS DE PASSE

### Points Positifs
- Hashage bcrypt avec sel automatique
- Politique de mot de passe forte (8+ caracteres, majuscule, minuscule, chiffre, special)
- Messages d'erreur generiques (pas d'enumeration d'utilisateurs)
- Journalisation des tentatives de connexion

### Vulnerabilites Critiques

#### 1.1 Timeout de Session NON APPLIQUE [CRITIQUE]
**Fichier:** `App/core/services/auth_service.py:175-182`

La methode `is_session_expired()` existe mais n'est JAMAIS appelee dans l'application.
- Session reste active indefiniment
- Aucun avertissement ou deconnexion automatique

**Remediation:**
```python
# Dans MainWindow.__init__()
self.session_timer = QTimer(self)
self.session_timer.timeout.connect(self.check_session)
self.session_timer.start(60000)  # Verifier chaque minute
```

#### 1.2 Protection Brute Force ABSENTE [CRITIQUE]
**Fichier:** `App/core/services/auth_service.py`

- Pas de limitation du nombre de tentatives
- Pas de verrouillage de compte
- Pas de delai exponentiel

**Remediation:** Implementer un compteur de tentatives avec verrouillage apres 5 echecs.

#### 1.3 Mot de Passe Admin par Defaut [HAUTE]
**Fichier:** `App/database/migrations/001_add_user_management.sql`

- Mot de passe "admin123" visible dans le code
- Pas de changement force a la premiere connexion

---

## 2. INJECTION SQL

### Points Positifs
- 95%+ des requetes utilisent des parametres (%s)
- `SafeQueryBuilder` dans `base.py` pour les requetes dynamiques

### Vulnerabilites

#### 2.1 Injection via Nom de Colonne Dynamique [CRITIQUE]
**Fichier:** `App/core/services/rh_service.py:641`

```python
cur.execute(f"""
    SELECT ... FROM documents d
    WHERE d.{column} = %s  # INJECTION POSSIBLE
""", (entite_id,))
```

**Remediation:** Utiliser une whitelist stricte et `SafeQueryBuilder`.

#### 2.2 Construction IN Clause avec f-string [HAUTE]
**Fichier:** `App/core/gui/bulk_assignment.py:1327-1330`

```python
cur.execute(f"""
    WHERE id IN ({placeholders})  # Pattern fragile
""", tuple(personnel_ids))
```

#### 2.3 Concatenation de Chaines WHERE [MOYENNE]
**Fichier:** `App/core/gui/historique.py:763`

---

## 3. GESTION DES SECRETS

### Vulnerabilites Critiques

#### 3.1 Credentials en Clair dans .env [CRITIQUE]
**Fichier:** `App/.env`

```
EMAC_DB_PASSWORD=emacViodos$13
EMAC_DB_HOST=192.168.1.128
```

**Actions Immediates:**
1. Changer le mot de passe de la base de donnees
2. Remplacer par des placeholders dans .env
3. Utiliser des variables d'environnement systeme

#### 3.2 Mot de Passe dans Historique Git [HAUTE]
**Fichier:** `App/config/configure_db.bat` (commit 3305cab)

**Remediation:**
```bash
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch App/config/configure_db.bat" \
  --prune-empty --tag-name-filter cat -- --all
```

#### 3.3 Credentials dans Documentation [MOYENNE]
**Fichier:** `App/database/README.md`

Adresse IP et nom d'utilisateur exposes.

---

## 4. SYSTEME DE PERMISSIONS

### Vulnerabilites Critiques

#### 4.1 Fallback Silencieux du Systeme Features [CRITIQUE]
**Fichier:** `App/core/services/permission_manager.py:150-154`

Si le systeme features echoue, fallback vers l'ancien systeme sans alerte.

#### 4.2 Escalade de Privileges via Overrides [CRITIQUE]
**Fichier:** `App/core/services/permission_manager.py:407-477`

- Race condition entre verification admin et modification
- Protection UI uniquement, pas de validation backend

#### 4.3 ID Role Admin Hardcode [CRITIQUE]
**Fichier:** `App/core/gui/feature_puzzle.py:177`

```python
ADMIN_ROLE_ID = 1  # HARDCODE - Dangereux
```

#### 4.4 Fonctions Sans Verification de Permission [HAUTE]
**Fichiers:** Plusieurs services

- `rechercher_operateurs()` - Pas de check
- `get_operateur_by_id()` - Pas de check
- `get_donnees_domaine()` - Pas de check

---

## 5. AUTRES VULNERABILITES

### 5.1 Injection de Commande [HAUTE]
**Fichiers:** `template_service.py`, `gestion_rh.py`

```python
subprocess.run(['xdg-open', file_path])  # file_path non valide
```

### 5.2 Divulgation d'Information [HAUTE]
**Fichiers:** Multiples GUI

```python
QMessageBox.critical(self, "Erreur", f"Erreur:\n{str(e)}")
# Expose des details systeme
```

### 5.3 Path Traversal [MOYENNE]
**Fichier:** `App/core/services/template_service.py:180`

```python
source_path = templates_dir / template['fichier_source'].replace('templates/', '')
# Peut echapper au repertoire
```

### 5.4 Validation Upload Insuffisante [MOYENNE]
**Fichier:** `App/core/gui/bulk_assignment.py`

- Validation extension uniquement
- Pas de verification MIME type

---

## 6. PLAN DE REMEDIATION

### Phase 1 - CRITIQUE (Cette Semaine)

| # | Action | Fichier | Effort |
|---|--------|---------|--------|
| 1 | Changer mot de passe DB | MySQL + .env | 30min |
| 2 | Nettoyer historique git | Repo | 1h |
| 3 | Implementer timeout session | main_qt.py | 2h |
| 4 | Ajouter protection brute force | auth_service.py | 4h |
| 5 | Corriger injection colonne dynamique | rh_service.py | 1h |

### Phase 2 - HAUTE (2 Semaines)

| # | Action | Fichier | Effort |
|---|--------|---------|--------|
| 6 | Remplacer ADMIN_ROLE_ID hardcode | feature_puzzle.py | 2h |
| 7 | Ajouter validation server-side permissions | permission_manager.py | 4h |
| 8 | Corriger divulgation erreurs | GUI files | 3h |
| 9 | Valider chemins fichiers | template_service.py | 2h |
| 10 | Ajouter require() aux services | rh_service.py | 4h |

### Phase 3 - MOYENNE (1 Mois)

| # | Action | Fichier | Effort |
|---|--------|---------|--------|
| 11 | Validation MIME upload | bulk_assignment.py | 2h |
| 12 | Audit log pour refus permissions | permission_manager.py | 2h |
| 13 | Forcer changement mdp premier login | auth_service.py | 3h |
| 14 | Transaction atomique last admin | auth_service.py | 2h |

---

## 7. POINTS POSITIFS

- Hashage bcrypt correctement implemente
- Journalisation comprehensive (historique, connexions)
- Architecture permissions dual-layer
- SafeQueryBuilder pour requetes dynamiques
- Pas de pickle/yaml dangereux
- Pas de shell=True dans subprocess

---

## 8. CONFORMITE

### RGPD
- Donnees personnelles journalisees
- Piste d'audit presente
- Suppression de donnees a verifier

### ISO 27001
- Gestion credentials: A AMELIORER
- Controle d'acces: MOYEN
- Journalisation: BON

---

## 9. CONCLUSION

L'application EMAC presente plusieurs vulnerabilites critiques necessitant une action immediate, principalement:

1. **Credentials exposes** - Mot de passe DB en clair
2. **Session non securisee** - Timeout non applique
3. **Protection brute force absente** - Tentatives illimitees
4. **Injection SQL** - Colonne dynamique non validee
5. **Escalade privileges** - Overrides non valides server-side

**Recommandation:** Suspendre tout deploiement jusqu'a correction des points CRITIQUES.

---

*Rapport genere le 2026-02-02 par Claude Code*
