# -*- coding: utf-8 -*-
"""
Package config_tabs — onglets de configuration du panel admin.

Réexporte toutes les classes publiques pour simplifier les imports
depuis admin_data_panel.py.
"""

from .tabs_rh import AteliersTab, ServicesTab, TranchesAgeTab, MotifsortieTab
from .tabs_absences import TypesAbsenceTab, JoursFeriesTab, SoldeCongesTab, DemandeAbsenceTab
from .tabs_production import CompetencesTab, PolyvalenceAdminTab
from .tabs_documents import CategoriesDocsTab, DocumentEventRulesTab
from .tabs_system import RolesTab, HistoriqueAdminTab, LogsConnexionTab
from .tabs_modules import ModulesApplicationTab

__all__ = [
    'AteliersTab', 'ServicesTab', 'TranchesAgeTab', 'MotifsortieTab',
    'TypesAbsenceTab', 'JoursFeriesTab', 'SoldeCongesTab', 'DemandeAbsenceTab',
    'CompetencesTab', 'PolyvalenceAdminTab',
    'CategoriesDocsTab', 'DocumentEventRulesTab',
    'RolesTab', 'HistoriqueAdminTab', 'LogsConnexionTab',
    'ModulesApplicationTab',
]
