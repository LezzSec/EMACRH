# -*- coding: utf-8 -*-
"""
Service de génération documentaire pour les formations.

Génère les documents officiels pré-remplis à partir des données saisies dans l'application :
  1. Demande de formation (EQ 07 30)
  2. Feuille d'émargement / Attestation de présence (EQ 07 17)
  3. Fiche de suivi de formation (EQ 07 02 01)

Usage:
    from core.services.formation_export_service import FormationExportService

    success, msg, path = FormationExportService.generate_dossier_formation(formation_data)
    # path = chemin vers le fichier xlsx généré
"""

import os
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

from core.utils.logging_config import get_logger

logger = get_logger(__name__)

try:
    import openpyxl
    from openpyxl.styles import (
        Font, Alignment, Border, Side, PatternFill, numbers
    )
    from openpyxl.utils import get_column_letter
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False
    logger.warning("openpyxl non disponible - génération xlsx impossible")


# Répertoire de sortie par défaut
_EXPORTS_DIR = Path(__file__).parent.parent.parent / "exports" / "formations"

# Couleurs
_BLUE_HEADER = "1F4E79"
_LIGHT_BLUE = "BDD7EE"
_GREY_LABEL = "F2F2F2"
_BORDER_COLOR = "4472C4"


def _thin_border() -> Border:
    side = Side(style='thin', color="000000")
    return Border(left=side, right=side, top=side, bottom=side)


def _header_font(size: int = 11) -> Font:
    return Font(name="Calibri", bold=True, size=size, color="FFFFFF")


def _label_font() -> Font:
    return Font(name="Calibri", bold=True, size=10)


def _value_font() -> Font:
    return Font(name="Calibri", size=10)


def _title_font(size: int = 14) -> Font:
    return Font(name="Calibri", bold=True, size=size, color=_BLUE_HEADER)


def _header_fill() -> PatternFill:
    return PatternFill("solid", fgColor=_BLUE_HEADER)


def _label_fill() -> PatternFill:
    return PatternFill("solid", fgColor=_GREY_LABEL)


def _accent_fill() -> PatternFill:
    return PatternFill("solid", fgColor=_LIGHT_BLUE)


def _set_cell(ws, coordinate: str, value, font=None, fill=None,
              alignment=None, border=None, number_format: str = None):
    cell = ws[coordinate]
    cell.value = value
    if font:
        cell.font = font
    if fill:
        cell.fill = fill
    if alignment:
        cell.alignment = alignment
    if border:
        cell.border = border
    if number_format:
        cell.number_format = number_format


def _fmt_date(d) -> str:
    if d is None:
        return ""
    if isinstance(d, (date, datetime)):
        return d.strftime("%d/%m/%Y")
    return str(d)


def _fmt_duree(heures) -> str:
    if not heures:
        return ""
    h = float(heures)
    jours = h / 7
    if h == int(h):
        return f"{int(h)} h ({jours:.1f} j)"
    return f"{h:.1f} h ({jours:.1f} j)"


# ============================  FEUILLE 1 : DEMANDE  ============================

def _build_demande(wb: "openpyxl.Workbook", data: Dict):
    ws = wb.create_sheet("Demande de formation (EQ 07 30)")

    # Largeurs de colonnes
    col_widths = [2, 2, 22, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 14]
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    # Hauteurs de lignes
    for r in range(1, 50):
        ws.row_dimensions[r].height = 18

    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    left = Alignment(horizontal="left", vertical="center", wrap_text=True)
    right_al = Alignment(horizontal="right", vertical="center")

    border = _thin_border()

    # --- Titre ---
    ws.merge_cells("C1:N2")
    _set_cell(ws, "C1", "DEMANDE DE FORMATION",
              font=_title_font(16), alignment=center)
    ws.merge_cells("O1:Q2")
    _set_cell(ws, "O1", "EQ 07 30 rev1",
              font=_value_font(), alignment=right_al)
    ws.row_dimensions[1].height = 30
    ws.row_dimensions[2].height = 20

    # --- Ligne vide ---
    ws.row_dimensions[3].height = 8

    # --- Salarié ---
    ws.merge_cells("C4:Q4")
    _set_cell(ws, "C4", "INFORMATIONS SALARIÉ",
              font=_header_font(11), fill=_header_fill(), alignment=center)

    # Nom
    ws.merge_cells("C5:D5")
    _set_cell(ws, "C5", "Nom :", font=_label_font(), fill=_label_fill(),
              alignment=left, border=border)
    ws.merge_cells("E5:G5")
    _set_cell(ws, "E5", data.get('nom', '').upper(),
              font=_value_font(), alignment=left, border=border)

    # Prénom
    ws.merge_cells("H5:I5")
    _set_cell(ws, "H5", "Prénom :", font=_label_font(), fill=_label_fill(),
              alignment=left, border=border)
    ws.merge_cells("J5:L5")
    _set_cell(ws, "J5", data.get('prenom', ''),
              font=_value_font(), alignment=left, border=border)

    # Service
    ws.merge_cells("M5:N5")
    _set_cell(ws, "M5", "Service :", font=_label_font(), fill=_label_fill(),
              alignment=left, border=border)
    ws.merge_cells("O5:Q5")
    _set_cell(ws, "O5", data.get('service', ''),
              font=_value_font(), alignment=left, border=border)

    ws.row_dimensions[5].height = 22

    # --- Formation ---
    ws.row_dimensions[6].height = 8

    ws.merge_cells("C7:Q7")
    _set_cell(ws, "C7", "INFORMATIONS FORMATION",
              font=_header_font(11), fill=_header_fill(), alignment=center)

    # Intitulé
    ws.merge_cells("C8:D8")
    _set_cell(ws, "C8", "Intitulé :", font=_label_font(), fill=_label_fill(),
              alignment=left, border=border)
    ws.merge_cells("E8:Q8")
    _set_cell(ws, "E8", data.get('intitule', ''),
              font=_value_font(), alignment=left, border=border)
    ws.row_dimensions[8].height = 22

    # Objectif
    ws.merge_cells("C9:D10")
    _set_cell(ws, "C9", "Objectif :", font=_label_font(), fill=_label_fill(),
              alignment=Alignment(horizontal="left", vertical="top"))
    ws.merge_cells("E9:Q10")
    _set_cell(ws, "E9", data.get('objectif', ''),
              font=_value_font(),
              alignment=Alignment(horizontal="left", vertical="top", wrap_text=True))
    ws.row_dimensions[9].height = 22
    ws.row_dimensions[10].height = 22

    # Organisme
    ws.merge_cells("C11:D11")
    _set_cell(ws, "C11", "Organisme :", font=_label_font(), fill=_label_fill(),
              alignment=left, border=border)
    ws.merge_cells("E11:H11")
    _set_cell(ws, "E11", data.get('organisme', ''),
              font=_value_font(), alignment=left, border=border)

    # Lieu
    ws.merge_cells("I11:J11")
    _set_cell(ws, "I11", "Lieu :", font=_label_font(), fill=_label_fill(),
              alignment=left, border=border)
    ws.merge_cells("K11:N11")
    _set_cell(ws, "K11", data.get('lieu', ''),
              font=_value_font(), alignment=left, border=border)

    # Coût
    ws.merge_cells("O11:P11")
    _set_cell(ws, "O11", "Coût :", font=_label_font(), fill=_label_fill(),
              alignment=left, border=border)
    cout = data.get('cout')
    _set_cell(ws, "Q11",
              f"{float(cout):.2f} €" if cout else "",
              font=_value_font(), alignment=left, border=border)

    ws.row_dimensions[11].height = 22

    # Dates
    ws.merge_cells("C12:D12")
    _set_cell(ws, "C12", "Date début :", font=_label_font(), fill=_label_fill(),
              alignment=left, border=border)
    ws.merge_cells("E12:F12")
    _set_cell(ws, "E12", _fmt_date(data.get('date_debut')),
              font=_value_font(), alignment=center, border=border)

    ws.merge_cells("G12:H12")
    _set_cell(ws, "G12", "Date fin :", font=_label_font(), fill=_label_fill(),
              alignment=left, border=border)
    ws.merge_cells("I12:J12")
    _set_cell(ws, "I12", _fmt_date(data.get('date_fin')),
              font=_value_font(), alignment=center, border=border)

    ws.merge_cells("K12:L12")
    _set_cell(ws, "K12", "Durée :", font=_label_font(), fill=_label_fill(),
              alignment=left, border=border)
    ws.merge_cells("M12:Q12")
    _set_cell(ws, "M12", _fmt_duree(data.get('duree_heures')),
              font=_value_font(), alignment=left, border=border)

    ws.row_dimensions[12].height = 22

    # Formateur
    ws.merge_cells("C13:D13")
    _set_cell(ws, "C13", "Formateur :", font=_label_font(), fill=_label_fill(),
              alignment=left, border=border)
    ws.merge_cells("E13:Q13")
    _set_cell(ws, "E13", data.get('formateur', ''),
              font=_value_font(), alignment=left, border=border)
    ws.row_dimensions[13].height = 22

    # Commentaire / Observations
    ws.merge_cells("C14:D15")
    _set_cell(ws, "C14", "Observations :", font=_label_font(), fill=_label_fill(),
              alignment=Alignment(horizontal="left", vertical="top"))
    ws.merge_cells("E14:Q15")
    _set_cell(ws, "E14", data.get('commentaire', ''),
              font=_value_font(),
              alignment=Alignment(horizontal="left", vertical="top", wrap_text=True))
    ws.row_dimensions[14].height = 22
    ws.row_dimensions[15].height = 22

    # --- Signatures ---
    ws.row_dimensions[16].height = 8
    ws.merge_cells("C17:Q17")
    _set_cell(ws, "C17", "SIGNATURES",
              font=_header_font(11), fill=_header_fill(), alignment=center)

    ws.row_dimensions[18].height = 18
    headers_sig = [("C18:F18", "Demandeur"), ("G18:J18", "Date"),
                   ("K18:N18", "Responsable direct"), ("O18:Q18", "Visa")]
    for rng, label in headers_sig:
        ws.merge_cells(rng)
        _set_cell(ws, rng.split(":")[0], label,
                  font=_label_font(), fill=_label_fill(), alignment=center, border=border)

    ws.merge_cells("C19:F21")
    ws.merge_cells("G19:J21")
    ws.merge_cells("K19:N21")
    ws.merge_cells("O19:Q21")
    for cell_coord in ["C19", "G19", "K19", "O19"]:
        _set_cell(ws, cell_coord, "",
                  font=_value_font(), border=border,
                  alignment=Alignment(horizontal="center", vertical="center"))
    for r in [19, 20, 21]:
        ws.row_dimensions[r].height = 22

    ws.row_dimensions[22].height = 8
    ws.merge_cells("C23:F23")
    _set_cell(ws, "C23", "Le demandeur",
              font=_label_font(), alignment=center)
    ws.merge_cells("K23:N23")
    _set_cell(ws, "K23", "Le responsable hiérarchique",
              font=_label_font(), alignment=center)

    # Note bas de page
    ws.row_dimensions[24].height = 8
    ws.merge_cells("B25:Q25")
    _set_cell(ws, "B25",
              "Cette demande devra être présentée au responsable hiérarchique "
              "et à la direction des Ressources Humaines.",
              font=Font(name="Calibri", size=9, italic=True),
              alignment=Alignment(horizontal="center", vertical="center", wrap_text=True))


# ========================  FEUILLE 2 : ÉMARGEMENT  ========================

def _build_emargement(wb: "openpyxl.Workbook", data: Dict):
    ws = wb.create_sheet("Feuille d'émargement (EQ 07 17)")

    col_widths = [2, 4, 30, 16, 16, 16, 16, 16, 16, 2]
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    left = Alignment(horizontal="left", vertical="center", wrap_text=True)
    border = _thin_border()

    # --- Titre ---
    ws.merge_cells("C1:I2")
    _set_cell(ws, "C1", "FEUILLE D'ÉMARGEMENT / ATTESTATION DE PRÉSENCE",
              font=_title_font(14), alignment=center)
    ws.merge_cells("C3:I3")
    _set_cell(ws, "C3", "EQ 07 17 rév.2",
              font=_value_font(),
              alignment=Alignment(horizontal="right", vertical="center"))
    ws.row_dimensions[1].height = 28
    ws.row_dimensions[2].height = 20

    # --- Infos formation ---
    ws.row_dimensions[4].height = 8

    ws.merge_cells("C5:D5")
    _set_cell(ws, "C5", "Intitulé :", font=_label_font(), fill=_label_fill(),
              alignment=left, border=border)
    ws.merge_cells("E5:I5")
    _set_cell(ws, "E5", data.get('intitule', ''),
              font=_value_font(), alignment=left, border=border)
    ws.row_dimensions[5].height = 22

    ws.merge_cells("C6:D6")
    _set_cell(ws, "C6", "Lieu :", font=_label_font(), fill=_label_fill(),
              alignment=left, border=border)
    ws.merge_cells("E6:F6")
    _set_cell(ws, "E6", data.get('lieu', ''),
              font=_value_font(), alignment=left, border=border)

    ws.merge_cells("G6:H6")
    _set_cell(ws, "G6", "Durée :", font=_label_font(), fill=_label_fill(),
              alignment=left, border=border)
    _set_cell(ws, "I6", _fmt_duree(data.get('duree_heures')),
              font=_value_font(), alignment=left, border=border)
    ws.row_dimensions[6].height = 22

    ws.merge_cells("C7:D7")
    _set_cell(ws, "C7", "Date(s) :", font=_label_font(), fill=_label_fill(),
              alignment=left, border=border)
    dates_str = _fmt_date(data.get('date_debut'))
    if data.get('date_fin') and data.get('date_fin') != data.get('date_debut'):
        dates_str += f"  au  {_fmt_date(data.get('date_fin'))}"
    ws.merge_cells("E7:F7")
    _set_cell(ws, "E7", dates_str,
              font=_value_font(), alignment=left, border=border)

    ws.merge_cells("G7:H7")
    _set_cell(ws, "G7", "Organisme :", font=_label_font(), fill=_label_fill(),
              alignment=left, border=border)
    _set_cell(ws, "I7", data.get('organisme', ''),
              font=_value_font(), alignment=left, border=border)
    ws.row_dimensions[7].height = 22

    ws.merge_cells("C8:D8")
    _set_cell(ws, "C8", "Formateur :", font=_label_font(), fill=_label_fill(),
              alignment=left, border=border)
    ws.merge_cells("E8:I8")
    _set_cell(ws, "E8", data.get('formateur', ''),
              font=_value_font(), alignment=left, border=border)
    ws.row_dimensions[8].height = 22

    # --- Tableau des stagiaires ---
    ws.row_dimensions[9].height = 8

    ws.merge_cells("C10:I10")
    _set_cell(ws, "C10", "LISTE DES STAGIAIRES",
              font=_header_font(11), fill=_header_fill(), alignment=center)
    ws.row_dimensions[10].height = 20

    # En-têtes
    headers = ["N°", "Nom et Prénom du stagiaire", "Signature Matin",
               "Signature Après-midi", "Nb heures", "Observations"]
    col_map = ["C", "D", "F", "G", "H", "I"]
    ws.merge_cells("C11:C11")
    ws.merge_cells("D11:E11")
    ws.merge_cells("F11:F11")
    ws.merge_cells("G11:G11")
    ws.merge_cells("H11:H11")
    ws.merge_cells("I11:I11")
    header_cells = ["C11", "D11", "F11", "G11", "H11", "I11"]
    for cell_c, label in zip(header_cells, headers):
        _set_cell(ws, cell_c, label,
                  font=_label_font(), fill=_accent_fill(),
                  alignment=center, border=border)
    ws.row_dimensions[11].height = 30

    # Pré-remplir la première ligne avec le stagiaire de la formation
    nom_prenom = f"{data.get('prenom', '')} {data.get('nom', '').upper()}".strip()
    row = 12
    _set_cell(ws, f"C{row}", "1", font=_value_font(), alignment=center, border=border)
    ws.merge_cells(f"D{row}:E{row}")
    _set_cell(ws, f"D{row}", nom_prenom,
              font=_value_font(), alignment=left, border=border)
    _set_cell(ws, f"F{row}", "", border=border)
    _set_cell(ws, f"G{row}", "", border=border)
    _set_cell(ws, f"H{row}", "", border=border)
    _set_cell(ws, f"I{row}", "", border=border)
    ws.row_dimensions[row].height = 22

    # Lignes vides supplémentaires (2 à 15)
    for i in range(2, 16):
        row = 12 + i - 1
        _set_cell(ws, f"C{row}", str(i), font=_value_font(), alignment=center, border=border)
        ws.merge_cells(f"D{row}:E{row}")
        _set_cell(ws, f"D{row}", "", border=border)
        _set_cell(ws, f"F{row}", "", border=border)
        _set_cell(ws, f"G{row}", "", border=border)
        _set_cell(ws, f"H{row}", "", border=border)
        _set_cell(ws, f"I{row}", "", border=border)
        ws.row_dimensions[row].height = 22

    # Signature formateur
    last = 12 + 15
    ws.row_dimensions[last].height = 8
    ws.merge_cells(f"C{last+1}:D{last+1}")
    _set_cell(ws, f"C{last+1}", "Signature du Formateur :",
              font=_label_font(), fill=_label_fill(),
              alignment=left, border=border)
    ws.merge_cells(f"E{last+1}:I{last+1}")
    _set_cell(ws, f"E{last+1}", "",
              font=_value_font(), border=border)
    ws.row_dimensions[last + 1].height = 40

    note_row = last + 2
    ws.merge_cells(f"C{note_row}:I{note_row}")
    _set_cell(ws, f"C{note_row}",
              "* Par ma signature, j'atteste avoir reçu / dispensé la formation ci-dessus.",
              font=Font(name="Calibri", size=9, italic=True),
              alignment=Alignment(horizontal="center", vertical="center"))


# ======================  FEUILLE 3 : FICHE DE SUIVI  ======================

def _build_suivi(wb: "openpyxl.Workbook", data: Dict):
    ws = wb.create_sheet("Fiche de suivi (EQ 07 02 01)")

    col_widths = [2, 4, 22, 16, 16, 14, 14, 14, 14, 2]
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    left = Alignment(horizontal="left", vertical="center", wrap_text=True)
    border = _thin_border()

    # --- Titre ---
    ws.merge_cells("C1:I2")
    _set_cell(ws, "C1", "FICHE DE SUIVI DE FORMATION",
              font=_title_font(16), alignment=center)
    ws.merge_cells("C3:I3")
    _set_cell(ws, "C3", "EQ 07 02 01 rev.6",
              font=_value_font(),
              alignment=Alignment(horizontal="right", vertical="center"))
    ws.row_dimensions[1].height = 28

    # --- Infos ---
    ws.row_dimensions[4].height = 8

    ws.merge_cells("C5:D5")
    _set_cell(ws, "C5", "Formation réalisée du :",
              font=_label_font(), fill=_label_fill(), alignment=left, border=border)
    ws.merge_cells("E5:F5")
    _set_cell(ws, "E5", _fmt_date(data.get('date_debut')),
              font=_value_font(), alignment=center, border=border)
    _set_cell(ws, "G5", "au",
              font=_label_font(), alignment=center, border=border)
    ws.merge_cells("H5:I5")
    _set_cell(ws, "H5", _fmt_date(data.get('date_fin')),
              font=_value_font(), alignment=center, border=border)
    ws.row_dimensions[5].height = 22

    ws.merge_cells("C6:D6")
    _set_cell(ws, "C6", "Durée de la formation :",
              font=_label_font(), fill=_label_fill(), alignment=left, border=border)
    ws.merge_cells("E6:I6")
    _set_cell(ws, "E6", _fmt_duree(data.get('duree_heures')),
              font=_value_font(), alignment=left, border=border)
    ws.row_dimensions[6].height = 22

    # --- Stagiaire / Organisme ---
    ws.row_dimensions[7].height = 8

    ws.merge_cells("C8:D8")
    _set_cell(ws, "C8", "STAGIAIRE",
              font=_header_font(11), fill=_header_fill(), alignment=center)
    ws.merge_cells("F8:I8")
    _set_cell(ws, "F8", "ORGANISME DE FORMATION",
              font=_header_font(11), fill=_header_fill(), alignment=center)

    ws.merge_cells("C9:D9")
    _set_cell(ws, "C9", "Nom :", font=_label_font(), fill=_label_fill(),
              alignment=left, border=border)
    _set_cell(ws, "E9", data.get('nom', '').upper(),
              font=Font(name="Calibri", bold=True, size=11),
              alignment=left, border=border)
    ws.merge_cells("F9:G9")
    _set_cell(ws, "F9", "Raison sociale :", font=_label_font(), fill=_label_fill(),
              alignment=left, border=border)
    ws.merge_cells("H9:I9")
    _set_cell(ws, "H9", data.get('organisme', ''),
              font=_value_font(), alignment=left, border=border)
    ws.row_dimensions[9].height = 22

    ws.merge_cells("C10:D10")
    _set_cell(ws, "C10", "Prénom :", font=_label_font(), fill=_label_fill(),
              alignment=left, border=border)
    _set_cell(ws, "E10", data.get('prenom', ''),
              font=Font(name="Calibri", bold=True, size=11),
              alignment=left, border=border)
    ws.merge_cells("F10:G10")
    _set_cell(ws, "F10", "Intitulé :", font=_label_font(), fill=_label_fill(),
              alignment=left, border=border)
    ws.merge_cells("H10:I10")
    _set_cell(ws, "H10", data.get('intitule', ''),
              font=_value_font(),
              alignment=Alignment(horizontal="left", vertical="center", wrap_text=True),
              border=border)
    ws.row_dimensions[10].height = 36

    ws.merge_cells("F11:G11")
    _set_cell(ws, "F11", "Lieu :", font=_label_font(), fill=_label_fill(),
              alignment=left, border=border)
    ws.merge_cells("H11:I11")
    _set_cell(ws, "H11", data.get('lieu', ''),
              font=_value_font(), alignment=left, border=border)
    ws.row_dimensions[11].height = 22

    # --- Questionnaire satisfaction ---
    ws.row_dimensions[12].height = 8

    ws.merge_cells("C13:I13")
    _set_cell(ws, "C13",
              "Ce document permet d'évaluer la satisfaction du stagiaire en fin de formation "
              "ainsi que l'atteinte des objectifs pédagogiques.",
              font=Font(name="Calibri", size=9, italic=True),
              alignment=Alignment(horizontal="left", vertical="center", wrap_text=True))
    ws.row_dimensions[13].height = 28

    # En-têtes questionnaire
    ws.merge_cells("C14:G14")
    _set_cell(ws, "C14", "ÉVALUATION DE LA FORMATION",
              font=_header_font(10), fill=_header_fill(), alignment=center)
    _set_cell(ws, "H14", "OUI", font=_header_font(10), fill=_header_fill(), alignment=center)
    _set_cell(ws, "I14", "NON", font=_header_font(10), fill=_header_fill(), alignment=center)
    ws.row_dimensions[14].height = 20

    questions = [
        "1. Organisation et déroulement de la formation",
        "2. Le contenu est clair et adapté",
        "3. Conformité du contenu au programme",
        "4. Animation de la formation (aptitude, motivation, compétence)",
        "5. Qualité des supports pédagogiques",
        "6. Qualité du matériel audiovisuel",
        "7. Progression de la formation (durée, rythme)",
        "8. Organisation matérielle : convocation, lieu, pauses",
        "9. L'objectif de la formation est atteint ?",
        "10. La composition du groupe est satisfaisante ?",
    ]

    for i, q in enumerate(questions):
        row = 15 + i
        ws.merge_cells(f"C{row}:G{row}")
        _set_cell(ws, f"C{row}", q,
                  font=_value_font(), alignment=left, border=border)
        _set_cell(ws, f"H{row}", "",
                  font=_value_font(), alignment=center, border=border)
        _set_cell(ws, f"I{row}", "",
                  font=_value_font(), alignment=center, border=border)
        ws.row_dimensions[row].height = 18

    note_row = 25
    ws.merge_cells(f"C{note_row}:G{note_row}")
    _set_cell(ws, f"C{note_row}", "Note globale :",
              font=_label_font(), fill=_label_fill(), alignment=left, border=border)
    ws.merge_cells(f"H{note_row}:I{note_row}")
    _set_cell(ws, f"H{note_row}", "... / 10",
              font=_value_font(), alignment=center, border=border)
    ws.row_dimensions[note_row].height = 22

    # Commentaires
    ws.row_dimensions[26].height = 8
    ws.merge_cells("C27:I27")
    _set_cell(ws, "C27", "COMMENTAIRES LIBRES",
              font=_header_font(10), fill=_header_fill(), alignment=center)

    ws.merge_cells("C28:I30")
    _set_cell(ws, "C28", "",
              font=_value_font(), border=border,
              alignment=Alignment(horizontal="left", vertical="top"))
    for r in [28, 29, 30]:
        ws.row_dimensions[r].height = 22

    # Signatures
    ws.row_dimensions[31].height = 8
    ws.merge_cells("C32:E32")
    _set_cell(ws, "C32", "Visa Responsable hiérarchique :",
              font=_label_font(), fill=_label_fill(), alignment=left, border=border)
    ws.merge_cells("F32:G32")
    _set_cell(ws, "F32", "Date :", font=_label_font(), fill=_label_fill(),
              alignment=left, border=border)
    ws.merge_cells("H32:I32")
    _set_cell(ws, "H32", "", font=_value_font(), border=border, alignment=center)
    ws.row_dimensions[32].height = 22

    ws.merge_cells("C33:I34")
    _set_cell(ws, "C33", "",
              font=_value_font(), border=border,
              alignment=Alignment(horizontal="left", vertical="top"))
    ws.row_dimensions[33].height = 30
    ws.row_dimensions[34].height = 30

    ws.row_dimensions[35].height = 8
    ws.merge_cells("C36:G36")
    _set_cell(ws, "C36", "Signature du stagiaire :",
              font=_label_font(), fill=_label_fill(), alignment=left, border=border)
    ws.merge_cells("C37:I38")
    _set_cell(ws, "C37", "", font=_value_font(), border=border,
              alignment=Alignment(horizontal="center", vertical="center"))
    ws.row_dimensions[37].height = 30
    ws.row_dimensions[38].height = 30


# ========================  POINT D'ENTRÉE PUBLIC  ========================

class FormationExportService:
    """Service de génération des documents officiels de formation pré-remplis."""

    @staticmethod
    def generate_dossier_formation(
        formation_data: Dict,
        output_dir: Optional[Path] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Génère un classeur xlsx avec les 3 documents officiels pré-remplis.

        Args:
            formation_data: Dict renvoyé par FormationServiceCRUD.get_formation_by_id().
                            Doit contenir : nom, prenom, intitule, organisme, lieu,
                            objectif, formateur, date_debut, date_fin, duree_heures,
                            cout, commentaire, service.
            output_dir: Répertoire de sortie (par défaut exports/formations/).

        Returns:
            (success, message, chemin_fichier)
        """
        if not OPENPYXL_AVAILABLE:
            return False, "openpyxl non installé (pip install openpyxl)", None

        try:
            out_dir = Path(output_dir) if output_dir else _EXPORTS_DIR
            out_dir.mkdir(parents=True, exist_ok=True)

            nom = formation_data.get('nom', 'INCONNU').upper()
            prenom = formation_data.get('prenom', '')
            intitule_court = formation_data.get('intitule', 'formation')[:30]
            date_str = datetime.now().strftime("%Y%m%d_%H%M")

            filename = f"Formation_{nom}_{prenom}_{intitule_court}_{date_str}.xlsx"
            filename = "".join(
                c if (c.isalnum() or c in "._- ") else "_" for c in filename
            ).strip()
            output_path = out_dir / filename

            wb = openpyxl.Workbook()
            # Supprimer la feuille par défaut
            del wb[wb.sheetnames[0]]

            _build_demande(wb, formation_data)
            _build_emargement(wb, formation_data)
            _build_suivi(wb, formation_data)

            wb.save(str(output_path))
            logger.info(f"Dossier formation généré : {output_path}")
            return True, "Dossier de formation généré avec succès.", str(output_path)

        except Exception as e:
            logger.exception(f"Erreur génération dossier formation: {e}")
            return False, f"Erreur lors de la génération : {e}", None

    @staticmethod
    def open_file(path: str):
        """Ouvre le fichier avec l'application par défaut du système."""
        import subprocess
        import sys
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.run(["open", path])
            else:
                subprocess.run(["xdg-open", path])
        except Exception as e:
            logger.error(f"Impossible d'ouvrir {path}: {e}")
