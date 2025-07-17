import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import json
import os
from datetime import datetime

class PostIt:
    def __init__(self, app, x=100, y=100, width=200, height=150, color="#FFFF99", text="", note_id=None):
        self.app = app  # Référence à l'application PostItApp
        self.root = app.root  # Référence à la fenêtre Tkinter
        self.note_id = note_id or datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        self.color = color
        self.is_dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.is_resizing = False
        self.resize_start_x = 0
        self.resize_start_y = 0
        self.start_width = 0
        self.start_height = 0
        
        # Créer la fenêtre du post-it
        self.window = tk.Toplevel(self.root)
        self.window.title("Post-it")
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        self.window.configure(bg=color)
        self.window.attributes("-topmost", True)  # Toujours au premier plan
        self.window.resizable(True, True)
        
        # Supprimer la barre de titre par défaut
        self.window.overrideredirect(True)
        
        # Créer la barre de titre personnalisée
        self.create_title_bar()
        
        # Zone de texte avec style moderne
        self.text_area = tk.Text(self.window, wrap=tk.WORD, 
                                font=("Segoe UI", 11),
                                bg=color, fg="#2C3E50", 
                                bd=0, padx=8, pady=8,
                                selectbackground="#3498DB",
                                selectforeground="white",
                                insertbackground="#2C3E50",
                                relief=tk.FLAT)
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
        
        # Ajuster le padding pour compenser la barre de titre
        self.text_area.pack_configure(pady=(31, 20))
        
        # Créer la zone de redimensionnement
        self.create_resize_grip()
        
        # Insérer le texte initial
        if text:
            self.text_area.insert(tk.END, text)
        
        # Événements pour le déplacement
        self.title_bar.bind("<Button-1>", self.start_drag)
        self.title_bar.bind("<B1-Motion>", self.on_drag)
        self.title_bar.bind("<ButtonRelease-1>", self.stop_drag)
        
        # Ajouter aussi le déplacement sur le titre
        self.title_label.bind("<Button-1>", self.start_drag)
        self.title_label.bind("<B1-Motion>", self.on_drag)
        self.title_label.bind("<ButtonRelease-1>", self.stop_drag)
        
        # Événement pour sauvegarder automatiquement
        self.text_area.bind("<KeyRelease>", self.auto_save)
        
        # Événement pour fermer avec Escape
        self.window.bind("<Escape>", lambda e: self.close_note())
        
        # Double-clic sur la barre de titre pour supprimer rapidement
        self.title_bar.bind("<Double-Button-1>", lambda e: self.close_note())
        self.title_label.bind("<Double-Button-1>", lambda e: self.close_note())
        
        self.window.focus_set()
    
    def create_resize_grip(self):
        """Crée une zone de redimensionnement dans le coin inférieur droit"""
        self.resize_grip = tk.Frame(self.window, bg=self.color, width=15, height=15, cursor="bottom_right_corner")
        self.resize_grip.place(relx=1.0, rely=1.0, anchor="se")
        
        # Ajouter des lignes visuelles pour indiquer la zone de redimensionnement
        canvas = tk.Canvas(self.resize_grip, width=15, height=15, bg=self.color, highlightthickness=0)
        canvas.pack()
        
        # Dessiner les lignes de grip
        canvas.create_line(10, 15, 15, 10, fill="#7F8C8D", width=1)
        canvas.create_line(7, 15, 15, 7, fill="#7F8C8D", width=1)
        canvas.create_line(4, 15, 15, 4, fill="#7F8C8D", width=1)
        
        # Événements pour le redimensionnement
        self.resize_grip.bind("<Button-1>", self.start_resize)
        self.resize_grip.bind("<B1-Motion>", self.on_resize)
        self.resize_grip.bind("<ButtonRelease-1>", self.stop_resize)
        canvas.bind("<Button-1>", self.start_resize)
        canvas.bind("<B1-Motion>", self.on_resize)
        canvas.bind("<ButtonRelease-1>", self.stop_resize)
        
        # Événements globaux pour permettre le redimensionnement même si la souris sort du grip
        self.window.bind("<Motion>", self.check_resize_cursor)
    
    def check_resize_cursor(self, event):
        """Change le curseur quand on s'approche du coin inférieur droit"""
        window_width = self.window.winfo_width()
        window_height = self.window.winfo_height()
        
        # Zone de 20x20 pixels dans le coin inférieur droit
        if (event.x > window_width - 20 and event.y > window_height - 20):
            self.window.configure(cursor="bottom_right_corner")
        else:
            self.window.configure(cursor="")
    
    def start_resize(self, event):
        """Commence le redimensionnement du post-it"""
        self.is_resizing = True
        self.resize_start_x = event.x_root
        self.resize_start_y = event.y_root
        self.start_width = self.window.winfo_width()
        self.start_height = self.window.winfo_height()
        
        # Capturer les événements globaux de la souris pour le redimensionnement
        self.window.bind("<B1-Motion>", self.on_resize_global)
        self.window.bind("<ButtonRelease-1>", self.stop_resize_global)
    
    def on_resize_global(self, event):
        """Redimensionne le post-it avec événements globaux"""
        if self.is_resizing:
            # Calculer la nouvelle taille
            delta_x = event.x_root - self.resize_start_x
            delta_y = event.y_root - self.resize_start_y
            
            new_width = max(150, self.start_width + delta_x)  # Largeur minimum 150px
            new_height = max(100, self.start_height + delta_y)  # Hauteur minimum 100px
            
            # Appliquer la nouvelle taille
            self.window.geometry(f"{new_width}x{new_height}")
    
    def stop_resize_global(self, event):
        """Arrête le redimensionnement avec événements globaux"""
        if self.is_resizing:
            self.is_resizing = False
            # Retirer les événements globaux
            self.window.unbind("<B1-Motion>")
            self.window.unbind("<ButtonRelease-1>")
            self.app.save_notes()  # Sauvegarder la nouvelle taille
    
    def on_resize(self, event):
        """Redimensionne le post-it"""
        if self.is_resizing:
            # Calculer la nouvelle taille
            delta_x = event.x_root - self.resize_start_x
            delta_y = event.y_root - self.resize_start_y
            
            new_width = max(150, self.start_width + delta_x)  # Largeur minimum 150px
            new_height = max(100, self.start_height + delta_y)  # Hauteur minimum 100px
            
            # Appliquer la nouvelle taille
            self.window.geometry(f"{new_width}x{new_height}")
    
    def stop_resize(self, event):
        """Arrête le redimensionnement"""
        self.is_resizing = False
        self.app.save_notes()  # Sauvegarder la nouvelle taille
    
    def create_title_bar(self):
        """Crée une barre de titre personnalisée moderne"""
        self.title_bar = tk.Frame(self.window, bg=self.color, height=28)
        self.title_bar.pack(fill=tk.X, side=tk.TOP)
        self.title_bar.pack_propagate(False)
        
        # Bouton pour changer la couleur avec style moderne
        color_btn = tk.Button(self.title_bar, text="🎨", 
                             font=("Segoe UI", 9),
                             command=self.change_color, 
                             bg=self.color,
                             relief=tk.FLAT, 
                             width=3, height=1,
                             cursor="hand2",
                             bd=0)
        color_btn.pack(side=tk.LEFT, padx=3, pady=3)
        
        # Titre (zone de déplacement) avec police moderne
        self.title_label = tk.Label(self.title_bar, text="📝 Post-it", 
                                   bg=self.color, 
                                   font=("Segoe UI", 10, "bold"),
                                   fg="#2C3E50")
        self.title_label.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=8)
        
        # Bouton pour minimiser/restaurer
        minimize_btn = tk.Button(self.title_bar, text="➖", 
                               font=("Segoe UI", 9),
                               command=self.minimize_note, 
                               bg=self.color,
                               relief=tk.FLAT, 
                               width=3, height=1,
                               cursor="hand2",
                               bd=0)
        minimize_btn.pack(side=tk.RIGHT, padx=2, pady=3)
        
        # Bouton pour fermer avec style moderne
        close_btn = tk.Button(self.title_bar, text="❌", 
                             font=("Segoe UI", 9),
                             command=self.close_note, 
                             bg=self.color,
                             relief=tk.FLAT, 
                             width=3, height=1,
                             cursor="hand2",
                             bd=0)
        close_btn.pack(side=tk.RIGHT, padx=2, pady=3)
    
    def start_drag(self, event):
        """Commence le déplacement du post-it"""
        self.is_dragging = True
        self.drag_start_x = event.x_root - self.window.winfo_x()
        self.drag_start_y = event.y_root - self.window.winfo_y()
    
    def on_drag(self, event):
        """Déplace le post-it"""
        if self.is_dragging:
            x = event.x_root - self.drag_start_x
            y = event.y_root - self.drag_start_y
            self.window.geometry(f"+{x}+{y}")
    
    def stop_drag(self, event):
        """Arrête le déplacement"""
        self.is_dragging = False
        self.app.save_notes()  # Sauvegarder la position
    
    def change_color(self):
        """Change la couleur du post-it"""
        color = colorchooser.askcolor(color=self.color)[1]
        if color:
            self.color = color
            self.window.configure(bg=color)
            self.title_bar.configure(bg=color)
            self.title_label.configure(bg=color)
            self.text_area.configure(bg=color)
            self.resize_grip.configure(bg=color)
            # Mettre à jour tous les boutons de la barre de titre
            for widget in self.title_bar.winfo_children():
                if isinstance(widget, tk.Button):
                    widget.configure(bg=color)
            # Mettre à jour le canvas du grip
            for widget in self.resize_grip.winfo_children():
                if isinstance(widget, tk.Canvas):
                    widget.configure(bg=color)
            self.app.save_notes()
    
    def minimize_note(self):
        """Minimise ou restaure le post-it"""
        if self.window.winfo_viewable():
            self.window.withdraw()  # Cacher
        else:
            self.window.deiconify()  # Afficher
    
    def close_note(self):
        """Ferme le post-it"""
        result = messagebox.askyesno("Confirmation", "Voulez-vous vraiment supprimer ce post-it ?", 
                                   parent=self.window)
        if result:
            self.app.remove_note(self.note_id)
            self.window.destroy()
    
    def auto_save(self, event=None):
        """Sauvegarde automatique du contenu"""
        self.app.save_notes()
    
    def get_data(self):
        """Retourne les données du post-it pour la sauvegarde"""
        return {
            "id": self.note_id,
            "x": self.window.winfo_x(),
            "y": self.window.winfo_y(),
            "width": self.window.winfo_width(),
            "height": self.window.winfo_height(),
            "color": self.color,
            "text": self.text_area.get(1.0, tk.END).strip()
        }

class PostItApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("📝 Gestionnaire de Post-its")
        self.root.geometry("450x650")
        self.root.configure(bg="#1A1A2E")
        self.root.resizable(False, False)
        
        # Essayer de centrer la fenêtre
        self.center_window()
        
        # Liste des post-its
        self.notes = {}
        self.notes_file = "post_its.json"
        
        # Interface principale
        self.create_main_interface()
        
        # Charger les notes sauvegardées
        self.load_notes()
        
        # Protocole de fermeture
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Raccourcis clavier
        self.root.bind("<Control-n>", lambda e: self.create_new_note())
        self.root.bind("<Control-N>", lambda e: self.create_new_note())
    
    def center_window(self):
        """Centre la fenêtre sur l'écran"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_modern_button(self, parent, text, command, bg_color, hover_color, icon=""):
        """Crée un bouton moderne avec effets de survol"""
        button_frame = tk.Frame(parent, bg="#1A1A2E")
        button_frame.pack(pady=8, padx=30, fill=tk.X)
        
        button = tk.Button(button_frame, 
                          text=f"{icon} {text}",
                          font=("Segoe UI", 12, "bold"),
                          bg=bg_color,
                          fg="white",
                          command=command,
                          relief=tk.FLAT,
                          bd=0,
                          padx=25,
                          pady=12,
                          cursor="hand2")
        button.pack(fill=tk.X)
        
        # Effets de survol
        def on_enter(e):
            button.configure(bg=hover_color)
        
        def on_leave(e):
            button.configure(bg=bg_color)
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        
        return button
    
    def create_main_interface(self):
        """Crée l'interface principale de gestion"""
        # Container principal avec padding
        main_container = tk.Frame(self.root, bg="#1A1A2E")
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header avec titre et gradient visuel
        header_frame = tk.Frame(main_container, bg="#16213E", relief=tk.FLAT, bd=0)
        header_frame.pack(fill=tk.X, pady=25)
        
        # Titre principal
        title_label = tk.Label(header_frame, 
                              text="📝 POST-ITS MANAGER",
                              font=("Segoe UI", 24, "bold"),
                              bg="#16213E", 
                              fg="#E74C3C",
                              pady=20)
        title_label.pack()
        
        # Sous-titre
        subtitle_label = tk.Label(header_frame,
                                 text="",
                                 font=("Segoe UI", 11, "italic"),
                                 bg="#16213E",
                                 fg="#BDC3C7")
        subtitle_label.pack(pady=15)
        
        # Section boutons principaux
        buttons_section = tk.Frame(main_container, bg="#1A1A2E")
        buttons_section.pack(fill=tk.X, pady=20)
        
        # Titre section
        section_title = tk.Label(buttons_section,
                                text="ACTIONS PRINCIPALES",
                                font=("Segoe UI", 10, "bold"),
                                bg="#1A1A2E",
                                fg="#7F8C8D")
        section_title.pack(anchor=tk.W, padx=30, pady=10)
        
        # Boutons modernes
        self.create_modern_button(buttons_section, "Nouveau Post-it", 
                                 self.create_new_note, "#27AE60", "#229954", "➕")
        
        self.create_modern_button(buttons_section, "Afficher Tous", 
                                 self.show_all_notes, "#3498DB", "#2980B9", "👁️")
        
        self.create_modern_button(buttons_section, "Masquer Tous", 
                                 self.hide_all_notes, "#E67E22", "#D35400", "🙈")
        
        self.create_modern_button(buttons_section, "Supprimer Tous", 
                                 self.delete_all_notes, "#E74C3C", "#C0392B", "🗑️")
        
        # Statistiques
        stats_frame = tk.Frame(main_container, bg="#16213E", relief=tk.FLAT, bd=0)
        stats_frame.pack(fill=tk.X, pady=20)
        
        stats_title = tk.Label(stats_frame,
                              text="STATISTIQUES",
                              font=("Segoe UI", 10, "bold"),
                              bg="#16213E",
                              fg="#7F8C8D")
        stats_title.pack(pady=15)
        
        # Compteur de notes avec style moderne
        self.counter_label = tk.Label(stats_frame, 
                                     text="Post-its actifs: 0",
                                     font=("Segoe UI", 14, "bold"),
                                     bg="#16213E", 
                                     fg="#F39C12")
        self.counter_label.pack(pady=15)
        
        # Section aide/raccourcis
        help_frame = tk.LabelFrame(main_container, 
                                  text=" 🎯 RACCOURCIS & AIDE ",
                                  font=("Segoe UI", 10, "bold"),
                                  bg="#0E1628", 
                                  fg="#BDC3C7",
                                  relief=tk.FLAT,
                                  bd=1,
                                  labelanchor=tk.N)
        help_frame.pack(fill=tk.X, pady=10)
        
        help_text = """🖱️  Glisser la barre de titre pour déplacer les post-its
🎨  Cliquer sur l'icône palette pour changer la couleur
➖  Bouton minimiser pour cacher/afficher
❌  Bouton fermer ou Échap pour supprimer
🖱️  Double-clic sur le titre pour suppression rapide
📏  Glisser le coin inférieur droit pour redimensionner
⌨️  Ctrl+N pour créer un nouveau post-it
💾  Sauvegarde automatique de vos notes"""
        
        help_label = tk.Label(help_frame, 
                             text=help_text,
                             font=("Segoe UI", 9),
                             bg="#0E1628", 
                             fg="#95A5A6",
                             justify=tk.LEFT)
        help_label.pack(padx=20, pady=15)
        
        # Footer
        footer_frame = tk.Frame(main_container, bg="#1A1A2E")
        footer_frame.pack(fill=tk.X, pady=15)
        
        footer_label = tk.Label(footer_frame,
                               text="✨ Votre productivité n'a plus de limites ✨",
                               font=("Segoe UI", 9, "italic"),
                               bg="#1A1A2E",
                               fg="#7F8C8D")
        footer_label.pack()
    
    def create_new_note(self):
        """Crée un nouveau post-it"""
        # Position décalée pour éviter la superposition
        offset = len(self.notes) * 30
        x = 150 + offset
        y = 150 + offset
        
        # Créer le post-it
        note = PostIt(self, x=x, y=y)  # Passer self (PostItApp) au lieu de self.root
        self.notes[note.note_id] = note
        
        # Mettre à jour le compteur
        self.update_counter()
        
        # Sauvegarder
        self.save_notes()
    
    def show_all_notes(self):
        """Affiche tous les post-its"""
        for note in self.notes.values():
            note.window.deiconify()
    
    def hide_all_notes(self):
        """Masque tous les post-its"""
        for note in self.notes.values():
            note.window.withdraw()
    
    def delete_all_notes(self):
        """Supprime tous les post-its"""
        if len(self.notes) == 0:
            messagebox.showinfo("Information", "Aucun post-it à supprimer.")
            return
            
        result = messagebox.askyesno("Confirmation", 
                              f"Voulez-vous vraiment supprimer tous les {len(self.notes)} post-its ?")
        if result:
            # Créer une copie de la liste des IDs pour éviter les erreurs
            note_ids = list(self.notes.keys())
            for note_id in note_ids:
                try:
                    self.notes[note_id].window.destroy()
                    del self.notes[note_id]
                except:
                    pass
            self.notes.clear()
            self.update_counter()
            self.save_notes()
    
    def remove_note(self, note_id):
        """Supprime un post-it spécifique"""
        if note_id in self.notes:
            del self.notes[note_id]
            self.update_counter()
            self.save_notes()
    
    def update_counter(self):
        """Met à jour le compteur de post-its"""
        count = len(self.notes)
        if count == 0:
            status_text = "Aucun post-it actif"
            color = "#7F8C8D"
        elif count == 1:
            status_text = "1 post-it actif"
            color = "#F39C12"
        else:
            status_text = f"{count} post-its actifs"
            color = "#27AE60"
        
        self.counter_label.configure(text=status_text, fg=color)
    
    def save_notes(self):
        """Sauvegarde tous les post-its dans un fichier JSON"""
        notes_data = []
        for note_id, note in list(self.notes.items()):
            try:
                # Vérifier que la fenêtre existe encore
                if note.window.winfo_exists():
                    data = note.get_data()
                    if data.get('text', '').strip():  # Sauvegarder seulement les notes non vides
                        notes_data.append(data)
                else:
                    # Supprimer la note si la fenêtre n'existe plus
                    if note_id in self.notes:
                        del self.notes[note_id]
            except Exception as e:
                print(f"Erreur lors de la sauvegarde de la note {note_id}: {e}")
                # Supprimer la note problématique
                if note_id in self.notes:
                    del self.notes[note_id]
        
        try:
            with open(self.notes_file, 'w', encoding='utf-8') as f:
                json.dump(notes_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erreur lors de l'écriture du fichier: {e}")
        
        # Mettre à jour le compteur après le nettoyage
        self.update_counter()
    
    def load_notes(self):
        """Charge les post-its depuis le fichier JSON"""
        if os.path.exists(self.notes_file):
            try:
                with open(self.notes_file, 'r', encoding='utf-8') as f:
                    notes_data = json.load(f)
                
                for data in notes_data:
                    if data.get('text'):  # Seulement charger les notes non vides
                        note = PostIt(
                            self,  # Passer self (PostItApp) au lieu de self.root
                            x=data.get('x', 100),
                            y=data.get('y', 100),
                            width=data.get('width', 200),
                            height=data.get('height', 150),
                            color=data.get('color', '#FFFF99'),
                            text=data.get('text', ''),
                            note_id=data.get('id')
                        )
                        self.notes[note.note_id] = note
                
                self.update_counter()
                
            except Exception as e:
                print(f"Erreur lors du chargement: {e}")
    
    def on_closing(self):
        """Gestion de la fermeture de l'application"""
        self.save_notes()
        
        # Fermer tous les post-its
        for note in self.notes.values():
            try:
                note.window.destroy()
            except:
                pass
        
        self.root.destroy()
    
    def run(self):
        """Lance l'application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = PostItApp()
    app.run()