# -*- coding: utf-8 -*-
"""
Package bulk_tabs — onglets et dialogs pour les opérations en masse.
"""

from .formation_bulk_tab import FormationBulkTab
from .absence_bulk_tab import AbsenceBulkTab
from .medical_bulk_tab import MedicalBulkTab
from .competence_bulk_tab import CompetenceBulkTab
from .progress_dialog import BulkOperationProgressDialog
from .results_dialog import BulkOperationResultsDialog

__all__ = [
    'FormationBulkTab', 'AbsenceBulkTab', 'MedicalBulkTab', 'CompetenceBulkTab',
    'BulkOperationProgressDialog', 'BulkOperationResultsDialog',
]
