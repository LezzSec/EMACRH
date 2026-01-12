# Exemples Pratiques - Upload de Documents RH

> **Cas d'usage concrets** pour bien utiliser le module de gestion documentaire

---

## 📋 Table des matières

1. [Cas 1 : Certificat médical d'embauche](#cas-1--certificat-médical-dembauche)
2. [Cas 2 : Diplôme ou formation](#cas-2--diplôme-ou-formation)
3. [Cas 3 : Titre de séjour temporaire](#cas-3--titre-de-séjour-temporaire)
4. [Cas 4 : Pièce d'identité](#cas-4--pièce-didentité)
5. [Cas 5 : Plusieurs documents en une fois](#cas-5--plusieurs-documents-en-une-fois)
6. [Cas 6 : Retrouver rapidement un document](#cas-6--retrouver-rapidement-un-document)
7. [Cas 7 : Gérer les documents expirés](#cas-7--gérer-les-documents-expirés)

---

## Cas 1 : Certificat médical d'embauche

### Contexte
Un nouvel employé, **Jean Dupont**, vient d'être embauché. Vous avez reçu son certificat médical d'aptitude au travail en PDF.

### Actions à réaliser

1. **Ouvrir le module**
   - Menu ☰ → "Documents RH"

2. **Sélectionner l'employé**
   - Employé : `Jean Dupont`

3. **Ajouter le document**
   - Cliquer sur "➕ Ajouter un document"
   - **Fichier** : Parcourir → Sélectionner `certificat_medical_dupont_2024.pdf`
   - **Catégorie** : `Certificats médicaux`
   - **Nom d'affichage** : `Visite médicale d'embauche 2024`
   - **Date d'expiration** : `31/12/2024` (validité 1 an)
   - **Notes** : `Apte à tous les postes sans restriction`
   - Cliquer sur "Enregistrer"

### Résultat
- ✅ Le document est enregistré dans : `documents/operateurs/M000123/medicaux/`
- ✅ Visible dans le tableau avec un code couleur rouge (catégorie médicale)
- ✅ Une alerte apparaîtra 30 jours avant la date d'expiration

### Conseils
- 💡 Profitez-en pour ajouter tous les autres documents d'embauche (contrat, pièce d'identité, etc.)
- 💡 Mettez une date d'expiration pour recevoir une alerte avant le renouvellement

---

## Cas 2 : Diplôme ou formation

### Contexte
**Marie Martin** vient d'obtenir une habilitation électrique. Vous souhaitez archiver ce certificat.

### Actions à réaliser

1. **Ouvrir le module**
   - Menu ☰ → "Documents RH"

2. **Sélectionner l'employé**
   - Employé : `Marie Martin`

3. **Ajouter le document**
   - Cliquer sur "➕ Ajouter un document"
   - **Fichier** : Sélectionner `habilitation_electrique_B1V.pdf`
   - **Catégorie** : `Diplômes et formations`
   - **Nom d'affichage** : `Habilitation électrique B1V`
   - **Date d'expiration** : `15/06/2027` (validité 3 ans)
   - **Date du document** : `15/06/2024` (date de délivrance)
   - **Notes** : `Formation suivie chez APAVE - Niveau B1V - Référence HABIL2024-1234`
   - Enregistrer

### Résultat
- ✅ Le certificat est archivé et consultable à tout moment
- ✅ Organisation automatique : `documents/operateurs/M000456/formations/`
- ✅ Alerte automatique 3 ans plus tard pour renouvellement

### Conseils
- 💡 Ajoutez la référence de formation dans les notes
- 💡 Scannez le verso du certificat s'il contient des informations importantes

---

## Cas 3 : Titre de séjour temporaire

### Contexte
**Ahmed Benali** a un titre de séjour valable 1 an. Vous devez le conserver pour être en règle.

### Actions à réaliser

1. **Ouvrir le module**
   - Menu ☰ → "Documents RH"

2. **Sélectionner l'employé**
   - Employé : `Ahmed Benali`

3. **Ajouter le document**
   - **Fichier** : Sélectionner `titre_sejour_benali_scan.pdf`
   - **Catégorie** : `Autorisations de travail`
   - **Nom d'affichage** : `Titre de séjour 2024-2025`
   - **Date d'expiration** : `30/09/2025` ⚠️ **IMPORTANT**
   - **Notes** : `Titre de séjour temporaire salarié - À renouveler avant échéance`
   - Enregistrer

### Résultat
- ✅ Document enregistré et sécurisé
- ✅ Alerte 30 jours avant expiration (01/09/2025)
- ✅ L'employeur sera notifié à temps pour demander le renouvellement

### Conseils
- 💡 **CRITIQUE** : Vérifiez bien la date d'expiration !
- 💡 Ajoutez une note dans votre agenda 2 mois avant l'expiration
- 💡 Scannez recto ET verso du titre de séjour

---

## Cas 4 : Pièce d'identité

### Contexte
Vous devez archiver une copie de la carte d'identité de **Sophie Lefebvre** pour le dossier du personnel.

### Actions à réaliser

1. **Ouvrir le module**
   - Menu ☰ → "Documents RH"

2. **Sélectionner l'employé**
   - Employé : `Sophie Lefebvre`

3. **Ajouter le document**
   - **Fichier** : Sélectionner `CNI_lefebvre_recto_verso.pdf` (scan recto-verso)
   - **Catégorie** : `Pièces d'identité`
   - **Nom d'affichage** : `Carte Nationale d'Identité`
   - **Date d'expiration** : `12/03/2030`
   - **Notes** : `CNI n° 123456789012 - Scan recto-verso`
   - Enregistrer

### Résultat
- ✅ Copie de la CNI archivée de façon sécurisée
- ✅ Conforme RGPD (accès restreint)
- ✅ Alerte avant expiration pour demander une mise à jour

### Conseils
- 💡 Scannez **recto ET verso** en un seul PDF
- 💡 Masquez le numéro de sécurité sociale si présent (RGPD)
- 💡 Vérifiez la date d'expiration sur le document physique

---

## Cas 5 : Plusieurs documents en une fois

### Contexte
**Thomas Rousseau** vient d'être embauché. Vous devez uploader :
- Son contrat de travail
- Sa visite médicale
- Sa pièce d'identité
- Son diplôme

### Méthode recommandée

**Répétez ces étapes 4 fois** (une fois par document) :

1. Menu ☰ → "Documents RH"
2. Sélectionner `Thomas Rousseau`
3. Cliquer sur "➕ Ajouter un document"
4. Remplir le formulaire et enregistrer
5. Le dialogue se ferme automatiquement
6. Recommencer pour le document suivant

### Organisation finale

```
documents/operateurs/M000789/
├── contrats/
│   └── CDI_Rousseau_2024.pdf
├── medicaux/
│   └── visite_medicale_embauche.pdf
├── identite/
│   └── CNI_rousseau.pdf
└── formations/
    └── diplome_technicien.pdf
```

### Conseils
- 💡 Commencez par les documents les plus importants (contrat, visite médicale)
- 💡 Utilisez des noms de fichiers clairs et cohérents
- 💡 Renseignez bien les dates d'expiration pour les documents à validité limitée

---

## Cas 6 : Retrouver rapidement un document

### Contexte
L'inspection du travail demande à consulter la **dernière visite médicale** de **Claire Blanc** datant de 2023.

### Méthode rapide

1. **Ouvrir le module**
   - Menu ☰ → "Documents RH"

2. **Utiliser les filtres**
   - **Employé** : `Claire Blanc`
   - **Catégorie** : `Certificats médicaux`
   - **Statut** : `Tous`

3. **Recherche textuelle** (optionnel)
   - Taper `2023` dans le champ "Recherche"

4. **Ouvrir le document**
   - Double-clic sur la ligne du tableau
   - Ou cliquer sur le bouton 📂

### Résultat
- ✅ Document trouvé en moins de 10 secondes
- ✅ Ouvert dans Adobe Reader
- ✅ Prêt à être imprimé ou envoyé par email

### Conseils
- 💡 Les filtres sont cumulatifs (employé + catégorie + recherche)
- 💡 La recherche textuelle cherche dans le nom d'affichage du document
- 💡 Double-clic est le moyen le plus rapide d'ouvrir

---

## Cas 7 : Gérer les documents expirés

### Contexte
Vous voulez identifier tous les **certificats médicaux expirés** pour planifier les renouvellements.

### Méthode

1. **Ouvrir le module**
   - Menu ☰ → "Documents RH"

2. **Appliquer les filtres**
   - **Employé** : `Tous les employés`
   - **Catégorie** : `Certificats médicaux`
   - **Statut** : `Expiré` ⚠️

3. **Analyser les résultats**
   - Les documents expirés apparaissent en **rouge** dans le tableau
   - Notez les employés concernés

4. **Actions à entreprendre**
   - Prendre rendez-vous chez la médecine du travail
   - Envoyer un email aux employés concernés
   - Mettre à jour le planning des visites médicales

### Exemple de résultat

| Employé | Document | Date d'expiration | Jours de retard |
|---------|----------|-------------------|----------------|
| Jean Dupont | Visite médicale 2023 | 31/12/2023 | 374 jours |
| Marie Martin | Visite médicale 2024 | 15/06/2024 | 208 jours |
| Paul Durand | Visite médicale 2024 | 20/08/2024 | 142 jours |

### Conseils
- 💡 Faites cette vérification **chaque mois**
- 💡 Exportez la liste des documents expirés (copie d'écran ou export Excel)
- 💡 Planifiez les renouvellements **2 mois à l'avance**

---

## 💡 Bonnes pratiques générales

### Nomenclature des fichiers

**❌ Mauvais exemples :**
- `scan001.pdf`
- `document.pdf`
- `IMG_2024.jpg`

**✅ Bons exemples :**
- `certificat_medical_dupont_2024.pdf`
- `diplome_CAP_mecanique_martin.pdf`
- `titre_sejour_benali_2024_2025.pdf`

### Organisation par type de document

| Type de document | Fréquence de mise à jour | Date d'expiration |
|------------------|--------------------------|-------------------|
| **Contrats** | À chaque modification | Date de fin si CDD |
| **Certificats médicaux** | Tous les 1-2 ans | Date de la prochaine visite |
| **Diplômes** | Jamais (permanent) | Aucune |
| **Autorisations de travail** | Variable (1-10 ans) | ⚠️ **CRITIQUE** |
| **Pièces d'identité** | Tous les 10-15 ans | Date d'expiration |

### Sauvegardes

- 📦 **Sauvegardez le dossier** `App/documents/` **chaque semaine**
- 📦 Conservez au moins **3 copies** (local, cloud, externe)
- 📦 Testez régulièrement vos sauvegardes (restauration)

---

## 📞 Besoin d'aide ?

- **Guide complet** : [guide-upload-documents.md](guide-upload-documents.md)
- **Documentation technique** : [../features/module-documents.md](../features/module-documents.md)
- **Guide ultra-rapide** : [../../COMMENT_UPLOADER_DOCUMENTS.md](../../COMMENT_UPLOADER_DOCUMENTS.md)

---

**Dernière mise à jour** : 2026-01-09
**Version** : 1.0
