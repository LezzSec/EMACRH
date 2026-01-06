# -*- mode: python ; coding: utf-8 -*-
"""
Configuration PyInstaller pour EMAC - Mode ONEFILE (fichier unique)
Inclut le fichier .env pour la connexion à la base de données
"""

import os
from PyInstaller.utils.hooks import collect_data_files

# IMPORTANT: Inclure le fichier .env avec les identifiants DB
datas = []
env_file = os.path.join(SPECPATH, '.env')
if os.path.exists(env_file):
    datas.append(('.env', '.'))
    print("[OK] Fichier .env inclus dans l'EXE")
else:
    print("[ATTENTION] Fichier .env non trouve!")

# Inclure les données de ReportLab et pytz
datas += collect_data_files('reportlab')
datas += collect_data_files('pytz')

a = Analysis(
    ['core\\gui\\main_qt.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'mysql.connector',
        'mysql.connector.pooling',
        'bcrypt',
        'PyQt5.QtPrintSupport',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'IPython', 'jupyter'],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,      # <- ONEFILE: Tout empaqueté dans l'EXE
    a.zipfiles,
    a.datas,
    [],
    name='EMAC',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
