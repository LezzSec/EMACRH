import mysql.connector
from mysql.connector import Error
import sys

class DoublonManager:
    def __init__(self):
        self.connection = None
        self.connect_database()
    
    def connect_database(self):
        """Connexion à la base de données"""
        try:
            self.connection = mysql.connector.connect(
                host='localhost',
                database='emac_db',
                user='root',
                password='emacViodos$13'
            )
            if self.connection.is_connected():
                print("✓ Connexion réussie à la base de données\n")
        except Error as e:
            print(f"✗ Erreur de connexion : {e}")
            sys.exit(1)
    
    def get_doublons(self):
        """Récupère tous les doublons avec leurs informations"""
        query = """
            SELECT 
                p.id,
                p.nom,
                p.prenom,
                p.statut,
                p.matricule,
                p.numposte,
                s.nom_service,
                COUNT(poly.id) as nb_polyvalences,
                GROUP_CONCAT(
                    CONCAT(pos.poste_code, ' (Niv.', poly.niveau, ')')
                    ORDER BY pos.poste_code
                    SEPARATOR ', '
                ) as liste_polyvalences
            FROM personnel p
            LEFT JOIN services s ON p.service_id = s.id
            LEFT JOIN polyvalence poly ON p.id = poly.operateur_id
            LEFT JOIN postes pos ON poly.poste_id = pos.id
            WHERE EXISTS (
                SELECT 1 
                FROM personnel p2 
                WHERE p2.nom = p.nom 
                AND p2.id != p.id
            )
            GROUP BY p.id, p.nom, p.prenom, p.statut, p.matricule, p.numposte, s.nom_service
            ORDER BY p.nom, p.prenom, p.id
        """
        
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(query)
        return cursor.fetchall()
    
    def group_doublons(self, doublons):
        """Groupe les doublons par nom uniquement"""
        groupes = {}
        for doublon in doublons:
            key = doublon['nom'].strip().upper()
            if key not in groupes:
                groupes[key] = []
            groupes[key].append(doublon)
        return groupes
    
    def afficher_stats(self, groupes_doublons, total_doublons):
        """Affiche les statistiques"""
        print("\n" + "="*60)
        print(" STATISTIQUES ")
        print("="*60)
        print(f"Groupes de doublons: {len(groupes_doublons)}")
        print(f"Entrées en double: {total_doublons}")
        print(f"À nettoyer: {total_doublons - len(groupes_doublons)}")
        print("="*60 + "\n")
    
    def afficher_personne(self, person, index, total):
        """Affiche les détails d'une personne"""
        print(f"\n┌─ Entrée {index}/{total} " + "─"*40)
        print("│")
        
        # En-tête avec ID et statut
        print(f"│ ID: {person['id']} | [{person['statut']}]")
        print(f"│ Nom: {person['nom']}")
        print(f"│ Prénom: {person['prenom']}")
        
        # Informations de base
        print("│")
        matricule = person['matricule'] if person['matricule'] else 'Non défini'
        poste = person['numposte'] if person['numposte'] else 'Non défini'
        service = person['nom_service'] if person['nom_service'] else 'Non défini'
        
        print(f"│ Matricule: {matricule}")
        print(f"│ Poste: {poste}")
        print(f"│ Service: {service}")
        
        # Polyvalences
        print("│")
        if person['nb_polyvalences'] > 0:
            print(f"│ 📊 Polyvalences ({person['nb_polyvalences']}):")
            print(f"│ {person['liste_polyvalences']}")
        else:
            print("│ 📊 Aucune polyvalence")
        
        print("└" + "─"*58)
    
    def afficher_groupe(self, nom, groupe, numero_groupe, total_groupes):
        """Affiche un groupe de doublons"""
        print("\n" + "="*60)
        print(f" GROUPE {numero_groupe}/{total_groupes} ")
        print(f" 👤 {nom} ({len(groupe)} entrées) ")
        print("="*60)
        
        for idx, person in enumerate(groupe, 1):
            self.afficher_personne(person, idx, len(groupe))
    
    def supprimer_personne(self, person_id):
        """Supprime une personne et ses polyvalences"""
        try:
            cursor = self.connection.cursor()
            
            # S'assurer qu'il n'y a pas de transaction en cours
            if self.connection.in_transaction:
                self.connection.rollback()
            
            # Suppression (CASCADE s'occupe des polyvalences)
            cursor.execute("DELETE FROM personnel WHERE id = %s", (person_id,))
            
            # Commit
            self.connection.commit()
            
            cursor.close()
            
            print(f"\n✓ Personnel ID {person_id} supprimé avec succès !")
            return True
            
        except Error as e:
            if self.connection.in_transaction:
                self.connection.rollback()
            print(f"\n✗ Erreur lors de la suppression : {e}")
            return False
    
    def menu_groupe(self, groupe):
        """Menu pour gérer un groupe de doublons"""
        while True:
            print("\n" + "-"*60)
            print("Que voulez-vous faire ?")
            print(f"  [1-{len(groupe)}] Supprimer l'entrée correspondante")
            print("  [S] Passer au groupe suivant")
            print("  [Q] Quitter")
            
            choix = input("\nVotre choix : ").strip().upper()
            
            if choix == 'Q':
                return 'quit'
            elif choix == 'S':
                return 'skip'
            elif choix.isdigit():
                idx = int(choix) - 1
                if 0 <= idx < len(groupe):
                    person = groupe[idx]
                    print("\n⚠ Vous allez supprimer :")
                    print(f"   ID: {person['id']}")
                    print(f"   {person['nom']} {person['prenom']}")
                    print(f"   Polyvalences: {person['nb_polyvalences']}")
                    
                    confirm = input("\nConfirmer la suppression ? (oui/non) : ").strip().lower()
                    
                    if confirm == 'oui':
                        if self.supprimer_personne(person['id']):
                            return 'deleted'
                    else:
                        print("Suppression annulée")
                else:
                    print("✗ Numéro invalide")
            else:
                print("✗ Choix invalide")
    
    def run(self):
        """Lance l'application"""
        print("\n" + "="*60)
        print(" 🔍 GESTIONNAIRE DE DOUBLONS - PERSONNEL ")
        print("="*60)
        
        # Récupération des doublons
        doublons = self.get_doublons()
        
        if not doublons:
            print("\n✅ Aucun doublon détecté !")
            print("Votre base de données est propre.\n")
            return
        
        # Groupement
        groupes = self.group_doublons(doublons)
        
        # Affichage des stats
        self.afficher_stats(groupes, len(doublons))
        
        # Avertissement
        print("="*60)
        print(" ⚠ ATTENTION ")
        print("="*60)
        print("La suppression d'un personnel supprimera automatiquement")
        print("toutes ses polyvalences associées (CASCADE).\n")
        
        input("Appuyez sur Entrée pour continuer...")
        
        # Traitement de chaque groupe
        numero_groupe = 1
        total_groupes = len(groupes)
        
        for nom, groupe in list(groupes.items()):
            
            # Rafraîchir les données du groupe
            doublons_refresh = self.get_doublons()
            groupes_refresh = self.group_doublons(doublons_refresh)
            
            if nom not in groupes_refresh:
                continue  # Le groupe a été résolu
            
            groupe = groupes_refresh[nom]
            
            if len(groupe) == 1:
                continue  # Plus de doublon
            
            self.afficher_groupe(nom, groupe, numero_groupe, total_groupes)
            
            resultat = self.menu_groupe(groupe)
            
            if resultat == 'quit':
                print("\nAu revoir !\n")
                break
            elif resultat == 'deleted':
                print("✓ Groupe traité")
            
            numero_groupe += 1
        
        print("\n✓ Traitement terminé !\n")
    
    def close(self):
        """Ferme la connexion"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Connexion fermée.\n")

def main():
    manager = DoublonManager()
    try:
        manager.run()
    except KeyboardInterrupt:
        print("\n\nInterruption par l'utilisateur")
    finally:
        manager.close()

if __name__ == "__main__":
    main()