# -*- mode: python ; coding: utf-8 -*-
"""
Fichier de configuration PyInstaller pour EMAC
"""

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collecter les données et sous-modules
datas = [
    ('App/config', 'config'),
    ('App/database/schema', 'database/schema'),
    ('App/database/migrations', 'database/migrations'),
    ('docs', 'docs'),
    ('README.md', '.'),
    ('App/core', 'core'),
]

# Modules cachés à inclure explicitement
hiddenimports = [
    'mysql.connector',
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
    'pandas',
    'openpyxl',
    'reportlab',
    'bcrypt',
    'dotenv',
]

a = Analysis(
    ['App/main.py'],
    pathex=['App'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='EMAC',
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Activer la console pour voir les erreurs
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='EMAC',
)
