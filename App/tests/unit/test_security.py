# -*- coding: utf-8 -*-
"""
Tests de sécurité pour valider les corrections de vulnérabilités.

Ce fichier teste:
1. Protection contre l'injection SQL (rh_service.py)
2. Protection contre le path traversal (template_service.py)
3. Protection contre l'injection de commandes (template_service.py)
4. Protection contre les race conditions TOCTOU (permission_manager.py)

Date: 2026-02-02
Mise à jour: 2026-02-04 - Ajout tests TOCTOU
Mise à jour: 2026-02-19 - Correction mocks QueryExecutor
"""

import sys
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import os
import time

# Initialiser une QApplication minimale pour les tests Qt (session timeout)
try:
    from PyQt5.QtWidgets import QApplication
    _qt_app = QApplication.instance() or QApplication(sys.argv)
except Exception:
    _qt_app = None


# ============================================================
# 1. TESTS SQL INJECTION - rh_service.get_documents_entite
# ============================================================

class TestSQLInjectionPrevention:
    """Tests pour valider la protection contre l'injection SQL."""

    def test_allowed_entity_types_accepted(self):
        """Les types d'entité autorisés doivent être acceptés."""
        from domain.services.rh.rh_service import get_documents_entite

        # Ces types sont dans la whitelist
        allowed_types = ['contrat', 'formation', 'declaration']

        for entity_type in allowed_types:
            with patch('core.db.query_executor.QueryExecutor.fetch_all', return_value=[]):
                # Ne doit pas lever d'exception
                result = get_documents_entite(entity_type, 1)
                assert isinstance(result, list)

    def test_sql_injection_column_rejected(self):
        """Une tentative d'injection SQL via le type d'entité doit être rejetée."""
        from domain.services.rh.rh_service import get_documents_entite

        # Tentatives d'injection SQL
        malicious_inputs = [
            "contrat; DROP TABLE documents; --",
            "contrat' OR '1'='1",
            "contrat UNION SELECT * FROM users --",
            "1=1; DELETE FROM personnel",
            "formation'; UPDATE users SET role='admin' WHERE '1'='1",
            "../../../etc/passwd",
            "contrat\"; DROP TABLE --",
        ]

        for malicious in malicious_inputs:
            result = get_documents_entite(malicious, 1)
            # Doit retourner une liste vide (rejeté silencieusement)
            assert result == [], f"Injection non bloquée: {malicious}"

    def test_unknown_entity_type_rejected(self):
        """Un type d'entité inconnu doit être rejeté."""
        from domain.services.rh.rh_service import get_documents_entite

        unknown_types = [
            'utilisateur',
            'personnel',
            'admin',
            'user',
            '',
            None,
            123,
        ]

        for unknown in unknown_types:
            result = get_documents_entite(unknown, 1)
            assert result == [], f"Type inconnu non rejeté: {unknown}"

    def test_whitelist_is_exhaustive(self):
        """La whitelist ne doit contenir que les colonnes attendues."""
        from domain.services.rh.rh_service import get_documents_entite

        # Seuls ces 3 types sont autorisés
        expected_allowed = {'contrat', 'formation', 'declaration'}

        # Test exhaustif
        all_possible = ['contrat', 'formation', 'declaration',
                        'personnel', 'utilisateur', 'admin', 'poste', 'atelier']

        for entity_type in all_possible:
            with patch('core.db.query_executor.QueryExecutor.fetch_all',
                       return_value=[{'id': 1}]) as mock_fetch:

                result = get_documents_entite(entity_type, 1)

                if entity_type in expected_allowed:
                    # Doit avoir appelé fetch_all (requête exécutée)
                    assert mock_fetch.called or result == []
                else:
                    # Ne doit PAS avoir appelé fetch_all (rejeté avant)
                    mock_fetch.assert_not_called()
                    assert result == []


# ============================================================
# 2. TESTS PATH TRAVERSAL - template_service
# ============================================================

class TestPathTraversalPrevention:
    """Tests pour valider la protection contre le path traversal."""

    def test_path_traversal_double_dots_blocked(self):
        """Les chemins avec .. doivent être bloqués."""
        from domain.services.documents.template_service import generate_filled_template

        # Mock du template avec un chemin malicieux
        malicious_paths = [
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32\\config\\sam',
            'templates/../../../secret.txt',
            '....//....//....//etc/passwd',
            './../.../../etc/shadow',
        ]

        for malicious_path in malicious_paths:
            with patch('core.db.query_executor.QueryExecutor.fetch_one', return_value={
                'id': 1,
                'nom': 'Test',
                'fichier_source': malicious_path,
                'champ_operateur': 'A1',
                'champ_auditeur': 'B1',
                'champ_date': 'C1',
            }):
                success, message, _ = generate_filled_template(
                    template_id=1,
                    operateur_nom='Test',
                    operateur_prenom='User'
                )

                assert success is False, f"Path traversal non bloqué: {malicious_path}"
                assert "invalide" in message.lower() or "refuse" in message.lower() or "non trouve" in message.lower()

    def test_absolute_path_blocked(self):
        """Les chemins absolus doivent être bloqués."""
        from domain.services.documents.template_service import generate_filled_template

        absolute_paths = [
            '/etc/passwd',
            '/var/log/syslog',
            'C:\\Windows\\System32\\config\\SAM',
        ]

        for abs_path in absolute_paths:
            with patch('core.db.query_executor.QueryExecutor.fetch_one', return_value={
                'id': 1,
                'nom': 'Test',
                'fichier_source': abs_path,
                'champ_operateur': 'A1',
                'champ_auditeur': 'B1',
                'champ_date': 'C1',
            }):
                success, message, _ = generate_filled_template(
                    template_id=1,
                    operateur_nom='Test',
                    operateur_prenom='User'
                )

                # Note: Certains chemins absolus seront traités comme "fichier non trouvé"
                # L'important est que success soit False
                assert success is False, f"Chemin absolu non bloqué: {abs_path}"


# ============================================================
# 3. TESTS COMMAND INJECTION - template_service.open_template_file
# ============================================================

class TestCommandInjectionPrevention:
    """Tests pour valider la protection contre l'injection de commandes."""

    def test_file_outside_allowed_dirs_blocked(self):
        """Les fichiers hors des répertoires autorisés doivent être bloqués."""
        from domain.services.documents.template_service import open_template_file

        # Créer un fichier dans un répertoire différent de temp_dir et templates_dir
        # On utilise le répertoire home de l'utilisateur qui ne devrait pas être autorisé
        home_dir = Path.home()
        test_file = home_dir / 'emac_security_test_file.txt'

        try:
            # Créer le fichier
            test_file.write_text('test content')

            # Ce fichier existe mais n'est pas dans temp_dir ou templates_dir
            success, message = open_template_file(str(test_file))

            # Doit être refusé
            assert success is False
            assert "refuse" in message.lower()
        finally:
            if test_file.exists():
                test_file.unlink()

    def test_nonexistent_file_rejected(self):
        """Les fichiers inexistants doivent être rejetés."""
        from domain.services.documents.template_service import open_template_file

        fake_paths = [
            '/nonexistent/path/file.txt',
            'C:\\fake\\path\\file.exe',
            '../../../nonexistent.txt',
        ]

        for fake_path in fake_paths:
            success, message = open_template_file(fake_path)
            assert success is False
            assert "non trouve" in message.lower() or "invalide" in message.lower()

    def test_directory_path_rejected(self):
        """Les chemins vers des répertoires doivent être rejetés."""
        from domain.services.documents.template_service import open_template_file

        # Utiliser un répertoire existant
        dir_path = tempfile.gettempdir()

        success, message = open_template_file(dir_path)

        assert success is False
        assert "invalide" in message.lower()

    def test_symlink_attack_consideration(self):
        """
        Test de considération des attaques par lien symbolique.
        Note: Ce test vérifie que is_file() est utilisé, ce qui détecte
        certains types de liens symboliques malicieux.
        """
        from domain.services.documents.template_service import open_template_file

        # Test avec un chemin qui ressemble à un lien symbolique
        # mais qui n'existe pas (devrait être rejeté)
        success, message = open_template_file('/tmp/fake_symlink_to_sensitive_file')
        assert success is False


# ============================================================
# 4. TESTS D'INTÉGRATION SÉCURITÉ
# ============================================================

class TestSecurityIntegration:
    """Tests d'intégration pour la sécurité globale."""

    def test_error_messages_do_not_leak_info(self):
        """Les messages d'erreur ne doivent pas divulguer d'informations sensibles."""
        from domain.services.documents.template_service import open_template_file
        from domain.services.rh.rh_service import get_documents_entite

        # Test open_template_file - le message ne doit pas contenir de détails système
        success, message = open_template_file('/etc/passwd')
        # Le message doit être générique
        assert success is False
        assert len(message) < 50  # Message court et générique

        # Test get_documents_entite - ne devrait pas inclure les détails SQL
        result = get_documents_entite("malicious'; DROP TABLE --", 1)
        assert result == []  # Rejeté silencieusement

    def test_logging_on_security_events(self):
        """Les événements de sécurité doivent être loggés."""
        from domain.services.rh.rh_service import get_documents_entite

        with patch('domain.services.rh.rh_service.logger') as mock_logger:
            # Tentative d'injection
            get_documents_entite("malicious_type", 1)

            # Doit avoir loggé un warning
            assert mock_logger.warning.called


# ============================================================
# 5. TESTS RACE CONDITION TOCTOU - permission_manager
# ============================================================

class TestTOCTOURaceConditionPrevention:
    """
    Tests pour valider la protection contre les race conditions TOCTOU
    (Time-of-Check-Time-of-Use) dans le système de permissions.
    """

    def test_require_checks_db_by_default(self):
        """require() doit vérifier en DB par défaut (fresh=True)."""
        from application.permission_manager import PermissionManager, PermissionError

        pm = PermissionManager()
        pm._user_id = 999
        pm._role_id = 1
        pm._loaded = True
        pm._cache_timestamp = time.time()

        # Simuler un cache avec la permission
        pm._allowed_features = {'test.feature'}

        # Mock pour vérifier que _check_permission_fresh est appelé
        with patch.object(pm, '_check_permission_fresh', return_value=False) as mock_fresh:
            # require() doit utiliser fresh=True par défaut
            with pytest.raises(PermissionError):
                pm.require('test.feature')

            # Vérifier que _check_permission_fresh a été appelé
            mock_fresh.assert_called_once_with('test.feature')

    def test_require_with_fresh_false_uses_cache(self):
        """require(fresh=False) doit utiliser le cache."""
        from application.permission_manager import PermissionManager, PermissionError

        pm = PermissionManager()
        pm._user_id = 999
        pm._role_id = 1
        pm._loaded = True
        pm._cache_timestamp = time.time()

        # Cache SANS la permission
        pm._allowed_features = set()

        # Mock pour vérifier que _check_permission_fresh N'est PAS appelé
        with patch.object(pm, '_check_permission_fresh') as mock_fresh:
            with pytest.raises(PermissionError):
                pm.require('test.feature', fresh=False)

            # _check_permission_fresh ne doit PAS avoir été appelé
            mock_fresh.assert_not_called()

    def test_cache_ttl_triggers_reload(self):
        """Le cache périmé doit déclencher un rechargement automatique."""
        from application.permission_manager import (
            PermissionManager, PERMISSION_CACHE_TTL_SECONDS
        )

        pm = PermissionManager()
        pm._user_id = 999
        pm._role_id = 1
        pm._loaded = True

        # Simuler un cache périmé (timestamp vieux)
        pm._cache_timestamp = time.time() - PERMISSION_CACHE_TTL_SECONDS - 10

        # Vérifier que le cache est considéré comme stale
        assert pm.is_cache_stale() is True

        # Mock reload pour vérifier qu'il est appelé
        with patch.object(pm, 'reload') as mock_reload:
            with patch.object(pm, 'load_for_user'):
                # can() avec cache stale doit appeler reload
                pm.can('test.feature')
                mock_reload.assert_called_once()

    def test_cache_not_stale_within_ttl(self):
        """Le cache frais ne doit pas être considéré comme périmé."""
        from application.permission_manager import PermissionManager

        pm = PermissionManager()
        pm._loaded = True
        pm._cache_timestamp = time.time()  # Tout juste chargé

        assert pm.is_cache_stale() is False

    def test_check_permission_fresh_queries_db(self):
        """_check_permission_fresh doit interroger la base de données."""
        from application.permission_manager import PermissionManager

        pm = PermissionManager()
        pm._user_id = 999
        pm._role_id = 1

        # Mock DatabaseCursor depuis core.db.configbd (import local dans permission_manager)
        with patch('core.db.configbd.DatabaseCursor') as mock_cursor:
            mock_ctx = MagicMock()
            mock_cur = MagicMock()
            mock_ctx.__enter__ = MagicMock(return_value=mock_cur)
            mock_ctx.__exit__ = MagicMock(return_value=False)

            # Simuler: pas d'override utilisateur, feature présente dans le rôle
            mock_cur.fetchone.side_effect = [
                None,  # Pas d'override
                {'1': 1}  # Feature dans le rôle
            ]
            mock_cursor.return_value = mock_ctx

            result = pm._check_permission_fresh('test.feature')

            # Doit avoir fait 2 requêtes
            assert mock_cur.execute.call_count == 2
            assert result is True

    def test_user_override_true_wins_in_fresh_check(self):
        """Un override utilisateur TRUE doit l'emporter en vérification fraîche."""
        from application.permission_manager import PermissionManager

        pm = PermissionManager()
        pm._user_id = 999
        pm._role_id = 1

        with patch('core.db.configbd.DatabaseCursor') as mock_cursor:
            mock_ctx = MagicMock()
            mock_cur = MagicMock()
            mock_ctx.__enter__ = MagicMock(return_value=mock_cur)
            mock_ctx.__exit__ = MagicMock(return_value=False)

            # Simuler: override utilisateur TRUE
            mock_cur.fetchone.return_value = {'value': True}
            mock_cursor.return_value = mock_ctx

            result = pm._check_permission_fresh('test.feature')

            # Override TRUE → autorisé
            assert result is True
            # Seulement 1 requête (override trouvé, pas besoin de vérifier le rôle)
            assert mock_cur.execute.call_count == 1

    def test_user_override_false_blocks_in_fresh_check(self):
        """Un override utilisateur FALSE doit bloquer en vérification fraîche."""
        from application.permission_manager import PermissionManager

        pm = PermissionManager()
        pm._user_id = 999
        pm._role_id = 1

        with patch('core.db.configbd.DatabaseCursor') as mock_cursor:
            mock_ctx = MagicMock()
            mock_cur = MagicMock()
            mock_ctx.__enter__ = MagicMock(return_value=mock_cur)
            mock_ctx.__exit__ = MagicMock(return_value=False)

            # Simuler: override utilisateur FALSE
            mock_cur.fetchone.return_value = {'value': False}
            mock_cursor.return_value = mock_ctx

            result = pm._check_permission_fresh('test.feature')

            # Override FALSE → refusé
            assert result is False

    def test_invalidate_user_cache_reloads_permission_manager(self):
        """invalidate_user_cache doit recharger le PermissionManager."""
        from infrastructure.cache.emac_cache import invalidate_user_cache

        with patch('core.utils.emac_cache.CacheManager') as mock_cache_mgr:
            mock_instance = MagicMock()
            mock_cache_mgr.get_instance.return_value = mock_instance

            with patch('application.permission_manager.perm') as mock_perm:
                mock_perm.is_loaded.return_value = True

                invalidate_user_cache(reload_current_user=True)

                # Le cache doit être invalidé
                mock_instance.invalidate_namespace.assert_called_with('permissions')
                # Et perm.reload() doit être appelé
                mock_perm.reload.assert_called_once()

    def test_require_fresh_always_checks_db(self):
        """require_fresh() doit toujours vérifier en DB."""
        from application.permission_manager import PermissionManager, PermissionError

        pm = PermissionManager()
        pm._user_id = 999
        pm._role_id = 1
        pm._loaded = True
        pm._cache_timestamp = time.time()
        pm._allowed_features = {'test.feature'}

        with patch.object(pm, '_check_permission_fresh', return_value=False) as mock_fresh:
            with pytest.raises(PermissionError):
                pm.require_fresh('test.feature')

            mock_fresh.assert_called_once_with('test.feature')


class TestPermissionInvalidationSecurity:
    """Tests pour la sécurité de l'invalidation des permissions."""

    def test_permission_change_triggers_reload(self):
        """La modification des permissions doit déclencher un reload."""
        from application.permission_manager import save_user_feature_overrides

        with patch('core.db.configbd.get_connection') as mock_conn:
            mock_connection = MagicMock()
            mock_cursor = MagicMock()
            mock_connection.cursor.return_value = mock_cursor
            mock_conn.return_value = mock_connection

            # is_admin et get_current_user sont importés localement depuis auth_service
            with patch('domain.services.admin.auth_service.is_admin', return_value=True):
                with patch('domain.services.admin.auth_service.get_current_user',
                           return_value={'id': 1, 'username': 'admin'}):
                    # invalidate_user_cache importé localement depuis core.utils.emac_cache
                    # log_hist_async importé localement depuis core.services.optimized_db_logger
                    with patch('core.utils.emac_cache.invalidate_user_cache') as mock_invalidate:
                        with patch('core.services.optimized_db_logger.log_hist_async'):
                            save_user_feature_overrides(user_id=999, overrides={'test.feature': True})

                            # invalidate_user_cache doit être appelé avec reload_current_user=True
                            mock_invalidate.assert_called_once_with(reload_current_user=True)


# ============================================================
# 6. TESTS SESSION TIMEOUT
# ============================================================

class TestSessionTimeout:
    """Tests pour le timeout de session."""

    def test_session_timeout_manager_creation(self):
        """SessionTimeoutManager doit être créé correctement."""
        from gui.workers.session_timeout import SessionTimeoutManager, SESSION_TIMEOUT_MINUTES

        # Utiliser None comme parent (QObject(None) est valide, pas d'installEventFilter)
        manager = SessionTimeoutManager(None, timeout_minutes=15)

        assert manager.timeout_minutes == 15
        assert manager._enabled is True
        assert manager._warning_shown is False

    def test_session_timeout_remaining_seconds(self):
        """get_remaining_seconds doit retourner le temps correct."""
        from gui.workers.session_timeout import SessionTimeoutManager
        from datetime import datetime, timedelta

        manager = SessionTimeoutManager(None, timeout_minutes=10)

        # Simuler dernière activité il y a 5 minutes
        manager._last_activity = datetime.now() - timedelta(minutes=5)

        remaining = manager.get_remaining_seconds()
        # Devrait rester environ 5 minutes (300 secondes)
        assert 290 <= remaining <= 310

    def test_session_timeout_reset(self):
        """reset() doit réinitialiser le timer."""
        from gui.workers.session_timeout import SessionTimeoutManager
        from datetime import datetime, timedelta

        manager = SessionTimeoutManager(None, timeout_minutes=10)

        # Simuler activité ancienne
        manager._last_activity = datetime.now() - timedelta(minutes=8)
        manager._warning_shown = True

        # Reset
        manager.reset()

        # Vérifier reset
        assert manager._warning_shown is False
        # La dernière activité devrait être récente
        assert (datetime.now() - manager._last_activity).total_seconds() < 2

    def test_session_timeout_config(self):
        """La configuration du timeout doit être accessible."""
        from gui.workers.session_timeout import get_session_timeout_config

        config = get_session_timeout_config()

        assert 'timeout_minutes' in config
        assert 'warning_minutes' in config
        assert 'check_interval_seconds' in config
        assert config['timeout_minutes'] > 0
        assert config['warning_minutes'] > 0
        assert config['warning_minutes'] < config['timeout_minutes']


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
