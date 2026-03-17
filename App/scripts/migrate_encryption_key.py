# -*- coding: utf-8 -*-
"""
Script de migration : re-chiffrement de .env.encrypted avec la nouvelle cle machine.

Contexte
--------
Avant le commit de securite du 2026-03-17, la cle Fernet etait uniquement la cle
embarquee dans le code (config_crypter._get_embedded_key).

Desormais la priorite est :
  1. EMAC_ENCRYPTION_KEY (variable d'environnement)
  2. Cle derivee de la machine (MachineGuid + hostname via PBKDF2)  <-- nouveau defaut
  3. Cle embarquee (fallback avec warning)

Ce script :
  1. Dechiffre App/.env.encrypted avec l'ANCIENNE cle embarquee
  2. Re-chiffre le contenu avec la NOUVELLE cle active (machine ou env)
  3. Sauvegarde l'ancien fichier en .env.encrypted.bak
  4. Verifie le round-trip avant d'ecraser quoi que ce soit

Usage
-----
    cd App
    py -m scripts.migrate_encryption_key              # migration standard
    py -m scripts.migrate_encryption_key --dry-run    # simulation sans ecriture
    py -m scripts.migrate_encryption_key --verify     # verifie que le fichier actuel est lisible
"""

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Chemin du fichier chiffre (relatif au dossier App/)
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).parent
_APP_DIR = _SCRIPT_DIR.parent
_ENCRYPTED_FILE = _APP_DIR / '.env.encrypted'


def _get_embedded_key() -> bytes:
    """Reconstitue la cle embarquee (AVANT migration) sans passer par la logique de priorite."""
    import base64
    parts = [
        b'a0J5MjFaSnEzV09QMUZuMw==',
        b'aS1YVnF3T2VQdkh4MXphZw==',
        b'QmhlQXBMNjdrRTA9',
    ]
    raw = b''
    for p in parts:
        raw += base64.b64decode(p)
    return raw[:44]


def _decrypt_with_key(encrypted_text: str, key: bytes) -> str:
    """Dechiffre avec une cle Fernet specifique."""
    import base64
    from cryptography.fernet import Fernet, InvalidToken
    f = Fernet(key)
    encrypted_bytes = base64.urlsafe_b64decode(encrypted_text.encode())
    return f.decrypt(encrypted_bytes).decode()


def _encrypt_with_new_key(plain_text: str) -> str:
    """Chiffre avec la nouvelle cle active (suit la priorite du module)."""
    # Import apres avoir configure le sys.path si besoin
    sys.path.insert(0, str(_APP_DIR))
    from core.utils.config_crypter import encrypt_config, _get_encryption_key
    key_used = _get_encryption_key()
    print(f"  Nouvelle cle (premiers octets) : {key_used[:8]}...")
    return encrypt_config(plain_text)


def verify(encrypted_file: Path = _ENCRYPTED_FILE) -> bool:
    """Verifie que le fichier chiffre actuel est lisible avec la cle active."""
    sys.path.insert(0, str(_APP_DIR))
    from core.utils.config_crypter import decrypt_env_file
    print(f"Verification de : {encrypted_file}")
    try:
        content = decrypt_env_file(str(encrypted_file))
        lines = [l for l in content.splitlines() if l.strip() and not l.startswith('#')]
        print(f"  OK — {len(lines)} variable(s) trouvee(s)")
        return True
    except Exception as e:
        print(f"  ECHEC — {e}")
        return False


def migrate(dry_run: bool = False, encrypted_file: Path = _ENCRYPTED_FILE) -> bool:
    """
    Re-chiffre encrypted_file avec la nouvelle cle machine.

    Returns True si succes, False sinon.
    """
    from cryptography.fernet import InvalidToken

    if not encrypted_file.exists():
        print(f"Fichier introuvable : {encrypted_file}")
        print("Rien a migrer.")
        return True

    print(f"Fichier source      : {encrypted_file}")
    print(f"Mode dry-run        : {'OUI' if dry_run else 'NON'}")
    print()

    # --- Etape 1 : lire le contenu chiffre ---
    encrypted_text = encrypted_file.read_text(encoding='ascii').strip()

    # --- Etape 2 : dechiffrer avec l'ancienne cle embarquee ---
    print("[1/4] Dechiffrement avec l'ancienne cle embarquee...")
    old_key = _get_embedded_key()
    try:
        plain_text = _decrypt_with_key(encrypted_text, old_key)
        print(f"      OK — {len(plain_text)} caracteres dechiffres")
    except InvalidToken:
        print("      ECHEC — le fichier n'est PAS chiffre avec l'ancienne cle embarquee.")
        print("      Tentative avec la cle active (peut-etre deja migre)...")
        if verify(encrypted_file):
            print("  Le fichier est deja lisible avec la cle active. Rien a faire.")
            return True
        else:
            print("  Impossible de dechiffrer avec aucune cle connue. Migration impossible.")
            return False

    # --- Etape 3 : re-chiffrer avec la nouvelle cle ---
    print("[2/4] Re-chiffrement avec la nouvelle cle machine...")
    try:
        new_encrypted = _encrypt_with_new_key(plain_text)
        print("      OK")
    except Exception as e:
        print(f"      ECHEC — {e}")
        return False

    # --- Etape 4 : verification du round-trip ---
    print("[3/4] Verification du round-trip...")
    sys.path.insert(0, str(_APP_DIR))
    from core.utils.config_crypter import decrypt_config
    try:
        verified = decrypt_config(new_encrypted)
        if verified != plain_text:
            print("      ECHEC — le contenu dechiffre ne correspond pas a l'original!")
            return False
        print("      OK — round-trip valide")
    except Exception as e:
        print(f"      ECHEC — {e}")
        return False

    # --- Etape 5 : ecriture ---
    if dry_run:
        print("[4/4] DRY-RUN — aucune ecriture effectuee.")
        print()
        print("Simulation reussie. Relancer sans --dry-run pour appliquer.")
        return True

    bak_file = encrypted_file.with_suffix(
        f'.encrypted.bak_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    )
    print(f"[4/4] Sauvegarde de l'ancien fichier -> {bak_file.name}")
    shutil.copy2(encrypted_file, bak_file)

    encrypted_file.write_text(new_encrypted, encoding='ascii')
    print(f"      Nouveau fichier ecrit : {encrypted_file}")
    print()
    print("Migration terminee avec succes.")
    print(f"Backup conserve dans : {bak_file}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Migration du fichier .env.encrypted vers la nouvelle cle machine"
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help="Simule la migration sans ecrire de fichier"
    )
    parser.add_argument(
        '--verify', action='store_true',
        help="Verifie uniquement que le fichier actuel est lisible"
    )
    parser.add_argument(
        '--file', default=str(_ENCRYPTED_FILE),
        help=f"Chemin du fichier .env.encrypted (defaut: {_ENCRYPTED_FILE})"
    )
    args = parser.parse_args()

    target = Path(args.file)

    if args.verify:
        ok = verify(target)
        sys.exit(0 if ok else 1)
    else:
        ok = migrate(dry_run=args.dry_run, encrypted_file=target)
        sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
