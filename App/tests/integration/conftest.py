# -*- coding: utf-8 -*-
"""
Configuration pytest locale pour les tests d'intégration.

Override du fixture autouse global reset_and_mock_permissions :
les tests d'intégration travaillent avec la DB réelle et ne doivent
pas avoir leurs permissions mockées.
"""
import pytest


@pytest.fixture(autouse=True)
def reset_and_mock_permissions():
    """
    Override du fixture global : ne pas mocker les permissions pour
    les tests d'intégration (on teste contre la DB réelle).
    """
    yield
