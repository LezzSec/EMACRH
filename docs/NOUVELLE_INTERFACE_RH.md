# Nouvelle Interface "Gestion RH"

## Vue d'ensemble

La nouvelle interface **Gestion RH** remplace l'ancienne interface "Gestion des Absences et Congés" en combinant plusieurs fonctionnalités RH essentielles dans une seule interface unifiée.

## Accès

**Menu Principal** → Bouton hamburger (☰) → **"Gestion RH"**

---

## 📊 Onglets disponibles

### 1. **📊 Tableau de bord**

Vue d'ensemble complète avec 4 sections :

#### Section Évaluations (Colonne gauche)

**⚠️ Évaluations en Retard**
- Nombre total d'évaluations en retard
- Liste des 10 évaluations les plus urgentes
- Format : `Nom Prénom - Code Poste (Atelier) - Retard: X jours`
- Couleur : Rouge (#e74c3c)

**📅 Prochaines Évaluations**
- Évaluations à venir dans les 30 prochains jours
- Liste des 10 prochaines évaluations
- Format : `Nom Prénom - Code Poste (Atelier) - Dans X jours`
- Couleur : Vert (#27ae60)

#### Section Absences/Congés (Colonne droite)

**🏖️ Mes Soldes de Congés**
- Carte affichant :
  - **Congés Payés** : Nombre de jours restants
  - **RTT** : Nombre de jours restants
- Couleur : Bleu (#3498db)

**📝 Mes Demandes Récentes**
- Liste des 5 dernières demandes d'absence
- Code couleur par statut :
  - 🟠 EN_ATTENTE : Orange
  - 🟢 VALIDEE : Vert
  - 🔴 REFUSEE : Rouge
  - ⚪ ANNULEE : Gris
- Bouton **"➕ Nouvelle Demande"** pour accès rapide

---

### 2. **📅 Calendrier Évaluations**

Interface complète de suivi des évaluations :

#### Filtres disponibles
- **Filtre poste** : Tous les postes / Poste spécifique
- **Période** :
  - En retard
  - 30 prochains jours
  - 90 prochains jours
  - Tous

#### Tableau des évaluations
Colonnes :
- Opérateur
- Poste
- Atelier
- Niveau (1-4)
- Dernière Évaluation
- Prochaine Évaluation
- Jours Restants

**Code couleur** :
- 🔴 Rouge : En retard (jours < 0)
- 🟠 Orange : Urgent (jours ≤ 30)
- ⚪ Normal : Pas d'urgence

#### Actions disponibles
- **📅 Planifier Évaluation** : Planifier une nouvelle évaluation
- **📤 Exporter** : Exporter le tableau

---

### 3. **🏖️ Mes Absences**

Gestion complète de mes absences et congés avec 3 sous-onglets :

#### 3.1 Mes Demandes

**Filtres** :
- Année (année courante ± 2 ans)
- Statut : Tous / En attente / Validées / Refusées

**Tableau** :
- ID, Type, Début, Fin, Nb jours, Motif, Statut, Validateur, Date validation

**Actions** :
- Annuler la demande (uniquement pour statut "EN_ATTENTE")

#### 3.2 Nouvelle Demande

**Formulaire complet** :

1. **Type d'absence** : Liste déroulante (CP, RTT, Maladie, etc.)

2. **Date de début** :
   - Calendrier popup
   - Options : Journée / Matin / Après-midi

3. **Date de fin** :
   - Calendrier popup
   - Options : Journée / Matin / Après-midi

4. **Nombre de jours ouvrés** : Calcul automatique

5. **Motif** : Texte libre (optionnel)

**Calcul intelligent** :
- ✅ Compte uniquement les jours ouvrés (lundi-vendredi)
- ✅ Gère les demi-journées (0.5 jour)
- ✅ Mise à jour en temps réel

**Bouton** : "Soumettre la demande" (vert, bien visible)

#### 3.3 Mes Soldes

**Affichage détaillé** :

**Sélection année** : Année courante ± 2 ans

**Cartes visuelles** :
- 🟢 **Congés Payés** : Jours restants (grande taille)
- 🔵 **RTT** : Jours restants (grande taille)

**Détails complets** :

Congés Payés :
- Acquis : X jours
- Reportés N-1 : X jours
- Pris : X jours
- **Restant : X jours**

RTT :
- Acquis : X jours
- Pris : X jours
- **Restant : X jours**

---

### 4. **📆 Planning Équipe**

Visualisation des absences de l'équipe :

**Calendrier interactif** :
- Affichage mensuel
- Cliquer sur un jour pour voir les absences

**Liste des absences du jour** :
- Tableau avec : Nom, Type, Du, Au
- Mise à jour en cliquant sur une date du calendrier

**Utilité** :
- Voir qui est absent un jour donné
- Planifier les congés en fonction des autres
- Éviter les conflits d'absences dans l'équipe

---

### 5. **✅ Validation** (Pour managers)

Interface de validation des demandes d'absence :

**Tableau des demandes en attente** :
- ID, Personnel, Type, Du, Au, Nb jours, Motif
- Triées par date de création (les plus anciennes en premier)

**Actions** :
1. Sélectionner une demande
2. Cliquer sur :
   - 🟢 **Valider** : Approuver la demande
   - 🔴 **Refuser** : Refuser la demande

**Confirmation** : Message de confirmation avant validation/refus

---

## 🎨 Design et ergonomie

### Codes couleur
- **Rouge** (#e74c3c) : Urgent / En retard / Refusé
- **Orange** (#f39c12) : En attente / Attention
- **Vert** (#27ae60) : Validé / OK / Prochaines évaluations
- **Bleu** (#3498db) : Informations / Soldes
- **Violet** (#9b59b6) : Demandes récentes

### Hiérarchie de l'information
1. **Niveau 1** : Onglets principaux (icônes + texte)
2. **Niveau 2** : Sous-onglets (si nécessaire)
3. **Niveau 3** : Cartes d'information avec couleurs distinctives
4. **Niveau 4** : Tableaux et listes détaillées

### Boutons d'action
- Vert : Actions principales (Soumettre, Valider)
- Rouge : Actions destructives (Refuser, Annuler)
- Bleu/Neutre : Actions secondaires (Actualiser, Export)

---

## 🔄 Flux de travail typique

### Employé standard

1. **Consulter le tableau de bord** pour voir :
   - Mes soldes de congés
   - Mes demandes récentes
   - (Bonus) Les évaluations à venir

2. **Faire une nouvelle demande** :
   - Onglet "Mes Absences" → "Nouvelle Demande"
   - Remplir le formulaire
   - Soumettre

3. **Suivre mes demandes** :
   - Onglet "Mes Absences" → "Mes Demandes"
   - Filtrer par statut si besoin

4. **Consulter le planning** :
   - Onglet "Planning Équipe"
   - Vérifier les absences des collègues

### Manager

1. **Vue d'ensemble** :
   - Tableau de bord pour voir les évaluations urgentes

2. **Valider les demandes** :
   - Onglet "Validation"
   - Consulter les demandes en attente
   - Valider ou refuser

3. **Planifier les évaluations** :
   - Onglet "Calendrier Évaluations"
   - Filtrer les évaluations en retard
   - Planifier via le bouton "📅 Planifier Évaluation"

---

## ⚡ Fonctionnalités principales

### ✅ Ce qui fonctionne

1. **Tableau de bord unifié** :
   - Vue d'ensemble RH complète
   - Évaluations + Absences sur un seul écran
   - Actualisation en temps réel

2. **Calendrier des évaluations** :
   - Filtres multiples
   - Code couleur intelligent
   - Export possible

3. **Gestion des absences** :
   - Création de demandes intuitive
   - Calcul automatique des jours
   - Suivi complet des demandes

4. **Soldes de congés** :
   - Affichage clair et visuel
   - Détails complets
   - Multi-années

5. **Planning d'équipe** :
   - Calendrier interactif
   - Visualisation des absences

6. **Validation** :
   - Interface simple pour managers
   - Workflow clair

---

## 🔮 Améliorations futures possibles

### Court terme
- [ ] Intégration complète avec GestionEvaluationDialog
- [ ] Notifications pour demandes en attente
- [ ] Filtres avancés sur le planning

### Moyen terme
- [ ] Export PDF du planning mensuel
- [ ] Statistiques RH (taux d'absence, etc.)
- [ ] Validation par lots

### Long terme
- [ ] Connexion avec un système de gestion de la paie
- [ ] Alertes automatiques par email
- [ ] Dashboard manager avec KPIs

---

## 🐛 Points d'attention

### Prérequis
- Tables `demande_absence`, `type_absence`, `solde_conges` doivent exister
- Service `absence_service` doit être fonctionnel
- Personnel connecté doit avoir un ID valide

### Limitations connues
- Validateur ID hardcodé à 1 (TODO: récupérer l'ID réel)
- Pas de filtre par service/équipe pour les managers
- Calendrier planning pas encore complètement implémenté

---

## 📝 Comparaison avec l'ancienne interface

| Fonctionnalité | Ancienne interface | Nouvelle interface |
|----------------|-------------------|-------------------|
| **Vue d'ensemble** | ❌ Non | ✅ Oui - Dashboard complet |
| **Évaluations** | ❌ Absentes | ✅ Intégrées |
| **Absences** | ✅ Oui | ✅ Oui (amélioré) |
| **Planning équipe** | ✅ Oui | ✅ Oui |
| **Soldes** | ✅ Oui | ✅ Oui (plus visuel) |
| **Validation** | ✅ Oui | ✅ Oui |
| **Ergonomie** | ⚪ Correcte | ✅ Excellente |
| **Organisation** | ⚪ Dispersée | ✅ Unifiée |

---

## 🎯 Objectif atteint

✅ **Interface unique** combinant :
- Calendriers d'évaluation (retrouvés !)
- Gestion des absences et congés
- Planning d'équipe
- Validation des demandes

✅ **Ergonomie améliorée** :
- Navigation claire avec onglets
- Tableau de bord centralisé
- Code couleur cohérent
- Actions intuitives

✅ **Fonctionnalités préservées** :
- Toutes les fonctionnalités de l'ancien module d'absences
- Plus les calendriers d'évaluation qui manquaient

---

## 📞 Support

Pour toute question ou suggestion d'amélioration, consultez :
- [CLAUDE.md](../CLAUDE.md) - Instructions développeur
- [GUIDE_UTILISATION_ABSENCES.md](GUIDE_UTILISATION_ABSENCES.md) - Guide utilisateur absences
