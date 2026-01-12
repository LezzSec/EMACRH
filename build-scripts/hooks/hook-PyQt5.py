# -*- coding: utf-8 -*-
"""
Hook PyInstaller personnalisé pour PyQt5
Réduit la taille en excluant les modules PyQt5 non utilisés
"""

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Modules PyQt5 à EXCLURE (non utilisés par EMAC)
EXCLUDED_PYQT5_MODULES = [
    'PyQt5.QtBluetooth',
    'PyQt5.QtDBus',
    'PyQt5.QtDesigner',
    'PyQt5.QtHelp',
    'PyQt5.QtLocation',
    'PyQt5.QtMultimedia',
    'PyQt5.QtMultimediaWidgets',
    'PyQt5.QtNetwork',  # ⚠️ Vérifier si utilisé
    'PyQt5.QtNfc',
    'PyQt5.QtOpenGL',
    'PyQt5.QtPositioning',
    'PyQt5.QtQml',
    'PyQt5.QtQuick',
    'PyQt5.QtQuickWidgets',
    'PyQt5.QtSensors',
    'PyQt5.QtSerialPort',
    'PyQt5.QtSql',
    'PyQt5.QtTest',
    'PyQt5.QtWebChannel',
    'PyQt5.QtWebEngine',
    'PyQt5.QtWebEngineCore',
    'PyQt5.QtWebEngineWidgets',
    'PyQt5.QtWebSockets',
    'PyQt5.QtXml',
    'PyQt5.QtXmlPatterns',
]

# Modules PyQt5 ESSENTIELS pour EMAC
REQUIRED_PYQT5_MODULES = [
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
    'PyQt5.QtPrintSupport',  # Pour impression/PDF
    'PyQt5.QtSvg',  # Pour icônes SVG si utilisées
]

# Collecter uniquement les modules essentiels
hiddenimports = REQUIRED_PYQT5_MODULES

# Exclure les modules non utilisés
excludedimports = EXCLUDED_PYQT5_MODULES

print(f"[OK] Hook PyQt5: {len(REQUIRED_PYQT5_MODULES)} modules inclus, {len(EXCLUDED_PYQT5_MODULES)} exclus")
