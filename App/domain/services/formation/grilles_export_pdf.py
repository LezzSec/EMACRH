# -*- coding: utf-8 -*-
"""
Service d'export PDF pour la grille de polyvalence.
Aucune dépendance PyQt5 — pur Python / reportlab.
"""

from datetime import datetime
from typing import List

from infrastructure.logging.logging_config import get_logger
from infrastructure.config.date_format import format_date

logger = get_logger(__name__)


class RotatedText:
    """Flowable reportlab pour texte vertical (en-têtes de postes)."""

    def __init__(self, text: str, fontSize: float = 5):
        from reportlab.platypus import Flowable
        # Dynamically inherit to avoid top-level reportlab import at module load
        self.__class__ = type('RotatedText', (Flowable,), {
            '__init__': RotatedText.__init__,
            'draw': RotatedText.draw,
        })
        self.text = text
        self.fontSize = fontSize
        self.width = fontSize * 1.2
        self.height = min(22, len(text) * fontSize * 0.6)

    def draw(self):
        canvas = self.canv
        canvas.saveState()
        canvas.translate(self.width / 2, 0)
        canvas.rotate(90)
        canvas.setFont("Helvetica-Bold", self.fontSize)
        canvas.drawString(1, -self.fontSize / 3, self.text)
        canvas.restoreState()


def export_grille_pdf(
    file_path: str,
    headers: List[str],
    row_labels: List[str],
    data: List[List[str]],
    synthesis_start_row: int,
) -> None:
    """Exporte la grille dans un fichier PDF.

    Args:
        file_path: Chemin complet du fichier .pdf de destination.
        headers: Liste des en-têtes de colonnes (codes postes).
        row_labels: Liste des libellés de lignes (opérateurs + synthèse).
        data: Matrice de données [ligne][colonne] en chaînes.
        synthesis_start_row: Index (0-based) de la première ligne de synthèse.

    Raises:
        Exception: toute erreur reportlab est laissée remonter à l'appelant.
    """
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Flowable
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm

    class _RotatedText(Flowable):
        def __init__(self, text, fontSize=5):
            Flowable.__init__(self)
            self.text = text
            self.fontSize = fontSize
            self.width = fontSize * 1.2
            self.height = min(22, len(text) * fontSize * 0.6)

        def draw(self):
            c = self.canv
            c.saveState()
            c.translate(self.width / 2, 0)
            c.rotate(90)
            c.setFont("Helvetica-Bold", self.fontSize)
            c.drawString(1, -self.fontSize / 3, self.text)
            c.restoreState()

    page = A4
    LM, RM, TM, BM = 3 * mm, 3 * mm, 8 * mm, 3 * mm
    usable_w = page[0] - LM - RM
    title_size = 11
    th_size = 6.5
    td_size = 6

    n_poste_cols = len(headers)
    first_col_w = 30 * mm
    summary_col_w = 12 * mm
    remaining_w = usable_w - first_col_w - summary_col_w
    poste_col_w = max(4.2 * mm, remaining_w / n_poste_cols) if n_poste_cols else 4.2 * mm
    col_widths = [first_col_w] + [poste_col_w] * n_poste_cols + [summary_col_w]

    td_c_style = ParagraphStyle("TDc", fontName="Helvetica", fontSize=td_size, leading=td_size + 1, alignment=1)
    td_l_style = ParagraphStyle("TDl", fontName="Helvetica", fontSize=td_size, leading=td_size + 1, alignment=0)
    td_b_style = ParagraphStyle("TDb", fontName="Helvetica-Bold", fontSize=td_size, leading=td_size + 1, alignment=1)

    operator_rows = data[:synthesis_start_row]
    operator_labels = row_labels[:synthesis_start_row]
    synthesis_rows = data[synthesis_start_row:]
    synthesis_labels = row_labels[synthesis_start_row:]

    # En-tête tableau
    header_row = [""] + [_RotatedText(h, th_size) for h in headers] + [_RotatedText("Résumé", th_size)]
    table_data = [header_row]

    # Lignes opérateurs
    for i, row in enumerate(operator_rows):
        levels = [v.strip() for v in row if v.strip().isdigit()]
        n1, n2, n3, n4 = levels.count('1'), levels.count('2'), levels.count('3'), levels.count('4')
        parts = []
        if n1: parts.append(f"{n1}xN1")
        if n2: parts.append(f"{n2}xN2")
        if n3: parts.append(f"{n3}xN3")
        if n4: parts.append(f"{n4}xN4")
        summary = "<br/>".join(parts) if parts else ""

        table_data.append(
            [Paragraph(operator_labels[i], td_l_style)] +
            [Paragraph(str(v) if v else "", td_c_style) for v in row] +
            [Paragraph(f"<b>{summary}</b>", td_b_style)]
        )

    # Lignes de synthèse
    for i, row in enumerate(synthesis_rows):
        table_data.append(
            [Paragraph(f"<b>{synthesis_labels[i]}</b>", td_l_style)] +
            [Paragraph(str(v) if v else "", td_c_style) for v in row] +
            [Paragraph("", td_c_style)]
        )

    table = Table(table_data, colWidths=col_widths)
    n_op_rows = len(operator_rows) + 1

    table_style = [
        ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#BFBFBF")),
        ("ALIGN", (0, 0), (0, 0), "LEFT"),
        ("ALIGN", (1, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("BACKGROUND", (0, n_op_rows), (-1, -1), colors.HexColor("#E0E0E0")),
        ("BACKGROUND", (-1, 1), (-1, n_op_rows - 1), colors.HexColor("#FFF9C4")),
        ("LEFTPADDING", (0, 0), (-1, -1), 1),
        ("RIGHTPADDING", (0, 0), (-1, -1), 1),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]
    table.setStyle(TableStyle(table_style))

    legend_style = ParagraphStyle("Leg", fontName="Helvetica", fontSize=6, leading=7, alignment=0)
    legend_text = (
        "<b>Niveaux :</b> "
        "<b>N1</b>: &lt;80% (nouveau/absent 12m) | "
        "<b>N2</b>: ≥80% (formé, autonome) | "
        "<b>N3</b>: &gt;90% (formateur) | "
        "<b>N4</b>: &gt;90% (leader/polyvalent) | "
        "<b>Résumé :</b> affiche le nombre de postes N3 et N4 (ex: 5xN3 = 5 postes niveau 3)"
    )
    legend = Paragraph(legend_text, legend_style)

    date_str = format_date(datetime.now())

    def on_page(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica-Bold", title_size)
        canvas.drawCentredString(
            page[0] / 2, page[1] - TM + 3 * mm,
            f"Grille de Polyvalence au {date_str}",
        )
        canvas.setFont("Helvetica", 6)
        canvas.drawString(LM, TM - 3 * mm, "LQ 07 02 02 rév.1")
        canvas.restoreState()

    doc = SimpleDocTemplate(
        file_path, pagesize=page,
        leftMargin=LM, rightMargin=RM,
        topMargin=TM + 5 * mm, bottomMargin=BM + 3 * mm,
        title="Grille de Polyvalence",
    )
    doc.build([table, Spacer(1, 2 * mm), legend], onFirstPage=on_page, onLaterPages=on_page)
    logger.info(f"Export PDF grille polyvalence : {file_path}")
