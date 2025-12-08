# -*- coding: utf-8 -*-
"""
Script pour affecter les dates d'entrée aux employés existants
Permet de saisir manuellement la date d'entrée pour chaque employé qui n'en a pas
"""

import sys
import os
from datetime import datetime, date

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.db.configbd import get_connection
from core.services.logger import log_hist


def get_personnel_sans_date_entree():
    """Récupère la liste des employés sans date d'entrée"""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:
        cur.execute("""
            SELECT
                p.id,
                p.nom,
                p.prenom,
                p.matricule,
                p.statut,
                pi.date_entree
            FROM personnel p
            LEFT JOIN personnel_infos pi ON p.id = pi.operateur_id
            WHERE pi.date_entree IS NULL OR pi.operateur_id IS NULL
            ORDER BY p.nom, p.prenom
        """)

        return cur.fetchall()

    finally:
        cur.close()
        conn.close()


def affecter_date_entree(operateur_id, nom, prenom, date_entree):
    """Affecte une date d'entrée à un employé"""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:
        # Vérifier si l'enregistrement existe dans personnel_infos
        cur.execute("SELECT operateur_id FROM personnel_infos WHERE operateur_id = %s", (operateur_id,))
        existe = cur.fetchone()

        if existe:
            # Mettre à jour la date d'entrée
            cur.execute("""
                UPDATE personnel_infos
                SET date_entree = %s
                WHERE operateur_id = %s
            """, (date_entree, operateur_id))
            action = "Mise à jour"
        else:
            # Créer l'enregistrement avec la date d'entrée
            cur.execute("""
                INSERT INTO personnel_infos (operateur_id, date_entree)
                VALUES (%s, %s)
            """, (operateur_id, date_entree))
            action = "Création"

        conn.commit()

        # Logger l'action
        log_hist(
            "AFFECTATION_DATE_ENTREE",
            f"{action} date d'entrée pour {nom} {prenom}: {date_entree}",
            operateur_id,
            None
        )

        return True

    except Exception as e:
        print(f"  ✗ Erreur : {e}")
        conn.rollback()
        return False

    finally:
        cur.close()
        conn.close()


def saisir_date():
    """Demande à l'utilisateur de saisir une date"""
    while True:
        date_str = input("    Date d'entrée (JJ/MM/AAAA) ou 'skip' pour passer : ").strip()

        if date_str.lower() == 'skip':
            return None

        try:
            # Essayer de parser la date
            date_entree = datetime.strptime(date_str, "%d/%m/%Y").date()

            # Vérifier que la date n'est pas dans le futur
            if date_entree > date.today():
                print("    ⚠ La date d'entrée ne peut pas être dans le futur.")
                continue

            # Vérifier que la date est raisonnable (pas avant 1950)
            if date_entree.year < 1950:
                print("    ⚠ La date semble incorrecte (avant 1950).")
                continue

            return date_entree

        except ValueError:
            print("    ✗ Format invalide. Utilisez JJ/MM/AAAA (ex: 15/03/2020)")


def mode_interactif():
    """Mode interactif pour saisir les dates une par une"""
    print("\n" + "="*70)
    print("MODE INTERACTIF - AFFECTATION DES DATES D'ENTRÉE")
    print("="*70 + "\n")

    personnel = get_personnel_sans_date_entree()

    if not personnel:
        print("✓ Tous les employés ont déjà une date d'entrée enregistrée.\n")
        return

    print(f"Trouvé {len(personnel)} employé(s) sans date d'entrée.\n")
    print("Instructions:")
    print("  - Saisissez la date au format JJ/MM/AAAA (ex: 15/03/2020)")
    print("  - Tapez 'skip' pour passer cet employé")
    print("  - Tapez 'quit' pour quitter\n")

    nb_modifies = 0
    nb_skipped = 0

    for i, emp in enumerate(personnel, 1):
        print(f"\n[{i}/{len(personnel)}] {emp['nom']} {emp['prenom']}")
        print(f"  Matricule: {emp['matricule']}")
        print(f"  Statut: {emp['statut']}")

        reponse = input("  Affecter une date d'entrée ? (o/n/quit) : ").strip().lower()

        if reponse == 'quit':
            print("\n⚠ Arrêt demandé par l'utilisateur.")
            break

        if reponse == 'n':
            nb_skipped += 1
            continue

        if reponse == 'o':
            date_entree = saisir_date()

            if date_entree is None:
                nb_skipped += 1
                continue

            # Confirmer
            date_str = date_entree.strftime("%d/%m/%Y")
            confirm = input(f"    Confirmer la date {date_str} ? (o/n) : ").strip().lower()

            if confirm == 'o':
                if affecter_date_entree(emp['id'], emp['nom'], emp['prenom'], date_entree):
                    print(f"    ✓ Date d'entrée affectée : {date_str}")
                    nb_modifies += 1
                else:
                    print(f"    ✗ Erreur lors de l'affectation")
            else:
                print("    ⚠ Annulé")
                nb_skipped += 1

    print("\n" + "="*70)
    print(f"RÉSUMÉ:")
    print(f"  - Employés traités : {len(personnel)}")
    print(f"  - Dates affectées  : {nb_modifies}")
    print(f"  - Ignorés/passés   : {nb_skipped}")
    print("="*70 + "\n")


def mode_date_unique():
    """Mode pour affecter la même date à tous les employés sans date"""
    print("\n" + "="*70)
    print("MODE DATE UNIQUE - AFFECTATION EN MASSE")
    print("="*70 + "\n")

    personnel = get_personnel_sans_date_entree()

    if not personnel:
        print("✓ Tous les employés ont déjà une date d'entrée enregistrée.\n")
        return

    print(f"Trouvé {len(personnel)} employé(s) sans date d'entrée:\n")

    for emp in personnel:
        print(f"  - {emp['nom']} {emp['prenom']} ({emp['matricule']})")

    print(f"\nVous allez affecter la MÊME date d'entrée à tous ces employés.")
    date_entree = saisir_date()

    if date_entree is None:
        print("\n⚠ Opération annulée.\n")
        return

    date_str = date_entree.strftime("%d/%m/%Y")
    confirm = input(f"\nConfirmer l'affectation de la date {date_str} à {len(personnel)} employés ? (o/n) : ").strip().lower()

    if confirm != 'o':
        print("\n⚠ Opération annulée.\n")
        return

    nb_modifies = 0

    for emp in personnel:
        if affecter_date_entree(emp['id'], emp['nom'], emp['prenom'], date_entree):
            print(f"  ✓ {emp['nom']} {emp['prenom']}")
            nb_modifies += 1
        else:
            print(f"  ✗ {emp['nom']} {emp['prenom']} - ERREUR")

    print("\n" + "="*70)
    print(f"RÉSUMÉ: {nb_modifies}/{len(personnel)} dates affectées")
    print("="*70 + "\n")


def afficher_statistiques():
    """Affiche les statistiques sur les dates d'entrée"""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    try:
        # Total employés actifs
        cur.execute("SELECT COUNT(*) as total FROM personnel WHERE statut = 'ACTIF'")
        total_actifs = cur.fetchone()['total']

        # Employés actifs avec date d'entrée
        cur.execute("""
            SELECT COUNT(*) as total
            FROM personnel p
            JOIN personnel_infos pi ON p.id = pi.operateur_id
            WHERE p.statut = 'ACTIF' AND pi.date_entree IS NOT NULL
        """)
        avec_date = cur.fetchone()['total']

        # Employés actifs sans date d'entrée
        sans_date = total_actifs - avec_date

        print("\n" + "="*70)
        print("STATISTIQUES - DATES D'ENTRÉE")
        print("="*70)
        print(f"\n  Employés actifs           : {total_actifs}")
        print(f"  Avec date d'entrée        : {avec_date}")
        print(f"  Sans date d'entrée        : {sans_date}")

        if total_actifs > 0:
            pourcentage = (avec_date / total_actifs) * 100
            print(f"  Taux de complétion        : {pourcentage:.1f}%")

        print("\n" + "="*70 + "\n")

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    print("\n" + "="*70)
    print("AFFECTATION DES DATES D'ENTRÉE - EMPLOYÉS EXISTANTS")
    print("="*70 + "\n")

    while True:
        afficher_statistiques()

        print("Choisissez un mode:")
        print("  1. Mode interactif (saisir date par date pour chaque employé)")
        print("  2. Mode date unique (affecter la même date à tous)")
        print("  3. Afficher les employés sans date d'entrée")
        print("  4. Quitter")

        choix = input("\nVotre choix (1-4) : ").strip()

        if choix == "1":
            mode_interactif()
        elif choix == "2":
            mode_date_unique()
        elif choix == "3":
            personnel = get_personnel_sans_date_entree()
            if not personnel:
                print("\n✓ Tous les employés ont une date d'entrée.\n")
            else:
                print(f"\n{len(personnel)} employé(s) sans date d'entrée:\n")
                for emp in personnel:
                    print(f"  - {emp['nom']} {emp['prenom']} ({emp['matricule']}) - Statut: {emp['statut']}")
                print()
        elif choix == "4":
            print("\nAu revoir!\n")
            break
        else:
            print("\n⚠ Choix invalide.\n")
