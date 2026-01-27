# -*- coding: utf-8 -*-
"""
EventBus - Système de publication/souscription d'événements métier.

Ce module fournit un bus d'événements centralisé pour la communication
entre les différentes couches de l'application (repositories, services, UI).

Usage:
    from core.services.event_bus import EventBus

    # Émettre un événement
    EventBus.emit('personnel.created', {
        'operateur_id': 123,
        'nom': 'Dupont',
        'prenom': 'Jean'
    })

    # S'abonner à un événement
    def my_handler(event):
        print(f"Reçu: {event.name} avec {event.data}")

    EventBus.subscribe('personnel.created', my_handler)

    # S'abonner avec wildcard
    EventBus.subscribe('personnel.*', my_handler)  # Tous les événements personnel

Événements supportés:
    - personnel.created      : Nouvel employé créé
    - personnel.updated      : Employé modifié
    - personnel.deactivated  : Employé désactivé
    - personnel.reactivated  : Employé réactivé
    - contrat.created        : Nouveau contrat
    - contrat.renewed        : Contrat renouvelé
    - contrat.expiring_soon  : Contrat expirant bientôt
    - polyvalence.created    : Nouvelle affectation poste
    - polyvalence.niveau_changed    : Changement de niveau
    - polyvalence.niveau_3_reached  : Passage au niveau 3
    - evaluation.completed   : Évaluation terminée
    - evaluation.overdue     : Évaluation en retard
"""

import logging
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock

from PyQt5.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


@dataclass
class DomainEvent:
    """
    Représente un événement métier.

    Attributes:
        name: Nom de l'événement (ex: 'personnel.created')
        data: Dictionnaire de données contextuelles
        timestamp: Date/heure de l'événement
        source: Module émetteur (optionnel, pour debug)
    """
    name: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None

    def __repr__(self) -> str:
        return f"DomainEvent(name='{self.name}', data={self.data}, source={self.source})"


class EventSignals(QObject):
    """
    Signaux PyQt5 pour les événements.

    Permet une communication thread-safe avec l'UI.
    Les handlers connectés à ces signaux sont exécutés dans le thread principal Qt.
    """
    # Signal émis pour chaque événement (event_name, data_dict)
    event_emitted = pyqtSignal(str, dict)

    # Signaux spécifiques pour les événements courants (optionnel, pour typage fort)
    personnel_created = pyqtSignal(dict)
    personnel_updated = pyqtSignal(dict)
    contrat_created = pyqtSignal(dict)
    contrat_renewed = pyqtSignal(dict)
    polyvalence_created = pyqtSignal(dict)
    polyvalence_niveau_changed = pyqtSignal(dict)


class EventBus:
    """
    Bus d'événements centralisé (Singleton thread-safe).

    Supporte deux modes de souscription:
    1. Callbacks Python standard (pour services backend)
    2. Signaux PyQt5 (pour UI, garantit exécution dans le thread principal)

    Le bus maintient un historique des N derniers événements pour debug/audit.
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
        """Initialise l'instance (appelé une seule fois)."""
        self._subscribers: Dict[str, List[Callable]] = {}
        self._qt_signals = EventSignals()
        self._history: List[DomainEvent] = []
        self._max_history = 100
        self._enabled = True
        logger.info("EventBus initialisé")

    @classmethod
    def emit(cls, event_name: str, data: Dict[str, Any], source: str = None):
        """
        Émet un événement vers tous les souscripteurs.

        L'événement est:
        1. Ajouté à l'historique (buffer circulaire)
        2. Envoyé aux callbacks Python enregistrés
        3. Envoyé aux wildcards correspondants (ex: 'personnel.*')
        4. Émis via le signal Qt pour les handlers UI

        Args:
            event_name: Nom de l'événement (ex: 'personnel.created')
            data: Dictionnaire de données contextuelles
            source: Module émetteur (optionnel, pour traçabilité)

        Example:
            EventBus.emit('personnel.created', {
                'operateur_id': 123,
                'nom': 'Dupont',
                'prenom': 'Jean'
            }, source='PersonnelRepository.create')
        """
        instance = cls()

        if not instance._enabled:
            logger.debug(f"EventBus désactivé, événement ignoré: {event_name}")
            return

        event = DomainEvent(name=event_name, data=data, source=source)

        # Ajouter à l'historique (buffer circulaire)
        instance._history.append(event)
        if len(instance._history) > instance._max_history:
            instance._history.pop(0)

        logger.debug(f"EventBus: émission de '{event_name}' (source: {source})")

        # 1. Notifier les callbacks Python pour cet événement exact
        if event_name in instance._subscribers:
            for callback in instance._subscribers[event_name]:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Erreur dans handler '{event_name}': {e}", exc_info=True)

        # 2. Notifier les wildcards (ex: 'personnel.*' matche 'personnel.created')
        parts = event_name.split('.')
        if len(parts) > 1:
            wildcard = f"{parts[0]}.*"
            if wildcard in instance._subscribers:
                for callback in instance._subscribers[wildcard]:
                    try:
                        callback(event)
                    except Exception as e:
                        logger.error(f"Erreur dans handler wildcard '{wildcard}': {e}", exc_info=True)

        # 3. Notifier le wildcard global '*'
        if '*' in instance._subscribers:
            for callback in instance._subscribers['*']:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Erreur dans handler global '*': {e}", exc_info=True)

        # 4. Émettre le signal Qt (thread-safe pour UI)
        instance._qt_signals.event_emitted.emit(event_name, data)

        # 5. Émettre les signaux spécifiques si définis
        signal_map = {
            'personnel.created': instance._qt_signals.personnel_created,
            'personnel.updated': instance._qt_signals.personnel_updated,
            'contrat.created': instance._qt_signals.contrat_created,
            'contrat.renewed': instance._qt_signals.contrat_renewed,
            'polyvalence.created': instance._qt_signals.polyvalence_created,
            'polyvalence.niveau_changed': instance._qt_signals.polyvalence_niveau_changed,
        }
        if event_name in signal_map:
            signal_map[event_name].emit(data)

    @classmethod
    def subscribe(cls, event_name: str, callback: Callable[[DomainEvent], None]):
        """
        S'abonne à un événement.

        Args:
            event_name: Nom de l'événement ou pattern wildcard
                - 'personnel.created' : événement exact
                - 'personnel.*' : tous les événements personnel
                - '*' : tous les événements
            callback: Fonction à appeler, reçoit un DomainEvent

        Example:
            def on_personnel_created(event: DomainEvent):
                print(f"Nouvel employé: {event.data['nom']}")

            EventBus.subscribe('personnel.created', on_personnel_created)
        """
        instance = cls()
        if event_name not in instance._subscribers:
            instance._subscribers[event_name] = []

        if callback not in instance._subscribers[event_name]:
            instance._subscribers[event_name].append(callback)
            logger.debug(f"EventBus: souscription à '{event_name}'")

    @classmethod
    def unsubscribe(cls, event_name: str, callback: Callable = None):
        """
        Désabonne un callback d'un événement.

        Args:
            event_name: Nom de l'événement
            callback: Callback spécifique à retirer, ou None pour tous les retirer
        """
        instance = cls()
        if event_name in instance._subscribers:
            if callback is not None:
                try:
                    instance._subscribers[event_name].remove(callback)
                    logger.debug(f"EventBus: désabonnement de '{event_name}'")
                except ValueError:
                    pass  # Callback pas dans la liste
            else:
                del instance._subscribers[event_name]
                logger.debug(f"EventBus: tous les handlers de '{event_name}' retirés")

    @classmethod
    def get_qt_signals(cls) -> EventSignals:
        """
        Retourne les signaux Qt pour connexion UI.

        Utiliser ces signaux garantit que les handlers sont exécutés
        dans le thread principal Qt, ce qui est obligatoire pour les
        opérations UI.

        Example:
            EventBus.get_qt_signals().event_emitted.connect(self.on_event)
            EventBus.get_qt_signals().personnel_created.connect(self.on_new_employee)

        Returns:
            EventSignals: Objet contenant les signaux Qt
        """
        return cls()._qt_signals

    @classmethod
    def get_history(cls, event_name: str = None) -> List[DomainEvent]:
        """
        Retourne l'historique des événements récents.

        Args:
            event_name: Filtrer par nom d'événement (optionnel)

        Returns:
            Liste des DomainEvent récents (max 100)
        """
        instance = cls()
        if event_name:
            return [e for e in instance._history if e.name == event_name]
        return instance._history.copy()

    @classmethod
    def clear_history(cls):
        """Efface l'historique des événements."""
        cls()._history.clear()

    @classmethod
    def set_enabled(cls, enabled: bool):
        """
        Active ou désactive le bus d'événements.

        Utile pour les tests ou les opérations en batch où les événements
        ne doivent pas être émis.

        Args:
            enabled: True pour activer, False pour désactiver
        """
        instance = cls()
        instance._enabled = enabled
        logger.info(f"EventBus {'activé' if enabled else 'désactivé'}")

    @classmethod
    def is_enabled(cls) -> bool:
        """Retourne True si le bus est activé."""
        return cls()._enabled

    @classmethod
    def get_subscriber_count(cls, event_name: str = None) -> int:
        """
        Retourne le nombre de souscripteurs.

        Args:
            event_name: Nom de l'événement spécifique, ou None pour le total

        Returns:
            Nombre de souscripteurs
        """
        instance = cls()
        if event_name:
            return len(instance._subscribers.get(event_name, []))
        return sum(len(subs) for subs in instance._subscribers.values())
