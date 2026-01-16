# -*- coding: utf-8 -*-
"""
Service de gestion des documents templates.

Ce service gère les templates de documents (formulaires d'évaluation, consignes, etc.)
qui peuvent être pré-remplis avec les informations de l'opérateur et ouverts pour impression.
"""

import os
import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from core.db.configbd import DatabaseCursor, DatabaseConnection
from core.services.logger import log_hist


def get_templates_dir() -> Path:
    """Retourne le répertoire des templates."""
    # En développement: App/templates/
    # En production (.exe): %APPDATA%/EMAC/templates/
    if getattr(sys, 'frozen', False):
        # Mode .exe
        app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
        return Path(app_data) / 'EMAC' / 'templates'
    else:
        # Mode développement
        return Path(__file__).parent.parent.parent / 'templates'


def get_temp_dir() -> Path:
    """Retourne le répertoire temporaire pour les fichiers générés."""
    temp_base = Path(tempfile.gettempdir()) / 'EMAC_templates'
    temp_base.mkdir(parents=True, exist_ok=True)
    return temp_base


import sys


def get_all_templates(actif_only: bool = True) -> List[Dict]:
    """
    Récupère tous les templates.

    Args:
        actif_only: Si True, ne retourne que les templates actifs

    Returns:
        Liste des templates avec leurs métadonnées
    """
    query = """
        SELECT id, nom, fichier_source, contexte, postes_associes,
               champ_operateur, champ_auditeur, champ_date,
               obligatoire, description, ordre_affichage, actif
        FROM documents_templates
    """
    if actif_only:
        query += " WHERE actif = TRUE"
    query += " ORDER BY contexte, ordre_affichage"

    with DatabaseCursor(dictionary=True) as cur:
        cur.execute(query)
        templates = cur.fetchall()

    # Parser le JSON des postes_associes
    for t in templates:
        if t['postes_associes']:
            try:
                t['postes_associes'] = json.loads(t['postes_associes'])
            except json.JSONDecodeError:
                t['postes_associes'] = []
        else:
            t['postes_associes'] = []

    return templates


def get_templates_by_contexte(contexte: str) -> List[Dict]:
    """
    Récupère les templates pour un contexte donné.

    Args:
        contexte: 'NOUVEL_OPERATEUR', 'NIVEAU_3', ou 'POSTE'

    Returns:
        Liste des templates pour ce contexte
    """
    query = """
        SELECT id, nom, fichier_source, contexte, postes_associes,
               champ_operateur, champ_auditeur, champ_date,
               obligatoire, description, ordre_affichage
        FROM documents_templates
        WHERE contexte = %s AND actif = TRUE
        ORDER BY ordre_affichage
    """

    with DatabaseCursor(dictionary=True) as cur:
        cur.execute(query, (contexte,))
        templates = cur.fetchall()

    for t in templates:
        if t['postes_associes']:
            try:
                t['postes_associes'] = json.loads(t['postes_associes'])
            except json.JSONDecodeError:
                t['postes_associes'] = []
        else:
            t['postes_associes'] = []

    return templates


def get_templates_for_poste(code_poste: str) -> List[Dict]:
    """
    Récupère les templates associés à un poste spécifique.

    Args:
        code_poste: Code du poste (ex: "506")

    Returns:
        Liste des templates pour ce poste
    """
    # Récupérer tous les templates de type POSTE
    all_poste_templates = get_templates_by_contexte('POSTE')

    # Filtrer ceux qui contiennent le code poste
    matching = []
    for t in all_poste_templates:
        if code_poste in t['postes_associes']:
            matching.append(t)

    return matching


def get_templates_for_nouvel_operateur() -> List[Dict]:
    """Récupère les templates pour un nouvel opérateur."""
    return get_templates_by_contexte('NOUVEL_OPERATEUR')


def get_templates_for_niveau_3() -> List[Dict]:
    """Récupère les templates pour le passage au niveau 3."""
    return get_templates_by_contexte('NIVEAU_3')


def generate_filled_template(
    template_id: int,
    operateur_nom: str = "",
    operateur_prenom: str = "",
    auditeur_nom: str = "",
    date_str: str = None
) -> Tuple[bool, str, Optional[str]]:
    """
    Génère une copie du template pré-remplie avec les informations fournies.

    Args:
        template_id: ID du template
        operateur_nom: Nom de l'opérateur
        operateur_prenom: Prénom de l'opérateur
        auditeur_nom: Nom de l'auditeur/évaluateur
        date_str: Date au format DD/MM/YYYY (par défaut: aujourd'hui)

    Returns:
        Tuple (succès, message, chemin_fichier_généré)
    """
    # Récupérer les infos du template
    with DatabaseCursor(dictionary=True) as cur:
        cur.execute("""
            SELECT * FROM documents_templates WHERE id = %s
        """, (template_id,))
        template = cur.fetchone()

    if not template:
        return False, "Template non trouvé", None

    # Construire le chemin source
    templates_dir = get_templates_dir()
    source_path = templates_dir / template['fichier_source'].replace('templates/', '')

    if not source_path.exists():
        return False, f"Fichier template non trouvé: {source_path}", None

    # Date par défaut
    if not date_str:
        date_str = datetime.now().strftime('%d/%m/%Y')

    # Nom complet de l'opérateur
    operateur_complet = f"{operateur_prenom} {operateur_nom}".strip()

    # Créer le nom du fichier de sortie
    extension = source_path.suffix
    safe_name = f"{template['nom']}_{operateur_complet}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    safe_name = "".join(c for c in safe_name if c.isalnum() or c in (' ', '_', '-')).strip()
    output_filename = f"{safe_name}{extension}"

    # Répertoire temporaire
    temp_dir = get_temp_dir()
    output_path = temp_dir / output_filename

    # Copier le fichier
    shutil.copy2(source_path, output_path)

    # Pré-remplir si c'est un Excel
    if extension.lower() in ('.xlsx', '.xlsm', '.xls'):
        try:
            success, msg = _fill_excel_template(
                output_path,
                template['champ_operateur'],
                template['champ_auditeur'],
                template['champ_date'],
                operateur_complet,
                auditeur_nom,
                date_str
            )
            if not success:
                return False, msg, None
        except Exception as e:
            # Si le pré-remplissage échoue, on garde le fichier non rempli
            pass

    # Logger l'action
    log_hist(
        "GENERATION_TEMPLATE",
        f"Génération du template '{template['nom']}' pour {operateur_complet}"
    )

    return True, "Fichier généré avec succès", str(output_path)


def _fill_excel_template(
    file_path: Path,
    cell_operateur: str,
    cell_auditeur: str,
    cell_date: str,
    operateur_nom: str,
    auditeur_nom: str,
    date_str: str
) -> Tuple[bool, str]:
    """
    Remplit les cellules d'un fichier Excel avec les données fournies.

    Args:
        file_path: Chemin du fichier Excel
        cell_operateur: Référence de la cellule pour l'opérateur (ex: "D7")
        cell_auditeur: Référence de la cellule pour l'auditeur
        cell_date: Référence de la cellule pour la date
        operateur_nom: Nom complet de l'opérateur
        auditeur_nom: Nom de l'auditeur
        date_str: Date formatée

    Returns:
        Tuple (succès, message)
    """
    file_path = Path(file_path)
    extension = file_path.suffix.lower()

    # Fichiers .xls (ancien format Excel 97-2003)
    # ⚠️ Le pré-remplissage n'est pas supporté pour les fichiers .xls
    # Le fichier est copié mais non pré-rempli. Pour le pré-remplissage automatique,
    # convertissez le template en .xlsx (Excel > Enregistrer sous > .xlsx)
    if extension == '.xls':
        # Retourner succès mais avec un message indiquant que le pré-remplissage n'est pas fait
        return True, "Fichier .xls copié (pré-remplissage non supporté pour ce format - convertir en .xlsx recommandé)"

    # Fichiers .xlsx et .xlsm (format moderne)
    else:
        try:
            import openpyxl

            # Charger le fichier (keep_vba pour les .xlsm)
            wb = openpyxl.load_workbook(file_path, keep_vba=True)
            ws = wb.active

            # Remplir les cellules si spécifiées
            if cell_operateur and operateur_nom:
                ws[cell_operateur] = operateur_nom

            if cell_auditeur and auditeur_nom:
                ws[cell_auditeur] = auditeur_nom

            if cell_date and date_str:
                ws[cell_date] = date_str

            # Sauvegarder
            wb.save(file_path)
            wb.close()

            return True, "Fichier rempli avec succès"

        except Exception as e:
            return False, f"Erreur lors du remplissage: {str(e)}"


def open_template_file(file_path: str) -> Tuple[bool, str]:
    """
    Ouvre un fichier template avec l'application par défaut du système.

    Args:
        file_path: Chemin du fichier à ouvrir

    Returns:
        Tuple (succès, message)
    """
    import subprocess
    import platform

    try:
        if platform.system() == 'Windows':
            os.startfile(file_path)
        elif platform.system() == 'Darwin':  # macOS
            subprocess.run(['open', file_path], check=True)
        else:  # Linux
            subprocess.run(['xdg-open', file_path], check=True)

        return True, "Fichier ouvert"

    except Exception as e:
        return False, f"Erreur lors de l'ouverture: {str(e)}"


def check_templates_table_exists() -> bool:
    """Vérifie si la table documents_templates existe."""
    try:
        with DatabaseCursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_schema = DATABASE()
                AND table_name = 'documents_templates'
            """)
            result = cur.fetchone()
            return result[0] > 0
    except Exception:
        return False


def get_template_by_id(template_id: int) -> Optional[Dict]:
    """Récupère un template par son ID."""
    with DatabaseCursor(dictionary=True) as cur:
        cur.execute("""
            SELECT * FROM documents_templates WHERE id = %s
        """, (template_id,))
        template = cur.fetchone()

    if template and template['postes_associes']:
        try:
            template['postes_associes'] = json.loads(template['postes_associes'])
        except json.JSONDecodeError:
            template['postes_associes'] = []

    return template


def get_postes_for_operateur(operateur_id: int) -> List[str]:
    """
    Récupère les codes de tous les postes auxquels un opérateur est affecté.

    Args:
        operateur_id: ID de l'opérateur

    Returns:
        Liste des codes postes
    """
    with DatabaseCursor(dictionary=True) as cur:
        cur.execute("""
            SELECT DISTINCT p.numposte
            FROM polyvalence pv
            JOIN postes p ON pv.poste_id = p.id
            WHERE pv.operateur_id = %s
        """, (operateur_id,))
        results = cur.fetchall()

    return [r['numposte'] for r in results if r['numposte']]


def get_all_templates_for_operateur(operateur_id: int) -> Dict[str, List[Dict]]:
    """
    Récupère tous les templates applicables à un opérateur, groupés par contexte.

    Args:
        operateur_id: ID de l'opérateur

    Returns:
        Dict avec clés 'NOUVEL_OPERATEUR', 'NIVEAU_3', 'POSTE'
    """
    result = {
        'NOUVEL_OPERATEUR': get_templates_for_nouvel_operateur(),
        'NIVEAU_3': get_templates_for_niveau_3(),
        'POSTE': []
    }

    # Récupérer les postes de l'opérateur
    postes = get_postes_for_operateur(operateur_id)

    # Récupérer les templates pour chaque poste
    seen_ids = set()
    for code_poste in postes:
        templates = get_templates_for_poste(code_poste)
        for t in templates:
            if t['id'] not in seen_ids:
                seen_ids.add(t['id'])
                result['POSTE'].append(t)

    return result
