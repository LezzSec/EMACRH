# -*- mode: python ; coding: utf-8 -*-
# ✅ VERSION OPTIMISÉE : Démarrage rapide (~2-3 secondes)
# 🔧 MISE À JOUR : Tous les hiddenimports et datas nécessaires pour .exe

block_cipher = None

a = Analysis(
    ['core\\gui\\main_qt.py'],
    pathex=['.'],  # Le répertoire courant (App/)
    binaries=[],
    datas=[
        # ✅ Fichiers SQL pour migrations/vérifications (optionnel)
        ('database\\schema\\*.sql', 'database\\schema'),
        ('database\\migrations\\*.sql', 'database\\migrations'),
        # NOTE: Le .env sera copié manuellement par le script build_clean.bat
    ],
    hiddenimports=[
        # ============ Sécurité (CRITIQUE pour authentification) ============
        'bcrypt',
        'bcrypt._bcrypt',  # Module C compilé de bcrypt
        '_cffi_backend',   # Dépendance de bcrypt

        # ============ Configuration (CRITIQUE pour .env) ============
        'dotenv',

        # ============ PyQt5 ============
        'PyQt5.QtPrintSupport',

        # ============ GUI Modules (tous les dialogues) ============
        'core.gui.gestion_personnel',
        'core.gui.manage_operateur',
        'core.gui.gestion_evaluation',
        'core.gui.liste_et_grilles',
        'core.gui.creation_modification_poste',
        'core.gui.historique',
        'core.gui.planning_absences',
        'core.gui.planning',
        'core.gui.contract_management',
        'core.gui.gestion_documentaire',
        'core.gui.gestion_documents_widget',
        'core.gui.document_dashboard',
        'core.gui.gestion_absences',
        'core.gui.gestion_rh',
        'core.gui.historique_personnel',
        'core.gui.import_historique_polyvalence',
        'core.gui.besoin_poste_dialog',
        'core.gui.ui_theme',
        'core.gui.emac_ui_kit',

        # ============ Services ============
        'core.services.auth_service',  # AJOUTÉ pour authentification
        'core.services.log_exporter',
        'core.services.document_service',
        'core.services.absence_service',
        'core.services.contrat_service',
        'core.services.evaluation_service',
        'core.services.calendrier_service',
        'core.services.matricule_service',
        'core.services.logger',
        'core.services.polyvalence_logger',
        'core.services.audit_logger',
        'core.services.liste_et_grilles_service',

        # ============ Utils (chemins compatibles .exe) ============
        'core.utils.app_paths',

        # ============ Database ============
        'core.db.configbd',
        'core.db.import_infos',

        # ============ Exporters ============
        'core.exporters.excel_export',
        'core.exporters.pdf_export',
        'core.exporters.log_export',

        # ============ ReportLab (exports PDF) ============
        'reportlab',
        'reportlab.lib',
        'reportlab.lib.pagesizes',
        'reportlab.lib.styles',
        'reportlab.lib.colors',
        'reportlab.lib.units',
        'reportlab.lib.enums',
        'reportlab.platypus',
        'reportlab.platypus.paragraph',
        'reportlab.platypus.tables',
        'reportlab.platypus.frames',
        'reportlab.platypus.doctemplate',
        'reportlab.pdfgen',
        'reportlab.pdfgen.canvas',
        'reportlab.pdfbase',
        'reportlab.pdfbase.pdfmetrics',
        'reportlab.pdfbase.ttfonts',

        # ============ OpenPyXL (exports Excel) ============
        'openpyxl',
        'openpyxl.styles',
        'openpyxl.styles.alignment',
        'openpyxl.styles.borders',
        'openpyxl.styles.colors',
        'openpyxl.styles.fills',
        'openpyxl.styles.fonts',
        'openpyxl.utils',
        'openpyxl.utils.dataframe',
        'openpyxl.worksheet',
        'openpyxl.worksheet.worksheet',
        'openpyxl.workbook',
        'openpyxl.workbook.workbook',
        'openpyxl.cell',
        'openpyxl.cell.cell',

        # ============ Pandas (grilles de données) ============
        'pandas',
        'pandas.core',
        'pandas.core.frame',
        'pandas.io',
        'pandas.io.excel',

        # ============ MySQL Connector ============
        'mysql.connector',
        'mysql.connector.cursor',
        'mysql.connector.pooling',

        # ============ Autres dépendances ============
        'datetime',
        'pathlib',
        'zipfile',
        'csv',
        'json',
        'logging',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # ============ OPTIMISATION : Exclure les modules inutiles ============
        # Interfaces graphiques alternatives
        'tkinter',
        'tkinter.ttk',

        # Bibliothèques scientifiques non utilisées
        'matplotlib',
        'scipy',
        'numpy.testing',
        'numpy.tests',

        # Modules de test
        'pandas.tests',
        'pandas.testing',
        'test',
        'unittest',
        'pytest',
        'nose',

        # Environnements de développement
        'IPython',
        'jupyter',
        'notebook',

        # Modules Python rarement utilisés
        'pydoc',
        'doctest',
        'pdb',
        'profile',
        'pstats',

        # Serveurs web (si non utilisés)
        'http.server',
        'xmlrpc',

        # Nos propres scripts de dev (CRITIQUE - ne pas inclure dans le build)
        'scripts',
        'tests',
        'demo_ui_kit',
        'test_startup_time',

        # Scripts d'insertion BDD (ne pas inclure en production)
        'core.db.insert_atelier',
        'core.db.insert_date',
        'core.db.insert_polyvalence',
        'core.db.insert_postes',
        'core.db.insert_operateurs',
        'core.db.insert_besoins_postes',
    ],
    noarchive=False,
    optimize=2,  # ✅ Optimisation Python bytecode (supprime docstrings, assertions)
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ✅ MODE ONE-FOLDER : Pas de décompression au démarrage
exe = EXE(
    pyz,
    a.scripts,
    [],  # ✅ IMPORTANT : Liste vide = mode one-folder
    exclude_binaries=True,  # ✅ Les binaires sont dans le dossier, pas dans l'EXE
    name='EMAC',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # ✅ DÉSACTIVÉ pour réseau : UPX ralentit la décompression sur partages réseau
    console=True,  # ✅ ACTIVÉ POUR DEBUG - Voir les erreurs au démarrage
    runtime_tmpdir=None,  # ✅ Force l'extraction dans %TEMP% local (pas sur le réseau)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Ajoutez un chemin vers .ico si vous avez un logo
)

# ✅ Création du dossier avec tous les fichiers
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,  # ✅ Désactivé pour performance réseau
    upx_exclude=[],
    name='EMAC',
)
