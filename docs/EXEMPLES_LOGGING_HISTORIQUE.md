# 💡 Exemples Pratiques de Logging d'Historique

## Introduction

Ce document fournit des exemples concrets et prêts à l'emploi pour logger correctement les actions dans l'historique EMAC.

## 📚 Table des matières

1. [Ajout de compétence (INSERT)](#1-ajout-de-compétence)
2. [Modification de niveau (UPDATE)](#2-modification-de-niveau)
3. [Modification de dates d'évaluation (UPDATE)](#3-modification-de-dates)
4. [Suppression de compétence (DELETE)](#4-suppression-de-compétence)
5. [Changement de statut opérateur (UPDATE)](#5-changement-de-statut)
6. [Import de données (INSERT multiple)](#6-import-de-données)
7. [Erreurs système (ERROR)](#7-erreurs-système)

---

## 1. Ajout de compétence

### Contexte
Un opérateur acquiert une nouvelle compétence sur un poste.

### Code complet

```python
from core.db.configbd import get_connection as get_db_connection
from core.services.logger import log_hist
import json
from datetime import datetime, timedelta

def add_competence(operateur_id, poste_id, niveau, date_evaluation=None):
    """Ajoute une compétence à un opérateur."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    try:
        # Récupérer infos opérateur
        cur.execute(
            "SELECT nom, prenom FROM personnel WHERE id = %s",
            (operateur_id,)
        )
        operateur = cur.fetchone()

        # Récupérer info poste
        cur.execute(
            "SELECT poste_code FROM postes WHERE id = %s",
            (poste_id,)
        )
        poste = cur.fetchone()

        # Date par défaut = aujourd'hui
        if date_evaluation is None:
            date_evaluation = datetime.now().date()

        # Calculer prochaine évaluation (+10 ans)
        prochaine_eval = date_evaluation.replace(year=date_evaluation.year + 10)

        # Insérer la compétence
        cur.execute("""
            INSERT INTO polyvalence
            (operateur_id, poste_id, niveau, date_evaluation, prochaine_evaluation)
            VALUES (%s, %s, %s, %s, %s)
        """, (operateur_id, poste_id, niveau, date_evaluation, prochaine_eval))

        poly_id = cur.lastrowid

        # Logger l'action
        log_hist(
            action="INSERT",
            table_name="polyvalence",
            record_id=poly_id,
            operateur_id=operateur_id,
            poste_id=poste_id,
            description=json.dumps({
                "operateur": f"{operateur['prenom']} {operateur['nom']}",
                "poste": poste['poste_code'],
                "niveau": niveau,
                "date_evaluation": date_evaluation.strftime('%Y-%m-%d'),
                "prochaine_evaluation": prochaine_eval.strftime('%Y-%m-%d'),
                "type": "ajout_competence"
            }, ensure_ascii=False),
            source="GUI/gestion_polyvalence"
        )

        conn.commit()
        return poly_id

    except Exception as e:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()
```

### Affichage dans l'interface
✅ **Résumé** : "Ajout de compétence : Niveau 3 sur 0515"

---

## 2. Modification de niveau

### Contexte
L'opérateur évolue d'un niveau 2 à un niveau 4.

### Code complet

```python
def update_niveau(poly_id, new_niveau):
    """Modifie le niveau d'une compétence."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    try:
        # Récupérer l'ancienne valeur ET les infos
        cur.execute("""
            SELECT pv.niveau as old_niveau, pv.operateur_id, pv.poste_id,
                   p.nom, p.prenom, po.poste_code
            FROM polyvalence pv
            JOIN personnel p ON pv.operateur_id = p.id
            JOIN postes po ON pv.poste_id = po.id
            WHERE pv.id = %s
        """, (poly_id,))
        data = cur.fetchone()

        if not data:
            raise ValueError(f"Polyvalence {poly_id} introuvable")

        old_niveau = data['old_niveau']

        # Ne rien faire si pas de changement
        if old_niveau == new_niveau:
            return

        # Mettre à jour
        cur.execute(
            "UPDATE polyvalence SET niveau = %s WHERE id = %s",
            (new_niveau, poly_id)
        )

        # Logger avec ancien et nouveau
        log_hist(
            action="UPDATE",
            table_name="polyvalence",
            record_id=poly_id,
            operateur_id=data['operateur_id'],
            poste_id=data['poste_id'],
            description=json.dumps({
                "operateur": f"{data['prenom']} {data['nom']}",
                "poste": data['poste_code'],
                "changes": {
                    "niveau": {
                        "old": old_niveau,
                        "new": new_niveau
                    }
                },
                "type": "modification_niveau"
            }, ensure_ascii=False),
            source="GUI/gestion_evaluation"
        )

        conn.commit()

    except Exception as e:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()
```

### Affichage dans l'interface
✅ **Résumé** : "Modification niveau : 2 → 4 sur 0515"
✅ **Détails** : Affichage avec code couleur (rouge pour ancien, vert pour nouveau)

---

## 3. Modification de dates

### Contexte
Report de la prochaine évaluation.

### Code complet

```python
from datetime import date

def update_prochaine_evaluation(poly_id, new_date):
    """Modifie la date de prochaine évaluation."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    try:
        # Récupérer ancienne valeur
        cur.execute("""
            SELECT pv.prochaine_evaluation as old_date, pv.operateur_id, pv.poste_id,
                   p.nom, p.prenom, po.poste_code
            FROM polyvalence pv
            JOIN personnel p ON pv.operateur_id = p.id
            JOIN postes po ON pv.poste_id = po.id
            WHERE pv.id = %s
        """, (poly_id,))
        data = cur.fetchone()

        old_date = data['old_date']

        # Mettre à jour
        cur.execute(
            "UPDATE polyvalence SET prochaine_evaluation = %s WHERE id = %s",
            (new_date, poly_id)
        )

        # Logger
        log_hist(
            action="UPDATE",
            table_name="polyvalence",
            record_id=poly_id,
            operateur_id=data['operateur_id'],
            poste_id=data['poste_id'],
            description=json.dumps({
                "operateur": f"{data['prenom']} {data['nom']}",
                "poste": data['poste_code'],
                "changes": {
                    "prochaine_evaluation": {
                        "old": old_date.strftime('%Y-%m-%d') if old_date else "Non définie",
                        "new": new_date.strftime('%Y-%m-%d') if isinstance(new_date, date) else new_date
                    }
                },
                "type": "modification_date_evaluation"
            }, ensure_ascii=False),
            source="GUI/gestion_evaluation"
        )

        conn.commit()

    except Exception as e:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()
```

### Affichage dans l'interface
✅ **Résumé** : "Modification prochaine évaluation sur 0515"
✅ **Détails** : "12/01/2025 → 18/02/2025"

---

## 4. Suppression de compétence

### Contexte
Retrait d'une compétence d'un opérateur.

### Code complet

```python
def delete_competence(poly_id, raison=""):
    """Supprime une compétence."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    try:
        # Récupérer les infos AVANT suppression
        cur.execute("""
            SELECT pv.niveau, pv.operateur_id, pv.poste_id,
                   p.nom, p.prenom, po.poste_code
            FROM polyvalence pv
            JOIN personnel p ON pv.operateur_id = p.id
            JOIN postes po ON pv.poste_id = po.id
            WHERE pv.id = %s
        """, (poly_id,))
        data = cur.fetchone()

        if not data:
            raise ValueError(f"Polyvalence {poly_id} introuvable")

        # Supprimer
        cur.execute("DELETE FROM polyvalence WHERE id = %s", (poly_id,))

        # Logger avec les infos sauvegardées
        description = {
            "operateur": f"{data['prenom']} {data['nom']}",
            "poste": data['poste_code'],
            "niveau": data['niveau'],
            "type": "suppression_competence"
        }

        if raison:
            description["raison"] = raison

        log_hist(
            action="DELETE",
            table_name="polyvalence",
            record_id=poly_id,
            operateur_id=data['operateur_id'],
            poste_id=data['poste_id'],
            description=json.dumps(description, ensure_ascii=False),
            source="GUI/gestion_polyvalence"
        )

        conn.commit()

    except Exception as e:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()
```

### Affichage dans l'interface
✅ **Résumé** : "Suppression : Niveau 3 sur 0515"

---

## 5. Changement de statut

### Contexte
Passer un opérateur de ACTIF à INACTIF.

### Code complet

```python
def change_status(operateur_id, new_statut):
    """Change le statut d'un opérateur."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    try:
        # Récupérer ancien statut
        cur.execute(
            "SELECT nom, prenom, statut FROM personnel WHERE id = %s",
            (operateur_id,)
        )
        data = cur.fetchone()

        old_statut = data['statut']

        # Mettre à jour
        cur.execute(
            "UPDATE personnel SET statut = %s WHERE id = %s",
            (new_statut, operateur_id)
        )

        # Logger (pas de poste_id pour ce type d'action)
        log_hist(
            action="UPDATE",
            table_name="personnel",
            record_id=operateur_id,
            operateur_id=operateur_id,
            poste_id=None,  # Pas de poste concerné
            description=json.dumps({
                "operateur": f"{data['prenom']} {data['nom']}",
                "changes": {
                    "statut": {
                        "old": old_statut,
                        "new": new_statut
                    }
                },
                "type": "changement_statut"
            }, ensure_ascii=False),
            source="GUI/gestion_personnel"
        )

        conn.commit()

    except Exception as e:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()
```

---

## 6. Import de données

### Contexte
Import massif depuis un fichier Excel.

### Code complet

```python
def import_competences_from_excel(excel_path):
    """Importe des compétences depuis Excel."""
    import pandas as pd

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    try:
        # Lire Excel
        df = pd.read_excel(excel_path)

        imported = 0
        errors = []

        for idx, row in df.iterrows():
            try:
                # Récupérer IDs
                cur.execute("SELECT id, nom, prenom FROM personnel WHERE matricule = %s", (row['matricule'],))
                operateur = cur.fetchone()

                cur.execute("SELECT id, poste_code FROM postes WHERE poste_code = %s", (row['poste'],))
                poste = cur.fetchone()

                if not operateur or not poste:
                    errors.append(f"Ligne {idx+2}: opérateur ou poste introuvable")
                    continue

                # Insérer
                cur.execute("""
                    INSERT INTO polyvalence (operateur_id, poste_id, niveau)
                    VALUES (%s, %s, %s)
                """, (operateur['id'], poste['id'], row['niveau']))

                poly_id = cur.lastrowid

                # Logger chaque import
                log_hist(
                    action="INSERT",
                    table_name="polyvalence",
                    record_id=poly_id,
                    operateur_id=operateur['id'],
                    poste_id=poste['id'],
                    description=json.dumps({
                        "operateur": f"{operateur['prenom']} {operateur['nom']}",
                        "poste": poste['poste_code'],
                        "niveau": row['niveau'],
                        "type": "import_excel",
                        "source_file": excel_path.split('/')[-1],
                        "ligne_excel": idx + 2
                    }, ensure_ascii=False),
                    source="GUI/import_data"
                )

                imported += 1

            except Exception as e:
                errors.append(f"Ligne {idx+2}: {str(e)}")

        conn.commit()

        return {
            "imported": imported,
            "errors": errors
        }

    except Exception as e:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()
```

---

## 7. Erreurs système

### Contexte
Enregistrer une erreur pour diagnostic.

### Code complet

```python
def log_error(error_message, context_data=None, operateur_id=None, poste_id=None):
    """Log une erreur système."""
    from core.services.logger import log_hist
    import json
    import traceback

    description = {
        "error_message": str(error_message),
        "error_traceback": traceback.format_exc(),
        "type": "erreur_systeme"
    }

    if context_data:
        description["context"] = context_data

    log_hist(
        action="ERROR",
        table_name="system",
        record_id=None,
        operateur_id=operateur_id,
        poste_id=poste_id,
        description=json.dumps(description, ensure_ascii=False),
        source="SYSTEM"
    )
```

### Exemple d'utilisation

```python
try:
    result = dangerous_operation()
except Exception as e:
    log_error(
        error_message=str(e),
        context_data={
            "operation": "dangerous_operation",
            "params": {"foo": "bar"}
        },
        operateur_id=123
    )
    raise
```

---

## 🎯 Patterns avancés

### Pattern 1 : Modification multiple

```python
def update_multiple_fields(poly_id, updates):
    """Met à jour plusieurs champs et log tous les changements."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    try:
        # Récupérer anciennes valeurs
        cur.execute("""
            SELECT pv.*, p.nom, p.prenom, po.poste_code
            FROM polyvalence pv
            JOIN personnel p ON pv.operateur_id = p.id
            JOIN postes po ON pv.poste_id = po.id
            WHERE pv.id = %s
        """, (poly_id,))
        old_data = cur.fetchone()

        # Construire UPDATE et changes
        set_clauses = []
        params = []
        changes = {}

        for field, new_value in updates.items():
            old_value = old_data.get(field)

            if old_value != new_value:
                set_clauses.append(f"{field} = %s")
                params.append(new_value)

                changes[field] = {
                    "old": str(old_value) if old_value else "Non défini",
                    "new": str(new_value) if new_value else "Non défini"
                }

        if not changes:
            return  # Aucun changement

        # Exécuter UPDATE
        params.append(poly_id)
        cur.execute(
            f"UPDATE polyvalence SET {', '.join(set_clauses)} WHERE id = %s",
            params
        )

        # Logger
        log_hist(
            action="UPDATE",
            table_name="polyvalence",
            record_id=poly_id,
            operateur_id=old_data['operateur_id'],
            poste_id=old_data['poste_id'],
            description=json.dumps({
                "operateur": f"{old_data['prenom']} {old_data['nom']}",
                "poste": old_data['poste_code'],
                "changes": changes,
                "type": "modification_multiple"
            }, ensure_ascii=False),
            source="GUI/gestion_evaluation"
        )

        conn.commit()

    except Exception as e:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()
```

### Pattern 2 : Transaction avec rollback intelligent

```python
def safe_operation_with_logging(operation_func, *args, **kwargs):
    """Exécute une opération avec logging automatique et rollback."""
    conn = get_db_connection()

    try:
        result = operation_func(conn, *args, **kwargs)
        conn.commit()
        return result

    except Exception as e:
        conn.rollback()

        # Logger l'échec
        log_error(
            error_message=f"Échec de {operation_func.__name__}",
            context_data={
                "function": operation_func.__name__,
                "args": str(args),
                "kwargs": str(kwargs)
            }
        )

        raise
    finally:
        conn.close()
```

### Pattern 3 : Audit trail complet

```python
def create_audit_trail(table_name, record_id, action, user_id=None):
    """Crée un trail d'audit complet pour une opération."""
    import socket
    import os

    log_hist(
        action=action,
        table_name=table_name,
        record_id=record_id,
        description=json.dumps({
            "user_id": user_id,
            "hostname": socket.gethostname(),
            "username": os.getenv('USERNAME'),
            "timestamp": datetime.now().isoformat(),
            "type": "audit_trail"
        }, ensure_ascii=False),
        source="AUDIT"
    )
```

---

## 🧪 Tests unitaires

```python
import unittest
from datetime import datetime, date

class TestHistoriqueLogging(unittest.TestCase):

    def setUp(self):
        # Setup base de données de test
        pass

    def test_insert_competence(self):
        """Test ajout de compétence avec logging."""
        poly_id = add_competence(
            operateur_id=1,
            poste_id=1,
            niveau=3
        )

        # Vérifier que le log existe
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM historique WHERE record_id = %s AND action = 'INSERT'",
            (poly_id,)
        )
        log = cur.fetchone()

        self.assertIsNotNone(log)
        self.assertEqual(log['action'], 'INSERT')

        # Vérifier le JSON
        import json
        data = json.loads(log['description'])
        self.assertEqual(data['niveau'], 3)
        self.assertIn('operateur', data)
        self.assertIn('poste', data)

    def test_update_niveau(self):
        """Test modification avec anciennes valeurs."""
        # Créer une compétence
        poly_id = add_competence(1, 1, 2)

        # Modifier
        update_niveau(poly_id, 4)

        # Vérifier le log
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM historique WHERE record_id = %s AND action = 'UPDATE' ORDER BY date_time DESC LIMIT 1",
            (poly_id,)
        )
        log = cur.fetchone()

        data = json.loads(log['description'])
        self.assertEqual(data['changes']['niveau']['old'], 2)
        self.assertEqual(data['changes']['niveau']['new'], 4)
```

---

**Version** : 1.0
**Dernière mise à jour** : Décembre 2025
**Projet** : EMAC
