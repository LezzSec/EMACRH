# EMAC - Gestion de Personnel et Polyvalence

Application de bureau PyQt5 pour la gestion des compétences, évaluations, et ressources humaines dans un environnement industriel.

---

## TL;DR

| | |
|---|---|
| **Quoi** | Application desktop PyQt5 pour la gestion RH et polyvalence en milieu industriel |
| **Statut** | Déployée en production |
| **Sécurité** | Auditée - Session timeout, protection TOCTOU, audit trail |
| **Réseau** | Déploiement client sans MySQL (connexion serveur) |
| **Performance** | Optimisée (connection pooling, cache LRU, threading) |

**Installation rapide** : voir [Démarrage rapide](#démarrage-rapide)

---

## Vue d'ensemble

EMAC est une application complète de gestion RH conçue pour les ateliers de production. Elle permet de :

- **Suivre les compétences** (polyvalence) des employés sur différents postes
- **Planifier les évaluations** périodiques avec calendrier automatisé
- **Gérer les contrats** et renouvellements (CDI, CDD, intérim, etc.)
- **Suivre les absences** et congés
- **Gérer les documents RH** (certificats, permis, formations) avec upload de fichiers
- **Gérer les permissions** avec système granulaire par "features"
- **Auditer toutes les modifications** dans un historique complet

---

## Démarrage rapide

### Installation

```bash
# 1. Cloner le projet
git clone <repo-url>
cd EMAC

# 2. Installer les dépendances
pip install -r App/requirements.txt

# 3. Configurer la base de données
cd App/config
configure_db.bat  # Windows
# Ou copier .env.example vers App/.env et remplir les valeurs

# 4. Initialiser la base de données MySQL
mysql -u root -p emac_db < App/database/schema/bddemac.sql

# 5. Appliquer les optimisations de performance (RECOMMANDÉ)
cd App/scripts
python apply_performance_indexes.py  # Ajoute 29 index

# 6. Lancer l'application
cd App
py -m core.gui.main_qt
```

**Guides** :
- [docs/DEMARRAGE_RAPIDE.md](docs/DEMARRAGE_RAPIDE.md) - Installation en 5 minutes
- [App/config/README.md](App/config/README.md) - Configuration détaillée
- [docs/INSTALLATION_CLIENT.md](docs/INSTALLATION_CLIENT.md) - Installation réseau

---

## Documentation

### Pour les utilisateurs
- [Guide des absences](docs/user/guide-absences.md)
- [Guide de l'interface historique](docs/user/guide-interface-historique.md)
- [Guide upload de documents](docs/user/guide-upload-documents.md)
- [Guide gestion utilisateurs](docs/user/guide-gestion-utilisateurs.md)

### Pour les développeurs
- [Architecture du projet](docs/dev/architecture.md)
- [Guide des tests](docs/dev/tests-report.md)
- [Système d'authentification](docs/dev/authentication-system.md)
- [Déploiement réseau](docs/dev/deploiement-reseau.md)

#### Optimisations Performance

**Vue d'ensemble:** [docs/dev/optimisation-reports/README.md](docs/dev/optimisation-reports/README.md)

| Guide | Description |
|-------|-------------|
| [Optimisations Base de Données](docs/dev/optimisation-database.md) | Connection pooling, indexes (gains 10-100x) |
| [Optimisations UI/Threads](docs/dev/optimisation-ui-threads.md) | DbWorker, 2-stage loading (UI fluide) |
| [Optimisations Cache](docs/dev/optimisation-cache.md) | Cache LRU avec TTL |
| [Monitoring Performance](docs/dev/monitoring-performance.md) | Métriques temps réel |

### Fonctionnalités
- [Module Absences](docs/features/module-absences.md)
- [Module Documents RH](docs/features/module-documents.md)
- [Historique Polyvalence](docs/features/historique-polyvalence.md)

### Sécurité
- [Gestion des credentials](docs/security/database-credentials.md)
- [Audit de sécurité 2026-02-02](docs/security/audit-report-2026-02-02.md)
- [Remédiation sécurité](docs/security/audit-remediation-2026-02-02.md)
- [Protection admin](docs/security/admin-protection.md)

---

## Technologies

- **Interface** : PyQt5 (thème personnalisé)
- **Base de données** : MySQL 8.0 (serveur distant ou local)
- **Exports** : Excel (openpyxl), PDF (ReportLab)
- **Logging** : Système d'audit complet en base de données

**Note importante** : Les postes clients n'ont **PAS besoin** d'installer MySQL. Seul le serveur hébergeant la base de données nécessite MySQL.

---

## Structure du projet

```
EMAC/
├── App/                    # Application principale
│   ├── core/              # Code source
│   │   ├── db/           # Couche base de données (connection pooling)
│   │   ├── gui/          # Interface PyQt5
│   │   ├── services/     # Logique métier
│   │   ├── repositories/ # Accès données (Repository pattern)
│   │   ├── exporters/    # Export Excel/PDF
│   │   └── utils/        # Utilitaires (cache, logging)
│   ├── config/           # Configuration (templates)
│   ├── database/         # Schémas et migrations SQL
│   ├── scripts/          # Scripts utilitaires
│   └── tests/            # Tests unitaires et intégration
│
├── docs/                  # Documentation
│   ├── dev/              # Docs développeur
│   ├── user/             # Guides utilisateur
│   ├── features/         # Documentation fonctionnelle
│   ├── security/         # Documentation sécurité
│   └── project-history/  # Historique du projet
│
├── build-scripts/        # Scripts de build et analyse
│
└── Deploy/               # Déploiement réseau
    ├── Lancer_EMAC.bat         # Lanceur optimisé (cache local)
    └── README_DEPLOIEMENT.md   # Guide admin système
```

**Documentation technique complète** : [CLAUDE.md](CLAUDE.md)

---

## Sécurité

**Score actuel : 9.0/10** (audit 2026-02-04)

### Protections implémentées

| Protection | Description |
|------------|-------------|
| Injection SQL | Requêtes paramétrées + validation whitelist |
| Path Traversal | Validation chemins avec `Path.resolve()` |
| Command Injection | Whitelist répertoires autorisés |
| Divulgation d'info | Messages d'erreur génériques (détails loggés) |
| Race condition TOCTOU | Cache permissions avec TTL + vérification DB |
| Session timeout | Déconnexion auto après 30 min d'inactivité |
| Credentials | Variables d'environnement (`.env`) |
| Audit trail | Toutes modifications tracées dans `historique` |

### Système de permissions "Features"

Système granulaire de permissions par fonctionnalité :
- Format : `module.submodule.action` (ex: `rh.personnel.edit`)
- Overrides utilisateur > Permissions rôle > Refusé
- Interface de gestion : Gestion Utilisateurs > "Gérer les Features"

**Documentation sécurité** : [docs/security/](docs/security/)

---

## Tests

```bash
cd App/tests
python run_all_tests.py

# Tests de sécurité spécifiques
pytest unit/test_security.py -v
```

Les tests couvrent :
- Intégrité de la base de données
- Logique métier (évaluations, contrats, absences)
- Système d'audit et logging
- **Sécurité** : injection SQL, path traversal, TOCTOU, session timeout

**Rapport de tests** : [docs/dev/tests-report.md](docs/dev/tests-report.md)

---

## Fonctionnalités principales

### Gestion de la Polyvalence
- Matrice de compétences par poste et atelier
- 4 niveaux de qualification (1=Apprenti → 4=Formateur)
- Calcul automatique des prochaines évaluations
- Grilles d'affichage et exports Excel

### Système d'évaluation
- Planification automatique sur 10 ans
- Prise en compte des jours fériés
- Alertes pour les évaluations en retard
- Historique complet des évaluations

### Gestion documentaire
- Stockage centralisé des documents RH
- Suivi des dates d'expiration (permis, certificats)
- Catégorisation par domaine (RH, Contrats, Formations)
- Upload de fichiers existants

### Ressources Humaines
- Gestion des contrats (CDD, CDI, intérim, apprentissage, etc.)
- Suivi des renouvellements
- Gestion des absences et congés
- Calcul automatique des soldes

### Audit et Historique
- Tous les changements tracés (qui, quoi, quand)
- Consultation par table, action, ou opérateur
- Export des logs en CSV
- Interface de recherche avancée

### Sécurité avancée
- Déconnexion automatique après inactivité (30 min)
- Avertissement 5 min avant déconnexion
- Vérification des permissions en temps réel
- Logs de sécurité (tentatives non autorisées)

---

## Déploiement

### Build de l'exécutable

```bash
cd App
pyinstaller EMAC_optimized.spec --clean --noconfirm
```

Résultat : `App\dist\EMAC\EMAC.exe`

### Installation sur les postes clients

**Aucune installation de MySQL nécessaire sur les postes clients !**

1. Copiez le dossier `dist/EMAC/` sur le poste client
2. Configurez `.env` avec l'adresse du serveur MySQL :
   ```env
   EMAC_DB_HOST=Votre Adresse IP
   EMAC_DB_USER=Votre Utilisateur
   EMAC_DB_PASSWORD=***
   EMAC_DB_NAME=Nom de votre base
   ```
3. Lancez `EMAC.exe`

### Déploiement réseau

| Scénario | Temps |
|----------|-------|
| Premier lancement | 30-60 sec |
| Lancements suivants | 2-3 sec |

**Guide complet** : [Deploy/README_DEPLOIEMENT.md](Deploy/README_DEPLOIEMENT.md)

---

## Contribution

1. Lire [CLAUDE.md](CLAUDE.md) pour comprendre l'architecture
2. Consulter les [patterns de sécurité](CLAUDE.md#-security-patterns-2026-02-02)
3. Créer une branche pour vos modifications
4. Tester avec `python App/tests/run_all_tests.py`
5. Soumettre une Pull Request

---

## Support

- Documentation technique : [CLAUDE.md](CLAUDE.md)
- Configuration : [App/config/README.md](App/config/README.md)
- Problèmes : Consulter [docs/dev/tests-report.md](docs/dev/tests-report.md)

---

## Licence

Projet interne - Tous droits réservés

---

## Roadmap

- [ ] API REST pour intégration externe
- [ ] Dashboard temps réel avec WebSockets
- [ ] Application mobile (consultation)
- [ ] Export PDF avancé avec templates
- [ ] Protection brute force (optionnel)

---

**Version** : 3.0
**Dernière mise à jour** : 2026-02-04
**Statut** : Production
**Score sécurité** : 9.0/10
