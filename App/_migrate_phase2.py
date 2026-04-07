# -*- coding: utf-8 -*-
"""Migration Phase 2: update imports after moving domain layer files."""

import os
import sys
from pathlib import Path

APP_DIR = Path(__file__).parent
SCRIPT_NAME = Path(__file__).name

replacements = [
    # interfaces
    ("from core.interfaces.", "from domain.interfaces."),
    ("import core.interfaces.", "import domain.interfaces."),

    # repositories
    ("from core.repositories.", "from domain.repositories."),
    ("import core.repositories.", "import domain.repositories."),

    # models
    ("from core.models import", "from domain.models import"),
    ("import core.models", "import domain.models"),

    # services rh
    ("from core.services.rh_service import", "from domain.services.rh.rh_service import"),
    ("from core.services.medical_service import", "from domain.services.rh.medical_service import"),
    ("from core.services.vie_salarie_service import", "from domain.services.rh.vie_salarie_service import"),
    ("from core.services.mutuelle_service import", "from domain.services.rh.mutuelle_service import"),
    ("from core.services.declaration_service_crud import", "from domain.services.rh.declaration_service_crud import"),
    ("from core.services.competences_service import", "from domain.services.rh.competences_service import"),

    # services personnel
    ("from core.services.personnel_service import", "from domain.services.personnel.personnel_service import"),
    ("from core.services.matricule_service import", "from domain.services.personnel.matricule_service import"),
    ("from core.services.bulk_service import", "from domain.services.personnel.bulk_service import"),

    # services formation
    ("from core.services.formation_service_crud import", "from domain.services.formation.formation_service_crud import"),
    ("from core.services.formation_export_service import", "from domain.services.formation.formation_export_service import"),
    ("from core.services.grilles_service import", "from domain.services.formation.grilles_service import"),
    ("from core.services.evaluation_service import", "from domain.services.formation.evaluation_service import"),

    # services planning
    ("from core.services.planning_service import", "from domain.services.planning.planning_service import"),
    ("from core.services.absence_service_crud import", "from domain.services.planning.absence_service_crud import"),
    ("from core.services.calendrier_service import", "from domain.services.planning.calendrier_service import"),

    # services documents
    ("from core.services.document_service import", "from domain.services.documents.document_service import"),
    ("from core.services.template_service import", "from domain.services.documents.template_service import"),
    ("from core.services.polyvalence_docs_service import", "from domain.services.documents.polyvalence_docs_service import"),

    # services admin
    ("from core.services.auth_service import", "from domain.services.admin.auth_service import"),
    ("from core.services.config_service import", "from domain.services.admin.config_service import"),
    ("from core.services.alert_service import", "from domain.services.admin.alert_service import"),
    ("from core.services.historique_service import", "from domain.services.admin.historique_service import"),
    ("from core.services.polyvalence_logger import", "from domain.services.admin.polyvalence_logger import"),
]


def migrate_file(file_path: Path) -> int:
    if file_path.name == SCRIPT_NAME:
        return 0

    try:
        content = file_path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, PermissionError):
        return 0

    original = content
    for old, new in replacements:
        content = content.replace(old, new)

    if content != original:
        file_path.write_text(content, encoding="utf-8")
        return 1
    return 0


def main():
    updated = 0
    files_checked = 0

    for py_file in APP_DIR.rglob("*.py"):
        # Skip __pycache__
        if "__pycache__" in py_file.parts:
            continue
        files_checked += 1
        updated += migrate_file(py_file)

    print(f"Checked {files_checked} files, updated {updated} files.")


if __name__ == "__main__":
    main()
