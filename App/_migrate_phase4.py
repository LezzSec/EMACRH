# -*- coding: utf-8 -*-
"""Migration Phase 4 - Mise a jour des imports apres deplacement de core/gui/ vers gui/"""
import os
import re

replacements = [
    # contrat_service_crud
    ("from domain.services.rh.contrat_service_crud import", "from domain.services.rh.contrat_service_crud import"),
    ("import domain.services.rh.contrat_service_crud", "import domain.services.rh.contrat_service_crud"),

    # main gui
    ("from gui.main_qt import", "from gui.main_qt import"),
    ("import gui.main_qt", "import gui.main_qt"),

    # components
    ("from gui.components.", "from gui.components."),
    ("import gui.components.", "import gui.components."),

    # workers
    ("from gui.workers.", "from gui.workers."),
    ("import gui.workers.", "import gui.workers."),

    # view_models
    ("from gui.view_models.", "from gui.view_models."),
    ("import gui.view_models.", "import gui.view_models."),

    # utils
    ("from gui.utils.", "from gui.utils."),
    ("import gui.utils.", "import gui.utils."),

    # screens rh - plus specifique en premier
    ("from gui.screens.rh.domaines.", "from gui.screens.rh.domaines."),
    ("from gui.screens.rh.", "from gui.screens.rh."),
    ("from gui.screens.rh.gestion_rh_dialogs import", "from gui.screens.rh.gestion_rh_dialogs import"),
    ("from gui.screens.rh.gestion_rh import", "from gui.screens.rh.gestion_rh import"),
    ("from gui.screens.rh.gestion_alertes_rh import", "from gui.screens.rh.gestion_alertes_rh import"),
    ("from gui.screens.rh.contract_management_refactored import", "from gui.screens.rh.contract_management_refactored import"),

    # screens personnel
    ("from gui.screens.personnel.gestion_personnel import", "from gui.screens.personnel.gestion_personnel import"),
    ("from gui.screens.personnel.manage_operateur import", "from gui.screens.personnel.manage_operateur import"),
    ("from gui.screens.personnel.historique_personnel import", "from gui.screens.personnel.historique_personnel import"),
    ("from gui.screens.personnel.bulk_assignment import", "from gui.screens.personnel.bulk_assignment import"),

    # screens formation
    ("from gui.screens.formation.gestion_formations import", "from gui.screens.formation.gestion_formations import"),
    ("from gui.screens.formation.catalogue_formation_dialog import", "from gui.screens.formation.catalogue_formation_dialog import"),
    ("from gui.screens.formation.gestion_evaluation import", "from gui.screens.formation.gestion_evaluation import"),
    ("from gui.screens.formation.liste_et_grilles import", "from gui.screens.formation.liste_et_grilles import"),
    ("from gui.screens.formation.import_historique_polyvalence import", "from gui.screens.formation.import_historique_polyvalence import"),
    ("from gui.screens.formation.besoin_poste_dialog import", "from gui.screens.formation.besoin_poste_dialog import"),

    # screens planning
    ("from gui.screens.planning.planning import", "from gui.screens.planning.planning import"),
    ("from gui.screens.planning.planning_absences import", "from gui.screens.planning.planning_absences import"),
    ("from gui.screens.planning.gestion_absences import", "from gui.screens.planning.gestion_absences import"),

    # screens documents
    ("from gui.screens.documents.gestion_documentaire import", "from gui.screens.documents.gestion_documentaire import"),
    ("from gui.screens.documents.gestion_documents_widget import", "from gui.screens.documents.gestion_documents_widget import"),
    ("from gui.screens.documents.gestion_templates import", "from gui.screens.documents.gestion_templates import"),
    ("from gui.screens.documents.document_proposal_dialog import", "from gui.screens.documents.document_proposal_dialog import"),
    ("from gui.screens.documents.imprimer_documents_dialog import", "from gui.screens.documents.imprimer_documents_dialog import"),

    # screens admin
    ("from gui.screens.admin.admin_data_panel import", "from gui.screens.admin.admin_data_panel import"),
    ("from gui.screens.admin.user_management import", "from gui.screens.admin.user_management import"),
    ("from gui.screens.admin.feature_puzzle import", "from gui.screens.admin.feature_puzzle import"),
    ("from gui.screens.admin.login_dialog import", "from gui.screens.admin.login_dialog import"),
    ("from gui.screens.admin.historique import", "from gui.screens.admin.historique import"),
    ("from gui.screens.admin.creation_modification_poste import", "from gui.screens.admin.creation_modification_poste import"),

    # catch-all dialogs
    ("from gui.screens.", "from gui.screens."),
    ("import gui.screens.", "import gui.screens."),

    # catch-all final core.gui
    ("from gui.", "from gui."),
    ("import gui.", "import gui."),
]

app_dir = os.path.dirname(os.path.abspath(__file__))
modified_files = []
errors = []

for root, dirs, files in os.walk(app_dir):
    # Ignorer __pycache__ et .git
    dirs[:] = [d for d in dirs if d not in ('__pycache__', '.git')]
    for fname in files:
        if not fname.endswith('.py'):
            continue
        fpath = os.path.join(root, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            errors.append(f"LIRE {fpath}: {e}")
            continue

        new_content = content
        for old, new in replacements:
            new_content = new_content.replace(old, new)

        if new_content != content:
            try:
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                rel = os.path.relpath(fpath, app_dir)
                modified_files.append(rel)
            except Exception as e:
                errors.append(f"ECRIRE {fpath}: {e}")

print(f"Fichiers modifies: {len(modified_files)}")
for f in sorted(modified_files):
    print(f"  {f}")
if errors:
    print(f"\nErreurs: {len(errors)}")
    for e in errors:
        print(f"  {e}")
else:
    print("\nAucune erreur.")
