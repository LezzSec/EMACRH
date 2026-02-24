# -*- coding: utf-8 -*-
"""
Service de gestion des règles d'événements documents.

Ce service charge les règles depuis la table `document_event_rules`
et retourne les templates à générer pour un événement donné.

Usage:
    from core.services.event_rule_service import get_matching_templates

    # Obtenir les templates pour un événement
    templates = get_matching_templates('personnel.created', {
        'operateur_id': 123,
        'nom': 'Dupont',
        'prenom': 'Jean'
    })

    for t in templates:
        print(f"Template: {t['template_nom']} (mode: {t['execution_mode']})")
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from core.db.query_executor import QueryExecutor
from core.utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class EventRule:
    """
    Représente une règle événement -> template.

    Attributes:
        id: ID de la règle
        event_name: Nom de l'événement déclencheur
        template_id: ID du template à générer
        template_nom: Nom du template (pour affichage)
        execution_mode: 'AUTO', 'PROPOSED', ou 'SILENT'
        condition_json: Conditions additionnelles (dict ou None)
        priority: Ordre de traitement (0 = premier)
    """
    id: int
    event_name: str
    template_id: int
    template_nom: str
    execution_mode: str
    condition_json: Optional[Dict]
    priority: int


def check_event_rules_table_exists() -> bool:
    """
    Vérifie si la table document_event_rules existe.

    Returns:
        True si la table existe, False sinon
    """
    try:
        count = QueryExecutor.fetch_scalar("""
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_schema = DATABASE()
            AND table_name = 'document_event_rules'
        """, default=0)
        return count > 0
    except Exception:
        return False


def get_rules_for_event(event_name: str) -> List[EventRule]:
    """
    Récupère toutes les règles actives pour un événement.

    Args:
        event_name: Nom de l'événement (ex: 'personnel.created')

    Returns:
        Liste des EventRule triées par priorité

    Example:
        rules = get_rules_for_event('personnel.created')
        for rule in rules:
            print(f"Rule {rule.id}: template={rule.template_nom}")
    """
    if not check_event_rules_table_exists():
        logger.warning("Table document_event_rules n'existe pas")
        return []

    query = """
        SELECT
            r.id,
            r.event_name,
            r.template_id,
            t.nom as template_nom,
            r.execution_mode,
            r.condition_json,
            r.priority
        FROM document_event_rules r
        JOIN documents_templates t ON r.template_id = t.id
        WHERE r.event_name = %s
          AND r.actif = TRUE
          AND t.actif = TRUE
        ORDER BY r.priority ASC
    """

    try:
        rows = QueryExecutor.fetch_all(query, (event_name,), dictionary=True)
    except Exception as e:
        logger.error(f"Erreur lecture règles pour '{event_name}': {e}")
        return []

    rules = []
    for row in rows:
        condition = None
        if row['condition_json']:
            try:
                if isinstance(row['condition_json'], str):
                    condition = json.loads(row['condition_json'])
                else:
                    # MySQL retourne déjà un dict pour les colonnes JSON
                    condition = row['condition_json']
            except json.JSONDecodeError as e:
                logger.warning(f"Condition JSON invalide pour règle {row['id']}: {e}")

        rules.append(EventRule(
            id=row['id'],
            event_name=row['event_name'],
            template_id=row['template_id'],
            template_nom=row['template_nom'],
            execution_mode=row['execution_mode'],
            condition_json=condition,
            priority=row['priority']
        ))

    logger.debug(f"Trouvé {len(rules)} règle(s) pour '{event_name}'")
    return rules


def evaluate_condition(condition: Optional[Dict], event_data: Dict) -> bool:
    """
    Évalue si une condition est satisfaite par les données de l'événement.

    Conditions supportées:
        - Égalité simple: {"niveau": 3}
            → event_data['niveau'] == 3

        - Opérateur gte (>=): {"niveau": {"gte": 3}}
            → event_data['niveau'] >= 3

        - Opérateur lte (<=): {"niveau": {"lte": 2}}
            → event_data['niveau'] <= 2

        - Opérateur eq (==): {"type": {"eq": "CDD"}}
            → event_data['type'] == 'CDD'

        - Opérateur in (liste): {"type_contrat": {"in": ["CDD", "CDI"]}}
            → event_data['type_contrat'] in ['CDD', 'CDI']

        - Liste de postes: {"postes": ["506", "507"]}
            → event_data['code_poste'] in ["506", "507"]
            (cas spécial pour les templates liés à des postes)

    Args:
        condition: Dictionnaire de conditions ou None
        event_data: Données de l'événement

    Returns:
        True si toutes les conditions sont satisfaites (ou si condition is None)

    Example:
        # Condition simple
        evaluate_condition({"niveau": 3}, {"niveau": 3})  # True
        evaluate_condition({"niveau": 3}, {"niveau": 2})  # False

        # Condition avec opérateur
        evaluate_condition({"niveau": {"gte": 3}}, {"niveau": 4})  # True
    """
    if not condition:
        return True

    for key, expected in condition.items():
        # Cas spécial: postes (comparaison avec code_poste de l'événement)
        if key == 'postes':
            code_poste = event_data.get('code_poste') or event_data.get('numposte')
            if code_poste is None:
                # Pas de poste dans l'événement, condition non applicable
                continue

            # Normaliser: supprimer les zéros initiaux pour comparaison
            # (postes table: "0506", templates: "506" → les deux → "506")
            def _normalize_code(c):
                s = str(c).lstrip('0')
                return s if s else str(c)

            code_poste_norm = _normalize_code(code_poste)

            # expected peut être une string JSON ou une liste
            if isinstance(expected, str):
                try:
                    expected = json.loads(expected)
                except json.JSONDecodeError:
                    expected = [expected]

            if isinstance(expected, list):
                expected_norm = [_normalize_code(e) for e in expected]
                if code_poste_norm not in expected_norm:
                    logger.debug(f"Condition postes non satisfaite: {code_poste_norm} not in {expected_norm}")
                    return False
            continue

        actual = event_data.get(key)

        if isinstance(expected, dict):
            # Opérateurs complexes
            if 'gte' in expected:
                if actual is None or actual < expected['gte']:
                    logger.debug(f"Condition gte non satisfaite: {actual} < {expected['gte']}")
                    return False

            if 'lte' in expected:
                if actual is None or actual > expected['lte']:
                    logger.debug(f"Condition lte non satisfaite: {actual} > {expected['lte']}")
                    return False

            if 'eq' in expected:
                if actual != expected['eq']:
                    logger.debug(f"Condition eq non satisfaite: {actual} != {expected['eq']}")
                    return False

            if 'in' in expected:
                if actual not in expected['in']:
                    logger.debug(f"Condition in non satisfaite: {actual} not in {expected['in']}")
                    return False

            if 'not_in' in expected:
                if actual in expected['not_in']:
                    logger.debug(f"Condition not_in non satisfaite: {actual} in {expected['not_in']}")
                    return False

        else:
            # Égalité simple
            if actual != expected:
                logger.debug(f"Condition égalité non satisfaite: {actual} != {expected}")
                return False

    return True


def get_matching_templates(event_name: str, event_data: Dict) -> List[Dict]:
    """
    Retourne les templates à générer pour un événement,
    après évaluation des conditions.

    C'est la fonction principale à utiliser pour déterminer quels
    documents doivent être générés suite à un événement.

    Args:
        event_name: Nom de l'événement (ex: 'personnel.created')
        event_data: Données contextuelles de l'événement

    Returns:
        Liste de dictionnaires avec:
            - template_id: ID du template
            - template_nom: Nom affiché
            - execution_mode: 'AUTO', 'PROPOSED', ou 'SILENT'
            - rule_id: ID de la règle ayant matché

    Example:
        templates = get_matching_templates('personnel.created', {
            'operateur_id': 123,
            'nom': 'Dupont',
            'prenom': 'Jean'
        })

        for t in templates:
            if t['execution_mode'] == 'AUTO':
                generate_template(t['template_id'])
            elif t['execution_mode'] == 'PROPOSED':
                add_to_pending(t)
    """
    rules = get_rules_for_event(event_name)
    matching = []

    for rule in rules:
        if evaluate_condition(rule.condition_json, event_data):
            matching.append({
                'template_id': rule.template_id,
                'template_nom': rule.template_nom,
                'execution_mode': rule.execution_mode,
                'rule_id': rule.id
            })
            logger.debug(f"Règle {rule.id} match: template '{rule.template_nom}'")
        else:
            logger.debug(f"Règle {rule.id} ignorée (condition non satisfaite)")

    logger.info(f"get_matching_templates('{event_name}'): {len(matching)} template(s)")
    return matching


def get_all_event_names() -> List[str]:
    """
    Retourne la liste de tous les noms d'événements configurés.

    Returns:
        Liste des noms d'événements uniques
    """
    if not check_event_rules_table_exists():
        return []

    try:
        rows = QueryExecutor.fetch_all("""
            SELECT DISTINCT event_name
            FROM document_event_rules
            WHERE actif = TRUE
            ORDER BY event_name
        """, dictionary=True)
        return [row['event_name'] for row in rows]
    except Exception as e:
        logger.error(f"Erreur lecture noms d'événements: {e}")
        return []


def get_rules_summary() -> List[Dict]:
    """
    Retourne un résumé de toutes les règles pour affichage admin.

    Returns:
        Liste de dictionnaires avec infos règle + template
    """
    if not check_event_rules_table_exists():
        return []

    try:
        return QueryExecutor.fetch_all("""
            SELECT
                r.id,
                r.event_name,
                r.execution_mode,
                r.priority,
                r.actif,
                r.description,
                t.nom as template_nom,
                t.contexte as template_contexte
            FROM document_event_rules r
            JOIN documents_templates t ON r.template_id = t.id
            ORDER BY r.event_name, r.priority
        """, dictionary=True)
    except Exception as e:
        logger.error(f"Erreur lecture résumé règles: {e}")
        return []


def create_rule(
    event_name: str,
    template_id: int,
    execution_mode: str = 'PROPOSED',
    condition_json: Optional[Dict] = None,
    priority: int = 0,
    description: str = None
) -> tuple:
    """
    Crée une nouvelle règle événement → template.

    Args:
        event_name: Nom de l'événement déclencheur
        template_id: ID du template à générer
        execution_mode: 'AUTO', 'PROPOSED', ou 'SILENT'
        condition_json: Conditions additionnelles (dict ou None)
        priority: Ordre de traitement (0 = premier)
        description: Description de la règle

    Returns:
        (succès, message, rule_id)
    """
    if not event_name or not event_name.strip():
        return False, "L'événement déclencheur est obligatoire", None

    if execution_mode not in ('AUTO', 'PROPOSED', 'SILENT'):
        return False, f"Mode d'exécution invalide: {execution_mode}", None

    try:
        condition_str = json.dumps(condition_json) if condition_json else None

        rule_id = QueryExecutor.execute_write(
            """INSERT INTO document_event_rules
               (event_name, template_id, execution_mode, condition_json, priority, actif, description)
               VALUES (%s, %s, %s, %s, %s, TRUE, %s)""",
            (event_name.strip(), template_id, execution_mode, condition_str, priority, description)
        )

        from core.services.logger import log_hist
        log_hist(
            action="CREATION_REGLE_EVENEMENT",
            table_name="document_event_rules",
            record_id=rule_id,
            description=f"Règle '{event_name}' → template #{template_id} ({execution_mode})"
        )

        return True, "Règle créée avec succès", rule_id

    except Exception as e:
        logger.exception(f"Erreur création règle: {e}")
        if "Duplicate entry" in str(e):
            return False, "Cette règle existe déjà (même événement + template)", None
        return False, "Erreur lors de la création de la règle", None
