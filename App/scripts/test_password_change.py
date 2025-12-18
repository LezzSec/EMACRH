# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.services.auth_service import authenticate_user, change_password, logout_user, get_current_user

print("Test de changement de mot de passe")
print("=" * 50)

# 1. Connexion avec admin/admin123
print("\n1. Connexion avec admin/admin123")
logout_user()
success, error = authenticate_user('admin', 'admin123')
print(f"   Resultat: {success}")
if not success:
    print(f"   Erreur: {error}")
    sys.exit(1)

# 2. Récupérer l'utilisateur
user = get_current_user()
print(f"\n2. Utilisateur connecte: {user['username']} (ID: {user['id']})")

# 3. Changer le mot de passe
print("\n3. Changement du mot de passe vers 'test123'")
success2, error2 = change_password(user['id'], 'test123')
print(f"   Resultat: {success2}")
if error2:
    print(f"   Erreur: {error2}")

# 4. Déconnexion
print("\n4. Deconnexion")
logout_user()

# 5. Tentative de connexion avec l'ancien mot de passe
print("\n5. Test connexion avec ancien mot de passe (admin123)")
success3, error3 = authenticate_user('admin', 'admin123')
print(f"   Resultat: {success3} (devrait etre False)")

# 6. Connexion avec le nouveau mot de passe
print("\n6. Test connexion avec nouveau mot de passe (test123)")
logout_user()
success4, error4 = authenticate_user('admin', 'test123')
print(f"   Resultat: {success4} (devrait etre True)")
if not success4:
    print(f"   Erreur: {error4}")

# 7. Remettre le mot de passe par défaut
if success4:
    print("\n7. Remise du mot de passe par defaut (admin123)")
    user = get_current_user()
    success5, error5 = change_password(user['id'], 'admin123')
    print(f"   Resultat: {success5}")

print("\n" + "=" * 50)
print("Test termine")
