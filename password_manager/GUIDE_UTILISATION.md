# 📋 GUIDE D'UTILISATION - GESTIONNAIRE DE MOTS DE PASSE

## 🚀 INSTALLATION

### Option 1: Utiliser l'exécutable (RECOMMANDÉE)
1. **Téléchargez** le fichier `GestionnaireMotsDePasse.exe`
2. **Placez-le** dans un dossier de votre choix (ex: `C:\MonGestionnaire\`)
3. **Double-cliquez** sur le fichier pour lancer l'application
4. **Première connexion** : 
   - Nom d'utilisateur: `admin`
   - Mot de passe: `admin123`

### Option 2: Utiliser le code Python
1. **Installez Python 3.8+** depuis https://python.org
2. **Installez les dépendances** :
   ```bash
   pip install customtkinter cryptography bcrypt
   ```
3. **Lancez** le fichier `Password manager.py`

## 🔐 PREMIÈRE UTILISATION

### 1. Connexion initiale
- Utilisez le compte admin par défaut
- Créez immédiatement votre propre compte utilisateur
- Changez le mot de passe admin

### 2. Créer votre compte personnel
1. Cliquez sur **"Créer un compte"**
2. Choisissez un nom d'utilisateur unique
3. Définissez un mot de passe fort
4. Connectez-vous avec votre nouveau compte

### 3. Sécurité des données
- ✅ Toutes les données sont stockées localement
- ✅ Mots de passe chiffrés avec AES-256
- ✅ Aucune connexion internet requise
- ✅ Base de données protégée par mot de passe

## 👥 GESTION DES RÔLES

### 🔴 Administrateur (admin)
- Accès complet à tous les mots de passe
- Gestion des utilisateurs
- Suppression de tous les mots de passe
- Accès au panneau d'administration

### 🟡 Manager
- Accès à tous les mots de passe
- Gestion des permissions
- Suppression des mots de passe
- Pas de gestion d'utilisateurs

### 🟢 Utilisateur (user)
- Accès à ses propres mots de passe
- Création de mots de passe personnels
- Modification de ses propres données
- Suppression de ses propres mots de passe

## 🛠️ FONCTIONNALITÉS PRINCIPALES

### Ajouter un mot de passe
1. Cliquez sur **"➕ Ajouter"**
2. Remplissez les informations
3. Utilisez **"Générer"** pour créer un mot de passe fort
4. Sauvegardez

### Consulter un mot de passe
1. **Double-cliquez** sur une entrée
2. Cliquez sur **"Afficher"** pour voir le mot de passe
3. Utilisez **"Copier"** pour le copier dans le presse-papiers

### Supprimer un mot de passe
1. **Clic droit** sur une entrée
2. Sélectionnez **"Supprimer"**
3. Confirmez la suppression

### Rechercher
- Utilisez la barre de recherche en haut
- Recherche dans les titres, noms d'utilisateur et URLs

## 🔍 DÉPANNAGE

### Erreur de déchiffrement
1. Reconnectez-vous à votre compte
2. Double-cliquez sur le mot de passe problématique
3. Cliquez sur **"Recréer le mot de passe"**
4. Saisissez le nouveau mot de passe

### Mot de passe admin oublié
1. Supprimez le fichier `password_manager.db`
2. Relancez l'application
3. Le compte admin sera recréé automatiquement

### Application ne se lance pas
1. Vérifiez que vous avez les droits d'exécution
2. Lancez en tant qu'administrateur si nécessaire
3. Vérifiez qu'aucun antivirus ne bloque l'application

## 📁 EMPLACEMENT DES DONNÉES

### Avec l'exécutable
- Base de données: `password_manager.db` (même dossier que l'exe)
- Sauvegardes: Dossier `backups\` (créé automatiquement)

### Avec Python
- Base de données: `password_manager.db` (dossier du script)
- Sauvegardes: Dossier `backups\` (créé automatiquement)

## 🔒 SÉCURITÉ ET BONNES PRATIQUES

### Recommandations
1. **Utilisez un mot de passe fort** pour votre compte
2. **Sauvegardez régulièrement** le fichier `password_manager.db`
3. **Ne partagez jamais** votre mot de passe de connexion
4. **Déconnectez-vous** quand vous quittez votre poste

### Sauvegarde manuelle
1. Copiez le fichier `password_manager.db`
2. Stockez-le dans un endroit sûr
3. Chiffrez-le avec 7-Zip ou WinRAR si nécessaire

## 📞 SUPPORT

Pour toute question ou problème :
1. Consultez ce guide
2. Contactez l'administrateur système
3. Vérifiez les messages d'erreur affichés

## 🎯 CONSEILS D'UTILISATION

### Mots de passe forts
- Minimum 12 caractères
- Mélange de lettres, chiffres et symboles
- Utilisez le générateur intégré

### Organisation
- Utilisez des catégories appropriées
- Ajoutez des notes descriptives
- Utilisez des titres clairs

### Sécurité
- Changez vos mots de passe régulièrement
- Ne réutilisez jamais un mot de passe
- Vérifiez l'intégrité avec le bouton "🔍 Vérifier"

---

**✅ PRÊT À UTILISER !**

Votre gestionnaire de mots de passe est maintenant prêt à sécuriser vos données !
