# -*- coding: utf-8 -*-
"""
Configuration des tests et fixtures partagées pour pytest
"""

import os
import sys
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

import pytest

# Ajouter le répertoire App au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =============================================================================
# CONFIGURATION PYTEST
# =============================================================================

def pytest_configure(config):
    """Enregistrement des markers personnalisés"""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (deselect with '-m \"not integration\"')"
    )


# =============================================================================
# FIXTURES : MOCK BASE DE DONNÉES
# =============================================================================

@pytest.fixture
def mock_db_connection():
    """Mock de la connexion à la base de données"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn, mock_cursor


@pytest.fixture
def mock_get_connection(mock_db_connection):
    """Patch get_connection pour retourner un mock"""
    mock_conn, mock_cursor = mock_db_connection
    with patch('core.db.configbd.get_connection', return_value=mock_conn):
        yield mock_conn, mock_cursor


@pytest.fixture
def mock_database_cursor():
    """Mock du context manager DatabaseCursor"""
    mock_cursor = MagicMock()

    class MockDatabaseCursor:
        def __init__(self, dictionary=False):
            self.dictionary = dictionary

        def __enter__(self):
            return mock_cursor

        def __exit__(self, *args):
            pass

    return MockDatabaseCursor, mock_cursor


@pytest.fixture
def mock_database_connection():
    """Mock du context manager DatabaseConnection"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    class MockDatabaseConnection:
        def __enter__(self):
            return mock_conn

        def __exit__(self, *args):
            pass

    return MockDatabaseConnection, mock_conn, mock_cursor


# =============================================================================
# FIXTURES : DONNÉES DE TEST
# =============================================================================

@pytest.fixture
def sample_user():
    """Utilisateur de test"""
    return {
        'id': 1,
        'username': 'testuser',
        'nom': 'Dupont',
        'prenom': 'Jean',
        'role_id': 1,
        'role_nom': 'admin',
        'actif': True,
        'password_hash': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X7v8m7OOOz6OO.OOO'  # hash de "Test1234!"
    }


@pytest.fixture
def sample_operator():
    """Opérateur de test"""
    return {
        'id': 1,
        'nom': 'Martin',
        'prenom': 'Pierre',
        'matricule': 'OP001',
        'statut': 'ACTIF'
    }


@pytest.fixture
def sample_poste():
    """Poste de test"""
    return {
        'id': 1,
        'poste_code': '0506',
        'atelier_id': 1,
        'nom_atelier': 'Atelier Principal'
    }


@pytest.fixture
def sample_polyvalence():
    """Enregistrement polyvalence de test"""
    return {
        'id': 1,
        'operateur_id': 1,
        'poste_id': 1,
        'niveau': 2,
        'date_evaluation': date.today() - timedelta(days=30),
        'prochaine_evaluation': date.today() + timedelta(days=335)
    }


@pytest.fixture
def sample_contract():
    """Contrat de test"""
    return {
        'id': 1,
        'operateur_id': 1,
        'type_contrat': 'CDI',
        'date_debut': date.today() - timedelta(days=365),
        'date_fin': None,
        'etp': 1.0,
        'actif': 1
    }


@pytest.fixture
def sample_contract_cdd():
    """Contrat CDD de test (avec date de fin)"""
    return {
        'id': 2,
        'operateur_id': 2,
        'type_contrat': 'CDD',
        'date_debut': date.today() - timedelta(days=30),
        'date_fin': date.today() + timedelta(days=60),
        'etp': 1.0,
        'actif': 1
    }


@pytest.fixture
def sample_absence_request():
    """Demande d'absence de test"""
    return {
        'id': 1,
        'personnel_id': 1,
        'type_absence_id': 1,
        'type_code': 'CP',
        'date_debut': date.today() + timedelta(days=7),
        'date_fin': date.today() + timedelta(days=14),
        'nb_jours': 5,
        'statut': 'EN_ATTENTE'
    }


@pytest.fixture
def sample_evaluation_overdue():
    """Évaluation en retard de test"""
    return {
        'polyvalence_id': 1,
        'operateur_id': 1,
        'nom': 'Martin',
        'prenom': 'Pierre',
        'matricule': 'OP001',
        'poste_id': 1,
        'poste_code': '0506',
        'nom_atelier': 'Atelier Principal',
        'niveau': 2,
        'date_evaluation': date.today() - timedelta(days=400),
        'prochaine_evaluation': date.today() - timedelta(days=35),
        'jours_retard': 35
    }


@pytest.fixture
def sample_evaluation_upcoming():
    """Évaluation à venir de test"""
    return {
        'polyvalence_id': 2,
        'operateur_id': 2,
        'nom': 'Durand',
        'prenom': 'Marie',
        'matricule': 'OP002',
        'poste_id': 2,
        'poste_code': '0830',
        'nom_atelier': 'Atelier Secondaire',
        'niveau': 3,
        'date_evaluation': date.today() - timedelta(days=335),
        'prochaine_evaluation': date.today() + timedelta(days=15),
        'jours_restants': 15
    }


# =============================================================================
# FIXTURES : SESSION UTILISATEUR
# =============================================================================

@pytest.fixture
def mock_user_session():
    """Mock de la session utilisateur"""
    with patch('core.services.auth_service.UserSession') as mock_session:
        mock_session.get_user.return_value = {
            'id': 1,
            'username': 'admin',
            'nom': 'Admin',
            'prenom': 'Test',
            'role_id': 1,
            'role_nom': 'admin'
        }
        mock_session.get_permissions.return_value = {
            'contrats': {'lecture': True, 'ecriture': True, 'suppression': True},
            'personnel': {'lecture': True, 'ecriture': True, 'suppression': True},
            'evaluations': {'lecture': True, 'ecriture': True, 'suppression': True}
        }
        mock_session.is_authenticated.return_value = True
        yield mock_session


@pytest.fixture
def mock_non_admin_session():
    """Mock de session utilisateur non-admin"""
    with patch('core.services.auth_service.UserSession') as mock_session:
        mock_session.get_user.return_value = {
            'id': 2,
            'username': 'user',
            'nom': 'User',
            'prenom': 'Test',
            'role_id': 2,
            'role_nom': 'lecteur'
        }
        mock_session.get_permissions.return_value = {
            'contrats': {'lecture': True, 'ecriture': False, 'suppression': False},
            'personnel': {'lecture': True, 'ecriture': False, 'suppression': False}
        }
        mock_session.is_authenticated.return_value = True
        yield mock_session


# =============================================================================
# FIXTURES : PERMISSION MANAGER
# =============================================================================

# Liste des modules qui importent 'require' et doivent être mockés
_MODULES_WITH_REQUIRE = [
    'core.services.permission_manager',
    'core.services.contrat_service_crud',
    'core.services.absence_service',
    'core.services.evaluation_service',
    'core.services.rh_service',
    'core.services.medical_service',
    'core.services.bulk_service',
]


@pytest.fixture(autouse=True)
def reset_and_mock_permissions():
    """
    Reset automatique du PermissionManager et mock de require() avant chaque test.

    Ceci permet aux tests unitaires de s'exécuter sans avoir à se soucier des
    vérifications de permissions. Pour tester spécifiquement les permissions,
    utilisez le fixture 'enforce_permissions'.
    """
    from contextlib import ExitStack
    from core.services.permission_manager import PermissionManager

    # Reset le singleton
    PermissionManager.reset()

    # Mock require() dans tous les modules qui l'importent
    with ExitStack() as stack:
        mock_require = MagicMock()  # Ne fait rien par défaut

        for module_path in _MODULES_WITH_REQUIRE:
            try:
                stack.enter_context(patch(f'{module_path}.require', mock_require))
            except AttributeError:
                # Le module n'a pas 'require' (peut-être pas encore importé)
                pass

        yield mock_require

    # Cleanup
    PermissionManager.reset()


@pytest.fixture
def enforce_permissions():
    """
    Fixture pour tester les vérifications de permissions.
    Utiliser ce fixture APRÈS un test normal pour faire des tests de permissions.

    Note: Les tests avec ce fixture doivent charger les permissions manuellement
    via PermissionManager.load_for_user() ou mocker can()/require() spécifiquement.

    Usage:
        def test_permission_denied(enforce_permissions):
            from core.services.permission_manager import PermissionManager, PermissionError
            PermissionManager.reset()  # Assure que les permissions ne sont pas chargées
            with pytest.raises(PermissionError):
                # Cette fonction devrait lever PermissionError
                some_protected_function()
    """
    from core.services.permission_manager import PermissionManager
    PermissionManager.reset()
    yield
    PermissionManager.reset()


@pytest.fixture
def mock_permission_manager():
    """Mock du PermissionManager pour simuler des permissions features"""
    with patch('core.services.permission_manager.perm') as mock_perm:
        mock_perm.is_loaded.return_value = False  # Par défaut, fallback vers l'ancien système
        mock_perm.can.return_value = False
        yield mock_perm


# =============================================================================
# FIXTURES : LOGGING
# =============================================================================

@pytest.fixture
def mock_log_hist():
    """Mock de la fonction log_hist"""
    with patch('core.services.logger.log_hist') as mock:
        yield mock


@pytest.fixture
def mock_log_hist_async():
    """Mock de la fonction log_hist_async"""
    with patch('core.services.optimized_db_logger.log_hist_async') as mock:
        yield mock


# =============================================================================
# HELPERS
# =============================================================================

def create_mock_fetchall(data):
    """Helper pour créer un mock fetchall avec des données"""
    mock = MagicMock()
    mock.fetchall.return_value = data
    return mock


def create_mock_fetchone(data):
    """Helper pour créer un mock fetchone avec des données"""
    mock = MagicMock()
    mock.fetchone.return_value = data
    return mock
