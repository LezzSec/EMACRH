# RAPPORT D'AUDIT DE SECURITE - EMAC

**Date initiale:** 2026-02-02
**Dernière mise à jour:** 2026-02-04
**Méthodologie:** Audit interne 

---

## CORRECTIONS APPLIQUEES

### 1. Injection SQL - Colonne Dynamique
**Fichier:** `App/core/services/rh_service.py:608-660`

- Requêtes SQL prédéfinies pour chaque type d'entité
- Double validation avec whitelist
- Logging des tentatives suspectes

### 2. Path Traversal
**Fichier:** `App/core/services/template_service.py:175-195`

- Validation contre `..` et chemins absolus
- Résolution avec `Path.resolve()`
- Vérification que le chemin reste dans `templates_dir`

### 3. Command Injection - Subprocess
**Fichier:** `App/core/services/template_service.py:313-370`

- Validation du chemin avec `Path.resolve()`
- Vérification que le fichier existe
- Whitelist des répertoires autorisés

### 4. Divulgation d'Information
**Fichiers:** 12 fichiers GUI, 35+ occurrences

- Fonction utilitaire `show_error_message()` dans `emac_ui_kit.py`
- Messages génériques pour l'utilisateur
- Détails complets dans les logs

### 5. Race Condition TOCTOU (Permissions)
**Fichiers:** `permission_manager.py`, `emac_cache.py`

- Cache permissions avec TTL de 5 minutes
- `require()` vérifie en DB par défaut
- `invalidate_user_cache()` recharge le PermissionManager

### 6. Session Timeout
**Fichiers:** `session_timeout.py`, `main_qt.py`

- Déconnexion automatique après 30 min d'inactivité
- Avertissement 5 min avant expiration
- Log de sécurité (LOGOUT_TIMEOUT)

### 7. ADMIN_ROLE_ID Dynamique
**Fichier:** `App/core/gui/feature_puzzle.py`

- Fonction `get_admin_role_id()` récupère l'ID depuis la DB
- Cache pour la performance
- Fallback sécurisé avec logging

---

## NON IMPLEMENTE (par choix)

| Item | Raison |
|------|--------|
| Protection brute force | Non requis pour l'usage interne |

---

## TESTS DE SECURITE

**Fichier:** `App/tests/unit/test_security.py`

| Classe | Tests |
|--------|-------|
| `TestSQLInjectionPrevention` | 4 |
| `TestPathTraversalPrevention` | 2 |
| `TestCommandInjectionPrevention` | 4 |
| `TestTOCTOURaceConditionPrevention` | 9 |
| `TestSessionTimeout` | 4 |

**Exécution:** `pytest tests/unit/test_security.py -v`

---

## POINTS FORTS

- Hashage bcrypt correctement implémenté
- Journalisation comprehensive (historique, connexions)
- Architecture permissions dual-layer (rôles + overrides)
- SafeQueryBuilder pour requêtes dynamiques
- Pas de pickle/yaml dangereux
- Pas de shell=True dans subprocess

---
