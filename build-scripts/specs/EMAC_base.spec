# -*- mode: python ; coding: utf-8 -*-
"""
EMAC_base.spec - Configuration PyInstaller
===========================================

Application: EMAC - Gestion du Personnel et Polyvalence
Version: 2026-02-16
Build: One-folder optimise

Changements recents:
--------------------
- Templates et documents stockes en BLOB dans MySQL
  -> Plus besoin du dossier templates/ dans le build
- Ajout hidden imports: mimetypes, tempfile, shutil (services BLOB)
- Suppression dossier templates des datas

Usage:
------
cd EMAC
pyinstaller build-scripts/specs/EMAC_base.spec

Sortie:
-------
dist/EMAC/EMAC.exe
"""

import os
import sys

# ============================================================================
# CONFIGURATION GLOBALE
# ============================================================================

# Racine du projet (2 niveaux au-dessus du .spec)
# SPECPATH = repertoire du fichier .spec (fourni par PyInstaller)
PROJECT_ROOT = os.path.abspath(os.path.join(SPECPATH, '..', '..'))

block_cipher = None
APP_NAME = 'EMAC'
MAIN_SCRIPT = os.path.join(PROJECT_ROOT, 'App', 'core', 'gui', 'main_qt.py')

# ============================================================================
# EXCLUSIONS
# ============================================================================

EXCLUDES = [
    # Data science (non utilise)
    'pandas', 'numpy', 'matplotlib', 'scipy', 'sklearn',
    'seaborn', 'statsmodels',

    # GUI alternatives
    'tkinter', 'wx', 'PySide2', 'PySide6', 'PyQt6', 'kivy',

    # Frameworks web
    'flask', 'django', 'tornado', 'fastapi', 'aiohttp',
    'requests', 'urllib3',

    # Tests
    'pytest', 'nose', 'coverage', 'hypothesis', '_pytest',

    # Documentation
    'sphinx', 'docutils', 'jinja2',

    # Image processing (PIL garde pour ReportLab)
    'imageio', 'opencv',

    # Jupyter
    'jupyter', 'IPython', 'notebook', 'ipykernel',

    # Compilation / build
    'Cython', 'numba', 'pyinstaller',
    'setuptools', 'pip', 'wheel', 'distutils',

    # Crypto non utilise
    'OpenSSL',

    # Reseau non utilise
    'ftplib', 'telnetlib', 'xmlrpc',
]

# ============================================================================
# HIDDEN IMPORTS
# ============================================================================

HIDDEN_IMPORTS = [
    # === MySQL Connector ===
    'mysql.connector',
    'mysql.connector.pooling',
    'mysql.connector.cursor',
    'mysql.connector.connection',
    'mysql.connector.errors',
    'mysql.connector.constants',

    # === PyQt5 ===
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
    'PyQt5.QtPrintSupport',
    'PyQt5.QtSvg',
    'PyQt5.sip',

    # === ReportLab (PDF) ===
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

    # === Openpyxl (Excel) ===
    'openpyxl',
    'openpyxl.cell',
    'openpyxl.cell._writer',
    'openpyxl.styles',
    'openpyxl.workbook',
    'openpyxl.worksheet',
    'openpyxl.utils',

    # === Bcrypt (Auth) ===
    'bcrypt',
    'bcrypt._bcrypt',

    # === Environment ===
    'dotenv',

    # === Stockage BLOB (documents/templates en base) ===
    'tempfile',
    'mimetypes',
    'shutil',

    # === Standard lib requis ===
    'datetime',
    'decimal',
    'json',
    'logging',
    'threading',
    'os',
    'sys',
    'pathlib',
    'dataclasses',

    # === Threads / Async ===
    'queue',
    'concurrent',
    'concurrent.futures',
]

# ============================================================================
# FICHIERS DE DONNEES
# ============================================================================
# Templates et documents sont maintenant stockes en BLOB dans MySQL.
# Plus besoin d'inclure le dossier templates/ dans le build.

DATA_FILES = [
    # Configuration template
    (os.path.join(PROJECT_ROOT, 'App', 'config', '.env.example'), 'config'),
]

# Ajouter .env.encrypted si present
env_encrypted = os.path.join(PROJECT_ROOT, 'App', '.env.encrypted')
if os.path.exists(env_encrypted):
    DATA_FILES.append((env_encrypted, '.'))

# ============================================================================
# ANALYSIS
# ============================================================================

a = Analysis(
    [MAIN_SCRIPT],
    pathex=[os.path.join(PROJECT_ROOT, 'App')],
    binaries=[],
    datas=DATA_FILES,
    hiddenimports=HIDDEN_IMPORTS,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
    noarchive=False,
    optimize=2,
    cipher=block_cipher,
)

# ============================================================================
# PYZ
# ============================================================================

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

# ============================================================================
# EXE
# ============================================================================

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=False,
    console=False,           # TEMPORAIRE: mettre False pour production
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
    uac_admin=False,
    uac_uiaccess=False,
)

# ============================================================================
# COLLECT
# ============================================================================

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=True,
    upx=False,
    upx_exclude=[],
    name=APP_NAME,
)

# ============================================================================
# POST-BUILD INFO
# ============================================================================

print("\n" + "=" * 70)
print(f"  EMAC - Build Configuration")
print("=" * 70)
print(f"  Script principal  : {MAIN_SCRIPT}")
print(f"  Mode              : One-folder")
print(f"  Optimisation      : Level 2")
print(f"  Strip             : Oui")
print(f"  UPX               : Non (evite antivirus)")
print(f"  Console           : Non (GUI)")
print(f"  Modules exclus    : {len(EXCLUDES)}")
print(f"  Hidden imports    : {len(HIDDEN_IMPORTS)}")
print(f"  Fichiers donnees  : {len(DATA_FILES)}")
print(f"  Templates         : En base MySQL (BLOB)")
print("=" * 70)
print(f"  Sortie : dist/{APP_NAME}/{APP_NAME}.exe")
print("=" * 70 + "\n")
