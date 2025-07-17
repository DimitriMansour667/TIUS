# 🎵 Lofi Concentration - Régulateur de Bruit

## Description
Application de concentration avec interface animée inspirée de Lofi Girl. Conçue pour les environnements de travail en open-space avec des fonctionnalités avancées de gestion du bruit et des distractions.

## Fonctionnalités Principales

### 🎧 Sons d'Ambiance
- **Café** : Ambiance de café avec conversations légères
- **Forêt** : Sons de nature et oiseaux
- **Pluie** : Pluie douce et relaxante
- **Bruit blanc** : Masquage sonore optimal
- **Océan** : Vagues et ambiance marine
- **Bibliothèque** : Atmosphère studieuse
- **Cheminée** : Crépitement relaxant
- **Orage** : Ambiance dramatique

### 🎯 Mode Concentration
- **Blocage automatique** des applications distrayantes
- **Minimisation** des fenêtres de réseaux sociaux
- **Pause concentration** en un clic
- **Restauration** automatique en fin de session

### 🔊 Fade Automatique
- **Détection automatique** des appels (Teams, Zoom, Discord, Slack)
- **Réduction progressive** du volume (fade out)
- **Restauration** automatique après l'appel
- **Configuration personnalisable**

### 🎨 Interface Animée
- **Style Lofi Girl** avec animations fluides
- **Particules flottantes** et effets visuels
- **Scène interactive** qui réagit à l'état de l'app
- **Indicateurs visuels** en temps réel

## Installation

1. **Cloner ou télécharger** le projet
2. **Installer les dépendances** :
   ```bash
   pip install -r requirements.txt
   ```
3. **Lancer l'application** :
   ```bash
   python concentration_app.py
   ```

## Utilisation

### Contrôles de Base
1. **Sélectionner une ambiance** dans la liste déroulante
2. **Cliquer sur Play** pour démarrer la lecture
3. **Ajuster le volume** avec le slider
4. **Utiliser Stop** pour arrêter complètement

### Fonctionnalités Avancées
- **Fade automatique** : Cochez pour activer la réduction automatique lors d'appels
- **Mode Concentration** : Cliquez pour bloquer les distractions
- **Surveillance** : Monitoring temps réel des processus

### Processus Surveillés
- **Appels** : Teams.exe, Zoom.exe, Discord.exe, Slack.exe
- **Distractions** : Navigateurs, réseaux sociaux, jeux, streaming

## Configuration

L'application sauvegarde automatiquement :
- Volume préféré
- État du fade automatique
- Dernière ambiance utilisée

Configuration dans : `concentration_config.json`

## Compatibilité

- **Windows 10/11** (testé)
- **Python 3.8+**
- **Audio** : Fichiers MP3/WAV

## Dépendances Principales

- **pygame** : Lecture audio
- **tkinter** : Interface graphique
- **psutil** : Monitoring des processus
- **pycaw** : Contrôle audio Windows
- **PIL** : Traitement d'images
- **numpy** : Calculs numériques

## Personnalisation

### Ajouter des Sons
1. Placez vos fichiers audio dans le dossier de l'app
2. Modifiez le dictionnaire `sounds` dans le code
3. Formats supportés : MP3, WAV, OGG

### Modifier la Surveillance
- Éditez `monitored_processes` pour les appels
- Modifiez `distraction_apps` pour le mode concentration

## Dépannage

### Problèmes Audio
- Vérifiez que pygame est installé correctement
- Assurez-vous que les fichiers audio sont accessibles
- Redémarrez l'application si le son ne fonctionne pas

### Problèmes de Permissions
- Exécutez en tant qu'administrateur si nécessaire
- Vérifiez les permissions d'accès aux processus

### Performance
- Réduisez la fréquence d'animation si nécessaire
- Fermez les applications non utilisées

## Développement

### Structure du Code
```
concentration_app.py
├── LofiConcentrationApp (classe principale)
├── Interface UI (tkinter)
├── Gestion Audio (pygame)
├── Animation (canvas)
├── Surveillance (psutil)
└── Configuration (json)
```

### Contribuer
1. Fork le projet
2. Créer une branche feature
3. Commit vos modifications
4. Push vers la branche
5. Créer une Pull Request

## Licence
MIT License - Voir le fichier LICENSE pour plus de détails

## Support
Pour toute question ou problème, créez une issue sur le dépôt GitHub.

---
*Inspiré par la communauté Lofi Girl 🎵*
