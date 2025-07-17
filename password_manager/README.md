# 🔒 Gestionnaire de Mots de Passe Entreprise

Un gestionnaire de mots de passe sécurisé développé avec CustomTkinter pour un usage en entreprise, avec chiffrement local et gestion des rôles utilisateur.

## 🚀 Fonctionnalités

### 🔐 Sécurité
- **Chiffrement AES-256** avec clés dérivées PBKDF2 (100,000 itérations)
- **Stockage local** - Aucune connexion cloud
- **Salage cryptographique** pour chaque utilisateur
- **Authentification par mot de passe** avec hachage bcrypt

### 👥 Gestion des Utilisateurs
- **Rôles hiérarchiques** : Admin, Manager, Utilisateur
- **Permissions granulaires** selon les rôles
- **Interface de gestion** des utilisateurs (admins seulement)
- **Changement de rôles** avec descriptions détaillées

### 🛠️ Fonctionnalités Avancées
- **Générateur de mots de passe** intégré
- **Historique des modifications** complet
- **Système de permissions** d'accès
- **Vérification d'intégrité** des données
- **Recherche et filtrage** des mots de passe
- **Catégorisation** des entrées

## 📋 Structure du Projet

```
password_manager/
├── Password manager.py          # Application principale
├── demo_features.py            # Démonstration des fonctionnalités
├── migrate_database.py         # Script de migration de base de données
├── test_encryption.py          # Tests de chiffrement
├── requirements.txt            # Dépendances Python
├── GUIDE_UTILISATION.md        # Guide utilisateur détaillé
└── Package_Distribution/       # Package prêt pour distribution
    ├── GestionnaireMotsDePasse.exe    # Exécutable standalone
    ├── GUIDE_UTILISATION.md           # Guide utilisateur
    ├── README.txt                     # Instructions rapides
    └── Lancer_GestionnaireMotsDePasse.bat  # Script de lancement
```

## 🔧 Installation

### Option 1: Utiliser l'exécutable (Recommandé)
1. Téléchargez le dossier `Package_Distribution`
2. Lancez `GestionnaireMotsDePasse.exe`
3. Première connexion : `admin` / `admin123`

### Option 2: Installation depuis les sources
1. Clonez le repository
2. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```
3. Lancez l'application :
   ```bash
   python "Password manager.py"
   ```

## 🎭 Rôles et Permissions

### 🔴 Administrateur
- ✅ Accès complet à tous les mots de passe
- ✅ Gestion des utilisateurs et rôles
- ✅ Suppression de tous les mots de passe
- ✅ Accès au panneau d'administration
- ✅ Gestion des permissions d'accès

### 🟡 Manager
- ✅ Accès complet à tous les mots de passe
- ✅ Suppression de tous les mots de passe
- ✅ Gestion des permissions d'accès
- ❌ Pas de gestion d'utilisateurs

### 🟢 Utilisateur
- ✅ Accès à ses propres mots de passe uniquement
- ✅ Création et modification de ses données
- ✅ Suppression de ses propres mots de passe
- ❌ Pas d'accès aux données des autres utilisateurs

## 🔍 Fonctionnalités Techniques

### Chiffrement
- **Algorithme** : AES-256 via Fernet (cryptography)
- **Dérivation de clé** : PBKDF2 avec SHA-256
- **Itérations** : 100,000 (recommandation OWASP)
- **Salage** : Unique par utilisateur, stocké en base

### Base de Données
- **Type** : SQLite (local)
- **Tables** : users, passwords, password_history, access_permissions
- **Sécurité** : Chiffrement au niveau application
- **Intégrité** : Vérifications automatiques

### Interface
- **Framework** : CustomTkinter (moderne, sombre)
- **Composants** : Treeview, dialogs, menus contextuels
- **Responsive** : Adaptation automatique de la taille
- **Accessibilité** : Raccourcis clavier, messages clairs

## 🚀 Déploiement

### Pour une équipe
1. **Compilez** l'exécutable avec PyInstaller
2. **Distribuez** le package à chaque utilisateur
3. **Chaque utilisateur** a sa propre base de données locale
4. **Aucune configuration** réseau requise

### Sécurité de déploiement
- ✅ Pas de données sensibles dans le code
- ✅ Chiffrement local uniquement
- ✅ Aucune dépendance cloud
- ✅ Audit trail complet

## 📊 Statistiques du Projet

- **Lignes de code** : ~1,400
- **Fichiers principaux** : 4
- **Dépendances** : 3 (customtkinter, cryptography, bcrypt)
- **Taille exécutable** : ~50 MB
- **Compatibilité** : Windows 10/11

## 🔄 Versions et Mises à Jour

### Version Actuelle : 1.0
- ✅ Fonctionnalités de base complètes
- ✅ Système de rôles implémenté
- ✅ Chiffrement sécurisé
- ✅ Interface utilisateur moderne
- ✅ Gestion des erreurs robuste

### Améliorations Futures
- 🔄 Sauvegarde automatique
- 🔄 Import/Export sécurisé
- 🔄 Authentification à deux facteurs
- 🔄 Thèmes personnalisables

## 🛡️ Sécurité et Conformité

### Bonnes Pratiques Implémentées
- ✅ Hachage des mots de passe avec bcrypt
- ✅ Chiffrement AES-256 des données sensibles
- ✅ Dérivation de clé sécurisée (PBKDF2)
- ✅ Salage cryptographique unique
- ✅ Pas de stockage en plain text
- ✅ Audit trail complet

### Recommandations d'Usage
- 🔒 Utilisez des mots de passe forts
- 🔒 Sauvegardez régulièrement la base de données
- 🔒 Limitez les accès physiques à la machine
- 🔒 Mettez à jour régulièrement l'application

## 📞 Support

Pour toute question ou problème :
1. Consultez le `GUIDE_UTILISATION.md`
2. Vérifiez les messages d'erreur dans l'application
3. Utilisez la fonction "🔍 Vérifier" pour diagnostiquer
4. Contactez l'administrateur système

## 📄 Licence

Ce projet est développé pour un usage interne en entreprise. Tous droits réservés.

---

**Développé avec ❤️ pour la sécurité des données en entreprise**
