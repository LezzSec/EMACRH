# EMAC - Gestion de Personnel et Polyvalence

![Status](https://img.shields.io/badge/status-production-green)
![Version](https://img.shields.io/badge/version-3.0-blue)
![Security](https://img.shields.io/badge/security-audited-brightgreen)
![Python](https://img.shields.io/badge/python-3.12-yellow)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15-orange)

Application de bureau PyQt5 pour la gestion RH et polyvalence en milieu industriel.

---

## TL;DR

| | |
|---|---|
| **Sécurité** | Audit OWASP complet — [détails](docs/security/audit-report-2026-02-02.md) |
| **Réseau** | Client léger sans MySQL local — [déploiement](docs/INSTALLATION_CLIENT.md) |
| **Performance** | Pool de connexions + cache + threading — [docs](docs/dev/optimisation-database.md) |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        EMAC Client                          │
├─────────────┬─────────────┬──────────────┬─────────────────┤
│    GUI      │  Services   │ Repositories │     Utils       │
│  (PyQt5)    │  (Métier)   │   (Données)  │ (Cache, Logs)   │
├─────────────┴─────────────┴──────────────┴─────────────────┤
│              QueryExecutor  ·  DatabaseCursor               │
│                    Connection Pool (5)                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  MySQL 8.0  (emac_db)                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Démarrage rapide

```bash
# 1. Dépendances
pip install -r App/requirements.txt

# 2. Configuration base de données
cd App/config && configure_db.bat

# 3. Lancement
cd App && py -m core.gui.main_qt
```

[Guide complet](docs/DEMARRAGE_RAPIDE.md)

---

## Documentation

### Utilisateurs

| Guide | Description |
|---|---|
| [Absences & Congés](docs/user/guide-absences.md) | Demandes, soldes CP/RTT, planning |
| [Historique](docs/user/guide-interface-historique.md) | Consultation de l'audit trail |
| [Documents](docs/user/guide-upload-documents.md) | Upload et gestion documentaire |
| [Gestion des comptes](docs/user/guide-gestion-utilisateurs.md) | Création utilisateurs, rôles |

### Administrateurs

| Guide | Description |
|---|---|
| [Installation client réseau](docs/INSTALLATION_CLIENT.md) | Déploiement sans MySQL local |
| [Déploiement réseau](docs/dev/deploiement-reseau.md) | Configuration serveur partagé |
| [Configuration DB](App/config/README.md) | Fichier `.env`, variables d'environnement |

### Développeurs

| Document | Description |
|---|---|
| [CLAUDE.md](CLAUDE.md) | Instructions complètes — patterns, conventions, architecture |
| [Architecture](docs/dev/architecture.md) | Structure des couches et modules |
| [Guide refactoring](docs/dev/refactoring-guide-2026-02-09.md) | QueryExecutor, CRUDService, EmacDialog |
| [Tests](docs/dev/tests-report.md) | Couverture et lancement |

### Sécurité

| Document | Description |
|---|---|
| [Audit OWASP](docs/security/audit-report-2026-02-02.md) | Rapport complet (SQL injection, path traversal…) |
| [Remédiation](docs/security/audit-remediation-2026-02-02.md) | Corrections appliquées |
| [Credentials DB](docs/security/database-credentials.md) | Gestion mot de passe `.env` / `.env.encrypted` |

### Performance

| Document | Description |
|---|---|
| [Base de données](docs/dev/optimisation-database.md) | Pool, index, QueryExecutor |
| [UI / Threads](docs/dev/optimisation-ui-threads.md) | DbWorker, chargement asynchrone |

---

## Modules

| Module | Fichier principal | Description |
|--------|-------------------|-------------|
| Personnel | `gestion_personnel.py` | Fiches employés, historique |
| Polyvalence | `liste_et_grilles.py` | Matrice compétences, 4 niveaux |
| Évaluations | `gestion_evaluation.py` | Planification auto, alertes |
| Contrats | `contract_management_refactored.py` | CDI/CDD/intérim, renouvellements |
| Absences | `planning_absences.py` | Congés, RTT, soldes |
| RH intégré | `gestion_rh.py` | Vue unifiée par domaine RH |
| Documents | `gestion_documentaire.py` | GED, upload, expiration |
| Permissions | `feature_puzzle.py` | Features granulaires par rôle/user |
| Audit | `historique.py` | Visualisation de l'audit trail |

[Détails fonctionnalités](docs/features/)

---

## Tests

```bash
cd App/tests && python run_all_tests.py
```

---

**v3.0** · 2026-03-17 · Production
