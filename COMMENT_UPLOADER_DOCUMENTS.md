# 📁 Comment uploader des documents existants dans EMAC

> **Guide ultra-rapide** pour importer vos documents RH dans l'application

---

## 🚀 En 3 étapes simples

### 1️⃣ Ouvrir le module

```
Menu ☰ (hamburger en haut à droite) → "Documents RH"
```

### 2️⃣ Sélectionner l'employé

```
Liste déroulante "Employé" → Choisir l'employé concerné
```

### 3️⃣ Ajouter le document

```
Bouton "➕ Ajouter un document" → Parcourir → Sélectionner le fichier
```

---

## 📋 Formulaire d'ajout

| Champ | Obligatoire | Exemple |
|-------|------------|---------|
| **Fichier** | ✅ | `certificat_medical_2024.pdf` |
| **Catégorie** | ✅ | "Certificats médicaux" |
| **Nom d'affichage** | ❌ | "Visite médicale annuelle 2024" |
| **Date d'expiration** | ❌ | 01/01/2025 |
| **Notes** | ❌ | "Visite d'embauche, apte sans restrictions" |

---

## ✅ Ce qui se passe ensuite

1. Le fichier est **copié** dans l'application (l'original reste intact)
2. Il est **organisé automatiquement** : `documents/operateurs/{matricule}/{catégorie}/`
3. Il apparaît dans le **tableau des documents** avec toutes ses informations
4. Des **alertes automatiques** seront affichées avant la date d'expiration

---

## 🎯 Actions disponibles

| Action | Comment | Résultat |
|--------|---------|----------|
| **Ouvrir** | Double-clic ou bouton 📂 | Ouvre le document avec l'appli par défaut |
| **Télécharger** | Bouton 💾 | Exporte une copie vers un emplacement choisi |
| **Supprimer** | Bouton 🗑️ | Supprime définitivement le document |

---

## 🔍 Filtres disponibles

- **Par employé** : Voir tous les documents d'une personne
- **Par catégorie** : Ex: "Certificats médicaux"
- **Par statut** : Actif, Expiré, Archivé
- **Recherche** : Taper un mot-clé dans le champ de recherche

---

## 📊 Catégories disponibles

1. **Contrats de travail** - CDI, CDD, avenants
2. **Certificats médicaux** - Visites médicales, aptitudes
3. **Diplômes et formations** - Certificats, habilitations
4. **Autorisations de travail** - Titres de séjour
5. **Pièces d'identité** - CNI, passeport, permis
6. **Attestations diverses** - Certificats employeur
7. **Documents administratifs** - Fiches de paie, relevés
8. **Autres** - Tout autre document

---

## 💡 Conseils pratiques

### ✅ À faire

- Utiliser des noms de fichiers clairs
- Renseigner les dates d'expiration pour les documents à validité limitée
- Ajouter des notes pour contextualiser
- Vérifier régulièrement les documents expirés

### ❌ À éviter

- Ne pas renommer/déplacer les fichiers dans le dossier `documents/` manuellement
- Ne pas uploader de fichiers trop volumineux (>50 Mo)
- Ne pas oublier de sauvegarder le dossier `documents/` régulièrement

---

## 🧪 Tester le module

Pour vérifier que tout fonctionne :

```bash
cd App
py scripts/test_document_upload.py
```

Résultat attendu : ✅ **TOUS LES TESTS ONT RÉUSSI!**

---

## 📖 Documentation complète

- **Guide détaillé** : [docs/user/guide-upload-documents.md](docs/user/guide-upload-documents.md)
- **Documentation technique** : [docs/features/module-documents.md](docs/features/module-documents.md)
- **Rapport d'amélioration** : [AMELIORATION_GESTION_DOCUMENTS_2026-01-09.md](AMELIORATION_GESTION_DOCUMENTS_2026-01-09.md)

---

## ❓ Problèmes fréquents

### "Module non installé"

```bash
cd App/scripts
py install_gestion_documentaire.py
```

### "Fichier introuvable"

Le fichier a été supprimé ou déplacé. Restaurez-le depuis une sauvegarde ou supprimez l'entrée.

### "Impossible d'ouvrir"

Installez l'application appropriée (ex: Adobe Reader pour les PDF).

---

## 🎉 C'est tout !

Vous pouvez maintenant importer tous vos documents RH existants dans l'application EMAC.

**Bon usage ! 🚀**
