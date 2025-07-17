import customtkinter as ctk
import sqlite3
import bcrypt
import json
import os
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import tkinter.messagebox as messagebox
from tkinter import ttk
import threading
import time

class PasswordManager:
    def __init__(self):
        # Configuration de l'apparence
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Variables d'état
        self.current_user = None
        self.current_role = None
        self.encryption_key = None
        self.db_connection = None
        
        # Initialisation de la base de données
        self.init_database()
        
        # Interface principale
        self.root = ctk.CTk()
        self.root.title("🔒 Gestionnaire de Mots de Passe Entreprise")
        self.root.geometry("1200x800")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Variables d'interface
        self.main_frame = None
        self.login_frame = None
        self.password_list = None
        self.search_var = ctk.StringVar()
        
        # Création de l'interface de connexion
        self.create_login_interface()
        
    def init_database(self):
        """Initialise la base de données SQLite"""
        self.db_connection = sqlite3.connect('password_manager.db', check_same_thread=False)
        cursor = self.db_connection.cursor()
        
        # Table des utilisateurs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                encryption_salt BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        
        # Table des mots de passe
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS passwords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                username TEXT,
                password_encrypted TEXT NOT NULL,
                url TEXT,
                notes TEXT,
                category TEXT DEFAULT 'General',
                created_by TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                visibility_level INTEGER DEFAULT 1
            )
        ''')
        
        # Table de l'historique
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS password_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                password_id INTEGER,
                action TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                changed_by TEXT NOT NULL,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (password_id) REFERENCES passwords (id)
            )
        ''')
        
        # Table des permissions d'accès
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS access_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                password_id INTEGER,
                permission_level INTEGER DEFAULT 1,
                granted_by TEXT NOT NULL,
                granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (password_id) REFERENCES passwords (id)
            )
        ''')
        
        self.db_connection.commit()
        
        # Créer l'utilisateur admin par défaut
        self.create_default_admin()
        
    def create_default_admin(self):
        """Crée l'utilisateur administrateur par défaut"""
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        
        if cursor.fetchone()[0] == 0:
            admin_password = "admin123"
            hashed_password = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())
            
            # Générer le salt pour le chiffrement
            _, salt = self.generate_encryption_key(admin_password)
            
            cursor.execute(
                "INSERT INTO users (username, password_hash, role, encryption_salt) VALUES (?, ?, ?, ?)",
                ("admin", hashed_password, "admin", salt)
            )
            self.db_connection.commit()
            
    def generate_encryption_key(self, password: str, salt: bytes = None) -> tuple:
        """Génère une clé de chiffrement à partir d'un mot de passe"""
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt
        
    def encrypt_password(self, password: str) -> str:
        """Chiffre un mot de passe"""
        if self.encryption_key is None:
            raise ValueError("Clé de chiffrement non initialisée")
        
        f = Fernet(self.encryption_key)
        encrypted_password = f.encrypt(password.encode())
        return base64.urlsafe_b64encode(encrypted_password).decode()
        
    def decrypt_password(self, encrypted_password: str) -> str:
        """Déchiffre un mot de passe"""
        if self.encryption_key is None:
            raise ValueError("Clé de chiffrement non initialisée")
        
        f = Fernet(self.encryption_key)
        encrypted_data = base64.urlsafe_b64decode(encrypted_password.encode())
        decrypted_password = f.decrypt(encrypted_data)
        return decrypted_password.decode()
        
    def create_login_interface(self):
        """Crée l'interface de connexion"""
        if self.main_frame:
            self.main_frame.destroy()
            
        self.login_frame = ctk.CTkFrame(self.root)
        self.login_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Titre
        title_label = ctk.CTkLabel(
            self.login_frame,
            text="🔒 Gestionnaire de Mots de Passe",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack(pady=30)
        
        # Frame de connexion
        login_container = ctk.CTkFrame(self.login_frame)
        login_container.pack(pady=20)
        
        # Nom d'utilisateur
        ctk.CTkLabel(login_container, text="Nom d'utilisateur:", font=ctk.CTkFont(size=14)).pack(pady=10)
        self.username_entry = ctk.CTkEntry(login_container, width=300, font=ctk.CTkFont(size=14))
        self.username_entry.pack(pady=5)
        
        # Mot de passe
        ctk.CTkLabel(login_container, text="Mot de passe:", font=ctk.CTkFont(size=14)).pack(pady=10)
        self.password_entry = ctk.CTkEntry(login_container, width=300, show="*", font=ctk.CTkFont(size=14))
        self.password_entry.pack(pady=5)
        
        # Boutons
        button_frame = ctk.CTkFrame(login_container)
        button_frame.pack(pady=20)
        
        login_button = ctk.CTkButton(
            button_frame,
            text="Se connecter",
            command=self.login,
            width=140,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        login_button.pack(side="left", padx=10)
        
        register_button = ctk.CTkButton(
            button_frame,
            text="Créer un compte",
            command=self.show_register_dialog,
            width=140,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        register_button.pack(side="left", padx=10)
        
        # Informations par défaut
        info_label = ctk.CTkLabel(
            self.login_frame,
            text="Compte admin par défaut: admin / admin123",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        info_label.pack(pady=10)
        
        # Binding pour Enter
        self.password_entry.bind('<Return>', lambda e: self.login())
        
    def show_register_dialog(self):
        """Affiche la boîte de dialogue d'inscription"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Créer un nouveau compte")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (dialog.winfo_screenheight() // 2) - (300 // 2)
        dialog.geometry(f"400x300+{x}+{y}")
        
        # Champs
        ctk.CTkLabel(dialog, text="Nom d'utilisateur:", font=ctk.CTkFont(size=14)).pack(pady=10)
        username_entry = ctk.CTkEntry(dialog, width=300)
        username_entry.pack(pady=5)
        
        ctk.CTkLabel(dialog, text="Mot de passe:", font=ctk.CTkFont(size=14)).pack(pady=10)
        password_entry = ctk.CTkEntry(dialog, width=300, show="*")
        password_entry.pack(pady=5)
        
        ctk.CTkLabel(dialog, text="Confirmer le mot de passe:", font=ctk.CTkFont(size=14)).pack(pady=10)
        confirm_password_entry = ctk.CTkEntry(dialog, width=300, show="*")
        confirm_password_entry.pack(pady=5)
        
        # Boutons
        button_frame = ctk.CTkFrame(dialog)
        button_frame.pack(pady=20)
        
        def register_user():
            username = username_entry.get().strip()
            password = password_entry.get()
            confirm_password = confirm_password_entry.get()
            
            if not username or not password:
                messagebox.showerror("Erreur", "Veuillez remplir tous les champs")
                return
                
            if password != confirm_password:
                messagebox.showerror("Erreur", "Les mots de passe ne correspondent pas")
                return
                
            cursor = self.db_connection.cursor()
            try:
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                
                # Générer le salt pour le chiffrement
                _, salt = self.generate_encryption_key(password)
                
                cursor.execute(
                    "INSERT INTO users (username, password_hash, role, encryption_salt) VALUES (?, ?, ?, ?)",
                    (username, hashed_password, "user", salt)
                )
                self.db_connection.commit()
                messagebox.showinfo("Succès", "Compte créé avec succès!")
                dialog.destroy()
            except sqlite3.IntegrityError:
                messagebox.showerror("Erreur", "Ce nom d'utilisateur existe déjà")
        
        ctk.CTkButton(button_frame, text="Créer", command=register_user, width=100).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Annuler", command=dialog.destroy, width=100).pack(side="left", padx=10)
        
    def login(self):
        """Gère la connexion utilisateur"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Erreur", "Veuillez remplir tous les champs")
            return
            
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT id, password_hash, role, encryption_salt FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user[1]):
            self.current_user = username
            self.current_role = user[2]
            
            # Générer la clé de chiffrement avec le salt stocké
            stored_salt = user[3]
            if stored_salt is None:
                # Première connexion ou migration - générer et stocker le salt
                self.encryption_key, new_salt = self.generate_encryption_key(password)
                cursor.execute("UPDATE users SET encryption_salt = ? WHERE username = ?", (new_salt, username))
                self.db_connection.commit()
            else:
                # Utiliser le salt stocké
                self.encryption_key, _ = self.generate_encryption_key(password, stored_salt)
            
            # Mettre à jour la dernière connexion
            cursor.execute("UPDATE users SET last_login = ? WHERE username = ?", (datetime.now(), username))
            self.db_connection.commit()
            
            # Créer l'interface principale
            self.create_main_interface()
        else:
            messagebox.showerror("Erreur", "Nom d'utilisateur ou mot de passe incorrect")
            
    def create_main_interface(self):
        """Crée l'interface principale"""
        if self.login_frame:
            self.login_frame.destroy()
            
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Barre supérieure
        top_frame = ctk.CTkFrame(self.main_frame)
        top_frame.pack(fill="x", padx=10, pady=10)
        
        # Informations utilisateur
        user_info = ctk.CTkLabel(
            top_frame,
            text=f"Connecté: {self.current_user} ({self.current_role})",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        user_info.pack(side="left", padx=10, pady=10)
        
        # Bouton de déconnexion
        logout_button = ctk.CTkButton(
            top_frame,
            text="Déconnexion",
            command=self.logout,
            width=100,
            height=30
        )
        logout_button.pack(side="right", padx=10, pady=10)
        
        # Barre d'outils
        toolbar_frame = ctk.CTkFrame(self.main_frame)
        toolbar_frame.pack(fill="x", padx=10, pady=5)
        
        # Recherche
        ctk.CTkLabel(toolbar_frame, text="Rechercher:", font=ctk.CTkFont(size=12)).pack(side="left", padx=5)
        search_entry = ctk.CTkEntry(toolbar_frame, textvariable=self.search_var, width=200)
        search_entry.pack(side="left", padx=5)
        search_entry.bind('<KeyRelease>', lambda e: self.filter_passwords())
        
        # Boutons d'action
        add_button = ctk.CTkButton(
            toolbar_frame,
            text="➕ Ajouter",
            command=self.show_add_password_dialog,
            width=100,
            height=30
        )
        add_button.pack(side="left", padx=10)
        
        refresh_button = ctk.CTkButton(
            toolbar_frame,
            text="🔄 Actualiser",
            command=self.refresh_password_list,
            width=100,
            height=30
        )
        refresh_button.pack(side="left", padx=5)
        
        # Bouton de vérification d'intégrité
        integrity_button = ctk.CTkButton(
            toolbar_frame,
            text="🔍 Vérifier",
            command=self.check_password_integrity,
            width=100,
            height=30
        )
        integrity_button.pack(side="left", padx=5)
        
        # Bouton de suppression
        delete_button = ctk.CTkButton(
            toolbar_frame,
            text="🗑️ Supprimer",
            command=self.delete_selected_password,
            width=100,
            height=30
        )
        delete_button.pack(side="left", padx=5)
        
        if self.current_role == "admin":
            admin_button = ctk.CTkButton(
                toolbar_frame,
                text="⚙️ Administration",
                command=self.show_admin_panel,
                width=120,
                height=30
            )
            admin_button.pack(side="right", padx=10)
        
        # Liste des mots de passe
        self.create_password_list()
        
    def create_password_list(self):
        """Crée la liste des mots de passe"""
        list_frame = ctk.CTkFrame(self.main_frame)
        list_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Treeview pour la liste
        columns = ("Titre", "Utilisateur", "URL", "Catégorie", "Créé par", "Modifié")
        
        self.password_list = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        # Configuration des colonnes
        self.password_list.heading("Titre", text="Titre")
        self.password_list.heading("Utilisateur", text="Utilisateur")
        self.password_list.heading("URL", text="URL")
        self.password_list.heading("Catégorie", text="Catégorie")
        self.password_list.heading("Créé par", text="Créé par")
        self.password_list.heading("Modifié", text="Dernière modification")
        
        self.password_list.column("Titre", width=200)
        self.password_list.column("Utilisateur", width=150)
        self.password_list.column("URL", width=200)
        self.password_list.column("Catégorie", width=100)
        self.password_list.column("Créé par", width=100)
        self.password_list.column("Modifié", width=150)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.password_list.yview)
        self.password_list.configure(yscrollcommand=scrollbar.set)
        
        # Placement
        self.password_list.pack(side="left", expand=True, fill="both")
        scrollbar.pack(side="right", fill="y")
        
        # Binding pour double-clic
        self.password_list.bind("<Double-1>", self.on_password_double_click)
        self.password_list.bind("<Button-3>", self.show_context_menu)
        
        # Charger les données
        self.refresh_password_list()
        
    def refresh_password_list(self):
        """Actualise la liste des mots de passe"""
        # Vider la liste
        for item in self.password_list.get_children():
            self.password_list.delete(item)
            
        # Récupérer les données
        cursor = self.db_connection.cursor()
        
        # Requête adaptée selon le rôle
        if self.current_role in ["admin", "manager"]:
            # Admins et managers voient tous les mots de passe
            query = """
                SELECT id, title, username, url, category, created_by, updated_at, visibility_level
                FROM passwords
                ORDER BY updated_at DESC
            """
            cursor.execute(query)
        else:
            # Utilisateurs normaux ne voient que les mots de passe qu'ils ont créés
            query = """
                SELECT id, title, username, url, category, created_by, updated_at, visibility_level
                FROM passwords
                WHERE created_by = ?
                ORDER BY updated_at DESC
            """
            cursor.execute(query, (self.current_user,))
            
        passwords = cursor.fetchall()
        
        for password in passwords:
            self.password_list.insert("", "end", values=(
                password[1],  # title
                password[2],  # username
                password[3],  # url
                password[4],  # category
                password[5],  # created_by
                password[6]   # updated_at
            ), tags=(password[0],))  # ID comme tag
            
    def filter_passwords(self):
        """Filtre les mots de passe selon la recherche"""
        search_term = self.search_var.get().lower()
        
        # Vider la liste
        for item in self.password_list.get_children():
            self.password_list.delete(item)
            
        # Récupérer les données filtrées
        cursor = self.db_connection.cursor()
        
        if self.current_role in ["admin", "manager"]:
            # Admins et managers voient tous les mots de passe
            query = """
                SELECT id, title, username, url, category, created_by, updated_at, visibility_level
                FROM passwords
                WHERE LOWER(title) LIKE ? OR LOWER(username) LIKE ? OR LOWER(url) LIKE ?
                ORDER BY updated_at DESC
            """
            cursor.execute(query, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
        else:
            # Utilisateurs normaux ne voient que les mots de passe qu'ils ont créés
            query = """
                SELECT id, title, username, url, category, created_by, updated_at, visibility_level
                FROM passwords
                WHERE created_by = ?
                AND (LOWER(title) LIKE ? OR LOWER(username) LIKE ? OR LOWER(url) LIKE ?)
                ORDER BY updated_at DESC
            """
            cursor.execute(query, (self.current_user, f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
            
        passwords = cursor.fetchall()
        
        for password in passwords:
            self.password_list.insert("", "end", values=(
                password[1],  # title
                password[2],  # username
                password[3],  # url
                password[4],  # category
                password[5],  # created_by
                password[6]   # updated_at
            ), tags=(password[0],))
            
    def show_context_menu(self, event):
        """Affiche le menu contextuel"""
        selection = self.password_list.selection()
        if not selection:
            return
            
        import tkinter as tk
        context_menu = tk.Menu(self.root, tearoff=0)
        context_menu.add_command(label="Voir/Modifier", command=self.on_password_double_click)
        context_menu.add_command(label="Copier le mot de passe", command=self.copy_password)
        context_menu.add_separator()
        context_menu.add_command(label="Historique", command=self.show_password_history)
        
        if self.current_role in ["admin", "manager"]:
            context_menu.add_command(label="Gérer les permissions", command=self.manage_permissions)
            context_menu.add_separator()
            context_menu.add_command(label="Supprimer", command=self.delete_password)
        elif self.current_role == "user":
            # Vérifier si l'utilisateur peut supprimer ce mot de passe (s'il en est le créateur)
            password_id = self.password_list.item(selection[0])['tags'][0]
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT created_by FROM passwords WHERE id = ?", (password_id,))
            creator = cursor.fetchone()
            if creator and creator[0] == self.current_user:
                context_menu.add_separator()
                context_menu.add_command(label="Supprimer", command=self.delete_password)
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
            
    def on_password_double_click(self, event=None):
        """Gère le double-clic sur un mot de passe"""
        selection = self.password_list.selection()
        if not selection:
            return
            
        password_id = self.password_list.item(selection[0])['tags'][0]
        self.show_password_details(password_id)
        
    def show_password_details(self, password_id):
        """Affiche les détails d'un mot de passe"""
        cursor = self.db_connection.cursor()
        cursor.execute("""
            SELECT title, username, password_encrypted, url, notes, category, visibility_level, created_by
            FROM passwords WHERE id = ?
        """, (password_id,))
        
        password_data = cursor.fetchone()
        if not password_data:
            messagebox.showerror("Erreur", "Mot de passe non trouvé")
            return
            
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Détails du mot de passe")
        dialog.geometry("500x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (600 // 2)
        dialog.geometry(f"500x600+{x}+{y}")
        
        # Vérifier les permissions
        can_edit = (self.current_role == "admin" or password_data[7] == self.current_user)
        
        # Champs
        ctk.CTkLabel(dialog, text="Titre:", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        title_entry = ctk.CTkEntry(dialog, width=400)
        title_entry.insert(0, password_data[0])
        title_entry.pack(pady=5)
        if not can_edit:
            title_entry.configure(state="disabled")
        
        ctk.CTkLabel(dialog, text="Nom d'utilisateur:", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        username_entry = ctk.CTkEntry(dialog, width=400)
        username_entry.insert(0, password_data[1] or "")
        username_entry.pack(pady=5)
        if not can_edit:
            username_entry.configure(state="disabled")
        
        ctk.CTkLabel(dialog, text="Mot de passe:", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        password_frame = ctk.CTkFrame(dialog)
        password_frame.pack(pady=5)
        
        password_entry = ctk.CTkEntry(password_frame, width=300, show="*")
        decryption_error = False
        try:
            decrypted_password = self.decrypt_password(password_data[2])
            password_entry.insert(0, decrypted_password)
        except Exception as e:
            decryption_error = True
            password_entry.insert(0, "⚠️ Erreur de déchiffrement")
            password_entry.configure(state="disabled")
        password_entry.pack(side="left", padx=5)
        if not can_edit:
            password_entry.configure(state="disabled")
        
        show_password_var = ctk.BooleanVar()
        def toggle_password():
            if show_password_var.get():
                password_entry.configure(show="")
            else:
                password_entry.configure(show="*")
        
        show_checkbox = ctk.CTkCheckBox(password_frame, text="Afficher", variable=show_password_var, command=toggle_password)
        if not decryption_error:
            show_checkbox.pack(side="left", padx=5)
        
        copy_button = ctk.CTkButton(password_frame, text="Copier", width=60, command=lambda: self.copy_to_clipboard(password_entry.get()))
        if not decryption_error:
            copy_button.pack(side="left", padx=5)
        
        # Afficher un message d'erreur si nécessaire
        if decryption_error:
            error_frame = ctk.CTkFrame(dialog)
            error_frame.pack(pady=10, padx=20, fill="x")
            
            error_label = ctk.CTkLabel(
                error_frame,
                text="⚠️ Erreur de déchiffrement détectée",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="orange"
            )
            error_label.pack(pady=5)
            
            info_label = ctk.CTkLabel(
                error_frame,
                text="Ce mot de passe a été créé avant la migration.\nReconnectez-vous pour générer votre clé de chiffrement.",
                font=ctk.CTkFont(size=10)
            )
            info_label.pack(pady=2)
            
            def recreate_password():
                # Permettre de recréer le mot de passe
                password_entry.configure(state="normal")
                password_entry.delete(0, "end")
                password_entry.insert(0, "")
                show_checkbox.pack(side="left", padx=5)
                copy_button.pack(side="left", padx=5)
                error_frame.destroy()
                messagebox.showinfo("Info", "Vous pouvez maintenant saisir un nouveau mot de passe")
            
            recreate_button = ctk.CTkButton(
                error_frame,
                text="Recréer le mot de passe",
                command=recreate_password,
                width=150,
                height=30
            )
            recreate_button.pack(pady=5)
        
        ctk.CTkLabel(dialog, text="URL:", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        url_entry = ctk.CTkEntry(dialog, width=400)
        url_entry.insert(0, password_data[3] or "")
        url_entry.pack(pady=5)
        if not can_edit:
            url_entry.configure(state="disabled")
        
        ctk.CTkLabel(dialog, text="Catégorie:", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        category_var = ctk.StringVar(value=password_data[5])
        category_combo = ctk.CTkComboBox(dialog, values=["General", "Email", "Social", "Work", "Banking", "Other"], variable=category_var, width=400)
        category_combo.pack(pady=5)
        if not can_edit:
            category_combo.configure(state="disabled")
        
        if self.current_role == "admin":
            ctk.CTkLabel(dialog, text="Niveau de visibilité:", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
            visibility_var = ctk.StringVar(value="Normal" if password_data[6] == 1 else "Restreint")
            visibility_combo = ctk.CTkComboBox(dialog, values=["Normal", "Restreint"], variable=visibility_var, width=400)
            visibility_combo.pack(pady=5)
        
        ctk.CTkLabel(dialog, text="Notes:", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        notes_text = ctk.CTkTextbox(dialog, width=400, height=100)
        notes_text.insert("1.0", password_data[4] or "")
        notes_text.pack(pady=5)
        if not can_edit:
            notes_text.configure(state="disabled")
        
        # Boutons
        button_frame = ctk.CTkFrame(dialog)
        button_frame.pack(pady=20)
        
        if can_edit:
            def save_changes():
                try:
                    # Vérifier si le mot de passe a changé
                    old_password = None
                    password_changed = False
                    
                    try:
                        old_password = self.decrypt_password(password_data[2])
                        new_password = password_entry.get()
                        password_changed = (old_password != new_password)
                    except:
                        # Erreur de déchiffrement - considérer comme changé
                        password_changed = True
                        new_password = password_entry.get()
                    
                    if not new_password:
                        messagebox.showerror("Erreur", "Le mot de passe ne peut pas être vide")
                        return
                    
                    encrypted_password = self.encrypt_password(new_password)
                    visibility_level = 1 if (self.current_role != "admin" or visibility_var.get() == "Normal") else 2
                    
                    cursor.execute("""
                        UPDATE passwords 
                        SET title=?, username=?, password_encrypted=?, url=?, notes=?, category=?, visibility_level=?, updated_at=?
                        WHERE id=?
                    """, (
                        title_entry.get(),
                        username_entry.get(),
                        encrypted_password,
                        url_entry.get(),
                        notes_text.get("1.0", "end-1c"),
                        category_var.get(),
                        visibility_level,
                        datetime.now(),
                        password_id
                    ))
                    
                    # Ajouter à l'historique
                    if password_changed:
                        cursor.execute("""
                            INSERT INTO password_history (password_id, action, old_value, new_value, changed_by)
                            VALUES (?, ?, ?, ?, ?)
                        """, (password_id, "PASSWORD_CHANGED", "***", "***", self.current_user))
                    
                    cursor.execute("""
                        INSERT INTO password_history (password_id, action, old_value, new_value, changed_by)
                        VALUES (?, ?, ?, ?, ?)
                    """, (password_id, "DETAILS_UPDATED", "", f"Title: {title_entry.get()}", self.current_user))
                    
                    self.db_connection.commit()
                    messagebox.showinfo("Succès", "Mot de passe mis à jour avec succès!")
                    dialog.destroy()
                    self.refresh_password_list()
                except Exception as e:
                    messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde: {str(e)}")
            
            save_button = ctk.CTkButton(button_frame, text="Sauvegarder", command=save_changes, width=100)
            save_button.pack(side="left", padx=10)
        
        close_button = ctk.CTkButton(button_frame, text="Fermer", command=dialog.destroy, width=100)
        close_button.pack(side="left", padx=10)
        
    def copy_to_clipboard(self, text):
        """Copie le texte dans le presse-papiers"""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("Succès", "Copié dans le presse-papiers!")
        
    def copy_password(self):
        """Copie le mot de passe sélectionné"""
        selection = self.password_list.selection()
        if not selection:
            return
            
        password_id = self.password_list.item(selection[0])['tags'][0]
        
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT password_encrypted FROM passwords WHERE id = ?", (password_id,))
        result = cursor.fetchone()
        
        if result:
            try:
                decrypted_password = self.decrypt_password(result[0])
                self.copy_to_clipboard(decrypted_password)
            except Exception as e:
                messagebox.showerror(
                    "Erreur de déchiffrement", 
                    "Impossible de déchiffrer ce mot de passe.\n\n"
                    "Cause possible: mot de passe créé avant la migration.\n"
                    "Solution: reconnectez-vous pour générer votre clé de chiffrement."
                )
                
    def show_add_password_dialog(self):
        """Affiche la boîte de dialogue d'ajout de mot de passe"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Ajouter un nouveau mot de passe")
        dialog.geometry("500x550")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (550 // 2)
        dialog.geometry(f"500x550+{x}+{y}")
        
        # Champs
        ctk.CTkLabel(dialog, text="Titre:", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        title_entry = ctk.CTkEntry(dialog, width=400)
        title_entry.pack(pady=5)
        
        ctk.CTkLabel(dialog, text="Nom d'utilisateur:", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        username_entry = ctk.CTkEntry(dialog, width=400)
        username_entry.pack(pady=5)
        
        ctk.CTkLabel(dialog, text="Mot de passe:", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        password_frame = ctk.CTkFrame(dialog)
        password_frame.pack(pady=5)
        
        password_entry = ctk.CTkEntry(password_frame, width=300, show="*")
        password_entry.pack(side="left", padx=5)
        
        def generate_password():
            import random
            import string
            chars = string.ascii_letters + string.digits + "!@#$%^&*"
            password = ''.join(random.choice(chars) for _ in range(12))
            password_entry.delete(0, "end")
            password_entry.insert(0, password)
        
        generate_button = ctk.CTkButton(password_frame, text="Générer", width=80, command=generate_password)
        generate_button.pack(side="left", padx=5)
        
        show_password_var = ctk.BooleanVar()
        def toggle_password():
            if show_password_var.get():
                password_entry.configure(show="")
            else:
                password_entry.configure(show="*")
        
        show_checkbox = ctk.CTkCheckBox(password_frame, text="Afficher", variable=show_password_var, command=toggle_password)
        show_checkbox.pack(side="left", padx=5)
        
        ctk.CTkLabel(dialog, text="URL:", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        url_entry = ctk.CTkEntry(dialog, width=400)
        url_entry.pack(pady=5)
        
        ctk.CTkLabel(dialog, text="Catégorie:", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        category_var = ctk.StringVar(value="General")
        category_combo = ctk.CTkComboBox(dialog, values=["General", "Email", "Social", "Work", "Banking", "Other"], variable=category_var, width=400)
        category_combo.pack(pady=5)
        
        if self.current_role == "admin":
            ctk.CTkLabel(dialog, text="Niveau de visibilité:", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
            visibility_var = ctk.StringVar(value="Normal")
            visibility_combo = ctk.CTkComboBox(dialog, values=["Normal", "Restreint"], variable=visibility_var, width=400)
            visibility_combo.pack(pady=5)
        
        ctk.CTkLabel(dialog, text="Notes:", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)
        notes_text = ctk.CTkTextbox(dialog, width=400, height=100)
        notes_text.pack(pady=5)
        
        # Boutons
        button_frame = ctk.CTkFrame(dialog)
        button_frame.pack(pady=20)
        
        def save_password():
            if not title_entry.get().strip() or not password_entry.get():
                messagebox.showerror("Erreur", "Le titre et le mot de passe sont obligatoires")
                return
            
            try:
                encrypted_password = self.encrypt_password(password_entry.get())
                visibility_level = 1 if (self.current_role != "admin" or visibility_var.get() == "Normal") else 2
                
                cursor = self.db_connection.cursor()
                cursor.execute("""
                    INSERT INTO passwords (title, username, password_encrypted, url, notes, category, visibility_level, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    title_entry.get(),
                    username_entry.get(),
                    encrypted_password,
                    url_entry.get(),
                    notes_text.get("1.0", "end-1c"),
                    category_var.get(),
                    visibility_level,
                    self.current_user
                ))
                
                password_id = cursor.lastrowid
                
                # Ajouter à l'historique
                cursor.execute("""
                    INSERT INTO password_history (password_id, action, old_value, new_value, changed_by)
                    VALUES (?, ?, ?, ?, ?)
                """, (password_id, "CREATED", "", f"Title: {title_entry.get()}", self.current_user))
                
                self.db_connection.commit()
                messagebox.showinfo("Succès", "Mot de passe ajouté avec succès!")
                dialog.destroy()
                self.refresh_password_list()
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'ajout: {str(e)}")
        
        save_button = ctk.CTkButton(button_frame, text="Sauvegarder", command=save_password, width=100)
        save_button.pack(side="left", padx=10)
        
        cancel_button = ctk.CTkButton(button_frame, text="Annuler", command=dialog.destroy, width=100)
        cancel_button.pack(side="left", padx=10)
        
    def show_password_history(self):
        """Affiche l'historique des modifications d'un mot de passe"""
        selection = self.password_list.selection()
        if not selection:
            return
            
        password_id = self.password_list.item(selection[0])['tags'][0]
        
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Historique des modifications")
        dialog.geometry("800x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (800 // 2)
        y = (dialog.winfo_screenheight() // 2) - (500 // 2)
        dialog.geometry(f"800x500+{x}+{y}")
        
        # Treeview pour l'historique
        columns = ("Date", "Action", "Utilisateur", "Détails")
        history_tree = ttk.Treeview(dialog, columns=columns, show="headings", height=15)
        
        history_tree.heading("Date", text="Date")
        history_tree.heading("Action", text="Action")
        history_tree.heading("Utilisateur", text="Utilisateur")
        history_tree.heading("Détails", text="Détails")
        
        history_tree.column("Date", width=150)
        history_tree.column("Action", width=150)
        history_tree.column("Utilisateur", width=100)
        history_tree.column("Détails", width=400)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=history_tree.yview)
        history_tree.configure(yscrollcommand=scrollbar.set)
        
        # Placement
        history_tree.pack(side="left", expand=True, fill="both", padx=10, pady=10)
        scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=10)
        
        # Charger l'historique
        cursor = self.db_connection.cursor()
        cursor.execute("""
            SELECT changed_at, action, changed_by, new_value
            FROM password_history
            WHERE password_id = ?
            ORDER BY changed_at DESC
        """, (password_id,))
        
        history = cursor.fetchall()
        
        for record in history:
            history_tree.insert("", "end", values=record)
        
        # Bouton fermer
        close_button = ctk.CTkButton(dialog, text="Fermer", command=dialog.destroy, width=100)
        close_button.pack(pady=10)
        
    def manage_permissions(self):
        """Gère les permissions d'accès"""
        selection = self.password_list.selection()
        if not selection:
            return
            
        password_id = self.password_list.item(selection[0])['tags'][0]
        
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Gestion des permissions")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (dialog.winfo_screenheight() // 2) - (400 // 2)
        dialog.geometry(f"600x400+{x}+{y}")
        
        # Interface de gestion des permissions
        ctk.CTkLabel(dialog, text="Gérer les permissions d'accès", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Liste des utilisateurs avec permissions
        permission_frame = ctk.CTkFrame(dialog)
        permission_frame.pack(expand=True, fill="both", padx=20, pady=10)
        
        # Ajouter une nouvelle permission
        add_frame = ctk.CTkFrame(permission_frame)
        add_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(add_frame, text="Ajouter un utilisateur:").pack(side="left", padx=5)
        
        # Récupérer la liste des utilisateurs
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT username FROM users WHERE username != ?", (self.current_user,))
        users = [row[0] for row in cursor.fetchall()]
        
        user_var = ctk.StringVar()
        user_combo = ctk.CTkComboBox(add_frame, values=users, variable=user_var, width=200)
        user_combo.pack(side="left", padx=5)
        
        def add_permission():
            if not user_var.get():
                messagebox.showerror("Erreur", "Veuillez sélectionner un utilisateur")
                return
            
            cursor.execute("SELECT id FROM users WHERE username = ?", (user_var.get(),))
            user_id = cursor.fetchone()[0]
            
            cursor.execute("""
                INSERT OR REPLACE INTO access_permissions (user_id, password_id, permission_level, granted_by)
                VALUES (?, ?, ?, ?)
            """, (user_id, password_id, 1, self.current_user))
            
            self.db_connection.commit()
            messagebox.showinfo("Succès", "Permission ajoutée avec succès!")
            dialog.destroy()
        
        add_button = ctk.CTkButton(add_frame, text="Ajouter", command=add_permission, width=100)
        add_button.pack(side="left", padx=5)
        
        # Bouton fermer
        close_button = ctk.CTkButton(dialog, text="Fermer", command=dialog.destroy, width=100)
        close_button.pack(pady=10)
        
    def delete_password(self):
        """Supprime un mot de passe"""
        selection = self.password_list.selection()
        if not selection:
            return
            
        password_id = self.password_list.item(selection[0])['tags'][0]
        password_title = self.password_list.item(selection[0])['values'][0]
        
        # Vérifier les permissions
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT created_by FROM passwords WHERE id = ?", (password_id,))
        creator = cursor.fetchone()
        
        if not creator:
            messagebox.showerror("Erreur", "Mot de passe non trouvé")
            return
        
        # Seuls les admins, managers ou le créateur peuvent supprimer
        if self.current_role not in ["admin", "manager"] and creator[0] != self.current_user:
            messagebox.showerror("Erreur", "Vous n'avez pas la permission de supprimer ce mot de passe")
            return
        
        if messagebox.askyesno("Confirmation", f"Êtes-vous sûr de vouloir supprimer '{password_title}' ?"):
            # Ajouter à l'historique avant suppression
            cursor.execute("""
                INSERT INTO password_history (password_id, action, old_value, new_value, changed_by)
                VALUES (?, ?, ?, ?, ?)
            """, (password_id, "DELETED", password_title, "", self.current_user))
            
            # Supprimer les permissions
            cursor.execute("DELETE FROM access_permissions WHERE password_id = ?", (password_id,))
            
            # Supprimer l'historique (après avoir ajouté l'entrée de suppression)
            cursor.execute("DELETE FROM password_history WHERE password_id = ?", (password_id,))
            
            # Supprimer le mot de passe
            cursor.execute("DELETE FROM passwords WHERE id = ?", (password_id,))
            
            self.db_connection.commit()
            messagebox.showinfo("Succès", "Mot de passe supprimé avec succès!")
            self.refresh_password_list()
            
    def delete_selected_password(self):
        """Supprime le mot de passe sélectionné (appelée par le bouton de suppression)"""
        selection = self.password_list.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner un mot de passe à supprimer")
            return
        
        # Réutiliser la fonction de suppression existante
        self.delete_password()
            
    def show_admin_panel(self):
        """Affiche le panneau d'administration"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Panneau d'Administration")
        dialog.geometry("800x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (800 // 2)
        y = (dialog.winfo_screenheight() // 2) - (600 // 2)
        dialog.geometry(f"800x600+{x}+{y}")
        
        # Notebook pour les onglets
        notebook = ctk.CTkTabview(dialog)
        notebook.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Onglet Utilisateurs
        users_tab = notebook.add("Utilisateurs")
        
        # Liste des utilisateurs
        users_frame = ctk.CTkFrame(users_tab)
        users_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        columns = ("Nom d'utilisateur", "Rôle", "Dernière connexion", "Créé le")
        users_tree = ttk.Treeview(users_frame, columns=columns, show="headings", height=10)
        
        for col in columns:
            users_tree.heading(col, text=col)
            users_tree.column(col, width=180)
        
        users_scrollbar = ttk.Scrollbar(users_frame, orient="vertical", command=users_tree.yview)
        users_tree.configure(yscrollcommand=users_scrollbar.set)
        
        users_tree.pack(side="left", expand=True, fill="both")
        users_scrollbar.pack(side="right", fill="y")
        
        # Charger les utilisateurs
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT username, role, last_login, created_at FROM users ORDER BY created_at DESC")
        users = cursor.fetchall()
        
        for user in users:
            users_tree.insert("", "end", values=user)
        
        # Boutons de gestion des utilisateurs
        user_buttons_frame = ctk.CTkFrame(users_tab)
        user_buttons_frame.pack(fill="x", padx=10, pady=10)
        
        def change_user_role():
            selection = users_tree.selection()
            if not selection:
                messagebox.showwarning("Attention", "Veuillez sélectionner un utilisateur")
                return
            
            selected_user = users_tree.item(selection[0])['values'][0]
            current_role = users_tree.item(selection[0])['values'][1]
            
            if selected_user == self.current_user:
                messagebox.showwarning("Attention", "Vous ne pouvez pas changer votre propre rôle")
                return
            
            self.show_change_role_dialog(selected_user, current_role, users_tree)
        
        def delete_user():
            selection = users_tree.selection()
            if not selection:
                messagebox.showwarning("Attention", "Veuillez sélectionner un utilisateur")
                return
            
            selected_user = users_tree.item(selection[0])['values'][0]
            
            if selected_user == self.current_user:
                messagebox.showwarning("Attention", "Vous ne pouvez pas supprimer votre propre compte")
                return
            
            if messagebox.askyesno("Confirmation", f"Êtes-vous sûr de vouloir supprimer l'utilisateur '{selected_user}' ?"):
                cursor.execute("DELETE FROM users WHERE username = ?", (selected_user,))
                self.db_connection.commit()
                messagebox.showinfo("Succès", "Utilisateur supprimé avec succès!")
                users_tree.delete(selection[0])
        
        ctk.CTkButton(user_buttons_frame, text="Changer le rôle", command=change_user_role, width=150).pack(side="left", padx=5)
        ctk.CTkButton(user_buttons_frame, text="Supprimer utilisateur", command=delete_user, width=150).pack(side="left", padx=5)
        
        # Onglet Statistiques
        stats_tab = notebook.add("Statistiques")
        
        stats_frame = ctk.CTkFrame(stats_tab)
        stats_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Calculer les statistiques
        cursor.execute("SELECT COUNT(*) FROM passwords")
        total_passwords = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM password_history WHERE changed_at > date('now', '-30 days')")
        recent_changes = cursor.fetchone()[0]
        
        # Afficher les statistiques
        ctk.CTkLabel(stats_frame, text="Statistiques du système", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)
        
        stats_info = ctk.CTkFrame(stats_frame)
        stats_info.pack(pady=20)
        
        ctk.CTkLabel(stats_info, text=f"Nombre total de mots de passe: {total_passwords}", font=ctk.CTkFont(size=16)).pack(pady=10)
        ctk.CTkLabel(stats_info, text=f"Nombre total d'utilisateurs: {total_users}", font=ctk.CTkFont(size=16)).pack(pady=10)
        ctk.CTkLabel(stats_info, text=f"Modifications récentes (30 jours): {recent_changes}", font=ctk.CTkFont(size=16)).pack(pady=10)
        
        # Bouton fermer
        close_button = ctk.CTkButton(dialog, text="Fermer", command=dialog.destroy, width=100)
        close_button.pack(pady=10)
        
    def show_change_role_dialog(self, username, current_role, users_tree):
        """Affiche la boîte de dialogue pour changer le rôle d'un utilisateur"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(f"Changer le rôle de {username}")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (dialog.winfo_screenheight() // 2) - (300 // 2)
        dialog.geometry(f"400x300+{x}+{y}")
        
        # Titre
        ctk.CTkLabel(
            dialog, 
            text=f"Modifier le rôle de {username}",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=20)
        
        # Rôle actuel
        ctk.CTkLabel(
            dialog, 
            text=f"Rôle actuel : {current_role}",
            font=ctk.CTkFont(size=14)
        ).pack(pady=10)
        
        # Nouveau rôle
        ctk.CTkLabel(dialog, text="Nouveau rôle :", font=ctk.CTkFont(size=14)).pack(pady=10)
        
        role_var = ctk.StringVar(value=current_role)
        role_combo = ctk.CTkComboBox(
            dialog, 
            values=["admin", "manager", "user"], 
            variable=role_var, 
            width=200
        )
        role_combo.pack(pady=10)
        
        # Description des rôles
        description_frame = ctk.CTkFrame(dialog)
        description_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        descriptions = {
            "admin": "• Accès complet\n• Gestion des utilisateurs\n• Suppression des mots de passe\n• Accès à tous les mots de passe",
            "manager": "• Gestion des permissions\n• Accès à tous les mots de passe\n• Pas de gestion d'utilisateurs\n• Pas de suppression",
            "user": "• Accès aux mots de passe partagés\n• Création de mots de passe personnels\n• Modification de ses propres mots de passe"
        }
        
        def update_description():
            selected_role = role_var.get()
            description_text.configure(state="normal")
            description_text.delete("1.0", "end")
            description_text.insert("1.0", descriptions.get(selected_role, ""))
            description_text.configure(state="disabled")
        
        description_text = ctk.CTkTextbox(description_frame, height=80)
        description_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Mettre à jour la description initiale
        update_description()
        
        # Lier le changement de rôle à la mise à jour de la description
        role_combo.configure(command=lambda choice: update_description())
        
        # Boutons
        button_frame = ctk.CTkFrame(dialog)
        button_frame.pack(pady=20)
        
        def save_role():
            new_role = role_var.get()
            if new_role == current_role:
                messagebox.showinfo("Information", "Aucun changement effectué")
                dialog.destroy()
                return
            
            cursor = self.db_connection.cursor()
            cursor.execute("UPDATE users SET role = ? WHERE username = ?", (new_role, username))
            self.db_connection.commit()
            
            messagebox.showinfo("Succès", f"Rôle de {username} changé en {new_role}")
            
            # Mettre à jour la liste des utilisateurs
            for item in users_tree.get_children():
                if users_tree.item(item)['values'][0] == username:
                    current_values = list(users_tree.item(item)['values'])
                    current_values[1] = new_role
                    users_tree.item(item, values=current_values)
                    break
            
            dialog.destroy()
        
        ctk.CTkButton(button_frame, text="Sauvegarder", command=save_role, width=100).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Annuler", command=dialog.destroy, width=100).pack(side="left", padx=10)
        
    def check_password_integrity(self):
        """Vérifie l'intégrité des mots de passe"""
        if self.encryption_key is None:
            messagebox.showerror("Erreur", "Clé de chiffrement non disponible")
            return
            
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT id, title, password_encrypted, created_by FROM passwords")
        all_passwords = cursor.fetchall()
        
        problematic_passwords = []
        
        for password in all_passwords:
            try:
                self.decrypt_password(password[2])
            except:
                problematic_passwords.append({
                    'id': password[0],
                    'title': password[1],
                    'created_by': password[3]
                })
        
        if problematic_passwords:
            dialog = ctk.CTkToplevel(self.root)
            dialog.title("Mots de passe problématiques")
            dialog.geometry("600x400")
            dialog.transient(self.root)
            dialog.grab_set()
            
            # Centrer la fenêtre
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
            y = (dialog.winfo_screenheight() // 2) - (400 // 2)
            dialog.geometry(f"600x400+{x}+{y}")
            
            ctk.CTkLabel(
                dialog,
                text=f"⚠️ {len(problematic_passwords)} mot(s) de passe problématique(s) détecté(s)",
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color="orange"
            ).pack(pady=20)
            
            info_text = ctk.CTkTextbox(dialog, width=550, height=200)
            info_text.pack(pady=10, padx=20)
            
            info_content = "Mots de passe avec erreurs de déchiffrement:\n\n"
            for pwd in problematic_passwords:
                info_content += f"• {pwd['title']} (ID: {pwd['id']}, créé par: {pwd['created_by']})\n"
            
            info_content += "\n\nSolutions possibles:\n"
            info_content += "1. Demandez aux utilisateurs de se reconnecter\n"
            info_content += "2. Recréez ces mots de passe\n"
            info_content += "3. Supprimez-les si ils ne sont plus nécessaires"
            
            info_text.insert("1.0", info_content)
            info_text.configure(state="disabled")
            
            ctk.CTkButton(dialog, text="Fermer", command=dialog.destroy).pack(pady=10)
        else:
            messagebox.showinfo("Succès", "Tous les mots de passe sont valides!")
            
    def logout(self):
        """Déconnecte l'utilisateur"""
        self.current_user = None
        self.current_role = None
        self.encryption_key = None
        self.create_login_interface()
        
    def on_closing(self):
        """Gère la fermeture de l'application"""
        if self.db_connection:
            self.db_connection.close()
        self.root.destroy()
        
    def run(self):
        """Lance l'application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = PasswordManager()
    app.run()
