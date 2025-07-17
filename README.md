# 📚 Relieur Virtuel de Documents

Application Python moderne pour fusionner facilement plusieurs documents (PDF, Word, Images) en un seul PDF professionnel avec table des matières automatique.

## 🚀 Fonctionnalités

- **📄 Support multi-formats** : PDF, Word (.docx, .doc), Images (.png, .jpg, .jpeg, .bmp, .gif, .tiff)
- **📋 Organisation en chapitres** : Structurez vos documents avec des chapitres personnalisés
- **👁️ Aperçu en temps réel** : Prévisualisez vos documents avant génération
- **🔨 Génération PDF avancée** : Table des matières automatique, pagination, styles professionnels
- **💾 Gestion de projets** : Sauvegardez et rechargez vos configurations
- **🎨 Interface moderne** : Interface CustomTkinter avec thèmes sombre/clair
- **🖥️ Plein écran** : Utilisation optimisée avec mode plein écran (F11/Échap)

## 📦 Installation

### Prérequis
- Python 3.8 ou supérieur
- Windows 10+ (optimisé pour Windows)

### Installation des dépendances
```bash
pip install -r requirements.txt
```

### Lancement de l'application
```bash
python pdf_manager.py
```

## 🎯 Utilisation

### 1. Ajouter des documents
- Cliquez sur **"📄 Ajouter PDF"** pour les fichiers PDF
- Cliquez sur **"📝 Ajouter Word"** pour les documents Word
- Cliquez sur **"🖼️ Ajouter Images"** pour les images

### 2. Organiser les documents
- Utilisez **"⬆️ Monter"** et **"⬇️ Descendre"** pour réorganiser
- Cliquez sur **"👁️"** pour prévisualiser un document
- Utilisez **"📋 Organiser Chapitres"** pour créer une structure

### 3. Générer le PDF final
- Cliquez sur **"🔨 Générer PDF"**
- Choisissez l'emplacement de sauvegarde
- Le PDF inclut automatiquement une table des matières

### 4. Gestion des projets
- **Menu Fichier > Nouveau projet** : Créer un nouveau projet
- **Menu Fichier > Sauvegarder projet** : Sauvegarder la configuration actuelle
- **Menu Fichier > Ouvrir projet** : Charger un projet existant

## 🛠️ Raccourcis clavier

- **F11** / **Échap** : Basculer entre plein écran et fenêtre normale
- **Ctrl+N** : Nouveau projet
- **Ctrl+S** : Sauvegarder projet
- **Ctrl+O** : Ouvrir projet

## 📁 Structure des fichiers

```
pdf_manager.py          # Application principale
requirements.txt        # Dépendances Python
README.md              # Documentation
```

## 🔧 Dépendances principales

- **CustomTkinter** : Interface utilisateur moderne
- **PyMuPDF (fitz)** : Traitement des fichiers PDF
- **python-docx** : Traitement des documents Word
- **ReportLab** : Génération de PDF avancée
- **Pillow (PIL)** : Traitement des images
- **PyInstaller** : Création d'exécutables (optionnel)

## 📊 Formats supportés

### Documents PDF
- ✅ Fichiers .pdf
- ✅ Toutes les pages converties en images haute qualité
- ✅ Préservation de la mise en page originale

### Documents Word
- ✅ Fichiers .docx et .doc
- ✅ Extraction du texte et formatage de base
- ✅ Conversion en paragraphes PDF

### Images
- ✅ PNG, JPG, JPEG, BMP, GIF, TIFF
- ✅ Redimensionnement automatique
- ✅ Préservation du ratio d'aspect

## 🔨 Création d'un exécutable

Pour créer un exécutable autonome :

```bash
pyinstaller --onefile --windowed --name=RelieurVirtuel pdf_manager.py
```

L'exécutable sera créé dans le dossier `dist/`.

## 🐛 Dépannage

### Problèmes de démarrage
- Vérifiez que Python 3.8+ est installé
- Installez toutes les dépendances : `pip install -r requirements.txt`
- Vérifiez les permissions d'exécution

### Problèmes de génération PDF
- Assurez-vous que les fichiers sources existent
- Vérifiez les droits d'écriture dans le dossier de sortie
- Contrôlez l'espace disque disponible

### Performance
- Les gros fichiers PDF peuvent ralentir l'aperçu
- La génération PDF peut prendre du temps selon le nombre de documents
- Utilisez le mode plein écran pour une meilleure expérience

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
- Signaler des bugs
- Proposer des améliorations
- Soumettre des pull requests

## 📞 Support

Pour toute question ou problème :
1. Consultez ce README
2. Vérifiez les issues existantes
3. Créez une nouvelle issue si nécessaire

---

**Relieur Virtuel v1.0** - Développé avec ❤️ en Python

*Créé le 17 juillet 2025*
