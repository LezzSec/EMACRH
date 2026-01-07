# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['App\\core\\gui\\main_qt.py'],
    pathex=[],
    binaries=[],
    datas=[('App/config/.env.example', 'config')],
    hiddenimports=['mysql.connector', 'PyQt5.QtPrintSupport', 'reportlab.pdfbase.ttfonts', 'openpyxl.cell._writer', 'bcrypt._bcrypt', 'dotenv'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pandas', 'numpy', 'matplotlib', 'tkinter'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='EMAC',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='EMAC',
)
