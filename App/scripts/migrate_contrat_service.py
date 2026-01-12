# -*- coding: utf-8 -*-
"""
Script de migration automatique pour contrat_service.py
Convertit les pattern get_db_connection() + _cursor + _rows vers DatabaseCursor
"""

import re

def migrate_read_functions():
    """Migre les fonctions de lecture (GET)"""

    file_path = r"c:\Users\tlahirigoyen\Desktop\PROJET\EMAC\App\core\services\contrat_service.py"

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern 1: Remplacer get_all_contracts
    content = re.sub(
        r'def get_all_contracts\(operateur_id: int, include_inactive: bool = False\) -> List\[dict\]:\s+"""Récupère tous les contrats d\'un opérateur\."""\s+try:\s+connection = get_db_connection\(\)\s+cursor, dict_mode = _cursor\(connection\)\s+query = """\s+SELECT c\.\*, p\.nom, p\.prenom\s+FROM contrat c\s+LEFT JOIN personnel p ON p\.id = c\.operateur_id\s+WHERE c\.operateur_id = %s\s+"""\s+if not include_inactive:\s+query \+= " AND c\.actif = 1"\s+query \+= " ORDER BY c\.date_debut DESC"\s+cursor\.execute\(query, \(operateur_id,\)\)\s+result = _rows\(cursor, dict_mode\)\s+cursor\.close\(\)\s+connection\.close\(\)\s+return result\s+except Exception as e:\s+print\(f"Erreur lors de la récupération des contrats : \{e\}"\)\s+return \[\]',
        '''def get_all_contracts(operateur_id: int, include_inactive: bool = False) -> List[dict]:
    """Récupère tous les contrats d'un opérateur."""
    try:
        query = """
            SELECT c.*, p.nom, p.prenom
            FROM contrat c
            LEFT JOIN personnel p ON p.id = c.operateur_id
            WHERE c.operateur_id = %s
        """

        if not include_inactive:
            query += " AND c.actif = 1"

        query += " ORDER BY c.date_debut DESC"

        with DatabaseCursor(dictionary=True) as cursor:
            cursor.execute(query, (operateur_id,))
            return cursor.fetchall()

    except Exception as e:
        print(f"Erreur lors de la récupération des contrats : {e}")
        return []''',
        content
    )

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("Migration terminée!")

if __name__ == "__main__":
    migrate_read_functions()
