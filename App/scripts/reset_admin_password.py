# -*- coding: utf-8 -*-
"""
Script pour réinitialiser le mot de passe admin
Usage: py scripts/reset_admin_password.py
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import bcrypt
except ImportError:
    print("❌ ERREUR: Module bcrypt manquant")
    print("   Installez avec: pip install bcrypt")
    sys.exit(1)

from core.db.configbd import get_connection

def reset_admin_password(new_password="admin123"):
    """Réinitialise le mot de passe admin"""

    print("\n" + "=" * 60)
    print("  RÉINITIALISATION DU MOT DE PASSE ADMIN")
    print("=" * 60)
    print()

    # Générer le hash bcrypt
    print(f"Nouveau mot de passe : {new_password}")
    password_bytes = new_password.encode('utf-8')
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

    print(f"Hash généré : {password_hash[:20]}... (longueur: {len(password_hash)})")
    print()

    # Se connecter à la BDD
    try:
        conn = get_connection()
        cur = conn.cursor()

        # Vérifier que l'utilisateur admin existe
        cur.execute("SELECT id, username FROM utilisateurs WHERE username = 'admin'")
        user = cur.fetchone()

        if not user:
            print("❌ ERREUR: Utilisateur 'admin' introuvable dans la base")
            print("   Le système d'utilisateurs n'est peut-être pas installé")
            cur.close()
            conn.close()
            return False

        user_id = user[0]
        print(f"✅ Utilisateur admin trouvé (ID: {user_id})")
        print()

        # Mettre à jour le mot de passe
        cur.execute("""
            UPDATE utilisateurs
            SET password_hash = %s
            WHERE username = 'admin'
        """, (password_hash,))

        conn.commit()

        print("✅ Mot de passe réinitialisé avec succès")
        print()
        print("=" * 60)
        print("  IDENTIFIANTS DE CONNEXION")
        print("=" * 60)
        print()
        print(f"  Utilisateur : admin")
        print(f"  Mot de passe : {new_password}")
        print()
        print("=" * 60)

        cur.close()
        conn.close()

        return True

    except Exception as e:
        print(f"❌ ERREUR lors de la réinitialisation: {e}")
        return False

def verify_password(username, password):
    """Vérifie qu'un mot de passe fonctionne"""

    print("\n" + "=" * 60)
    print("  VÉRIFICATION DU MOT DE PASSE")
    print("=" * 60)
    print()

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, username, password_hash
            FROM utilisateurs
            WHERE username = %s
        """, (username,))

        user = cur.fetchone()

        if not user:
            print(f"❌ Utilisateur '{username}' introuvable")
            return False

        user_id, username_db, password_hash = user

        print(f"Utilisateur : {username_db}")
        print(f"Hash stocké : {password_hash[:20]}...")
        print()

        # Vérifier le mot de passe
        password_bytes = password.encode('utf-8')
        hash_bytes = password_hash.encode('utf-8')

        if bcrypt.checkpw(password_bytes, hash_bytes):
            print("✅ MOT DE PASSE CORRECT")
            print()
            print("Vous pouvez vous connecter avec :")
            print(f"  Utilisateur : {username}")
            print(f"  Mot de passe : {password}")
            return True
        else:
            print("❌ MOT DE PASSE INCORRECT")
            return False

        cur.close()
        conn.close()

    except Exception as e:
        print(f"❌ ERREUR lors de la vérification: {e}")
        return False

if __name__ == "__main__":
    print("\nScript de reinitialisation du mot de passe admin")
    print()

    # Vérifier la connexion DB
    try:
        conn = get_connection()
        if conn:
            print("✅ Connexion à la base de données OK")
            conn.close()
        else:
            print("❌ Impossible de se connecter à la base de données")
            print("   Vérifiez le fichier .env")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur de connexion DB: {e}")
        sys.exit(1)

    # Réinitialiser le mot de passe
    success = reset_admin_password("admin123")

    if success:
        # Vérifier que ça fonctionne
        print("\nVerification du nouveau mot de passe...")
        verify_password("admin", "admin123")

        print("\n✅ Réinitialisation terminée avec succès")
        print()
        print("Vous pouvez maintenant vous connecter à EMAC avec :")
        print("  • Utilisateur : admin")
        print("  • Mot de passe : admin123")
        print()
    else:
        print("\n❌ La réinitialisation a échoué")
        print("   Consultez les messages d'erreur ci-dessus")
        sys.exit(1)
