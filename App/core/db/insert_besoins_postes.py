from core.db.configbd import get_connection as get_db_connection

def ensure_column(cursor):
    """
    Ajoute la colonne 'besoins_postes' dans la table 'postes' si elle n'existe pas.
    """
    cursor.execute("SHOW COLUMNS FROM postes LIKE 'besoins_postes'")
    if cursor.fetchone() is None:
        cursor.execute("""
            ALTER TABLE postes
            ADD COLUMN besoins_postes INT NOT NULL DEFAULT 0
            AFTER poste_code
        """)

def set_besoins_postes(data):
    """
    Met à jour la colonne besoins_postes dans la table 'postes' à partir d'une liste
    de tuples (poste_code, besoin). Les codes qui n'existent pas en base sont ignorés
    et listés à la fin.

    :param data: Liste de tuples (poste_code, besoin)
                 Exemple: [("OP01", 3), ("OP02", 5)]
    """
    try:
        # Connexion à la base de données
        connection = get_db_connection()
        cursor = connection.cursor()

        # S'assurer que la colonne existe
        ensure_column(cursor)
        connection.commit()

        # Récupérer tous les codes existants pour filtrer les inconnus
        cursor.execute("SELECT poste_code FROM postes")
        existing_codes = {row[0] for row in cursor.fetchall()}

        updates = []
        unknown = []
        for code, besoin in data:
            if code in existing_codes:
                # Normaliser: valeur entière >= 0
                try:
                    b = int(besoin)
                    if b < 0:
                        b = 0
                except Exception:
                    b = 0
                updates.append((b, code))
            else:
                unknown.append(code)

        # Exécuter les mises à jour
        if updates:
            cursor.executemany(
                "UPDATE postes SET besoins_postes = %s WHERE poste_code = %s",
                updates
            )
            connection.commit()

        print(f"{len(updates)} postes mis à jour.")
        if unknown:
            print("Codes poste inconnus (non mis à jour) :", ", ".join(sorted(set(unknown))))

    except Exception as e:
        print(f"Erreur lors de la mise à jour des besoins : {e}")
        try:
            connection.rollback()
        except Exception:
            pass
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            connection.close()
        except Exception:
            pass

# === Données à définir : (poste_code, besoin) ===
data_to_set = [
    # Exemples — remplace par tes véritables codes/valeurs
    ("0506", 3),
    ("0507", 3),
    ("0510", 3),
    ("0514", 3),
    ("0515", 3),
    ("0516", 2),
    ("0560", 2),
    ("0830", 3),
    ("0900", 3),
    ("0901", 1),
    ("0902", 1),
    ("0903", 1),
    ("0906", 1),
    ("0910", 2),
    ("0912", 2),
    ("0920", 2),
    ("0923", 1),
    ("0924", 1),
    ("0930", 2),
    ("0940", 1),
    ("0941", 1),
    ("0942", 1),
    ("1007", 1),
    ("1026", 1),
    ("1100", 1),
    ("1101", 1),
    ("1103", 1),
    ("1121", 2),
    ("1401", 3),
    ("1402", 3),
    ("1404", 3),
    ("1406", 3),
    ("1412", 3),
    ("0561", 2),

]

if __name__ == "__main__":
    set_besoins_postes(data_to_set)
