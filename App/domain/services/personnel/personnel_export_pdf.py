# -*- coding: utf-8 -*-
"""
personnel_export_pdf — export PDF professionnel du profil d'un opérateur.

Aucun import PyQt5. Entrées : données brutes. Sortie : fichier PDF.
"""

from infrastructure.logging.logging_config import get_logger
logger = get_logger(__name__)


def export_personnel_profile_pdf(
    operateur_id: int,
    nom: str,
    prenom: str,
    matricule: str,
    statut: str,
    infos_data: list,
    polyvalences: list,
    file_path: str,
) -> None:
    """
    Génère un PDF professionnel du profil d'un opérateur.

    Args:
        operateur_id:  Identifiant de l'opérateur (non utilisé dans le rendu, conservé pour extension).
        nom:           Nom de famille.
        prenom:        Prénom.
        matricule:     Matricule.
        statut:        Statut (ACTIF / INACTIF).
        infos_data:    Liste de tuples (section_title, [(label, value), ...]) issue du ViewModel.
        polyvalences:  Liste de dicts {poste, niveau, date_evaluation, prochaine_evaluation,
                       anciennete, statut_eval} — chaînes déjà formatées.
        file_path:     Chemin complet du fichier de sortie (.pdf).

    Raises:
        Exception: en cas d'erreur ReportLab, propagée à l'appelant.
    """
    import re
    import datetime as _dt

    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
    from reportlab.lib.units import cm
    from reportlab.pdfgen.canvas import Canvas

    from infrastructure.config.date_format import format_date

    # ---------- Helpers ----------
    def _clean_text(text: str) -> str:
        """Nettoie le texte des caractères de formatage."""
        if not text:
            return ""
        text = re.sub(r'[■█╔╗╚╝═─│┐└┘├┤┬┴┼]', '', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'\s*:\s*', ' : ', text)
        return text.strip()

    # ---------- Styles ----------
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=colors.HexColor("#1e40af"),
        spaceAfter=8,
        fontName="Helvetica-Bold"
    )
    section_style = ParagraphStyle(
        "CustomSection",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#1e40af"),
        spaceBefore=14,
        spaceAfter=8,
        fontName="Helvetica-Bold",
        borderWidth=0,
        borderColor=colors.HexColor("#3b82f6"),
        borderPadding=4
    )

    # ---------- En-tête / Pied ----------
    def _header_footer(canvas: Canvas, doc):
        canvas.saveState()

        canvas.setFillColor(colors.HexColor("#1e40af"))
        canvas.rect(0, A4[1] - 40, A4[0], 40, fill=1, stroke=0)

        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 12)
        canvas.drawString(doc.leftMargin, A4[1] - 25, f"{nom} {prenom}")

        canvas.setFont("Helvetica", 9)
        canvas.drawString(doc.leftMargin, A4[1] - 38,
                          f"Matricule : {matricule}  •  Statut : {statut}")

        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.setFont("Helvetica", 8)
        canvas.drawCentredString(A4[0] / 2, 15, f"Page {doc.page}")
        canvas.drawRightString(A4[0] - doc.rightMargin, 15,
                               f"Généré le {format_date(_dt.date.today())}")

        canvas.restoreState()

    # ---------- Document ----------
    doc = SimpleDocTemplate(
        file_path, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2.5 * cm, bottomMargin=2 * cm
    )
    flow = []

    flow.append(Paragraph("Fiche Personnel", title_style))
    flow.append(Spacer(1, 0.4 * cm))

    # ---------- Table unifiée : identité + sections ----------
    _sections = {t: items for t, items in (infos_data if infos_data else [])}

    unified_rows = []
    header_style_idx = []

    def _add_section_header(label):
        header_style_idx.append(len(unified_rows))
        unified_rows.append([label.upper(), ""])

    _add_section_header("Identité")
    unified_rows.append(["Nom", nom or "—"])
    unified_rows.append(["Prénom", prenom or "—"])
    unified_rows.append(["Matricule", matricule or "—"])
    unified_rows.append(["Statut", statut or "—"])
    for label, value in _sections.get("Informations Personnelles", []):
        if value and "Aucune" not in str(value):
            unified_rows.append([label, str(value)])

    _add_section_header("Contrat actuel")
    contrat_items = [
        (l, v) for l, v in _sections.get("Contrat Actuel", [])
        if v and "Aucun" not in str(v)
    ]
    if contrat_items:
        for l, v in contrat_items:
            unified_rows.append([l, str(v)])
    else:
        unified_rows.append(["Statut", "Aucun contrat actif"])

    _add_section_header("Formations")
    formation_items = [
        (l, v) for l, v in _sections.get("Formations", [])
        if "Aucune" not in l
    ]
    if formation_items:
        for l, v in formation_items:
            unified_rows.append([l, str(v)])
    else:
        unified_rows.append(["", "Aucune formation renseignée"])

    _add_section_header("Validités médicales")
    validite_items = [
        (l, v) for l, v in _sections.get("Validités", [])
        if "Aucune" not in l
    ]
    if validite_items:
        for l, v in validite_items:
            unified_rows.append([l, str(v)])
    else:
        unified_rows.append(["", "Aucune validité enregistrée"])

    t_unified = Table(unified_rows, colWidths=[5 * cm, 12 * cm])
    base_style = [
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#475569")),
        ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#1f2937")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
    ]
    for idx in header_style_idx:
        base_style += [
            ("BACKGROUND", (0, idx), (-1, idx), colors.HexColor("#e2e8f0")),
            ("TEXTCOLOR", (0, idx), (-1, idx), colors.HexColor("#334155")),
            ("FONTNAME", (0, idx), (-1, idx), "Helvetica-Bold"),
            ("SPAN", (0, idx), (-1, idx)),
        ]
    t_unified.setStyle(TableStyle(base_style))
    flow.append(t_unified)
    flow.append(Spacer(1, 0.5 * cm))

    # ---------- Polyvalences (si présentes) ----------
    if polyvalences:
        flow.append(Spacer(1, 0.5 * cm))
        flow.append(Paragraph("Polyvalences et Évaluations", section_style))

        poly_data = [["Poste", "Niveau", "Dernière\néval.", "Prochaine\néval.", "Ancienneté", "Statut"]]
        for p in polyvalences:
            poly_data.append([
                str(p.get("poste", "")),
                str(p.get("niveau", "")),
                str(p.get("date_evaluation", "")),
                str(p.get("prochaine_evaluation", "")),
                str(p.get("anciennete", "")),
                str(p.get("statut_eval", "")),
            ])

        col_widths = [4 * cm, 2 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm, 2 * cm]
        t_poly = Table(poly_data, colWidths=col_widths, repeatRows=1)
        t_poly.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("ALIGN", (1, 1), (-1, -1), "CENTER"),
            ("ALIGN", (0, 1), (0, -1), "LEFT"),
            ("VALIGN", (0, 1), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        flow.append(t_poly)

    doc.build(flow, onFirstPage=_header_footer, onLaterPages=_header_footer)
