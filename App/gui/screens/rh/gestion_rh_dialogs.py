# -*- coding: utf-8 -*-
"""
Shim de ré-export — gestion_rh_dialogs.py

Ce fichier re-exporte toutes les classes depuis les modules domaines/dialogs_*.py
pour conserver la compatibilité avec les imports existants.

Ne pas ajouter de logique ici. Modifier directement les fichiers sources :
  - domaines/dialogs_shared.py       → JustificatifMixin, ConsulterDetailDialog
  - domaines/dialogs_general.py      → EditInfosGeneralesDialog
  - domaines/dialogs_contrat.py      → EditContratDialog
  - domaines/dialogs_declaration.py  → EditDeclarationDialog
  - domaines/dialogs_competences.py  → EditCompetenceDialog
  - domaines/dialogs_formation.py    → EditFormationDialog, GestionDocsFormationDialog,
                                        AjouterDocFormationDialog, ConsulterFormationDialog
  - domaines/dialogs_medical.py      → EditVisiteDialog, EditAccidentDialog
  - domaines/dialogs_vie_salarie.py  → EditSanctionDialog, EditControleAlcoolDialog,
                                        EditTestSalivaireDialog, EditEntretienDialog
  - domaines/dialogs_mutuelle.py     → EditMutuelleDialog
  - domaines/dialogs_documents.py    → AjouterDocumentDialog
"""

from gui.screens.rh.domaines.dialogs_shared import (
    JustificatifMixin,
    ConsulterDetailDialog,
)
from gui.screens.rh.domaines.dialogs_general import EditInfosGeneralesDialog
from gui.screens.rh.domaines.dialogs_contrat import EditContratDialog
from gui.screens.rh.domaines.dialogs_declaration import EditDeclarationDialog
from gui.screens.rh.domaines.dialogs_competences import EditCompetenceDialog
from gui.screens.rh.domaines.dialogs_formation import (
    EditFormationDialog,
    GestionDocsFormationDialog,
    AjouterDocFormationDialog,
    ConsulterFormationDialog,
)
from gui.screens.rh.domaines.dialogs_medical import EditVisiteDialog, EditAccidentDialog, EditValiditeDialog
from gui.screens.rh.domaines.dialogs_vie_salarie import (
    EditSanctionDialog,
    EditControleAlcoolDialog,
    EditTestSalivaireDialog,
    EditEntretienDialog,
)
from gui.screens.rh.domaines.dialogs_mutuelle import EditMutuelleDialog
from gui.screens.rh.domaines.dialogs_documents import AjouterDocumentDialog

__all__ = [
    'JustificatifMixin',
    'ConsulterDetailDialog',
    'EditInfosGeneralesDialog',
    'EditContratDialog',
    'EditDeclarationDialog',
    'EditCompetenceDialog',
    'EditFormationDialog',
    'GestionDocsFormationDialog',
    'AjouterDocFormationDialog',
    'ConsulterFormationDialog',
    'EditVisiteDialog',
    'EditAccidentDialog',
    'EditValiditeDialog',
    'EditSanctionDialog',
    'EditControleAlcoolDialog',
    'EditTestSalivaireDialog',
    'EditEntretienDialog',
    'EditMutuelleDialog',
    'AjouterDocumentDialog',
]
