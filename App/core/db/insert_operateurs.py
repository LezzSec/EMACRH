# -*- coding: utf-8 -*-
"""
Script legacy de peuplement initial de la table personnel.

Usage: py -m core.db.insert_operateurs
"""
from core.db.configbd import get_connection

# Liste des opérateurs (format: "NOM Prenom")
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
    """Insère les opérateurs dans la table personnel (nom + prenom séparés)."""
    try:
        connection = get_connection()
        cursor = connection.cursor()

        for operateur in operateurs:
            parts = operateur.split(" ", 1)
            nom = parts[0]
            prenom = parts[1] if len(parts) > 1 else ""
            query = "INSERT INTO personnel (nom, prenom, statut) VALUES (%s, %s, 'ACTIF')"
            cursor.execute(query, (nom, prenom))

        connection.commit()
        print(f"{len(operateurs)} opérateurs ont été insérés dans la table 'personnel'.")
    except Exception as e:
        print(f"Une erreur est survenue : {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("Connexion à la base de données fermée.")


if __name__ == "__main__":
    insert_operateurs()
