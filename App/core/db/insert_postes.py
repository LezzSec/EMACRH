from configbd import get_db_connection

# Liste des postes 
postes = [
    "0506", "0507", "0510", "0514", "0515", "0516", "0560",
    "0830", "0900", "0901", "0902", "0903", "0906", "0910",
    "0912", "0920", "0923", "0924", "0930", "0940", "0941",
    "0942", "1007", "1026", "1100", "1101", "1103", "1121",
    "1401", "1402", "1404", "1406", "1412"
]

def create_and_insert_postes():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Créer la table 'postes' 
        create_table_query = """
        CREATE TABLE IF NOT EXISTS postes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            poste_code VARCHAR(50) NOT NULL
        );
        """
        cursor.execute(create_table_query)
        print("Table 'postes' créée ou déjà existante.")

        # Insérer les postes dans la table
        insert_query = "INSERT INTO postes (poste_code) VALUES (%s)"
        for poste in postes:
            cursor.execute(insert_query, (poste,))
        
        connection.commit()
        print(f"{cursor.rowcount} postes ont été insérés dans la table 'postes'.")
    except Exception as e:
        print(f"Une erreur est survenue : {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("Connexion à la base de données fermée.")

# Exécuter le script
if __name__ == "__main__":
    create_and_insert_postes()
