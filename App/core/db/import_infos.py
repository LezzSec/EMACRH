import mysql.connector
from datetime import datetime

# ===============================
# CONFIGURATION DE CONNECTION
# ===============================
DB_HOST = "localhost"
DB_PORT = 3306
DB_USER = "root"
DB_PASS = "emacViodos$13"
DB_NAME = "emac_db"


def ask(prompt, allow_empty=True):
    """Demande une valeur en entrée, accepte vide si autorisé."""
    while True:
        val = input(f"{prompt} : ").strip()
        if val or allow_empty:
            return val or None
        print("Valeur obligatoire.")


def ask_date(prompt):
    """Demande une date au format JJ/MM/AAAA ou laisse vide."""
    while True:
        val = input(f"{prompt} (JJ/MM/AAAA ou vide) : ").strip()
        if val == "":
            return None
        try:
            return datetime.strptime(val, "%d/%m/%Y").date()
        except ValueError:
            print("❌ Format incorrect. Exemple correct : 04/08/1999")


def main():
    print("=== REMPLISSAGE DE PERSONNEL_INFOS ===")
    print("")

    # -------------------------
    # Sélection opérateur
    # -------------------------

    nom = ask("Nom de l'opérateur (pour recherche)")
    prenom = ask("Prénom de l'opérateur (pour recherche)")

    try:
        conn = mysql.connector.connect(
            host=DB_HOST, port=DB_PORT,
            user=DB_USER, password=DB_PASS,
            database=DB_NAME
        )
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, nom, prenom FROM personnel
            WHERE nom LIKE %s AND prenom LIKE %s
        """, (f"%{nom}%", f"%{prenom}%"))

        results = cursor.fetchall()

        if not results:
            print("❌ Aucun opérateur trouvé.")
            return

        if len(results) > 1:
            print("⚠ Plusieurs opérateurs trouvés :")
            for r in results:
                print(f"  {r['id']} - {r['nom']} {r['prenom']}")
            op_id = int(input("ID exact de l'opérateur : "))
        else:
            op_id = results[0]["id"]

        print(f"\n→ Remplissage des infos pour l'opérateur ID {op_id}\n")

        # ----------------------------
        # Vérifier si fiche existante
        # ----------------------------
        cursor.execute(
            "SELECT * FROM personnel_infos WHERE operateur_id = %s",
            (op_id,)
        )
        existing = cursor.fetchone()

        is_update = existing is not None

        # ----------------------------
        # Questions
        # ----------------------------
        sexe = ask("Sexe (M/F/X/NSP)", allow_empty=False)
        date_entree = ask_date("Date d'entrée")
        nationalite = ask("Nationalité")
        cp_naissance = ask("Code postal naissance")
        ville_naissance = ask("Ville naissance")
        pays_naissance = ask("Pays naissance")
        date_naissance = ask_date("Date de naissance")
        adresse1 = ask("Adresse (ligne 1)")
        adresse2 = ask("Adresse (ligne 2)")
        cp_adresse = ask("Code postal adresse")
        ville_adresse = ask("Ville adresse")
        pays_adresse = ask("Pays adresse")
        telephone = ask("Téléphone")
        email = ask("Email")
        commentaire = ask("Commentaire")

        # ----------------------------
        # Générer SQL INSERT ou UPDATE
        # ----------------------------

        if is_update:
            print("\n➡ Mise à jour de la fiche existante…\n")
            sql = """
                UPDATE personnel_infos SET
                    sexe = %s,
                    date_entree = %s,
                    nationalite = %s,
                    cp_naissance = %s,
                    ville_naissance = %s,
                    pays_naissance = %s,
                    date_naissance = %s,
                    adresse1 = %s,
                    adresse2 = %s,
                    cp_adresse = %s,
                    ville_adresse = %s,
                    pays_adresse = %s,
                    telephone = %s,
                    email = %s,
                    commentaire = %s
                WHERE operateur_id = %s
            """

            params = (
                sexe, date_entree, nationalite, cp_naissance, ville_naissance, pays_naissance,
                date_naissance, adresse1, adresse2, cp_adresse, ville_adresse, pays_adresse,
                telephone, email, commentaire, op_id
            )

        else:
            print("\n➡ Création d’une nouvelle fiche…\n")
            sql = """
                INSERT INTO personnel_infos (
                    operateur_id,
                    sexe, date_entree, nationalite,
                    cp_naissance, ville_naissance, pays_naissance,
                    date_naissance,
                    adresse1, adresse2, cp_adresse, ville_adresse, pays_adresse,
                    telephone, email, commentaire
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s
                )
            """

            params = (
                op_id,
                sexe, date_entree, nationalite,
                cp_naissance, ville_naissance, pays_naissance,
                date_naissance,
                adresse1, adresse2, cp_adresse, ville_adresse, pays_adresse,
                telephone, email, commentaire
            )

        cursor.execute(sql, params)
        conn.commit()

        print("✅ Enregistrement effectué avec succès !")

    except Exception as e:
        print(f"❌ Erreur : {e}")

    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass


if __name__ == "__main__":
    main()
