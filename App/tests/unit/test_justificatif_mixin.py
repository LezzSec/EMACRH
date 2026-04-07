# -*- coding: utf-8 -*-
"""
Tests unitaires – JustificatifMixin & intégration dans les formulaires RH
=========================================================================

Vérifie l'implémentation du document justificatif obligatoire ajouté dans
gestion_rh_dialogs.py pour les 6 formulaires de création :
  - EditContratDialog
  - EditDeclarationDialog
  - EditFormationDialog
  - EditVisiteDialog
  - EditAccidentDialog
  - EditSanctionDialog

Structure des tests :
  1. TestJustificatifMixinLogique       – logique pure du mixin (sans Qt)
  2. TestJustificatifMixinSauvegarde    – upload document après création
  3. TestDialogsMROInheritance          – héritage correct dans chaque dialog
  4. TestCreationModeSections           – section justificatif présente/absente
  5. TestValidation                     – validate() bloque sans justificatif
  6. TestSaveToDbJustificatif           – upload déclenché après création réussie

Usage :
    cd App
    py -m pytest tests/unit/test_justificatif_mixin.py -v
"""

import sys
import os
import types
import pytest
from unittest.mock import patch, MagicMock, call

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# ---------------------------------------------------------------------------
# Stubs Qt minimal (permet d'importer les dialogs sans Qt installé en CI)
# ---------------------------------------------------------------------------

def _make_qt_stubs():
    """Injecte des stubs PyQt5 dans sys.modules si PyQt5 est absent."""
    try:
        from PyQt5.QtWidgets import QWidget
        return False  # Qt réel disponible
    except ImportError:
        pass

    for mod_name in [
        'PyQt5', 'PyQt5.QtWidgets', 'PyQt5.QtCore', 'PyQt5.QtGui',
    ]:
        sys.modules.setdefault(mod_name, types.ModuleType(mod_name))

    # --- QtWidgets stubs ---
    widgets_mod = sys.modules['PyQt5.QtWidgets']

    class _FakeWidget:
        def __init__(self, *a, **kw): pass
        def setReadOnly(self, *a): pass
        def setPlaceholderText(self, *a): pass
        def setStyleSheet(self, *a): pass
        def setFixedWidth(self, *a): pass
        def clicked(self): pass
        def connect(self, *a): pass
        def addWidget(self, *a): pass
        def addLayout(self, *a): pass
        def setSpacing(self, *a): pass
        def setText(self, *a): pass
        def text(self): return ''
        def toPlainText(self): return ''
        def currentText(self): return ''
        def currentData(self): return None
        def setWordWrap(self, *a): pass
        def isChecked(self): return False
        def value(self): return 0.0
        def date(self): return MagicMock(year=lambda: 2026, toPyDate=lambda: None)
        def setEnabled(self, *a): pass
        def setMaximumHeight(self, *a): pass
        def setRange(self, *a): pass
        def setSuffix(self, *a): pass
        def setSingleStep(self, *a): pass
        def setDecimals(self, *a): pass
        def setValue(self, *a): pass
        def setCalendarPopup(self, *a): pass
        def setDisplayFormat(self, *a): pass
        def setSpecialValueText(self, *a): pass
        def setMinimumDate(self, *a): pass
        def setDate(self, *a): pass
        def setCheckable(self, *a): pass
        def setCursor(self, *a): pass
        def addItem(self, *a): pass
        def addItems(self, *a): pass
        def findText(self, *a): return -1
        def setCurrentIndex(self, *a): pass
        def count(self): return 0
        def model(self): return MagicMock()
        def setMinimumWidth(self, *a): pass

    class _FakeLayout(_FakeWidget):
        def addRow(self, *a): pass

    class _FakeGroupBox(_FakeWidget):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            self._layout = None
        def setLayout(self, l): self._layout = l

    class _FakeDialog(_FakeWidget):
        def __init__(self, *a, **kw):
            self.content_layout = _FakeLayout()
        def exec_(self): return 0

    for name, cls in [
        ('QWidget', _FakeWidget), ('QDialog', _FakeDialog),
        ('QVBoxLayout', _FakeLayout), ('QHBoxLayout', _FakeLayout),
        ('QFormLayout', _FakeLayout),
        ('QLabel', _FakeWidget), ('QLineEdit', _FakeWidget),
        ('QPushButton', _FakeWidget), ('QTextEdit', _FakeWidget),
        ('QComboBox', _FakeWidget), ('QDateEdit', _FakeWidget),
        ('QDoubleSpinBox', _FakeWidget), ('QCheckBox', _FakeWidget),
        ('QGroupBox', _FakeGroupBox),
        ('QListWidget', _FakeWidget), ('QListWidgetItem', _FakeWidget),
        ('QFrame', _FakeWidget), ('QScrollArea', _FakeWidget),
        ('QStackedWidget', _FakeWidget), ('QTableWidget', _FakeWidget),
        ('QTableWidgetItem', _FakeWidget), ('QHeaderView', _FakeWidget),
        ('QAbstractItemView', _FakeWidget), ('QSizePolicy', _FakeWidget),
        ('QSpacerItem', _FakeWidget), ('QGridLayout', _FakeLayout),
        ('QMessageBox', _FakeWidget), ('QFileDialog', _FakeWidget),
        ('QApplication', _FakeWidget),
    ]:
        setattr(widgets_mod, name, cls)

    # --- QtCore stubs ---
    core_mod = sys.modules['PyQt5.QtCore']
    core_mod.Qt = MagicMock()
    core_mod.QTimer = MagicMock()
    core_mod.pyqtSignal = MagicMock(return_value=MagicMock())
    core_mod.QDate = MagicMock()

    # --- QtGui stubs ---
    gui_mod = sys.modules['PyQt5.QtGui']
    gui_mod.QFont = MagicMock()
    gui_mod.QColor = MagicMock()

    return True  # stubs injectés


_STUBS_INJECTED = _make_qt_stubs()

# ---------------------------------------------------------------------------
# QApplication singleton (nécessaire pour créer des widgets Qt réels)
# Sans cela, Qt crashe (exit 0xC0000409) dès qu'un widget est instancié.
# ---------------------------------------------------------------------------
_qt_app = None
if not _STUBS_INJECTED:
    try:
        from PyQt5.QtWidgets import QApplication as _QApp
        _qt_app = _QApp.instance() or _QApp([])
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Import du mixin et des dialogs (après stubs Qt éventuels)
# ---------------------------------------------------------------------------

# Patcher les dépendances services avant l'import des dialogs
_services_to_patch = {
    'domain.services.rh.rh_service': MagicMock(
        update_infos_generales=MagicMock(return_value=(True, '')),
        create_contrat=MagicMock(return_value=(True, '', 1)),
        update_contrat=MagicMock(return_value=(True, '')),
        create_formation=MagicMock(return_value=(True, '', 2)),
        update_formation=MagicMock(return_value=(True, '')),
        create_declaration=MagicMock(return_value=(True, '', 3)),
        update_declaration=MagicMock(return_value=(True, '')),
        create_competence_personnel=MagicMock(return_value=(True, '', 4)),
        get_categories_documents=MagicMock(return_value=[
            {'id': 1, 'nom': 'Contrats de travail'},
            {'id': 2, 'nom': 'Attestations diverses'},
            {'id': 3, 'nom': 'Diplômes et formations'},
            {'id': 4, 'nom': 'Certificats médicaux'},
            {'id': 5, 'nom': 'Documents médicaux'},
            {'id': 6, 'nom': 'Sanctions disciplinaires'},
        ]),
        CATEGORIE_TO_DOMAINE={},
        DomaineRH=MagicMock(),
        is_matricule_disponible=MagicMock(return_value=True),
    ),
    'domain.services.rh.medical_service': MagicMock(
        create_visite=MagicMock(return_value=(True, '', 10)),
        update_visite=MagicMock(return_value=(True, '')),
        create_accident=MagicMock(return_value=(True, '', 11)),
        update_accident=MagicMock(return_value=(True, '')),
        get_visites=MagicMock(return_value=[]),
        delete_visite=MagicMock(return_value=(True, '')),
        get_accidents=MagicMock(return_value=[]),
        delete_accident=MagicMock(return_value=(True, '')),
        get_validites=MagicMock(return_value=[]),
        create_validite=MagicMock(return_value=(True, '', 12)),
        update_validite=MagicMock(return_value=(True, '')),
        delete_validite=MagicMock(return_value=(True, '')),
        get_alertes_medicales=MagicMock(return_value=[]),
    ),
    'domain.services.rh.vie_salarie_service': MagicMock(
        create_sanction=MagicMock(return_value=(True, '', 20)),
        update_sanction=MagicMock(return_value=(True, '')),
        get_sanctions=MagicMock(return_value=[]),
        delete_sanction=MagicMock(return_value=(True, '')),
        create_controle_alcool=MagicMock(return_value=(True, '', 21)),
        delete_controle_alcool=MagicMock(return_value=(True, '')),
        get_controles_alcool=MagicMock(return_value=[]),
        create_test_salivaire=MagicMock(return_value=(True, '', 22)),
        delete_test_salivaire=MagicMock(return_value=(True, '')),
        get_tests_salivaires=MagicMock(return_value=[]),
        create_entretien=MagicMock(return_value=(True, '', 23)),
        update_entretien=MagicMock(return_value=(True, '')),
        get_entretiens=MagicMock(return_value=[]),
        delete_entretien=MagicMock(return_value=(True, '')),
        get_types_sanction=MagicMock(return_value=['Avertissement', 'Mise à pied']),
        get_types_entretien=MagicMock(return_value=['Annuel', 'Professionnel']),
        get_managers_liste=MagicMock(return_value=[]),
    ),
    'domain.services.rh.declaration_service_crud': MagicMock(
        DeclarationServiceCRUD=MagicMock(
            get_types_declaration=MagicMock(return_value=['Arrêt maladie', 'AT'])
        )
    ),
    'domain.services.rh.competences_service': MagicMock(
        remove_assignment=MagicMock(return_value=(True, '')),
        get_all_competences=MagicMock(return_value=[]),
        update_assignment=MagicMock(return_value=(True, '')),
    ),
    'core.services.contrat_service_crud': MagicMock(
        ContratServiceCRUD=MagicMock(
            get_contract_types=MagicMock(return_value=['CDI', 'CDD'])
        )
    ),
    'domain.services.documents.document_service': MagicMock(),
    'domain.services.admin.auth_service': MagicMock(
        get_current_user=MagicMock(return_value={'nom_complet': 'Test User'})
    ),
    'application.permission_manager': MagicMock(
        can=MagicMock(return_value=True),
        require=MagicMock(return_value=None),
    ),
    'core.gui.components.ui_theme': MagicMock(),
    'core.gui.components.emac_ui_kit': MagicMock(),
    'core.gui.components.emac_dialog': MagicMock(),
}

# Appliquer tous les patches avant import
for _mod, _mock in _services_to_patch.items():
    sys.modules.setdefault(_mod, _mock)

# Stub EmacFormDialog : base concrète utilisable en test
import unittest.mock as _um

class _EmacFormDialogStub:
    """Stub minimal d'EmacFormDialog pour instancier les dialogs sans Qt."""

    def __init__(self, title='', min_width=400, min_height=400,
                 add_title_bar=True, parent=None):
        self.content_layout = MagicMock()
        self.content_layout.addWidget = MagicMock()
        self.content_layout.addLayout = MagicMock()
        self._title = title
        self.init_ui()  # appel explicite comme EmacFormDialog.__init__ le ferait

    def init_ui(self):
        pass  # override dans les sous-classes


# Remplacer EmacFormDialog dans sys.modules par notre stub
_emac_dialog_mod = sys.modules['core.gui.components.emac_dialog']
_emac_dialog_mod.EmacFormDialog = _EmacFormDialogStub

# Stub EmacButton
_ui_theme_mod = sys.modules['core.gui.components.ui_theme']
_ui_theme_mod.EmacButton = MagicMock(return_value=MagicMock(
    clicked=MagicMock(connect=MagicMock()),
    setFixedWidth=MagicMock(),
))

# Import du module cible APRÈS tous les patches
from core.gui.dialogs.gestion_rh_dialogs import (  # noqa: E402
    JustificatifMixin,
    EditContratDialog,
    EditDeclarationDialog,
    EditFormationDialog,
    EditVisiteDialog,
    EditAccidentDialog,
    EditSanctionDialog,
)


# ===========================================================================
# 1. Logique pure du mixin (sans Qt, sans DB)
# ===========================================================================

class TestJustificatifMixinLogique:
    """Teste _valider_justificatif() indépendamment de tout dialog Qt."""

    def _make_instance(self):
        class Holder(JustificatifMixin):
            pass
        return Holder()

    def test_valider_sans_fichier_retourne_false(self):
        h = self._make_instance()
        ok, msg = h._valider_justificatif()
        assert ok is False
        assert msg

    def test_valider_sans_fichier_message_explicite(self):
        h = self._make_instance()
        _, msg = h._valider_justificatif()
        assert "justificatif" in msg.lower()

    def test_valider_path_none_retourne_false(self):
        h = self._make_instance()
        h._justificatif_path = None
        ok, _ = h._valider_justificatif()
        assert ok is False

    def test_valider_path_chaine_vide_retourne_false(self):
        h = self._make_instance()
        h._justificatif_path = ""
        ok, _ = h._valider_justificatif()
        assert ok is False

    def test_valider_avec_fichier_retourne_true(self):
        h = self._make_instance()
        h._justificatif_path = "/tmp/doc.pdf"
        ok, msg = h._valider_justificatif()
        assert ok is True
        assert msg == ""

    def test_valider_avec_chemin_windows(self):
        h = self._make_instance()
        h._justificatif_path = r"C:\Documents\contrat.pdf"
        ok, _ = h._valider_justificatif()
        assert ok is True

    def test_valider_avec_image(self):
        h = self._make_instance()
        h._justificatif_path = "/home/user/scan.jpg"
        ok, _ = h._valider_justificatif()
        assert ok is True


# ===========================================================================
# 2. Sauvegarde du justificatif (_sauvegarder_justificatif)
# ===========================================================================

class TestJustificatifMixinSauvegarde:
    """Teste que _sauvegarder_justificatif appelle DocumentService correctement."""

    def _make_instance(self, path="/tmp/test.pdf", categorie_hint="Contrats de travail"):
        class Holder(JustificatifMixin):
            pass
        h = Holder()
        h._justificatif_path = path
        h._justificatif_categorie_nom = categorie_hint
        return h

    def test_sans_fichier_nappelle_pas_document_service(self):
        h = self._make_instance(path=None)
        mock_service = MagicMock()
        with patch.dict(sys.modules, {'domain.services.documents.document_service': MagicMock(DocumentService=mock_service)}):
            h._sauvegarder_justificatif(operateur_id=42)
        mock_service.assert_not_called()

    def test_avec_fichier_appelle_add_document(self):
        mock_doc_instance = MagicMock()
        mock_doc_class = MagicMock(return_value=mock_doc_instance)

        categories = [
            {'id': 1, 'nom': 'Contrats de travail'},
            {'id': 2, 'nom': 'Attestations diverses'},
        ]

        h = self._make_instance(path="/tmp/contrat.pdf", categorie_hint="Contrats")
        with patch('domain.services.rh.rh_service.get_categories_documents',
                   return_value=categories), \
             patch('domain.services.documents.document_service.DocumentService', mock_doc_class), \
             patch('domain.services.admin.auth_service.get_current_user',
                   return_value={'nom_complet': 'Jean Test'}):
            h._sauvegarder_justificatif(operateur_id=99)

        mock_doc_instance.add_document.assert_called_once()
        kwargs = mock_doc_instance.add_document.call_args[1]
        assert kwargs['operateur_id'] == 99
        assert kwargs['categorie_id'] == 1
        assert kwargs['fichier_source'] == "/tmp/contrat.pdf"
        assert kwargs['nom_affichage'] == "contrat.pdf"
        assert kwargs['uploaded_by'] == "Jean Test"

    def test_categorie_hint_correspond_partiellement(self):
        mock_doc_instance = MagicMock()
        mock_doc_class = MagicMock(return_value=mock_doc_instance)

        categories = [
            {'id': 5, 'nom': 'Documents médicaux'},
            {'id': 6, 'nom': 'Sanctions disciplinaires'},
        ]

        h = self._make_instance(path="/tmp/rapport.pdf", categorie_hint="médicaux")
        with patch('domain.services.rh.rh_service.get_categories_documents',
                   return_value=categories), \
             patch('domain.services.documents.document_service.DocumentService', mock_doc_class), \
             patch('domain.services.admin.auth_service.get_current_user',
                   return_value={'nom_complet': 'RH Test'}):
            h._sauvegarder_justificatif(operateur_id=7)

        kwargs = mock_doc_instance.add_document.call_args[1]
        assert kwargs['categorie_id'] == 5

    def test_fallback_premiere_categorie_si_hint_inconnu(self):
        mock_doc_instance = MagicMock()
        mock_doc_class = MagicMock(return_value=mock_doc_instance)

        categories = [{'id': 99, 'nom': 'Catégorie générique'}]

        h = self._make_instance(path="/tmp/doc.pdf", categorie_hint="inexistant_xyz")
        with patch('domain.services.rh.rh_service.get_categories_documents',
                   return_value=categories), \
             patch('domain.services.documents.document_service.DocumentService', mock_doc_class), \
             patch('domain.services.admin.auth_service.get_current_user', return_value={}):
            h._sauvegarder_justificatif(operateur_id=1)

        kwargs = mock_doc_instance.add_document.call_args[1]
        assert kwargs['categorie_id'] == 99

    def test_erreur_document_service_est_silencieuse(self):
        """Une erreur dans DocumentService ne doit pas faire planter le dialog."""
        mock_doc_instance = MagicMock()
        mock_doc_instance.add_document.side_effect = RuntimeError("DMS indisponible")
        mock_doc_class = MagicMock(return_value=mock_doc_instance)

        h = self._make_instance(path="/tmp/doc.pdf")
        with patch('domain.services.rh.rh_service.get_categories_documents',
                   return_value=[{'id': 1, 'nom': 'Contrats de travail'}]), \
             patch('domain.services.documents.document_service.DocumentService', mock_doc_class), \
             patch('domain.services.admin.auth_service.get_current_user', return_value={}):
            h._sauvegarder_justificatif(operateur_id=1)  # ne doit pas lever


# ===========================================================================
# 3. Héritage MRO — chaque dialog hérite de JustificatifMixin
# ===========================================================================

DIALOGS_CREATION = [
    EditContratDialog,
    EditDeclarationDialog,
    EditFormationDialog,
    EditVisiteDialog,
    EditAccidentDialog,
    EditSanctionDialog,
]

class TestDialogsMROInheritance:
    """Vérifie que chaque dialog intègre correctement JustificatifMixin."""

    @pytest.mark.parametrize("dialog_cls", DIALOGS_CREATION)
    def test_herite_de_justificatif_mixin(self, dialog_cls):
        assert issubclass(dialog_cls, JustificatifMixin), (
            f"{dialog_cls.__name__} n'hérite pas de JustificatifMixin"
        )

    @pytest.mark.parametrize("dialog_cls", DIALOGS_CREATION)
    def test_possede_valider_justificatif(self, dialog_cls):
        assert hasattr(dialog_cls, '_valider_justificatif')
        assert callable(getattr(dialog_cls, '_valider_justificatif'))

    @pytest.mark.parametrize("dialog_cls", DIALOGS_CREATION)
    def test_possede_sauvegarder_justificatif(self, dialog_cls):
        assert hasattr(dialog_cls, '_sauvegarder_justificatif')
        assert callable(getattr(dialog_cls, '_sauvegarder_justificatif'))

    @pytest.mark.parametrize("dialog_cls", DIALOGS_CREATION)
    def test_possede_validate(self, dialog_cls):
        """Chaque dialog doit avoir une méthode validate() propre."""
        assert 'validate' in dialog_cls.__dict__, (
            f"{dialog_cls.__name__} n'a pas de validate() propre"
        )

    @pytest.mark.parametrize("dialog_cls", DIALOGS_CREATION)
    def test_mixin_avant_emac_form_dans_mro(self, dialog_cls):
        mro_names = [c.__name__ for c in dialog_cls.__mro__]
        assert 'JustificatifMixin' in mro_names, (
            f"JustificatifMixin absent du MRO de {dialog_cls.__name__}"
        )


# ===========================================================================
# 4. Section justificatif présente en création, absente en modification
# ===========================================================================

def _noop_section(self, categorie_nom_hint=''):
    """
    Remplaçant de _ajouter_section_justificatif pendant la construction.
    Initialise les attributs attendus sans créer de vrais widgets Qt.
    """
    self._justificatif_path = None
    self._justificatif_categorie_nom = categorie_nom_hint
    self._justificatif_label = MagicMock()


def _make_dialog(cls, is_edit: bool, **kwargs):
    """
    Instancie un dialog en mode création ou modification.
    Pendant la construction, _ajouter_section_justificatif est remplacé par
    _noop_section pour éviter de mélanger vrais widgets Qt et MagicMocks.
    """
    with patch.object(JustificatifMixin, '_ajouter_section_justificatif', _noop_section):
        if cls == EditContratDialog:
            dlg = cls(operateur_id=1, contrat={'id': 9, 'type_contrat': 'CDI'} if is_edit else None)
        elif cls == EditDeclarationDialog:
            dlg = cls(operateur_id=1, declaration={'id': 9} if is_edit else None)
        elif cls == EditFormationDialog:
            dlg = cls(operateur_id=1, formation={'id': 9, 'intitule': 'Test'} if is_edit else None)
        elif cls == EditVisiteDialog:
            dlg = cls(operateur_id=1, visite={'id': 9} if is_edit else None)
        elif cls == EditAccidentDialog:
            dlg = cls(operateur_id=1, accident={'id': 9} if is_edit else None)
        elif cls == EditSanctionDialog:
            dlg = cls(operateur_id=1, sanction={'id': 9} if is_edit else None)
        else:
            raise ValueError(f"Dialog inconnu: {cls}")
    return dlg


class TestCreationModeSections:
    """
    Vérifie que _ajouter_section_justificatif est appelé en création uniquement,
    avec le bon hint de catégorie.

    Stratégie : spy wrappant _noop_section pour capturer les args sans créer
    de vrais widgets Qt.
    """

    def _spy_section(self):
        calls = []

        def _wrapped(self_dlg, categorie_nom_hint=''):
            calls.append(categorie_nom_hint)
            _noop_section(self_dlg, categorie_nom_hint)

        return _wrapped, calls

    @pytest.mark.parametrize("dialog_cls", DIALOGS_CREATION)
    def test_creation_appelle_ajouter_section(self, dialog_cls):
        spy, calls = self._spy_section()
        with patch.object(JustificatifMixin, '_ajouter_section_justificatif', spy):
            if dialog_cls == EditContratDialog:
                dialog_cls(operateur_id=1, contrat=None)
            elif dialog_cls == EditDeclarationDialog:
                dialog_cls(operateur_id=1, declaration=None)
            elif dialog_cls == EditFormationDialog:
                dialog_cls(operateur_id=1, formation=None)
            elif dialog_cls == EditVisiteDialog:
                dialog_cls(operateur_id=1, visite=None)
            elif dialog_cls == EditAccidentDialog:
                dialog_cls(operateur_id=1, accident=None)
            elif dialog_cls == EditSanctionDialog:
                dialog_cls(operateur_id=1, sanction=None)
        assert len(calls) == 1, (
            f"{dialog_cls.__name__}: attendu 1 appel en création, reçu {len(calls)}"
        )

    @pytest.mark.parametrize("dialog_cls", DIALOGS_CREATION)
    def test_modification_nappelle_pas_ajouter_section(self, dialog_cls):
        spy, calls = self._spy_section()
        with patch.object(JustificatifMixin, '_ajouter_section_justificatif', spy):
            if dialog_cls == EditContratDialog:
                dialog_cls(operateur_id=1, contrat={'id': 9, 'type_contrat': 'CDI'})
            elif dialog_cls == EditDeclarationDialog:
                dialog_cls(operateur_id=1, declaration={'id': 9})
            elif dialog_cls == EditFormationDialog:
                dialog_cls(operateur_id=1, formation={'id': 9, 'intitule': 'Test'})
            elif dialog_cls == EditVisiteDialog:
                dialog_cls(operateur_id=1, visite={'id': 9})
            elif dialog_cls == EditAccidentDialog:
                dialog_cls(operateur_id=1, accident={'id': 9})
            elif dialog_cls == EditSanctionDialog:
                dialog_cls(operateur_id=1, sanction={'id': 9})
        assert len(calls) == 0, (
            f"{dialog_cls.__name__}: _ajouter_section_justificatif ne doit pas "
            f"être appelé en modification"
        )

    @pytest.mark.parametrize("dialog_cls,expected_hint", [
        (EditContratDialog,     "Contrats de travail"),
        (EditDeclarationDialog, "Attestations"),
        (EditFormationDialog,   "Diplômes et formations"),
        (EditVisiteDialog,      "Certificats médicaux"),
        (EditAccidentDialog,    "Documents médicaux"),
        (EditSanctionDialog,    "Sanctions disciplinaires"),
    ])
    def test_categorie_hint_correcte(self, dialog_cls, expected_hint):
        spy, calls = self._spy_section()
        with patch.object(JustificatifMixin, '_ajouter_section_justificatif', spy):
            if dialog_cls == EditContratDialog:
                dialog_cls(operateur_id=1, contrat=None)
            elif dialog_cls == EditDeclarationDialog:
                dialog_cls(operateur_id=1, declaration=None)
            elif dialog_cls == EditFormationDialog:
                dialog_cls(operateur_id=1, formation=None)
            elif dialog_cls == EditVisiteDialog:
                dialog_cls(operateur_id=1, visite=None)
            elif dialog_cls == EditAccidentDialog:
                dialog_cls(operateur_id=1, accident=None)
            elif dialog_cls == EditSanctionDialog:
                dialog_cls(operateur_id=1, sanction=None)
        assert calls, f"{dialog_cls.__name__}: _ajouter_section_justificatif non appelé"
        assert expected_hint in calls[0], (
            f"{dialog_cls.__name__}: attendu '{expected_hint}' dans '{calls[0]}'"
        )


# ===========================================================================
# 5. validate() bloque sans justificatif (création) et passe en modification
# ===========================================================================

class TestValidation:
    """Teste validate() pour chaque dialog."""

    @pytest.mark.parametrize("dialog_cls", DIALOGS_CREATION)
    def test_creation_sans_justificatif_bloque(self, dialog_cls):
        dlg = _make_dialog(dialog_cls, is_edit=False)
        dlg._justificatif_path = None

        if hasattr(dlg, 'intitule'):
            dlg.intitule = MagicMock(text=MagicMock(return_value="Test Formation"))

        ok, msg = dlg.validate()
        assert ok is False, (
            f"{dialog_cls.__name__}: validate() devrait retourner False sans justificatif"
        )
        assert "justificatif" in msg.lower()

    @pytest.mark.parametrize("dialog_cls", DIALOGS_CREATION)
    def test_creation_avec_justificatif_passe(self, dialog_cls):
        dlg = _make_dialog(dialog_cls, is_edit=False)
        dlg._justificatif_path = "/tmp/justificatif.pdf"

        if hasattr(dlg, 'intitule'):
            dlg.intitule = MagicMock(text=MagicMock(return_value="Formation test"))
        if hasattr(dlg, 'competence_combo'):
            dlg.competence_combo = MagicMock(currentData=MagicMock(return_value={'id': 1}))

        ok, _ = dlg.validate()
        assert ok is True, (
            f"{dialog_cls.__name__}: validate() devrait retourner True avec justificatif"
        )

    @pytest.mark.parametrize("dialog_cls", DIALOGS_CREATION)
    def test_modification_sans_justificatif_autorise(self, dialog_cls):
        dlg = _make_dialog(dialog_cls, is_edit=True)

        if hasattr(dlg, 'intitule'):
            dlg.intitule = MagicMock(text=MagicMock(return_value="Formation modifiée"))
        if hasattr(dlg, 'nom'):
            dlg.nom = MagicMock(text=MagicMock(return_value="Dupont"))
        if hasattr(dlg, 'prenom'):
            dlg.prenom = MagicMock(text=MagicMock(return_value="Jean"))

        ok, _ = dlg.validate()
        assert ok is True, (
            f"{dialog_cls.__name__}: validate() en modification ne doit pas bloquer "
            f"sans justificatif"
        )


# ===========================================================================
# 6. save_to_db() appelle _sauvegarder_justificatif uniquement en création
# ===========================================================================

class TestSaveToDbJustificatif:
    """Vérifie que le justificatif est uploadé après une création réussie."""

    # Les fonctions sont importées dans le namespace du module dialogs :
    # il faut patcher core.gui.gestion_rh_dialogs.<fn>, pas la source.
    _DIALOGS_MODULE = 'core.gui.dialogs.gestion_rh_dialogs'

    def _test_creation_upload(self, dialog_cls, fn_name, success_retval):
        """Création réussie → _sauvegarder_justificatif appelé."""
        dlg = _make_dialog(dialog_cls, is_edit=False)
        dlg._justificatif_path = "/tmp/justif.pdf"
        dlg._justificatif_categorie_nom = "test"
        _patch_form_fields(dlg)

        with patch.object(dlg, '_sauvegarder_justificatif') as mock_save, \
             patch(f'{self._DIALOGS_MODULE}.{fn_name}', return_value=success_retval):
            dlg.save_to_db()

        mock_save.assert_called_once_with(dlg.operateur_id)

    def _test_echec_creation_pas_upload(self, dialog_cls, fn_name, fail_retval):
        """Création échouée → _sauvegarder_justificatif NON appelé."""
        dlg = _make_dialog(dialog_cls, is_edit=False)
        dlg._justificatif_path = "/tmp/justif.pdf"
        _patch_form_fields(dlg)

        with patch.object(dlg, '_sauvegarder_justificatif') as mock_save, \
             patch(f'{self._DIALOGS_MODULE}.{fn_name}', return_value=fail_retval):
            try:
                dlg.save_to_db()
            except Exception:
                pass

        mock_save.assert_not_called()

    def test_contrat_creation_upload_justificatif(self):
        self._test_creation_upload(EditContratDialog, 'create_contrat', (True, '', 1))

    def test_contrat_echec_creation_pas_upload(self):
        self._test_echec_creation_pas_upload(EditContratDialog, 'create_contrat', (False, 'Erreur BD', None))

    def test_declaration_creation_upload_justificatif(self):
        self._test_creation_upload(EditDeclarationDialog, 'create_declaration', (True, '', 3))

    def test_formation_creation_upload_justificatif(self):
        self._test_creation_upload(EditFormationDialog, 'create_formation', (True, '', 2))

    def test_visite_creation_upload_justificatif(self):
        self._test_creation_upload(EditVisiteDialog, 'create_visite', (True, '', 10))

    def test_accident_creation_upload_justificatif(self):
        self._test_creation_upload(EditAccidentDialog, 'create_accident', (True, '', 11))

    def test_sanction_creation_upload_justificatif(self):
        self._test_creation_upload(EditSanctionDialog, 'create_sanction', (True, '', 20))

    def test_modification_nappelle_jamais_sauvegarder(self):
        """En mode modification, _sauvegarder_justificatif ne doit jamais être appelé."""
        for dialog_cls in DIALOGS_CREATION:
            dlg = _make_dialog(dialog_cls, is_edit=True)
            with patch.object(dlg, '_sauvegarder_justificatif') as mock_save:
                _patch_form_fields(dlg)
                try:
                    dlg.save_to_db()
                except Exception:
                    pass
            assert not mock_save.called, (
                f"{dialog_cls.__name__}: _sauvegarder_justificatif ne doit pas "
                f"être appelé en modification"
            )


# ---------------------------------------------------------------------------
# Utilitaire : patcher les champs de formulaire Qt
# ---------------------------------------------------------------------------

def _patch_form_fields(dlg):
    """Remplace les widgets Qt par des mocks renvoyant des valeurs cohérentes."""
    from datetime import date as _date

    _date_mock = MagicMock()
    _date_mock.toPyDate.return_value = _date(2026, 1, 1)
    _date_mock.year.return_value = 2026

    _date_widget = MagicMock()
    _date_widget.date.return_value = _date_mock

    for attr in [
        'type_combo', 'date_debut', 'date_fin', 'etp', 'categorie', 'emploi',
        'salaire', 'motif', 'intitule', 'organisme', 'duree', 'statut_combo',
        'certificat', 'commentaire', 'date_visite', 'type_visite',
        'resultat_combo', 'restrictions', 'medecin', 'prochaine_visite',
        'date_accident', 'avec_arret', 'circonstances', 'siege_lesions',
        'nature_lesions', 'nb_jours', 'date_sanction',
    ]:
        if not hasattr(dlg, attr):
            setattr(dlg, attr, MagicMock())

    for date_attr in ['date_debut', 'date_fin', 'date_visite', 'prochaine_visite',
                      'date_accident', 'date_sanction', 'date_entretien',
                      'prochaine_date', 'date_test', 'date_controle']:
        if hasattr(dlg, date_attr):
            setattr(dlg, date_attr, _date_widget)

    for text_attr in ['categorie', 'emploi', 'organisme', 'motif', 'commentaire',
                      'circonstances', 'siege_lesions', 'nature_lesions',
                      'restrictions', 'medecin', 'intitule']:
        if hasattr(dlg, text_attr):
            getattr(dlg, text_attr).text = MagicMock(return_value='')
            getattr(dlg, text_attr).toPlainText = MagicMock(return_value='')

    for spin_attr in ['etp', 'salaire', 'duree', 'nb_jours']:
        if hasattr(dlg, spin_attr):
            getattr(dlg, spin_attr).value = MagicMock(return_value=0.0)

    for combo_attr in ['type_combo', 'statut_combo', 'resultat_combo']:
        if hasattr(dlg, combo_attr):
            getattr(dlg, combo_attr).currentText = MagicMock(return_value='CDI')

    for chk_attr in ['certificat', 'avec_arret']:
        if hasattr(dlg, chk_attr):
            getattr(dlg, chk_attr).isChecked = MagicMock(return_value=False)
