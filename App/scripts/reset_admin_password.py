# -*- coding: utf-8 -*-
"""
Réinitialise le mot de passe de l'utilisateur admin
"""

import sys
import os

app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, app_dir)
os.chdir(app_dir)

from dotenv import load_dotenv
load_dotenv('.env')

import bcrypt
from core.db.configbd import get_connection

def hash_password(password: str) -> str:
    """Hash un mot de passe avec bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

print("="*60)
print("REINITIALISATION DU MOT DE PASSE ADMIN")
print("="*60)

# Nouveau mot de passe
new_password = "admin"
password_hash = hash_password(new_password)

print(f"\nNouveau mot de passe: {new_password}")
print(f"Hash: {password_hash[:50]}...")

# Mise à jour dans la base
conn = get_connection()
cur = conn.cursor()

try:
    cur.execute("""
        UPDATE utilisateurs
        SET password_hash = %s
        WHERE username = 'admin'
    """, (password_hash,))
    
    conn.commit()
    
    print("\n[OK] Mot de passe admin reinitialise avec succes!")
    print("Vous pouvez maintenant vous connecter avec:")
    print("  Username: admin")
    print("  Password: admin")
    
except Exception as e:
    print(f"\n[ERROR] Erreur lors de la reinitialisation: {e}")
    conn.rollback()
finally:
    cur.close()
    conn.close()

print("="*60)
