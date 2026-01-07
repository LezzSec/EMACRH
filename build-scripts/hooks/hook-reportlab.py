# -*- coding: utf-8 -*-
"""
Hook PyInstaller pour ReportLab
Réduit la taille en excluant les polices et modules non essentiels
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collecter seulement les données essentielles
datas = collect_data_files('reportlab', subdir='fonts', includes=['*.afm', '*.pfb'])

# Modules essentiels ReportLab
hiddenimports = [
    'reportlab.pdfbase',
    'reportlab.pdfbase.ttfonts',
    'reportlab.pdfbase._fontdata',
    'reportlab.lib',
    'reportlab.lib.colors',
    'reportlab.lib.pagesizes',
    'reportlab.lib.styles',
    'reportlab.lib.units',
    'reportlab.platypus',
    'reportlab.platypus.paragraph',
    'reportlab.platypus.tables',
]

# Exclure les modules non utilisés
excludedimports = [
    'reportlab.graphics.charts',  # Charts non utilisés
    'reportlab.graphics.barcode',  # Barcodes non utilisés
]

print(f"✅ Hook ReportLab: modules essentiels inclus, charts/barcodes exclus")
