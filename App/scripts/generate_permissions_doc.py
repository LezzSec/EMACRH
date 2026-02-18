# -*- coding: utf-8 -*-
"""Génère la documentation PDF du système de permissions EMAC."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, PageBreak
)
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'docs',
                           'permissions_guide.pdf')

# ─────────────────────────────────────────────────────────────────────────────
# Palette de couleurs EMAC
# ─────────────────────────────────────────────────────────────────────────────
BLUE_DARK  = colors.HexColor('#1e3a5f')
BLUE_MID   = colors.HexColor('#2563eb')
BLUE_LIGHT = colors.HexColor('#dbeafe')
BLUE_PALE  = colors.HexColor('#eff6ff')
PURPLE     = colors.HexColor('#7c3aed')
PURPLE_LIGHT = colors.HexColor('#ede9fe')
GREEN      = colors.HexColor('#16a34a')
GREEN_LIGHT= colors.HexColor('#dcfce7')
RED        = colors.HexColor('#dc2626')
RED_LIGHT  = colors.HexColor('#fee2e2')
ORANGE     = colors.HexColor('#d97706')
ORANGE_LIGHT = colors.HexColor('#fef3c7')
GREY_DARK  = colors.HexColor('#374151')
GREY_MID   = colors.HexColor('#6b7280')
GREY_LIGHT = colors.HexColor('#f3f4f6')
GREY_LINE  = colors.HexColor('#e5e7eb')
WHITE      = colors.white
BLACK      = colors.black


def make_styles():
    base = getSampleStyleSheet()

    def s(name, **kw):
        return ParagraphStyle(name, **kw)

    styles = {
        'title': s('title',
            fontName='Helvetica-Bold', fontSize=26, leading=32,
            textColor=WHITE, alignment=TA_CENTER, spaceAfter=4),
        'subtitle': s('subtitle',
            fontName='Helvetica', fontSize=13, leading=18,
            textColor=colors.HexColor('#bfdbfe'), alignment=TA_CENTER),

        'h1': s('h1',
            fontName='Helvetica-Bold', fontSize=16, leading=22,
            textColor=BLUE_DARK, spaceBefore=18, spaceAfter=6,
            borderPad=4),
        'h2': s('h2',
            fontName='Helvetica-Bold', fontSize=13, leading=18,
            textColor=BLUE_MID, spaceBefore=14, spaceAfter=4),
        'h3': s('h3',
            fontName='Helvetica-Bold', fontSize=11, leading=15,
            textColor=GREY_DARK, spaceBefore=10, spaceAfter=3),

        'body': s('body',
            fontName='Helvetica', fontSize=10, leading=15,
            textColor=GREY_DARK, spaceAfter=6, alignment=TA_JUSTIFY),
        'body_small': s('body_small',
            fontName='Helvetica', fontSize=9, leading=13,
            textColor=GREY_DARK, spaceAfter=4),
        'code': s('code',
            fontName='Courier', fontSize=8.5, leading=13,
            textColor=colors.HexColor('#1e1b4b'),
            backColor=colors.HexColor('#f5f3ff'),
            spaceAfter=4, leftIndent=8, rightIndent=8,
            borderPad=3),
        'bullet': s('bullet',
            fontName='Helvetica', fontSize=10, leading=14,
            textColor=GREY_DARK, leftIndent=14, spaceAfter=3,
            bulletIndent=4),

        'table_header': s('table_header',
            fontName='Helvetica-Bold', fontSize=9, leading=12,
            textColor=WHITE, alignment=TA_CENTER),
        'table_cell': s('table_cell',
            fontName='Helvetica', fontSize=9, leading=12,
            textColor=GREY_DARK),
        'table_cell_code': s('table_cell_code',
            fontName='Courier', fontSize=8, leading=11,
            textColor=colors.HexColor('#1e1b4b')),

        'caption': s('caption',
            fontName='Helvetica-Oblique', fontSize=9,
            textColor=GREY_MID, alignment=TA_CENTER, spaceAfter=12),

        'note': s('note',
            fontName='Helvetica-Oblique', fontSize=9, leading=13,
            textColor=colors.HexColor('#92400e')),
        'tip': s('tip',
            fontName='Helvetica', fontSize=9, leading=13,
            textColor=colors.HexColor('#065f46')),
        'warn': s('warn',
            fontName='Helvetica-Bold', fontSize=9, leading=13,
            textColor=colors.HexColor('#991b1b')),
    }
    return styles


def hr(color=GREY_LINE, thickness=0.5):
    return HRFlowable(width='100%', thickness=thickness,
                      color=color, spaceAfter=6, spaceBefore=6)


def section_box(content_rows, bg=BLUE_PALE, border=BLUE_MID, radius=4):
    """Encadré coloré autour d'un bloc de contenu."""
    t = Table([[c] for c in content_rows], colWidths=['100%'])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg),
        ('BOX', (0, 0), (-1, -1), 1, border),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('ROUNDEDCORNERS', [radius]),
    ]))
    return t


def make_feature_table(styles, rows, title_col='Clé de permission',
                        col_widths=None):
    """Table stylisée pour liste de features."""
    if col_widths is None:
        col_widths = [6.5*cm, 4.5*cm, 7*cm]

    header = [
        Paragraph(title_col, styles['table_header']),
        Paragraph('Label affiché', styles['table_header']),
        Paragraph('Ce que ça contrôle dans l\'UI', styles['table_header']),
    ]
    data = [header] + [
        [Paragraph(r[0], styles['table_cell_code']),
         Paragraph(r[1], styles['table_cell']),
         Paragraph(r[2], styles['table_cell'])]
        for r in rows
    ]

    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = TableStyle([
        # En-tête
        ('BACKGROUND', (0, 0), (-1, 0), BLUE_DARK),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        # Lignes alternées
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, GREY_LIGHT]),
        # Bordures
        ('GRID', (0, 0), (-1, -1), 0.4, GREY_LINE),
        ('BOX', (0, 0), (-1, -1), 0.8, BLUE_MID),
        # Padding
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ])
    t.setStyle(style)
    return t


def make_role_table(styles, roles_data):
    """Table de comparaison des rôles."""
    header = [Paragraph(h, styles['table_header']) for h in
              ['Permission', 'ADMIN', 'GESTION_PRODUCTION', 'GESTION_RH']]
    data = [header]
    for row in roles_data:
        def cell(v):
            if v == '✓':
                return Paragraph('<font color="#16a34a"><b>✓</b></font>', styles['table_cell'])
            elif v == '—':
                return Paragraph('<font color="#9ca3af">—</font>', styles['table_cell'])
            elif v == 'Lecture':
                return Paragraph('<font color="#2563eb">Lecture</font>', styles['table_cell'])
            else:
                return Paragraph(v, styles['table_cell_code'])
        data.append([cell(row[0]), cell(row[1]), cell(row[2]), cell(row[3])])

    col_w = [7.5*cm, 2.5*cm, 4*cm, 3.5*cm]
    t = Table(data, colWidths=col_w, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BLUE_DARK),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, GREY_LIGHT]),
        ('GRID', (0, 0), (-1, -1), 0.4, GREY_LINE),
        ('BOX', (0, 0), (-1, -1), 0.8, BLUE_MID),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    return t


def badge_table(items):
    """Ligne de badges colorés (légende)."""
    cells = []
    for label, bg, fg in items:
        p = Paragraph(f'<b>{label}</b>',
                      ParagraphStyle('badge', fontName='Helvetica-Bold',
                                     fontSize=9, textColor=fg, alignment=TA_CENTER))
        cells.append(p)
    t = Table([cells], colWidths=[4.5*cm]*len(items))
    bg_colors = [bg for _, bg, _ in items]
    for i, bg in enumerate(bg_colors):
        t.setStyle(TableStyle([
            ('BACKGROUND', (i, 0), (i, 0), bg),
            ('BOX', (i, 0), (i, 0), 0.5, GREY_LINE),
            ('TOPPADDING', (i, 0), (i, 0), 6),
            ('BOTTOMPADDING', (i, 0), (i, 0), 6),
            ('LEFTPADDING', (i, 0), (i, 0), 8),
            ('RIGHTPADDING', (i, 0), (i, 0), 8),
        ]))
    return t


# ─────────────────────────────────────────────────────────────────────────────
# Numérotation de pages
# ─────────────────────────────────────────────────────────────────────────────

def _header_footer(canvas, doc):
    canvas.saveState()
    w, h = A4

    # En-tête
    canvas.setFillColor(BLUE_DARK)
    canvas.rect(0, h - 1.2*cm, w, 1.2*cm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont('Helvetica-Bold', 9)
    canvas.drawString(1.5*cm, h - 0.82*cm, 'EMAC – Documentation Système de Permissions')
    canvas.setFont('Helvetica', 8)
    canvas.drawRightString(w - 1.5*cm, h - 0.82*cm, 'Confidentiel – Usage interne')

    # Pied de page
    canvas.setFillColor(GREY_LINE)
    canvas.rect(0, 0, w, 0.9*cm, fill=1, stroke=0)
    canvas.setFillColor(GREY_MID)
    canvas.setFont('Helvetica', 8)
    canvas.drawString(1.5*cm, 0.32*cm, 'EMAC v2.0 – 2026')
    canvas.drawRightString(w - 1.5*cm, 0.32*cm, f'Page {doc.page}')

    canvas.restoreState()


# ─────────────────────────────────────────────────────────────────────────────
# DOCUMENT
# ─────────────────────────────────────────────────────────────────────────────

def build_pdf():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    doc = SimpleDocTemplate(
        OUTPUT_PATH, pagesize=A4,
        leftMargin=1.8*cm, rightMargin=1.8*cm,
        topMargin=2.2*cm, bottomMargin=1.8*cm,
        title='Documentation Permissions EMAC',
        author='EMAC',
    )
    S = make_styles()
    story = []

    # ── PAGE DE COUVERTURE ────────────────────────────────────────────────────
    story.append(Spacer(1, 1.5*cm))

    cover_inner = [
        Spacer(1, 0.6*cm),
        Paragraph('EMAC', S['title']),
        Paragraph('Système de Gestion des Permissions', S['subtitle']),
        Spacer(1, 0.3*cm),
        Paragraph('Guide complet — Usage interne', S['subtitle']),
        Spacer(1, 0.6*cm),
    ]
    cover = Table([[p] for p in cover_inner],
                  colWidths=[doc.width])
    cover.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BLUE_DARK),
        ('ROUNDEDCORNERS', [8]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(cover)
    story.append(Spacer(1, 1*cm))

    # Résumé couverture
    summary_rows = [
        ['📋 35 permissions', 'organisées en 4 modules'],
        ['👥 3 rôles prédéfinis', 'Admin · Gestion Production · Gestion RH'],
        ['🔧 Surcharges par utilisateur', 'OUI / NON / AUTO (hérite du rôle)'],
        ['🔒 Cache sécurisé', 'TTL 5 min · Vérification DB sur opérations critiques'],
    ]
    for key, val in summary_rows:
        t = Table([[
            Paragraph(key, ParagraphStyle('ck', fontName='Helvetica-Bold',
                                          fontSize=10, textColor=BLUE_DARK)),
            Paragraph(val, ParagraphStyle('cv', fontName='Helvetica',
                                          fontSize=10, textColor=GREY_DARK)),
        ]], colWidths=[7*cm, 10*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), BLUE_PALE),
            ('BACKGROUND', (1, 0), (1, 0), WHITE),
            ('BOX', (0, 0), (-1, -1), 0.5, GREY_LINE),
            ('GRID', (0, 0), (-1, -1), 0.3, GREY_LINE),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.15*cm))

    story.append(PageBreak())

    # ── 1. VUE D'ENSEMBLE ────────────────────────────────────────────────────
    story.append(Paragraph('1. Vue d\'ensemble du système', S['h1']))
    story.append(hr(BLUE_MID, 1))
    story.append(Paragraph(
        'EMAC utilise un système de permissions granulaires basé sur des <b>features</b> '
        '(fonctionnalités). Chaque feature représente une action précise dans l\'application '
        '(ex. : modifier un personnel, exporter une grille). Les permissions sont assignées '
        'aux <b>rôles</b>, puis peuvent être affinées individuellement par utilisateur via des '
        '<b>surcharges</b>.',
        S['body']))

    story.append(Paragraph('Hiérarchie de résolution des permissions', S['h2']))

    resolution = [
        ['Niveau', 'Source', 'Priorité', 'Description'],
        ['1 – Surcharge utilisateur', 'Table user_features', 'HAUTE',
         'Override individuel OUI/NON. Prend le dessus sur tout.'],
        ['2 – Permission du rôle', 'Table role_features', 'NORMALE',
         'Permission héritée du rôle assigné à l\'utilisateur.'],
        ['3 – Défaut', '—', 'BASSE',
         'Refusé si aucune règle trouvée.'],
    ]
    t = Table(resolution, colWidths=[4.5*cm, 4*cm, 2.5*cm, 6.5*cm], repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BLUE_DARK),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [GREEN_LIGHT, ORANGE_LIGHT, RED_LIGHT]),
        ('GRID', (0, 0), (-1, -1), 0.4, GREY_LINE),
        ('BOX', (0, 0), (-1, -1), 0.8, BLUE_MID),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph('Cycle de vie d\'une vérification de permission', S['h2']))
    story.append(Paragraph(
        'À la <b>connexion</b>, les permissions du rôle et les surcharges individuelles sont chargées '
        'en mémoire (cache TTL 5 min). Pendant l\'utilisation, les vérifications d\'<b>interface</b> '
        '(visibilité des boutons) utilisent ce cache. Les <b>opérations critiques</b> (suppression, '
        'modification de données sensibles) re-vérifient systématiquement la base de données pour '
        'prévenir les attaques TOCTOU (race conditions). Après modification des permissions par un '
        'administrateur, le cache est invalidé immédiatement.',
        S['body']))

    # Schéma simplifié
    flow_data = [
        ['Connexion', '→', 'Cache chargé\n(rôle + surcharges)', '→', 'UI affichée\nselon can()'],
        ['', '', '', '', '↓'],
        ['Permission modifiée\npar admin', '→', 'Cache invalidé\net rechargé', '→', 'Effet immédiat'],
    ]
    ft = Table(flow_data, colWidths=[4*cm, 1*cm, 4.5*cm, 1*cm, 4*cm])
    ft.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), BLUE_LIGHT),
        ('BACKGROUND', (2, 0), (2, 0), GREEN_LIGHT),
        ('BACKGROUND', (4, 0), (4, 0), BLUE_LIGHT),
        ('BACKGROUND', (0, 2), (0, 2), ORANGE_LIGHT),
        ('BACKGROUND', (2, 2), (2, 2), GREEN_LIGHT),
        ('BACKGROUND', (4, 2), (4, 2), BLUE_LIGHT),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BOX', (0, 0), (0, 0), 0.5, BLUE_MID),
        ('BOX', (2, 0), (2, 0), 0.5, GREEN),
        ('BOX', (4, 0), (4, 0), 0.5, BLUE_MID),
        ('BOX', (0, 2), (0, 2), 0.5, ORANGE),
        ('BOX', (2, 2), (2, 2), 0.5, GREEN),
        ('BOX', (4, 2), (4, 2), 0.5, BLUE_MID),
    ]))
    story.append(ft)

    # ── 2. INTERFACE "GÉRER LES PERMISSIONS" ────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph('2. Interface « Gérer les Permissions »', S['h1']))
    story.append(hr(BLUE_MID, 1))
    story.append(Paragraph(
        'Accessible depuis <b>Gestion Utilisateurs → 🔐 Gérer les Features</b> '
        '(réservé aux administrateurs). Cette interface permet de configurer '
        'les permissions par rôle ou par utilisateur individuel.',
        S['body']))

    story.append(Paragraph('2.1 Accès à l\'interface', S['h2']))
    steps = [
        ('1', 'Ouvrir le menu principal (hamburger en haut à gauche)'),
        ('2', 'Cliquer sur <b>Administration</b> dans le drawer'),
        ('3', 'Sélectionner <b>Gestion Utilisateurs</b>'),
        ('4', 'Cliquer sur le bouton <b>🔐 Gérer les Features</b>'),
    ]
    for num, text in steps:
        t = Table([[
            Paragraph(f'<b>{num}</b>',
                      ParagraphStyle('n', fontName='Helvetica-Bold', fontSize=11,
                                     textColor=WHITE, alignment=TA_CENTER)),
            Paragraph(text, S['body']),
        ]], colWidths=[1*cm, doc.width - 1*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), BLUE_MID),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.1*cm))

    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph('2.2 Mode d\'édition', S['h2']))
    story.append(Paragraph(
        'L\'interface propose deux modes :', S['body']))

    modes = [
        ['Mode', 'Cible', 'Effet', 'Cas d\'usage'],
        ['Modifier un Rôle',
         'Toutes les personnes\ndu rôle sélectionné',
         'Modifie la table\nrole_features',
         'Configurer les droits standards\nd\'un groupe entier'],
        ['Modifier un Utilisateur',
         'Une personne précise\nuniquement',
         'Modifie la table\nuser_features (override)',
         'Accorder une exception\nou restreindre un individu'],
    ]
    mt = Table(modes, colWidths=[4*cm, 4*cm, 4*cm, 5.5*cm], repeatRows=1)
    mt.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PURPLE),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [PURPLE_LIGHT, WHITE]),
        ('GRID', (0, 0), (-1, -1), 0.4, GREY_LINE),
        ('BOX', (0, 0), (-1, -1), 0.8, PURPLE),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(mt)

    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph('2.3 Les trois états d\'un interrupteur de permission', S['h2']))

    story.append(badge_table([
        ('OUI', GREEN_LIGHT, GREEN),
        ('NON', RED_LIGHT, RED),
        ('AUTO', BLUE_LIGHT, BLUE_MID),
    ]))
    story.append(Spacer(1, 0.2*cm))

    badge_desc = [
        ['OUI (vert)', 'Permission explicitement accordée. Prend le dessus sur le rôle si en mode Utilisateur.'],
        ['NON (rouge)', 'Permission explicitement refusée. Prend le dessus sur le rôle si en mode Utilisateur.'],
        ['AUTO (bleu)', 'Mode Utilisateur uniquement. L\'utilisateur hérite de la valeur de son rôle. '
                        'C\'est l\'état par défaut (pas de surcharge).'],
    ]
    for state, desc in badge_desc:
        t = Table([[
            Paragraph(f'<b>{state}</b>', S['body']),
            Paragraph(desc, S['body']),
        ]], colWidths=[3.5*cm, doc.width - 3.5*cm])
        t.setStyle(TableStyle([
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('LINEBELOW', (0, 0), (-1, -1), 0.3, GREY_LINE),
        ]))
        story.append(t)

    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph('2.4 Boutons d\'action rapide', S['h2']))
    quick = [
        ('Tout sélectionner', 'Active toutes les permissions en OUI pour le rôle ou utilisateur courant.'),
        ('Tout désélectionner', 'Passe toutes les permissions en NON.'),
        ('Réinitialiser au rôle', 'Mode Utilisateur uniquement. Supprime toutes les surcharges '
                                   '(repasse tout en AUTO). L\'utilisateur hérite à nouveau de son rôle.'),
        ('Enregistrer', 'Sauvegarde les modifications en base de données et invalide le cache.'),
        ('Annuler', 'Ferme sans sauvegarder.'),
    ]
    for btn, desc in quick:
        story.append(Paragraph(f'• <b>{btn}</b> — {desc}', S['bullet']))

    story.append(Spacer(1, 0.3*cm))
    b = section_box([
        Paragraph('⚠️ Protection de l\'administrateur',
                  ParagraphStyle('wt', fontName='Helvetica-Bold', fontSize=10,
                                 textColor=colors.HexColor('#92400e'))),
        Paragraph(
            'Les permissions du module <b>Administration</b> ne peuvent pas être retirées '
            'du rôle Admin dans l\'interface. Cette protection empêche la suppression '
            'accidentelle des droits d\'administration.',
            ParagraphStyle('wb', fontName='Helvetica', fontSize=9, leading=13,
                           textColor=colors.HexColor('#92400e'))),
    ], bg=ORANGE_LIGHT, border=ORANGE)
    story.append(b)

    # ── 3. MODULES ET PERMISSIONS ────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph('3. Catalogue des permissions par module', S['h1']))
    story.append(hr(BLUE_MID, 1))
    story.append(Paragraph(
        'Les permissions sont organisées en 4 modules. Chaque clé de permission '
        'suit la convention <b>module.sous-module.action</b>.',
        S['body']))

    # MODULE RH
    story.append(Paragraph('3.1 Module RH', S['h2']))
    rh_features = [
        ('rh.view', 'Accès module RH',
         'Affiche le menu/onglet RH dans le drawer. Sans cette permission, tout le module RH est masqué.'),
        ('rh.personnel.view', 'Voir Personnel',
         'Accès à la liste des employés dans Gestion RH. Affiche les données générales, contrats, absences (lecture seule).'),
        ('rh.personnel.create', 'Ajouter Personnel',
         'Bouton « Nouvel opérateur » visible et actif. Permet de créer une nouvelle fiche employé.'),
        ('rh.personnel.edit', 'Modifier Personnel',
         'Bouton Modifier visible dans la fiche employé. Permet aussi l\'accès aux « Actions en masse » (formations, absences en lot).'),
        ('rh.personnel.delete', 'Supprimer Personnel',
         'Bouton de désactivation/suppression d\'un employé visible et actif.'),
        ('rh.contrats.view', 'Voir Contrats',
         'Onglet Contrat visible dans la fiche employé. Affiche le type, dates et durée des contrats.'),
        ('rh.contrats.edit', 'Modifier Contrats',
         'Boutons Ajouter/Modifier contrat actifs. Permet la création et modification de contrats. Affiche aussi la carte Alertes Contrats sur le dashboard.'),
        ('rh.contrats.delete', 'Supprimer Contrats',
         'Bouton Supprimer contrat actif dans l\'onglet Contrat.'),
        ('rh.documents.view', 'Voir Documents RH',
         'Onglet Documents visible dans la fiche employé. Consultation des documents archivés.'),
        ('rh.documents.edit', 'Gérer Documents RH',
         'Boutons Ajouter, Archiver, Restaurer document actifs. Affiche aussi la carte Alertes Contrats sur le dashboard.'),
        ('rh.documents.print', 'Imprimer Documents',
         'Génération et impression de documents RH (courriers, attestations).'),
        ('rh.templates.view', 'Voir Templates',
         'Accès à la liste des modèles de documents dans le menu Templates.'),
        ('rh.templates.edit', 'Gérer Templates',
         'Création et modification des modèles de documents (Word, PDF).'),
        ('rh.formations.edit', 'Gérer Formations',
         'Boutons Ajouter/Modifier formation dans l\'onglet Formation de la fiche employé.'),
        ('rh.formations.delete', 'Supprimer Formations',
         'Bouton Supprimer formation actif dans l\'onglet Formation.'),
        ('rh.competences.edit', 'Gérer Compétences',
         'Boutons Ajouter/Modifier compétence dans l\'onglet Compétences de la fiche employé.'),
        ('rh.competences.delete', 'Supprimer Compétences',
         'Bouton Supprimer compétence actif dans l\'onglet Compétences.'),
        ('rh.medical.edit', 'Gérer Médical',
         'Boutons Ajouter visite médicale, accident, modifier dans l\'onglet Médical.'),
        ('rh.vie_salarie.edit', 'Gérer Vie Salarié',
         'Boutons Ajouter sanction, entretien, test alcool/salivaire dans l\'onglet Vie du salarié.'),
        ('rh.declarations.edit', 'Gérer Déclarations',
         'Boutons Ajouter/Modifier déclaration dans l\'onglet dédié de la fiche employé.'),
    ]
    story.append(make_feature_table(S, rh_features,
                                    col_widths=[5.5*cm, 4*cm, 8*cm]))

    # MODULE PRODUCTION
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph('3.2 Module Production', S['h2']))
    prod_features = [
        ('production.view', 'Accès Production',
         'Affiche le menu Production dans le drawer. Condition de base pour tout le module.'),
        ('production.evaluations.view', 'Voir Évaluations',
         'Bouton Évaluations visible dans le menu. Affiche la carte Retard Évaluations sur le dashboard avec les évaluations en retard/à venir.'),
        ('production.evaluations.edit', 'Modifier Évaluations',
         'Permet de planifier, modifier et valider des évaluations de compétences.'),
        ('production.polyvalence.view', 'Voir Polyvalence',
         'Accès à la matrice de polyvalence (lecture seule).'),
        ('production.polyvalence.edit', 'Modifier Polyvalence',
         'Permet de modifier les niveaux de compétence (1 à 4) des employés sur les postes.'),
        ('production.postes.view', 'Voir Postes',
         'Affichage de la liste des postes et ateliers (lecture seule).'),
        ('production.postes.edit', 'Gérer Postes',
         'Création, modification et suppression de postes de travail. Bouton Création/Suppression de poste dans le drawer.'),
        ('production.grilles.view', 'Voir Grilles',
         'Accès aux grilles de compétences (matrices Employé × Poste). Bouton Grilles visible dans le menu.'),
        ('production.grilles.export', 'Exporter Grilles',
         'Boutons Export Excel et Export PDF actifs dans les grilles de compétences.'),
    ]
    story.append(make_feature_table(S, prod_features,
                                    col_widths=[5.5*cm, 4*cm, 8*cm]))

    # MODULE PLANNING
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph('3.3 Module Planning', S['h2']))
    plan_features = [
        ('planning.view', 'Accès Planning',
         'Bouton Planning visible dans le drawer. Accès à la vue de régularisation et absences.'),
        ('planning.absences.view', 'Voir Absences',
         'Consultation du planning d\'absences (lecture seule). Onglet Absence visible dans la fiche employé.'),
        ('planning.absences.edit', 'Gérer Absences',
         'Boutons Ajouter, Modifier, Supprimer absence actifs. Permet la saisie et gestion complète des absences.'),
    ]
    story.append(make_feature_table(S, plan_features,
                                    col_widths=[5.5*cm, 4*cm, 8*cm]))

    # MODULE ADMIN
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph('3.4 Module Administration', S['h2']))
    admin_features = [
        ('admin.view', 'Accès Administration',
         'Affiche la section Administration dans le drawer. Condition de base pour tout le module admin.'),
        ('admin.users.view', 'Voir Utilisateurs',
         'Liste des utilisateurs de l\'application visible (login, rôle, statut).'),
        ('admin.users.create', 'Créer Utilisateurs',
         'Bouton Nouvel utilisateur actif. Permet de créer de nouveaux comptes d\'accès.'),
        ('admin.users.edit', 'Modifier Utilisateurs',
         'Bouton Modifier utilisateur actif. Permet de changer le rôle, mot de passe, statut.'),
        ('admin.users.delete', 'Supprimer Utilisateurs',
         'Bouton Supprimer utilisateur actif.'),
        ('admin.permissions', 'Gérer Permissions',
         'Accès au bouton 🔐 Gérer les Features. Permet de modifier les permissions des rôles et utilisateurs.'),
        ('admin.roles.edit', 'Gérer Rôles',
         'Modification des permissions associées à chaque rôle.'),
        ('admin.historique.view', 'Voir Historique',
         'Bouton Historique visible dans le drawer. Consultation du journal d\'audit complet.'),
        ('admin.historique.export', 'Exporter Historique',
         'Bouton Export CSV dans l\'historique. Permet d\'exporter les logs d\'audit.'),
    ]
    story.append(make_feature_table(S, admin_features,
                                    col_widths=[5.5*cm, 4*cm, 8*cm]))

    # ── 4. RÔLES PRÉDÉFINIS ──────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph('4. Rôles prédéfinis et leurs permissions', S['h1']))
    story.append(hr(BLUE_MID, 1))
    story.append(Paragraph(
        'L\'application dispose de 3 rôles par défaut. Les permissions peuvent être '
        'étendues ou restreintes par rôle, puis affinées individuellement par utilisateur.',
        S['body']))

    # Description des rôles
    roles_desc = [
        ('ADMIN', BLUE_DARK, 'Accès total à l\'application. Peut gérer les utilisateurs, '
         'les permissions, l\'historique, et toutes les fonctions RH et Production.'),
        ('GESTION_PRODUCTION', colors.HexColor('#047857'), 'Accès complet au module Production '
         '(évaluations, polyvalence, postes, grilles). Lecture seule sur les données RH de base '
         '(personnel et contrats). Pas d\'accès aux fonctions RH avancées ni à l\'administration.'),
        ('GESTION_RH', colors.HexColor('#b45309'), 'Accès complet au module RH (personnel, contrats, '
         'documents, templates, formations, compétences, absences). Lecture seule sur la '
         'production. Peut consulter l\'historique.'),
    ]
    for role, color, desc in roles_desc:
        t = Table([[
            Paragraph(f'<b>{role}</b>',
                      ParagraphStyle('rn', fontName='Helvetica-Bold', fontSize=11,
                                     textColor=WHITE, alignment=TA_CENTER)),
            Paragraph(desc, S['body_small']),
        ]], colWidths=[4.5*cm, doc.width - 4.5*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), color),
            ('BACKGROUND', (1, 0), (1, 0), WHITE),
            ('BOX', (0, 0), (-1, -1), 0.8, color),
            ('GRID', (0, 0), (-1, -1), 0.3, GREY_LINE),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.15*cm))

    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph('Tableau comparatif des permissions par rôle', S['h2']))

    role_comparison = [
        # (permission, ADMIN, GESTION_PRODUCTION, GESTION_RH)
        ('── MODULE RH ──', '', '', ''),
        ('rh.view', '✓', 'Lecture', '✓'),
        ('rh.personnel.view', '✓', 'Lecture', '✓'),
        ('rh.personnel.create', '✓', '—', '✓'),
        ('rh.personnel.edit', '✓', '—', '✓'),
        ('rh.personnel.delete', '✓', '—', '✓'),
        ('rh.contrats.view', '✓', 'Lecture', '✓'),
        ('rh.contrats.edit', '✓', '—', '✓'),
        ('rh.contrats.delete', '✓', '—', '✓'),
        ('rh.documents.view', '✓', '—', '✓'),
        ('rh.documents.edit', '✓', '—', '✓'),
        ('rh.documents.print', '✓', '—', '✓'),
        ('rh.templates.view', '✓', '—', '✓'),
        ('rh.templates.edit', '✓', '—', '✓'),
        ('rh.formations.edit', '✓', '—', '✓'),
        ('rh.competences.edit', '✓', '—', '✓'),
        ('rh.medical.edit', '✓', '—', '✓'),
        ('rh.vie_salarie.edit', '✓', '—', '✓'),
        ('── MODULE PRODUCTION ──', '', '', ''),
        ('production.view', '✓', '✓', '✓'),
        ('production.evaluations.view', '✓', '✓', '—'),
        ('production.evaluations.edit', '✓', '✓', '—'),
        ('production.polyvalence.view', '✓', '✓', 'Lecture'),
        ('production.polyvalence.edit', '✓', '✓', '—'),
        ('production.postes.view', '✓', '✓', 'Lecture'),
        ('production.postes.edit', '✓', '✓', '—'),
        ('production.grilles.view', '✓', '✓', 'Lecture'),
        ('production.grilles.export', '✓', '✓', '—'),
        ('── MODULE PLANNING ──', '', '', ''),
        ('planning.view', '✓', '✓', '✓'),
        ('planning.absences.view', '✓', 'Lecture', '✓'),
        ('planning.absences.edit', '✓', '—', '✓'),
        ('── MODULE ADMINISTRATION ──', '', '', ''),
        ('admin.view', '✓', '—', '—'),
        ('admin.users.*', '✓', '—', '—'),
        ('admin.permissions', '✓', '—', '—'),
        ('admin.historique.view', '✓', '—', 'Lecture'),
        ('admin.historique.export', '✓', '—', '—'),
    ]

    # Séparer les sections
    comp_data = [['Permission', 'ADMIN', 'GESTION_PRODUCTION', 'GESTION_RH']]
    section_rows = []
    for i, row in enumerate(role_comparison):
        if row[0].startswith('──'):
            section_rows.append(i + 1)  # +1 pour l'en-tête
        comp_data.append(list(row))

    ct = Table(comp_data, colWidths=[7*cm, 2*cm, 4*cm, 3.5*cm], repeatRows=1)
    style_list = [
        ('BACKGROUND', (0, 0), (-1, 0), BLUE_DARK),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.3, GREY_LINE),
        ('BOX', (0, 0), (-1, -1), 0.8, BLUE_MID),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]
    # Lignes alternées
    for i in range(1, len(comp_data)):
        if i not in section_rows:
            if i % 2 == 0:
                style_list.append(('BACKGROUND', (0, i), (-1, i), GREY_LIGHT))
            # Colorier ✓ et —
    # Sections en gras bleu
    for sr in section_rows:
        style_list += [
            ('BACKGROUND', (0, sr), (-1, sr), BLUE_LIGHT),
            ('FONTNAME', (0, sr), (-1, sr), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, sr), (-1, sr), BLUE_DARK),
            ('SPAN', (0, sr), (-1, sr)),
        ]
    ct.setStyle(TableStyle(style_list))
    story.append(ct)

    # ── 5. TABLEAU DE BORD ET ACCÈS PAR PERMISSION ──────────────────────────
    story.append(PageBreak())
    story.append(Paragraph('5. Ce que voit chaque rôle dans l\'interface', S['h1']))
    story.append(hr(BLUE_MID, 1))

    story.append(Paragraph('5.1 Tableau de bord principal (dashboard)', S['h2']))
    dash_items = [
        ('Carte Retard Évaluations', 'production.evaluations.view',
         'Affiche les évaluations en retard avec compteur d\'urgence.'),
        ('Carte Prochaines Évaluations', 'production.evaluations.view',
         'Affiche les évaluations à venir dans les prochains jours.'),
        ('Carte Alertes Contrats', 'rh.contrats.edit OU rh.documents.edit',
         'Liste des contrats expirant dans les 30 jours avec filtre par type.'),
        ('Filtre ateliers/postes', 'production.grilles.view',
         'Sélecteurs pour filtrer les évaluations par atelier et poste.'),
    ]
    for elem, perm_key, desc in dash_items:
        t = Table([[
            Paragraph(f'<b>{elem}</b>', S['body_small']),
            Paragraph(perm_key,
                      ParagraphStyle('pk', fontName='Courier', fontSize=8,
                                     textColor=PURPLE)),
            Paragraph(desc, S['body_small']),
        ]], colWidths=[4.5*cm, 5*cm, 8*cm])
        t.setStyle(TableStyle([
            ('LINEBELOW', (0, 0), (-1, -1), 0.3, GREY_LINE),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(t)

    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph('5.2 Menu latéral (drawer)', S['h2']))
    drawer_items = [
        ('Grilles', 'production.grilles.view', 'Accès aux grilles de compétences.'),
        ('Évaluations', 'production.evaluations.view', 'Gestion des évaluations.'),
        ('Gestion RH', 'rh.contrats.edit OU rh.contrats.view OU rh.documents.view',
         'Interface complète de gestion RH.'),
        ('Alertes RH', 'rh.contrats.edit OU rh.documents.edit',
         'Dialog alertes contrats/RH (droits écriture requis).'),
        ('Création/Suppression de poste', 'production.postes.edit',
         'Interface CRUD des postes de travail.'),
        ('Planning', 'planning.view', 'Gestion du planning et régularisations.'),
        ('Documents', 'rh.documents.view', 'Gestion documentaire RH.'),
        ('Historique', 'admin.historique.view', 'Journal d\'audit complet.'),
        ('Administration', 'admin.view', 'Gestion utilisateurs et permissions.'),
    ]
    for item, perm_key, desc in drawer_items:
        t = Table([[
            Paragraph(f'<b>{item}</b>', S['body_small']),
            Paragraph(perm_key,
                      ParagraphStyle('pk2', fontName='Courier', fontSize=8,
                                     textColor=PURPLE)),
            Paragraph(desc, S['body_small']),
        ]], colWidths=[5*cm, 5.5*cm, 7*cm])
        t.setStyle(TableStyle([
            ('LINEBELOW', (0, 0), (-1, -1), 0.3, GREY_LINE),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(t)

    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph('5.3 Gestion RH – Fiche employé (détail des onglets)', S['h2']))
    tabs_items = [
        ('Onglet Données générales', 'rh.personnel.view', 'rh.personnel.edit',
         'Consultation libre si .view. Bouton Modifier si .edit.'),
        ('Onglet Contrat', 'rh.contrats.view', 'rh.contrats.edit + .delete',
         'Lecture si .view. Ajouter/Modifier/Supprimer si .edit/.delete.'),
        ('Onglet Absence', 'planning.absences.view', 'planning.absences.edit',
         'Lecture si .view. Gestion complète si .edit.'),
        ('Onglet Compétences', 'rh.personnel.view', 'rh.competences.edit + .delete',
         'Visible si .view personnel. Actions si .edit/.delete compétences.'),
        ('Onglet Formation', 'rh.personnel.view', 'rh.formations.edit + .delete',
         'Visible si .view personnel. Ajouter/Modifier/Supprimer si .edit/.delete.'),
        ('Onglet Médical', 'rh.personnel.view', 'rh.medical.edit',
         'Visible si .view personnel. Saisie visites et accidents si .edit.'),
        ('Onglet Vie du salarié', 'rh.personnel.view', 'rh.vie_salarie.edit',
         'Visible si .view personnel. Saisie sanctions, entretiens si .edit.'),
        ('Onglet Documents', 'rh.documents.view', 'rh.documents.edit + .print',
         'Consultation si .view. Ajouter/Archiver/Imprimer si .edit/.print.'),
        ('Onglet Déclarations', 'rh.personnel.view', 'rh.declarations.edit',
         'Visible si .view personnel. Gestion complète si .edit.'),
        ('Bouton Actions en masse', '—', 'rh.personnel.edit',
         'Visible uniquement si .edit. Assigne formations/absences/visites à plusieurs employés en lot.'),
    ]
    tab_data = [['Élément', 'Permission lecture', 'Permission écriture', 'Comportement']]
    for row in tabs_items:
        tab_data.append([
            Paragraph(row[0], S['table_cell']),
            Paragraph(row[1], S['table_cell_code']),
            Paragraph(row[2], S['table_cell_code']),
            Paragraph(row[3], S['table_cell']),
        ])
    ot = Table(tab_data, colWidths=[4*cm, 3.5*cm, 4*cm, 6*cm], repeatRows=1)
    ot.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BLUE_DARK),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, GREY_LIGHT]),
        ('GRID', (0, 0), (-1, -1), 0.3, GREY_LINE),
        ('BOX', (0, 0), (-1, -1), 0.8, BLUE_MID),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(ot)

    # ── 6. SÉCURITÉ ──────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph('6. Règles de sécurité', S['h1']))
    story.append(hr(BLUE_MID, 1))

    story.append(Paragraph('6.1 Cache vs vérification base de données', S['h2']))
    story.append(Paragraph(
        'Le système distingue deux types de vérification pour optimiser performance et sécurité :',
        S['body']))

    cache_data = [
        ['Fonction', 'Vérifie', 'Utilisation', 'Performance'],
        ['can(feature)', 'Cache (TTL 5 min)', 'Visibilité des boutons,\néléments UI', 'Rapide'],
        ['require(feature)', 'Base de données\n(par défaut)', 'Opérations critiques\ndans les services', 'Plus lent mais sûr'],
        ['require(feature, fresh=False)', 'Cache', 'Checks non-critiques\ndans les services', 'Rapide'],
        ['require_fresh(feature)', 'Base de données\n(toujours)', 'Opérations très sensibles\n(suppression, admin)', 'Plus lent mais sûr'],
    ]
    ct2 = Table(cache_data, colWidths=[5.5*cm, 4*cm, 4.5*cm, 3.5*cm], repeatRows=1)
    ct2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BLUE_DARK),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, GREY_LIGHT]),
        ('BACKGROUND', (0, 2), (-1, 2), GREEN_LIGHT),
        ('BACKGROUND', (0, 4), (-1, 4), GREEN_LIGHT),
        ('GRID', (0, 0), (-1, -1), 0.3, GREY_LINE),
        ('BOX', (0, 0), (-1, -1), 0.8, BLUE_MID),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 1), (0, -1), 'Courier'),
        ('FONTSIZE', (0, 1), (0, -1), 8),
    ]))
    story.append(ct2)

    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph('6.2 Cas pratiques', S['h2']))

    cases = [
        ('Modification des permissions par un admin',
         'Le cache de l\'utilisateur concerné est invalidé immédiatement. '
         'L\'effet est visible à la prochaine action de l\'utilisateur, sans '
         'nécessiter de déconnexion/reconnexion.'),
        ('Révocation d\'une permission pendant une session active',
         'Si un admin retire une permission à un utilisateur en cours de session, '
         'toute opération critique (service layer) sera refusée immédiatement car '
         'require() vérifie la BDD. Les éléments UI seront masqués au prochain '
         'chargement (max 5 min de délai).'),
        ('Timeout de session (30 min d\'inactivité)',
         'L\'application déconnecte automatiquement l\'utilisateur après 30 minutes '
         'd\'inactivité. Les permissions sont rechargées à la reconnexion.'),
        ('Surcharge utilisateur prioritaire',
         'Si un utilisateur a une surcharge NON sur une permission que son rôle accorde, '
         'c\'est la surcharge qui s\'applique. Inversement, un OUI individuel accorde '
         'l\'accès même si le rôle ne l\'a pas.'),
    ]
    for title, desc in cases:
        story.append(KeepTogether([
            Paragraph(f'<b>• {title}</b>', S['bullet']),
            Paragraph(desc, ParagraphStyle('cd', fontName='Helvetica',
                                           fontSize=9, leading=13,
                                           textColor=GREY_MID,
                                           leftIndent=20, spaceAfter=8)),
        ]))

    story.append(Spacer(1, 0.4*cm))
    b2 = section_box([
        Paragraph('🔒 Bonne pratique : principe du moindre privilège',
                  ParagraphStyle('bpt', fontName='Helvetica-Bold', fontSize=10,
                                 textColor=colors.HexColor('#065f46'))),
        Paragraph(
            'Commencer avec les permissions minimales du rôle standard, puis accorder '
            'des permissions supplémentaires uniquement si nécessaire via les surcharges '
            'individuelles. Ne jamais accorder la permission admin.permissions à un '
            'utilisateur non-administrateur.',
            ParagraphStyle('bpd', fontName='Helvetica', fontSize=9, leading=13,
                           textColor=colors.HexColor('#065f46'))),
    ], bg=GREEN_LIGHT, border=GREEN)
    story.append(b2)

    # ── 7. RÉSUMÉ RAPIDE ──────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph('7. Référence rapide', S['h1']))
    story.append(hr(BLUE_MID, 1))
    story.append(Paragraph(
        'Tableau de synthèse pour identifier rapidement quelle permission activer '
        'selon le besoin fonctionnel.', S['body']))

    quick_ref = [
        ['Besoin', 'Permission à activer'],
        ('L\'utilisateur doit voir la liste du personnel', 'rh.personnel.view'),
        ('L\'utilisateur doit créer de nouveaux employés', 'rh.personnel.create'),
        ('L\'utilisateur doit modifier les fiches employé', 'rh.personnel.edit'),
        ('L\'utilisateur doit faire des actions en lot (masse)', 'rh.personnel.edit'),
        ('L\'utilisateur doit voir les grilles de compétences', 'production.grilles.view'),
        ('L\'utilisateur doit exporter en Excel/PDF', 'production.grilles.export'),
        ('L\'utilisateur doit planifier des évaluations', 'production.evaluations.edit'),
        ('L\'utilisateur doit modifier les niveaux de compétence', 'production.polyvalence.edit'),
        ('L\'utilisateur doit gérer les postes de travail', 'production.postes.edit'),
        ('L\'utilisateur doit voir les alertes de contrats', 'rh.contrats.edit OU rh.documents.edit'),
        ('L\'utilisateur doit gérer les contrats', 'rh.contrats.edit + rh.contrats.delete'),
        ('L\'utilisateur doit gérer les absences', 'planning.absences.edit'),
        ('L\'utilisateur doit gérer les formations', 'rh.formations.edit'),
        ('L\'utilisateur doit accéder aux visites médicales', 'rh.medical.edit'),
        ('L\'utilisateur doit gérer les documents RH', 'rh.documents.edit'),
        ('L\'utilisateur doit gérer les modèles de documents', 'rh.templates.edit'),
        ('L\'utilisateur doit consulter l\'historique', 'admin.historique.view'),
        ('L\'utilisateur doit gérer d\'autres utilisateurs', 'admin.users.* + admin.view'),
        ('L\'utilisateur doit gérer les permissions', 'admin.permissions + admin.view'),
    ]

    qr_data = [[Paragraph(quick_ref[0][0], S['table_header']),
                 Paragraph(quick_ref[0][1], S['table_header'])]]
    for i, (besoin, perm_key) in enumerate(quick_ref[1:]):
        qr_data.append([
            Paragraph(besoin, S['table_cell']),
            Paragraph(perm_key, S['table_cell_code']),
        ])

    qrt = Table(qr_data, colWidths=[10*cm, 7.5*cm], repeatRows=1)
    qrt.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BLUE_DARK),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, GREY_LIGHT]),
        ('GRID', (0, 0), (-1, -1), 0.3, GREY_LINE),
        ('BOX', (0, 0), (-1, -1), 0.8, BLUE_MID),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(qrt)

    story.append(Spacer(1, 0.6*cm))
    story.append(Paragraph('Glossaire', S['h2']))
    glossary = [
        ('Feature', 'Unité atomique de permission identifiée par une clé (ex. rh.personnel.edit).'),
        ('Rôle', 'Ensemble de features accordées à un groupe d\'utilisateurs.'),
        ('Surcharge (override)', 'Permission individuelle qui prend le dessus sur celle du rôle.'),
        ('Cache', 'Copie en mémoire des permissions chargées à la connexion (TTL 5 min).'),
        ('TTL', 'Time To Live – durée de validité du cache (5 minutes).'),
        ('TOCTOU', 'Time Of Check / Time Of Use – type d\'attaque par race condition sur les permissions. '
                   'Protégé par require() qui vérifie la BDD.'),
        ('require()', 'Fonction qui lève une PermissionError si la permission est refusée. '
                      'Vérifie la BDD par défaut.'),
        ('can()', 'Fonction qui retourne True/False depuis le cache. Utilisée pour l\'UI.'),
    ]
    for term, definition in glossary:
        t = Table([[
            Paragraph(f'<b>{term}</b>', S['body_small']),
            Paragraph(definition, S['body_small']),
        ]], colWidths=[3.5*cm, doc.width - 3.5*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), BLUE_PALE),
            ('LINEBELOW', (0, 0), (-1, -1), 0.3, GREY_LINE),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(t)

    # BUILD
    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    print(f"PDF genere : {os.path.abspath(OUTPUT_PATH)}")


if __name__ == '__main__':
    build_pdf()
