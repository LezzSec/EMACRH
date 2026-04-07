# -*- coding: utf-8 -*-
"""
Point d'entrée de compatibilité — le code a été déplacé dans rh/.

Conservé uniquement pour ne pas casser les imports existants :
    from gui.screens.rh.gestion_rh import GestionRHDialog

Pour les nouveaux modules, importer directement depuis :
    from gui.screens.rh import GestionRHDialog
"""
from gui.screens.rh import GestionRHDialog  # noqa: F401

__all__ = ["GestionRHDialog"]
