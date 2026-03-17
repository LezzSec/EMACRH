# Analyse : Fonctionnalités RH manquantes dans EMAC

## État actuel de l'application

### ✅ Fonctionnalités existantes
- ✅ Gestion du personnel (ajout, modification, statut ACTIF/INACTIF)
- ✅ Matricules automatiques pour le personnel de production
- ✅ Polyvalence et compétences par poste
- ✅ Évaluations et planification (dates, niveaux 1-4)
- ✅ Postes et ateliers
- ✅ Historique des actions
- ✅ Listes et grilles de compétences
- ✅ Planning (module existant)
- ✅ Gestion des contrats (table existe mais vide)
- ✅ Gestion des documents (table + vues)
- ✅ Gestion des formations (table existe mais vide)

### Tables existantes mais non utilisées
- ⚠️ `contrat` (0 enregistrements)
- ⚠️ `formation` (0 enregistrements)
- ⚠️ `documents` (probablement peu utilisé)
- ⚠️ `personnel_infos` (informations complémentaires)
- ⚠️ `declaration` (usage inconnu)
- ⚠️ `services` (départements/services)
- ⚠️ `tranche_age` (statistiques démographiques)

---

## FONCTIONNALITÉS RH CRITIQUES MANQUANTES

### 1. **GESTION DES ABSENCES ET CONGÉS** ⭐⭐⭐
**Priorité : CRITIQUE**

**Manque actuel :**
- Aucun système de demande de congés
- Pas de suivi des absences (maladie, CP, RTT, sans solde)
- Pas de calendrier des absences
- Pas de validation hiérarchique
- Pas de calcul de soldes de congés

**À implémenter :**
```
- Module de demande de congés (formulaire)
- Workflow de validation (N+1, RH)
- Calendrier visuel des absences d'équipe
- Calcul automatique des soldes (CP, RTT)
- Export pour la paie
- Alertes pour les absences qui se chevauchent
- Statistiques d'absentéisme
```

**Impact :** Sans cela, impossible de gérer les plannings réels et les remplacements.

---

### 2. **GESTION DE LA PAIE ET RÉMUNÉRATION** ⭐⭐⭐
**Priorité : CRITIQUE**

**Manque actuel :**
- Aucune information salariale
- Pas de gestion des heures travaillées
- Pas de calcul d'heures supplémentaires
- Pas de primes/indemnités
- Pas de gestion des acomptes

**À implémenter :**
```
- Table 'salaire' (salaire_base, primes, indemnités)
- Gestion des heures (pointage, heures sup, nuit, weekend)
- Calcul automatique de la paie mensuelle
- Historique des augmentations
- Export vers logiciel de paie
- Gestion des avances/acomptes
- Bulletins de paie (génération PDF)
```

**Impact :** Essentiel pour les RH et la comptabilité.

---

### 3. **RECRUTEMENT ET ONBOARDING** ⭐⭐
**Priorité : HAUTE**

**Manque actuel :**
- Pas de gestion des candidatures
- Pas de suivi des entretiens
- Pas de process d'intégration
- Pas de période d'essai

**À implémenter :**
```
- Module de recrutement :
  - Offres d'emploi
  - Candidatures (CV, lettres)
  - Planning d'entretiens
  - Évaluation des candidats
  - Statuts (présélectionné, refusé, embauché)

- Module onboarding :
  - Checklist d'intégration
  - Documents à fournir
  - Formations obligatoires
  - Période d'essai et évaluations
  - Parrain/tuteur
```

**Impact :** Améliore la qualité du recrutement et l'intégration.

---

### 4. **ENTRETIENS ANNUELS ET OBJECTIFS** ⭐⭐
**Priorité : HAUTE**

**Manque actuel :**
- Pas de gestion des entretiens annuels
- Pas de fixation d'objectifs
- Pas de suivi de performance individuelle
- Pas d'évaluation 360°

**À implémenter :**
```
- Entretiens annuels :
  - Planification automatique (dates anniversaires)
  - Formulaires d'évaluation personnalisables
  - Objectifs SMART (Spécifiques, Mesurables, etc.)
  - Bilan de compétences
  - Plan de développement personnel
  - Signature électronique

- Suivi de performance :
  - KPI par personne
  - Tableaux de bord
  - Évolution dans le temps
```

**Impact :** Obligatoire légalement et améliore l'engagement.

---

### 5. **GESTION DES TEMPS ET ACTIVITÉS** ⭐⭐
**Priorité : HAUTE**

**Manque actuel :**
- Pas de pointage/badgeage
- Pas de gestion des horaires variables
- Pas de suivi temps réel vs théorique
- Pas de gestion du télétravail

**À implémenter :**
```
- Pointage :
  - Badgeage entrée/sortie
  - Import depuis système de pointage
  - Anomalies de pointage
  - Régularisation

- Horaires :
  - Horaires théoriques par personne
  - Horaires flexibles/variables
  - Astreintes
  - Télétravail (jours autorisés)

- Reporting :
  - Heures travaillées par mois
  - Écarts théorique/réel
  - Heures supplémentaires
```

**Impact :** Essentiel pour la paie et le respect du droit du travail.

---

### 6. **GESTION DES FORMATIONS (amélioration)** ⭐⭐
**Priorité : MOYENNE**

**Manque actuel :**
- Table `formation` existe mais vide
- Pas de plan de formation
- Pas de budget formation
- Pas de suivi des certifications

**À implémenter :**
```
- Catalogue de formations
- Demandes de formation (salarié/manager)
- Plan de formation annuel
- Budget et coûts
- Prestataires/organismes
- Certifications et renouvellements
- Bilan de compétences post-formation
- Évaluation à chaud/à froid
- Attestations et diplômes
```

**Impact :** Développement des compétences et conformité CPF.

---

### 7. **GESTION DES CONTRATS (amélioration)** ⭐⭐
**Priorité : MOYENNE**

**Manque actuel :**
- Table `contrat` existe mais vide (0 enregistrements)
- Interface existe ([contract_management.py](App/core/gui/contract_management.py))
- Pas de workflow de renouvellement

**À implémenter :**
```
- Saisie des contrats :
  - Type (CDI, CDD, intérim, apprentissage, stage)
  - Dates début/fin
  - Durée hebdomadaire
  - Coefficient
  - Avenants

- Alertes automatiques :
  - Fins de CDD approchantes (30/60/90 jours)
  - Périodes d'essai
  - Renouvellements

- Génération de contrats (modèles Word/PDF)
- Historique des contrats par personne
```

**Impact :** Conformité légale et gestion administrative.

---

### 8. **GESTION DES DOCUMENTS RH** ⭐
**Priorité : MOYENNE**

**Manque actuel :**
- Tables existent (`documents`, vues) mais peu utilisé
- Pas de GED (Gestion Électronique des Documents)
- Pas de signature électronique
- Pas de gestion des versions

**À implémenter :**
```
- Upload de documents :
  - CV
  - Diplômes et certifications
  - Pièces d'identité
  - Attestations (IBAN, mutuelle, etc.)
  - Contrats signés
  - Bulletins de paie

- Catégorisation et recherche
- Dates d'expiration (permis, habilitations)
- Alertes de renouvellement
- Droits d'accès (confidentialité)
- Archivage légal (5/10 ans)
- Signature électronique
```

**Impact :** Dématérialisation et gain de temps.

---

### 9. **ORGANIGRAMME ET STRUCTURE** ⭐
**Priorité : MOYENNE**

**Manque actuel :**
- Pas de hiérarchie N+1
- Pas d'organigramme visuel
- Table `services` existe mais pas utilisée
- Pas de gestion des équipes

**À implémenter :**
```
- Structure hiérarchique :
  - Manager (N+1)
  - Service/Département
  - Équipe
  - Direction

- Organigramme visuel interactif
- Fiches de poste
- Effectifs par service
- Budgets par département
- Workflow de validation basé sur hiérarchie
```

**Impact :** Clarté organisationnelle et workflows.

---

### 10. **DOSSIER MÉDICAL ET SANTÉ** ⭐
**Priorité : BASSE (mais légalement sensible)**

**Manque actuel :**
- Aucune donnée médicale
- Pas de suivi des visites médicales
- Pas de gestion des accidents du travail
- Pas de restrictions médicales

**À implémenter :**
```
- Visites médicales :
  - Visite d'embauche
  - Visites périodiques
  - Visites de reprise
  - Alertes de planification

- Restrictions et aptitudes :
  - Port de charges
  - Travail en hauteur
  - Travail de nuit
  - Restrictions temporaires

- Accidents du travail :
  - Déclaration
  - Suivi
  - Jours d'arrêt
  - Statistiques

⚠️ ATTENTION : Données sensibles RGPD !
```

**Impact :** Conformité médecine du travail.

---

### 11. **NOTES DE FRAIS** ⭐
**Priorité : BASSE**

**Manque actuel :**
- Aucun système de notes de frais
- Pas de remboursements

**À implémenter :**
```
- Saisie de notes de frais :
  - Déplacements (km, péages)
  - Repas
  - Hébergement
  - Fournitures

- Workflow de validation
- Export comptable
- Barèmes et plafonds
- Justificatifs (photos)
```

**Impact :** Confort pour les salariés et comptabilité.

---

### 12. **STATISTIQUES ET REPORTING RH** ⭐⭐
**Priorité : MOYENNE**

**Manque actuel :**
- Peu de tableaux de bord RH
- Pas de pyramide des âges (table `tranche_age` existe)
- Pas de turn-over
- Pas de bilan social

**À implémenter :**
```
- KPI RH :
  - Effectif (CDI/CDD/Intérim)
  - Pyramide des âges
  - Ancienneté moyenne
  - Turn-over
  - Absentéisme
  - Heures de formation
  - Coût salarial

- Tableaux de bord visuels
- Export Excel/PDF
- Bilan social annuel
- Alertes sur indicateurs critiques
```

**Impact :** Pilotage RH et décisions stratégiques.

---

## TABLEAU RÉCAPITULATIF PAR PRIORITÉ

### ⭐⭐⭐ CRITIQUE (à implémenter en priorité)
1. **Gestion des absences et congés** - Bloquant pour planning
2. **Gestion de la paie** - Essentiel administratif

### ⭐⭐ HAUTE
3. **Recrutement et onboarding** - Améliore qualité embauche
4. **Entretiens annuels** - Obligation légale
5. **Gestion des temps** - Nécessaire pour paie
6. **Formations (amélioration)** - Développement compétences
7. **Contrats (amélioration)** - Conformité légale

### ⭐ MOYENNE/BASSE
8. **Documents RH** - Dématérialisation
9. **Organigramme** - Clarté structure
10. **Santé/médical** - Conformité (RGPD sensible)
11. **Notes de frais** - Confort
12. **Reporting RH** - Pilotage

---

## RECOMMANDATIONS D'IMPLÉMENTATION

### Phase 1 : Fondamentaux (3-6 mois)
- ✅ Gestion des absences/congés
- ✅ Gestion des contrats (compléter)
- ✅ Gestion des temps de base

### Phase 2 : Développement (6-12 mois)
- ✅ Paie et rémunération
- ✅ Entretiens annuels
- ✅ Formations (compléter)
- ✅ Recrutement

### Phase 3 : Optimisation (12-24 mois)
- ✅ Documents RH (GED)
- ✅ Organigramme
- ✅ Reporting avancé
- ✅ Notes de frais

### Phase 4 : Spécialisé (si nécessaire)
- ✅ Médical/santé (RGPD)
- ✅ Intégrations externes (paie, pointage)

---

## BONUS : Fonctionnalités modernes

### Digitales
-  Application mobile (congés, pointage)
-  Notifications push
-  Signature électronique
-  Chatbot RH (FAQ)
-  Dashboards temps réel

### Collaboratives
-  Communication interne (messagerie)
-  Annuaire d'entreprise
-  OKR (Objectives and Key Results)
-  Reconnaissance entre pairs
-  Feedback continu

### Analytiques
-  Prédiction de turn-over (IA)
-  Analyse des compétences manquantes
-  Recommandations de formation
-  Simulation budgétaire

---

## ASPECTS LÉGAUX À CONSIDÉRER

-  **RGPD** : Données personnelles, droit à l'oubli, consentement
-  **Code du travail** : Durée du travail, congés, entretiens
-  **Médecine du travail** : Visites obligatoires
-  **URSSAF** : Déclarations sociales
-  **Bilan social** : Obligatoire si > 300 salariés
-  **Sécurité** : Données sensibles (santé, salaires)

---

## CONCLUSION

L'application EMAC est **excellente pour la gestion des compétences et polyvalences**, mais il manque les **modules RH administratifs essentiels** :

**Top 3 priorités :**
1.  **Absences/Congés** - Bloquant pour planning réel
2.  **Paie/Rémunération** - Essentiel administratif
3.  **Gestion des temps** - Nécessaire paie et conformité

Avec ces 3 modules, l'application deviendra un **SIRH complet et opérationnel**.
