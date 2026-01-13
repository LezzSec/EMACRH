# -*- coding: utf-8 -*-
"""
Script pour chiffrer le fichier .env avant distribution.
Usage: python encrypt_env.py
"""

import sys
import os

# Ajouter le dossier App au path pour importer les modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'App'))

from core.utils.config_crypter import encrypt_env_file
from cryptography.fernet import Fernet


def main():
    print("=" * 80)
    print("EMAC - Chiffrement du fichier .env")
    print("=" * 80)
    print()

    env_path = 'App/.env'

    if not os.path.exists(env_path):
        print(f"[ERREUR] Fichier {env_path} introuvable.")
        print()
        print("Creez d'abord votre fichier App/.env avec vos identifiants DB.")
        return 1

    print(f"[INFO] Fichier source: {env_path}")
    print()

    # Lire le contenu
    with open(env_path, 'r', encoding='utf-8') as f:
        content = f.read()

    print("Contenu du fichier:")
    print("-" * 80)
    print(content)
    print("-" * 80)
    print()

    confirm = input("[WARNING] Confirmer le chiffrement de ce fichier ? (oui/non): ")
    if confirm.lower() not in ['oui', 'o', 'yes', 'y']:
        print("[ANNULE] Operation annulee.")
        return 0

    print()
    print("[INFO] Chiffrement en cours...")

    # Chiffrer
    output_path = 'App/.env.encrypted'
    encrypt_env_file(env_path, output_path)

    print()
    print("=" * 80)
    print("[OK] CHIFFREMENT TERMINE")
    print("=" * 80)
    print()
    print(f"[OK] Fichier chiffre cree: {output_path}")
    print()
    print("Prochaines étapes:")
    print("  1. Ce fichier chiffré sera inclus dans l'exe lors de la compilation")
    print("  2. L'application le déchiffrera automatiquement au démarrage")
    print("  3. Vous n'avez PAS besoin de distribuer le .env en clair")
    print()
    print("IMPORTANT:")
    print("  - Gardez le fichier .env original en sécurité (ne pas le distribuer)")
    print("  - Le .env.encrypted sera inclus automatiquement dans l'exe")
    print("  - La clé de chiffrement est dans: App/core/utils/config_crypter.py")
    print()
    print("=" * 80)

    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n[ERREUR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
