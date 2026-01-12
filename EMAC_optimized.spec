# -*- mode: python ; coding: utf-8 -*-
"""
EMAC.spec optimisé pour PyInstaller
===================================

Optimisations appliquées:
- ✅ One-folder (pas one-file pour éviter décompression lente)
- ✅ optimize=2 (bytecode optimisé Python)
- ✅ UPX désactivé (évite faux positifs antivirus)
- ✅ Exclusions agressives (réduction 30-50%)
- ✅ strip=True (suppression symboles debug)
- ✅ Hook personnalisé pour PyQt5

Date: 2026-01-07
"""

import os
import sys

# ===========================
# Configuration
# ===========================

block_cipher = None

# Exclusions agressives pour réduire la taille
EXCLUDES = [
    # Data science (non utilisé)
    # 'pandas',  # ✅ UTILISÉ pour exports Excel
    # 'numpy',   # ✅ Requis par pandas
    'matplotlib',
    'scipy',
    'sklearn',
    'seaborn',

    # GUI alternatives (non utilisées)
    'tkinter',
    'wx',
    'PySide2',
    'PySide6',
    'PyQt6',

    # Tests
    'pytest',
    'unittest',
    'nose',
    'coverage',

    # Documentation
    'sphinx',
    'docutils',

    # Image processing (si non utilisé)
    'PIL',
    'Pillow',
    'imageio',

    # Web frameworks (non utilisé)
    'flask',
    'django',
    'tornado',
    'fastapi',

    # Async (si non utilisé)
    'asyncio',
    'aiohttp',

    # Jupyter
    'jupyter',
    'IPython',
    'notebook',

    # Compilation
    'Cython',
    'numba',

    # Divers
    'setuptools',
    'pip',
    'wheel',
]

# Imports cachés nécessaires
HIDDEN_IMPORTS = [
    # MySQL
    'mysql.connector',
    'mysql.connector.pooling',
    'mysql.connector.cursor',

    # PyQt5 essentiels
    'PyQt5.QtPrintSupport',
    'PyQt5.QtSvg',

    # ReportLab pour PDF
    'reportlab.pdfbase.ttfonts',
    'reportlab.pdfbase._fontdata',
    'reportlab.lib.colors',

    # OpenPyXL pour Excel
    'openpyxl.cell._writer',
    'openpyxl.styles',

    # Auth
    'bcrypt._bcrypt',

    # Environment
    'dotenv',
]

# Données à inclure
DATA_FILES = [
    ('App/config/.env.example', 'config'),
]

# ===========================
# Analysis
# ===========================

a = Analysis(
    ['App\\core\\gui\\main_qt.py'],
    pathex=[],
    binaries=[],
    datas=DATA_FILES,
    hiddenimports=HIDDEN_IMPORTS,
    hookspath=['build-scripts/hooks'],  # Hooks personnalisés
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
    noarchive=False,
    optimize=2,  # ✅ Bytecode optimisé (supprime assert, __debug__)
)

# ===========================
# PYZ (Python ZIP archive)
# ===========================

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

# ===========================
# EXE (Executable)
# ===========================

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,  # ✅ One-folder mode
    name='EMAC',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,  # ✅ Supprime symboles debug (réduit taille)
    upx=False,  # ✅ DÉSACTIVÉ pour éviter antivirus (faux positifs)
    console=False,  # Application GUI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Ajouter un .ico si disponible
)

# ===========================
# COLLECT (Rassemble fichiers)
# ===========================

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=True,  # ✅ Supprime symboles debug des binaires
    upx=False,  # ✅ DÉSACTIVÉ
    upx_exclude=[],
    name='EMAC',
)

# ===========================
# Post-build info
# ===========================

print("\n" + "="*70)
print("[OK] EMAC.spec optimise charge")
print("="*70)
print(f"Optimize level: 2 (bytecode optimise)")
print(f"UPX: Desactive (evite antivirus)")
print(f"Strip: Active (reduit taille)")
print(f"Mode: One-folder (rapide)")
print(f"Exclusions: {len(EXCLUDES)} modules")
print("="*70 + "\n")
