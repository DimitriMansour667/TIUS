import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pygame
import threading
import time
import os
import json
import random
import math
import numpy as np
from PIL import Image, ImageTk
import subprocess
import psutil
try:
    import win32gui
    import win32con
    import win32process
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    print("Win32 modules non disponibles - certaines fonctionnalités seront limitées")

try:
    from ctypes import cast, POINTER
    from comtypes import CLSID_MMDeviceEnumerator, CoInitialize, CoUninitialize
    from pycaw.pycaw import AudioUtilities, AudioSession
    AUDIO_CONTROL_AVAILABLE = True
except ImportError:
    AUDIO_CONTROL_AVAILABLE = False
    print("Contrôle audio avancé non disponible")

class LofiConcentrationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Lofi Concentration - Régulateur de Bruit")
        self.root.geometry("1000x700")
        self.root.configure(bg='#2a2a2a')
        
        # Variables d'état
        self.is_playing = False
        self.current_sound = None
        self.volume = 0.5
        self.fade_volume = 0.5
        self.concentration_mode = False
        self.auto_fade = True
        self.fade_in_progress = False
        
        # Configuration des sons
        self.sounds = {
            "Café": "sounds/cafe-noise-32940.mp3",
            "Forêt": "sounds/forest-ambience-296528.mp3",
            "Pluie": "sounds/calming-rain-257596.mp3",
            "Bruit blanc": "sounds/white_noise.wav",
            "Océan": "sounds/soothing-ocean-waves-372489.mp3",
            "Bibliothèque": "sounds/library-ambiance-60000.mp3",  # Utilise café comme bibliothèque
            "Cheminée": "sounds/crackling-fireplace-nature-sounds-8012.mp3",  # Utilise bruit blanc
            "Orage": "sounds/thunderstorm-14708.mp3"  # Utilise pluie
        }
        
        # Animation variables
        self.animation_frame = 0
        self.particles = []
        self.breathing_offset = 0
        
        # Configuration des processus à surveiller
        self.monitored_processes = ["Teams.exe", "Zoom.exe", "discord.exe", "slack.exe"]
        
        # Initialisation de pygame pour l'audio
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        
        # Création de l'interface
        self.create_ui()
        
        # Démarrage des threads de surveillance
        self.start_monitoring()
        
        # Démarrage de l'animation
        self.animate()
        
        # Chargement de la configuration
        self.load_config()
        
    def create_ui(self):
        # Frame principale avec style lofi
        main_frame = tk.Frame(self.root, bg='#2a2a2a')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Titre avec style lofi
        title_frame = tk.Frame(main_frame, bg='#2a2a2a')
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = tk.Label(title_frame, text="🎵 Lofi Concentration Space", 
                              font=('Arial', 24, 'bold'), fg='#e8b4a6', bg='#2a2a2a')
        title_label.pack()
        
        subtitle_label = tk.Label(title_frame, text="Régulateur de bruit pour open-space", 
                                 font=('Arial', 12), fg='#b8860b', bg='#2a2a2a')
        subtitle_label.pack()
        
        # Zone d'animation (style lofi girl)
        self.animation_canvas = tk.Canvas(main_frame, height=200, bg='#3c3c3c', 
                                        highlightthickness=0, relief='flat')
        self.animation_canvas.pack(fill=tk.X, pady=(0, 20))
        
        # Panneau de contrôle principal
        control_frame = tk.Frame(main_frame, bg='#2a2a2a')
        control_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Sélection du son
        sound_frame = tk.Frame(control_frame, bg='#2a2a2a')
        sound_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        tk.Label(sound_frame, text="Ambiance:", font=('Arial', 12, 'bold'), 
                fg='#e8b4a6', bg='#2a2a2a').pack(anchor=tk.W)
        
        self.sound_var = tk.StringVar(value="Café")
        self.sound_combo = ttk.Combobox(sound_frame, textvariable=self.sound_var, 
                                       values=list(self.sounds.keys()), 
                                       font=('Arial', 10), width=15)
        self.sound_combo.pack(pady=(5, 0))
        self.sound_combo.bind('<<ComboboxSelected>>', self.change_sound)
        
        # Contrôles de lecture
        play_frame = tk.Frame(control_frame, bg='#2a2a2a')
        play_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        tk.Label(play_frame, text="Contrôles:", font=('Arial', 12, 'bold'), 
                fg='#e8b4a6', bg='#2a2a2a').pack(anchor=tk.W)
        
        button_frame = tk.Frame(play_frame, bg='#2a2a2a')
        button_frame.pack(pady=(5, 0))
        
        self.play_button = tk.Button(button_frame, text="▶️ Play", 
                                    command=self.toggle_play, bg='#4a4a4a', 
                                    fg='white', font=('Arial', 10, 'bold'),
                                    relief='flat', padx=15)
        self.play_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_button = tk.Button(button_frame, text="⏹️ Stop", 
                                    command=self.stop_sound, bg='#4a4a4a', 
                                    fg='white', font=('Arial', 10, 'bold'),
                                    relief='flat', padx=15)
        self.stop_button.pack(side=tk.LEFT)
        
        # Contrôle du volume
        volume_frame = tk.Frame(control_frame, bg='#2a2a2a')
        volume_frame.pack(side=tk.LEFT)
        
        tk.Label(volume_frame, text="Volume:", font=('Arial', 12, 'bold'), 
                fg='#e8b4a6', bg='#2a2a2a').pack(anchor=tk.W)
        
        self.volume_scale = tk.Scale(volume_frame, from_=0, to=100, orient=tk.HORIZONTAL, 
                                    command=self.change_volume, bg='#3c3c3c', 
                                    fg='white', troughcolor='#4a4a4a', 
                                    highlightthickness=0, font=('Arial', 9))
        self.volume_scale.set(50)
        self.volume_scale.pack(pady=(5, 0))
        
        # Panneau de fonctionnalités avancées
        features_frame = tk.LabelFrame(main_frame, text="Fonctionnalités Avancées", 
                                     bg='#2a2a2a', fg='#e8b4a6', 
                                     font=('Arial', 12, 'bold'))
        features_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Options de fade automatique
        fade_frame = tk.Frame(features_frame, bg='#2a2a2a')
        fade_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.auto_fade_var = tk.BooleanVar(value=True)
        auto_fade_check = tk.Checkbutton(fade_frame, text="Fade automatique (appels/Teams)", 
                                       variable=self.auto_fade_var, 
                                       command=self.toggle_auto_fade,
                                       bg='#2a2a2a', fg='white', 
                                       font=('Arial', 10), selectcolor='#4a4a4a')
        auto_fade_check.pack(side=tk.LEFT)
        
        # Bouton pause concentration
        self.concentration_button = tk.Button(fade_frame, text="🎯 Mode Concentration", 
                                            command=self.toggle_concentration_mode,
                                            bg='#8b4513', fg='white', 
                                            font=('Arial', 11, 'bold'),
                                            relief='flat', padx=20)
        self.concentration_button.pack(side=tk.RIGHT)
        
        # Statut de surveillance
        status_frame = tk.Frame(features_frame, bg='#2a2a2a')
        status_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Label(status_frame, text="Surveillance:", font=('Arial', 10, 'bold'), 
                fg='#e8b4a6', bg='#2a2a2a').pack(side=tk.LEFT)
        
        self.status_label = tk.Label(status_frame, text="Actif - Aucune distraction détectée", 
                                   font=('Arial', 10), fg='#90EE90', bg='#2a2a2a')
        self.status_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Informations sur les processus surveillés
        info_frame = tk.Frame(main_frame, bg='#2a2a2a')
        info_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(info_frame, text="Processus surveillés:", font=('Arial', 11, 'bold'), 
                fg='#e8b4a6', bg='#2a2a2a').pack(anchor=tk.W)
        
        self.process_text = tk.Text(info_frame, height=8, bg='#3c3c3c', fg='white', 
                                   font=('Courier', 9), wrap=tk.WORD)
        self.process_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Scrollbar pour le texte
        scrollbar = tk.Scrollbar(info_frame, command=self.process_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.process_text.config(yscrollcommand=scrollbar.set)
        
        # Mise à jour initiale du texte d'info
        self.update_process_info()
        
    def animate(self):
        """Animation continue style lofi"""
        self.animation_frame += 1
        self.breathing_offset = math.sin(self.animation_frame * 0.02) * 5
        
        # Nettoyer le canvas
        self.animation_canvas.delete("all")
        
        # Dessiner le fond avec gradient
        canvas_width = self.animation_canvas.winfo_width()
        canvas_height = self.animation_canvas.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:
            # Effet de gradient simple
            for i in range(canvas_height):
                color_intensity = int(60 + (i / canvas_height) * 40)
                color = f"#{color_intensity:02x}{color_intensity:02x}{color_intensity:02x}"
                self.animation_canvas.create_line(0, i, canvas_width, i, fill=color)
            
            # Dessiner des particules flottantes
            self.update_particles(canvas_width, canvas_height)
            
            # Dessiner une "fille lofi" stylisée (forme simple)
            self.draw_lofi_scene(canvas_width, canvas_height)
        
        # Programmer la prochaine frame
        self.root.after(50, self.animate)
        
    def update_particles(self, width, height):
        """Mise à jour des particules flottantes"""
        # Ajouter de nouvelles particules
        if random.random() < 0.3:
            self.particles.append({
                'x': random.randint(0, width),
                'y': height,
                'speed': random.uniform(0.5, 2),
                'size': random.randint(1, 3),
                'color': random.choice(['#ffebb3', '#e8b4a6', '#d4a574'])
            })
        
        # Mettre à jour les particules existantes
        for particle in self.particles[:]:
            particle['y'] -= particle['speed']
            particle['x'] += math.sin(particle['y'] * 0.01) * 0.5
            
            if particle['y'] < 0:
                self.particles.remove(particle)
            else:
                self.animation_canvas.create_oval(
                    particle['x'] - particle['size'],
                    particle['y'] - particle['size'],
                    particle['x'] + particle['size'],
                    particle['y'] + particle['size'],
                    fill=particle['color'], outline=""
                )
                
    def draw_lofi_scene(self, width, height):
        """Dessiner une scène lofi stylisée"""
        # Bureau/table
        table_y = height - 40
        self.animation_canvas.create_rectangle(
            50, table_y, width - 50, height - 20,
            fill='#8b4513', outline='#654321', width=2
        )
        
        # Ordinateur portable
        laptop_x = width // 2 - 30
        laptop_y = table_y - 25
        self.animation_canvas.create_rectangle(
            laptop_x, laptop_y, laptop_x + 60, laptop_y + 20,
            fill='#2a2a2a', outline='#1a1a1a', width=2
        )
        
        # Écran avec effet de respiration
        screen_offset = self.breathing_offset * 0.3
        screen_color = '#4a4a4a' if self.is_playing else '#2a2a2a'
        self.animation_canvas.create_rectangle(
            laptop_x + 5, laptop_y + 3 + screen_offset,
            laptop_x + 55, laptop_y + 17 + screen_offset,
            fill=screen_color, outline='#6a6a6a'
        )
        
        # Plante
        plant_x = width - 120
        plant_y = table_y - 30
        self.animation_canvas.create_rectangle(
            plant_x, plant_y + 15, plant_x + 15, plant_y + 25,
            fill='#8b4513', outline='#654321'
        )
        
        # Feuilles qui bougent légèrement
        leaf_offset = math.sin(self.animation_frame * 0.03) * 2
        self.animation_canvas.create_oval(
            plant_x + 5 + leaf_offset, plant_y + leaf_offset,
            plant_x + 20 + leaf_offset, plant_y + 15 + leaf_offset,
            fill='#228b22', outline='#006400'
        )
        
        # Tasse de café avec vapeur
        cup_x = laptop_x - 40
        cup_y = table_y - 15
        self.animation_canvas.create_rectangle(
            cup_x, cup_y + 5, cup_x + 15, cup_y + 15,
            fill='#f5deb3', outline='#daa520'
        )
        
        # Vapeur qui monte
        if self.is_playing:
            for i in range(3):
                steam_x = cup_x + 7 + math.sin(self.animation_frame * 0.1 + i) * 2
                steam_y = cup_y - i * 10
                self.animation_canvas.create_text(
                    steam_x, steam_y, text="~", fill='#dcdcdc', font=('Arial', 8)
                )
        
        # Indicateur de statut
        status_color = '#90EE90' if not self.concentration_mode else '#ff6b6b'
        status_text = "Zen Mode" if self.is_playing else "Paused"
        self.animation_canvas.create_text(
            width - 80, 20, text=status_text, fill=status_color, font=('Arial', 12, 'bold')
        )
        
    def toggle_play(self):
        """Basculer entre lecture et pause"""
        if self.is_playing:
            self.pause_sound()
        else:
            self.play_sound()
            
    def play_sound(self):
        """Jouer le son sélectionné"""
        if not self.is_playing:
            sound_name = self.sound_var.get()
            sound_file = self.sounds.get(sound_name, "cafe_ambiance.mp3")
            
            # Créer le fichier de son si nécessaire (sons générés)
            self.ensure_sound_file(sound_file)
            
            try:
                pygame.mixer.music.load(sound_file)
                pygame.mixer.music.play(-1)  # Loop infini
                pygame.mixer.music.set_volume(self.volume)
                
                self.is_playing = True
                self.play_button.config(text="⏸️ Pause")
                self.update_status("Lecture en cours")
                
            except pygame.error as e:
                messagebox.showerror("Erreur", f"Impossible de jouer le son: {e}")
                
    def pause_sound(self):
        """Mettre en pause le son"""
        if self.is_playing:
            pygame.mixer.music.pause()
            self.is_playing = False
            self.play_button.config(text="▶️ Play")
            self.update_status("En pause")
            
    def stop_sound(self):
        """Arrêter le son"""
        pygame.mixer.music.stop()
        self.is_playing = False
        self.play_button.config(text="▶️ Play")
        self.update_status("Arrêté")
        
    def change_sound(self, event=None):
        """Changer le son d'ambiance"""
        if self.is_playing:
            self.stop_sound()
            self.play_sound()
            
    def change_volume(self, value):
        """Changer le volume"""
        self.volume = float(value) / 100
        if not self.fade_in_progress:
            pygame.mixer.music.set_volume(self.volume)
            
    def toggle_auto_fade(self):
        """Basculer le fade automatique"""
        self.auto_fade = self.auto_fade_var.get()
        if self.auto_fade:
            self.update_status("Fade automatique activé")
        else:
            self.update_status("Fade automatique désactivé")
            
    def toggle_concentration_mode(self):
        """Basculer le mode concentration"""
        self.concentration_mode = not self.concentration_mode
        
        if self.concentration_mode:
            self.concentration_button.config(text="🔓 Quitter Mode Concentration", bg='#ff6b6b')
            self.block_distractions()
            self.update_status("Mode concentration activé")
        else:
            self.concentration_button.config(text="🎯 Mode Concentration", bg='#8b4513')
            self.unblock_distractions()
            self.update_status("Mode concentration désactivé")
            
    def block_distractions(self):
        """Bloquer les distractions (minimiser les fenêtres)"""
        if not WIN32_AVAILABLE:
            messagebox.showwarning("Fonctionnalité limitée", 
                                 "Le blocage des distractions nécessite les modules win32.\n"
                                 "Installez: pip install pywin32")
            return
            
        distraction_apps = [
            "chrome.exe", "firefox.exe", "msedge.exe",
            "discord.exe", "WhatsApp.exe", "Telegram.exe",
            "spotify.exe", "steam.exe"
        ]
        
        blocked_count = 0
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'].lower() in [app.lower() for app in distraction_apps]:
                    # Trouver et minimiser la fenêtre
                    def enum_handler(hwnd, results):
                        if win32gui.IsWindowVisible(hwnd):
                            _, pid = win32process.GetWindowThreadProcessId(hwnd)
                            if pid == proc.info['pid']:
                                win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                                results.append(hwnd)
                    
                    results = []
                    win32gui.EnumWindows(enum_handler, results)
                    if results:
                        blocked_count += 1
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
        if blocked_count > 0:
            self.update_status(f"Mode concentration: {blocked_count} distractions bloquées")
        else:
            self.update_status("Mode concentration: aucune distraction détectée")
            
    def unblock_distractions(self):
        """Débloquer les distractions"""
        self.update_status("Distractions débloquées")
        
    def start_monitoring(self):
        """Démarrer la surveillance des processus"""
        def monitor():
            while True:
                try:
                    self.check_for_distractions()
                    time.sleep(2)  # Vérifier toutes les 2 secondes
                except Exception as e:
                    print(f"Erreur de surveillance: {e}")
                    time.sleep(5)
                    
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
        
    def check_for_distractions(self):
        """Vérifier les distractions et appliquer le fade si nécessaire"""
        if not self.auto_fade or not self.is_playing:
            return
            
        distraction_detected = False
        active_distractions = []
        
        # Vérifier les processus surveillés
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] in self.monitored_processes:
                    active_distractions.append(proc.info['name'])
                    distraction_detected = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
        # Appliquer le fade si nécessaire
        if distraction_detected and not self.fade_in_progress:
            self.apply_fade_out()
            self.root.after(0, lambda: self.update_status(f"Fade appliqué: {', '.join(active_distractions)}"))
        elif not distraction_detected and self.fade_in_progress:
            self.apply_fade_in()
            self.root.after(0, lambda: self.update_status("Fade restauré"))
            
    def apply_fade_out(self):
        """Appliquer un fade out"""
        self.fade_in_progress = True
        self.fade_volume = self.volume * 0.2  # Réduire à 20%
        pygame.mixer.music.set_volume(self.fade_volume)
        
    def apply_fade_in(self):
        """Appliquer un fade in"""
        self.fade_in_progress = False
        pygame.mixer.music.set_volume(self.volume)
        
    def update_status(self, message):
        """Mettre à jour le statut"""
        self.status_label.config(text=message)
        
    def update_process_info(self):
        """Mettre à jour les informations sur les processus"""
        info_text = "Processus surveillés pour le fade automatique:\n"
        info_text += "• Teams, Zoom, Discord, Slack\n\n"
        info_text += "Distractions bloquées en mode concentration:\n"
        info_text += "• Navigateurs (Chrome, Firefox, Edge)\n"
        info_text += "• Réseaux sociaux (Discord, WhatsApp, Telegram)\n"
        info_text += "• Divertissement (Spotify, Steam)\n\n"
        info_text += "Fonctionnalités:\n"
        info_text += "• Fade automatique lors d'appels\n"
        info_text += "• Mode concentration avec blocage de distractions\n"
        info_text += "• Sons d'ambiance en boucle\n"
        info_text += "• Interface animée style lofi\n"
        
        self.process_text.delete(1.0, tk.END)
        self.process_text.insert(tk.END, info_text)
        
    def ensure_sound_file(self, filename):
        """S'assurer que le fichier son existe (générer si nécessaire)"""
        if not os.path.exists(filename):
            # Créer le dossier sounds s'il n'existe pas
            sounds_dir = os.path.dirname(filename)
            if not os.path.exists(sounds_dir):
                os.makedirs(sounds_dir)
            
            # Générer les fichiers audio si nécessaire
            try:
                from generate_sounds import create_sound_files
                create_sound_files()
            except ImportError:
                messagebox.showwarning("Fichiers audio manquants", 
                                     f"Le fichier {filename} n'existe pas.\n"
                                     "Lancez 'python generate_sounds.py' pour créer les fichiers audio.")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la génération des sons: {e}")
            
    def generate_sound_file(self, filename):
        """Générer un fichier son simple (version simplifiée)"""
        messagebox.showinfo("Génération de sons", 
                          "Pour une meilleure qualité audio, lancez:\n"
                          "python generate_sounds.py\n\n"
                          "Cela créera des fichiers audio optimisés.")
            
    def load_config(self):
        """Charger la configuration"""
        try:
            if os.path.exists("concentration_config.json"):
                with open("concentration_config.json", "r") as f:
                    config = json.load(f)
                    self.volume = config.get("volume", 0.5)
                    self.auto_fade = config.get("auto_fade", True)
                    self.volume_scale.set(self.volume * 100)
                    self.auto_fade_var.set(self.auto_fade)
        except Exception as e:
            print(f"Erreur lors du chargement de la configuration: {e}")
            
    def save_config(self):
        """Sauvegarder la configuration"""
        try:
            config = {
                "volume": self.volume,
                "auto_fade": self.auto_fade,
                "last_sound": self.sound_var.get()
            }
            with open("concentration_config.json", "w") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde: {e}")
            
    def on_closing(self):
        """Gérer la fermeture de l'application"""
        self.save_config()
        pygame.mixer.quit()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = LofiConcentrationApp(root)
    
    # Gérer la fermeture
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Démarrer l'application
    root.mainloop()

if __name__ == "__main__":
    main()
