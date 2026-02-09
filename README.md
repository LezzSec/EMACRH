# EMAC - Gestion de Personnel et Polyvalence

![Status](https://img.shields.io/badge/status-production-green)
![Version](https://img.shields.io/badge/version-3.0-blue)
![Security](https://img.shields.io/badge/security-audited-brightgreen)
![Python](https://img.shields.io/badge/python-3.12-yellow)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15-orange)

Application de bureau pour la gestion RH et polyvalence en milieu industriel.

---

## TL;DR

| | |
|---|---|
| **Sécurité** | Audit interne ([details](#sécurité)) |
| **Réseau** | Client sans MySQL ([details](#administrateurs)) |
| **Performance** | Pool + cache + threading ([details](#performance)) |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        EMAC Client                          │
├─────────────┬─────────────┬─────────────┬──────────────────┤
│    GUI      │  Services   │ Repositories│     Utils        │
│  (PyQt5)    │  (Logic)    │   (Data)    │ (Cache, Logging) │
├─────────────┴─────────────┴─────────────┴──────────────────┤
│                    Connection Pool                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     MySQL Server                            │
│                      (emac_db)                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Démarrage rapide

```bash
pip install -r App/requirements.txt
cd App/config && configure_db.bat
cd App && py -m core.gui.main_qt
```

[Guide complet](docs/DEMARRAGE_RAPIDE.md)

---

## Documentation

### Utilisateurs

| | |
|---|---|
| [Absences](docs/user/guide-absences.md) | [Historique](docs/user/guide-interface-historique.md) |
| [Documents](docs/user/guide-upload-documents.md) | [Comptes](docs/user/guide-gestion-utilisateurs.md) |

### Administrateurs

| | |
|---|---|
| [Installation client](docs/INSTALLATION_CLIENT.md) | [Déploiement réseau](docs/dev/deploiement-reseau.md) |
| [Configuration DB](App/config/README.md) | |

### Développeurs

| | |
|---|---|
| [CLAUDE.md](CLAUDE.md) | Instructions techniques |
| [Architecture](docs/dev/architecture.md) | Structure du code |
| [Tests](docs/dev/tests-report.md) | Couverture |

### Sécurité

| | |
|---|---|
| [Audit OWASP](docs/security/audit-report-2026-02-02.md) | [Remédiation](docs/security/audit-remediation-2026-02-02.md) |
| [Patterns](CLAUDE.md#-security-patterns-2026-02-02) | Bonnes pratiques |

### Performance

| | |
|---|---|
| [Overview](docs/dev/optimisation-reports/README.md) | [Database](docs/dev/optimisation-database.md) |
| [UI/Threads](docs/dev/optimisation-ui-threads.md) | |

---

## Modules

| Module | Description |
|--------|-------------|
| Polyvalence | Matrice compétences, 4 niveaux |
| Évaluations | Planification auto, alertes |
| Contrats | CDI/CDD/intérim, renouvellements |
| Documents | Upload, expiration |
| Absences | Congés, RTT, soldes |
| Permissions | Features granulaires |
| Audit | Historique complet |

[Détails](docs/features/)

---

## Tests

```bash
cd App/tests && python run_all_tests.py
```

---

**v3.0** | 2026-02-04 | Production
