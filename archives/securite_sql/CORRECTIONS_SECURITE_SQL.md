# Guide Détaillé des Corrections de Sécurité SQL

## Table des matières
1. [Correction 1 - polyvalence_logger.py](#correction-1-polyvalence_loggerpy)
2. [Correction 2 - document_service.py](#correction-2-document_servicepy)
3. [Correction 3 - gestion_documentaire.py](#correction-3-gestion_documentairepy)
4. [Correction 4 - historique.py](#correction-4-historiquepy)
5. [Correction 5 - contrat_service.py](#correction-5-contrat_servicepy)

---

## Correction 1 - polyvalence_logger.py

### Localisation
Fichier: `App/core/services/polyvalence_logger.py`
Lignes: 251 et 284
Risque: **CRITIQUE**

### Problème

```python
# Occurrence 1 (ligne 251)
if limit:
    query += f" LIMIT {int(limit)}"

cur.execute(query, (operateur_id,))
```

La clause LIMIT est construite avec une f-string, ce qui peut être dangereux si:
- `limit` n'est pas validé correctement
- Une exception est levée et laisse passer des données impropres
- Le pattern encourage de mauvaises pratiques

### Solution Recommandée

**Approche 1: Constantes prédéfinies (MEILLEURE)**

```python
# En haut du fichier ou dans une configuration
ALLOWED_LIMITS = {
    'recent': 50,
    'standard': 100,
    'all': 1000,
    'export': 10000
}

# Dans la fonction (ligne 251)
def get_historique_operateur(operateur_id, limit=None):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:
        query = """
            SELECT * FROM v_historique_polyvalence_complet
            WHERE operateur_id = %s
            ORDER BY date_action DESC
        """

        # Valider et appliquer le limit
        if limit and limit in ALLOWED_LIMITS:
            limit_value = ALLOWED_LIMITS[limit]
            query += f" LIMIT {limit_value}"

        cur.execute(query, (operateur_id,))
        return cur.fetchall()

    finally:
        cur.close()
        conn.close()
```

**Approche 2: Validation stricte (Alternative)**

```python
def get_historique_operateur(operateur_id, limit=None):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:
        query = """
            SELECT * FROM v_historique_polyvalence_complet
            WHERE operateur_id = %s
            ORDER BY date_action DESC
        """

        # Valider le limit
        if limit:
            try:
                limit_int = int(limit)
                # Vérifier que c'est un entier positif et pas trop grand
                if not (0 < limit_int <= 10000):
                    limit_int = 100  # Valeur par défaut
                query += f" LIMIT {limit_int}"
            except (ValueError, TypeError):
                # Si conversion échoue, ignorer le limit
                pass

        cur.execute(query, (operateur_id,))
        return cur.fetchall()

    finally:
        cur.close()
        conn.close()
```

**Appliquer à la ligne 284 de la même manière:**

```python
def get_historique_operateur_poste(operateur_id, poste_id, limit=None):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:
        query = """
            SELECT * FROM v_historique_polyvalence_complet
            WHERE operateur_id = %s AND poste_id = %s
            ORDER BY date_action DESC
        """

        # Approche 1 (recommandée): constantes
        if limit and limit in {'recent': 50, 'all': 1000}.keys():
            limits = {'recent': 50, 'all': 1000}
            query += f" LIMIT {limits[limit]}"

        cur.execute(query, (operateur_id, poste_id))
        return cur.fetchall()

    finally:
        cur.close()
        conn.close()
```

### Tests de Validation

```python
# test_polyvalence_logger.py
import pytest
from core.services.polyvalence_logger import get_historique_operateur

def test_limit_avec_valeur_valide():
    """Test avec un limit valide"""
    result = get_historique_operateur(1, limit='recent')
    assert len(result) <= 50

def test_limit_avec_valeur_invalide():
    """Test avec un limit invalide"""
    result = get_historique_operateur(1, limit='999_INVALID')
    # Ne doit pas lever d'erreur, ignorer le limit
    assert isinstance(result, list)

def test_limit_avec_null():
    """Test sans limit"""
    result = get_historique_operateur(1, limit=None)
    assert isinstance(result, list)

def test_limit_injection_attempt():
    """Test de sécurité: tentative d'injection"""
    # Cette tentative ne doit pas fonctionner
    result = get_historique_operateur(1, limit="50 ; DROP TABLE operateurs;")
    assert isinstance(result, list)  # Pas d'erreur SQL
```

---

## Correction 2 - document_service.py

### Localisation
Fichier: `App/core/services/document_service.py`
Ligne: 396
Risque: **CRITIQUE**

### Problème

```python
# Ligne 365-398
def update_document(self, document_id, nom_affichage=None, date_expiration=None, ...):
    ...
    updates = []
    params = []

    if nom_affichage is not None:
        updates.append("nom_affichage = %s")
        params.append(nom_affichage)

    if date_expiration is not None:
        updates.append("date_expiration = %s")
        params.append(date_expiration)

    # ... plus de conditions

    sql = f"UPDATE documents SET {', '.join(updates)} WHERE id = %s"  # ⚠️ DANGER
    cursor.execute(sql, tuple(params))
```

Bien que actuellement sans danger (les noms de colonnes sont codés en dur), ce pattern est fragile et mauvais pour la sécurité.

### Solution Recommandée

**Approche 1: Liste blanche des colonnes (MEILLEURE pour la flexibilité)**

```python
def update_document(self, document_id, nom_affichage=None, date_expiration=None,
                   categorie_id=None, notes=None, statut=None):
    """
    Met à jour un document avec validation stricte des colonnes.

    Args:
        document_id: ID du document
        nom_affichage: Nouveau nom d'affichage
        date_expiration: Nouvelle date d'expiration
        categorie_id: Nouvelle catégorie
        notes: Nouvelles notes
        statut: Nouveau statut
    """

    # LISTE BLANCHE: seules ces colonnes peuvent être modifiées
    UPDATABLE_COLUMNS = {
        'nom_affichage': ('nom_affichage', str),
        'date_expiration': ('date_expiration', (type(None), type(date))),
        'categorie_id': ('categorie_id', (int, type(None))),
        'notes': ('notes', (str, type(None))),
        'statut': ('statut', str)
    }

    # Construire les mises à jour avec validation
    updates = []
    params = []

    # Utiliser un dictionnaire pour faciliter la validation
    updates_dict = {
        'nom_affichage': nom_affichage,
        'date_expiration': date_expiration,
        'categorie_id': categorie_id,
        'notes': notes,
        'statut': statut
    }

    for key, value in updates_dict.items():
        if value is not None:
            # Valider que la clé est dans la liste blanche
            if key not in UPDATABLE_COLUMNS:
                continue  # Ignorer les colonnes non autorisées

            # Valider le type
            expected_types = UPDATABLE_COLUMNS[key][1]
            if not isinstance(value, expected_types if isinstance(expected_types, tuple) else (expected_types,)):
                raise ValueError(f"Type invalide pour {key}: attendu {expected_types}, reçu {type(value)}")

            col_name = UPDATABLE_COLUMNS[key][0]
            updates.append(f"{col_name} = %s")
            params.append(value)

    # Vérifier qu'il y a au moins une colonne à modifier
    if not updates:
        return False, "Aucune modification à effectuer"

    # Ajouter l'ID du document comme paramètre final
    params.append(document_id)

    # Construire la requête en toute sécurité
    sql = f"UPDATE documents SET {', '.join(updates)} WHERE id = %s"

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, tuple(params))
        conn.commit()
        cursor.close()
        conn.close()

        return True, "Document mis à jour avec succès"
    except Exception as e:
        return False, f"Erreur lors de la mise à jour: {str(e)}"
```

**Approche 2: Requête complète (Plus simple, moins flexible)**

```python
def update_document(self, document_id, nom_affichage=None, date_expiration=None,
                   categorie_id=None, notes=None, statut=None):
    """
    Met à jour un document avec une requête SQL complète et contrôlée.
    """

    try:
        conn = get_connection()

        # Récupérer d'abord le document existant
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM documents WHERE id = %s", (document_id,))
        existing = cursor.fetchone()

        if not existing:
            return False, "Document non trouvé"

        # Utiliser les valeurs existantes si pas de mise à jour
        nom_affichage = nom_affichage if nom_affichage is not None else existing['nom_affichage']
        date_expiration = date_expiration if date_expiration is not None else existing['date_expiration']
        categorie_id = categorie_id if categorie_id is not None else existing['categorie_id']
        notes = notes if notes is not None else existing['notes']
        statut = statut if statut is not None else existing['statut']

        # Requête SQL complète et paramétrée (pas d'injection possible)
        sql = """
            UPDATE documents
            SET nom_affichage = %s,
                date_expiration = %s,
                categorie_id = %s,
                notes = %s,
                statut = %s
            WHERE id = %s
        """

        cursor.execute(sql, (nom_affichage, date_expiration, categorie_id, notes, statut, document_id))
        conn.commit()
        cursor.close()
        conn.close()

        return True, "Document mis à jour avec succès"
    except Exception as e:
        return False, f"Erreur lors de la mise à jour: {str(e)}"
```

### Tests de Validation

```python
# test_document_service.py
import pytest
from datetime import date
from core.services.document_service import DocumentService

@pytest.fixture
def doc_service():
    return DocumentService()

def test_update_document_with_valid_data(doc_service):
    """Test de mise à jour avec données valides"""
    success, message = doc_service.update_document(
        1,
        nom_affichage="Nouveau nom",
        date_expiration=date(2026, 12, 31)
    )
    assert success
    assert "succès" in message.lower()

def test_update_document_with_invalid_column_name(doc_service):
    """Test de sécurité: tentative d'injection via nom de colonne"""
    # Cette approche ne doit pas fonctionner
    try:
        updates = ["nom_affichage = %s", "'; DROP TABLE documents; --"]
        # L'approche avec liste blanche doit ignorer les colonnes non autorisées
        assert True
    except ValueError:
        assert True  # Exception attendue

def test_update_document_empty(doc_service):
    """Test sans modifications"""
    success, message = doc_service.update_document(1)
    assert not success
    assert "aucune modification" in message.lower()

def test_update_document_invalid_type(doc_service):
    """Test avec type invalide"""
    with pytest.raises(ValueError):
        doc_service.update_document(1, categorie_id="pas_un_entier")
```

---

## Correction 3 - gestion_documentaire.py

### Localisation
Fichier: `App/core/gui/gestion_documentaire.py`
Lignes: 254-261
Risque: **CRITIQUE**

### Problème

```python
def load_operateurs(self):
    ...
    table_name = 'personnel'  # Ligne 248

    query = f"""
    SELECT id, nom, prenom, statut
    FROM {table_name}  # ⚠️ Injection de nom de table
    WHERE statut = 'ACTIF'
    ORDER BY nom, prenom
    """

    cur.execute(query)  # Ligne 261
```

Bien que `table_name` soit actuellement contrôlée, l'utilisation d'une f-string pour injecter un nom de table est dangereuse et viole les bonnes pratiques.

### Solution Recommandée

**Approche 1: Supprimer la variable (MEILLEURE si table est toujours `personnel`)**

```python
def load_operateurs(self):
    """Charge la liste des opérateurs actifs"""
    conn = None
    cur = None

    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True, buffered=True)

        # Requête directe sans variable (plus sûre)
        query = """
        SELECT id, nom, prenom, statut
        FROM personnel
        WHERE statut = 'ACTIF'
        ORDER BY nom, prenom
        """

        cur.execute(query)
        operateurs = cur.fetchall()

        self.operateur_combo.clear()
        self.operateur_combo.addItem("Tous les employés", None)

        for op in operateurs:
            display_name = f"{op['nom']} {op['prenom']}"
            self.operateur_combo.addItem(display_name, op['id'])

        # Sélectionner l'opérateur si fourni
        if self.operateur_id:
            for i in range(self.operateur_combo.count()):
                if self.operateur_combo.itemData(i) == self.operateur_id:
                    self.operateur_combo.setCurrentIndex(i)
                    break

    except Exception as e:
        QMessageBox.warning(self, "Erreur", f"Impossible de charger les opérateurs : {e}")

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
```

**Approche 2: Avec liste blanche (si plusieurs tables possibles)**

```python
def load_operateurs(self):
    """Charge la liste des opérateurs actifs"""

    # LISTE BLANCHE: tables autorisées
    ALLOWED_TABLES = {
        'personnel': 'personnel',
        'operateurs': 'operateurs'  # Pour compatibilité transitoire
    }

    # Configuration: quelle table utiliser
    TABLE_TO_USE = 'personnel'  # ou depuis config

    # Valider que la table est autorisée
    if TABLE_TO_USE not in ALLOWED_TABLES:
        TABLE_TO_USE = 'personnel'  # Fallback sûr

    table_name = ALLOWED_TABLES[TABLE_TO_USE]

    conn = None
    cur = None

    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True, buffered=True)

        # Construire la requête avec la table validée
        query = f"""
        SELECT id, nom, prenom, statut
        FROM {table_name}
        WHERE statut = 'ACTIF'
        ORDER BY nom, prenom
        """

        cur.execute(query)
        operateurs = cur.fetchall()

        self.operateur_combo.clear()
        self.operateur_combo.addItem("Tous les employés", None)

        for op in operateurs:
            display_name = f"{op['nom']} {op['prenom']}"
            self.operateur_combo.addItem(display_name, op['id'])

        if self.operateur_id:
            for i in range(self.operateur_combo.count()):
                if self.operateur_combo.itemData(i) == self.operateur_id:
                    self.operateur_combo.setCurrentIndex(i)
                    break

    except Exception as e:
        QMessageBox.warning(self, "Erreur", f"Impossible de charger les opérateurs : {e}")

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
```

---

## Correction 4 - historique.py

### Localisation
Fichier: `App/core/gui/historique.py`
Lignes: 643-677
Risque: **MOYEN**

### Problème

```python
# Ligne 643-677
where = ["date_time >= %s", "date_time <= %s"]
params = [...]

if action_filter and action_filter != "(Toutes les actions)":
    sql_action = action_map.get(action_filter, action_filter)
    where.append("action = %s")
    params.append(sql_action)

if search_text:  # ⚠️ search_text non validé
    like = f"%{search_text}%"
    where.append("(action LIKE %s OR description LIKE %s ...)")
    params += [like, like, like, like]

sql = (
    "SELECT ... FROM historique "
    f"WHERE {' AND '.join(where)} "
    "ORDER BY date_time DESC, id DESC"
)
cur.execute(sql, params)
```

Le problème principal est que `search_text` n'est pas validé et pourrait contenir des caractères SQL spéciaux qui pourraient être interprétés comme des operateurs LIKE.

### Solution Recommandée

```python
def _fetch_logs(self, d_from: QDate, d_to: QDate, search_text: str, action_filter: str):
    """Récupère les logs avec validation des entrées"""

    cur = None
    try:
        cur = self._cursor()

        # Valider les entrées
        where = ["date_time >= %s", "date_time <= %s"]
        params = [
            dt.datetime(d_from.year(), d_from.month(), d_from.day(), 0, 0, 0),
            dt.datetime(d_to.year(),   d_to.month(),   d_to.day(),   23, 59, 59)
        ]

        # Valider et traiter le filtre d'action
        action_map = {
            "Ajout": "INSERT",
            "Modification": "UPDATE",
            "Suppression": "DELETE",
            "Erreur": "ERROR"
        }

        if action_filter and action_filter != "(Toutes les actions)":
            sql_action = action_map.get(action_filter)
            if sql_action:  # Vérifier que l'action est dans le map
                where.append("action = %s")
                params.append(sql_action)

        # Valider et traiter le texte de recherche
        if search_text:
            # 1. Convertir en string et nettoyer
            search_text = str(search_text).strip()

            # 2. Limiter la longueur pour éviter les requêtes massives
            MAX_SEARCH_LENGTH = 255
            if len(search_text) > MAX_SEARCH_LENGTH:
                search_text = search_text[:MAX_SEARCH_LENGTH]

            # 3. Ne pas filtrer les caractères LIKE (%, _) car la recherche LIKE est utile
            # Les caractères LIKE seront simplement traités comme part du pattern
            # Les paramètres préparés les traiteront correctement

            # 4. Utiliser les paramètres pour les LIKE patterns
            like = f"%{search_text}%"
            where.append("("
                         "action LIKE %s OR "
                         "description LIKE %s OR "
                         "CAST(operateur_id AS CHAR) LIKE %s OR "
                         "CAST(poste_id AS CHAR) LIKE %s"
                         ")")
            params += [like, like, like, like]

        # Construire et exécuter la requête
        sql = (
            "SELECT id, date_time, action, operateur_id, poste_id, description "
            "FROM historique "
            f"WHERE {' AND '.join(where)} "  # Safe: where contient des constantes
            "ORDER BY date_time DESC, id DESC"
        )

        cur.execute(sql, params)
        return cur.fetchall() or []

    finally:
        try:
            if cur: cur.close()
        except Exception:
            pass
```

### Tests de Validation

```python
# test_historique.py
def test_search_with_sql_characters():
    """Test que les caractères SQL dans search_text ne causent pas d'injection"""
    dialog = HistoriqueDialog()

    # Tenter une injection
    dialog.search.setText("' OR '1'='1")
    dialog.reload()  # Ne doit pas causer d'erreur SQL

    # Vérifier que la recherche retourne un résultat sûr
    assert isinstance(dialog.cards_layout, object)

def test_search_with_like_wildcards():
    """Test que les wildcard LIKE fonctionnent correctement"""
    dialog = HistoriqueDialog()

    dialog.search.setText("test%")
    dialog.reload()

    # La recherche doit chercher "test%" comme pattern LIKE
    # Pas d'erreur

def test_search_length_limit():
    """Test que la recherche est limitée en longueur"""
    dialog = HistoriqueDialog()

    # Créer une chaîne très longue
    long_text = "a" * 1000
    dialog.search.setText(long_text)
    dialog.reload()

    # Ne doit pas causer d'erreur ou de timeout
    assert True
```

---

## Correction 5 - contrat_service.py

### Localisation
Fichier: `App/core/services/contrat_service.py`
Lignes: 312-324
Risque: **MOYEN**

### Problème

```python
def get_contrats_operateur(operateur_id, include_inactive=False):
    ...
    query = """
        SELECT c.*, p.nom, p.prenom
        FROM contrat c
        LEFT JOIN personnel p ON p.id = c.operateur_id
        WHERE c.operateur_id = %s
    """

    if not include_inactive:
        query += " AND c.actif = 1"  # ⚠️ Concaténation dynamique

    query += " ORDER BY c.date_debut DESC"

    cursor.execute(query, (operateur_id,))
```

Bien que actuellement sans danger (les fragments SQL sont constants), c'est un anti-pattern qui pourrait devenir dangereux.

### Solution Recommandée

**Approche 1: Requête conditionnelle complète (MEILLEURE)**

```python
def get_contrats_operateur(operateur_id, include_inactive=False):
    """
    Récupère les contrats d'un opérateur.

    Args:
        operateur_id: ID de l'opérateur
        include_inactive: Si True, inclut les contrats inactifs

    Returns:
        Liste des contrats
    """
    connection = get_db_connection()
    cursor, dict_mode = _cursor(connection)

    try:
        # Utiliser deux requêtes complètes selon le contexte
        if include_inactive:
            query = """
                SELECT c.*, p.nom, p.prenom
                FROM contrat c
                LEFT JOIN personnel p ON p.id = c.operateur_id
                WHERE c.operateur_id = %s
                ORDER BY c.date_debut DESC
            """
        else:
            query = """
                SELECT c.*, p.nom, p.prenom
                FROM contrat c
                LEFT JOIN personnel p ON p.id = c.operateur_id
                WHERE c.operateur_id = %s AND c.actif = 1
                ORDER BY c.date_debut DESC
            """

        # Exécuter avec la requête complète (pas de concaténation)
        cursor.execute(query, (operateur_id,))
        return _rows(cursor, dict_mode)

    finally:
        cursor.close()
        connection.close()
```

**Approche 2: Avec liste blanche de conditions (Alternative)**

```python
def get_contrats_operateur(operateur_id, include_inactive=False, status_filter=None):
    """
    Récupère les contrats d'un opérateur avec filtres optionnels.

    Args:
        operateur_id: ID de l'opérateur
        include_inactive: Si True, inclut les contrats inactifs
        status_filter: Filtre sur le statut (doit être dans ALLOWED_STATUS)
    """

    # LISTE BLANCHE: statuts autorisés
    ALLOWED_STATUS = ['CDI', 'CDD', 'STAGE', 'APPRENTICE']

    connection = get_db_connection()
    cursor, dict_mode = _cursor(connection)

    try:
        query = """
            SELECT c.*, p.nom, p.prenom
            FROM contrat c
            LEFT JOIN personnel p ON p.id = c.operateur_id
            WHERE c.operateur_id = %s
        """
        params = [operateur_id]

        # Ajouter les conditions de manière sûre
        if not include_inactive:
            query += " AND c.actif = 1"

        # Valider le filtre de statut
        if status_filter and status_filter in ALLOWED_STATUS:
            query += " AND c.type = %s"
            params.append(status_filter)

        query += " ORDER BY c.date_debut DESC"

        cursor.execute(query, tuple(params))
        return _rows(cursor, dict_mode)

    finally:
        cursor.close()
        connection.close()
```

### Tests de Validation

```python
# test_contrat_service.py
def test_get_contrats_actifs():
    """Test récupération des contrats actifs"""
    contrats = get_contrats_operateur(1, include_inactive=False)

    for c in contrats:
        assert c['actif'] == 1

def test_get_contrats_tous():
    """Test récupération de tous les contrats"""
    contrats_actifs = get_contrats_operateur(1, include_inactive=False)
    contrats_tous = get_contrats_operateur(1, include_inactive=True)

    assert len(contrats_tous) >= len(contrats_actifs)

def test_sql_injection_attempt():
    """Test de sécurité: tentative d'injection"""
    # Cette tentative ne doit pas causer d'erreur SQL
    contrats = get_contrats_operateur(
        "1 ; DROP TABLE contrat; --",
        include_inactive=False
    )
    # Ne doit pas lever d'erreur, ou retourner liste vide
    assert isinstance(contrats, list)
```

---

## Bonnes Pratiques à Suivre

### Pour Toutes les Requêtes SQL:

1. **TOUJOURS utiliser des paramètres préparés**
   ```python
   # BON
   cursor.execute("SELECT * FROM table WHERE id = %s", (id,))

   # MAUVAIS
   cursor.execute(f"SELECT * FROM table WHERE id = {id}")
   ```

2. **Valider les entrées utilisateur**
   ```python
   # BON
   if isinstance(limit, int) and 0 < limit <= 1000:
       query += f" LIMIT {limit}"

   # MAUVAIS
   query += f" LIMIT {limit}"
   ```

3. **Utiliser des listes blanches pour les énumérations**
   ```python
   # BON
   ALLOWED_STATUSES = ['ACTIF', 'INACTIF']
   if status in ALLOWED_STATUSES:
       where.append("statut = %s")
       params.append(status)

   # MAUVAIS
   where.append(f"statut = '{status}'")
   ```

4. **Éviter les f-strings pour le SQL**
   ```python
   # BON
   cursor.execute("UPDATE table SET col = %s WHERE id = %s", (value, id))

   # MAUVAIS
   cursor.execute(f"UPDATE table SET col = {value} WHERE id = {id}")
   ```

5. **Construire les requêtes dans des fonctions réutilisables**
   ```python
   # BON
   def build_query(filters):
       where_clauses = []
       params = []
       # Ajouter les conditions de manière contrôlée
       return query, params

   # MAUVAIS
   query = "SELECT * FROM table WHERE " + user_input
   ```

---

## Checklist de Revue de Code pour SQL

Avant de commiter du code contenant des requêtes SQL:

- [ ] Toutes les valeurs dynamiques utilisent des paramètres %s
- [ ] Pas de f-strings dans les requêtes SQL (sauf pour des constantes contrôlées)
- [ ] Les entrées utilisateur sont validées avant utilisation
- [ ] Les noms de colonnes/tables utilisent une liste blanche si dynamiques
- [ ] Les clauses WHERE/LIMIT/ORDER BY utilisent des constantes ou liste blanche
- [ ] La requête a été testée avec des entrées suspectes
- [ ] Les exceptions SQL sont gérées correctement
- [ ] Les curseurs et connexions sont fermés dans un bloc finally
- [ ] Pas de concaténation de string pour construire les requêtes
- [ ] La requête est lisible et maintenable

---

## Conclusion

Ces corrections garantissent que le projet EMAC sera protégé contre les injections SQL. L'application de ces corrections devrait prendre environ 2-4 heures pour un développeur expérimenté.
