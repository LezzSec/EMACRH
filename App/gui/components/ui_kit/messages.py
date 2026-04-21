# -*- coding: utf-8 -*-
import logging
from PyQt5 import QtWidgets


def show_error_message(parent, title: str, user_message: str, exception: Exception = None):
    """
    Affiche un message d'erreur sécurisé sans exposer les détails techniques.
    Les détails sont loggés pour le débogage.
    """
    logger = logging.getLogger(__name__)
    if exception:
        logger.exception(f"{title}: {user_message} - Details: {exception}")

    QtWidgets.QMessageBox.critical(
        parent,
        title,
        f"{user_message}\n\nSi le probleme persiste, contactez l'administrateur."
    )


def show_warning_message(parent, title: str, user_message: str, exception: Exception = None):
    """
    Affiche un avertissement sécurisé sans exposer les détails techniques.
    """
    logger = logging.getLogger(__name__)
    if exception:
        logger.warning(f"{title}: {user_message} - Details: {exception}")

    QtWidgets.QMessageBox.warning(
        parent,
        title,
        f"{user_message}\n\nSi le probleme persiste, contactez l'administrateur."
    )
