# -*- coding: utf-8 -*-
import json

ACTION_LABEL = {
    "INSERT": "Ajout",
    "UPDATE": "Modification",
    "DELETE": "Suppression",
    "ERROR":  "Erreur",
}

ACTION_CONFIG = {
    "INSERT":         ("+",   "Ajout de compétence",      "#4caf50", "#e8f5e9"),
    "UPDATE":         ("~",   "Modification de compétence","#f57f17", "#fff8e1"),
    "DELETE":         ("-",   "Suppression de compétence", "#f44336", "#ffebee"),
    "ERROR":          ("!",   "Erreur",                   "#d32f2f", "#ffebee"),
    "CONNEXION":      ("CNX", "Connexion utilisateur",     "#1976d2", "#e3f2fd"),
    "DECONNEXION":    ("DCX", "Déconnexion utilisateur",   "#455a64", "#eceff1"),
    "LOGOUT_TIMEOUT": ("TO",  "Déconnexion automatique",  "#7b1fa2", "#f3e5f5"),
}
_ACTION_CONFIG_DEFAULT = ("i", "Action", "#616161", "#f5f5f5")


def get_action_config(action: str) -> tuple:
    """Retourne (icône, libellé, couleur, couleur_fond) pour un type d'action."""
    return ACTION_CONFIG.get((action or "").upper(), _ACTION_CONFIG_DEFAULT)


def fr_action(a: str) -> str:
    return ACTION_LABEL.get((a or "").upper(), a or "")


def get_detailed_action_type(row: dict) -> str:
    action = row.get("action", "")
    desc = row.get("description") or ""

    try:
        data = json.loads(desc)
        if action.upper() == "INSERT":
            niveau = data.get("niveau", "?")
            return f"Ajout (N{niveau})"
        elif action.upper() == "UPDATE":
            changes = data.get("changes", {})
            if "niveau" in changes:
                old = changes["niveau"].get("old", "?")
                new = changes["niveau"].get("new", "?")
                return f"Modification (N{old}→N{new})"
            else:
                return "Modification"
        elif action.upper() == "DELETE":
            niveau = data.get("niveau", "?")
            return f"Suppression (N{niveau})"
    except (json.JSONDecodeError, ValueError):
        pass

    return fr_action(action)


def make_resume(row: dict) -> str:
    action = row.get("action", "")
    op_id = row.get("operateur_id")
    po_id = row.get("poste_id")
    desc = row.get("description") or ""

    op_name = row.get('op_name') or (f"#{op_id}" if op_id else None)
    po_name = row.get('po_name') or (f"Poste #{po_id}" if po_id else None)

    try:
        data = json.loads(desc)
    except (json.JSONDecodeError, ValueError):
        if desc:
            return desc[:100] + ("..." if len(desc) > 100 else "")
        return fr_action(action)

    try:
        if "operateur" in data:
            op_name = data["operateur"]
        if "poste" in data:
            po_name = data["poste"]

        if action.upper() == "INSERT":
            niveau = data.get("niveau", "?")
            return f"{op_name} > {po_name} : Niveau {niveau} (nouveau)"
        elif action.upper() == "UPDATE":
            changes = data.get("changes", {})
            if "niveau" in changes:
                old = changes["niveau"].get("old", "?")
                new = changes["niveau"].get("new", "?")
                return f"{op_name} > {po_name} : Niveau {old} -> {new}"
            else:
                return f"{op_name} > {po_name} : Modifié"
        elif action.upper() == "DELETE":
            niveau = data.get("niveau", "?")
            return f"{op_name} > {po_name} : Niveau {niveau} (supprimé)"
    except Exception:
        pass

    parts = []
    if op_name:
        parts.append(op_name)
    elif op_id:
        parts.append(f"#{op_id}")
    if po_name:
        parts.append(po_name)
    elif po_id:
        parts.append(f"Poste #{po_id}")

    if parts:
        return " > ".join(parts)
    return f"Action : {action}"
