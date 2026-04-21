# EMAC - Gestion de Personnel et Polyvalence

![Status](https://img.shields.io/badge/status-production-green)
![Version](https://img.shields.io/badge/version-3.1-blue)
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
├──────────┬──────────────┬────────────────┬──────────────────┤
│  gui/    │   domain/    │ infrastructure/│  application/    │
│ (PyQt5)  │ services +   │  db · logs ·   │  permissions     │
│          │ repositories │  cache         │                  │
├──────────┴──────────────┴────────────────┴──────────────────┤
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
cd App && py -m gui.main_qt
```

---

## Modules

| Module | Description |
|--------|-------------|
| Personnel | Fiches employés, matricules, statuts, historique |
| Polyvalence | Matrice compétences, 4 niveaux, historique |
| Évaluations | Planification auto, alertes échéances |
| Contrats | CDI/CDD/intérim, alertes renouvellement |
| Absences | Congés, RTT, maladie, planning visuel |
| RH intégré | Vue unifiée par domaine (contrat, médical, vie salarié…) |
| Documents | GED intégrée, templates, expiration |
| Distance domicile | Calcul distance domicile-entreprise par commune (RGPD) |
| Permissions | Features granulaires par rôle/utilisateur |
| Audit | Historique complet de toutes les actions |

---

## Tests

```bash
cd App && py -m pytest tests/
```

---

**v3.1** · 2026-04-20 · Production
