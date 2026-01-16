from datetime import datetime
import json

def log_polyvalence_change(connection, action, operateur_id, poste_id, old_niveau=None, new_niveau=None):
    """
    Enregistre un changement de polyvalence dans l'historique.
    
    Args:
        connection: Connexion à la base de données
        action: 'INSERT', 'UPDATE', ou 'DELETE'
        operateur_id: ID de l'opérateur
        poste_id: ID du poste
        old_niveau: Ancien niveau (pour UPDATE et DELETE)
        new_niveau: Nouveau niveau (pour INSERT et UPDATE)
    """
    try:
        cursor = connection.cursor()
        
        # Récupérer les noms pour une description lisible
        cursor.execute("SELECT nom, prenom FROM personnel WHERE id = %s", (operateur_id,))
        op_row = cursor.fetchone()
        operateur_nom = f"{op_row[1]} {op_row[0]}" if op_row else f"ID {operateur_id}"
        
        cursor.execute("SELECT poste_code FROM postes WHERE id = %s", (poste_id,))
        poste_row = cursor.fetchone()
        poste_nom = poste_row[0] if poste_row else f"ID {poste_id}"
        
        # Construire la description en JSON (format compatible avec historique.py)
        if action == 'INSERT':
            description = json.dumps({
                "operateur": operateur_nom,
                "poste": poste_nom,
                "niveau": new_niveau,
                "type": "ajout"
            }, ensure_ascii=False)
            
        elif action == 'UPDATE':
            changes = {}
            if old_niveau != new_niveau:
                changes["niveau"] = {"old": old_niveau, "new": new_niveau}
            
            description = json.dumps({
                "operateur": operateur_nom,
                "poste": poste_nom,
                "changes": changes,
                "type": "modification"
            }, ensure_ascii=False)
            
        elif action == 'DELETE':
            description = json.dumps({
                "operateur": operateur_nom,
                "poste": poste_nom,
                "niveau": old_niveau,
                "type": "suppression"
            }, ensure_ascii=False)
        else:
            description = None
        
        # Récupérer l'utilisateur connecté
        utilisateur = None
        try:
            from core.services.auth_service import get_current_user
            current_user = get_current_user()
            if current_user:
                utilisateur = current_user.get('username') or f"{current_user.get('prenom', '')} {current_user.get('nom', '')}".strip()
        except Exception:
            pass

        # Enregistrer dans l'historique
        cursor.execute("""
            INSERT INTO historique (date_time, action, operateur_id, poste_id, description, utilisateur)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (datetime.now(), action, operateur_id, poste_id, description, utilisateur))

        cursor.close()
        return True

    except Exception as e:
        print(f"Erreur logging historique : {e}")
        return False