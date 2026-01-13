# -*- mode: python ; coding: utf-8 -*-
"""
EMAC.spec - Configuration PyInstaller Optimisée
================================================

Application: EMAC - Gestion du Personnel et Polyvalence
Version: 2026-01-13
Build: One-folder optimisé

Optimisations appliquées:
--------------------------
✅ optimize=2           - Bytecode Python optimisé (-30% taille)
✅ strip=True           - Suppression symboles debug (-20% taille)
✅ UPX désactivé        - Évite faux positifs antivirus
✅ One-folder mode      - Lancement rapide (pas de décompression)
✅ Exclusions ciblées   - Modules non utilisés exclus
✅ Hidden imports       - Dépendances dynamiques incluses

Taille estimée du build: ~120-150 MB (vs 300+ MB non optimisé)
Temps de build: ~2-3 minutes

Usage:
------
pyinstaller EMAC.spec

Sortie:
-------
dist/EMAC/EMAC.exe
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# ============================================================================
# CONFIGURATION GLOBALE
# ============================================================================

block_cipher = None
APP_NAME = 'EMAC'
MAIN_SCRIPT = 'App/core/gui/main_qt.py'

# ============================================================================
# EXCLUSIONS AGRESSIVES
# ============================================================================
# Modules qui ne seront JAMAIS inclus dans le build

EXCLUDES = [
    # ===== DATA SCIENCE (NON UTILISÉ) =====
    'pandas',           # Excel géré par openpyxl uniquement
    'numpy',
    'matplotlib',
    'scipy',
    'sklearn',
    'seaborn',
    'statsmodels',

    # ===== GUI ALTERNATIVES (NON UTILISÉES) =====
    'tkinter',
    'wx',
    'PySide2',
    'PySide6',
    'PyQt6',
    'kivy',

    # ===== FRAMEWORKS WEB (NON UTILISÉ) =====
    'flask',
    'django',
    'tornado',
    'fastapi',
    'aiohttp',
    'requests',
    'urllib3',

    # ===== TESTS =====
    'pytest',
    'unittest',
    'nose',
    'coverage',
    'hypothesis',
    '_pytest',

    # ===== DOCUMENTATION =====
    'sphinx',
    'docutils',
    'jinja2',

    # ===== IMAGE PROCESSING (NON UTILISÉ) =====
    'PIL',
    'Pillow',
    'imageio',
    'opencv',

    # ===== ASYNC (NON UTILISÉ) =====
    'asyncio',
    'concurrent.futures',

    # ===== JUPYTER =====
    'jupyter',
    'IPython',
    'notebook',
    'ipykernel',

    # ===== COMPILATION =====
    'Cython',
    'numba',
    'pyinstaller',

    # ===== BUILD TOOLS =====
    'setuptools',
    'pip',
    'wheel',
    'distutils',

    # ===== CRYPTO NON UTILISÉ =====
    'cryptography',
    'OpenSSL',

    # ===== AUTRES =====
    'email',
    'ftplib',
    'telnetlib',
    'xmlrpc',
]

# ============================================================================
# HIDDEN IMPORTS
# ============================================================================
# Modules importés dynamiquement qui doivent être inclus explicitement

HIDDEN_IMPORTS = [
    # ===== MYSQL CONNECTOR =====
    'mysql.connector',
    'mysql.connector.pooling',
    'mysql.connector.cursor',
    'mysql.connector.connection',
    'mysql.connector.errors',
    'mysql.connector.constants',

    # ===== PYQT5 ESSENTIELS =====
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
    'PyQt5.QtPrintSupport',
    'PyQt5.QtSvg',
    'PyQt5.sip',

    # ===== REPORTLAB (PDF) =====
    'reportlab.pdfgen',
    'reportlab.lib',
    'reportlab.lib.colors',
    'reportlab.lib.pagesizes',
    'reportlab.lib.styles',
    'reportlab.lib.units',
    'reportlab.platypus',
    'reportlab.pdfbase',
    'reportlab.pdfbase.ttfonts',
    'reportlab.pdfbase._fontdata',
    'reportlab.pdfbase.pdfmetrics',

    # ===== OPENPYXL (EXCEL) =====
    'openpyxl',
    'openpyxl.cell',
    'openpyxl.cell._writer',
    'openpyxl.styles',
    'openpyxl.workbook',
    'openpyxl.worksheet',
    'openpyxl.utils',

    # ===== BCRYPT (AUTH) =====
    'bcrypt',
    'bcrypt._bcrypt',

    # ===== ENVIRONMENT =====
    'dotenv',

    # ===== STANDARD LIB REQUIS =====
    'datetime',
    'decimal',
    'json',
    'logging',
    'sqlite3',
    'threading',
]

# ============================================================================
# FICHIERS DE DONNÉES
# ============================================================================
# Fichiers non-Python à inclure dans le build

DATA_FILES = [
    # Configuration template
    ('App/config/.env.example', 'config'),

    # Schéma de base de données (pour référence)
    ('App/database/schema/bddemac.sql', 'database/schema'),
]

# ============================================================================
# BINARIES ADDITIONNELS
# ============================================================================
# Bibliothèques natives requises (auto-détectées, liste vide par défaut)

BINARIES = []

# ============================================================================
# ANALYSIS
# ============================================================================

a = Analysis(
    [MAIN_SCRIPT],
    pathex=[],
    binaries=BINARIES,
    datas=DATA_FILES,
    hiddenimports=HIDDEN_IMPORTS,
    hookspath=['build-scripts/hooks'],  # Hooks personnalisés si existants
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
    noarchive=False,
    optimize=2,  # ✅ OPTIMISATION MAXIMALE: supprime asserts, __debug__, docstrings
    cipher=block_cipher,
)

# ============================================================================
# PYZ (Archive Python ZIP)
# ============================================================================

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

# ============================================================================
# EXE (Exécutable Windows)
# ============================================================================

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,  # ✅ ONE-FOLDER MODE (rapide)
    name=APP_NAME,
    debug=False,            # Pas de debug
    bootloader_ignore_signals=False,
    strip=True,             # ✅ STRIP SYMBOLS (réduit taille ~20%)
    upx=False,              # ✅ DÉSACTIVÉ (évite antivirus)
    console=False,          # Application GUI (pas de console)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,              # TODO: Ajouter icon='App/resources/icon.ico'
    uac_admin=False,        # Pas besoin de droits admin
    uac_uiaccess=False,
)

# ============================================================================
# COLLECT (Rassemble tous les fichiers)
# ============================================================================

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=True,             # ✅ STRIP BINARIES
    upx=False,              # ✅ DÉSACTIVÉ
    upx_exclude=[],
    name=APP_NAME,
)

# ============================================================================
# POST-BUILD INFO
# ============================================================================

print("\n" + "=" * 80)
print(f"{'EMAC.spec - Configuration PyInstaller':^80}")
print("=" * 80)
print(f"✅ Script principal    : {MAIN_SCRIPT}")
print(f"✅ Mode de build       : One-folder (rapide)")
print(f"✅ Optimisation Python : Level 2 (bytecode optimisé)")
print(f"✅ Strip symbols       : Activé (réduit taille)")
print(f"✅ UPX compression     : Désactivé (évite antivirus)")
print(f"✅ Console             : Désactivée (GUI uniquement)")
print(f"✅ Modules exclus      : {len(EXCLUDES)} modules")
print(f"✅ Imports cachés      : {len(HIDDEN_IMPORTS)} modules")
print(f"✅ Fichiers données    : {len(DATA_FILES)} fichiers")
print("=" * 80)
print(f"📦 Sortie attendue     : dist/{APP_NAME}/{APP_NAME}.exe")
print(f"📊 Taille estimée      : ~120-150 MB")
print(f"⏱️  Temps de build      : ~2-3 minutes")
print("=" * 80 + "\n")
