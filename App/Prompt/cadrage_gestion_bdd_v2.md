# Cadrage fonctionnel — Évolution de l'onglet Gestion BDD

> Document de cadrage **fonctionnel** uniquement.
> Le *quoi* et le *pourquoi*, pas le *comment*.
> Les choix techniques (SQL, PyQt5, architecture) sont traités dans un document séparé.
>
> **Note de lecture** — Les sections sont pré-remplies à partir d'une exploration du code EMAC.
> Tout ce qui est entre `[À CONFIRMER]` ou `[À TRANCHER]` doit être validé par toi (ou avec l'utilisateur final / le tuteur) avant de figer le périmètre.

---

## 1. Contexte et déclencheur

### Situation actuelle

EMAC dispose déjà d'un onglet d'administration (`AdminDataPanelDialog`) qui regroupe les onglets suivants :

- **RH** : Ateliers, Services, Tranches d'âge, Motifs de sortie
- **Absences** : Types d'absence, Jours fériés, Solde congés, Demandes d'absence
- **Production** : Compétences (catalogue), Polyvalence (correction admin)
- **Documents** : Catégories, Règles événementielles documents (`document_event_rules`)
- **Système** : Rôles, Historique, Logs de connexion
- **Modules** : Activation/désactivation des modules de l'application

Pour chaque onglet, l'utilisateur peut aujourd'hui faire du CRUD basique : ajouter, modifier, supprimer.

### Limites concrètes constatées

1. **Pas de table `niveau_polyvalence`** — Les niveaux 1/2/3/4 sont définis comme un `Enum` Python (`NiveauPolyvalence` dans `domain/models.py`) et stockés en `INT` dans la table `polyvalence`. Impossible d'ajouter un niveau "Référent technique" sans modifier le code.

2. **Fréquences d'évaluation codées en dur** — Dans `gui/view_models/evaluation_view_model.py` :
   ```
   _JOURS_PAR_NIVEAU = {1: 30, 2: 30, 3: 3650, 4: 3650}
   ```
   La même logique est dupliquée dans `manage_operateur.py`, `historique_personnel.py`, `grilles_service.py`, `polyvalence_repo.py`. Toute modification de fréquence demande une intervention IT et une recompilation.

3. **Aiguillage des documents par `if/elif`** — Le code émet des événements `polyvalence.niveau_1_reached`, `polyvalence.niveau_2_reached`, etc. via une cascade `if nouveau_niveau == 1: ... elif == 2: ...`. Ajouter un nouveau niveau implique de modifier ce code à plusieurs endroits.

4. **Absence de champ `actif` sur `services` et `atelier`** — Ces deux tables n'ont actuellement que `id` + `nom`. Impossible de désactiver proprement un atelier obsolète, on est obligé de le supprimer (avec les casses de FK que ça implique) ou de le laisser tel quel.

5. **Pas d'analyse d'impact avant suppression** — Quand on supprime un atelier dans `AteliersTab`, l'utilisateur ne sait pas combien de postes y sont rattachés ni combien de salariés sont concernés.

6. **Historique partiel** — La table `historique` existe et trace les actions, mais elle ne stocke pas de manière structurée `ancienne_valeur` / `nouvelle_valeur` par champ. Difficile de répondre à "qui a changé quoi exactement le mois dernier ?".

### Pourquoi maintenant

`[À CONFIRMER]` — Quel événement précis a fait émerger ce besoin ?
Hypothèses possibles :
- Une demande utilisateur d'ajouter un nouveau niveau de polyvalence qui s'est heurtée à "il faut modifier le code"
- Un changement réglementaire sur les fréquences d'évaluation
- Un cas où une suppression a cassé l'historique d'un opérateur
- Une volonté générale de réduire la dette technique avant montée en charge

### Ce que ça doit résoudre

Permettre à un administrateur métier (sans intervention IT) de faire évoluer les référentiels de l'application — y compris ajouter de nouveaux niveaux de polyvalence, modifier des fréquences d'évaluation, gérer les documents associés à un événement métier — tout en garantissant la traçabilité et la cohérence des données existantes.

---

## 2. Objectif

### Énoncé en une phrase

Transformer l'onglet d'administration EMAC en back-office métier autonome, où un administrateur peut faire évoluer les référentiels et règles applicatives sans code, avec analyse d'impact préalable et historique complet.

### Critère de succès

`[À CONFIRMER]` — Propositions :
- **Cible mesurable** : Zéro intervention IT requise pour ajouter / modifier un niveau de polyvalence, une fréquence d'évaluation, un document associé, ou un type d'absence
- **Délai** : Une demande métier passe de "ticket IT + livraison + redéploiement" (plusieurs jours) à "5 minutes dans Gestion BDD"
- **Traçabilité** : 100% des modifications de référentiels sont retrouvables dans l'historique avec qui / quand / quoi / ancienne valeur

---

## 3. Utilisateurs et permissions

### Qui aura accès à Gestion BDD

Le système de rôles existe déjà (table `roles`) avec 3 rôles définis :

| Rôle | Description |
|------|-------------|
| `admin` | Administrateur — Accès complet à toutes les fonctionnalités |
| `gestion_production` | Accès aux évaluations et polyvalence (lecture seule sur les contrats) |
| `gestion_rh` | Accès aux contrats et documents administratifs (lecture seule sur la polyvalence) |

`AdminDataPanelDialog` filtre déjà via `is_admin()`. La V1 conserve cette restriction : **seul le rôle `admin` accède à Gestion BDD**.

### Granularité des droits

Le système de **features** (54 features dans la table `features`) permettrait théoriquement une granularité fine. Cependant, vu que Gestion BDD est un outil de configuration sensible :

`[À TRANCHER]`
- [ ] **Option A** — Tout `admin` peut tout faire dans Gestion BDD (simple, V1)
- [ ] **Option B** — Découpage par module : un admin RH gère les types d'absence, un admin production gère les niveaux et postes
- [ ] **Option C** — Granularité par feature (`admin.referentiel.niveaux.edit`, `admin.referentiel.documents.edit`, etc.)

**Recommandation V1** : Option A. La granularité fine peut venir en V2 si plusieurs personnes administrent simultanément.

### Cycle de validation

`[À TRANCHER]`
- [ ] Validation directe (modif → enregistrée → appliquée à la prochaine ouverture)
- [ ] Double validation pour les modifs critiques (désactivation impactant > N salariés)
- [ ] Validation systématique

**Recommandation V1** : Validation directe avec confirmation explicite (popup d'analyse d'impact). Le double-check humain peut venir en V2 si besoin.

---

## 4. Cas d'usage principaux

### Scénario 1 — Ajouter un nouveau niveau de polyvalence

> Marie, responsable production, veut introduire un niveau "Référent technique" entre les niveaux 3 (Confirmé) et 4 (Expert/Formateur), avec une réévaluation tous les 24 mois et un document d'attestation spécifique.

Déroulé attendu :
1. Marie ouvre Gestion BDD → onglet Production → Niveaux de polyvalence
2. Elle clique sur "Ajouter"
3. Elle saisit : nom = "Référent technique", code = 5, ordre d'affichage = 4 (entre Confirmé et Expert), couleur, description, fréquence d'évaluation = 24 mois
4. Onglet Relations : elle peut cocher les postes compatibles (optionnel à la création)
5. Onglet Documents : elle associe un template "Attestation référent technique" (option : créer le document plus tard)
6. Validation
7. Le lendemain, à la réouverture de l'app, le niveau 5 apparaît dans toutes les interfaces (saisie d'évaluation, grilles, statistiques)

### Scénario 2 — Modifier la fréquence d'évaluation d'un niveau existant

> Suite à un audit qualité, la fréquence d'évaluation du niveau "Autonome" (2) doit passer de 30 jours à 90 jours.

Déroulé attendu :
1. Marie ouvre Niveaux de polyvalence → niveau "Autonome" → Modifier
2. Onglet Général : elle change "Fréquence d'évaluation" : 30 → 90 jours
3. Onglet Impact (avant validation) : "47 salariés sont actuellement au niveau Autonome. Leur prochaine date d'évaluation a déjà été calculée selon l'ancienne règle (30 jours). Voulez-vous (a) ne rien faire pour les évaluations existantes, (b) recalculer les prochaines évaluations selon la nouvelle règle ?"
4. Marie choisit (a) — la nouvelle règle s'applique à partir des prochaines évaluations
5. Validation, historique tracé

### Scénario 3 — Désactiver un type d'absence avec impact

> L'entreprise abandonne le type d'absence "AUTRE" qui n'est plus conforme aux exigences de paie.

Déroulé attendu :
1. Patricia (admin RH) ouvre Types d'absence → "AUTRE"
2. Elle clique sur "Désactiver"
3. Onglet Impact : "12 demandes d'absence en cours utilisent ce type. 3 sont en attente de validation, 9 sont validées et futures. La désactivation empêchera de créer de nouvelles demandes mais conservera les existantes. Continuer ?"
4. Patricia confirme
5. Le type devient invisible dans le sélecteur de création d'absence, mais reste affiché en lecture pour les demandes existantes
6. Historique tracé

### Scénario 4 — Consulter l'historique d'une donnée

> Le directeur veut savoir qui a modifié le niveau "Confirmé" la semaine dernière et pourquoi.

Déroulé attendu :
1. Marie ouvre Niveaux de polyvalence → niveau "Confirmé" → onglet Historique
2. Liste chronologique : "23/04/2026 14:32 — Marie a modifié 'fréquence_evaluation' : 30 → 90 jours. Commentaire : audit qualité Q2"
3. Possibilité de filtrer par date, par utilisateur, par type d'action

### Scénario 5 — Réactiver un niveau désactivé par erreur

> Hier, un admin a désactivé par erreur le niveau "Apprentissage". Il faut le remettre.

Déroulé attendu :
1. Filtrer la liste sur "Inactifs uniquement" (toggle dans l'UI)
2. Cliquer sur le niveau "Apprentissage" → bouton "Réactiver"
3. Confirmation
4. Le niveau redevient disponible pour les nouvelles évaluations à la prochaine ouverture

### Scénario 6 — Modifier la règle de génération d'un document

> Quand un opérateur atteint le niveau 3, EMAC propose le "Questionnaire Qualité EMAC". L'entreprise veut que ce soit fait automatiquement (sans dialog) à partir de maintenant.

Déroulé attendu :
1. Patricia ouvre Documents → Règles événementielles
2. Cherche la règle `polyvalence.niveau_3_reached → Questionnaire Qualité EMAC`
3. Modifie le mode d'exécution : `PROPOSED` → `AUTO`
4. Onglet Impact : "Cette règle s'est déclenchée 23 fois sur les 6 derniers mois. Elle continuera de se déclencher selon les mêmes conditions, mais sans demander confirmation à l'utilisateur."
5. Validation

---

## 5. Périmètre fonctionnel

### Données concernées

Les référentiels gérables depuis Gestion BDD (basés sur les tabs existants + nouveaux) :

**Existants — à enrichir avec le nouveau pattern (fiche, relations, impact, historique)** :
- [x] Ateliers (`atelier`)
- [x] Services (`services`)
- [x] Postes (`postes`)
- [x] Compétences catalogue (`competences_catalogue`)
- [x] Types d'absence (`type_absence`)
- [x] Motifs de sortie (`ref_motif_sortie`)
- [x] Tranches d'âge (`tranche_age`)
- [x] Catégories de documents (`categories_documents`)
- [x] Jours fériés (`jours_feries`)
- [x] Règles événementielles documents (`document_event_rules`)

**À créer (n'existent pas encore en table)** :
- [ ] **Niveaux de polyvalence** — nouvelle table `niveau_polyvalence` (aujourd'hui c'est un `Enum` Python, c'est exactement le pilote)
- [ ] **Fréquences d'évaluation par niveau** — soit colonne dans `niveau_polyvalence`, soit table dédiée si la règle se complexifie

### Pilote V1 fortement recommandé

**Niveaux de polyvalence** — c'est le seul cas qui combine :
- Référentiel à créer de zéro (aucune table existante)
- Règles applicatives associées (fréquence d'évaluation, documents déclenchés)
- Hardcoding multiple à neutraliser dans le code (`if niveau == X` à 5+ endroits)
- Impact métier fort et visible (chaque salarié a au moins une polyvalence)

Si ce pilote tient, le pattern se réplique sur les autres référentiels.

### Ordre de priorité après le pilote

1. **Postes** — déjà avec FK vers atelier, nombreuses relations (polyvalence, plannings)
2. **Types d'absence** — relations avec demandes d'absence et soldes
3. **Compétences catalogue** — déjà bien structuré, faible risque
4. **Ateliers / Services** — ajouter d'abord le champ `actif`, puis le pattern
5. **Catégories documents** — ajouter le champ `actif`, puis le pattern
6. **Règles événementielles** — déjà éditables, à enrichir avec impact
7. **Tranches d'âge / Motifs de sortie / Jours fériés** — les plus simples, font du remplissage

### Règles applicatives configurables

Pour le pilote (Niveaux de polyvalence), ce qui est configurable :

- [x] Nom (ex: "Apprentissage", "Autonome", "Référent technique")
- [x] Code numérique (1, 2, 3, 4, 5...) ou code string (à arbitrer)
- [x] Ordre d'affichage
- [x] Description
- [x] Couleur (pour l'UI grilles/calendrier)
- [x] **Fréquence d'évaluation en jours** — actuellement codé en dur (`_JOURS_PAR_NIVEAU`)
- [x] **Documents associés** — via `document_event_rules` existant, nom de l'événement à générer (`polyvalence.niveau_X_reached`)
- [x] Statut actif/inactif
- [x] Postes compatibles (table de liaison `niveau_polyvalence_poste`)

### Ce qui reste figé dans le code

Pour rester maîtrisable, **ne jamais** rendre configurable :
- Le calcul du statut d'un opérateur (ACTIF/INACTIF)
- La structure des tables (pas de DDL depuis Gestion BDD, jamais)
- Les algorithmes de calcul de planning, de soldes congés
- La logique d'authentification et d'autorisation
- Le format des matricules, numéros de sécurité sociale, dates

### Actions disponibles dans l'interface

- [x] Consulter la liste avec filtre actif/inactif
- [x] Consulter une fiche détaillée (onglets Général / Relations / Impact / Historique)
- [x] Ajouter
- [x] Modifier
- [x] Désactiver (pas de suppression hard)
- [x] Réactiver
- [ ] Supprimer définitivement — **réservé V2 ou jamais**, à réfléchir

---

## 6. Contraintes et invariants métier

À ne jamais pouvoir violer, même en `admin` :

- [x] Il doit toujours exister **au moins un niveau de polyvalence actif** (sinon l'app ne peut plus créer d'évaluations)
- [x] Il doit toujours exister **au moins un type d'absence actif décompté du solde** (`decompte_solde=1`) — sinon plus possible de poser un congé
- [x] Un poste ne peut pas être désactivé s'il a des polyvalences en cours sans bloquer la possibilité de futures évaluations sur ce poste — `[À TRANCHER : empêcher la désactivation, ou désactiver et masquer les polyvalences associées ?]`
- [x] Un atelier ne peut pas être supprimé s'il a des postes liés (la FK `postes.atelier_id` existe déjà avec `ON DELETE SET NULL`, ce qui est dangereux pour la cohérence)
- [x] Le rôle `admin` doit toujours exister et avoir au moins un utilisateur affecté
- [x] Les catégories `categories_documents` avec `exige_date_expiration=1` ne doivent pas pouvoir basculer à `0` s'il existe des documents sans date d'expiration affectés à cette catégorie

### Comportement si l'admin tente de violer un invariant

Recommandation : **bouton grisé** + tooltip explicatif quand l'invariant est connu d'avance, **message d'erreur explicite** au moment de la validation pour les cas dynamiques (vérifiés au moment du clic).

---

## 7. Analyse d'impact et traçabilité

### Ce que l'utilisateur voit avant de valider

**V1 — compteurs simples** :
- "Cette modification affecte X salariés"
- "Y polyvalences en cours utilisent ce niveau"
- "Z documents générés par cette règle dans les 6 derniers mois"
- "W demandes d'absence en cours utilisent ce type"

**V2 — détail cliquable** : depuis chaque compteur, ouvrir la liste des éléments concernés (noms, références, dates).

### Niveau de détail de l'historique

La table `historique` existe déjà mais est insuffisamment structurée. Pour Gestion BDD, on a besoin de :

- [x] Qui (`utilisateur` — déjà présent)
- [x] Quand (`date_time` — déjà présent)
- [x] Quelle table (`table_name` — déjà présent)
- [x] Quel enregistrement (`record_id` — déjà présent)
- [x] Type d'action (`action` — déjà présent, à standardiser : CREATE / UPDATE / DEACTIVATE / REACTIVATE / RELATION_ADD / RELATION_REMOVE / RULE_CHANGE)
- [ ] **Champ modifié** (à ajouter)
- [ ] **Ancienne valeur** (à ajouter)
- [ ] **Nouvelle valeur** (à ajouter)
- [ ] **Commentaire libre** (optionnel mais utile pour l'audit qualité)

`[À TRANCHER]` Modifier la table `historique` existante ou créer une table `audit_referentiel` dédiée à Gestion BDD. La seconde option évite de polluer l'historique métier (qui trace déjà les actions sur les opérateurs) avec les modifs de configuration.

### Durée de conservation de l'historique

`[À CONFIRMER]` — Pour les modifications de référentiels, je recommande **conservation indéfinie** (faible volume, fort intérêt en cas d'audit). Pour comparaison, la table `logs_connexion` peut avoir une rotation plus courte.

---

## 8. Communication des modifications

### Pour quelles modifs ?

`[À TRANCHER]`
- [ ] **Option A** — Aucune notification (juste tracé)
- [ ] **Option B** — Notification uniquement pour les modifs critiques : désactivation impactant > N salariés, changement de mode AUTO/PROPOSED sur une règle de document
- [ ] **Option C** — Toutes les modifs

**Recommandation V1** : Option A (simplicité, l'historique est consultable). Option B en V2 si besoin.

### Qui est destinataire (si Option B)

`[À CONFIRMER]` — Possibles : tous les admins, le dirigeant, le service RH selon le module touché.

### Quel canal

`[À CONFIRMER]` — Pas de mail dans la V1 (EMAC est une app desktop, pas de SMTP configuré actuellement). Une notification interne dans l'app pourrait apparaître au prochain démarrage des autres admins.

---

## 9. Prise en compte des modifications

### Quand les changements deviennent visibles

EMAC est une **app desktop multi-utilisateurs** connectée à un MariaDB partagé. Les autres utilisateurs n'ont pas la modif tant que leur app n'a pas rechargé ses caches.

**V1 recommandée** :
- L'admin qui fait la modif voit immédiatement le résultat (rafraîchissement de sa propre vue)
- Les autres utilisateurs voient la modif **à la prochaine ouverture** de leur application
- **Bouton "Recharger les référentiels"** disponible dans le menu pour les utilisateurs qui veulent forcer la mise à jour sans redémarrer

`[À CONFIRMER]` — Faut-il pousser la modif via un mécanisme actif (polling, signal) ? Le code expose déjà un `EventBus` mais il est intra-process. Un mécanisme cross-process nécessiterait un canal supplémentaire (table `notifications_pending` polled toutes les N secondes par chaque client par exemple). À éviter en V1.

### Gestion des conflits

Cas : deux admins ouvrent la même fiche en même temps et modifient des choses différentes.

`[À TRANCHER]`
- [ ] **Option A** — Le dernier qui enregistre gagne (silencieux). Risque : modifications perdues sans le savoir.
- [ ] **Option B** — Verrouillage optimiste : avant validation, l'app vérifie que la fiche n'a pas changé depuis l'ouverture. Si oui, message "La fiche a été modifiée par X à HH:MM. Vos changements n'ont pas été appliqués. Recharger ?"
- [ ] **Option C** — Verrouillage pessimiste : la fiche est en lecture seule pour les autres admins tant qu'elle est ouverte par quelqu'un.

**Recommandation V1** : Option B (verrouillage optimiste via une colonne `version` ou `date_modification` sur chaque table de référentiel). Option C est plus sûre mais plus complexe à implémenter (gestion des locks orphelins si un admin crashe).

---

## 10. Hors périmètre

### Ce que Gestion BDD ne fera jamais

- **Pas de DDL** (CREATE / ALTER / DROP TABLE) — jamais, même en V3. Le besoin se traite par tables `custom_fields` si nécessaire.
- **Pas de gestion des comptes utilisateurs** — déjà fait dans `user_management.py`, accessible via le même menu admin mais distinct
- **Pas de gestion des permissions / features** — déjà fait dans `permission_manager.py` et la fenêtre dédiée
- **Pas de modification de plannings, polyvalences, contrats, demandes d'absence existants** — Gestion BDD touche aux **référentiels**, pas aux **données opérationnelles**
- **Pas de remplacement de l'accès DBA pour la maintenance** — sauvegardes, migrations, restaurations restent en dehors

### Repoussé à plus tard mais possible

**V2 envisagée** :
- Granularité fine des permissions Gestion BDD (par module ou par feature)
- Notifications inter-utilisateurs des modifications
- Détail cliquable des compteurs d'impact
- Bouton "Recharger les référentiels" dans le menu utilisateur
- Annulation d'une modification (rollback ciblé depuis l'historique)
- Édition en lot (ex: désactiver 10 motifs de sortie d'un coup)

**V3 envisagée** :
- Champs personnalisés sans DDL (tables `custom_fields` + `custom_field_values`)
- Workflow de double validation pour les modifs critiques
- Versioning complet d'un référentiel (snapshots + restauration)
- Export/import d'un référentiel (utile pour migration entre environnements)

---

## 11. Questions ouvertes

| # | Question | À valider avec | Échéance |
|---|----------|----------------|----------|
| 1 | Quel est l'événement déclencheur précis du besoin ? | Utilisateur final / dirigeant | Avant de coder |
| 2 | Granularité des droits : tout admin ou découpage RH/Production ? | Utilisateur final | Avant V1 |
| 3 | Cycle de validation : direct ou double ? | Utilisateur final | Avant V1 |
| 4 | Quand on change la fréquence d'évaluation, faut-il recalculer les prochaines évals existantes ou pas ? | Utilisateur final + responsable production | Pendant le scénario 2 |
| 5 | Désactivation d'un poste utilisé : bloquer ou propager sur les polyvalences ? | Responsable production | Avant V1 |
| 6 | Modifier la table `historique` existante ou créer une table dédiée `audit_referentiel` ? | Toi (choix technique) | Phase de conception |
| 7 | Suppression définitive d'un référentiel : possible (V2/V3) ou jamais ? | Utilisateur final + DPO si données personnelles | V2 |
| 8 | Notification des autres utilisateurs : utile dès la V1 ou plus tard ? | Utilisateur final | Avant V1 |
| 9 | Gestion des conflits : optimiste (recommandé) ou pessimiste ? | Toi (choix technique) | Phase de conception |
| 10 | Quelle durée de conservation de l'historique des modifications ? | Utilisateur final + obligations légales | Avant V1 |

---

## Annexes

### Inventaire des hardcoding détectés à neutraliser

À traiter dans le pilote "Niveaux de polyvalence" :

| Fichier | Ligne(s) | Pattern |
|---------|----------|---------|
| `gui/view_models/evaluation_view_model.py` | 39, 168, 211 | `_JOURS_PAR_NIVEAU = {1: 30, 2: 30, 3: 3650, 4: 3650}` |
| `gui/view_models/evaluation_view_model.py` | 161 | `if nouveau_niveau not in [1, 2, 3, 4]` |
| `gui/view_models/evaluation_view_model.py` | 276-296 | Cascade `if nouveau_niveau == 1 / 2 / 3 / 4` pour émettre les events |
| `gui/screens/personnel/manage_operateur.py` | 96-101 | Calcul de `jours` selon niveau hardcodé |
| `gui/screens/personnel/historique_personnel.py` | 484-493 | Mapping niveau → libellé hardcodé |
| `domain/services/formation/grilles_service.py` | 316-336 | Cascade hardcodée |
| `domain/repositories/polyvalence_repo.py` | 383+ | Cascade hardcodée |
| `domain/models.py` | `NiveauPolyvalence` Enum | À conserver pour compat mais alimenté depuis la DB |

### Glossaire métier

- **Polyvalence** : capacité d'un opérateur à tenir un poste donné, évaluée à un niveau (1 à 4 actuellement)
- **Niveau** : degré de maîtrise d'un opérateur sur un poste (Apprentissage, Autonome, Confirmé, Expert/Formateur)
- **Évaluation** : événement périodique où un opérateur est noté sur un poste, et où sa prochaine évaluation est planifiée
- **Atelier / Service** : regroupements organisationnels — atelier = unité de production, service = unité administrative ou technique
- **Document event rule** : règle qui dit "quand l'événement X se produit, proposer/générer automatiquement le template Y"
