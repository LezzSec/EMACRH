# -*- coding: utf-8 -*-
"""
Utilitaires de formatage de dates pour l'affichage (format français DD/MM/YYYY).

Usage:
    from core.utils.date_format import format_date, format_datetime

    label.setText(format_date(some_date))       # "17/03/2026"
    label.setText(format_datetime(some_dt))     # "17/03/2026 14:30:00"
"""

from datetime import date, datetime
from typing import Union, Optional


def format_date(d: Optional[Union[date, datetime, str]], default: str = "") -> str:
    """
    Formate une date en DD/MM/YYYY (format français).

    Args:
        d: date, datetime, ou None
        default: valeur retournée si d est None ou invalide

    Returns:
        Chaîne DD/MM/YYYY ou default
    """
    if d is None:
        return default
    if isinstance(d, str):
        return d  # Déjà formatée ou format inconnu, on ne touche pas
    try:
        return d.strftime('%d/%m/%Y')
    except Exception:
        return default


def format_datetime(dt: Optional[Union[datetime, date]], default: str = "") -> str:
    """
    Formate une datetime en DD/MM/YYYY HH:MM:SS (format français).

    Args:
        dt: datetime ou None
        default: valeur retournée si dt est None ou invalide

    Returns:
        Chaîne DD/MM/YYYY HH:MM:SS ou default
    """
    if dt is None:
        return default
    try:
        if isinstance(dt, datetime):
            return dt.strftime('%d/%m/%Y %H:%M:%S')
        return dt.strftime('%d/%m/%Y')
    except Exception:
        return default


def format_date_short(d: Optional[Union[date, datetime]], default: str = "") -> str:
    """Formate en DD/MM/YY (format court)."""
    if d is None:
        return default
    try:
        return d.strftime('%d/%m/%y')
    except Exception:
        return default


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """
    Formate en YYYYMMDD_HHMMSS (pour noms de fichiers et identifiants).

    Args:
        dt: datetime ou None (par défaut: maintenant)

    Returns:
        Chaîne YYYYMMDD_HHMMSS
    """
    if dt is None:
        dt = datetime.now()
    try:
        return dt.strftime('%Y%m%d_%H%M%S')
    except Exception:
        return datetime.now().strftime('%Y%m%d_%H%M%S')
