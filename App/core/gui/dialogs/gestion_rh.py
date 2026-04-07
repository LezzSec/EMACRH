# -*- coding: utf-8 -*-
"""
Point d'entrée de compatibilité — le code a été déplacé dans rh/.

Conservé uniquement pour ne pas casser les imports existants :
    from core.gui.dialogs.gestion_rh import GestionRHDialog

Pour les nouveaux modules, importer directement depuis :
    from core.gui.dialogs.rh import GestionRHDialog
"""
from core.gui.dialogs.rh import GestionRHDialog  # noqa: F401

__all__ = ["GestionRHDialog"]
