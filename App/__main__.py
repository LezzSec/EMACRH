# -*- coding: utf-8 -*-
"""
Point d'entrée pour : python -m App <commande>  (depuis EMAC/)

Délègue à core.cli.main().
"""

import os
import sys

# App/ doit être dans sys.path pour que les imports core.* fonctionnent
_app_dir = os.path.dirname(__file__)
if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)

from core.cli import main

if __name__ == "__main__":
    main()
