# -*- coding: utf-8 -*-
"""
Permet d'invoquer la CLI avec : python -m cli <commande>
"""

import os
import sys

# Garantit que App/ est dans sys.path quel que soit le répertoire de lancement
_app_dir = os.path.dirname(os.path.dirname(__file__))
if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)

from cli import main

if __name__ == "__main__":
    main()
