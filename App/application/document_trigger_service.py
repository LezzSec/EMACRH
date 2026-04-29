# -*- coding: utf-8 -*-
"""
Service de déclenchement automatique des documents.

Ce service écoute les événements métier via l'EventBus et génère
ou propose les documents selon les règles configurées.

Modes d'exécution:
    - AUTO: Génère et ouvre automatiquement le document
    - PROPOSED: Ajoute à la liste des documents en attente (dialog)
    - SILENT: Log seulement (pour audit sans action)

Usage:
    # Initialisation au démarrage de l'application
    from application.document_trigger_service import DocumentTriggerService
    trigger_service = DocumentTriggerService()  # S'abonne automatiquement

    # Les événements sont traités automatiquement
    EventBus.emit('personnel.created', {'operateur_id': 1, 'nom': 'Dupont', ...})

    # Récupérer les documents en attente
    pending = DocumentTriggerService.get_pending_documents(operateur_id=1)

    # Générer un document en attente
    success, msg, path = DocumentTriggerService.generate_pending(pending[0])
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock

from application.event_bus import EventBus, DomainEvent
from application.event_rule_service import get_matching_templates
from domain.services.documents.template_service import generate_filled_template, open_template_file
from infrastructure.logging.optimized_db_logger import log_hist

logger = logging.getLogger(__name__)


@dataclass
class PendingDocument:
    """
    Document en attente de génération/validation par l'utilisateur.

    Attributes:
        template_id: ID du template
        template_nom: Nom affiché du template
        execution_mode: Mode d'exécution original
        operateur_id: ID de l'opérateur concerné
        operateur_nom: Nom de l'opérateur
        operateur_prenom: Prénom de l'opérateur
        event_name: Événement déclencheur
        rule_id: ID de la règle ayant déclenché
        timestamp: Date/heure de création
    """
    template_id: int
    template_nom: str
    execution_mode: str
    operateur_id: int
    operateur_nom: str
    operateur_prenom: str
    event_name: str
    rule_id: int = 0
    document_type: str = 'template'
    formation_doc_id: int = 0
    poste_id: Optional[int] = None
    niveau: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def __repr__(self) -> str:
        return f"PendingDocument({self.template_nom} pour {self.operateur_prenom} {self.operateur_nom})"


class DocumentTriggerService:
    """
    Service de déclenchement de documents (Singleton).

    S'abonne aux événements métier et:
    - Mode AUTO: génère automatiquement en background
    - Mode PROPOSED: stocke pour affichage dans un dialog
    - Mode SILENT: log seulement sans action

    Thread-safe grâce à un lock sur les opérations de liste.
    """

    _instance = None
    _lock = Lock()

    def __new__(cls):
        """Implémentation Singleton thread-safe."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialise les souscriptions aux événements."""
        self._pending_documents: List[PendingDocument] = []
        self._pending_lock = Lock()
        self._enabled = True

        # S'abonner à tous les événements pertinents via wildcards
        EventBus.subscribe('personnel.*', self._handle_event)
        EventBus.subscribe('contrat.*', self._handle_event)
        EventBus.subscribe('polyvalence.*', self._handle_event)
        EventBus.subscribe('evaluation.*', self._handle_event)

        logger.info("DocumentTriggerService initialisé et abonné aux événements")

    def _handle_event(self, event: DomainEvent):
        """
        Gestionnaire central des événements.

        Récupère les templates correspondants et les traite selon leur mode.

        Args:
            event: L'événement reçu
        """
        if not self._enabled:
            logger.debug(f"DocumentTrigger désactivé, événement ignoré: {event.name}")
            return

        logger.debug(f"DocumentTrigger: traitement de '{event.name}'")

        # Quand le niveau baisse, supprimer les docs en attente des niveaux devenus invalides
        # (traité avant la récupération des templates car niveau_changed n'a pas de règles)
        if event.name == 'polyvalence.niveau_changed':
            op_id = event.data.get('operateur_id')
            new_niv = event.data.get('new_niveau')
            old_niv = event.data.get('old_niveau')
            if op_id and new_niv is not None and old_niv is not None and new_niv < old_niv:
                for n in range(new_niv + 1, 5):
                    self._remove_pending_by_event(op_id, f'polyvalence.niveau_{n}_reached')
                logger.info(
                    f"Niveau abaissé ({old_niv}→{new_niv}) pour op {op_id}: "
                    f"docs niveaux {new_niv+1}-4 supprimés de la queue"
                )

        # Pour les créations de personnel, ignorer si ce n'est pas de la production
        if event.name == 'personnel.created' and not event.data.get('is_production', True):
            logger.debug("DocumentTrigger: personnel non-production, documents ignorés")
            return

        # Récupérer les templates correspondants (avec évaluation des conditions)
        # Priorite des niveaux: a traiter avant la recherche de templates.
        # Le niveau 4 n'a pas de template, mais il doit quand meme purger
        # les documents niveau 1-3 encore en attente.
        import re as _re
        _m = _re.match(r'polyvalence\.niveau_(\d)_reached', event.name)
        if _m:
            new_niv = int(_m.group(1))
            op_id = event.data.get('operateur_id')
            if op_id and new_niv > 1:
                for n in range(1, new_niv):
                    self._remove_pending_by_event(op_id, f'polyvalence.niveau_{n}_reached')
            elif op_id and new_niv == 1:
                self._remove_pending_by_event(op_id, 'polyvalence.niveau_1_reached')
                logger.debug(
                    f"niveau_1_reached sur nouveau poste pour op {op_id}: "
                    f"anciens docs niveau_1 supprimÃ©s de la queue"
                )

        templates = get_matching_templates(event.name, event.data)
        templates = self._with_niveau_3_poste_templates(event.name, event.data, templates)

        if not templates:
            logger.debug(f"Aucun template configuré pour '{event.name}'")
            return

        logger.info(f"DocumentTrigger: {len(templates)} template(s) pour '{event.name}'")

        # Extraire les infos opérateur depuis les données de l'événement
        operateur_id = event.data.get('operateur_id')
        operateur_nom = event.data.get('nom', '')
        operateur_prenom = event.data.get('prenom', '')

        # Quand un niveau supérieur est atteint, supprimer les docs des niveaux inférieurs.
        # Ex : 1→3 direct : niveau_1_reached doit être retiré quand niveau_3_reached arrive.
        # Quand niveau_1_reached est émis pour un nouveau poste, purger les anciens docs
        # niveau_1_reached d'autres postes déjà en file d'attente pour cet opérateur afin
        # de ne proposer que le document du poste actuellement traité.
        import re as _re
        _m = _re.match(r'polyvalence\.niveau_(\d)_reached', event.name)
        if _m:
            new_niv = int(_m.group(1))
            op_id = event.data.get('operateur_id')
            if op_id and new_niv > 1:
                for n in range(1, new_niv):
                    self._remove_pending_by_event(op_id, f'polyvalence.niveau_{n}_reached')
            elif op_id and new_niv == 1:
                # Purger les anciens docs niveau_1 (autres postes) pour ne montrer
                # que les documents du poste en cours d'affectation.
                self._remove_pending_by_event(op_id, 'polyvalence.niveau_1_reached')
                logger.debug(
                    f"niveau_1_reached sur nouveau poste pour op {op_id}: "
                    f"anciens docs niveau_1 supprimés de la queue"
                )

        # Traiter chaque template selon son mode
        for tpl in templates:
            mode = tpl['execution_mode']

            if mode == 'AUTO':
                self._generate_auto(
                    tpl, operateur_id, operateur_nom, operateur_prenom, event.name
                )

            elif mode == 'PROPOSED':
                self._add_pending(
                    tpl, operateur_id, operateur_nom, operateur_prenom, event.name
                )

            else:  # SILENT
                self._log_silent(tpl, operateur_id, event.name)

    @staticmethod
    def _append_unique_templates(base: List[Dict], extra: List[Dict]) -> List[Dict]:
        """Fusionne des templates en evitant les doublons par template_id."""
        result = list(base)
        seen = {tpl.get('template_id') for tpl in result}
        for tpl in extra:
            template_id = tpl.get('template_id')
            if template_id in seen:
                continue
            seen.add(template_id)
            result.append(tpl)
        return result

    @classmethod
    def _get_poste_sheet_templates(cls, event_data: Dict) -> List[Dict]:
        """
        Retourne la feuille de poste applicable.

        Les feuilles de poste sont configurees sur polyvalence.created dans la
        base actuelle. On garde un fallback vers niveau_2 si les regles ont ete
        rangees la-bas.
        """
        poste_templates = get_matching_templates('polyvalence.created', event_data)
        if poste_templates:
            return poste_templates
        return get_matching_templates('polyvalence.niveau_2_reached', event_data)

    @classmethod
    def _with_niveau_3_poste_templates(
        cls,
        event_name: str,
        event_data: Dict,
        templates: List[Dict],
    ) -> List[Dict]:
        """Au niveau 3, ajoute la feuille de poste en plus du questionnaire."""
        if event_name != 'polyvalence.niveau_3_reached':
            return templates
        return cls._append_unique_templates(
            templates,
            cls._get_poste_sheet_templates(event_data),
        )

    def _generate_auto(
        self,
        template: Dict,
        op_id: int,
        nom: str,
        prenom: str,
        event_name: str
    ):
        """
        Génère automatiquement un document et l'ouvre.

        Exécuté en mode synchrone (peut être amélioré avec DbWorker si besoin).

        Args:
            template: Infos du template
            op_id: ID opérateur
            nom: Nom opérateur
            prenom: Prénom opérateur
            event_name: Nom de l'événement déclencheur
        """
        try:
            success, msg, path = generate_filled_template(
                template_id=template['template_id'],
                operateur_nom=nom,
                operateur_prenom=prenom
            )

            if success and path:
                open_template_file(path)
                log_hist(
                    "DOCUMENT_AUTO_GENERATED",
                    "documents_templates",
                    template['template_id'],
                    f"Document '{template['template_nom']}' généré automatiquement "
                    f"pour {prenom} {nom} (événement: {event_name})",
                    operateur_id=op_id
                )
                logger.info(f"Document AUTO généré: {template['template_nom']} -> {path}")
            else:
                logger.error(f"Échec génération AUTO: {msg}")

        except Exception as e:
            logger.error(f"Erreur génération AUTO '{template['template_nom']}': {e}", exc_info=True)

    def _add_pending(
        self,
        template: Dict,
        op_id: int,
        nom: str,
        prenom: str,
        event_name: str
    ) -> bool:
        """
        Ajoute un document à la liste des documents en attente.

        Args:
            template: Infos du template
            op_id: ID opérateur
            nom: Nom opérateur
            prenom: Prénom opérateur
            event_name: Nom de l'événement déclencheur
        """
        pending = PendingDocument(
            template_id=template['template_id'],
            template_nom=template['template_nom'],
            execution_mode=template['execution_mode'],
            operateur_id=op_id,
            operateur_nom=nom,
            operateur_prenom=prenom,
            event_name=event_name,
            rule_id=template.get('rule_id', 0)
        )

        return self._append_pending(pending)

    def _append_pending(self, pending: PendingDocument) -> bool:
        """Ajoute un document en attente en evitant les doublons."""
        with self._pending_lock:
            # Éviter les doublons
            exists = any(
                p.operateur_id == pending.operateur_id
                and p.document_type == pending.document_type
                and (
                    (p.document_type == 'formation' and p.formation_doc_id == pending.formation_doc_id)
                    or (p.document_type != 'formation' and p.template_id == pending.template_id)
                )
                for p in self._pending_documents
            )
            if not exists:
                self._pending_documents.append(pending)
                logger.debug(f"Document en attente ajoute: {pending.template_nom}")
                return True
            return False

    def _add_pending_formation(
        self,
        doc: Dict,
        op_id: int,
        nom: str,
        prenom: str,
        event_name: str
    ) -> bool:
        """Ajoute un dossier de formation poste/niveau a la file d'attente."""
        pending = PendingDocument(
            template_id=0,
            template_nom=doc.get('nom_affichage') or doc.get('nom_fichier') or 'Document formation',
            execution_mode='PROPOSED',
            operateur_id=op_id,
            operateur_nom=nom,
            operateur_prenom=prenom,
            event_name=event_name,
            rule_id=0,
            document_type='formation',
            formation_doc_id=doc.get('id') or 0,
            poste_id=doc.get('poste_id'),
            niveau=doc.get('niveau'),
        )
        return self._append_pending(pending)

    def _remove_pending_by_event(self, operateur_id: int, event_name: str):
        """
        Retire tous les documents en attente d'un opérateur liés à un événement donné.

        Utilisé pour les règles de priorité (ex: niveau 3 annule les docs niveau 2).
        """
        with self._pending_lock:
            before = len(self._pending_documents)
            self._pending_documents = [
                p for p in self._pending_documents
                if not (p.operateur_id == operateur_id and p.event_name == event_name)
            ]
            removed = before - len(self._pending_documents)
            if removed:
                logger.debug(
                    f"Priorité niveau 3 : {removed} doc(s) '{event_name}' "
                    f"supprimé(s) pour opérateur {operateur_id}"
                )

    def _log_silent(self, template: Dict, op_id: int, event_name: str):
        """
        Log un événement SILENT (pas de génération).

        Args:
            template: Infos du template
            op_id: ID opérateur
            event_name: Nom de l'événement
        """
        log_hist(
            "DOCUMENT_SILENT_TRIGGER",
            "documents_templates",
            template['template_id'],
            f"Document '{template['template_nom']}' déclenché en mode silencieux "
            f"(événement: {event_name})",
            operateur_id=op_id
        )
        logger.debug(f"Document SILENT logué: {template['template_nom']}")

    # =========================================================================
    # API publique (méthodes de classe)
    # =========================================================================

    @classmethod
    def get_pending_documents(cls, operateur_id: int = None) -> List[PendingDocument]:
        """
        Récupère les documents en attente.

        Args:
            operateur_id: Filtrer par opérateur (optionnel)

        Returns:
            Liste des PendingDocument
        """
        instance = cls()
        with instance._pending_lock:
            if operateur_id is not None:
                return [p for p in instance._pending_documents if p.operateur_id == operateur_id]
            return instance._pending_documents.copy()

    @classmethod
    def get_pending_count(cls, operateur_id: int = None) -> int:
        """
        Retourne le nombre de documents en attente.

        Args:
            operateur_id: Filtrer par opérateur (optionnel)

        Returns:
            Nombre de documents en attente
        """
        return len(cls.get_pending_documents(operateur_id))

    @classmethod
    def has_pending_documents(cls, operateur_id: int = None) -> bool:
        """
        Vérifie s'il y a des documents en attente.

        Args:
            operateur_id: Filtrer par opérateur (optionnel)

        Returns:
            True s'il y a des documents en attente
        """
        return cls.get_pending_count(operateur_id) > 0

    @classmethod
    def clear_pending(cls, operateur_id: int = None):
        """
        Efface les documents en attente.

        Args:
            operateur_id: Effacer uniquement pour cet opérateur (optionnel)
        """
        instance = cls()
        with instance._pending_lock:
            if operateur_id is not None:
                instance._pending_documents = [
                    p for p in instance._pending_documents
                    if p.operateur_id != operateur_id
                ]
                logger.debug(f"Documents en attente effacés pour opérateur {operateur_id}")
            else:
                instance._pending_documents.clear()
                logger.debug("Tous les documents en attente effacés")

    @classmethod
    def add_formation_docs_for_level(
        cls,
        operateur_id: int,
        nom: str,
        prenom: str,
        poste_id: int,
        niveau: int,
        event_name: str = None,
    ) -> int:
        """
        Ajoute les documents de formation lies au poste/niveau dans la file.

        Ces documents viennent de documents_formation_polyvalence et ne passent
        pas par document_event_rules.
        """
        if not operateur_id or not poste_id or niveau not in (1, 2, 3):
            return 0

        try:
            from domain.services.documents.polyvalence_docs_service import get_docs_pour_poste
            docs = get_docs_pour_poste(poste_id, niveau)
        except Exception as e:
            logger.warning(f"Erreur lecture documents formation poste {poste_id}/N{niveau}: {e}")
            return 0

        instance = cls()
        added = 0
        trigger = event_name or f'polyvalence.niveau_{niveau}_reached'
        for doc in docs:
            if instance._add_pending_formation(doc, operateur_id, nom, prenom, trigger):
                added += 1
        return added

    @classmethod
    def remove_pending(cls, pending: PendingDocument):
        """
        Retire un document spécifique de la liste d'attente.

        Args:
            pending: Le document à retirer
        """
        instance = cls()
        with instance._pending_lock:
            try:
                instance._pending_documents.remove(pending)
            except ValueError:
                pass  # Pas dans la liste

    @classmethod
    def _extract_formation_pending(
        cls,
        pending: PendingDocument,
        remove_after: bool = False,
        action: str = "DOCUMENT_FORMATION_GENERATED",
    ) -> Tuple[bool, str, Optional[str]]:
        """Extrait un document de formation BLOB vers un fichier imprimable."""
        try:
            from domain.services.documents.polyvalence_docs_service import extraire_vers_fichier_temp

            if not pending.formation_doc_id:
                return False, "Document formation invalide", None

            path = extraire_vers_fichier_temp(pending.formation_doc_id)
            if not path:
                return False, "Document formation introuvable", None

            log_hist(
                action,
                "documents_formation_polyvalence",
                pending.formation_doc_id,
                f"Document formation '{pending.template_nom}' extrait pour "
                f"{pending.operateur_prenom} {pending.operateur_nom}",
                operateur_id=pending.operateur_id
            )

            if remove_after:
                cls.remove_pending(pending)

            return True, "Document formation pret", str(path)

        except Exception as e:
            logger.error(f"Erreur extraction document formation '{pending.template_nom}': {e}", exc_info=True)
            return False, str(e), None

    @classmethod
    def generate_pending(
        cls,
        pending: PendingDocument,
        auditeur_nom: str = ""
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Génère un document en attente.

        Args:
            pending: Le document à générer
            auditeur_nom: Nom de l'auditeur (optionnel)

        Returns:
            Tuple (success, message, file_path)
        """
        try:
            if pending.document_type == 'formation':
                return cls._extract_formation_pending(
                    pending,
                    remove_after=True,
                    action="DOCUMENT_FORMATION_GENERATED",
                )

            success, msg, path = generate_filled_template(
                template_id=pending.template_id,
                operateur_nom=pending.operateur_nom,
                operateur_prenom=pending.operateur_prenom,
                auditeur_nom=auditeur_nom
            )

            if success:
                log_hist(
                    "DOCUMENT_PROPOSED_GENERATED",
                    "documents_templates",
                    pending.template_id,
                    f"Document '{pending.template_nom}' généré pour "
                    f"{pending.operateur_prenom} {pending.operateur_nom}",
                    operateur_id=pending.operateur_id
                )
                # Retirer de la liste d'attente
                cls.remove_pending(pending)

            return success, msg, path

        except Exception as e:
            logger.error(f"Erreur génération pending: {e}", exc_info=True)
            return False, str(e), None

    @classmethod
    def compute_documents_for_polyvalences(
        cls,
        operateur_id: int,
        nom: str,
        prenom: str,
        polyvalences: list
    ) -> List['PendingDocument']:
        """
        Calcule les documents disponibles pour les polyvalences d'un opérateur
        **sans modifier la file d'attente** (lecture seule).

        Utilisé pour afficher les documents potentiels avant que l'utilisateur
        confirme la génération.

        Args:
            operateur_id: ID de l'opérateur
            nom: Nom de l'opérateur
            prenom: Prénom de l'opérateur
            polyvalences: Liste de dicts avec clés: id, poste_id, poste_code, niveau

        Returns:
            Liste de PendingDocument (non ajoutés à la queue)
        """
        from application.event_rule_service import get_matching_templates

        result = []
        seen: set = set()

        for poly in polyvalences:
            niveau = poly.get('niveau')
            poste_id = poly.get('poste_id')
            code_poste = poly.get('poste_code') or str(poste_id)

            event_data = {
                'operateur_id': operateur_id,
                'nom': nom,
                'prenom': prenom,
                'polyvalence_id': poly.get('id'),
                'poste_id': poste_id,
                'code_poste': code_poste,
                'niveau': niveau,
                'new_niveau': niveau,
            }

            if niveau in (1, 2, 3):
                try:
                    from domain.services.documents.polyvalence_docs_service import get_docs_pour_poste
                    for doc in get_docs_pour_poste(poste_id, niveau):
                        key = ('formation', doc.get('id'), operateur_id)
                        if key not in seen:
                            seen.add(key)
                            result.append(PendingDocument(
                                template_id=0,
                                template_nom=doc.get('nom_affichage') or doc.get('nom_fichier') or 'Document formation',
                                execution_mode='PROPOSED',
                                operateur_id=operateur_id,
                                operateur_nom=nom,
                                operateur_prenom=prenom,
                                event_name=f'polyvalence.niveau_{niveau}_reached',
                                document_type='formation',
                                formation_doc_id=doc.get('id') or 0,
                                poste_id=poste_id,
                                niveau=doc.get('niveau'),
                            ))
                except Exception as e:
                    logger.warning(f"Erreur calcul documents formation poste {poste_id}/N{niveau}: {e}")

            for event_name in (f'polyvalence.niveau_{niveau}_reached', 'evaluation.completed'):
                templates = get_matching_templates(event_name, event_data)
                templates = cls._with_niveau_3_poste_templates(event_name, event_data, templates)
                for tpl in templates:
                    key = ('template', tpl['template_id'], operateur_id)
                    if key not in seen:
                        seen.add(key)
                        result.append(PendingDocument(
                            template_id=tpl['template_id'],
                            template_nom=tpl['template_nom'],
                            execution_mode=tpl['execution_mode'],
                            operateur_id=operateur_id,
                            operateur_nom=nom,
                            operateur_prenom=prenom,
                            event_name=event_name,
                            rule_id=tpl.get('rule_id', 0)
                        ))

        return result

    @classmethod
    def generate_on_demand(
        cls,
        pending: 'PendingDocument'
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Génère un document à la demande (hors file d'attente).

        Contrairement à `generate_pending`, ne retire rien de la queue
        et logue l'action comme DOCUMENT_ON_DEMAND_GENERATED.

        Args:
            pending: Document à générer

        Returns:
            Tuple (success, message, file_path)
        """
        try:
            if pending.document_type == 'formation':
                return cls._extract_formation_pending(
                    pending,
                    remove_after=False,
                    action="DOCUMENT_FORMATION_ON_DEMAND",
                )

            success, msg, path = generate_filled_template(
                template_id=pending.template_id,
                operateur_nom=pending.operateur_nom,
                operateur_prenom=pending.operateur_prenom,
            )

            if success:
                log_hist(
                    "DOCUMENT_ON_DEMAND_GENERATED",
                    "documents_templates",
                    pending.template_id,
                    f"Document '{pending.template_nom}' généré à la demande pour "
                    f"{pending.operateur_prenom} {pending.operateur_nom}",
                    operateur_id=pending.operateur_id
                )
                logger.info(f"Document on-demand généré: {pending.template_nom} → {path}")

            return success, msg, path

        except Exception as e:
            logger.error(f"Erreur génération on-demand '{pending.template_nom}': {e}", exc_info=True)
            return False, str(e), None

    @classmethod
    def propose_for_polyvalences(
        cls,
        operateur_id: int,
        nom: str,
        prenom: str,
        polyvalences: list
    ) -> int:
        """
        Propose documents à la demande selon les polyvalences actuelles d'un opérateur.

        Pour chaque polyvalence, vérifie les règles configurées pour l'événement
        `polyvalence.niveau_X_reached` et `evaluation.completed` afin de proposer
        les documents correspondants au niveau et au poste.

        Args:
            operateur_id: ID de l'opérateur
            nom: Nom de l'opérateur
            prenom: Prénom de l'opérateur
            polyvalences: Liste de dicts avec clés: id, poste_id, poste_code, niveau

        Returns:
            Nombre de documents ajoutés à la file d'attente
        """
        from application.event_rule_service import get_matching_templates

        instance = cls()
        added = 0

        for poly in polyvalences:
            niveau = poly.get('niveau')
            poste_id = poly.get('poste_id')
            code_poste = poly.get('poste_code') or str(poste_id)

            event_data = {
                'operateur_id': operateur_id,
                'nom': nom,
                'prenom': prenom,
                'polyvalence_id': poly.get('id'),
                'poste_id': poste_id,
                'code_poste': code_poste,
                'niveau': niveau,
                'new_niveau': niveau,
            }

            added += cls.add_formation_docs_for_level(
                operateur_id,
                nom,
                prenom,
                poste_id,
                niveau,
                f'polyvalence.niveau_{niveau}_reached',
            )

            events_to_check = [
                f'polyvalence.niveau_{niveau}_reached',
                'evaluation.completed',
            ]

            for event_name in events_to_check:
                templates = get_matching_templates(event_name, event_data)
                templates = cls._with_niveau_3_poste_templates(event_name, event_data, templates)
                for tpl in templates:
                    instance._add_pending(tpl, operateur_id, nom, prenom, event_name)
                    added += 1

        logger.info(
            f"propose_for_polyvalences: {added} document(s) ajoutés pour "
            f"{prenom} {nom} ({len(polyvalences)} polyvalence(s))"
        )
        return added

    @classmethod
    def set_enabled(cls, enabled: bool):
        """
        Active ou désactive le service.

        Args:
            enabled: True pour activer, False pour désactiver
        """
        instance = cls()
        instance._enabled = enabled
        logger.info(f"DocumentTriggerService {'activé' if enabled else 'désactivé'}")

    @classmethod
    def is_enabled(cls) -> bool:
        """Retourne True si le service est activé."""
        return cls()._enabled
