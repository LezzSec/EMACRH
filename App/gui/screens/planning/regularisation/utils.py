# -*- coding: utf-8 -*-


_TYPE_LABELS = {
    'CongePaye': 'Congé Payé',
    'RTT': 'RTT',
    'SansSolde': 'Sans Solde',
    'Maladie': 'Maladie',
    'AccidentTravail': 'Accident Travail',
    'AccidentTrajet': 'Accident Trajet',
    'ArretTravail': 'Arrêt Travail',
    'CongeNaissance': 'Congé Naissance',
    'Formation': 'Formation',
    'Autorisation': 'Autorisation',
    'Autre': 'Autre',
}

_TYPE_COLORS = {
    'CongePaye': '#10b981',
    'RTT': '#3b82f6',
    'SansSolde': '#6b7280',
    'Maladie': '#8b5cf6',
    'AccidentTravail': '#dc2626',
    'AccidentTrajet': '#dc2626',
    'ArretTravail': '#f59e0b',
    'CongeNaissance': '#ec4899',
    'Formation': '#06b6d4',
    'Autorisation': '#14b8a6',
    'Autre': '#64748b',
}


def format_type_declaration(type_decl: str) -> str:
    return _TYPE_LABELS.get(type_decl, type_decl)


def get_type_color(type_decl: str) -> str:
    return _TYPE_COLORS.get(type_decl, '#6b7280')
