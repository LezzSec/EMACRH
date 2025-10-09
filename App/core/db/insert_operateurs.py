from configbd import get_db_connection

# Liste des opérateurs
operateurs = [
    "ACEDO Sebastien",
    "AGUERRE Stéphane",
    "BAGDASARIAN Eduardi",
    "BEHEREGARAY Jean Michel",
    "BENGOCHEA Emmanuel",
    "BIDONDO Anthony",
    "BIDONDO Michael",
    "BIDONDO Pierre",
    "BRANKAER Alexandre",
    "CAMPANE Jean francois",
    "CARRICABURU Alain",
    "CAZENAVE Jean",
    "CORDANI Jean Marie",
    "CORREIA DOS SANTOS Jorg",
    "COSTA Daniel",
    "COUCHINAVE Eric",
    "COURTIES Doryan",
    "DA COSTA Sergio",
    "DAVIES Edouard",
    "DELGADO Cedric",
    "DEVAUX David",
    "DOS SANTOS Charly",
    "ETCHEVERRY Frédéric",
    "FERNANDEZ Thomas",
    "GONOT Damien",
    "GOUVINHAS Alexandre",
    "GUIMON Alain",
    "LUQUET Francois",
    "MARCADIEU Cedric",
    "MARTA Frederic",
    "MERCIRIS Theo",
    "MILAGE Alban",
    "MOLUS Sonia",
    "MONTOIS Xabi",
    "MORIAT Andre",
    "MOUSTROUS Herve",
    "ORDUNA Pierre",
    "OYHENART Nicolas",
    "PEREZ Xavier",
    "POCHELU André Maurice",
    "POISSONNET Jean louis",
    "POUTOU Eldon Tresor",
    "RICE Matthew",
    "SALLETTE Frédéric",
    "SARALEGUI Eric",
    "SERVANT Mikaël",
    "SICRE Pierre",
    "TRADERE Jonathan",
    "UNANUA Dominique",
    "URRUTIA Laurent",
    "VASSEUR Joffrey",
    "VERGE Olivier"
]
def insert_operateurs():
    try:
        # Obtenir une connexion à la base de données
        connection = get_db_connection()
        cursor = connection.cursor()

        # Insérer chaque opérateur dans la table 'operateurs'
        for operateur in operateurs:
            query = "INSERT INTO operateurs (nom_prenom) VALUES (%s)"
            cursor.execute(query, (operateur,))
        
        # Valider les modifications
        connection.commit()
        print(f"{cursor.rowcount} opérateurs ont été insérés dans la table 'operateurs'.")
    except Exception as e:
        print(f"Une erreur est survenue : {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("Connexion à la base de données fermée.")

# Exécuter le script
if __name__ == "__main__":
    insert_operateurs()
