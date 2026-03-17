# GUIDE D'UTILISATION - MODULE ABSENCES ET CONGÉS

## ACCÈS AU MODULE

### Depuis l'application EMAC :
1. Lancez l'application : `py -m core.gui.main_qt`
2. Cliquez sur le bouton **"Planning/Absences"** dans le menu latéral
3. Le module de gestion des absences s'ouvre

---

## LES 5 ONGLETS

### 1️⃣ **MES DEMANDES** - Voir toutes mes demandes

**Ce que vous voyez :**
- Liste complète de vos demandes d'absence
- Pour chaque demande : Type, Dates, Nb jours, Motif, Statut, Validateur

**Filtres disponibles :**
-  **Année** : 2023, 2024, 2025, 2026...
-  **Statut** : Tous / En attente / Validées / Refusées

**Actions possibles :**
- ❌ **Annuler** : Annule une demande EN_ATTENTE
-  **Actualiser** : Rafraîchit la liste

**Codes couleur :**
-  **Vert** = Demande validée
-  **Rouge** = Demande refusée
-  **Blanc** = En attente ou annulée

---

### 2️⃣ **NOUVELLE DEMANDE** - Créer une demande de congés

**Étapes pour créer une demande :**

1. **Sélectionner le type d'absence :**
   - Congés Payés (CP)
   - RTT
   - Arrêt Maladie
   - Congé Sans Solde
   - Congé Maternité
   - Congé Paternité
   - Formation
   - Événement Familial
   - Autre

2. **Choisir la date de début :**
   - Cliquez sur le calendrier 
   - Sélectionnez : **Journée** / **Matin** / **Après-midi**

3. **Choisir la date de fin :**
   - Cliquez sur le calendrier 
   - Sélectionnez : **Journée** / **Matin** / **Après-midi**

4. **Vérifier le calcul automatique :**
   - Le système calcule automatiquement les **jours ouvrés** (lun-ven)
   - Les **weekends** sont exclus
   - Les **jours fériés** sont exclus
   - Les **demi-journées** comptent 0.5 jour

5. **Ajouter un motif (optionnel) :**
   - Décrivez brièvement la raison

6. **Soumettre :**
   - Cliquez sur le bouton vert **"Soumettre la demande"**
   - Confirmation affichée
   - Statut : **EN_ATTENTE**

**Exemples de calcul :**
```
Du lundi au vendredi = 5 jours
Du lundi matin au vendredi après-midi = 5 jours
Du lundi matin au vendredi midi = 4.5 jours
Du jeudi au lundi suivant = 4 jours (exclut samedi-dimanche)
Du 24/12 au 26/12 (avec férié 25/12) = 2 jours
```

---

### 3️⃣ **CALENDRIER** - Voir les absences de l'équipe

**Fonctionnalités :**
-  **Calendrier visuel** mensuel
- Cliquez sur un jour → affiche les absents de la journée
- Liste détaillée :
  - Nom du personnel
  - Type d'absence
  - Dates de début et fin

**Utilité :**
- Éviter les conflits (plusieurs absents le même jour)
- Planifier vos congés selon l'équipe
- Vue d'ensemble des absences

---

### 4️⃣ **MES SOLDES** - Consulter mes soldes CP/RTT

**Affichage :**

 **Grande card verte - CONGÉS PAYÉS**
- Affiche le **nombre de jours restants** en gros
- Détails :
  - CP acquis : 25 jours
  - CP reportés N-1 : X jours
  - CP pris : X jours
  - **CP restants** : X jours

 **Grande card bleue - RTT**
- Affiche le **nombre de jours restants** en gros
- Détails :
  - RTT acquis : 10 jours
  - RTT pris : X jours
  - **RTT restants** : X jours

**Sélection d'année :**
- Dropdown pour changer d'année (2023-2026)
- Utile pour voir l'historique

---

### 5️⃣ **VALIDATION** - Pour les managers/RH

**Ce que vous voyez :**
- Liste des demandes **EN_ATTENTE** de toute l'équipe
- Colonnes : Personnel, Type, Du, Au, Nb jours, Motif

**Actions :**
-  **Valider** : Approuve la demande
  - Statut → VALIDEE
  - Solde CP/RTT décompté automatiquement
  - Date et validateur enregistrés

-  **Refuser** : Refuse la demande
  - Statut → REFUSEE
  - Solde non décompté
  - Possibilité d'ajouter un commentaire

**Workflow :**
1. Sélectionner une demande dans la liste
2. Cliquer "Valider" ou "Refuser"
3. Confirmer l'action
4. La demande disparaît de la liste EN_ATTENTE
5. L'employé voit le changement dans "Mes Demandes"

---

## CAS D'USAGE FRÉQUENTS

### ✅ Je veux poser une semaine de congés
```
1. Onglet "Nouvelle Demande"
2. Type : Congés Payés (CP)
3. Du : lundi (Journée)
4. Au : vendredi (Journée)
5. → Calcul auto : 5 jours
6. Soumettre
```

### ✅ Je veux poser un après-midi
```
1. Nouvelle Demande
2. Type : RTT
3. Du : vendredi (Après-midi)
4. Au : vendredi (Après-midi)
5. → Calcul auto : 0.5 jour
6. Soumettre
```

### ✅ Je suis malade
```
1. Nouvelle Demande
2. Type : Arrêt Maladie
3. Dates : selon arrêt
4. Motif : "Arrêt maladie"
5. Soumettre
Note : Ne décompte PAS le solde CP/RTT
```

### ✅ Je veux voir mes congés restants
```
1. Onglet "Mes Soldes"
2. Sélectionner l'année 2025
3. Voir les grandes cards colorées
4. Détails en bas
```

### ✅ Je veux annuler une demande
```
1. Onglet "Mes Demandes"
2. Sélectionner une demande EN_ATTENTE
3. Cliquer "Annuler la demande"
4. Confirmer
5. Statut → ANNULEE
```

### ✅ Je suis manager et je valide une demande
```
1. Onglet "Validation"
2. Liste des demandes EN_ATTENTE
3. Sélectionner une demande
4. Cliquer "Valider" (vert)
5. Confirmer
6. Solde décompté automatiquement
```

---

## RÈGLES DE GESTION

### Jours ouvrés
- **Comptés** : Lundi, Mardi, Mercredi, Jeudi, Vendredi
- **Exclus** : Samedi, Dimanche
- **Exclus** : Jours fériés (configurés dans la base)

### Demi-journées
- **Matin** : 0.5 jour (08h-12h)
- **Après-midi** : 0.5 jour (14h-18h)
- **Journée** : 1 jour (08h-18h)

### Décompte des soldes
**Types qui décomptent :**
- ✅ CP (Congés Payés) → décompte CP
- ✅ RTT → décompte RTT

**Types qui ne décomptent PAS :**
- ❌ Maladie
- ❌ Sans Solde
- ❌ Maternité/Paternité
- ❌ Formation
- ❌ Événement Familial
- ❌ Autre

### Workflow de validation
```
Demande créée
    ↓
Statut: EN_ATTENTE
    ↓
Manager valide/refuse
    ↓
VALIDEE → Solde décompté
    ou
REFUSEE → Solde non décompté
```

---

## FAQ

**Q : Je ne vois pas mes soldes, ils sont à 0**
R : Les soldes doivent être initialisés pour l'année. Demandez à l'administrateur d'exécuter :
```python
from core.services.absence_service import initialiser_soldes_annee
initialiser_soldes_annee(2025)
```

**Q : Le calcul de jours ne semble pas correct**
R : Vérifiez :
- Les weekends sont bien exclus
- Les jours fériés sont dans la table `jours_feries`
- Les demi-journées sont correctement sélectionnées

**Q : Je suis manager, pourquoi je ne vois pas les demandes à valider ?**
R : L'onglet "Validation" affiche TOUTES les demandes EN_ATTENTE. Le filtrage par équipe/service sera ajouté dans une future version.

**Q : Puis-je modifier une demande après l'avoir soumise ?**
R : Non, vous devez l'annuler et en créer une nouvelle.

**Q : Combien de CP ai-je par an ?**
R : Par défaut : 25 CP + 10 RTT. Configurable par l'administrateur.

**Q : Les CP N-1 se reportent-ils ?**
R : Oui, le champ `cp_n_1` dans la table `solde_conges` permet le report.

---

## 🆘 EN CAS DE PROBLÈME

### L'application ne se lance pas
```bash
cd App
py -m core.gui.main_qt
```

### Le module d'absences ne s'ouvre pas
Vérifiez que les tables existent :
```bash
py install_absences_module.py
```

### Erreur "Personnel non identifié"
Le système utilise actuellement le premier personnel ACTIF. Dans une future version, un système d'authentification sera ajouté.

### Les jours fériés 2026 ne sont pas à jour
Ajoutez-les manuellement :
```sql
INSERT INTO jours_feries (date_ferie, libelle, fixe) VALUES
('2026-01-01', 'Jour de l\'An', TRUE),
-- etc.
```

---

## CONTACT SUPPORT

Pour toute question :
1. Consultez le fichier `MODULE_ABSENCES_README.md`
2. Vérifiez la base de données
3. Consultez les logs d'erreur

**Bon courage ! **
