# EMAC - Gestion de Personnel et Polyvalence

![Status](https://img.shields.io/badge/status-production-green)
![Version](https://img.shields.io/badge/version-3.0-blue)
![Security](https://img.shields.io/badge/sécurité-audit_interne-brightgreen)
![Python](https://img.shields.io/badge/python-3.12-yellow)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15-orange)

Application de bureau PyQt5 pour la gestion RH et polyvalence en milieu industriel.

---

## En bref

| | |
|---|---|
| **Type** | Application lourde Windows (PyQt5) |
| **Base de données** | MySQL 8.0 partagé sur réseau local |
| **Sécurité** | Audit interne — injections SQL, traversée de chemins, permissions |
| **Performance** | Pool de connexions + cache + threads |

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
| Permissions | `feature_puzzle.py` | Features granulaires par rôle/utilisateur |
| Audit | `historique.py` | Consultation de l'historique des actions |

---

## Tests

```bash
cd App/tests && python run_all_tests.py
```

---

**v3.0** · 2026-03-24 · Production
