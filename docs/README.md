# Documentation EMAC

La documentation est organisée par type d'utilisateur.

---

## Structure

```
docs/
├── dev/              # Documentation développeur
├── user/             # Guides utilisateurs finaux
├── features/         # Documentation fonctionnalités
├── security/         # Sécurité
└── project-history/  # Historique du projet
```

---

## Développeurs

### Architecture & patterns

| Fichier | Description |
|---------|-------------|
| [dev/architecture.md](dev/architecture.md) | Couches, modules, conventions |
| [dev/refactoring-guide-2026-02-09.md](dev/refactoring-guide-2026-02-09.md) | QueryExecutor, CRUDService, EmacDialog |
| [dev/exemples-logging.md](dev/exemples-logging.md) | Utilisation du système de logs |
| [dev/tests-report.md](dev/tests-report.md) | Couverture de tests |
| [dev/build-optimization.md](dev/build-optimization.md) | Compilation PyInstaller |

### Performance

| Fichier | Description |
|---------|-------------|
| [dev/optimisation-database.md](dev/optimisation-database.md) | Pool, index, QueryExecutor |
| [dev/optimisation-ui-threads.md](dev/optimisation-ui-threads.md) | DbWorker, chargement async |
| [dev/optimisation-cache.md](dev/optimisation-cache.md) | Cache permissions / données |

### RH & modules

| Fichier | Description |
|---------|-------------|
| [dev/analyse-fonctionnalites-rh.md](dev/analyse-fonctionnalites-rh.md) | Analyse des fonctionnalités RH |
| [dev/interface-rh.md](dev/interface-rh.md) | Documentation interface GestionRH |
| [dev/structure-donnees-historique.md](dev/structure-donnees-historique.md) | Tables d'historique |
| [dev/vues-database-2026-02-09.md](dev/vues-database-2026-02-09.md) | Vues SQL |

### Déploiement

| Fichier | Description |
|---------|-------------|
| [dev/deploiement-reseau.md](dev/deploiement-reseau.md) | Déploiement client réseau |
| [INSTALLATION_CLIENT.md](INSTALLATION_CLIENT.md) | Installation sans MySQL local |
| [DEMARRAGE_RAPIDE.md](DEMARRAGE_RAPIDE.md) | Démarrage en 5 minutes |

---

## Utilisateurs

| Fichier | Description |
|---------|-------------|
| [user/guide-absences.md](user/guide-absences.md) | Demandes de congés, RTT, soldes |
| [user/guide-interface-historique.md](user/guide-interface-historique.md) | Consultation de l'audit trail |
| [user/guide-upload-documents.md](user/guide-upload-documents.md) | Uploader et gérer des documents |
| [user/guide-gestion-utilisateurs.md](user/guide-gestion-utilisateurs.md) | Comptes utilisateurs et rôles |
| [user/guide-verification-formations.md](user/guide-verification-formations.md) | Suivi des formations |
| [user/resolution-lenteur.md](user/resolution-lenteur.md) | Résoudre les problèmes de lenteur |

---

## Fonctionnalités

| Fichier | Description |
|---------|-------------|
| [features/module-absences.md](features/module-absences.md) | Module absences — 5 onglets |
| [features/module-documents.md](features/module-documents.md) | GED intégrée |
| [features/historique-polyvalence.md](features/historique-polyvalence.md) | Historique compétences |
| [features/historique-polyvalence-implementation.md](features/historique-polyvalence-implementation.md) | Implémentation technique |

---

## Sécurité

| Fichier | Description |
|---------|-------------|
| [security/database-credentials.md](security/database-credentials.md) | `.env` et `.env.encrypted` |
| [security/security-changelog.md](security/security-changelog.md) | Journal des modifications de sécurité |
| [security/audit-report-2026-02-02.md](security/audit-report-2026-02-02.md) | Rapport d'audit OWASP |
| [security/audit-remediation-2026-02-02.md](security/audit-remediation-2026-02-02.md) | Corrections appliquées |
| [security/admin-protection.md](security/admin-protection.md) | Protection compte administrateur |

---

## Documentation principale

- **[../CLAUDE.md](../CLAUDE.md)** — Référence technique complète (patterns, sécurité, architecture)
- **[../README.md](../README.md)** — Page d'accueil du projet

---

**Dernière mise à jour** : 2026-03-17
