import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog, ttk, colorchooser
import sys
import os
import datetime
import math
import json
import shutil
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
import markdown2

class TreeNode:
    def __init__(self, text="Node", x=0, y=0, parent=None):
        self.text = text
        self.x = x
        self.y = y
        self.parent = parent
        self.children = []
        self.width = 80
        self.height = 40
        self.color = "#E3F2FD"
        self.text_color = "#000000"
        self.border_color = "#2196F3"
        self.selected = False
        self.canvas_id = None
        self.text_id = None
        
    def add_child(self, child):
        child.parent = self
        self.children.append(child)
        
    def remove_child(self, child):
        if child in self.children:
            child.parent = None
            self.children.remove(child)
            
    def get_depth(self):
        if self.parent is None:
            return 0
        return self.parent.get_depth() + 1
        
    def get_all_descendants(self):
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        return descendants

class Task:
    def __init__(self, title="Nouvelle tâche", description="", status="À faire", priority="Moyenne", assignee="", due_date="", linked_node=None):
        self.id = id(self)  # ID unique basé sur l'adresse mémoire
        self.title = title
        self.description = description
        self.status = status  # "À faire", "En cours", "Terminé"
        self.priority = priority  # "Basse", "Moyenne", "Critique"
        self.assignee = assignee
        self.due_date = due_date
        self.linked_node = linked_node  # Lien vers un noeud de l'arbre
        self.created_date = datetime.datetime.now().strftime('%d/%m/%Y')
        
    def to_dict(self):
        """Convertir la tâche en dictionnaire pour la sauvegarde"""
        return {
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'assignee': self.assignee,
            'due_date': self.due_date,
            'linked_node_text': self.linked_node.text if self.linked_node else None,
            'created_date': self.created_date.isoformat() if hasattr(self, 'created_date') and isinstance(self.created_date, datetime.datetime) else datetime.datetime.now().isoformat()
        }
    
    @classmethod
    def from_dict(cls, data, tree_nodes=None):
        """Créer une tâche depuis un dictionnaire"""
        task = cls(
            title=data.get('title', ''),
            description=data.get('description', ''),
            status=data.get('status', 'À faire'),
            priority=data.get('priority', 'Moyenne'),
            assignee=data.get('assignee', ''),
            due_date=data.get('due_date', '')
        )
        
        # Restaurer le lien avec le nœud
        linked_node_text = data.get('linked_node_text')
        if linked_node_text and tree_nodes:
            for node in tree_nodes:
                if node.text == linked_node_text:
                    task.linked_node = node
                    break
        
        # Restaurer la date de création
        if 'created_date' in data:
            try:
                task.created_date = datetime.datetime.fromisoformat(data['created_date'])
            except:
                task.created_date = datetime.datetime.now()
        
        return task
    

class LogEntry:
    def __init__(self, entry_type="manual", title="", description="", author="", category="Decision"):
        self.id = id(self)
        self.timestamp = datetime.datetime.now()
        self.entry_type = entry_type  # "auto" (automatique) ou "manual"
        self.title = title
        self.description = description
        self.author = author
        self.category = category  # "Decision", "Technical", "Meeting", "Node", "Task", "Status"
        
    def to_dict(self):
        """Convertir l'entrée en dictionnaire pour la sauvegarde"""
        timestamp_iso = self.timestamp.isoformat() if isinstance(self.timestamp, datetime.datetime) else datetime.datetime.now().isoformat()
        
        return {
            'entry_type': self.entry_type,
            'title': self.title,
            'description': self.description,
            'author': self.author,
            'category': self.category,
            'timestamp': timestamp_iso
        }
    
    @classmethod
    def from_dict(cls, data):
        """Créer une entrée depuis un dictionnaire"""
        entry = cls(
            entry_type=data.get('entry_type', 'manual'),
            title=data.get('title', ''),
            description=data.get('description', ''),
            author=data.get('author', ''),
            category=data.get('category', 'Other')
        )
        
        # Restaurer le timestamp
        if 'timestamp' in data:
            try:
                entry.timestamp = datetime.datetime.fromisoformat(data['timestamp'])
            except:
                entry.timestamp = datetime.datetime.now()
        
        return entry

class Document:
    def __init__(self, filename="", file_path="", category="General", version="1.0", linked_node=None, description=""):
        self.id = id(self)
        self.filename = filename
        self.file_path = file_path
        self.stored_path = ""
        self.category = category
        self.version = version
        self.linked_node = linked_node
        self.description = description
        self.tags = []
        self.upload_date = datetime.datetime.now()
        self.file_size = os.path.getsize(file_path) if file_path and os.path.exists(file_path) else 0
        self.file_type = os.path.splitext(filename)[1].lower() if filename else ""
        
    def format_file_size(self):
        """Formater la taille du fichier de manière lisible"""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        elif self.file_size < 1024 * 1024 * 1024:
            return f"{self.file_size / (1024 * 1024):.1f} MB"
        else:
            return f"{self.file_size / (1024 * 1024 * 1024):.1f} GB"
            
    def get_file_type_icon(self):
        """Obtenir l'icône selon le type de fichier"""
        icons = {
            ".pdf": "📄", ".doc": "📝", ".docx": "📝", ".txt": "📝", ".md": "📝",
            ".xls": "📊", ".xlsx": "📊", ".csv": "📊",
            ".ppt": "📽️", ".pptx": "📽️",
            ".jpg": "🖼️", ".jpeg": "🖼️", ".png": "🖼️", ".gif": "🖼️", ".bmp": "🖼️",
            ".zip": "📦", ".rar": "📦", ".7z": "📦",
            ".py": "🐍", ".js": "📜", ".html": "🌐", ".css": "🎨", ".json": "📋"
        }
        return icons.get(self.file_type, "📄")
        
    def get_category_icon(self):
        """Obtenir l'icône selon la catégorie"""
        icons = {
            "Spécifications": "📋", "Tests": "🧪", "Livrables": "📦",
            "Documentation": "📚", "Images": "🖼️", "Code": "💻",
            "Rapports": "📊", "General": "📄"
        }
        return icons.get(self.category, "📄")
    def to_dict(self):
        """Convertir le document en dictionnaire pour la sauvegarde"""
        upload_date_iso = self.upload_date.isoformat() if isinstance(self.upload_date, datetime.datetime) else datetime.datetime.now().isoformat()
        
        return {
            'id': getattr(self, 'id', id(self)),
            'filename': self.filename,
            'file_path': getattr(self, 'file_path', ''),
            'stored_path': getattr(self, 'stored_path', ''),
            'category': self.category,
            'version': self.version,
            'description': getattr(self, 'description', ''),
            'tags': getattr(self, 'tags', []),
            'upload_date': upload_date_iso,
            'file_size': getattr(self, 'file_size', 0),
            'file_type': getattr(self, 'file_type', ''),
            'linked_node_text': self.linked_node.text if getattr(self, 'linked_node', None) else None
        }
    
    @classmethod
    def from_dict(cls, data, tree_nodes=None):
        """Créer un document depuis un dictionnaire"""
        doc = cls(
            filename=data.get('filename', ''),
            file_path=data.get('file_path', ''),
            category=data.get('category', 'General'),
            version=data.get('version', '1.0')
        )
        
        # Restaurer les attributs
        doc.id = data.get('id', id(doc))
        doc.stored_path = data.get('stored_path', '')
        doc.description = data.get('description', '')
        doc.tags = data.get('tags', [])
        doc.file_size = data.get('file_size', 0)
        doc.file_type = data.get('file_type', '')
        
        # Restaurer la date
        if 'upload_date' in data:
            try:
                doc.upload_date = datetime.datetime.fromisoformat(data['upload_date'])
            except:
                doc.upload_date = datetime.datetime.now()
        
        # Restaurer le lien avec le nœud
        linked_node_text = data.get('linked_node_text')
        if linked_node_text and tree_nodes:
            for node in tree_nodes:
                if node.text == linked_node_text:
                    doc.linked_node = node
                    break
        
        return doc

class ProjectBlock:
    """Classe pour représenter un bloc de projet réutilisable"""
    def __init__(self, name="Nouveau Bloc", description="", category="General", domain="", client=""):
        self.id = id(self)
        self.name = name
        self.description = description
        self.category = category  # "Process", "Testing", "CI/CD", "Hardware", "Software", etc.
        self.domain = domain  # "Embedded", "Web", "Mobile", "IoT", etc.
        self.client = client  # Pour les blocs spécifiques client
        self.created_date = datetime.datetime.now()
        self.last_used = None
        self.usage_count = 0
        self.success_rate = 0.0  # Pourcentage de succès dans les projets
        self.average_duration = 0  # Durée moyenne en jours
        self.tags = []
        
        # Contenu du bloc
        self.nodes = []  # Liste des nœuds (sérialisés)
        self.tasks = []  # Liste des tâches templates
        self.documents = []  # Documents templates/exemples
        self.resources = []  # Templates de ressources
        self.notes = ""  # Notes d'utilisation
        
        # Historique d'utilisation
        self.usage_history = []  # Liste des utilisations avec résultats
        
    def to_dict(self):
        """Convertir le bloc en dictionnaire pour la sauvegarde"""
        # Gérer last_used
        last_used_iso = None
        if hasattr(self, 'last_used') and self.last_used:
            if isinstance(self.last_used, datetime.datetime):
                last_used_iso = self.last_used.isoformat()
            elif isinstance(self.last_used, str):
                last_used_iso = self.last_used
        
        # Gérer created_date
        created_date_iso = datetime.datetime.now().isoformat()
        if hasattr(self, 'created_date'):
            if isinstance(self.created_date, datetime.datetime):
                created_date_iso = self.created_date.isoformat()
            elif isinstance(self.created_date, str):
                created_date_iso = self.created_date
        
        return {
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'domain': getattr(self, 'domain', ''),
            'client': getattr(self, 'client', ''),
            'tags': getattr(self, 'tags', []),
            'nodes': getattr(self, 'nodes', []),
            'tasks': getattr(self, 'tasks', []),
            'usage_count': getattr(self, 'usage_count', 0),
            'success_rate': getattr(self, 'success_rate', 0.0),
            'average_duration': getattr(self, 'average_duration', 0.0),
            'last_used': last_used_iso,
            'created_date': created_date_iso,
            'notes': getattr(self, 'notes', ''),
            'usage_history': getattr(self, 'usage_history', [])
        }
    
    @classmethod
    def from_dict(cls, data):
        """Créer un bloc depuis un dictionnaire"""
        block = cls(
            name=data.get('name', ''),
            description=data.get('description', ''),
            category=data.get('category', 'General'),
            domain=data.get('domain', ''),
            client=data.get('client', '')
        )
        
        # Restaurer les attributs
        block.tags = data.get('tags', [])
        block.nodes = data.get('nodes', [])
        block.tasks = data.get('tasks', [])
        block.usage_count = data.get('usage_count', 0)
        block.success_rate = data.get('success_rate', 0.0)
        block.average_duration = data.get('average_duration', 0.0)
        block.notes = data.get('notes', '')
        block.usage_history = data.get('usage_history', [])
        
        # Restaurer les dates
        if 'last_used' in data and data['last_used']:
            try:
                block.last_used = datetime.datetime.fromisoformat(data['last_used'])
            except:
                block.last_used = None
        
        if 'created_date' in data:
            try:
                block.created_date = datetime.datetime.fromisoformat(data['created_date'])
            except:
                block.created_date = datetime.datetime.now()
        
        return block
        
    def add_usage_record(self, project_name, duration_days, success=True, notes=""):
        """Ajouter un enregistrement d'utilisation"""
        record = {
            'project_name': project_name,
            'date': datetime.datetime.now().isoformat(),
            'duration_days': duration_days,
            'success': success,
            'notes': notes
        }
        self.usage_history.append(record)
        self.usage_count += 1
        self.last_used = datetime.datetime.now()
        
        # Recalculer les statistiques
        self.calculate_statistics()
        
    def calculate_statistics(self):
        """Recalculer les statistiques basées sur l'historique"""
        if not self.usage_history:
            return
            
        # Taux de succès
        successful_uses = sum(1 for record in self.usage_history if record.get('success', True))
        self.success_rate = (successful_uses / len(self.usage_history)) * 100
        
        # Durée moyenne
        durations = [record.get('duration_days', 0) for record in self.usage_history if record.get('duration_days', 0) > 0]
        if durations:
            self.average_duration = sum(durations) / len(durations)
            
    def get_category_icon(self):
        """Obtenir l'icône selon la catégorie"""
        icons = {
            "Process": "⚙️", "Testing": "🧪", "CI/CD": "🔄", "Hardware": "🔌",
            "Software": "💻", "Integration": "🔗", "Validation": "✅", "Documentation": "📚",
            "Planning": "📅", "Quality": "🎯", "Security": "🔒", "General": "📦"
        }
        return icons.get(self.category, "📦")

class BlockUsageRecord:
    """Enregistrement d'utilisation d'un bloc"""
    def __init__(self, block_id, project_name, start_date, end_date=None, success=True, notes="", lessons_learned=""):
        self.block_id = block_id
        self.project_name = project_name
        self.start_date = start_date
        self.end_date = end_date
        self.success = success
        self.notes = notes
        self.lessons_learned = lessons_learned
        self.duration_days = 0
        
        if end_date and start_date:
            self.duration_days = (end_date - start_date).days



class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configuration de la fenêtre principale
        self.title("Gestionnaire de projet")
        self.geometry("1200x800")
        self.minsize(800, 600)
        
        # Configuration du thème
        ctk.set_appearance_mode("dark")  # "light" ou "dark"
        ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"
        
        # Créer l'interface utilisateur
        self.create_widgets()
        
        # Configurer la grille principale
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
    def create_widgets(self):
        """Créer tous les widgets de l'interface"""
        
        # Frame de navigation (sidebar)
        self.create_sidebar()
        
        # Frame principal
        self.create_main_frame()
        
        # Barre de statut
        self.create_status_bar()
        
        # Afficher le contenu par défaut après que tous les widgets soient créés
        self.show_home()
        
    def create_sidebar(self):
        """Créer la barre latérale de navigation"""
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=3, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(10, weight=1)
        
        # Logo/Titre de l'application
        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text="Menu", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Boutons de navigation
        self.sidebar_button_1 = ctk.CTkButton(
            self.sidebar_frame,
            text="Accueil",
            command=self.show_home,
            width=180
        )
        self.sidebar_button_1.grid(row=1, column=0, padx=20, pady=10)
        
        self.sidebar_button_2 = ctk.CTkButton(
            self.sidebar_frame,
            text="🗂 Cadrage Projet",
            command=self.show_project_charter,
            width=180
        )
        self.sidebar_button_2.grid(row=2, column=0, padx=20, pady=10)
        
        self.sidebar_button_3 = ctk.CTkButton(
            self.sidebar_frame,
            text="🌳 Diagramme en Arbre",
            command=self.show_tree_diagram,
            width=180
        )
        self.sidebar_button_3.grid(row=3, column=0, padx=20, pady=10)
        
        self.sidebar_button_4 = ctk.CTkButton(
            self.sidebar_frame,
            text="✅ Suivi des Tâches",
            command=self.show_task_tracker,
            width=180
        )
        self.sidebar_button_4.grid(row=4, column=0, padx=20, pady=10)
        
        self.sidebar_button_5 = ctk.CTkButton(
            self.sidebar_frame,
            text="💬 Journal de Bord",
            command=self.show_decision_log,
            width=180
        )
        self.sidebar_button_5.grid(row=5, column=0, padx=20, pady=10)
        
        self.sidebar_button_6 = ctk.CTkButton(
            self.sidebar_frame,
            text="📁 Gestion Documents",
            command=self.show_document_manager,
            width=180
        )
        self.sidebar_button_6.grid(row=6, column=0, padx=20, pady=10)
            
        self.sidebar_button_7 = ctk.CTkButton(
            self.sidebar_frame,
            text="📦 Bibliothèque Blocs",
            command=self.show_block_library,
            width=180
        )
        self.sidebar_button_7.grid(row=8, column=0, padx=20, pady=10)

        # Séparateur
        self.separator = ctk.CTkFrame(self.sidebar_frame, height=2)
        self.separator.grid(row=9, column=0, padx=20, pady=20, sticky="ew")
        
        # Thème selector
        self.appearance_mode_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text="Thème:", 
            anchor="w"
        )
        self.appearance_mode_label.grid(row=11, column=0, padx=20, pady=(10, 0))
        
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(
            self.sidebar_frame,
            values=["Light", "Dark", "System"],
            command=self.change_appearance_mode_event
        )
        self.appearance_mode_optionemenu.grid(row=12, column=0, padx=20, pady=(10, 10))
        
    def create_main_frame(self):
        """Créer le frame principal de contenu"""
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, padx=0, pady=0, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        # Titre de la page
        self.main_title = ctk.CTkLabel(
            self.main_frame,
            text="Bienvenue dans votre application",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.main_title.grid(row=0, column=0, padx=20, pady=10)
        
        # Zone de contenu principal
        self.content_frame = ctk.CTkScrollableFrame(self.main_frame)
        self.content_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        
    def create_status_bar(self):
        """Créer la barre de statut"""
        self.status_frame = ctk.CTkFrame(self, height=25)
        self.status_frame.grid(row=1, column=1, padx=0, pady=0, sticky="ew")
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Prêt",
            anchor="w"
        )
        self.status_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
    def clear_content(self):
        """Effacer le contenu actuel"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
    def show_home(self):
        """Afficher la page d'accueil"""
        self.clear_content()
        self.main_title.configure(text="Accueil")
        
        # Contenu de la page d'accueil
        welcome_text = ctk.CTkTextbox(self.content_frame, height=200)
        welcome_text.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        welcome_text.insert("0.0", 
            "Bienvenue dans le gestionnaire de projet !\n\n"
            "Cette application vous permet de :\n"
            "• Naviguer entre différentes étapes de la résalisation du projet\n"
            "• Exporter les différents tableaux, textes et rapports\n"
            "• Ajouter votre documentation et la lier aux différentes étapes de conception\n\n"
        )
        
        # Boutons d'exemple
        button_frame = ctk.CTkFrame(self.content_frame)
        button_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        example_button1 = ctk.CTkButton(
            button_frame,
            text="Ouvrir un projet",
            command=self.load_project,
        )
        example_button1.grid(row=0, column=0, padx=10, pady=10)
        
        example_button2 = ctk.CTkButton(
            button_frame,
            text="Enregistrer le projet",
            command=self.save_project,
        )
        example_button2.grid(row=0, column=1, padx=10, pady=10)
        
        self.update_status("Page d'accueil affichée")
        
    def show_project_charter(self):
        """Afficher le module de cadrage / charte de projet"""
        self.clear_content()
        self.main_title.configure(text="🗂 Cadrage Projet")
        
        # Configurer content_frame pour utiliser tout l'espace disponible
        self.content_frame.grid_rowconfigure(1, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(1, weight=1)
        self.content_frame.grid_columnconfigure(2, weight=1)
        
        # Initialiser les variables si elles n'existent pas
        if not hasattr(self, 'charter_data'):
            self.charter_data = {}
        
        # ✅ NOUVEAU : Toolbar avec boutons d'action
        toolbar_frame = ctk.CTkFrame(self.content_frame)
        toolbar_frame.grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        toolbar_frame.grid_columnconfigure(0, weight=1)
        
        # Boutons d'action
        buttons_frame = ctk.CTkFrame(toolbar_frame)
        buttons_frame.pack(pady=10)
        
        ctk.CTkButton(buttons_frame, text="💾 Sauvegarder", 
                    command=self.save_charter_data, width=120).pack(side="left", padx=5)
        ctk.CTkButton(buttons_frame, text="📄 Export PDF", 
                    command=self.export_charter_pdf, width=120).pack(side="left", padx=5)
        ctk.CTkButton(buttons_frame, text="📝 Export Markdown", 
                    command=self.export_charter_markdown, width=120).pack(side="left", padx=5)
        ctk.CTkButton(buttons_frame, text="👁️ Aperçu", 
                    command=self.preview_charter, width=120).pack(side="left", padx=5)
        
        # Créer trois colonnes pour organiser les sections
        # Colonne 1 - Sections de base
        col1_frame = ctk.CTkFrame(self.content_frame)
        col1_frame.grid(row=1, column=0, padx=(0, 5), pady=0, sticky="nsew")
        col1_frame.grid_columnconfigure(0, weight=1)
        
        # Colonne 2 - Sections intermédiaires  
        col2_frame = ctk.CTkFrame(self.content_frame)
        col2_frame.grid(row=1, column=1, padx=5, pady=0, sticky="nsew")
        col2_frame.grid_columnconfigure(0, weight=1)
        
        # Colonne 3 - Sections avancées
        col3_frame = ctk.CTkFrame(self.content_frame)
        col3_frame.grid(row=1, column=2, padx=(5, 0), pady=0, sticky="nsew")
        col3_frame.grid_columnconfigure(0, weight=1)
        
        # === COLONNE 1 - Sections de base ===
        current_row = 0
        
        # 1. Objectif principal
        obj_label = ctk.CTkLabel(col1_frame, text="🎯 Objectif principal:", 
                                font=ctk.CTkFont(size=14, weight="bold"))
        obj_label.grid(row=current_row, column=0, padx=15, pady=(15, 5), sticky="w")
        current_row += 1
        
        self.objective_text = ctk.CTkTextbox(col1_frame, height=100)
        self.objective_text.grid(row=current_row, column=0, padx=15, pady=(0, 10), sticky="ew")
        if 'objective' in self.charter_data:
            self.objective_text.insert("0.0", self.charter_data['objective'])
        current_row += 1
        
        # 2. Livrables attendus
        deliv_label = ctk.CTkLabel(col1_frame, text="📦 Livrables attendus:", 
                                font=ctk.CTkFont(size=14, weight="bold"))
        deliv_label.grid(row=current_row, column=0, padx=15, pady=(5, 5), sticky="w")
        current_row += 1
        
        self.deliverables_text = ctk.CTkTextbox(col1_frame, height=100)
        self.deliverables_text.grid(row=current_row, column=0, padx=15, pady=(0, 10), sticky="ew")
        if 'deliverables' in self.charter_data:
            self.deliverables_text.insert("0.0", self.charter_data['deliverables'])
        current_row += 1
        
        # 3. Parties prenantes
        stake_label = ctk.CTkLabel(col1_frame, text="👥 Parties prenantes:", 
                                font=ctk.CTkFont(size=14, weight="bold"))
        stake_label.grid(row=current_row, column=0, padx=15, pady=(5, 5), sticky="w")
        current_row += 1
        
        self.stakeholders_text = ctk.CTkTextbox(col1_frame, height=100)
        self.stakeholders_text.grid(row=current_row, column=0, padx=15, pady=(0, 10), sticky="ew")
        if 'stakeholders' in self.charter_data:
            self.stakeholders_text.insert("0.0", self.charter_data['stakeholders'])
        current_row += 1
        
        # 4. Contraintes
        const_label = ctk.CTkLabel(col1_frame, text="⚠️ Contraintes:", 
                                font=ctk.CTkFont(size=14, weight="bold"))
        const_label.grid(row=current_row, column=0, padx=15, pady=(5, 5), sticky="w")
        current_row += 1
        
        self.constraints_text = ctk.CTkTextbox(col1_frame, height=100)
        self.constraints_text.grid(row=current_row, column=0, padx=15, pady=(0, 15), sticky="ew")
        if 'constraints' in self.charter_data:
            self.constraints_text.insert("0.0", self.charter_data['constraints'])
        
        # === COLONNE 2 - Sections intermédiaires ===
        current_row = 0
        
        # 5. Hypothèses initiales
        hypo_label = ctk.CTkLabel(col2_frame, text="💭 Hypothèses initiales:", 
                                font=ctk.CTkFont(size=14, weight="bold"))
        hypo_label.grid(row=current_row, column=0, padx=15, pady=(15, 5), sticky="w")
        current_row += 1
        
        self.assumptions_text = ctk.CTkTextbox(col2_frame, height=100)
        self.assumptions_text.grid(row=current_row, column=0, padx=15, pady=(0, 10), sticky="ew")
        if 'assumptions' in self.charter_data:
            self.assumptions_text.insert("0.0", self.charter_data['assumptions'])
        current_row += 1
        
        # 6. Critères de succès
        success_label = ctk.CTkLabel(col2_frame, text="✅ Critères de succès:", 
                                    font=ctk.CTkFont(size=14, weight="bold"))
        success_label.grid(row=current_row, column=0, padx=15, pady=(5, 5), sticky="w")
        current_row += 1
        
        self.success_criteria_text = ctk.CTkTextbox(col2_frame, height=100)
        self.success_criteria_text.grid(row=current_row, column=0, padx=15, pady=(0, 10), sticky="ew")
        if 'success_criteria' in self.charter_data:
            self.success_criteria_text.insert("0.0", self.charter_data['success_criteria'])
        current_row += 1
        
        # 7. Budget estimé
        budget_label = ctk.CTkLabel(col2_frame, text="💰 Budget estimé:", 
                                font=ctk.CTkFont(size=14, weight="bold"))
        budget_label.grid(row=current_row, column=0, padx=15, pady=(5, 5), sticky="w")
        current_row += 1
        
        self.budget_text = ctk.CTkTextbox(col2_frame, height=100)
        self.budget_text.grid(row=current_row, column=0, padx=15, pady=(0, 10), sticky="ew")
        if 'budget' in self.charter_data:
            self.budget_text.insert("0.0", self.charter_data['budget'])
        current_row += 1
        
        # 8. Échéancier
        schedule_label = ctk.CTkLabel(col2_frame, text="📅 Échéancier:", 
                                    font=ctk.CTkFont(size=14, weight="bold"))
        schedule_label.grid(row=current_row, column=0, padx=15, pady=(5, 5), sticky="w")
        current_row += 1
        
        self.schedule_text = ctk.CTkTextbox(col2_frame, height=100)
        self.schedule_text.grid(row=current_row, column=0, padx=15, pady=(0, 15), sticky="ew")
        if 'schedule' in self.charter_data:
            self.schedule_text.insert("0.0", self.charter_data['schedule'])
        
        # === COLONNE 3 - Sections avancées ===
        current_row = 0
        
        # 9. Risques identifiés
        risks_label = ctk.CTkLabel(col3_frame, text="⚡ Risques identifiés:", 
                                font=ctk.CTkFont(size=14, weight="bold"))
        risks_label.grid(row=current_row, column=0, padx=15, pady=(15, 5), sticky="w")
        current_row += 1
        
        self.risks_text = ctk.CTkTextbox(col3_frame, height=100)
        self.risks_text.grid(row=current_row, column=0, padx=15, pady=(0, 10), sticky="ew")
        if 'risks' in self.charter_data:
            self.risks_text.insert("0.0", self.charter_data['risks'])
        current_row += 1
        
        # 10. Technologies / Outils
        tech_label = ctk.CTkLabel(col3_frame, text="🔧 Technologies / Outils:", 
                                font=ctk.CTkFont(size=14, weight="bold"))
        tech_label.grid(row=current_row, column=0, padx=15, pady=(5, 5), sticky="w")
        current_row += 1
        
        self.technology_text = ctk.CTkTextbox(col3_frame, height=100)
        self.technology_text.grid(row=current_row, column=0, padx=15, pady=(0, 10), sticky="ew")
        if 'technology' in self.charter_data:
            self.technology_text.insert("0.0", self.charter_data['technology'])
        current_row += 1
        
        # 11. Mesures de qualité
        quality_label = ctk.CTkLabel(col3_frame, text="🎯 Mesures de qualité:", 
                                    font=ctk.CTkFont(size=14, weight="bold"))
        quality_label.grid(row=current_row, column=0, padx=15, pady=(5, 5), sticky="w")
        current_row += 1
        
        self.quality_text = ctk.CTkTextbox(col3_frame, height=100)
        self.quality_text.grid(row=current_row, column=0, padx=15, pady=(0, 10), sticky="ew")
        if 'quality' in self.charter_data:
            self.quality_text.insert("0.0", self.charter_data['quality'])
        current_row += 1
        
        # 12. Communication
        comm_label = ctk.CTkLabel(col3_frame, text="📢 Communication:", 
                                font=ctk.CTkFont(size=14, weight="bold"))
        comm_label.grid(row=current_row, column=0, padx=15, pady=(5, 5), sticky="w")
        current_row += 1
        
        self.communication_text = ctk.CTkTextbox(col3_frame, height=100)
        self.communication_text.grid(row=current_row, column=0, padx=15, pady=(0, 15), sticky="ew")
        if 'communication' in self.charter_data:
            self.communication_text.insert("0.0", self.charter_data['communication'])
        
        self.update_status("Module de cadrage projet affiché - toutes sections visibles")

    def save_charter_data(self):
        """Sauvegarder les données de la charte"""
        try:
            # Sauvegarder toutes les données des textbox
            self.charter_data = {
                'objective': self.objective_text.get("1.0", "end-1c"),
                'deliverables': self.deliverables_text.get("1.0", "end-1c"),
                'stakeholders': self.stakeholders_text.get("1.0", "end-1c"),
                'constraints': self.constraints_text.get("1.0", "end-1c"),
                'assumptions': self.assumptions_text.get("1.0", "end-1c"),
                'success_criteria': self.success_criteria_text.get("1.0", "end-1c"),
                'budget': self.budget_text.get("1.0", "end-1c"),
                'schedule': self.schedule_text.get("1.0", "end-1c"),
                'risks': self.risks_text.get("1.0", "end-1c"),
                'technology': self.technology_text.get("1.0", "end-1c"),
                'quality': self.quality_text.get("1.0", "end-1c"),
                'communication': self.communication_text.get("1.0", "end-1c")
            }
            
            # Sauvegarder dans un fichier JSON
            with open("charter_data.json", "w", encoding="utf-8") as f:
                json.dump(self.charter_data, f, ensure_ascii=False, indent=2)
                
            messagebox.showinfo("Sauvegarde", "Données de la charte sauvegardées avec succès!")
            self.update_status("Charte sauvegardée")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde :\n{str(e)}")

    def export_charter_pdf(self):
        """Exporter la charte en PDF"""
        try:
            # Sauvegarder d'abord les données
            self.save_charter_data()
            
            # Demander où sauvegarder
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                title="Exporter la charte de projet"
            )
            
            if filename:
                from reportlab.lib.pagesizes import letter
                from reportlab.pdfgen import canvas
                from reportlab.lib.utils import ImageReader
                
                c = canvas.Canvas(filename, pagesize=letter)
                width, height = letter
                
                # Titre
                c.setFont("Helvetica-Bold", 20)
                c.drawString(50, height - 50, "Charte de Projet")
                
                # Date
                c.setFont("Helvetica", 10)
                c.drawString(50, height - 70, f"Créé le : {datetime.datetime.now().strftime('%d/%m/%Y à %H:%M')}")
                
                y_position = height - 100
                
                sections = [
                    ("Objectif principal", self.charter_data.get('objective', '')),
                    ("Livrables attendus", self.charter_data.get('deliverables', '')),
                    ("Parties prenantes", self.charter_data.get('stakeholders', '')),
                    ("Contraintes", self.charter_data.get('constraints', '')),
                    ("Hypothèses initiales", self.charter_data.get('assumptions', ''))
                ]
                
                for title, content in sections:
                    if y_position < 100:  # Nouvelle page si nécessaire
                        c.showPage()
                        y_position = height - 50
                        
                    c.setFont("Helvetica-Bold", 12)
                    c.drawString(50, y_position, title)
                    y_position -= 20
                    
                    c.setFont("Helvetica", 10)
                    lines = content.split('\n')
                    for line in lines:
                        if y_position < 100:
                            c.showPage()
                            y_position = height - 50
                        c.drawString(70, y_position, line[:80])  # Limiter la longueur
                        y_position -= 15
                    
                    y_position -= 10
                
                c.save()
                messagebox.showinfo("Export PDF", f"Charte exportée avec succès :\n{filename}")
                self.update_status("Charte exportée en PDF")
                
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'export PDF :\n{str(e)}")

    def export_charter_markdown(self):
        """Exporter la charte en Markdown"""
        try:
            # Sauvegarder d'abord les données
            self.save_charter_data()
            
            # Demander où sauvegarder
            filename = filedialog.asksaveasfilename(
                defaultextension=".md",
                filetypes=[("Markdown files", "*.md")],
                title="Sauvegarder la charte de projet"
            )
            
            if filename:
                # Créer le contenu Markdown
                md_content = f"""# 🗂 Charte de Projet

    *Créé le : {datetime.datetime.now().strftime('%d/%m/%Y à %H:%M')}*

    ## 🎯 Objectif principal

    {self.charter_data.get('objective', '')}

    ## 📦 Livrables attendus

    {self.charter_data.get('deliverables', '')}

    ## 👥 Parties prenantes / Intervenants clés

    {self.charter_data.get('stakeholders', '')}

    ## ⚠️ Contraintes

    {self.charter_data.get('constraints', '')}

    ## 💭 Hypothèses initiales

    {self.charter_data.get('assumptions', '')}

    ## ✅ Critères de succès

    {self.charter_data.get('success_criteria', '')}

    ## 💰 Budget estimé

    {self.charter_data.get('budget', '')}

    ## 📅 Échéancier

    {self.charter_data.get('schedule', '')}

    ## ⚡ Risques identifiés

    {self.charter_data.get('risks', '')}

    ## 🔧 Technologies / Outils

    {self.charter_data.get('technology', '')}

    ## 🎯 Mesures de qualité

    {self.charter_data.get('quality', '')}

    ## 📢 Communication

    {self.charter_data.get('communication', '')}

    ---
    *Document généré automatiquement par l'application de gestion de projet*
    """
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(md_content)
                    
                messagebox.showinfo("Export Markdown", f"Charte exportée avec succès :\n{filename}")
                self.update_status("Charte exportée en Markdown")
                
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'export Markdown :\n{str(e)}")

    def preview_charter(self):
        """Afficher un aperçu de la charte"""
        # Sauvegarder d'abord les données
        self.save_charter_data()
        
        # Créer une nouvelle fenêtre pour l'aperçu
        preview_window = ctk.CTkToplevel(self)
        preview_window.title("Aperçu de la Charte de Projet")
        preview_window.geometry("800x600")
        
        # Zone de texte pour l'aperçu
        preview_text = ctk.CTkTextbox(preview_window)
        preview_text.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Contenu de l'aperçu
        preview_content = f"""🗂 CHARTE DE PROJET

    Créé le : {datetime.datetime.now().strftime('%d/%m/%Y à %H:%M')}

    🎯 OBJECTIF PRINCIPAL
    {self.charter_data.get('objective', 'Non renseigné')}

    📦 LIVRABLES ATTENDUS
    {self.charter_data.get('deliverables', 'Non renseigné')}

    👥 PARTIES PRENANTES / INTERVENANTS CLÉS
    {self.charter_data.get('stakeholders', 'Non renseigné')}

    ⚠️ CONTRAINTES
    {self.charter_data.get('constraints', 'Non renseigné')}

    💭 HYPOTHÈSES INITIALES
    {self.charter_data.get('assumptions', 'Non renseigné')}

    ✅ CRITÈRES DE SUCCÈS
    {self.charter_data.get('success_criteria', 'Non renseigné')}

    💰 BUDGET ESTIMÉ
    {self.charter_data.get('budget', 'Non renseigné')}

    📅 ÉCHÉANCIER
    {self.charter_data.get('schedule', 'Non renseigné')}

    ⚡ RISQUES IDENTIFIÉS
    {self.charter_data.get('risks', 'Non renseigné')}

    🔧 TECHNOLOGIES / OUTILS
    {self.charter_data.get('technology', 'Non renseigné')}

    🎯 MESURES DE QUALITÉ
    {self.charter_data.get('quality', 'Non renseigné')}

    📢 COMMUNICATION
    {self.charter_data.get('communication', 'Non renseigné')}

    ---
    Document généré automatiquement par l'application de gestion de projet
    """
        
        preview_text.insert("0.0", preview_content)
        preview_text.configure(state="disabled")
        
        self.update_status("Aperçu de la charte affiché") 
                
    def preview_charter(self):
        """Afficher un aperçu de la charte"""
        # Sauvegarder d'abord les données
        self.save_charter_data()
        
        # Créer une nouvelle fenêtre pour l'aperçu
        preview_window = ctk.CTkToplevel(self)
        preview_window.title("Aperçu de la Charte de Projet")
        preview_window.geometry("800x600")
        
        # Zone de texte pour l'aperçu
        preview_text = ctk.CTkTextbox(preview_window)
        preview_text.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Contenu de l'aperçu
        preview_content = f"""🗂 CHARTE DE PROJET

Créé le : {datetime.datetime.now().strftime('%d/%m/%Y à %H:%M')}

🎯 OBJECTIF PRINCIPAL
{self.charter_data.get('objective', 'Non renseigné')}

📦 LIVRABLES ATTENDUS
{self.charter_data.get('deliverables', 'Non renseigné')}

👥 PARTIES PRENANTES / INTERVENANTS CLÉS
{self.charter_data.get('stakeholders', 'Non renseigné')}

⚠️ CONTRAINTES
{self.charter_data.get('constraints', 'Non renseigné')}

💭 HYPOTHÈSES INITIALES
{self.charter_data.get('assumptions', 'Non renseigné')}

---
Document généré automatiquement par l'application de gestion de projet
"""
        
        preview_text.insert("0.0", preview_content)
        preview_text.configure(state="disabled")
        
        self.update_status("Aperçu de la charte affiché")
        
    def show_tree_diagram(self):
        """Afficher le module de diagramme en arbre - CORRIGÉ"""
        self.clear_content()
        self.main_title.configure(text="🌳 Diagramme en Arbre")
        
        # ✅ CORRECTION : Initialiser seulement si nécessaire
        if not hasattr(self, 'tree_nodes'):
            self.tree_nodes = []
        if not hasattr(self, 'selected_tree_node'):
            self.selected_tree_node = None
        if not hasattr(self, 'tree_mode'):
            self.tree_mode = "select"
        if not hasattr(self, 'connection_start'):
            self.connection_start = None
        if not hasattr(self, 'zoom_factor'):
            self.zoom_factor = 1.0
        if not hasattr(self, 'drag_data'):
            self.drag_data = {"x": 0, "y": 0, "item": None}
        
        # Frame pour la toolbar
        toolbar_frame = ctk.CTkFrame(self.content_frame)
        toolbar_frame.grid(row=0, column=0, padx=5, pady=2, sticky="ew")
    
        
        # Modes d'interaction
        mode_label = ctk.CTkLabel(toolbar_frame, text="Mode:")
        mode_label.grid(row=0, column=0, padx=5, pady=5)
        
        mode_frame = ctk.CTkFrame(toolbar_frame)
        mode_frame.grid(row=0, column=1, padx=5, pady=5)
        
        # Boutons de mode
        select_btn = ctk.CTkButton(mode_frame, text="Sélection", width=80, height=25,
                                command=lambda: self.change_tree_mode("select"))
        select_btn.grid(row=0, column=0, padx=2, pady=2)
        
        add_btn = ctk.CTkButton(mode_frame, text="Ajouter", width=80, height=25,
                            command=lambda: self.change_tree_mode("add_node"))
        add_btn.grid(row=0, column=1, padx=2, pady=2)
        
        connect_btn = ctk.CTkButton(mode_frame, text="Connecter", width=80, height=25,
                                command=lambda: self.change_tree_mode("connect"))
        connect_btn.grid(row=0, column=2, padx=2, pady=2)
        
        delete_btn = ctk.CTkButton(mode_frame, text="Supprimer", width=80, height=25,
                                command=lambda: self.change_tree_mode("delete"))
        delete_btn.grid(row=0, column=3, padx=2, pady=2)
        
        # Boutons d'action
        action_frame = ctk.CTkFrame(toolbar_frame)
        action_frame.grid(row=0, column=2, padx=10, pady=5)
        
        center_btn = ctk.CTkButton(action_frame, text="Centrer", width=60, height=25,
                                command=self.tree_center_view)
        center_btn.grid(row=0, column=0, padx=2)
        
        clear_btn = ctk.CTkButton(action_frame, text="Effacer", width=60, height=25,
                                command=self.clear_tree)
        clear_btn.grid(row=0, column=1, padx=2)
        
        # Frame principal avec canvas
        main_tree_frame = ctk.CTkFrame(self.content_frame)
        main_tree_frame.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
        main_tree_frame.grid_columnconfigure(0, weight=1)
        main_tree_frame.grid_rowconfigure(0, weight=1)
        
        # Canvas
        canvas_frame = ctk.CTkFrame(main_tree_frame)
        canvas_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        canvas_frame.grid_columnconfigure(0, weight=1)
        canvas_frame.grid_rowconfigure(0, weight=1)
        
        self.tree_canvas = tk.Canvas(canvas_frame, bg='white', width=1300, height=850)
        self.tree_canvas.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.tree_canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient="horizontal", command=self.tree_canvas.xview)
        self.tree_canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Configuration de la zone de scroll
        self.tree_canvas.configure(scrollregion=(-500, -500, 1500, 1500))
        
        # Panel de propriétés simple
        self.tree_properties_frame = ctk.CTkFrame(main_tree_frame, width=200)
        self.tree_properties_frame.grid(row=0, column=1, sticky="nsew")
        self.tree_properties_frame.grid_propagate(False)
        
        self.setup_simple_tree_properties()
        
        # Bind des événements
        self.tree_canvas.bind("<Button-1>", self.on_tree_canvas_click)
        self.tree_canvas.bind("<B1-Motion>", self.on_tree_canvas_drag)
        self.tree_canvas.bind("<ButtonRelease-1>", self.on_tree_canvas_release)
        
        # ✅ CORRECTION : Créer un nœud racine seulement si l'arbre est vide
        if not self.tree_nodes:
            self.create_tree_root_node()
        else:
            # Redessiner l'arbre existant
            self.redraw_tree_all()
            self.update_tree_statistics()
        
        self.content_frame.grid_rowconfigure(1, weight=1)
        self.update_status("Module de diagramme en arbre affiché")

    def setup_simple_tree_properties(self):
        """Configurer un panel de propriétés simplifié"""
        # Titre
        title_label = ctk.CTkLabel(self.tree_properties_frame, text="Propriétés", 
                                font=ctk.CTkFont(size=14, weight="bold"))
        title_label.pack(pady=10)
        
        # Texte du noeud
        text_label = ctk.CTkLabel(self.tree_properties_frame, text="Texte du noeud:")
        text_label.pack(anchor='w', padx=10, pady=(10, 0))
        
        self.tree_text_entry = ctk.CTkEntry(self.tree_properties_frame, width=160)
        self.tree_text_entry.pack(padx=10, pady=5)
        self.tree_text_entry.bind('<Return>', self.update_node_text)
        
        # Bouton pour appliquer
        apply_btn = ctk.CTkButton(self.tree_properties_frame, text="Appliquer", 
                                command=self.update_node_text)
        apply_btn.pack(pady=5)
        
        # Actions rapides
        actions_label = ctk.CTkLabel(self.tree_properties_frame, text="Actions:")
        actions_label.pack(anchor='w', padx=10, pady=(20, 5))
        
        add_child_btn = ctk.CTkButton(self.tree_properties_frame, text="+ Enfant", 
                                    command=self.add_child_to_selected)
        add_child_btn.pack(pady=2, padx=10, fill='x')
        
        delete_node_btn = ctk.CTkButton(self.tree_properties_frame, text="Supprimer", 
                                    command=self.delete_selected_node)
        delete_node_btn.pack(pady=2, padx=10, fill='x')
        
        # Statistiques
        stats_label = ctk.CTkLabel(self.tree_properties_frame, text="Statistiques:")
        stats_label.pack(anchor='w', padx=10, pady=(20, 5))
        
        self.tree_stats_label = ctk.CTkLabel(self.tree_properties_frame, text="Noeuds: 0")
        self.tree_stats_label.pack(padx=10, pady=5)

    def change_tree_mode(self, mode):
        """Changer le mode d'édition du diagramme"""
        self.tree_mode = mode
        self.connection_start = None
        self.update_status(f"Mode: {mode}")

    def create_tree_root_node(self):
        """Créer le noeud racine"""
        root_node = TreeNode("Racine", 400, 200)
        self.tree_nodes.append(root_node)
        self.draw_tree_node(root_node)
        self.update_tree_statistics()

    def draw_tree_node(self, node):
        """Dessiner un noeud sur le canvas"""
        # Calculer la taille basée sur le texte
        text_width = len(node.text) * 8 + 20
        node.width = max(60, text_width)
        node.height = 40
        
        # Position sur le canvas
        x, y = node.x, node.y
        w, h = node.width, node.height
        
        # Supprimer l'ancien dessin
        if hasattr(node, 'canvas_id') and node.canvas_id:
            self.tree_canvas.delete(node.canvas_id)
        if hasattr(node, 'text_id') and node.text_id:
            self.tree_canvas.delete(node.text_id)
        
        # Couleur selon la sélection
        fill_color = "#FFE082" if node.selected else "#E3F2FD"
        border_color = "#FF5722" if node.selected else "#2196F3"
        border_width = 2 if node.selected else 1
        
        # Dessiner le rectangle
        node.canvas_id = self.tree_canvas.create_rectangle(
            x - w/2, y - h/2, x + w/2, y + h/2,
            fill=fill_color,
            outline=border_color,
            width=border_width,
            tags="node"
        )
        
        # Dessiner le texte
        node.text_id = self.tree_canvas.create_text(
            x, y,
            text=node.text,
            fill="#000000",
            font=("Arial", 10),
            tags="node_text"
        )

    def draw_tree_connections(self):
        """Dessiner toutes les connexions"""
        # Supprimer les anciennes connexions
        self.tree_canvas.delete("connection")
        
        # Dessiner les nouvelles connexions
        for node in self.tree_nodes:
            for child in node.children:
                self.draw_connection(node, child)

    def draw_connection(self, parent, child):
        """Dessiner une connexion entre deux noeuds"""
        x1, y1 = parent.x, parent.y
        x2, y2 = child.x, child.y
        
        # Calculer les points de connexion sur les bords des rectangles
        dx, dy = x2 - x1, y2 - y1
        dist = (dx*dx + dy*dy) ** 0.5
        
        if dist > 0:
            # Points sur les bords
            px1 = x1 + (dx/dist) * (parent.width/2)
            py1 = y1 + (dy/dist) * (parent.height/2)
            px2 = x2 - (dx/dist) * (child.width/2)
            py2 = y2 - (dy/dist) * (child.height/2)
            
            # Dessiner la ligne avec flèche
            self.tree_canvas.create_line(
                px1, py1, px2, py2,
                fill="#666666",
                width=2,
                arrow=tk.LAST,
                arrowshape=(8, 10, 3),
                tags="connection"
            )

    def redraw_tree_all(self):
        """Redessiner tout le diagramme"""
        self.tree_canvas.delete("all")
        
        # Dessiner les connexions d'abord
        self.draw_tree_connections()
        
        # Puis dessiner les noeuds
        for node in self.tree_nodes:
            self.draw_tree_node(node)

    def on_tree_canvas_click(self, event):
        """Gérer les clics sur le canvas"""
        x = self.tree_canvas.canvasx(event.x)
        y = self.tree_canvas.canvasy(event.y)
        
        if self.tree_mode == "select":
            self.select_node_at(x, y)
            self.drag_data = {"x": x, "y": y, "item": self.selected_tree_node}
        elif self.tree_mode == "add_node":
            self.create_node_at(x, y)
        elif self.tree_mode == "connect":
            self.handle_connection_at(x, y)
        elif self.tree_mode == "delete":
            self.delete_node_at(x, y)

    def on_tree_canvas_drag(self, event):
        """Gérer le glissement"""
        if self.tree_mode == "select" and self.drag_data["item"]:
            x = self.tree_canvas.canvasx(event.x)
            y = self.tree_canvas.canvasy(event.y)
            
            dx = x - self.drag_data["x"]
            dy = y - self.drag_data["y"]
            
            self.drag_data["item"].x += dx
            self.drag_data["item"].y += dy
            
            self.drag_data["x"] = x
            self.drag_data["y"] = y
            
            self.redraw_tree_all()

    def on_tree_canvas_release(self, event):
        """Gérer le relâchement"""
        self.drag_data = {"x": 0, "y": 0, "item": None}

    def select_node_at(self, x, y):
        """Sélectionner un noeud à la position donnée"""
        # Désélectionner le noeud actuel
        if self.selected_tree_node:
            self.selected_tree_node.selected = False
        
        # Trouver le noeud cliqué
        clicked_node = None
        for node in self.tree_nodes:
            if (abs(node.x - x) < node.width/2 and 
                abs(node.y - y) < node.height/2):
                clicked_node = node
                break
        
        # Sélectionner le nouveau noeud
        self.selected_tree_node = clicked_node
        if self.selected_tree_node:
            self.selected_tree_node.selected = True
            self.update_properties_panel()
        
        self.redraw_tree_all()

    def create_node_at(self, x, y):
        """Créer un nouveau noeud"""
        new_node = TreeNode(f"Noeud {len(self.tree_nodes) + 1}", x, y)
        self.tree_nodes.append(new_node)
        self.draw_tree_node(new_node)
        self.update_tree_statistics()

    def handle_connection_at(self, x, y):
        """Gérer la création de connexions"""
        clicked_node = self.find_node_at(x, y)
        
        if clicked_node:
            if self.connection_start is None:
                self.connection_start = clicked_node
                self.update_status("Sélectionnez le noeud de destination")
            else:
                if self.connection_start != clicked_node:
                    self.connection_start.add_child(clicked_node)
                    self.redraw_tree_all()
                    self.update_status("Connexion créée")
                self.connection_start = None

    def delete_node_at(self, x, y):
        """Supprimer un noeud"""
        node_to_delete = self.find_node_at(x, y)
        if node_to_delete and len(self.tree_nodes) > 1:
            self.delete_tree_node(node_to_delete)

    def find_node_at(self, x, y):
        """Trouver le noeud à la position donnée"""
        for node in self.tree_nodes:
            if (abs(node.x - x) < node.width/2 and 
                abs(node.y - y) < node.height/2):
                return node
        return None

    def delete_tree_node(self, node):
        """Supprimer un noeud"""
        # Supprimer des enfants du parent
        if node.parent:
            node.parent.remove_child(node)
        
        # Déplacer les enfants vers le parent
        for child in node.children[:]:
            node.remove_child(child)
            if node.parent:
                node.parent.add_child(child)
        
        # Supprimer de la liste
        self.tree_nodes.remove(node)
        
        if self.selected_tree_node == node:
            self.selected_tree_node = None
            
        self.redraw_tree_all()
        self.update_tree_statistics()

    def tree_center_view(self):
        """Centrer la vue sur les noeuds"""
        if not self.tree_nodes:
            return
        
        # Calculer le centre des noeuds
        min_x = min(node.x for node in self.tree_nodes)
        max_x = max(node.x for node in self.tree_nodes)
        min_y = min(node.y for node in self.tree_nodes)
        max_y = max(node.y for node in self.tree_nodes)
        
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        
        # Centrer le canvas
        canvas_width = self.tree_canvas.winfo_width()
        canvas_height = self.tree_canvas.winfo_height()
        
        scroll_x = (center_x - canvas_width/2) / 2000
        scroll_y = (center_y - canvas_height/2) / 2000
        
        self.tree_canvas.xview_moveto(max(0, min(1, scroll_x)))
        self.tree_canvas.yview_moveto(max(0, min(1, scroll_y)))

    def clear_tree(self):
        """Effacer tout le diagramme"""
        if messagebox.askyesno("Confirmation", "Effacer tout le diagramme ?\n\nCette action est irréversible !"):
            self.tree_nodes.clear()
            self.selected_tree_node = None
            self.connection_start = None
            self.tree_canvas.delete("all")
            self.create_tree_root_node()
            self.update_status("Diagramme effacé et réinitialisé")

    def update_node_text(self, event=None):
        """Mettre à jour le texte du noeud sélectionné"""
        if self.selected_tree_node:
            new_text = self.tree_text_entry.get().strip()
            if new_text:
                self.selected_tree_node.text = new_text
                self.redraw_tree_all()

    def update_properties_panel(self):
        """Mettre à jour le panel de propriétés"""
        if self.selected_tree_node:
            self.tree_text_entry.delete(0, tk.END)
            self.tree_text_entry.insert(0, self.selected_tree_node.text)

    def add_child_to_selected(self):
        """Ajouter un enfant au noeud sélectionné"""
        if not self.selected_tree_node:
            messagebox.showwarning("Attention", "Sélectionnez d'abord un noeud")
            return
        
        parent = self.selected_tree_node
        child = TreeNode("Nouveau", parent.x + 100, parent.y + 80)
        parent.add_child(child)
        self.tree_nodes.append(child)
        self.redraw_tree_all()
        self.update_tree_statistics()

    def delete_selected_node(self):
        """Supprimer le noeud sélectionné"""
        if not self.selected_tree_node:
            messagebox.showwarning("Attention", "Sélectionnez d'abord un noeud")
            return
        
        if len(self.tree_nodes) <= 1:
            messagebox.showwarning("Attention", "Impossible de supprimer le dernier noeud")
            return
        
        if messagebox.askyesno("Confirmation", f"Supprimer '{self.selected_tree_node.text}' ?"):
            self.delete_tree_node(self.selected_tree_node)

    def update_tree_statistics(self):
        """Mettre à jour les statistiques"""
        count = len(self.tree_nodes)
        self.tree_stats_label.configure(text=f"Noeuds: {count}")
        
    def show_task_tracker(self):
        """Afficher le module de suivi des tâches"""
        self.clear_content()
        self.main_title.configure(text="✅ Module de Suivi des Tâches")
        
        # ✅ CORRECTION : Configuration de l'expansion complète
        self.content_frame.grid_rowconfigure(1, weight=1)  # Ligne principale des tâches
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        # Initialiser les variables des tâches si nécessaire
        if not hasattr(self, 'tasks'):
            self.tasks = []
        if not hasattr(self, 'task_view_mode'):
            self.task_view_mode = "kanban"
        
        # ✅ NOUVEAU : Taille fixe en mode Large
        self.task_area_width = 1600   # Taille Large fixe
        self.task_area_height = 800   # Taille Large fixe
            
        # Toolbar avec boutons d'action
        toolbar_frame = ctk.CTkFrame(self.content_frame)
        toolbar_frame.grid(row=0, column=0, padx=5, pady=2, sticky="ew")
        
        # Boutons principaux
        main_buttons_frame = ctk.CTkFrame(toolbar_frame)
        main_buttons_frame.grid(row=0, column=0, padx=5, pady=5)
        
        ctk.CTkButton(main_buttons_frame, text="➕ Nouvelle Tâche", 
                    command=self.add_new_task).grid(row=0, column=0, padx=5, pady=5)
        ctk.CTkButton(main_buttons_frame, text="🔄 Synchroniser avec Arbre", 
                    command=self.sync_tasks_with_tree).grid(row=0, column=1, padx=5, pady=5)
        ctk.CTkButton(main_buttons_frame, text="📝 Tâches d'exemple", 
                    command=self.create_sample_tasks).grid(row=0, column=2, padx=5, pady=5)
        
        # Sélecteur de vue
        view_frame = ctk.CTkFrame(toolbar_frame)
        view_frame.grid(row=0, column=1, padx=20, pady=5)
        
        ctk.CTkLabel(view_frame, text="Vue:").grid(row=0, column=0, padx=5, pady=5)
        
        self.task_view_var = tk.StringVar(value=self.task_view_mode)
        view_kanban_btn = ctk.CTkButton(view_frame, text="📋 Kanban", width=80, height=25,
                                    command=lambda: self.change_task_view("kanban"))
        view_kanban_btn.grid(row=0, column=1, padx=2, pady=5)
        
        view_table_btn = ctk.CTkButton(view_frame, text="📊 Tableau", width=80, height=25,
                                    command=lambda: self.change_task_view("table"))
        view_table_btn.grid(row=0, column=2, padx=2, pady=5)
        
        # Statistiques
        stats_frame = ctk.CTkFrame(toolbar_frame)
        stats_frame.grid(row=0, column=2, padx=20, pady=5)
        
        self.task_stats_label = ctk.CTkLabel(stats_frame, text="Chargement...")
        self.task_stats_label.grid(row=0, column=0, padx=10, pady=5)
        
        # ✅ Frame principal avec zone de tâches en taille Large fixe
        main_task_frame = ctk.CTkFrame(self.content_frame)
        main_task_frame.grid(row=1, column=0, padx=5, pady=2, sticky="nsew")
        main_task_frame.grid_columnconfigure(0, weight=1)
        main_task_frame.grid_rowconfigure(0, weight=1)
        
        # ✅ Canvas pour la zone de tâches avec taille Large fixe
        task_canvas_frame = ctk.CTkFrame(main_task_frame)
        task_canvas_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        task_canvas_frame.grid_columnconfigure(0, weight=1)
        task_canvas_frame.grid_rowconfigure(0, weight=1)
        
        # ✅ Canvas principal des tâches avec taille Large (1600x800)
        self.task_canvas = tk.Canvas(task_canvas_frame, bg='#f0f0f0', 
                                    width=self.task_area_width, 
                                    height=self.task_area_height)
        self.task_canvas.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbars pour la zone de tâches
        task_v_scrollbar = ttk.Scrollbar(task_canvas_frame, orient="vertical", command=self.task_canvas.yview)
        task_h_scrollbar = ttk.Scrollbar(task_canvas_frame, orient="horizontal", command=self.task_canvas.xview)
        self.task_canvas.configure(yscrollcommand=task_v_scrollbar.set, xscrollcommand=task_h_scrollbar.set)
        
        task_v_scrollbar.grid(row=0, column=1, sticky="ns")
        task_h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Configuration de la zone de scroll
        self.task_canvas.configure(scrollregion=(0, 0, self.task_area_width + 200, self.task_area_height + 200))
        
        # ✅ Frame pour le contenu des tâches à l'intérieur du canvas
        self.task_content_frame = ctk.CTkFrame(self.task_canvas)
        self.task_canvas_window = self.task_canvas.create_window(0, 0, anchor="nw", window=self.task_content_frame)
        self.task_content_frame.grid_columnconfigure(0, weight=1)
        
        # Bind pour ajuster la taille du frame interne
        self.task_content_frame.bind('<Configure>', self.on_task_frame_configure)
        self.task_canvas.bind('<Configure>', self.on_task_canvas_configure)
        
        # Afficher la vue actuelle
        self.refresh_task_view()
        
        self.update_status("Module de suivi des tâches affiché en taille Large (1600x800)")

    def update_task_area_size(self, value=None):
        """Mettre à jour la taille de la zone de tâches"""
        # Récupérer les nouvelles valeurs
        new_width = int(self.task_width_slider.get())
        new_height = int(self.task_height_slider.get())
        
        # Mettre à jour les variables
        self.task_area_width = new_width
        self.task_area_height = new_height
        
        # Mettre à jour les labels
        self.task_width_label.configure(text=f"{new_width}px")
        self.task_height_label.configure(text=f"{new_height}px")
        
        # Redimensionner le canvas
        if hasattr(self, 'task_canvas'):
            self.task_canvas.configure(width=new_width, height=new_height)
            self.task_canvas.configure(scrollregion=(0, 0, new_width + 200, new_height + 200))
            
            # Rafraîchir l'affichage
            self.refresh_task_view()

    def set_task_area_preset(self, width, height):
        """Définir une taille prédéfinie pour la zone de tâches"""
        self.task_area_width = width
        self.task_area_height = height
        
        # Mettre à jour les sliders
        self.task_width_slider.set(width)
        self.task_height_slider.set(height)
        
        # Appliquer les changements
        self.update_task_area_size()
        
        self.update_status(f"Zone de tâches redimensionnée : {width}x{height}")

    def on_task_frame_configure(self, event):
        """Gérer le redimensionnement du frame de contenu des tâches"""
        # Mettre à jour la scrollregion pour inclure tout le contenu
        self.task_canvas.configure(scrollregion=self.task_canvas.bbox("all"))

    def on_task_canvas_configure(self, event):
        """Gérer le redimensionnement du canvas des tâches"""
        # Ajuster la largeur du frame interne au canvas
        canvas_width = event.width
        self.task_canvas.itemconfig(self.task_canvas_window, width=canvas_width)

    def refresh_task_view(self):
        """Rafraîchir l'affichage des tâches - MODIFIÉ pour utiliser le canvas"""
        print(f"🔄 Rafraîchissement de l'affichage des tâches...")
        print(f"   - Nombre de tâches: {len(self.tasks)}")
        print(f"   - Mode de vue: {self.task_view_mode}")
        print(f"   - Taille zone: {self.task_area_width}x{self.task_area_height}")
        
        # Nettoyer le contenu actuel
        for widget in self.task_content_frame.winfo_children():
            widget.destroy()
            
        # Debug: afficher le nombre de tâches
        print(f"Nombre de tâches: {len(self.tasks)}")
        print(f"Mode de vue: {self.task_view_mode}")
            
        if self.task_view_mode == "kanban":
            print("   ➡️ Affichage vue Kanban")
            self.show_kanban_view()
        else:
            print("   ➡️ Affichage vue Tableau")
            self.show_table_view()
            
        self.update_task_stats()
        print(f"✅ Rafraîchissement terminé")

    def show_kanban_view(self):
        """Afficher la vue Kanban - MODIFIÉ pour utiliser l'espace personnalisable"""
        # Créer les colonnes avec largeur adaptée
        kanban_frame = ctk.CTkFrame(self.task_content_frame)
        kanban_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        kanban_frame.grid_columnconfigure(0, weight=1)
        kanban_frame.grid_columnconfigure(1, weight=1)
        kanban_frame.grid_columnconfigure(2, weight=1)
        
        statuses = ["À faire", "En cours", "Terminé"]
        status_colors = ["#FFE0B2", "#BBDEFB", "#C8E6C9"]
        
        # Calculer la largeur des colonnes selon la zone disponible
        column_width = max(300, (self.task_area_width - 60) // 3)  # 60px pour les marges
        
        for i, status in enumerate(statuses):
            # Colonne
            column_frame = ctk.CTkFrame(kanban_frame, width=column_width)
            column_frame.grid(row=0, column=i, sticky="nsew", padx=5, pady=5)
            column_frame.grid_propagate(False)  # ✅ Maintenir la largeur fixe
            
            # En-tête de colonne
            header = ctk.CTkLabel(column_frame, text=f"{status}", 
                                font=ctk.CTkFont(size=16, weight="bold"))
            header.pack(pady=10)
            
            # Séparateur
            separator = ctk.CTkFrame(column_frame, height=2)
            separator.pack(fill="x", padx=10, pady=5)
            
            # Zone scrollable pour les tâches de cette colonne
            column_scroll = ctk.CTkScrollableFrame(column_frame, 
                                                height=max(400, self.task_area_height - 150))
            column_scroll.pack(fill="both", expand=True, padx=5, pady=5)
            
            # Tâches dans cette colonne
            tasks_in_status = [task for task in self.tasks if task.status == status]
            
            for task in tasks_in_status:
                self.create_kanban_task_card_enhanced(column_scroll, task, column_width - 30)

    def create_kanban_task_card_enhanced(self, parent, task, card_width):
        """Créer une carte de tâche améliorée pour la vue Kanban"""
        card = ctk.CTkFrame(parent, width=card_width)
        card.pack(fill="x", padx=5, pady=5)
        card.grid_propagate(False)
        
        # Titre de la tâche avec largeur adaptée
        title_label = ctk.CTkLabel(card, text=task.title, 
                                font=ctk.CTkFont(size=12, weight="bold"),
                                wraplength=card_width - 20)
        title_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Priorité
        priority_colors = {"Basse": "#4CAF50", "Moyenne": "#FF9800", "Critique": "#F44336"}
        priority_label = ctk.CTkLabel(card, text=f"🔥 {task.priority}", 
                                    text_color=priority_colors.get(task.priority, "#666666"))
        priority_label.pack(anchor="w", padx=10, pady=2)
        
        # Responsable
        if task.assignee:
            assignee_label = ctk.CTkLabel(card, text=f"👤 {task.assignee}")
            assignee_label.pack(anchor="w", padx=10, pady=2)
            
        # Échéance
        if task.due_date:
            due_label = ctk.CTkLabel(card, text=f"📅 {task.due_date}")
            due_label.pack(anchor="w", padx=10, pady=2)
            
        # Lien avec noeud de l'arbre
        if task.linked_node:
            node_label = ctk.CTkLabel(card, text=f"🌳 {task.linked_node.text}", 
                                    text_color="#2196F3")
            node_label.pack(anchor="w", padx=10, pady=2)
            
        # Boutons d'action
        buttons_frame = ctk.CTkFrame(card)
        buttons_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(buttons_frame, text="✏️", width=30, height=25,
                    command=lambda: self.edit_task(task)).pack(side="left", padx=2)
        ctk.CTkButton(buttons_frame, text="🗑️", width=30, height=25,
                    command=lambda: self.delete_task(task)).pack(side="left", padx=2)
                    
        # Boutons de changement de statut
        if task.status == "À faire":
            ctk.CTkButton(buttons_frame, text="▶️", width=30, height=25,
                        command=lambda: self.change_task_status(task, "En cours")).pack(side="right", padx=2)
        elif task.status == "En cours":
            ctk.CTkButton(buttons_frame, text="✅", width=30, height=25,
                        command=lambda: self.change_task_status(task, "Terminé")).pack(side="right", padx=2)
            ctk.CTkButton(buttons_frame, text="⏸️", width=30, height=25,
                        command=lambda: self.change_task_status(task, "À faire")).pack(side="right", padx=2)
        else:  # Terminé
            ctk.CTkButton(buttons_frame, text="🔄", width=30, height=25,
                        command=lambda: self.change_task_status(task, "En cours")).pack(side="right", padx=2)

    def show_table_view(self):
        """Afficher la vue tableau - MODIFIÉ pour utiliser l'espace personnalisable"""
        # En-têtes avec largeur adaptée
        headers_frame = ctk.CTkFrame(self.task_content_frame)
        headers_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        headers_frame.grid_columnconfigure(0, weight=2)  # Titre
        headers_frame.grid_columnconfigure(1, weight=1)  # Statut
        headers_frame.grid_columnconfigure(2, weight=1)  # Priorité
        headers_frame.grid_columnconfigure(3, weight=1)  # Responsable
        headers_frame.grid_columnconfigure(4, weight=1)  # Échéance
        headers_frame.grid_columnconfigure(5, weight=1)  # Actions
        
        headers = ["Titre", "Statut", "Priorité", "Responsable", "Échéance", "Actions"]
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(headers_frame, text=header, 
                            font=ctk.CTkFont(size=12, weight="bold"))
            label.grid(row=0, column=i, padx=5, pady=10, sticky="w")
            
        # Zone scrollable pour les lignes de tâches
        table_scroll = ctk.CTkScrollableFrame(self.task_content_frame, 
                                            height=max(500, self.task_area_height - 100))
        table_scroll.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        table_scroll.grid_columnconfigure(0, weight=1)
            
        # Tâches
        for i, task in enumerate(self.tasks):
            self.create_table_task_row_enhanced(table_scroll, task, i)

    def create_table_task_row_enhanced(self, parent, task, row_index):
        """Créer une ligne de tâche améliorée pour la vue tableau"""
        row_frame = ctk.CTkFrame(parent)
        row_frame.grid(row=row_index, column=0, sticky="ew", padx=5, pady=2)
        
        # ✅ CORRECTION : Configuration des colonnes avec weights identiques aux en-têtes
        row_frame.grid_columnconfigure(0, weight=2)  # Titre
        row_frame.grid_columnconfigure(1, weight=1)  # Statut
        row_frame.grid_columnconfigure(2, weight=1)  # Priorité
        row_frame.grid_columnconfigure(3, weight=1)  # Responsable
        row_frame.grid_columnconfigure(4, weight=1)  # Échéance
        row_frame.grid_columnconfigure(5, weight=1)  # Actions
        
        # ✅ CORRECTION : Titre avec largeur minimale et alignement cohérent
        title_text = task.title
        if task.linked_node:
            title_text += f" 🌳"
        title_label = ctk.CTkLabel(row_frame, text=title_text, anchor="w")
        title_label.grid(row=0, column=0, padx=5, pady=5, sticky="ew")  # ✅ sticky="ew"
        
        # ✅ CORRECTION : Statut avec couleur et centrage
        status_colors = {"À faire": "#FF9800", "En cours": "#2196F3", "Terminé": "#4CAF50"}
        status_label = ctk.CTkLabel(row_frame, text=task.status, 
                                text_color=status_colors.get(task.status, "#666666"))
        status_label.grid(row=0, column=1, padx=5, pady=5, sticky="ew")  # ✅ sticky="ew"
        
        # ✅ CORRECTION : Priorité avec couleur et centrage
        priority_colors = {"Basse": "#4CAF50", "Moyenne": "#FF9800", "Critique": "#F44336"}
        priority_label = ctk.CTkLabel(row_frame, text=task.priority,
                                    text_color=priority_colors.get(task.priority, "#666666"))
        priority_label.grid(row=0, column=2, padx=5, pady=5, sticky="ew")  # ✅ sticky="ew"
        
        # ✅ CORRECTION : Responsable avec gestion des textes vides
        assignee_text = task.assignee if task.assignee and task.assignee.strip() else "-"
        assignee_label = ctk.CTkLabel(row_frame, text=assignee_text)
        assignee_label.grid(row=0, column=3, padx=5, pady=5, sticky="ew")  # ✅ sticky="ew"
        
        # ✅ CORRECTION : Échéance avec gestion des dates vides
        due_text = task.due_date if task.due_date and task.due_date.strip() else "-"
        due_label = ctk.CTkLabel(row_frame, text=due_text)
        due_label.grid(row=0, column=4, padx=5, pady=5, sticky="ew")  # ✅ sticky="ew"
        
        # ✅ CORRECTION : Actions avec largeur fixe et centrage
        actions_frame = ctk.CTkFrame(row_frame)
        actions_frame.grid(row=0, column=5, padx=5, pady=5, sticky="ew")  # ✅ sticky="ew"
        
        # ✅ Centrer les boutons dans la colonne Actions
        actions_frame.grid_columnconfigure(0, weight=1)
        actions_frame.grid_columnconfigure(1, weight=1)
        actions_frame.grid_columnconfigure(2, weight=1)
        
        ctk.CTkButton(actions_frame, text="✏️", width=25, height=25,
                    command=lambda: self.edit_task(task)).grid(row=0, column=0, padx=1)
        ctk.CTkButton(actions_frame, text="🗑️", width=25, height=25,
                    command=lambda: self.delete_task(task)).grid(row=0, column=1, padx=1)

    def show_table_view(self):
        """Afficher la vue tableau - MODIFIÉ pour un meilleur alignement"""
        # ✅ CORRECTION : En-têtes avec configuration exacte
        headers_frame = ctk.CTkFrame(self.task_content_frame)
        headers_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        
        # ✅ Configuration des colonnes avec proportions précises
        headers_frame.grid_columnconfigure(0, weight=2, minsize=200)  # Titre - plus large
        headers_frame.grid_columnconfigure(1, weight=1, minsize=100)  # Statut
        headers_frame.grid_columnconfigure(2, weight=1, minsize=100)  # Priorité
        headers_frame.grid_columnconfigure(3, weight=1, minsize=120)  # Responsable
        headers_frame.grid_columnconfigure(4, weight=1, minsize=100)  # Échéance
        headers_frame.grid_columnconfigure(5, weight=1, minsize=80)   # Actions
        
        headers = ["Titre", "Statut", "Priorité", "Responsable", "Échéance", "Actions"]
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(headers_frame, text=header, 
                            font=ctk.CTkFont(size=12, weight="bold"))
            # ✅ CORRECTION : Alignement cohérent des en-têtes
            if i == 0:  # Titre à gauche
                label.grid(row=0, column=i, padx=5, pady=10, sticky="w")
            else:  # Autres colonnes centrées
                label.grid(row=0, column=i, padx=5, pady=10, sticky="ew")
            
        # ✅ CORRECTION : Ligne de séparation sous les en-têtes
        separator = ctk.CTkFrame(self.task_content_frame, height=2)
        separator.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 5))
        
        # Zone scrollable pour les lignes de tâches
        table_scroll = ctk.CTkScrollableFrame(self.task_content_frame, 
                                            height=max(500, self.task_area_height - 150))
        table_scroll.grid(row=2, column=0, sticky="ew", padx=10, pady=5)  # ✅ row=2 au lieu de row=1
        table_scroll.grid_columnconfigure(0, weight=1)
            
        # Tâches
        for i, task in enumerate(self.tasks):
            self.create_table_task_row_enhanced(table_scroll, task, i)

    def change_task_view(self, view_mode):
        """Changer le mode de vue des tâches"""
        self.task_view_mode = view_mode
        self.refresh_task_view()
        self.update_status(f"Vue changée : {view_mode}")

    def on_task_frame_configure(self, event):
        """Gérer le redimensionnement du frame de contenu des tâches"""
        # Mettre à jour la scrollregion pour inclure tout le contenu
        if hasattr(self, 'task_canvas'):
            self.task_canvas.configure(scrollregion=self.task_canvas.bbox("all"))

    def on_task_canvas_configure(self, event):
        """Gérer le redimensionnement du canvas des tâches"""
        # Ajuster la largeur du frame interne au canvas
        if hasattr(self, 'task_canvas_window'):
            canvas_width = event.width
            self.task_canvas.itemconfig(self.task_canvas_window, width=canvas_width)

    def add_new_task(self):
        """Ajouter une nouvelle tâche"""
        self.edit_task(None)
        
    def edit_task(self, task):
        """Éditer une tâche (nouvelle ou existante)"""
        # Créer une fenêtre de dialogue
        dialog = ctk.CTkToplevel(self)
        dialog.title("Éditer la tâche" if task else "Nouvelle tâche")
        dialog.geometry("500x600")
        dialog.transient(self)
        dialog.grab_set()
        
        # Centrer la fenêtre
        dialog.geometry("+%d+%d" % (
            self.winfo_rootx() + 100,
            self.winfo_rooty() + 100
        ))
        
        # Frame principal
        main_frame = ctk.CTkScrollableFrame(dialog)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Titre
        ctk.CTkLabel(main_frame, text="Titre:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        title_entry = ctk.CTkEntry(main_frame, width=400)
        title_entry.pack(fill='x', pady=(0, 10))
        if task:
            title_entry.insert(0, task.title)
            
        # Description
        ctk.CTkLabel(main_frame, text="Description:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        desc_textbox = ctk.CTkTextbox(main_frame, height=80, width=400)
        desc_textbox.pack(fill='x', pady=(0, 10))
        if task:
            desc_textbox.insert("1.0", task.description)
            
        # Statut
        ctk.CTkLabel(main_frame, text="Statut:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        status_var = tk.StringVar(value=task.status if task else "À faire")
        status_menu = ctk.CTkOptionMenu(main_frame, values=["À faire", "En cours", "Terminé"], 
                                    variable=status_var)
        status_menu.pack(fill='x', pady=(0, 10))
        
        # Priorité
        ctk.CTkLabel(main_frame, text="Priorité:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        priority_var = tk.StringVar(value=task.priority if task else "Moyenne")
        priority_menu = ctk.CTkOptionMenu(main_frame, values=["Basse", "Moyenne", "Critique"], 
                                        variable=priority_var)
        priority_menu.pack(fill='x', pady=(0, 10))
        
        # Responsable
        ctk.CTkLabel(main_frame, text="Responsable:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        assignee_entry = ctk.CTkEntry(main_frame, width=400, placeholder_text="Nom ou email")
        assignee_entry.pack(fill='x', pady=(0, 10))
        if task:
            assignee_entry.insert(0, task.assignee)
            
        # Échéance
        ctk.CTkLabel(main_frame, text="Échéance:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        due_entry = ctk.CTkEntry(main_frame, width=400, placeholder_text="JJ/MM/AAAA")
        due_entry.pack(fill='x', pady=(0, 10))
        if task:
            due_entry.insert(0, task.due_date)
            
        # Lien avec noeud de l'arbre
        ctk.CTkLabel(main_frame, text="Lien avec noeud de l'arbre:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        
        # Récupérer les noeuds disponibles
        node_options = ["Aucun"]
        if hasattr(self, 'tree_nodes') and self.tree_nodes:
            node_options.extend([node.text for node in self.tree_nodes])
        
        linked_node_var = tk.StringVar(value=task.linked_node.text if task and task.linked_node else "Aucun")
        node_menu = ctk.CTkOptionMenu(main_frame, values=node_options, variable=linked_node_var)
        node_menu.pack(fill='x', pady=(0, 20))
        
        # Variable pour le résultat
        result = {"saved": False}
        
        def save_task():
            # Validation
            if not title_entry.get().strip():
                messagebox.showerror("Erreur", "Le titre est obligatoire!")
                return
                
            # Trouver le noeud lié
            linked_node = None
            if linked_node_var.get() != "Aucun" and hasattr(self, 'tree_nodes'):
                for node in self.tree_nodes:
                    if node.text == linked_node_var.get():
                        linked_node = node
                        break
            
            if task:
                # Modifier la tâche existante
                task.title = title_entry.get().strip()
                task.description = desc_textbox.get("1.0", "end-1c")
                task.status = status_var.get()
                task.priority = priority_var.get()
                task.assignee = assignee_entry.get().strip()
                task.due_date = due_entry.get().strip()
                task.linked_node = linked_node
            else:
                # Créer une nouvelle tâche
                new_task = Task(
                    title=title_entry.get().strip(),
                    description=desc_textbox.get("1.0", "end-1c"),
                    status=status_var.get(),
                    priority=priority_var.get(),
                    assignee=assignee_entry.get().strip(),
                    due_date=due_entry.get().strip(),
                    linked_node=linked_node
                )
                self.tasks.append(new_task)
            
            result["saved"] = True
            dialog.destroy()
            
        def cancel():
            dialog.destroy()
            
        # Boutons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill='x', pady=10)
        
        ctk.CTkButton(button_frame, text="Annuler", command=cancel).pack(side='right', padx=(5, 0))
        ctk.CTkButton(button_frame, text="Sauvegarder", command=save_task).pack(side='right')
        
        # Attendre la fermeture
        dialog.wait_window()
        
        # Rafraîchir l'affichage si sauvegardé
        if result["saved"]:
            self.refresh_task_view()

    def delete_task(self, task):
        """Supprimer une tâche"""
        if messagebox.askyesno("Confirmation", f"Supprimer la tâche '{task.title}' ?"):
            self.tasks.remove(task)
            self.refresh_task_view()
            
    def change_task_status(self, task, new_status):
        """Changer le statut d'une tâche"""
        task.status = new_status
        self.refresh_task_view()
        
    def sync_tasks_with_tree(self):
        """Synchroniser les tâches avec les noeuds de l'arbre"""
        # Vérification plus robuste
        if not hasattr(self, 'tree_nodes'):
            messagebox.showwarning("Avertissement", "Le module d'arbre n'a pas été initialisé!\nVeuillez d'abord aller dans 'Diagramme en Arbre'.")
            return
            
        if not self.tree_nodes:
            messagebox.showwarning("Avertissement", "L'arbre est vide!\nVeuillez d'abord créer des nœuds dans le diagramme.")
            return
        
        # Vérifier que les tâches existent
        if not hasattr(self, 'tasks'):
            self.tasks = []
        
        # Compter les tâches créées
        created_count = 0
        
        for node in self.tree_nodes:
            # Vérifier si une tâche existe déjà pour ce noeud
            existing_task = None
            for task in self.tasks:
                if hasattr(task, 'linked_node') and task.linked_node == node:
                    existing_task = task
                    break
                    
            if not existing_task:
                # Créer une nouvelle tâche pour ce noeud
                new_task = Task(
                    title=f"Tâche: {node.text}",
                    description=f"Tâche automatiquement créée pour le noeud '{node.text}'",
                    linked_node=node
                )
                self.tasks.append(new_task)
                created_count += 1
                
        if created_count > 0:
            messagebox.showinfo("Synchronisation", f"{created_count} nouvelle(s) tâche(s) créée(s)!")
            
            # Rafraîchir seulement la vue des tâches, PAS l'arbre
            if hasattr(self, 'refresh_task_view'):
                self.refresh_task_view()
            
            # Enregistrement automatique dans le journal
            if hasattr(self, 'add_automatic_log_entry'):
                self.add_automatic_log_entry(
                    title=f"Synchronisation tâches-arbre",
                    description=f"{created_count} nouvelles tâches créées depuis l'arbre\nNœuds traités: {len(self.tree_nodes)}",
                    category="Task"
                )
            
            self.update_status(f"✅ {created_count} tâches synchronisées")
        else:
            messagebox.showinfo("Synchronisation", "Toutes les tâches sont déjà synchronisées!")
            self.update_status("Aucune synchronisation nécessaire")

    def update_task_stats(self):
        """Mettre à jour les statistiques des tâches"""
        total = len(self.tasks)
        todo = len([t for t in self.tasks if t.status == "À faire"])
        in_progress = len([t for t in self.tasks if t.status == "En cours"])
        done = len([t for t in self.tasks if t.status == "Terminé"])
        critical = len([t for t in self.tasks if t.priority == "Critique"])
        
        stats_text = f"Total: {total} | À faire: {todo} | En cours: {in_progress} | Terminé: {done}"
        if critical > 0:
            stats_text += f" | 🔥 Critique: {critical}"
            
        if hasattr(self, 'task_stats_label'):
            self.task_stats_label.configure(text=stats_text)                     
    
    def add_new_task(self):
        """Ajouter une nouvelle tâche"""
        self.edit_task(None)
        
    def edit_task(self, task):
        """Éditer une tâche (nouvelle ou existante)"""
        # Créer une fenêtre de dialogue
        dialog = ctk.CTkToplevel(self)
        dialog.title("Éditer la tâche" if task else "Nouvelle tâche")
        dialog.geometry("500x600")
        dialog.transient(self)
        dialog.grab_set()
        
        # Centrer la fenêtre
        dialog.geometry("+%d+%d" % (
            self.winfo_rootx() + 100,
            self.winfo_rooty() + 100
        ))
        
        # Frame principal
        main_frame = ctk.CTkScrollableFrame(dialog)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Titre
        ctk.CTkLabel(main_frame, text="Titre:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        title_entry = ctk.CTkEntry(main_frame, width=400)
        title_entry.pack(fill='x', pady=(0, 10))
        if task:
            title_entry.insert(0, task.title)
            
        # Description
        ctk.CTkLabel(main_frame, text="Description:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        desc_textbox = ctk.CTkTextbox(main_frame, height=80, width=400)
        desc_textbox.pack(fill='x', pady=(0, 10))
        if task:
            desc_textbox.insert("1.0", task.description)
            
        # Statut
        ctk.CTkLabel(main_frame, text="Statut:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        status_var = tk.StringVar(value=task.status if task else "À faire")
        status_menu = ctk.CTkOptionMenu(main_frame, values=["À faire", "En cours", "Terminé"], 
                                       variable=status_var)
        status_menu.pack(fill='x', pady=(0, 10))
        
        # Priorité
        ctk.CTkLabel(main_frame, text="Priorité:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        priority_var = tk.StringVar(value=task.priority if task else "Moyenne")
        priority_menu = ctk.CTkOptionMenu(main_frame, values=["Basse", "Moyenne", "Critique"], 
                                         variable=priority_var)
        priority_menu.pack(fill='x', pady=(0, 10))
        
        # Responsable
        ctk.CTkLabel(main_frame, text="Responsable:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        assignee_entry = ctk.CTkEntry(main_frame, width=400, placeholder_text="Nom ou email")
        assignee_entry.pack(fill='x', pady=(0, 10))
        if task:
            assignee_entry.insert(0, task.assignee)
            
        # Échéance
        ctk.CTkLabel(main_frame, text="Échéance:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        due_entry = ctk.CTkEntry(main_frame, width=400, placeholder_text="JJ/MM/AAAA")
        due_entry.pack(fill='x', pady=(0, 10))
        if task:
            due_entry.insert(0, task.due_date)
            
        # Lien avec noeud de l'arbre
        ctk.CTkLabel(main_frame, text="Lien avec noeud de l'arbre:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        
        # Récupérer les noeuds disponibles
        node_options = ["Aucun"]
        if hasattr(self, 'tree_nodes') and self.tree_nodes:
            node_options.extend([node.text for node in self.tree_nodes])
        
        linked_node_var = tk.StringVar(value=task.linked_node.text if task and task.linked_node else "Aucun")
        node_menu = ctk.CTkOptionMenu(main_frame, values=node_options, variable=linked_node_var)
        node_menu.pack(fill='x', pady=(0, 20))
        
        # Variable pour le résultat
        result = {"saved": False}
        
        def save_task():
            # Validation
            if not title_entry.get().strip():
                messagebox.showerror("Erreur", "Le titre est obligatoire!")
                return
                
            # Trouver le noeud lié
            linked_node = None
            if linked_node_var.get() != "Aucun" and hasattr(self, 'tree_nodes'):
                for node in self.tree_nodes:
                    if node.text == linked_node_var.get():
                        linked_node = node
                        break
            
            if task:
                # Modifier la tâche existante
                task.title = title_entry.get().strip()
                task.description = desc_textbox.get("1.0", "end-1c")
                task.status = status_var.get()
                task.priority = priority_var.get()
                task.assignee = assignee_entry.get().strip()
                task.due_date = due_entry.get().strip()
                task.linked_node = linked_node
            else:
                # Créer une nouvelle tâche
                new_task = Task(
                    title=title_entry.get().strip(),
                    description=desc_textbox.get("1.0", "end-1c"),
                    status=status_var.get(),
                    priority=priority_var.get(),
                    assignee=assignee_entry.get().strip(),
                    due_date=due_entry.get().strip(),
                    linked_node=linked_node
                )
                self.tasks.append(new_task)
            
            result["saved"] = True
            dialog.destroy()
            
        def cancel():
            dialog.destroy()
            
        # Boutons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill='x', pady=10)
        
        ctk.CTkButton(button_frame, text="Annuler", command=cancel).pack(side='right', padx=(5, 0))
        ctk.CTkButton(button_frame, text="Sauvegarder", command=save_task).pack(side='right')
        
        # Attendre la fermeture
        dialog.wait_window()
        
        # Rafraîchir l'affichage si sauvegardé
        if result["saved"]:
            self.refresh_task_view()
            
    def delete_task(self, task):
        """Supprimer une tâche"""
        if messagebox.askyesno("Confirmation", f"Supprimer la tâche '{task.title}' ?"):
            self.tasks.remove(task)
            self.refresh_task_view()
            
    def change_task_status(self, task, new_status):
        """Changer le statut d'une tâche"""
        task.status = new_status
        self.refresh_task_view()
        
    def sync_tasks_with_tree(self):
        """Synchroniser les tâches avec les noeuds de l'arbre"""
        # Vérification plus robuste
        if not hasattr(self, 'tree_nodes'):
            messagebox.showwarning("Avertissement", "Le module d'arbre n'a pas été initialisé!\nVeuillez d'abord aller dans 'Diagramme en Arbre'.")
            return
            
        if not self.tree_nodes:
            messagebox.showwarning("Avertissement", "L'arbre est vide!\nVeuillez d'abord créer des nœuds dans le diagramme.")
            return
        
        # Vérifier que les tâches existent
        if not hasattr(self, 'tasks'):
            self.tasks = []
        
        # Compter les tâches créées
        created_count = 0
        
        for node in self.tree_nodes:
            # Vérifier si une tâche existe déjà pour ce noeud
            existing_task = None
            for task in self.tasks:
                if hasattr(task, 'linked_node') and task.linked_node == node:
                    existing_task = task
                    break
                    
            if not existing_task:
                # Créer une nouvelle tâche pour ce noeud
                new_task = Task(
                    title=f"Tâche: {node.text}",
                    description=f"Tâche automatiquement créée pour le noeud '{node.text}'",
                    linked_node=node
                )
                self.tasks.append(new_task)
                created_count += 1
                
        if created_count > 0:
            messagebox.showinfo("Synchronisation", f"{created_count} nouvelle(s) tâche(s) créée(s)!")
            
            # Rafraîchir seulement la vue des tâches, PAS l'arbre
            if hasattr(self, 'refresh_task_view'):
                self.refresh_task_view()
            
            # Enregistrement automatique dans le journal
            if hasattr(self, 'add_automatic_log_entry'):
                self.add_automatic_log_entry(
                    title=f"Synchronisation tâches-arbre",
                    description=f"{created_count} nouvelles tâches créées depuis l'arbre\nNœuds traités: {len(self.tree_nodes)}",
                    category="Task"
                )
            
            self.update_status(f"✅ {created_count} tâches synchronisées")
        else:
            messagebox.showinfo("Synchronisation", "Toutes les tâches sont déjà synchronisées!")
            self.update_status("Aucune synchronisation nécessaire")
    
    def update_task_stats(self):
        """Mettre à jour les statistiques des tâches"""
        total = len(self.tasks)
        todo = len([t for t in self.tasks if t.status == "À faire"])
        in_progress = len([t for t in self.tasks if t.status == "En cours"])
        done = len([t for t in self.tasks if t.status == "Terminé"])
        critical = len([t for t in self.tasks if t.priority == "Critique"])
        
        stats_text = f"Total: {total} | À faire: {todo} | En cours: {in_progress} | Terminé: {done}"
        if critical > 0:
            stats_text += f" | 🔥 Critique: {critical}"
            
        if hasattr(self, 'task_stats_label'):
            self.task_stats_label.configure(text=stats_text)
        
    def example_action(self):
        """Action d'exemple"""
        messagebox.showinfo("Information", "Action exécutée avec succès !")
        self.update_status("Action exécutée")
        
    def change_appearance_mode_event(self, new_appearance_mode: str):
        """Changer le thème de l'application"""
        ctk.set_appearance_mode(new_appearance_mode.lower())
        self.update_status(f"Thème changé : {new_appearance_mode}")
        
    def update_status(self, message: str):
        """Mettre à jour la barre de statut"""
        if hasattr(self, 'status_label'):
            self.status_label.configure(text=message)
        
    def on_closing(self):
        """Gestionnaire de fermeture de l'application"""
        if messagebox.askokcancel("Quitter", "Voulez-vous vraiment quitter l'application ?"):
            self.destroy()
            
    def create_sample_tasks(self):
        """Créer quelques tâches d'exemple pour les tests"""
        sample_tasks = [
            Task(
                title="Analyser les besoins du projet",
                description="Recueillir et analyser les exigences fonctionnelles",
                status="En cours",
                priority="Critique",
                assignee="Chef de projet",
                due_date="15/12/2024"
            ),
            Task(
                title="Concevoir l'architecture",
                description="Définir l'architecture technique du système",
                status="À faire",
                priority="Moyenne",
                assignee="Architecte",
                due_date="20/12/2024"
            ),
            Task(
                title="Développer le module principal",
                description="Implémenter les fonctionnalités de base",
                status="À faire",
                priority="Critique",
                assignee="Développeur senior",
                due_date="30/12/2024"
            ),
            Task(
                title="Tests unitaires",
                description="Créer et exécuter les tests unitaires",
                status="À faire",
                priority="Moyenne",
                assignee="Testeur",
                due_date="05/01/2025"
            ),
            Task(
                title="Documentation utilisateur",
                description="Rédiger la documentation pour les utilisateurs finaux",
                status="Terminé",
                priority="Basse",
                assignee="Rédacteur technique",
                due_date="10/12/2024"
            )
        ]
        
        self.tasks.extend(sample_tasks)
        self.refresh_task_view()
        self.update_status(f"{len(sample_tasks)} tâches d'exemple créées")
        
    def show_decision_log(self):
        """Afficher le module journal de bord / carnet de décisions"""
        self.clear_content()
        self.main_title.configure(text="💬 Journal de Bord / Carnet de Décisions")
        
        # ✅ CORRECTION : Configuration de l'expansion complète
        self.content_frame.grid_rowconfigure(1, weight=1)  # Ligne principale du journal
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        # Initialiser les variables du journal si nécessaire
        if not hasattr(self, 'log_entries'):
            self.log_entries = []
        if not hasattr(self, 'log_filter_author'):
            self.log_filter_author = "Tous"
        if not hasattr(self, 'log_filter_category'):
            self.log_filter_category = "Toutes"
        if not hasattr(self, 'log_filter_date_from'):
            self.log_filter_date_from = ""
        if not hasattr(self, 'log_filter_date_to'):
            self.log_filter_date_to = ""
        
        # ✅ NOUVEAU : Taille fixe en mode Large
        self.log_area_width = 1600   # Taille Large fixe
        self.log_area_height = 800   # Taille Large fixe
            
        # Toolbar avec contrôles
        toolbar_frame = ctk.CTkFrame(self.content_frame)
        toolbar_frame.grid(row=0, column=0, padx=5, pady=2, sticky="ew")
        toolbar_frame.grid_columnconfigure(1, weight=1)
        
        # Section boutons d'action
        actions_frame = ctk.CTkFrame(toolbar_frame)
        actions_frame.grid(row=0, column=0, padx=5, pady=5)
        
        ctk.CTkButton(actions_frame, text="➕ Nouvelle Entrée", 
                    command=self.add_manual_log_entry).grid(row=0, column=0, padx=5, pady=5)
        ctk.CTkButton(actions_frame, text="📥 Exporter Journal", 
                    command=self.export_decision_log).grid(row=0, column=1, padx=5, pady=5)
        ctk.CTkButton(actions_frame, text="🗑️ Vider Journal", 
                    command=self.clear_decision_log).grid(row=0, column=2, padx=5, pady=5)
        
        # Section filtres
        filters_frame = ctk.CTkFrame(toolbar_frame)
        filters_frame.grid(row=0, column=1, padx=20, pady=5, sticky="ew")
        filters_frame.grid_columnconfigure(4, weight=1)
        
        ctk.CTkLabel(filters_frame, text="Filtres:").grid(row=0, column=0, padx=5, pady=5)
        
        # Filtre par auteur
        ctk.CTkLabel(filters_frame, text="Auteur:").grid(row=0, column=1, padx=(10, 2), pady=5)
        authors = ["Tous"] + list(set([entry.author for entry in self.log_entries if entry.author]))
        self.log_author_filter = ctk.CTkOptionMenu(filters_frame, values=authors if authors else ["Tous"],
                                                command=self.apply_log_filters, width=100)
        self.log_author_filter.grid(row=0, column=2, padx=2, pady=5)
        
        # Filtre par catégorie
        ctk.CTkLabel(filters_frame, text="Catégorie:").grid(row=0, column=3, padx=(10, 2), pady=5)
        categories = ["Toutes", "Decision", "Technical", "Meeting", "Node", "Task", "Status"]
        self.log_category_filter = ctk.CTkOptionMenu(filters_frame, values=categories,
                                                    command=self.apply_log_filters, width=100)
        self.log_category_filter.grid(row=0, column=4, padx=2, pady=5)
        
        # Filtre par date
        date_frame = ctk.CTkFrame(filters_frame)
        date_frame.grid(row=0, column=5, padx=10, pady=5)
        
        ctk.CTkLabel(date_frame, text="Du:").pack(side="left", padx=2)
        self.log_date_from = ctk.CTkEntry(date_frame, width=80, placeholder_text="JJ/MM/AAAA")
        self.log_date_from.pack(side="left", padx=2)
        self.log_date_from.bind('<KeyRelease>', lambda e: self.apply_log_filters())
        
        ctk.CTkLabel(date_frame, text="Au:").pack(side="left", padx=(10, 2))
        self.log_date_to = ctk.CTkEntry(date_frame, width=80, placeholder_text="JJ/MM/AAAA")
        self.log_date_to.pack(side="left", padx=2)
        self.log_date_to.bind('<KeyRelease>', lambda e: self.apply_log_filters())
        
        ctk.CTkButton(date_frame, text="🔄", width=30, 
                    command=self.reset_log_filters).pack(side="left", padx=5)
        
        # Statistiques
        stats_frame = ctk.CTkFrame(toolbar_frame)
        stats_frame.grid(row=0, column=2, padx=10, pady=5)
        
        self.log_stats_label = ctk.CTkLabel(stats_frame, text="Chargement...")
        self.log_stats_label.pack(padx=10, pady=5)
        
        # ✅ Frame principal avec zone de journal en taille Large fixe
        main_log_frame = ctk.CTkFrame(self.content_frame)
        main_log_frame.grid(row=1, column=0, padx=5, pady=2, sticky="nsew")
        main_log_frame.grid_columnconfigure(0, weight=1)
        main_log_frame.grid_rowconfigure(0, weight=1)
        
        # ✅ Canvas pour la zone de journal avec taille Large fixe
        log_canvas_frame = ctk.CTkFrame(main_log_frame)
        log_canvas_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        log_canvas_frame.grid_columnconfigure(0, weight=1)
        log_canvas_frame.grid_rowconfigure(0, weight=1)
        
        # ✅ Canvas principal du journal avec taille Large (1600x800)
        self.log_canvas = tk.Canvas(log_canvas_frame, bg='#f0f0f0', 
                                width=self.log_area_width, 
                                height=self.log_area_height,
                                highlightthickness=0)  # ✅ Retirer la bordure
        self.log_canvas.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbars pour la zone de journal
        log_v_scrollbar = ttk.Scrollbar(log_canvas_frame, orient="vertical", command=self.log_canvas.yview)
        log_h_scrollbar = ttk.Scrollbar(log_canvas_frame, orient="horizontal", command=self.log_canvas.xview)
        self.log_canvas.configure(yscrollcommand=log_v_scrollbar.set, xscrollcommand=log_h_scrollbar.set)
        
        log_v_scrollbar.grid(row=0, column=1, sticky="ns")
        log_h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # ✅ Configuration de la zone de scroll - taille exacte
        self.log_canvas.configure(scrollregion=(0, 0, self.log_area_width, self.log_area_height))
        
        # ✅ Frame pour le contenu du journal à l'intérieur du canvas
        self.log_content_frame = ctk.CTkFrame(self.log_canvas)
        self.log_canvas_window = self.log_canvas.create_window(0, 0, anchor="nw", window=self.log_content_frame)
        self.log_content_frame.grid_columnconfigure(0, weight=1)
        
        # ✅ Configuration du contenu pour occuper exactement la taille du canvas
        self.log_content_frame.configure(width=self.log_area_width, height=self.log_area_height)
        
        # Bind pour ajuster la taille du frame interne
        self.log_content_frame.bind('<Configure>', self.on_log_frame_configure)
        self.log_canvas.bind('<Configure>', self.on_log_canvas_configure)
        
        # Afficher les entrées
        self.refresh_log_view()
        
        self.update_status("Module journal de bord affiché en taille Large (1600x800)")

    def on_log_frame_configure(self, event):
        """Gérer le redimensionnement du frame de contenu du journal"""
        # ✅ CORRECTION : Mettre à jour la scrollregion pour la taille exacte du contenu
        canvas_width = self.log_canvas.winfo_width()
        canvas_height = self.log_canvas.winfo_height()
        
        # Ajuster la taille de la scrollregion au contenu réel
        bbox = self.log_canvas.bbox("all")
        if bbox:
            self.log_canvas.configure(scrollregion=bbox)
        else:
            # Si pas de contenu, utiliser la taille exacte du canvas
            self.log_canvas.configure(scrollregion=(0, 0, canvas_width, canvas_height))

    def on_log_canvas_configure(self, event):
        """Gérer le redimensionnement du canvas du journal"""
        # ✅ CORRECTION : Ajuster la largeur du frame interne exactement au canvas
        canvas_width = event.width
        canvas_height = event.height
        
        # Configurer la fenêtre du canvas pour occuper exactement l'espace
        self.log_canvas.itemconfig(self.log_canvas_window, width=canvas_width, height=canvas_height)
        
        # Mettre à jour la taille du frame de contenu
        self.log_content_frame.configure(width=canvas_width, height=canvas_height)

    def refresh_log_view(self):
        """Rafraîchir l'affichage du journal - MODIFIÉ pour utiliser le canvas"""
        print(f"🔄 Rafraîchissement de l'affichage du journal...")
        print(f"   - Nombre d'entrées: {len(self.log_entries)}")
        print(f"   - Taille zone: {self.log_area_width}x{self.log_area_height}")
        
        # Nettoyer le contenu actuel
        for widget in self.log_content_frame.winfo_children():
            widget.destroy()
            
        # Filtrer les entrées
        filtered_entries = self.get_filtered_log_entries()
        
        # Trier par date (plus récent en premier)
        filtered_entries.sort(key=lambda x: x.timestamp, reverse=True)
        
        if not filtered_entries:
            no_entries_label = ctk.CTkLabel(self.log_content_frame, 
                                        text="Aucune entrée trouvée avec les filtres actuels",
                                        font=ctk.CTkFont(size=14))
            no_entries_label.pack(pady=50)
        else:
            # ✅ Utiliser pack au lieu de grid pour une meilleure gestion de l'espace
            for entry in filtered_entries:
                self.create_log_entry_widget_enhanced(entry)
                
        self.update_log_stats(filtered_entries)
        print(f"✅ Rafraîchissement terminé")

    def create_log_entry_widget_enhanced(self, entry):
        """Créer le widget pour une entrée de journal - Version améliorée pour canvas"""
        # ✅ Frame principal pour l'entrée avec largeur adaptée
        entry_frame = ctk.CTkFrame(self.log_content_frame)
        entry_frame.pack(fill="x", padx=10, pady=5)
        
        # Calculer la largeur disponible
        available_width = max(400, self.log_area_width - 40)  # 40px pour les marges
        
        # Header avec info principale
        header_frame = ctk.CTkFrame(entry_frame)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        # Icône selon la catégorie
        category_icons = {
            "Decision": "📋", "Technical": "🔧", "Meeting": "👥",
            "Node": "🌳", "Task": "✅", "Status": "🔄", "Auto": "🤖"
        }
        icon = category_icons.get(entry.category, "📝")
        
        # Type d'entrée (auto/manual)
        type_color = "#4CAF50" if entry.entry_type == "auto" else "#2196F3"
        type_text = "AUTO" if entry.entry_type == "auto" else "MANUEL"
        
        # Date et heure
        date_str = entry.timestamp.strftime("%d/%m/%Y à %H:%M")
        
        # Ligne 1 : Icône, titre, type, date
        title_label = ctk.CTkLabel(header_frame, text=f"{icon} {entry.title}", 
                                font=ctk.CTkFont(size=14, weight="bold"),
                                wraplength=available_width - 200)  # Laisser de la place pour les infos
        title_label.pack(side="left", anchor="w", fill="x", expand=True)
        
        info_frame = ctk.CTkFrame(header_frame)
        info_frame.pack(side="right")
        
        type_label = ctk.CTkLabel(info_frame, text=type_text, 
                                text_color=type_color, font=ctk.CTkFont(size=10, weight="bold"))
        type_label.pack(side="right", padx=5)
        
        date_label = ctk.CTkLabel(info_frame, text=date_str, 
                                font=ctk.CTkFont(size=10))
        date_label.pack(side="right", padx=5)
        
        # Ligne 2 : Auteur et catégorie
        meta_frame = ctk.CTkFrame(entry_frame)
        meta_frame.pack(fill="x", padx=10, pady=2)
        
        if entry.author:
            author_label = ctk.CTkLabel(meta_frame, text=f"👤 {entry.author}", 
                                    font=ctk.CTkFont(size=10))
            author_label.pack(side="left", padx=5)
            
        category_label = ctk.CTkLabel(meta_frame, text=f"🏷️ {entry.category}", 
                                    font=ctk.CTkFont(size=10))
        category_label.pack(side="left", padx=5)
        
        # Description (adaptée à la largeur)
        if entry.description:
            desc_frame = ctk.CTkFrame(entry_frame)
            desc_frame.pack(fill="x", padx=10, pady=(2, 5))
            
            # ✅ Hauteur adaptée au contenu mais limitée
            desc_height = min(150, max(80, len(entry.description) // 10))  # Hauteur dynamique
            
            desc_text = ctk.CTkTextbox(desc_frame, height=desc_height, width=available_width)
            desc_text.pack(fill="x", padx=5, pady=5)
            desc_text.insert("1.0", entry.description)
            desc_text.configure(state="disabled")
            
            # Bouton pour voir en détail si l'entrée est longue
            if len(entry.description) > 500:
                detail_btn = ctk.CTkButton(desc_frame, text="🔍 Voir en détail", height=25,
                                    command=lambda: self.show_full_log_entry(entry))
                detail_btn.pack(pady=2)
                    
        # Boutons d'action pour les entrées manuelles
        if entry.entry_type == "manual":
            actions_frame = ctk.CTkFrame(entry_frame)
            actions_frame.pack(fill="x", padx=10, pady=(0, 10))
            
            ctk.CTkButton(actions_frame, text="✏️ Modifier", width=80, height=25,
                        command=lambda: self.edit_log_entry(entry)).pack(side="right", padx=2)
            ctk.CTkButton(actions_frame, text="🗑️ Supprimer", width=80, height=25,
                        command=lambda: self.delete_log_entry(entry)).pack(side="right", padx=2)
            ctk.CTkButton(actions_frame, text="📋 Copier", width=80, height=25,
                        command=lambda: self.copy_log_entry_to_clipboard(entry)).pack(side="left", padx=2)

    def copy_log_entry_to_clipboard(self, entry):
        """Copier le contenu d'une entrée dans le presse-papiers"""
        try:
            content = f"""--- {entry.title} ---
    Date: {entry.timestamp.strftime('%d/%m/%Y à %H:%M:%S')}
    Auteur: {entry.author}
    Catégorie: {entry.category}
    Type: {'Automatique' if entry.entry_type == 'auto' else 'Manuelle'}

    {entry.description}
    """
            # Copier dans le presse-papiers (compatible multi-plateforme)
            import tkinter as tk
            self.clipboard_clear()
            self.clipboard_append(content)
            self.update()  # Maintenant il y reste après que la fenêtre est fermée
            
            # Message de confirmation temporaire
            self.update_status("Entrée copiée dans le presse-papiers")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de copier dans le presse-papiers :\n{str(e)}")
        
    def add_manual_log_entry(self):
        """Ajouter une entrée manuelle au journal"""
        # Créer une fenêtre de dialogue
        dialog = ctk.CTkToplevel(self)
        dialog.title("Nouvelle Entrée Journal")
        dialog.geometry("600x500")
        dialog.transient(self)
        dialog.grab_set()
        
        # Centrer la fenêtre
        dialog.geometry("+%d+%d" % (
            self.winfo_rootx() + 100,
            self.winfo_rooty() + 100
        ))
        
        # Frame principal
        main_frame = ctk.CTkScrollableFrame(dialog)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Titre
        ctk.CTkLabel(main_frame, text="Titre:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        title_entry = ctk.CTkEntry(main_frame, width=500, placeholder_text="Ex: Décision architecture microservices")
        title_entry.pack(fill='x', pady=(0, 10))
        
        # Catégorie
        ctk.CTkLabel(main_frame, text="Catégorie:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        category_var = tk.StringVar(value="Decision")
        category_menu = ctk.CTkOptionMenu(main_frame, values=["Decision", "Technical", "Meeting", "Other"], 
                                         variable=category_var)
        category_menu.pack(fill='x', pady=(0, 10))
        
        # Auteur
        ctk.CTkLabel(main_frame, text="Auteur:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        author_entry = ctk.CTkEntry(main_frame, width=500, placeholder_text="Votre nom ou email")
        author_entry.pack(fill='x', pady=(0, 10))
        
        # Description
        ctk.CTkLabel(main_frame, text="Description / Détails:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        desc_textbox = ctk.CTkTextbox(main_frame, height=200, width=500)
        desc_textbox.pack(fill='both', expand=True, pady=(0, 20))
        desc_textbox.insert("1.0", "Contexte:\n\n\nDécision prise:\n\n\nJustification:\n\n\nImpact:\n\n")
        
        # Variable pour le résultat
        result = {"saved": False}
        
        def save_entry():
            if not title_entry.get().strip():
                messagebox.showerror("Erreur", "Le titre est obligatoire!")
                return
                
            new_entry = LogEntry(
                entry_type="manual",
                title=title_entry.get().strip(),
                description=desc_textbox.get("1.0", "end-1c"),
                author=author_entry.get().strip(),
                category=category_var.get()
            )
            
            self.log_entries.append(new_entry)
            result["saved"] = True
            dialog.destroy()
            
        def cancel():
            dialog.destroy()
            
        # Boutons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill='x', pady=10)
        
        ctk.CTkButton(button_frame, text="Annuler", command=cancel).pack(side='right', padx=(5, 0))
        ctk.CTkButton(button_frame, text="Sauvegarder", command=save_entry).pack(side='right')
        
        # Focus sur le titre
        title_entry.focus()
        
        # Attendre la fermeture
        dialog.wait_window()
        
        # Rafraîchir l'affichage si sauvegardé
        if result["saved"]:
            self.refresh_log_view()
            self.update_status("Nouvelle entrée ajoutée au journal")
            
    def add_automatic_log_entry(self, title, description, category="Auto"):
        """Ajouter une entrée automatique au journal"""
        entry = LogEntry(
            entry_type="auto",
            title=title,
            description=description,
            author="Système",
            category=category
        )
        
        if not hasattr(self, 'log_entries'):
            self.log_entries = []
            
        self.log_entries.append(entry)
        
        # Limiter le nombre d'entrées automatiques à 1000 pour éviter l'encombrement
        auto_entries = [e for e in self.log_entries if e.entry_type == "auto"]
        if len(auto_entries) > 1000:
            # Supprimer les plus anciennes entrées automatiques
            auto_entries.sort(key=lambda x: x.timestamp)
            for old_entry in auto_entries[:100]:  # Supprimer les 100 plus anciennes
                self.log_entries.remove(old_entry)
                
    def refresh_log_view(self):
        """Rafraîchir l'affichage du journal"""
        # Nettoyer le contenu actuel
        for widget in self.log_content_frame.winfo_children():
            widget.destroy()
            
        # Filtrer les entrées
        filtered_entries = self.get_filtered_log_entries()
        
        # Trier par date (plus récent en premier)
        filtered_entries.sort(key=lambda x: x.timestamp, reverse=True)
        
        if not filtered_entries:
            no_entries_label = ctk.CTkLabel(self.log_content_frame, 
                                          text="Aucune entrée trouvée avec les filtres actuels",
                                          font=ctk.CTkFont(size=14))
            no_entries_label.pack(pady=50)
        else:
            for entry in filtered_entries:
                self.create_log_entry_widget(entry)
                
        self.update_log_stats(filtered_entries)
        
    def get_filtered_log_entries(self):
        """Obtenir les entrées filtrées selon les critères"""
        filtered = self.log_entries.copy()
        
        # Filtre par auteur
        if hasattr(self, 'log_author_filter') and self.log_author_filter.get() != "Tous":
            filtered = [e for e in filtered if e.author == self.log_author_filter.get()]
            
        # Filtre par catégorie
        if hasattr(self, 'log_category_filter') and self.log_category_filter.get() != "Toutes":
            filtered = [e for e in filtered if e.category == self.log_category_filter.get()]
            
        # Filtre par date
        if hasattr(self, 'log_date_from') and self.log_date_from.get():
            try:
                date_from = datetime.datetime.strptime(self.log_date_from.get(), "%d/%m/%Y")
                filtered = [e for e in filtered if e.timestamp.date() >= date_from.date()]
            except ValueError:
                pass  # Ignorer les dates invalides
                
        if hasattr(self, 'log_date_to') and self.log_date_to.get():
            try:
                date_to = datetime.datetime.strptime(self.log_date_to.get(), "%d/%m/%Y")
                filtered = [e for e in filtered if e.timestamp.date() <= date_to.date()]
            except ValueError:
                pass  # Ignorer les dates invalides
                
        return filtered
        
    def create_log_entry_widget(self, entry):
        """Créer le widget pour une entrée de journal"""
        # Frame principal pour l'entrée
        entry_frame = ctk.CTkFrame(self.log_content_frame)
        entry_frame.pack(fill="x", padx=10, pady=5)
        
        # Header avec info principale
        header_frame = ctk.CTkFrame(entry_frame)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        # Icône selon la catégorie
        category_icons = {
            "Decision": "📋", "Technical": "🔧", "Meeting": "👥",
            "Node": "🌳", "Task": "✅", "Status": "🔄", "Auto": "🤖"
        }
        icon = category_icons.get(entry.category, "📝")
        
        # Type d'entrée (auto/manual)
        type_color = "#4CAF50" if entry.entry_type == "auto" else "#2196F3"
        type_text = "AUTO" if entry.entry_type == "auto" else "MANUEL"
        
        # Date et heure
        date_str = entry.timestamp.strftime("%d/%m/%Y à %H:%M")
        
        # Ligne 1 : Icône, titre, type, date
        title_label = ctk.CTkLabel(header_frame, text=f"{icon} {entry.title}", 
                                  font=ctk.CTkFont(size=14, weight="bold"))
        title_label.pack(side="left", anchor="w")
        
        info_frame = ctk.CTkFrame(header_frame)
        info_frame.pack(side="right")
        
        type_label = ctk.CTkLabel(info_frame, text=type_text, 
                                 text_color=type_color, font=ctk.CTkFont(size=10, weight="bold"))
        type_label.pack(side="right", padx=5)
        
        date_label = ctk.CTkLabel(info_frame, text=date_str, 
                                 font=ctk.CTkFont(size=10))
        date_label.pack(side="right", padx=5)
        
        # Ligne 2 : Auteur et catégorie
        meta_frame = ctk.CTkFrame(entry_frame)
        meta_frame.pack(fill="x", padx=10, pady=2)
        
        if entry.author:
            author_label = ctk.CTkLabel(meta_frame, text=f"👤 {entry.author}", 
                                       font=ctk.CTkFont(size=10))
            author_label.pack(side="left", padx=5)
            
        category_label = ctk.CTkLabel(meta_frame, text=f"🏷️ {entry.category}", 
                                     font=ctk.CTkFont(size=10))
        category_label.pack(side="left", padx=5)
        
        # Description (pliable)
        if entry.description:
            desc_frame = ctk.CTkFrame(entry_frame)
            desc_frame.pack(fill="x", padx=10, pady=(2, 5))
            
            # Limiter l'affichage initial
            short_desc = entry.description[:200] + "..." if len(entry.description) > 200 else entry.description
            
            desc_text = ctk.CTkTextbox(desc_frame, height=60)
            desc_text.pack(fill="x", padx=5, pady=5)
            desc_text.insert("1.0", short_desc)
            desc_text.configure(state="disabled")
            
            # Bouton pour voir plus si nécessaire
            if len(entry.description) > 200:
                def show_full_description():
                    self.show_full_log_entry(entry)
                    
                more_btn = ctk.CTkButton(desc_frame, text="Voir plus...", height=20,
                                       command=show_full_description)
                more_btn.pack(pady=2)
                
        # Boutons d'action pour les entrées manuelles
        if entry.entry_type == "manual":
            actions_frame = ctk.CTkFrame(entry_frame)
            actions_frame.pack(fill="x", padx=10, pady=(0, 10))
            
            ctk.CTkButton(actions_frame, text="✏️ Modifier", width=80, height=25,
                         command=lambda: self.edit_log_entry(entry)).pack(side="right", padx=2)
            ctk.CTkButton(actions_frame, text="🗑️ Supprimer", width=80, height=25,
                         command=lambda: self.delete_log_entry(entry)).pack(side="right", padx=2)
                         
    def show_full_log_entry(self, entry):
        """Afficher une entrée complète dans une nouvelle fenêtre"""
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Entrée Journal - {entry.title}")
        dialog.geometry("700x600")
        dialog.transient(self)
        
        # Frame principal
        main_frame = ctk.CTkScrollableFrame(dialog)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # En-tête
        header_text = f"""📋 {entry.title}
        
🕐 Date: {entry.timestamp.strftime('%d/%m/%Y à %H:%M:%S')}
👤 Auteur: {entry.author}
🏷️ Catégorie: {entry.category}
🔧 Type: {'Automatique' if entry.entry_type == 'auto' else 'Manuelle'}

📝 Description:
"""
        
        header_label = ctk.CTkLabel(main_frame, text=header_text, 
                                   font=ctk.CTkFont(size=12),
                                   justify="left")
        header_label.pack(anchor="w", pady=(0, 10))
        
        # Contenu
        content_text = ctk.CTkTextbox(main_frame)
        content_text.pack(fill='both', expand=True, pady=10)
        content_text.insert("1.0", entry.description)
        content_text.configure(state="disabled")
        
        # Bouton fermer
        ctk.CTkButton(main_frame, text="Fermer", 
                     command=dialog.destroy).pack(pady=10)
                     
    def edit_log_entry(self, entry):
        """Modifier une entrée de journal"""
        if entry.entry_type == "auto":
            messagebox.showwarning("Attention", "Les entrées automatiques ne peuvent pas être modifiées!")
            return
            
        # Réutiliser la logique d'ajout mais en pré-remplissant
        dialog = ctk.CTkToplevel(self)
        dialog.title("Modifier Entrée Journal")
        dialog.geometry("600x500")
        dialog.transient(self)
        dialog.grab_set()
        
        # Centrer la fenêtre
        dialog.geometry("+%d+%d" % (
            self.winfo_rootx() + 100,
            self.winfo_rooty() + 100
        ))
        
        # Frame principal
        main_frame = ctk.CTkScrollableFrame(dialog)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Titre
        ctk.CTkLabel(main_frame, text="Titre:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        title_entry = ctk.CTkEntry(main_frame, width=500)
        title_entry.pack(fill='x', pady=(0, 10))
        title_entry.insert(0, entry.title)
        
        # Catégorie
        ctk.CTkLabel(main_frame, text="Catégorie:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        category_var = tk.StringVar(value=entry.category)
        category_menu = ctk.CTkOptionMenu(main_frame, values=["Decision", "Technical", "Meeting", "Other"], 
                                         variable=category_var)
        category_menu.pack(fill='x', pady=(0, 10))
        
        # Auteur
        ctk.CTkLabel(main_frame, text="Auteur:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        author_entry = ctk.CTkEntry(main_frame, width=500)
        author_entry.pack(fill='x', pady=(0, 10))
        author_entry.insert(0, entry.author)
        
        # Description
        ctk.CTkLabel(main_frame, text="Description / Détails:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        desc_textbox = ctk.CTkTextbox(main_frame, height=200, width=500)
        desc_textbox.pack(fill='both', expand=True, pady=(0, 20))
        desc_textbox.insert("1.0", entry.description)
        
        # Variable pour le résultat
        result = {"saved": False}
        
        def save_changes():
            if not title_entry.get().strip():
                messagebox.showerror("Erreur", "Le titre est obligatoire!")
                return
                
            entry.title = title_entry.get().strip()
            entry.description = desc_textbox.get("1.0", "end-1c")
            entry.author = author_entry.get().strip()
            entry.category = category_var.get()
            
            result["saved"] = True
            dialog.destroy()
            
        def cancel():
            dialog.destroy()
            
        # Boutons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill='x', pady=10)
        
        ctk.CTkButton(button_frame, text="Annuler", command=cancel).pack(side='right', padx=(5, 0))
        ctk.CTkButton(button_frame, text="Sauvegarder", command=save_changes).pack(side='right')
        
        # Attendre la fermeture
        dialog.wait_window()
        
        # Rafraîchir l'affichage si sauvegardé
        if result["saved"]:
            self.refresh_log_view()
            self.update_status("Entrée modifiée")
            
    def delete_log_entry(self, entry):
        """Supprimer une entrée de journal"""
        if messagebox.askyesno("Confirmation", f"Supprimer l'entrée '{entry.title}' ?"):
            self.log_entries.remove(entry)
            self.refresh_log_view()
            self.update_status("Entrée supprimée")
            
    def apply_log_filters(self, *args):
        """Appliquer les filtres et rafraîchir la vue"""
        self.refresh_log_view()
        
    def reset_log_filters(self):
        """Réinitialiser tous les filtres"""
        if hasattr(self, 'log_author_filter'):
            self.log_author_filter.set("Tous")
        if hasattr(self, 'log_category_filter'):
            self.log_category_filter.set("Toutes")
        if hasattr(self, 'log_date_from'):
            self.log_date_from.delete(0, 'end')
        if hasattr(self, 'log_date_to'):
            self.log_date_to.delete(0, 'end')
        self.refresh_log_view()
        
    def update_log_stats(self, filtered_entries):
        """Mettre à jour les statistiques du journal"""
        total = len(self.log_entries)
        filtered_count = len(filtered_entries)
        manual_count = len([e for e in filtered_entries if e.entry_type == "manual"])
        auto_count = len([e for e in filtered_entries if e.entry_type == "auto"])
        
        stats_text = f"Total: {total} | Affichées: {filtered_count} | Manuelles: {manual_count} | Auto: {auto_count}"
        
        if hasattr(self, 'log_stats_label'):
            self.log_stats_label.configure(text=stats_text)
            
    def export_decision_log(self):
        """Exporter le journal de bord"""
        if not self.log_entries:
            messagebox.showwarning("Avertissement", "Aucune entrée à exporter!")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown files", "*.md"), ("Text files", "*.txt")],
            title="Sauvegarder le journal de bord"
        )
        
        if filename:
            try:
                filtered_entries = self.get_filtered_log_entries()
                filtered_entries.sort(key=lambda x: x.timestamp, reverse=True)
                
                content = f"""# 💬 Journal de Bord / Carnet de Décisions

    *Exporté le : {datetime.datetime.now().strftime('%d/%m/%Y à %H:%M')}*
    *Nombre d'entrées : {len(filtered_entries)}*

---

"""
                
                for entry in filtered_entries:
                    entry_type = "🤖 AUTOMATIQUE" if entry.entry_type == "auto" else "👤 MANUELLE"
                    
                    content += f"""## {entry.title}

**📅 Date :** {entry.timestamp.strftime('%d/%m/%Y à %H:%M:%S')}
**👤 Auteur :** {entry.author}
**🏷️ Catégorie :** {entry.category}
**🔧 Type :** {entry_type}

**📝 Description :**
{entry.description}

---

"""
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                messagebox.showinfo("Export", f"Journal exporté avec succès :\n{filename}")
                self.update_status("Journal exporté")
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'export :\n{str(e)}")
                
    def clear_decision_log(self):
        """Vider le journal de bord"""
        if not self.log_entries:
            messagebox.showwarning("Avertissement", "Le journal est déjà vide!")
            return
            
        response = messagebox.askyesnocancel(
            "Confirmation", 
            "Que voulez-vous supprimer ?\n\n"
            "• Oui = Tout supprimer\n"
            "• Non = Supprimer seulement les entrées automatiques\n"
            "• Annuler = Ne rien supprimer"
        )
        
        if response is True:  # Tout supprimer
            self.log_entries.clear()
            self.refresh_log_view()
            self.update_status("Journal vidé complètement")
        elif response is False:  # Supprimer seulement les automatiques
            self.log_entries = [e for e in self.log_entries if e.entry_type == "manual"]
            self.refresh_log_view()
            self.update_status("Entrées automatiques supprimées")

    def show_document_manager(self):
        """Afficher le module de gestion documentaire"""
        self.clear_content()
        self.main_title.configure(text="📁 Gestionnaire de Documents")
        
        # ✅ CORRECTION : Configuration de l'expansion complète
        self.content_frame.grid_rowconfigure(1, weight=1)  # Ligne principale des documents
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        # Initialiser les variables si nécessaire
        if not hasattr(self, 'documents'):
            self.documents = []
        if not hasattr(self, 'documents_storage_path'):
            self.documents_storage_path = os.path.join(os.getcwd(), "documents_storage")
            if not os.path.exists(self.documents_storage_path):
                os.makedirs(self.documents_storage_path)
        if not hasattr(self, 'doc_view_mode'):
            self.doc_view_mode = "grid"  # "grid" ou "list"
        if not hasattr(self, 'doc_filter_category'):
            self.doc_filter_category = "Toutes"
        if not hasattr(self, 'doc_filter_node'):
            self.doc_filter_node = "Tous"
        
        # ✅ NOUVEAU : Taille fixe en mode Large
        self.doc_area_width = 1600   # Taille Large fixe
        self.doc_area_height = 800   # Taille Large fixe
            
        # Toolbar avec contrôles
        toolbar_frame = ctk.CTkFrame(self.content_frame)
        toolbar_frame.grid(row=0, column=0, padx=5, pady=2, sticky="ew")
        toolbar_frame.grid_columnconfigure(1, weight=1)
        
        # Section boutons d'action
        actions_frame = ctk.CTkFrame(toolbar_frame)
        actions_frame.grid(row=0, column=0, padx=5, pady=5)
        
        ctk.CTkButton(actions_frame, text="📁 Ajouter Document", 
                    command=self.add_document).grid(row=0, column=0, padx=5, pady=5)
        ctk.CTkButton(actions_frame, text="📋 Importer Dossier", 
                    command=self.import_folder).grid(row=0, column=1, padx=5, pady=5)
        ctk.CTkButton(actions_frame, text="📊 Rapport Documents", 
                    command=self.generate_document_report).grid(row=0, column=2, padx=5, pady=5)
        
        # Section filtres et vues
        filters_frame = ctk.CTkFrame(toolbar_frame)
        filters_frame.grid(row=0, column=1, padx=20, pady=5, sticky="ew")
        filters_frame.grid_columnconfigure(4, weight=1)
        
        ctk.CTkLabel(filters_frame, text="Filtres:").grid(row=0, column=0, padx=5, pady=5)
        
        # Filtre par catégorie
        ctk.CTkLabel(filters_frame, text="Catégorie:").grid(row=0, column=1, padx=(10, 2), pady=5)
        categories = ["Toutes", "Spécifications", "Tests", "Livrables", "Documentation", "Images", "Code", "Rapports", "General"]
        self.doc_category_filter = ctk.CTkOptionMenu(filters_frame, values=categories,
                                                    command=self.apply_document_filters, width=120)
        self.doc_category_filter.grid(row=0, column=2, padx=2, pady=5)
        
        # Filtre par noeud
        ctk.CTkLabel(filters_frame, text="Nœud:").grid(row=0, column=3, padx=(10, 2), pady=5)
        nodes = ["Tous"]
        if hasattr(self, 'tree_nodes') and self.tree_nodes:
            nodes.extend([node.text for node in self.tree_nodes])
        self.doc_node_filter = ctk.CTkOptionMenu(filters_frame, values=nodes,
                                                command=self.apply_document_filters, width=120)
        self.doc_node_filter.grid(row=0, column=4, padx=2, pady=5)
        
        # Sélecteur de vue
        view_frame = ctk.CTkFrame(filters_frame)
        view_frame.grid(row=0, column=5, padx=10, pady=5)
        
        ctk.CTkButton(view_frame, text="⊞", width=30, height=25,
                    command=lambda: self.change_document_view("grid")).pack(side="left", padx=1)
        ctk.CTkButton(view_frame, text="☰", width=30, height=25,
                    command=lambda: self.change_document_view("list")).pack(side="left", padx=1)
        
        # Statistiques
        stats_frame = ctk.CTkFrame(toolbar_frame)
        stats_frame.grid(row=0, column=2, padx=10, pady=5)
        
        self.doc_stats_label = ctk.CTkLabel(stats_frame, text="Chargement...")
        self.doc_stats_label.pack(padx=10, pady=5)
        
        # ✅ Frame principal avec zone de documents en taille Large fixe
        main_doc_frame = ctk.CTkFrame(self.content_frame)
        main_doc_frame.grid(row=1, column=0, padx=5, pady=2, sticky="nsew")
        main_doc_frame.grid_columnconfigure(0, weight=1)
        main_doc_frame.grid_rowconfigure(0, weight=1)
        
        # ✅ Canvas pour la zone de documents avec taille Large fixe
        doc_canvas_frame = ctk.CTkFrame(main_doc_frame)
        doc_canvas_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        doc_canvas_frame.grid_columnconfigure(0, weight=1)
        doc_canvas_frame.grid_rowconfigure(0, weight=1)
        
        # ✅ Canvas principal des documents avec taille Large (1600x800)
        self.doc_canvas = tk.Canvas(doc_canvas_frame, bg='#f0f0f0', 
                                width=self.doc_area_width, 
                                height=self.doc_area_height,
                                highlightthickness=0)  # ✅ Retirer la bordure
        self.doc_canvas.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbars pour la zone de documents
        doc_v_scrollbar = ttk.Scrollbar(doc_canvas_frame, orient="vertical", command=self.doc_canvas.yview)
        doc_h_scrollbar = ttk.Scrollbar(doc_canvas_frame, orient="horizontal", command=self.doc_canvas.xview)
        self.doc_canvas.configure(yscrollcommand=doc_v_scrollbar.set, xscrollcommand=doc_h_scrollbar.set)
        
        doc_v_scrollbar.grid(row=0, column=1, sticky="ns")
        doc_h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # ✅ Configuration de la zone de scroll - taille exacte
        self.doc_canvas.configure(scrollregion=(0, 0, self.doc_area_width, self.doc_area_height))
        
        # ✅ Frame pour le contenu des documents à l'intérieur du canvas
        self.doc_content_frame = ctk.CTkFrame(self.doc_canvas)
        self.doc_canvas_window = self.doc_canvas.create_window(0, 0, anchor="nw", window=self.doc_content_frame)
        self.doc_content_frame.grid_columnconfigure(0, weight=1)
        
        # ✅ Configuration du contenu pour occuper exactement la taille du canvas
        self.doc_content_frame.configure(width=self.doc_area_width, height=self.doc_area_height)
        
        # Bind pour ajuster la taille du frame interne
        self.doc_content_frame.bind('<Configure>', self.on_doc_frame_configure)
        self.doc_canvas.bind('<Configure>', self.on_doc_canvas_configure)
        
        # Afficher les documents
        self.refresh_document_view()
        
        self.update_status("Module de gestion documentaire affiché en taille Large (1600x800)")

    def on_doc_frame_configure(self, event):
        """Gérer le redimensionnement du frame de contenu des documents"""
        # ✅ CORRECTION : Mettre à jour la scrollregion pour la taille exacte du contenu
        canvas_width = self.doc_canvas.winfo_width()
        canvas_height = self.doc_canvas.winfo_height()
        
        # Ajuster la taille de la scrollregion au contenu réel
        bbox = self.doc_canvas.bbox("all")
        if bbox:
            self.doc_canvas.configure(scrollregion=bbox)
        else:
            # Si pas de contenu, utiliser la taille exacte du canvas
            self.doc_canvas.configure(scrollregion=(0, 0, canvas_width, canvas_height))

    def on_doc_canvas_configure(self, event):
        """Gérer le redimensionnement du canvas des documents"""
        # ✅ CORRECTION : Ajuster la largeur du frame interne exactement au canvas
        canvas_width = event.width
        canvas_height = event.height
        
        # Configurer la fenêtre du canvas pour occuper exactement l'espace
        self.doc_canvas.itemconfig(self.doc_canvas_window, width=canvas_width, height=canvas_height)
        
        # Mettre à jour la taille du frame de contenu
        self.doc_content_frame.configure(width=canvas_width, height=canvas_height)

    def refresh_document_view(self):
        """Rafraîchir l'affichage des documents - MODIFIÉ pour utiliser le canvas"""
        print(f"🔄 Rafraîchissement de l'affichage des documents...")
        print(f"   - Nombre de documents: {len(self.documents)}")
        print(f"   - Mode de vue: {self.doc_view_mode}")
        print(f"   - Taille zone: {self.doc_area_width}x{self.doc_area_height}")
        
        # Nettoyer le contenu actuel
        for widget in self.doc_content_frame.winfo_children():
            widget.destroy()
            
        # Filtrer les documents
        filtered_docs = self.get_filtered_documents()
        
        if not filtered_docs:
            no_docs_label = ctk.CTkLabel(self.doc_content_frame, 
                                        text="Aucun document trouvé avec les filtres actuels",
                                        font=ctk.CTkFont(size=14))
            no_docs_label.pack(pady=50)
        else:
            if self.doc_view_mode == "grid":
                self.show_documents_grid_enhanced(filtered_docs)
            else:
                self.show_documents_list_enhanced(filtered_docs)
                
        self.update_document_stats(filtered_docs)
        print(f"✅ Rafraîchissement terminé")

    def show_documents_grid_enhanced(self, documents):
        """Afficher les documents en vue grille - MODIFIÉ pour utiliser l'espace Large"""
        # Container pour la grille
        grid_frame = ctk.CTkFrame(self.doc_content_frame)
        grid_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Calculer le nombre de colonnes selon la largeur disponible
        card_width = 280
        available_width = self.doc_area_width - 40  # 40px pour les marges
        columns = max(1, available_width // (card_width + 10))  # 10px pour l'espacement
        
        # Configurer la grille dynamiquement
        for i in range(columns):
            grid_frame.grid_columnconfigure(i, weight=1)
        
        # Afficher les documents
        for i, doc in enumerate(documents):
            row = i // columns
            col = i % columns
            self.create_document_card_enhanced(grid_frame, doc, row, col, card_width)

    def create_document_card_enhanced(self, parent, doc, row, col, card_width):
        """Créer une carte de document améliorée pour la vue grille"""
        card = ctk.CTkFrame(parent, width=card_width, height=280)
        card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        card.grid_propagate(False)
        
        # Icône du type de fichier (plus grande)
        icon_label = ctk.CTkLabel(card, text=doc.get_file_type_icon(), 
                                font=ctk.CTkFont(size=36))
        icon_label.pack(pady=(15, 8))
        
        # Nom du document (avec wrapping amélioré)
        name_label = ctk.CTkLabel(card, text=doc.filename, 
                                font=ctk.CTkFont(size=12, weight="bold"),
                                wraplength=card_width - 20)
        name_label.pack(padx=10, pady=(0, 5))
        
        # Catégorie et version
        cat_version_text = f"{doc.get_category_icon()} {doc.category} • v{doc.version}"
        cat_label = ctk.CTkLabel(card, text=cat_version_text, 
                                font=ctk.CTkFont(size=10))
        cat_label.pack(pady=2)
        
        # Taille et date
        size_date_text = f"{doc.format_file_size()} • {doc.upload_date.strftime('%d/%m/%Y')}"
        size_label = ctk.CTkLabel(card, text=size_date_text, 
                                font=ctk.CTkFont(size=9))
        size_label.pack(pady=2)
        
        # Noeud lié
        if doc.linked_node:
            node_label = ctk.CTkLabel(card, text=f"🌳 {doc.linked_node.text}", 
                                    text_color="#2196F3", font=ctk.CTkFont(size=9))
            node_label.pack(pady=2)
            
        # Description courte si disponible
        if doc.description:
            desc_short = doc.description[:60] + "..." if len(doc.description) > 60 else doc.description
            desc_label = ctk.CTkLabel(card, text=desc_short, 
                                    font=ctk.CTkFont(size=9),
                                    wraplength=card_width - 20, height=30)
            desc_label.pack(padx=5, pady=3)
        
        # Tags si disponibles
        if doc.tags:
            tags_text = " ".join([f"#{tag}" for tag in doc.tags[:2]])  # Max 2 tags
            tags_label = ctk.CTkLabel(card, text=tags_text, 
                                    text_color="#4CAF50", font=ctk.CTkFont(size=8))
            tags_label.pack(pady=2)
        
        # Boutons d'action (plus compacts)
        buttons_frame = ctk.CTkFrame(card)
        buttons_frame.pack(side="bottom", fill="x", padx=8, pady=8)
        
        ctk.CTkButton(buttons_frame, text="👁️", width=35, height=25,
                    command=lambda: self.view_document(doc)).pack(side="left", padx=1)
        ctk.CTkButton(buttons_frame, text="✏️", width=35, height=25,
                    command=lambda: self.edit_document(doc)).pack(side="left", padx=1)
        ctk.CTkButton(buttons_frame, text="📁", width=35, height=25,
                    command=lambda: self.open_document_folder(doc)).pack(side="left", padx=1)
        ctk.CTkButton(buttons_frame, text="🗑️", width=35, height=25,
                    command=lambda: self.delete_document(doc)).pack(side="right", padx=1)

    def show_documents_list_enhanced(self, documents):
        """Afficher les documents en vue liste - MODIFIÉ pour utiliser l'espace Large"""
        # En-têtes avec largeur adaptée à la zone Large
        headers_frame = ctk.CTkFrame(self.doc_content_frame)
        headers_frame.pack(fill="x", padx=10, pady=5)
        
        # ✅ Configuration des colonnes pour la largeur Large
        headers_frame.grid_columnconfigure(0, weight=2, minsize=250)  # Document
        headers_frame.grid_columnconfigure(1, weight=1, minsize=120)  # Catégorie
        headers_frame.grid_columnconfigure(2, weight=1, minsize=80)   # Version
        headers_frame.grid_columnconfigure(3, weight=1, minsize=100)  # Taille
        headers_frame.grid_columnconfigure(4, weight=1, minsize=100)  # Date
        headers_frame.grid_columnconfigure(5, weight=1, minsize=150)  # Noeud
        headers_frame.grid_columnconfigure(6, weight=1, minsize=200)  # Description
        headers_frame.grid_columnconfigure(7, weight=1, minsize=120)  # Actions
        
        headers = ["Document", "Catégorie", "Version", "Taille", "Date", "Nœud", "Description", "Actions"]
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(headers_frame, text=header, 
                            font=ctk.CTkFont(size=12, weight="bold"))
            # ✅ CORRECTION : Alignement cohérent des en-têtes
            if i == 0:  # Document à gauche
                label.grid(row=0, column=i, padx=5, pady=10, sticky="w")
            else:  # Autres colonnes centrées
                label.grid(row=0, column=i, padx=5, pady=10, sticky="ew")
        
        # ✅ Ligne de séparation sous les en-têtes
        separator = ctk.CTkFrame(self.doc_content_frame, height=2)
        separator.pack(fill="x", padx=10, pady=(0, 5))
        
        # Zone scrollable pour les lignes de documents
        table_scroll = ctk.CTkScrollableFrame(self.doc_content_frame, 
                                            height=max(500, self.doc_area_height - 150))
        table_scroll.pack(fill="x", padx=10, pady=5)
        table_scroll.grid_columnconfigure(0, weight=1)
            
        # Documents
        for i, doc in enumerate(documents):
            self.create_document_row_enhanced(table_scroll, doc, i)

    def create_document_row_enhanced(self, parent, doc, row_index):
        """Créer une ligne de document améliorée pour la vue liste"""
        row_frame = ctk.CTkFrame(parent)
        row_frame.pack(fill="x", padx=5, pady=2)
        
        # ✅ Configuration des colonnes identique aux en-têtes
        row_frame.grid_columnconfigure(0, weight=2, minsize=250)  # Document
        row_frame.grid_columnconfigure(1, weight=1, minsize=120)  # Catégorie
        row_frame.grid_columnconfigure(2, weight=1, minsize=80)   # Version
        row_frame.grid_columnconfigure(3, weight=1, minsize=100)  # Taille
        row_frame.grid_columnconfigure(4, weight=1, minsize=100)  # Date
        row_frame.grid_columnconfigure(5, weight=1, minsize=150)  # Noeud
        row_frame.grid_columnconfigure(6, weight=1, minsize=200)  # Description
        row_frame.grid_columnconfigure(7, weight=1, minsize=120)  # Actions
        
        # Document avec icône
        name_text = f"{doc.get_file_type_icon()} {doc.filename}"
        name_label = ctk.CTkLabel(row_frame, text=name_text, anchor="w")
        name_label.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        # Catégorie avec icône
        cat_text = f"{doc.get_category_icon()} {doc.category}"
        cat_label = ctk.CTkLabel(row_frame, text=cat_text)
        cat_label.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Version
        version_label = ctk.CTkLabel(row_frame, text=f"v{doc.version}")
        version_label.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        # Taille
        size_label = ctk.CTkLabel(row_frame, text=doc.format_file_size())
        size_label.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
        
        # Date
        date_label = ctk.CTkLabel(row_frame, text=doc.upload_date.strftime('%d/%m/%Y'))
        date_label.grid(row=0, column=4, padx=5, pady=5, sticky="ew")
        
        # Noeud lié
        node_text = doc.linked_node.text if doc.linked_node else "-"
        node_label = ctk.CTkLabel(row_frame, text=node_text)
        node_label.grid(row=0, column=5, padx=5, pady=5, sticky="ew")
        
        # Description (tronquée)
        desc_text = doc.description[:50] + "..." if doc.description and len(doc.description) > 50 else (doc.description or "-")
        desc_label = ctk.CTkLabel(row_frame, text=desc_text, wraplength=180)
        desc_label.grid(row=0, column=6, padx=5, pady=5, sticky="ew")
        
        # Actions
        actions_frame = ctk.CTkFrame(row_frame)
        actions_frame.grid(row=0, column=7, padx=5, pady=5, sticky="ew")
        
        # ✅ Configuration pour centrer les boutons
        actions_frame.grid_columnconfigure(0, weight=1)
        actions_frame.grid_columnconfigure(1, weight=1)
        actions_frame.grid_columnconfigure(2, weight=1)
        actions_frame.grid_columnconfigure(3, weight=1)
        
        ctk.CTkButton(actions_frame, text="👁️", width=25, height=25,
                    command=lambda: self.view_document(doc)).grid(row=0, column=0, padx=1)
        ctk.CTkButton(actions_frame, text="✏️", width=25, height=25,
                    command=lambda: self.edit_document(doc)).grid(row=0, column=1, padx=1)
        ctk.CTkButton(actions_frame, text="📁", width=25, height=25,
                    command=lambda: self.open_document_folder(doc)).grid(row=0, column=2, padx=1)
        ctk.CTkButton(actions_frame, text="🗑️", width=25, height=25,
                    command=lambda: self.delete_document(doc)).grid(row=0, column=3, padx=1)
        
    def add_document(self):
        """Ajouter un nouveau document"""
        # Sélectionner le fichier
        file_path = filedialog.askopenfilename(
            title="Sélectionner un document",
            filetypes=[
                ("Tous les fichiers", "*.*"),
                ("PDF", "*.pdf"),
                ("Documents Word", "*.doc;*.docx"),
                ("Excel", "*.xls;*.xlsx"),
                ("PowerPoint", "*.ppt;*.pptx"),
                ("Images", "*.jpg;*.jpeg;*.png;*.gif;*.bmp"),
                ("Texte", "*.txt;*.md"),
                ("Archives", "*.zip;*.rar;*.7z")
            ]
        )
        
        if not file_path:
            return
            
        # Créer une fenêtre de dialogue pour les métadonnées
        dialog = ctk.CTkToplevel(self)
        dialog.title("Ajouter un Document")
        dialog.geometry("500x600")
        dialog.transient(self)
        dialog.grab_set()
        
        # Centrer la fenêtre
        dialog.geometry("+%d+%d" % (
            self.winfo_rootx() + 100,
            self.winfo_rooty() + 100
        ))
        
        # Frame principal
        main_frame = ctk.CTkScrollableFrame(dialog)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Informations du fichier
        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        file_type = os.path.splitext(filename)[1].lower()
        
        # Afficher les infos du fichier
        info_frame = ctk.CTkFrame(main_frame)
        info_frame.pack(fill='x', pady=(0, 20))
        
        ctk.CTkLabel(info_frame, text="📄 Informations du fichier", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        ctk.CTkLabel(info_frame, text=f"Nom: {filename}").pack(anchor='w', padx=10)
        ctk.CTkLabel(info_frame, text=f"Taille: {Document('', file_path).format_file_size()}").pack(anchor='w', padx=10)
        ctk.CTkLabel(info_frame, text=f"Type: {file_type}").pack(anchor='w', padx=10, pady=(0, 10))
        
        # Nom du document (modifiable)
        ctk.CTkLabel(main_frame, text="Nom du document:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        name_entry = ctk.CTkEntry(main_frame, width=400)
        name_entry.pack(fill='x', pady=(0, 10))
        name_entry.insert(0, os.path.splitext(filename)[0])
        
        # Catégorie (auto-détectée)
        ctk.CTkLabel(main_frame, text="Catégorie:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        
        # Auto-détection de la catégorie
        auto_category = self.detect_document_category(filename, file_type)
        category_var = tk.StringVar(value=auto_category)
        
        categories = ["Spécifications", "Tests", "Livrables", "Documentation", "Images", "Code", "Rapports", "General"]
        category_menu = ctk.CTkOptionMenu(main_frame, values=categories, variable=category_var)
        category_menu.pack(fill='x', pady=(0, 10))
        
        # Version
        ctk.CTkLabel(main_frame, text="Version:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        version_entry = ctk.CTkEntry(main_frame, width=400, placeholder_text="Ex: 1.0, 2.1, v1.0")
        version_entry.pack(fill='x', pady=(0, 10))
        version_entry.insert(0, "1.0")
        
        # Description
        ctk.CTkLabel(main_frame, text="Description:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        desc_textbox = ctk.CTkTextbox(main_frame, height=80, width=400)
        desc_textbox.pack(fill='x', pady=(0, 10))
        
        # Lien avec noeud de l'arbre
        ctk.CTkLabel(main_frame, text="Lier à un nœud:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        
        # Récupérer les noeuds disponibles
        node_options = ["Aucun"]
        if hasattr(self, 'tree_nodes') and self.tree_nodes:
            node_options.extend([node.text for node in self.tree_nodes])
        
        linked_node_var = tk.StringVar(value="Aucun")
        node_menu = ctk.CTkOptionMenu(main_frame, values=node_options, variable=linked_node_var)
        node_menu.pack(fill='x', pady=(0, 10))
        
        # Tags
        ctk.CTkLabel(main_frame, text="Tags (séparés par des virgules):", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        tags_entry = ctk.CTkEntry(main_frame, width=400, placeholder_text="urgent, client, v2.0")
        tags_entry.pack(fill='x', pady=(0, 20))
        
        # Variable pour le résultat
        result = {"saved": False}
        
        def save_document():
            try:
                # Trouver le noeud lié
                linked_node = None
                if linked_node_var.get() != "Aucun" and hasattr(self, 'tree_nodes'):
                    for node in self.tree_nodes:
                        if node.text == linked_node_var.get():
                            linked_node = node
                            break
                
                # Créer le document
                doc = Document(
                    filename=name_entry.get().strip() or filename,
                    file_path=file_path,
                    category=category_var.get(),
                    version=version_entry.get().strip() or "1.0",
                    linked_node=linked_node,
                    description=desc_textbox.get("1.0", "end-1c")
                )
                
                # Traiter les tags
                tags_text = tags_entry.get().strip()
                if tags_text:
                    doc.tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]
                
                # Copier le fichier dans le stockage de l'app
                stored_filename = f"{doc.id}_{filename}"
                stored_path = os.path.join(self.documents_storage_path, stored_filename)
                shutil.copy2(file_path, stored_path)
                doc.stored_path = stored_path
                
                # Ajouter à la liste
                self.documents.append(doc)
                
                # Enregistrement automatique dans le journal
                if hasattr(self, 'add_automatic_log_entry'):
                    self.add_automatic_log_entry(
                        title=f"Document ajouté : '{doc.filename}'",
                        description=f"Nouveau document ajouté.\nCatégorie: {doc.category}\nVersion: {doc.version}\nTaille: {doc.format_file_size()}",
                        category="Document"
                    )
                
                result["saved"] = True
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'ajout du document :\n{str(e)}")
                
        def cancel():
            dialog.destroy()
            
        # Boutons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill='x', pady=10)
        
        ctk.CTkButton(button_frame, text="Annuler", command=cancel).pack(side='right', padx=(5, 0))
        ctk.CTkButton(button_frame, text="Ajouter", command=save_document).pack(side='right')
        
        # Attendre la fermeture
        dialog.wait_window()
        
        # Rafraîchir l'affichage si sauvegardé
        if result["saved"]:
            self.refresh_document_view()
            self.update_status("Document ajouté avec succès")
            
    def detect_document_category(self, filename, file_type):
        """Détecter automatiquement la catégorie d'un document"""
        filename_lower = filename.lower()
        
        # Mots-clés pour chaque catégorie
        keywords = {
            "Spécifications": ["spec", "specification", "cahier", "requirements", "req", "exigences"],
            "Tests": ["test", "unittest", "qa", "quality", "validation", "verify"],
            "Livrables": ["deliverable", "livrable", "release", "final", "production"],
            "Documentation": ["doc", "manuel", "guide", "readme", "help", "tutorial"],
            "Images": ["screenshot", "capture", "image", "photo", "mockup", "wireframe"],
            "Code": ["source", "code", "script", "program"],
            "Rapports": ["rapport", "report", "analyse", "summary", "résultat"]
        }
        
        # Vérifier par type de fichier d'abord
        if file_type in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg"]:
            return "Images"
        elif file_type in [".py", ".js", ".html", ".css", ".java", ".cpp", ".c"]:
            return "Code"
        elif file_type in [".pdf"] and any(word in filename_lower for word in ["rapport", "report"]):
            return "Rapports"
        
        # Vérifier par mots-clés dans le nom
        for category, words in keywords.items():
            if any(word in filename_lower for word in words):
                return category
                
        return "General"
        
    def import_folder(self):
        """Importer tous les fichiers d'un dossier"""
        folder_path = filedialog.askdirectory(title="Sélectionner un dossier à importer")
        
        if not folder_path:
            return
        
        # ✅ Vérifier et créer le dossier de stockage si nécessaire
        if not hasattr(self, 'documents_storage_path'):
            self.documents_storage_path = os.path.join(os.getcwd(), "documents_storage")
        if not os.path.exists(self.documents_storage_path):
            os.makedirs(self.documents_storage_path)


        # Compter les fichiers
        files_to_import = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                # Ignorer les fichiers système et cachés
                if not file.startswith('.') and os.path.isfile(file_path):
                    files_to_import.append(file_path)
        
        if not files_to_import:
            messagebox.showwarning("Avertissement", "Aucun fichier trouvé dans le dossier sélectionné!")
            return
            
        # Demander confirmation
        if not messagebox.askyesno("Confirmation", 
                                f"Importer {len(files_to_import)} fichier(s) ?\n\n"
                                f"Les fichiers seront automatiquement catégorisés."):
            return
            
        # Créer une barre de progression
        progress_dialog = ctk.CTkToplevel(self)
        progress_dialog.title("Import en cours...")
        progress_dialog.geometry("400x150")
        progress_dialog.transient(self)
        progress_dialog.grab_set()
        
        # Centrer la fenêtre
        progress_dialog.geometry("+%d+%d" % (
            self.winfo_rootx() + 200,
            self.winfo_rooty() + 200
        ))
        
        progress_label = ctk.CTkLabel(progress_dialog, text="Import en cours...")
        progress_label.pack(pady=20)
        
        progress_bar = ctk.CTkProgressBar(progress_dialog, width=300)
        progress_bar.pack(pady=10)
        progress_bar.set(0)
        
        status_label = ctk.CTkLabel(progress_dialog, text="")
        status_label.pack(pady=10)
        
        # Importer les fichiers
        imported_count = 0
        total_files = len(files_to_import)
        
        def import_file(index):
            nonlocal imported_count
            
            if index >= total_files:
                # Import terminé
                progress_dialog.destroy()
                messagebox.showinfo("Import terminé", f"{imported_count} fichier(s) importé(s) avec succès!")
                self.refresh_document_view()
                return
                
            file_path = files_to_import[index]
            filename = os.path.basename(file_path)
            
            # Mettre à jour l'interface
            progress = (index + 1) / total_files
            progress_bar.set(progress)
            status_label.configure(text=f"Import: {filename}")
            progress_dialog.update()
            
            try:
                # Créer le document
                doc = Document(
                    filename=filename,
                    file_path=file_path,
                    category=self.detect_document_category(filename, os.path.splitext(filename)[1].lower()),
                    version="1.0",
                    description=f"Importé automatiquement depuis {os.path.dirname(file_path)}"
                )
                
                # Copier le fichier
                stored_filename = f"{doc.id}_{filename}"
                stored_path = os.path.join(self.documents_storage_path, stored_filename)
                shutil.copy2(file_path, stored_path)
                doc.stored_path = stored_path
                
                # Ajouter à la liste
                self.documents.append(doc)
                imported_count += 1
                
            except Exception as e:
                print(f"Erreur lors de l'import de {filename}: {str(e)}")
                
            # Programmer l'import du fichier suivant
            progress_dialog.after(50, lambda: import_file(index + 1))
            
        # Commencer l'import
        import_file(0)
        
    def change_document_view(self, view_mode):
        """Changer le mode de vue des documents"""
        self.doc_view_mode = view_mode
        self.refresh_document_view()
        
    def apply_document_filters(self, *args):
        """Appliquer les filtres et rafraîchir la vue"""
        self.refresh_document_view()
        
    def refresh_document_view(self):
        """Rafraîchir l'affichage des documents"""
        # Nettoyer le contenu actuel
        for widget in self.doc_content_frame.winfo_children():
            widget.destroy()
            
        # Filtrer les documents
        filtered_docs = self.get_filtered_documents()
        
        if not filtered_docs:
            no_docs_label = ctk.CTkLabel(self.doc_content_frame, 
                                        text="Aucun document trouvé avec les filtres actuels",
                                        font=ctk.CTkFont(size=14))
            no_docs_label.pack(pady=50)
        else:
            if self.doc_view_mode == "grid":
                self.show_documents_grid(filtered_docs)
            else:
                self.show_documents_list(filtered_docs)
                
        self.update_document_stats(filtered_docs)
        
    def get_filtered_documents(self):
        """Obtenir les documents filtrés selon les critères"""
        filtered = self.documents.copy()
        
        # Filtre par catégorie
        if hasattr(self, 'doc_category_filter') and self.doc_category_filter.get() != "Toutes":
            filtered = [d for d in filtered if d.category == self.doc_category_filter.get()]
            
        # Filtre par noeud
        if hasattr(self, 'doc_node_filter') and self.doc_node_filter.get() != "Tous":
            filtered = [d for d in filtered if d.linked_node and d.linked_node.text == self.doc_node_filter.get()]
            
        return filtered
        
    def show_documents_grid(self, documents):
        """Afficher les documents en vue grille"""
        # Container pour la grille
        grid_frame = ctk.CTkFrame(self.doc_content_frame)
        grid_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Configurer la grille (4 colonnes)
        for i in range(4):
            grid_frame.grid_columnconfigure(i, weight=1)
        
        # Afficher les documents
        for i, doc in enumerate(documents):
            row = i // 4
            col = i % 4
            self.create_document_card(grid_frame, doc, row, col)
            
    def create_document_card(self, parent, doc, row, col):
        """Créer une carte de document pour la vue grille"""
        card = ctk.CTkFrame(parent, width=200, height=250)
        card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        card.grid_propagate(False)
        
        # Icône du type de fichier
        icon_label = ctk.CTkLabel(card, text=doc.get_file_type_icon(), 
                                font=ctk.CTkFont(size=32))
        icon_label.pack(pady=(15, 5))
        
        # Nom du document
        name_label = ctk.CTkLabel(card, text=doc.filename, 
                                font=ctk.CTkFont(size=12, weight="bold"),
                                wraplength=180)
        name_label.pack(padx=10, pady=5)
        
        # Catégorie et version
        cat_version_text = f"{doc.get_category_icon()} {doc.category} • v{doc.version}"
        cat_label = ctk.CTkLabel(card, text=cat_version_text, 
                                font=ctk.CTkFont(size=10))
        cat_label.pack(pady=2)
        
        # Taille et date
        size_date_text = f"{doc.format_file_size()} • {doc.upload_date.strftime('%d/%m/%Y')}"
        size_label = ctk.CTkLabel(card, text=size_date_text, 
                                font=ctk.CTkFont(size=9))
        size_label.pack(pady=2)
        
        # Noeud lié
        if doc.linked_node:
            node_label = ctk.CTkLabel(card, text=f"🌳 {doc.linked_node.text}", 
                                    text_color="#2196F3", font=ctk.CTkFont(size=9))
            node_label.pack(pady=2)
            
        # Boutons d'action
        buttons_frame = ctk.CTkFrame(card)
        buttons_frame.pack(side="bottom", fill="x", padx=10, pady=10)
        
        ctk.CTkButton(buttons_frame, text="👁️", width=30, height=25,
                    command=lambda: self.view_document(doc)).pack(side="left", padx=1)
        ctk.CTkButton(buttons_frame, text="✏️", width=30, height=25,
                    command=lambda: self.edit_document(doc)).pack(side="left", padx=1)
        ctk.CTkButton(buttons_frame, text="📁", width=30, height=25,
                    command=lambda: self.open_document_folder(doc)).pack(side="left", padx=1)
        ctk.CTkButton(buttons_frame, text="🗑️", width=30, height=25,
                    command=lambda: self.delete_document(doc)).pack(side="right", padx=1)
                    
    def show_documents_list(self, documents):
        """Afficher les documents en vue liste"""
        # En-têtes
        headers_frame = ctk.CTkFrame(self.doc_content_frame)
        headers_frame.pack(fill="x", padx=10, pady=5)
        headers_frame.grid_columnconfigure(0, weight=2)  # Nom
        headers_frame.grid_columnconfigure(1, weight=1)  # Catégorie
        headers_frame.grid_columnconfigure(2, weight=1)  # Version
        headers_frame.grid_columnconfigure(3, weight=1)  # Taille
        headers_frame.grid_columnconfigure(4, weight=1)  # Date
        headers_frame.grid_columnconfigure(5, weight=1)  # Noeud
        headers_frame.grid_columnconfigure(6, weight=1)  # Actions
        
        headers = ["Document", "Catégorie", "Version", "Taille", "Date", "Nœud", "Actions"]
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(headers_frame, text=header, 
                            font=ctk.CTkFont(size=12, weight="bold"))
            label.grid(row=0, column=i, padx=5, pady=10, sticky="w")
            
        # Documents
        for i, doc in enumerate(documents):
            self.create_document_row(i + 1, doc)
            
    def create_document_row(self, row, doc):
        """Créer une ligne de document pour la vue liste"""
        row_frame = ctk.CTkFrame(self.doc_content_frame)
        row_frame.pack(fill="x", padx=10, pady=2)
        row_frame.grid_columnconfigure(0, weight=2)
        row_frame.grid_columnconfigure(1, weight=1)
        row_frame.grid_columnconfigure(2, weight=1)
        row_frame.grid_columnconfigure(3, weight=1)
        row_frame.grid_columnconfigure(4, weight=1)
        row_frame.grid_columnconfigure(5, weight=1)
        row_frame.grid_columnconfigure(6, weight=1)
        
        # Nom avec icône
        name_text = f"{doc.get_file_type_icon()} {doc.filename}"
        name_label = ctk.CTkLabel(row_frame, text=name_text, anchor="w")
        name_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        # Catégorie avec icône
        cat_text = f"{doc.get_category_icon()} {doc.category}"
        cat_label = ctk.CTkLabel(row_frame, text=cat_text)
        cat_label.grid(row=0, column=1, padx=5, pady=5)
        
        # Version
        version_label = ctk.CTkLabel(row_frame, text=f"v{doc.version}")
        version_label.grid(row=0, column=2, padx=5, pady=5)
        
        # Taille
        size_label = ctk.CTkLabel(row_frame, text=doc.format_file_size())
        size_label.grid(row=0, column=3, padx=5, pady=5)
        
        # Date
        date_label = ctk.CTkLabel(row_frame, text=doc.upload_date.strftime('%d/%m/%Y'))
        date_label.grid(row=0, column=4, padx=5, pady=5)
        
        # Noeud lié
        node_text = doc.linked_node.text if doc.linked_node else "-"
        node_label = ctk.CTkLabel(row_frame, text=node_text)
        node_label.grid(row=0, column=5, padx=5, pady=5)
        
        # Actions
        actions_frame = ctk.CTkFrame(row_frame)
        actions_frame.grid(row=0, column=6, padx=5, pady=5)
        
        ctk.CTkButton(actions_frame, text="👁️", width=25, height=25,
                    command=lambda: self.view_document(doc)).pack(side="left", padx=1)
        ctk.CTkButton(actions_frame, text="✏️", width=25, height=25,
                    command=lambda: self.edit_document(doc)).pack(side="left", padx=1)
        ctk.CTkButton(actions_frame, text="🗑️", width=25, height=25,
                    command=lambda: self.delete_document(doc)).pack(side="left", padx=1)
                    
    def view_document(self, doc):
        """Visualiser un document"""
        if not os.path.exists(doc.stored_path):
            messagebox.showerror("Erreur", "Le fichier n'existe plus sur le disque!")
            return
            
        # Ouvrir avec l'application par défaut du système
        try:
            if sys.platform.startswith('win'):
                os.startfile(doc.stored_path)
            elif sys.platform.startswith('darwin'):  # macOS
                os.system(f'open "{doc.stored_path}"')
            else:  # Linux
                os.system(f'xdg-open "{doc.stored_path}"')
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le document :\n{str(e)}")
            
    def edit_document(self, doc):
        """Éditer les métadonnées d'un document"""
        # Créer une fenêtre de dialogue
        dialog = ctk.CTkToplevel(self)
        dialog.title("Éditer le Document")
        dialog.geometry("500x600")
        dialog.transient(self)
        dialog.grab_set()
        
        # Centrer la fenêtre
        dialog.geometry("+%d+%d" % (
            self.winfo_rootx() + 100,
            self.winfo_rooty() + 100
        ))
        
        # Frame principal
        main_frame = ctk.CTkScrollableFrame(dialog)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Informations du fichier (non modifiables)
        info_frame = ctk.CTkFrame(main_frame)
        info_frame.pack(fill='x', pady=(0, 20))
        
        ctk.CTkLabel(info_frame, text="📄 Informations du fichier", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        ctk.CTkLabel(info_frame, text=f"Fichier: {os.path.basename(doc.stored_path)}").pack(anchor='w', padx=10)
        ctk.CTkLabel(info_frame, text=f"Taille: {doc.format_file_size()}").pack(anchor='w', padx=10)
        ctk.CTkLabel(info_frame, text=f"Type: {doc.file_type}").pack(anchor='w', padx=10)
        ctk.CTkLabel(info_frame, text=f"Ajouté: {doc.upload_date.strftime('%d/%m/%Y à %H:%M')}").pack(anchor='w', padx=10, pady=(0, 10))
        
        # Nom du document
        ctk.CTkLabel(main_frame, text="Nom du document:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        name_entry = ctk.CTkEntry(main_frame, width=400)
        name_entry.pack(fill='x', pady=(0, 10))
        name_entry.insert(0, doc.filename)
        
        # Catégorie
        ctk.CTkLabel(main_frame, text="Catégorie:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        category_var = tk.StringVar(value=doc.category)
        categories = ["Spécifications", "Tests", "Livrables", "Documentation", "Images", "Code", "Rapports", "General"]
        category_menu = ctk.CTkOptionMenu(main_frame, values=categories, variable=category_var)
        category_menu.pack(fill='x', pady=(0, 10))
        
        # Version
        ctk.CTkLabel(main_frame, text="Version:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        version_entry = ctk.CTkEntry(main_frame, width=400)
        version_entry.pack(fill='x', pady=(0, 10))
        version_entry.insert(0, doc.version)
        
        # Description
        ctk.CTkLabel(main_frame, text="Description:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        desc_textbox = ctk.CTkTextbox(main_frame, height=80, width=400)
        desc_textbox.pack(fill='x', pady=(0, 10))
        desc_textbox.insert("1.0", doc.description)
        
        # Lien avec noeud de l'arbre
        ctk.CTkLabel(main_frame, text="Lier à un nœud:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        
        node_options = ["Aucun"]
        if hasattr(self, 'tree_nodes') and self.tree_nodes:
            node_options.extend([node.text for node in self.tree_nodes])
        
        linked_node_var = tk.StringVar(value=doc.linked_node.text if doc.linked_node else "Aucun")
        node_menu = ctk.CTkOptionMenu(main_frame, values=node_options, variable=linked_node_var)
        node_menu.pack(fill='x', pady=(0, 10))
        
        # Tags
        ctk.CTkLabel(main_frame, text="Tags (séparés par des virgules):", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        tags_entry = ctk.CTkEntry(main_frame, width=400)
        tags_entry.pack(fill='x', pady=(0, 20))
        if doc.tags:
            tags_entry.insert(0, ", ".join(doc.tags))
        
        # Variable pour le résultat
        result = {"saved": False}
        
        def save_changes():
            try:
                # Trouver le noeud lié
                linked_node = None
                if linked_node_var.get() != "Aucun" and hasattr(self, 'tree_nodes'):
                    for node in self.tree_nodes:
                        if node.text == linked_node_var.get():
                            linked_node = node
                            break
                
                # Mettre à jour le document
                doc.filename = name_entry.get().strip()
                doc.category = category_var.get()
                doc.version = version_entry.get().strip()
                doc.description = desc_textbox.get("1.0", "end-1c")
                doc.linked_node = linked_node
                
                # Traiter les tags
                tags_text = tags_entry.get().strip()
                if tags_text:
                    doc.tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]
                else:
                    doc.tags = []
                
                # Enregistrement automatique dans le journal
                if hasattr(self, 'add_automatic_log_entry'):
                    self.add_automatic_log_entry(
                        title=f"Document modifié : '{doc.filename}'",
                        description=f"Métadonnées du document mises à jour.",
                        category="Document"
                    )
                
                result["saved"] = True
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la modification :\n{str(e)}")
                
        def cancel():
            dialog.destroy()
            
        # Boutons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill='x', pady=10)
        
        ctk.CTkButton(button_frame, text="Annuler", command=cancel).pack(side='right', padx=(5, 0))
        ctk.CTkButton(button_frame, text="Sauvegarder", command=save_changes).pack(side='right')
        
        # Attendre la fermeture
        dialog.wait_window()
        
        # Rafraîchir l'affichage si sauvegardé
        if result["saved"]:
            self.refresh_document_view()
            self.update_status("Document modifié")
            
    def delete_document(self, doc):
        """Supprimer un document"""
        if messagebox.askyesno("Confirmation", 
                            f"Supprimer le document '{doc.filename}' ?\n\n"
                            f"Le fichier sera supprimé définitivement."):
            try:
                # Supprimer le fichier physique
                if os.path.exists(doc.stored_path):
                    os.remove(doc.stored_path)
                    
                # Supprimer de la liste
                self.documents.remove(doc)
                
                # Enregistrement automatique dans le journal
                if hasattr(self, 'add_automatic_log_entry'):
                    self.add_automatic_log_entry(
                        title=f"Document supprimé : '{doc.filename}'",
                        description=f"Document supprimé définitivement.",
                        category="Document"
                    )
                
                self.refresh_document_view()
                self.update_status("Document supprimé")
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la suppression :\n{str(e)}")
                
    def open_document_folder(self, doc):
        """Ouvrir le dossier contenant le document"""
        try:
            folder_path = os.path.dirname(doc.stored_path)
            if sys.platform.startswith('win'):
                os.startfile(folder_path)
            elif sys.platform.startswith('darwin'):  # macOS
                os.system(f'open "{folder_path}"')
            else:  # Linux
                os.system(f'xdg-open "{folder_path}"')
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le dossier :\n{str(e)}")
            
    def update_document_stats(self, filtered_docs):
        """Mettre à jour les statistiques des documents"""
        total = len(self.documents)
        filtered_count = len(filtered_docs)
        
        # Calcul de la taille totale
        total_size = sum(doc.file_size for doc in filtered_docs)
        if total_size < 1024*1024:
            size_text = f"{total_size/1024:.1f} KB"
        else:
            size_text = f"{total_size/(1024*1024):.1f} MB"
        
        # Compter par catégorie
        categories = {}
        for doc in filtered_docs:
            categories[doc.category] = categories.get(doc.category, 0) + 1
        
        stats_text = f"Total: {total} | Affichés: {filtered_count} | Taille: {size_text}"
        
        if hasattr(self, 'doc_stats_label'):
            self.doc_stats_label.configure(text=stats_text)
            
    def generate_document_report(self):
        """Générer un rapport des documents"""
        if not self.documents:
            messagebox.showwarning("Avertissement", "Aucun document à inclure dans le rapport!")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown files", "*.md"), ("Text files", "*.txt")],
            title="Sauvegarder le rapport des documents"
        )
        
        if filename:
            try:
                # Trier les documents par catégorie
                docs_by_category = {}
                for doc in self.documents:
                    if doc.category not in docs_by_category:
                        docs_by_category[doc.category] = []
                    docs_by_category[doc.category].append(doc)
                
                content = f"""# 📁 Rapport de Gestion Documentaire

    *Généré le : {datetime.datetime.now().strftime('%d/%m/%Y à %H:%M')}*
    *Nombre total de documents : {len(self.documents)}*

    ## 📊 Statistiques Générales

    """
                
                # Statistiques par catégorie
                for category, docs in docs_by_category.items():
                    total_size = sum(doc.file_size for doc in docs)
                    size_text = f"{total_size/(1024*1024):.1f} MB" if total_size > 1024*1024 else f"{total_size/1024:.1f} KB"
                    content += f"- **{category}** : {len(docs)} document(s) - {size_text}\n"
                
                content += "\n---\n\n"
                
                # Détail par catégorie
                for category, docs in sorted(docs_by_category.items()):
                    icon = docs[0].get_category_icon() if docs else "📄"
                    content += f"## {icon} {category}\n\n"
                    
                    for doc in sorted(docs, key=lambda x: x.filename):
                        linked_text = f" (🌳 {doc.linked_node.text})" if doc.linked_node else ""
                        tags_text = f" [Tags: {', '.join(doc.tags)}]" if doc.tags else ""
                        
                        content += f"""### {doc.get_file_type_icon()} {doc.filename}

    - **Version :** {doc.version}
    - **Taille :** {doc.format_file_size()}
    - **Date d'ajout :** {doc.upload_date.strftime('%d/%m/%Y à %H:%M')}
    - **Description :** {doc.description or "Aucune description"}
    - **Nœud lié :** {doc.linked_node.text if doc.linked_node else "Aucun"}{tags_text}

    """
                
                content += f"""
    ---

    *Rapport généré automatiquement par l'application de gestion de projet*
    *Chemin de stockage : {self.documents_storage_path}*
    """
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                messagebox.showinfo("Rapport généré", f"Rapport sauvegardé avec succès :\n{filename}")
                self.update_status("Rapport des documents généré")
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la génération du rapport :\n{str(e)}")
                        
    def show_block_library(self):
        """Afficher le module de bibliothèque de blocs réutilisables"""
        self.clear_content()
        self.main_title.configure(text="📦 Bibliothèque de Blocs Réutilisables")
        
        # ✅ CORRECTION : Configuration de l'expansion complète
        self.content_frame.grid_rowconfigure(1, weight=1)  # Ligne principale des blocs
        self.content_frame.grid_columnconfigure(0, weight=1)
        
        # Initialiser les variables si nécessaire
        if not hasattr(self, 'project_blocks'):
            self.project_blocks = []
        if not hasattr(self, 'block_view_mode'):
            self.block_view_mode = "grid"  # "grid" ou "list"
        if not hasattr(self, 'block_filter_category'):
            self.block_filter_category = "Toutes"
        if not hasattr(self, 'block_filter_domain'):
            self.block_filter_domain = "Tous"
        if not hasattr(self, 'blocks_storage_path'):
            self.blocks_storage_path = os.path.join(os.getcwd(), "project_blocks")
            if not os.path.exists(self.blocks_storage_path):
                os.makedirs(self.blocks_storage_path)
        
        # ✅ NOUVEAU : Taille fixe en mode Large
        self.block_area_width = 1600   # Taille Large fixe
        self.block_area_height = 800   # Taille Large fixe
        
        # Charger les blocs sauvegardés
        self.load_project_blocks()
        
        # Toolbar avec contrôles
        toolbar_frame = ctk.CTkFrame(self.content_frame)
        toolbar_frame.grid(row=0, column=0, padx=5, pady=2, sticky="ew")
        toolbar_frame.grid_columnconfigure(1, weight=1)
        
        # Section boutons d'action
        actions_frame = ctk.CTkFrame(toolbar_frame)
        actions_frame.grid(row=0, column=0, padx=5, pady=5)
        
        ctk.CTkButton(actions_frame, text="➕ Nouveau Bloc", 
                    command=self.create_new_block).grid(row=0, column=0, padx=5, pady=5)
        ctk.CTkButton(actions_frame, text="💾 Créer depuis Arbre", 
                    command=self.create_block_from_tree).grid(row=0, column=1, padx=5, pady=5)
        ctk.CTkButton(actions_frame, text="📤 Exporter Blocs", 
                    command=self.export_blocks).grid(row=0, column=2, padx=5, pady=5)
        ctk.CTkButton(actions_frame, text="📥 Importer Blocs", 
                    command=self.import_blocks).grid(row=0, column=3, padx=5, pady=5)
        ctk.CTkButton(actions_frame, text="📊 Rapport d'Usage", 
                    command=self.generate_usage_report).grid(row=0, column=4, padx=5, pady=5)
        
        # Section filtres et vues
        filters_frame = ctk.CTkFrame(toolbar_frame)
        filters_frame.grid(row=0, column=1, padx=20, pady=5, sticky="ew")
        filters_frame.grid_columnconfigure(4, weight=1)
        
        ctk.CTkLabel(filters_frame, text="Filtres:").grid(row=0, column=0, padx=5, pady=5)
        
        # Filtre par catégorie
        ctk.CTkLabel(filters_frame, text="Catégorie:").grid(row=0, column=1, padx=(10, 2), pady=5)
        categories = ["Toutes", "Process", "Testing", "CI/CD", "Hardware", "Software", "Integration", "Validation", "Documentation", "Planning", "Quality", "Security", "General"]
        self.block_category_filter = ctk.CTkOptionMenu(filters_frame, values=categories,
                                                    command=self.apply_block_filters, width=120)
        self.block_category_filter.grid(row=0, column=2, padx=2, pady=5)
        
        # Filtre par domaine
        ctk.CTkLabel(filters_frame, text="Domaine:").grid(row=0, column=3, padx=(10, 2), pady=5)
        domains = ["Tous", "Embedded", "Web", "Mobile", "IoT", "Desktop", "Cloud", "AI/ML", "Data"]
        self.block_domain_filter = ctk.CTkOptionMenu(filters_frame, values=domains,
                                                    command=self.apply_block_filters, width=120)
        self.block_domain_filter.grid(row=0, column=4, padx=2, pady=5)
        
        # Tri
        ctk.CTkLabel(filters_frame, text="Tri:").grid(row=0, column=5, padx=(10, 2), pady=5)
        sort_options = ["Nom", "Date création", "Usage", "Succès", "Dernière utilisation"]
        self.block_sort_filter = ctk.CTkOptionMenu(filters_frame, values=sort_options,
                                                command=self.apply_block_filters, width=140)
        self.block_sort_filter.grid(row=0, column=6, padx=2, pady=5)
        
        # Sélecteur de vue
        view_frame = ctk.CTkFrame(filters_frame)
        view_frame.grid(row=0, column=7, padx=10, pady=5)
        
        ctk.CTkButton(view_frame, text="⊞", width=30, height=25,
                    command=lambda: self.change_block_view("grid")).pack(side="left", padx=1)
        ctk.CTkButton(view_frame, text="☰", width=30, height=25,
                    command=lambda: self.change_block_view("list")).pack(side="left", padx=1)
        
        # Statistiques
        stats_frame = ctk.CTkFrame(toolbar_frame)
        stats_frame.grid(row=0, column=2, padx=10, pady=5)
        
        self.block_stats_label = ctk.CTkLabel(stats_frame, text="Chargement...")
        self.block_stats_label.pack(padx=10, pady=5)
        
        # ✅ Frame principal avec zone de blocs en taille Large fixe
        main_block_frame = ctk.CTkFrame(self.content_frame)
        main_block_frame.grid(row=1, column=0, padx=5, pady=2, sticky="nsew")
        main_block_frame.grid_columnconfigure(0, weight=1)
        main_block_frame.grid_rowconfigure(0, weight=1)
        
        # ✅ Canvas pour la zone de blocs avec taille Large fixe
        block_canvas_frame = ctk.CTkFrame(main_block_frame)
        block_canvas_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        block_canvas_frame.grid_columnconfigure(0, weight=1)
        block_canvas_frame.grid_rowconfigure(0, weight=1)
        
        # ✅ Canvas principal des blocs avec taille Large (1600x800)
        self.block_canvas = tk.Canvas(block_canvas_frame, bg='#f0f0f0', 
                                    width=self.block_area_width, 
                                    height=self.block_area_height,
                                    highlightthickness=0)  # ✅ Retirer la bordure
        self.block_canvas.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbars pour la zone de blocs
        block_v_scrollbar = ttk.Scrollbar(block_canvas_frame, orient="vertical", command=self.block_canvas.yview)
        block_h_scrollbar = ttk.Scrollbar(block_canvas_frame, orient="horizontal", command=self.block_canvas.xview)
        self.block_canvas.configure(yscrollcommand=block_v_scrollbar.set, xscrollcommand=block_h_scrollbar.set)
        
        block_v_scrollbar.grid(row=0, column=1, sticky="ns")
        block_h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # ✅ Configuration de la zone de scroll - taille exacte
        self.block_canvas.configure(scrollregion=(0, 0, self.block_area_width, self.block_area_height))
        
        # ✅ Frame pour le contenu des blocs à l'intérieur du canvas
        self.block_content_frame = ctk.CTkFrame(self.block_canvas)
        self.block_canvas_window = self.block_canvas.create_window(0, 0, anchor="nw", window=self.block_content_frame)
        self.block_content_frame.grid_columnconfigure(0, weight=1)
        
        # ✅ Configuration du contenu pour occuper exactement la taille du canvas
        self.block_content_frame.configure(width=self.block_area_width, height=self.block_area_height)
        
        # Bind pour ajuster la taille du frame interne
        self.block_content_frame.bind('<Configure>', self.on_block_frame_configure)
        self.block_canvas.bind('<Configure>', self.on_block_canvas_configure)
        
        # Créer quelques blocs d'exemple si la bibliothèque est vide
        if not self.project_blocks:
            self.create_sample_blocks()
        
        # Afficher les blocs
        self.refresh_block_view()
        
        self.update_status("Module bibliothèque de blocs affiché en taille Large (1600x800)")

    def on_block_frame_configure(self, event):
        """Gérer le redimensionnement du frame de contenu des blocs"""
        # ✅ CORRECTION : Mettre à jour la scrollregion pour la taille exacte du contenu
        canvas_width = self.block_canvas.winfo_width()
        canvas_height = self.block_canvas.winfo_height()
        
        # Ajuster la taille de la scrollregion au contenu réel
        bbox = self.block_canvas.bbox("all")
        if bbox:
            self.block_canvas.configure(scrollregion=bbox)
        else:
            # Si pas de contenu, utiliser la taille exacte du canvas
            self.block_canvas.configure(scrollregion=(0, 0, canvas_width, canvas_height))

    def on_block_canvas_configure(self, event):
        """Gérer le redimensionnement du canvas des blocs"""
        # ✅ CORRECTION : Ajuster la largeur du frame interne exactement au canvas
        canvas_width = event.width
        canvas_height = event.height
        
        # Configurer la fenêtre du canvas pour occuper exactement l'espace
        self.block_canvas.itemconfig(self.block_canvas_window, width=canvas_width, height=canvas_height)
        
        # Mettre à jour la taille du frame de contenu
        self.block_content_frame.configure(width=canvas_width, height=canvas_height)

    def refresh_block_view(self):
        """Rafraîchir l'affichage des blocs - MODIFIÉ pour utiliser le canvas"""
        print(f"🔄 Rafraîchissement de l'affichage des blocs...")
        print(f"   - Nombre de blocs: {len(self.project_blocks)}")
        print(f"   - Mode de vue: {self.block_view_mode}")
        print(f"   - Taille zone: {self.block_area_width}x{self.block_area_height}")
        
        # Nettoyer le contenu actuel
        for widget in self.block_content_frame.winfo_children():
            widget.destroy()
        
        # Filtrer et trier les blocs
        filtered_blocks = self.get_filtered_blocks()
        
        if not filtered_blocks:
            no_blocks_label = ctk.CTkLabel(self.block_content_frame, 
                                        text="Aucun bloc trouvé avec les filtres actuels",
                                        font=ctk.CTkFont(size=14))
            no_blocks_label.pack(pady=50)
        else:
            if self.block_view_mode == "grid":
                self.show_blocks_grid_enhanced(filtered_blocks)
            else:
                self.show_blocks_list_enhanced(filtered_blocks)
        
        self.update_block_stats(filtered_blocks)
        print(f"✅ Rafraîchissement terminé")

    def show_blocks_grid_enhanced(self, blocks):
        """Afficher les blocs en vue grille - MODIFIÉ pour utiliser l'espace Large"""
        # Container pour la grille
        grid_frame = ctk.CTkFrame(self.block_content_frame)
        grid_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Calculer le nombre de colonnes selon la largeur disponible
        card_width = 320
        available_width = self.block_area_width - 40  # 40px pour les marges
        columns = max(1, available_width // (card_width + 15))  # 15px pour l'espacement
        
        # Configurer la grille dynamiquement
        for i in range(columns):
            grid_frame.grid_columnconfigure(i, weight=1)
        
        # Afficher les blocs
        for i, block in enumerate(blocks):
            row = i // columns
            col = i % columns
            self.create_block_card_enhanced(grid_frame, block, row, col, card_width)

    def create_block_card_enhanced(self, parent, block, row, col, card_width):
        """Créer une carte de bloc améliorée pour la vue grille"""
        card = ctk.CTkFrame(parent, width=card_width, height=380)
        card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
        card.grid_propagate(False)
        
        # En-tête avec icône et nom
        header_frame = ctk.CTkFrame(card)
        header_frame.pack(fill="x", padx=12, pady=(12, 8))
        
        icon_label = ctk.CTkLabel(header_frame, text=block.get_category_icon(), 
                                font=ctk.CTkFont(size=28))
        icon_label.pack(side="left", padx=(8, 15))
        
        name_frame = ctk.CTkFrame(header_frame)
        name_frame.pack(side="left", fill="x", expand=True)
        
        name_label = ctk.CTkLabel(name_frame, text=block.name, 
                                font=ctk.CTkFont(size=13, weight="bold"),
                                wraplength=card_width - 80)
        name_label.pack(anchor="w", pady=(5, 0))
        
        # Catégorie et domaine
        cat_domain_text = f"🏷️ {block.category}"
        if block.domain:
            cat_domain_text += f" • 🌐 {block.domain}"
        cat_label = ctk.CTkLabel(card, text=cat_domain_text, 
                                font=ctk.CTkFont(size=10))
        cat_label.pack(padx=12, pady=3)
        
        # Client si spécifié
        if block.client:
            client_label = ctk.CTkLabel(card, text=f"👤 Client: {block.client}", 
                                    font=ctk.CTkFont(size=10),
                                    text_color="#2196F3")
            client_label.pack(padx=12, pady=3)
        
        # Description (adaptée à la largeur)
        desc_text = block.description[:120] + "..." if len(block.description) > 120 else block.description
        desc_label = ctk.CTkLabel(card, text=desc_text, 
                                font=ctk.CTkFont(size=10),
                                wraplength=card_width - 24, height=60)
        desc_label.pack(padx=12, pady=8, fill="x")
        
        # Statistiques détaillées
        stats_frame = ctk.CTkFrame(card)
        stats_frame.pack(fill="x", padx=12, pady=8)
        
        # Ligne 1 : Usage et succès
        stats1_frame = ctk.CTkFrame(stats_frame)
        stats1_frame.pack(fill="x", pady=3)
        
        usage_label = ctk.CTkLabel(stats1_frame, text=f"📊 Utilisé {block.usage_count} fois", 
                                font=ctk.CTkFont(size=9))
        usage_label.pack(side="left", padx=8)
        
        if block.usage_count > 0:
            success_color = "#4CAF50" if block.success_rate > 80 else "#FF9800" if block.success_rate > 60 else "#F44336"
            success_label = ctk.CTkLabel(stats1_frame, text=f"✅ {block.success_rate:.0f}%", 
                                        text_color=success_color, font=ctk.CTkFont(size=9))
            success_label.pack(side="right", padx=8)
        
        # Ligne 2 : Durée et dernière utilisation
        stats2_frame = ctk.CTkFrame(stats_frame)
        stats2_frame.pack(fill="x", pady=3)
        
        if block.average_duration > 0:
            duration_label = ctk.CTkLabel(stats2_frame, text=f"⏱️ {block.average_duration:.0f}j moy.", 
                                        font=ctk.CTkFont(size=9))
            duration_label.pack(side="left", padx=8)
        
        if block.last_used:
            days_ago = (datetime.datetime.now() - block.last_used).days
            last_used_text = f"Il y a {days_ago}j" if days_ago > 0 else "Aujourd'hui"
            last_used_label = ctk.CTkLabel(stats2_frame, text=f"🕐 {last_used_text}", 
                                        font=ctk.CTkFont(size=9))
            last_used_label.pack(side="right", padx=8)
        
        # Ligne 3 : Contenu du bloc
        if block.nodes or block.tasks:
            content_frame = ctk.CTkFrame(stats_frame)
            content_frame.pack(fill="x", pady=3)
            
            if block.nodes:
                nodes_count = self.count_nodes_in_structure(block.nodes) if hasattr(self, 'count_nodes_in_structure') else 1
                nodes_label = ctk.CTkLabel(content_frame, text=f"🌳 {nodes_count} nœuds", 
                                        font=ctk.CTkFont(size=9))
                nodes_label.pack(side="left", padx=8)
            
            if block.tasks:
                tasks_label = ctk.CTkLabel(content_frame, text=f"✅ {len(block.tasks)} tâches", 
                                        font=ctk.CTkFont(size=9))
                tasks_label.pack(side="right", padx=8)
        
        # Tags (limités à 3 pour l'espace)
        if block.tags:
            tags_text = " ".join([f"#{tag}" for tag in block.tags[:3]])  # Max 3 tags
            if len(block.tags) > 3:
                tags_text += f" +{len(block.tags) - 3}"
            tags_label = ctk.CTkLabel(card, text=tags_text, 
                                    text_color="#2196F3", font=ctk.CTkFont(size=9))
            tags_label.pack(padx=12, pady=5)
        
        # Boutons d'action (plus compacts et mieux organisés)
        buttons_frame = ctk.CTkFrame(card)
        buttons_frame.pack(side="bottom", fill="x", padx=12, pady=12)
        
        # Ligne 1 : Actions principales
        main_actions = ctk.CTkFrame(buttons_frame)
        main_actions.pack(fill="x", pady=(0, 5))
        
        ctk.CTkButton(main_actions, text="🔍 Détails", width=70, height=28,
                    command=lambda: self.view_block_details(block)).pack(side="left", padx=2)
        ctk.CTkButton(main_actions, text="📥 Importer", width=70, height=28,
                    command=lambda: self.import_block_to_project(block)).pack(side="left", padx=2)
        ctk.CTkButton(main_actions, text="✏️ Éditer", width=60, height=28,
                    command=lambda: self.edit_block(block)).pack(side="right", padx=2)
        
        # Ligne 2 : Actions secondaires
        secondary_actions = ctk.CTkFrame(buttons_frame)
        secondary_actions.pack(fill="x")
        
        ctk.CTkButton(secondary_actions, text="📝 Tâches", width=65, height=25,
                    command=lambda: self.edit_block_tasks(block)).pack(side="left", padx=2)
        ctk.CTkButton(secondary_actions, text="🗑️ Suppr.", width=60, height=25,
                    command=lambda: self.delete_block(block)).pack(side="right", padx=2)

    def show_blocks_list_enhanced(self, blocks):
        """Afficher les blocs en vue liste - MODIFIÉ pour utiliser l'espace Large"""
        # En-têtes avec largeur adaptée à la zone Large
        headers_frame = ctk.CTkFrame(self.block_content_frame)
        headers_frame.pack(fill="x", padx=10, pady=5)
        
        # ✅ Configuration des colonnes pour la largeur Large
        headers_frame.grid_columnconfigure(0, weight=2, minsize=220)  # Nom - plus large
        headers_frame.grid_columnconfigure(1, weight=1, minsize=120)  # Catégorie
        headers_frame.grid_columnconfigure(2, weight=1, minsize=100)  # Domaine
        headers_frame.grid_columnconfigure(3, weight=1, minsize=80)   # Usage
        headers_frame.grid_columnconfigure(4, weight=1, minsize=80)   # Succès
        headers_frame.grid_columnconfigure(5, weight=1, minsize=100)  # Durée
        headers_frame.grid_columnconfigure(6, weight=1, minsize=120)  # Dernière util.
        headers_frame.grid_columnconfigure(7, weight=2, minsize=200)  # Description
        headers_frame.grid_columnconfigure(8, weight=1, minsize=150)  # Actions
        
        headers = ["Nom du Bloc", "Catégorie", "Domaine", "Usage", "Succès", "Durée Moy.", "Dernière Util.", "Description", "Actions"]
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(headers_frame, text=header, 
                            font=ctk.CTkFont(size=12, weight="bold"))
            # ✅ CORRECTION : Alignement cohérent des en-têtes
            if i == 0:  # Nom à gauche
                label.grid(row=0, column=i, padx=5, pady=10, sticky="w")
            else:  # Autres colonnes centrées
                label.grid(row=0, column=i, padx=5, pady=10, sticky="ew")
        
        # ✅ Ligne de séparation sous les en-têtes
        separator = ctk.CTkFrame(self.block_content_frame, height=2)
        separator.pack(fill="x", padx=10, pady=(0, 5))
        
        # Zone scrollable pour les lignes de blocs
        table_scroll = ctk.CTkScrollableFrame(self.block_content_frame, 
                                            height=max(500, self.block_area_height - 150))
        table_scroll.pack(fill="x", padx=10, pady=5)
        table_scroll.grid_columnconfigure(0, weight=1)
        
        # Blocs
        for i, block in enumerate(blocks):
            self.create_block_row_enhanced(table_scroll, block, i)

    def create_block_row_enhanced(self, parent, block, row_index):
        """Créer une ligne de bloc améliorée pour la vue liste"""
        row_frame = ctk.CTkFrame(parent)
        row_frame.pack(fill="x", padx=5, pady=2)
        
        # ✅ Configuration des colonnes identique aux en-têtes
        row_frame.grid_columnconfigure(0, weight=2, minsize=220)  # Nom
        row_frame.grid_columnconfigure(1, weight=1, minsize=120)  # Catégorie
        row_frame.grid_columnconfigure(2, weight=1, minsize=100)  # Domaine
        row_frame.grid_columnconfigure(3, weight=1, minsize=80)   # Usage
        row_frame.grid_columnconfigure(4, weight=1, minsize=80)   # Succès
        row_frame.grid_columnconfigure(5, weight=1, minsize=100)  # Durée
        row_frame.grid_columnconfigure(6, weight=1, minsize=120)  # Dernière util.
        row_frame.grid_columnconfigure(7, weight=2, minsize=200)  # Description
        row_frame.grid_columnconfigure(8, weight=1, minsize=150)  # Actions
        
        # Nom avec icône
        name_text = f"{block.get_category_icon()} {block.name}"
        name_label = ctk.CTkLabel(row_frame, text=name_text, anchor="w")
        name_label.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        # Catégorie
        cat_label = ctk.CTkLabel(row_frame, text=block.category)
        cat_label.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Domaine
        domain_label = ctk.CTkLabel(row_frame, text=block.domain or "-")
        domain_label.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        # Usage
        usage_label = ctk.CTkLabel(row_frame, text=str(block.usage_count))
        usage_label.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
        
        # Succès
        if block.usage_count > 0:
            success_color = "#4CAF50" if block.success_rate > 80 else "#FF9800" if block.success_rate > 60 else "#F44336"
            success_text = f"{block.success_rate:.0f}%"
        else:
            success_color = "#666666"
            success_text = "N/A"
        success_label = ctk.CTkLabel(row_frame, text=success_text, text_color=success_color)
        success_label.grid(row=0, column=4, padx=5, pady=5, sticky="ew")
        
        # Durée moyenne
        duration_text = f"{block.average_duration:.0f}j" if block.average_duration > 0 else "N/A"
        duration_label = ctk.CTkLabel(row_frame, text=duration_text)
        duration_label.grid(row=0, column=5, padx=5, pady=5, sticky="ew")
        
        # Dernière utilisation
        if block.last_used:
            days_ago = (datetime.datetime.now() - block.last_used).days
            last_used_text = f"Il y a {days_ago}j" if days_ago > 0 else "Aujourd'hui"
        else:
            last_used_text = "Jamais"
        last_used_label = ctk.CTkLabel(row_frame, text=last_used_text)
        last_used_label.grid(row=0, column=6, padx=5, pady=5, sticky="ew")
        
        # Description (tronquée)
        desc_text = block.description[:80] + "..." if len(block.description) > 80 else block.description
        desc_label = ctk.CTkLabel(row_frame, text=desc_text, wraplength=180)
        desc_label.grid(row=0, column=7, padx=5, pady=5, sticky="ew")
        
        # Actions
        actions_frame = ctk.CTkFrame(row_frame)
        actions_frame.grid(row=0, column=8, padx=5, pady=5, sticky="ew")
        
        # ✅ Configuration pour centrer les boutons
        actions_frame.grid_columnconfigure(0, weight=1)
        actions_frame.grid_columnconfigure(1, weight=1)
        actions_frame.grid_columnconfigure(2, weight=1)
        actions_frame.grid_columnconfigure(3, weight=1)
        actions_frame.grid_columnconfigure(4, weight=1)
        
        ctk.CTkButton(actions_frame, text="🔍", width=25, height=25,
                    command=lambda: self.view_block_details(block)).grid(row=0, column=0, padx=1)
        ctk.CTkButton(actions_frame, text="📥", width=25, height=25,
                    command=lambda: self.import_block_to_project(block)).grid(row=0, column=1, padx=1)
        ctk.CTkButton(actions_frame, text="📝", width=25, height=25,
                    command=lambda: self.edit_block_tasks(block)).grid(row=0, column=2, padx=1)
        ctk.CTkButton(actions_frame, text="✏️", width=25, height=25,
                    command=lambda: self.edit_block(block)).grid(row=0, column=3, padx=1)
        ctk.CTkButton(actions_frame, text="🗑️", width=25, height=25,
                    command=lambda: self.delete_block(block)).grid(row=0, column=4, padx=1)
    def create_sample_blocks(self):
        """Créer quelques blocs d'exemple"""
        sample_blocks = [
            ProjectBlock(
                name="Pipeline CI/CD Standard",
                description="Pipeline complet avec tests automatisés, build et déploiement",
                category="CI/CD",
                domain="Software",
                client=""
            ),
            ProjectBlock(
                name="Processus de Validation Embarqué",
                description="Tests HIL, SIL et validation matérielle pour systèmes embarqués",
                category="Testing",
                domain="Embedded",
                client=""
            ),
            ProjectBlock(
                name="Phase d'Intégration IoT",
                description="Intégration capteurs, communication et cloud pour projets IoT",
                category="Integration",
                domain="IoT",
                client=""
            ),
            ProjectBlock(
                name="Documentation Technique",
                description="Template complet de documentation projet avec livrables",
                category="Documentation",
                domain="General",
                client=""
            ),
            ProjectBlock(
                name="Tests de Sécurité",
                description="Audit sécurité, tests de pénétration et validation",
                category="Security",
                domain="Web",
                client=""
            )
        ]
        
        # Ajouter des données d'usage fictives
        for i, block in enumerate(sample_blocks):
            block.usage_count = (i + 1) * 3
            block.success_rate = 85 + (i * 3)
            block.average_duration = 10 + (i * 5)
            block.tags = ["standard", "testé", "fiable"]
            
            # Ajouter quelques tâches d'exemple
            block.tasks = [
                {"title": f"Tâche 1 - {block.name}", "description": "Description de la tâche", "priority": "Moyenne"},
                {"title": f"Tâche 2 - {block.name}", "description": "Description de la tâche", "priority": "Critique"}
            ]
            
            # Historique d'usage
            for j in range(block.usage_count):
                block.usage_history.append({
                    'project_name': f"Projet-{j+1}",
                    'date': (datetime.datetime.now() - datetime.timedelta(days=j*30)).isoformat(),
                    'duration_days': block.average_duration + (j-1),
                    'success': j % 4 != 0,  # 3/4 de succès
                    'notes': f"Utilisation {j+1}"
                })
        
        self.project_blocks.extend(sample_blocks)
        self.save_project_blocks()

    def load_project_blocks(self):
        """Charger les blocs depuis le fichier de sauvegarde"""
        blocks_file = os.path.join(self.blocks_storage_path, "project_blocks.json")
        if os.path.exists(blocks_file):
            try:
                with open(blocks_file, 'r', encoding='utf-8') as f:
                    blocks_data = json.load(f)
                
                self.project_blocks = []
                for block_data in blocks_data:
                    block = ProjectBlock.from_dict(block_data)
                    self.project_blocks.append(block)
                    
            except Exception as e:
                print(f"Erreur lors du chargement des blocs : {str(e)}")
                self.project_blocks = []

    def save_project_blocks(self):
        """Sauvegarder les blocs dans un fichier"""
        blocks_file = os.path.join(self.blocks_storage_path, "project_blocks.json")
        try:
            blocks_data = [block.to_dict() for block in self.project_blocks]
            with open(blocks_file, 'w', encoding='utf-8') as f:
                json.dump(blocks_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des blocs : {str(e)}")

    def change_block_view(self, view_mode):
        """Changer le mode de vue des blocs"""
        self.block_view_mode = view_mode
        self.refresh_block_view()

    def apply_block_filters(self, *args):
        """Appliquer les filtres et rafraîchir la vue"""
        self.refresh_block_view()

    def refresh_block_view(self):
        """Rafraîchir l'affichage des blocs"""
        # Nettoyer le contenu actuel
        for widget in self.block_content_frame.winfo_children():
            widget.destroy()
        
        # Filtrer et trier les blocs
        filtered_blocks = self.get_filtered_blocks()
        
        if not filtered_blocks:
            no_blocks_label = ctk.CTkLabel(self.block_content_frame, 
                                        text="Aucun bloc trouvé avec les filtres actuels",
                                        font=ctk.CTkFont(size=14))
            no_blocks_label.pack(pady=50)
        else:
            if self.block_view_mode == "grid":
                self.show_blocks_grid(filtered_blocks)
            else:
                self.show_blocks_list(filtered_blocks)
        
        self.update_block_stats(filtered_blocks)

    def get_filtered_blocks(self):
        """Obtenir les blocs filtrés et triés"""
        filtered = self.project_blocks.copy()
        
        # Filtre par catégorie
        if hasattr(self, 'block_category_filter') and self.block_category_filter.get() != "Toutes":
            filtered = [b for b in filtered if b.category == self.block_category_filter.get()]
        
        # Filtre par domaine
        if hasattr(self, 'block_domain_filter') and self.block_domain_filter.get() != "Tous":
            filtered = [b for b in filtered if b.domain == self.block_domain_filter.get()]
        
        # Tri
        sort_option = getattr(self, 'block_sort_filter', None)
        if sort_option:
            sort_key = sort_option.get() if hasattr(sort_option, 'get') else "Nom"
            
            if sort_key == "Nom":
                filtered.sort(key=lambda x: x.name.lower())
            elif sort_key == "Date création":
                filtered.sort(key=lambda x: x.created_date, reverse=True)
            elif sort_key == "Usage":
                filtered.sort(key=lambda x: x.usage_count, reverse=True)
            elif sort_key == "Succès":
                filtered.sort(key=lambda x: x.success_rate, reverse=True)
            elif sort_key == "Dernière utilisation":
                filtered.sort(key=lambda x: x.last_used or datetime.datetime.min, reverse=True)
        
        return filtered

    def show_blocks_grid(self, blocks):
        """Afficher les blocs en vue grille"""
        # Container pour la grille
        grid_frame = ctk.CTkFrame(self.block_content_frame)
        grid_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Configurer la grille (3 colonnes)
        for i in range(3):
            grid_frame.grid_columnconfigure(i, weight=1)
        
        # Afficher les blocs
        for i, block in enumerate(blocks):
            row = i // 3
            col = i % 3
            self.create_block_card(grid_frame, block, row, col)

    def create_block_card(self, parent, block, row, col):
        """Créer une carte de bloc pour la vue grille"""
        card = ctk.CTkFrame(parent, width=280, height=320)
        card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
        card.grid_propagate(False)
        
        # En-tête avec icône et nom
        header_frame = ctk.CTkFrame(card)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        icon_label = ctk.CTkLabel(header_frame, text=block.get_category_icon(), 
                                font=ctk.CTkFont(size=24))
        icon_label.pack(side="left", padx=(5, 10))
        
        name_label = ctk.CTkLabel(header_frame, text=block.name, 
                                font=ctk.CTkFont(size=12, weight="bold"),
                                wraplength=200)
        name_label.pack(side="left", anchor="w")
        
        # Catégorie et domaine
        cat_domain_text = f"🏷️ {block.category}"
        if block.domain:
            cat_domain_text += f" • 🌐 {block.domain}"
        cat_label = ctk.CTkLabel(card, text=cat_domain_text, 
                                font=ctk.CTkFont(size=10))
        cat_label.pack(padx=10, pady=2)
        
        # Client si spécifié
        if block.client:
            client_label = ctk.CTkLabel(card, text=f"👤 Client: {block.client}", 
                                    font=ctk.CTkFont(size=10))
            client_label.pack(padx=10, pady=2)
        
        # Description
        desc_label = ctk.CTkLabel(card, text=block.description, 
                                font=ctk.CTkFont(size=10),
                                wraplength=250, height=60)
        desc_label.pack(padx=10, pady=5, fill="x")
        
        # Statistiques
        stats_frame = ctk.CTkFrame(card)
        stats_frame.pack(fill="x", padx=10, pady=5)
        
        # Ligne 1 : Usage et succès
        stats1_frame = ctk.CTkFrame(stats_frame)
        stats1_frame.pack(fill="x", pady=2)
        
        usage_label = ctk.CTkLabel(stats1_frame, text=f"📊 Utilisé {block.usage_count} fois", 
                                font=ctk.CTkFont(size=9))
        usage_label.pack(side="left", padx=5)
        
        if block.usage_count > 0:
            success_color = "#4CAF50" if block.success_rate > 80 else "#FF9800" if block.success_rate > 60 else "#F44336"
            success_label = ctk.CTkLabel(stats1_frame, text=f"✅ {block.success_rate:.0f}%", 
                                        text_color=success_color, font=ctk.CTkFont(size=9))
            success_label.pack(side="right", padx=5)
        
        # Ligne 2 : Durée et dernière utilisation
        stats2_frame = ctk.CTkFrame(stats_frame)
        stats2_frame.pack(fill="x", pady=2)
        
        if block.average_duration > 0:
            duration_label = ctk.CTkLabel(stats2_frame, text=f"⏱️ {block.average_duration:.0f}j moy.", 
                                        font=ctk.CTkFont(size=9))
            duration_label.pack(side="left", padx=5)
        
        if block.last_used:
            days_ago = (datetime.datetime.now() - block.last_used).days
            last_used_text = f"Il y a {days_ago}j" if days_ago > 0 else "Aujourd'hui"
            last_used_label = ctk.CTkLabel(stats2_frame, text=f"🕐 {last_used_text}", 
                                        font=ctk.CTkFont(size=9))
            last_used_label.pack(side="right", padx=5)
        
        # Tags
        if block.tags:
            tags_text = " ".join([f"#{tag}" for tag in block.tags[:3]])  # Max 3 tags
            tags_label = ctk.CTkLabel(card, text=tags_text, 
                                    text_color="#2196F3", font=ctk.CTkFont(size=9))
            tags_label.pack(padx=10, pady=2)
        
        # Boutons d'action
        buttons_frame = ctk.CTkFrame(card)
        buttons_frame.pack(side="bottom", fill="x", padx=10, pady=10)
        
        ctk.CTkButton(buttons_frame, text="🔍 Voir", width=50, height=25,
                    command=lambda: self.view_block_details(block)).pack(side="left", padx=1)
        ctk.CTkButton(buttons_frame, text="📥 Importer", width=60, height=25,
                    command=lambda: self.import_block_to_project(block)).pack(side="left", padx=1)
        ctk.CTkButton(buttons_frame, text="✏️", width=30, height=25,
                    command=lambda: self.edit_block(block)).pack(side="left", padx=1)
        ctk.CTkButton(buttons_frame, text="🗑️", width=30, height=25,
                    command=lambda: self.delete_block(block)).pack(side="right", padx=1)

    def show_blocks_list(self, blocks):
        """Afficher les blocs en vue liste"""
        # En-têtes
        headers_frame = ctk.CTkFrame(self.block_content_frame)
        headers_frame.pack(fill="x", padx=10, pady=5)
        headers_frame.grid_columnconfigure(0, weight=2)  # Nom
        headers_frame.grid_columnconfigure(1, weight=1)  # Catégorie
        headers_frame.grid_columnconfigure(2, weight=1)  # Domaine
        headers_frame.grid_columnconfigure(3, weight=1)  # Usage
        headers_frame.grid_columnconfigure(4, weight=1)  # Succès
        headers_frame.grid_columnconfigure(5, weight=1)  # Durée
        headers_frame.grid_columnconfigure(6, weight=1)  # Actions
        
        headers = ["Nom du Bloc", "Catégorie", "Domaine", "Usage", "Succès", "Durée Moy.", "Actions"]
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(headers_frame, text=header, 
                                font=ctk.CTkFont(size=12, weight="bold"))
            label.grid(row=0, column=i, padx=5, pady=10, sticky="w")
        
        # Blocs
        for i, block in enumerate(blocks):
            self.create_block_row(i + 1, block)

    def create_block_row(self, row, block):
        """Créer une ligne de bloc pour la vue liste"""
        row_frame = ctk.CTkFrame(self.block_content_frame)
        row_frame.pack(fill="x", padx=10, pady=2)
        row_frame.grid_columnconfigure(0, weight=2)
        row_frame.grid_columnconfigure(1, weight=1)
        row_frame.grid_columnconfigure(2, weight=1)
        row_frame.grid_columnconfigure(3, weight=1)
        row_frame.grid_columnconfigure(4, weight=1)
        row_frame.grid_columnconfigure(5, weight=1)
        row_frame.grid_columnconfigure(6, weight=1)
        
        # Nom avec icône
        name_text = f"{block.get_category_icon()} {block.name}"
        name_label = ctk.CTkLabel(row_frame, text=name_text, anchor="w")
        name_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        # Catégorie
        cat_label = ctk.CTkLabel(row_frame, text=block.category)
        cat_label.grid(row=0, column=1, padx=5, pady=5)
        
        # Domaine
        domain_label = ctk.CTkLabel(row_frame, text=block.domain or "-")
        domain_label.grid(row=0, column=2, padx=5, pady=5)
        
        # Usage
        usage_label = ctk.CTkLabel(row_frame, text=str(block.usage_count))
        usage_label.grid(row=0, column=3, padx=5, pady=5)
        
        # Succès
        if block.usage_count > 0:
            success_color = "#4CAF50" if block.success_rate > 80 else "#FF9800" if block.success_rate > 60 else "#F44336"
            success_text = f"{block.success_rate:.0f}%"
        else:
            success_color = "#666666"
            success_text = "N/A"
        success_label = ctk.CTkLabel(row_frame, text=success_text, text_color=success_color)
        success_label.grid(row=0, column=4, padx=5, pady=5)
        
        # Durée moyenne
        duration_text = f"{block.average_duration:.0f}j" if block.average_duration > 0 else "N/A"
        duration_label = ctk.CTkLabel(row_frame, text=duration_text)
        duration_label.grid(row=0, column=5, padx=5, pady=5)
        
        # Actions
        actions_frame = ctk.CTkFrame(row_frame)
        actions_frame.grid(row=0, column=6, padx=5, pady=5)
        
        ctk.CTkButton(actions_frame, text="🔍", width=25, height=25,
                    command=lambda: self.view_block_details(block)).pack(side="left", padx=1)
        ctk.CTkButton(actions_frame, text="📥", width=25, height=25,
                    command=lambda: self.import_block_to_project(block)).pack(side="left", padx=1)
        ctk.CTkButton(actions_frame, text="✏️", width=25, height=25,
                    command=lambda: self.edit_block(block)).pack(side="left", padx=1)
        ctk.CTkButton(actions_frame, text="🗑️", width=25, height=25,
                    command=lambda: self.delete_block(block)).pack(side="left", padx=1)

    def update_block_stats(self, filtered_blocks):
        """Mettre à jour les statistiques des blocs"""
        total = len(self.project_blocks)
        filtered_count = len(filtered_blocks)
        total_usage = sum(block.usage_count for block in filtered_blocks)
        avg_success = sum(block.success_rate for block in filtered_blocks if block.usage_count > 0) / len([b for b in filtered_blocks if b.usage_count > 0]) if [b for b in filtered_blocks if b.usage_count > 0] else 0
        
        stats_text = f"Total: {total} | Affichés: {filtered_count} | Usage total: {total_usage} | Succès moy: {avg_success:.0f}%"
        
        if hasattr(self, 'block_stats_label'):
            self.block_stats_label.configure(text=stats_text)

    def create_new_block(self):
        """Créer un nouveau bloc vide"""
        self.edit_block(None)

    def create_block_from_tree(self):
        """Créer un bloc à partir de l'arbre actuel"""
        if not hasattr(self, 'tree_nodes') or not self.tree_nodes:
            messagebox.showwarning("Avertissement", "Aucun diagramme en arbre trouvé!")
            return
        
        if not hasattr(self, 'selected_tree_node') or not self.selected_tree_node:
            messagebox.showwarning("Avertissement", "Sélectionnez d'abord un nœud racine dans l'arbre!")
            return
        
        # Demander les informations du bloc
        dialog = ctk.CTkToplevel(self)
        dialog.title("Créer un Bloc depuis l'Arbre")
        dialog.geometry("500x400")
        dialog.transient(self)
        dialog.grab_set()
        
        # Centrer la fenêtre
        dialog.geometry("+%d+%d" % (
            self.winfo_rootx() + 100,
            self.winfo_rooty() + 100
        ))
        
        # Frame principal
        main_frame = ctk.CTkScrollableFrame(dialog)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Informations du nœud sélectionné
        info_frame = ctk.CTkFrame(main_frame)
        info_frame.pack(fill='x', pady=(0, 20))
        
        ctk.CTkLabel(info_frame, text="🌳 Nœud racine sélectionné", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        ctk.CTkLabel(info_frame, text=f"Nœud: {self.selected_tree_node.text}").pack(anchor='w', padx=10)
        
        # Compter les descendants
        descendants = self.selected_tree_node.get_all_descendants()
        ctk.CTkLabel(info_frame, text=f"Sous-nœuds inclus: {len(descendants)}").pack(anchor='w', padx=10, pady=(0, 10))
        
        # Nom du bloc
        ctk.CTkLabel(main_frame, text="Nom du bloc:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        name_entry = ctk.CTkEntry(main_frame, width=400)
        name_entry.pack(fill='x', pady=(0, 10))
        name_entry.insert(0, f"Bloc - {self.selected_tree_node.text}")
        
        # Description
        ctk.CTkLabel(main_frame, text="Description:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        desc_textbox = ctk.CTkTextbox(main_frame, height=80, width=400)
        desc_textbox.pack(fill='x', pady=(0, 10))
        desc_textbox.insert("1.0", f"Bloc créé à partir du nœud '{self.selected_tree_node.text}' et ses {len(descendants)} sous-nœuds.")
        
        # Catégorie
        ctk.CTkLabel(main_frame, text="Catégorie:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        category_var = tk.StringVar(value="Process")
        categories = ["Process", "Testing", "CI/CD", "Hardware", "Software", "Integration", "Validation", "Documentation", "Planning", "Quality", "Security", "General"]
        category_menu = ctk.CTkOptionMenu(main_frame, values=categories, variable=category_var)
        category_menu.pack(fill='x', pady=(0, 10))
        
        # Domaine
        ctk.CTkLabel(main_frame, text="Domaine:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        domain_var = tk.StringVar(value="General")
        domains = ["General", "Embedded", "Web", "Mobile", "IoT", "Desktop", "Cloud", "AI/ML", "Data"]
        domain_menu = ctk.CTkOptionMenu(main_frame, values=domains, variable=domain_var)
        domain_menu.pack(fill='x', pady=(0, 10))
        
        # Client
        ctk.CTkLabel(main_frame, text="Client (optionnel):", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        client_entry = ctk.CTkEntry(main_frame, width=400, placeholder_text="Nom du client spécifique")
        client_entry.pack(fill='x', pady=(0, 10))
        
        # Tags
        ctk.CTkLabel(main_frame, text="Tags (séparés par des virgules):", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        tags_entry = ctk.CTkEntry(main_frame, width=400, placeholder_text="standard, testé, éprouvé")
        tags_entry.pack(fill='x', pady=(0, 20))
        
        # Variable pour le résultat
        result = {"saved": False}
        
        def save_block():
            if not name_entry.get().strip():
                messagebox.showerror("Erreur", "Le nom du bloc est obligatoire!")
                return
            
            # Créer le bloc
            new_block = ProjectBlock(
                name=name_entry.get().strip(),
                description=desc_textbox.get("1.0", "end-1c"),
                category=category_var.get(),
                domain=domain_var.get(),
                client=client_entry.get().strip()
            )
            
            # Traiter les tags
            tags_text = tags_entry.get().strip()
            if tags_text:
                new_block.tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]
            
            # Sauvegarder les nœuds
            new_block.nodes = self.serialize_tree_branch(self.selected_tree_node)
            
            # Chercher les tâches liées
            if hasattr(self, 'tasks'):
                linked_tasks = [task for task in self.tasks if task.linked_node and 
                            (task.linked_node == self.selected_tree_node or task.linked_node in descendants)]
                new_block.tasks = [task.to_dict() for task in linked_tasks]
            
            # Ajouter à la bibliothèque
            self.project_blocks.append(new_block)
            self.save_project_blocks()
            
            # Enregistrement dans le journal
            if hasattr(self, 'add_automatic_log_entry'):
                self.add_automatic_log_entry(
                    title=f"Bloc créé : '{new_block.name}'",
                    description=f"Nouveau bloc créé depuis l'arbre.\nNœuds inclus: {len(new_block.nodes)}\nTâches liées: {len(new_block.tasks)}",
                    category="Block"
                )
            
            result["saved"] = True
            dialog.destroy()
        
        def cancel():
            dialog.destroy()
        
        # Boutons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill='x', pady=10)
        
        ctk.CTkButton(button_frame, text="Annuler", command=cancel).pack(side='right', padx=(5, 0))
        ctk.CTkButton(button_frame, text="Créer le Bloc", command=save_block).pack(side='right')
        
        # Focus sur le nom
        name_entry.focus()
        
        # Attendre la fermeture
        dialog.wait_window()
        
        # Rafraîchir l'affichage si sauvegardé
        if result["saved"]:
            self.refresh_block_view()
            self.update_status("Bloc créé depuis l'arbre")

    def serialize_tree_branch(self, root_node):
        """Sérialiser une branche d'arbre en format JSON"""
        def node_to_dict(node):
            return {
                'text': node.text,
                'x': node.x,
                'y': node.y,
                'color': node.color,
                'border_color': node.border_color,
                'children': [node_to_dict(child) for child in node.children]
            }
        
        return node_to_dict(root_node)

    def view_block_details(self, block):
        """Afficher les détails complets d'un bloc"""
        # Créer une nouvelle fenêtre
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Détails - {block.name}")
        dialog.geometry("800x700")
        dialog.transient(self)
        
        # Frame principal avec onglets
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # En-tête
        header_frame = ctk.CTkFrame(main_frame)
        header_frame.pack(fill="x", pady=(0, 20))
        
        # Titre avec icône
        title_frame = ctk.CTkFrame(header_frame)
        title_frame.pack(fill="x", padx=10, pady=10)
        
        icon_label = ctk.CTkLabel(title_frame, text=block.get_category_icon(), 
                                font=ctk.CTkFont(size=32))
        icon_label.pack(side="left", padx=(10, 15))
        
        info_frame = ctk.CTkFrame(title_frame)
        info_frame.pack(side="left", fill="x", expand=True)
        
        name_label = ctk.CTkLabel(info_frame, text=block.name, 
                                font=ctk.CTkFont(size=18, weight="bold"))
        name_label.pack(anchor="w", pady=(5, 0))
        
        meta_text = f"🏷️ {block.category}"
        if block.domain:
            meta_text += f" • 🌐 {block.domain}"
        if block.client:
            meta_text += f" • 👤 {block.client}"
        
        meta_label = ctk.CTkLabel(info_frame, text=meta_text, 
                                font=ctk.CTkFont(size=12))
        meta_label.pack(anchor="w", pady=(0, 5))
        
        # Statistiques rapides
        stats_frame = ctk.CTkFrame(header_frame)
        stats_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        stats_text = f"📊 Utilisé {block.usage_count} fois"
        if block.usage_count > 0:
            stats_text += f" • ✅ {block.success_rate:.0f}% de succès"
            if block.average_duration > 0:
                stats_text += f" • ⏱️ {block.average_duration:.0f}j en moyenne"
        
        stats_label = ctk.CTkLabel(stats_frame, text=stats_text)
        stats_label.pack(padx=10, pady=5)
        
        # Contenu avec onglets simulés
        content_frame = ctk.CTkScrollableFrame(main_frame)
        content_frame.pack(fill="both", expand=True)
        
        # Description
        desc_section = ctk.CTkFrame(content_frame)
        desc_section.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(desc_section, text="📝 Description", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        desc_text = ctk.CTkTextbox(desc_section, height=80)
        desc_text.pack(fill="x", padx=10, pady=(0, 10))
        desc_text.insert("1.0", block.description)
        desc_text.configure(state="disabled")
        
        # Nœuds inclus
        if block.nodes:
            nodes_section = ctk.CTkFrame(content_frame)
            nodes_section.pack(fill="x", padx=10, pady=10)
            
            ctk.CTkLabel(nodes_section, text=f"🌳 Structure ({self.count_nodes_in_structure(block.nodes)} nœuds)", 
                        font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
            
            nodes_text = ctk.CTkTextbox(nodes_section, height=100)
            nodes_text.pack(fill="x", padx=10, pady=(0, 10))
            nodes_text.insert("1.0", self.format_node_structure(block.nodes))
            nodes_text.configure(state="disabled")
        
        # Tâches
        if block.tasks:
            tasks_section = ctk.CTkFrame(content_frame)
            tasks_section.pack(fill="x", padx=10, pady=10)
            
            ctk.CTkLabel(tasks_section, text=f"✅ Tâches templates ({len(block.tasks)})", 
                        font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
            
            for i, task in enumerate(block.tasks[:5]):  # Montrer max 5 tâches
                task_name = task.get('title', 'Tâche sans nom') if isinstance(task, dict) else str(task)
                task_frame = ctk.CTkFrame(tasks_section)
                task_frame.pack(fill="x", padx=20, pady=2)
                
                ctk.CTkLabel(task_frame, text=f"• {task_name}").pack(anchor="w", padx=10, pady=5)
            
            if len(block.tasks) > 5:
                ctk.CTkLabel(tasks_section, text=f"... et {len(block.tasks) - 5} autres tâches").pack(anchor="w", padx=20, pady=5)
        
        # Historique d'utilisation
        if block.usage_history:
            history_section = ctk.CTkFrame(content_frame)
            history_section.pack(fill="x", padx=10, pady=10)
            
            ctk.CTkLabel(history_section, text=f"📈 Historique d'utilisation ({len(block.usage_history)} projets)", 
                        font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
            
            # Afficher les 5 dernières utilisations
            recent_usage = sorted(block.usage_history, key=lambda x: x.get('date', ''), reverse=True)[:5]
            
            for usage in recent_usage:
                usage_frame = ctk.CTkFrame(history_section)
                usage_frame.pack(fill="x", padx=20, pady=2)
                
                project_name = usage.get('project_name', 'Projet inconnu')
                date_str = usage.get('date', '')
                if date_str:
                    try:
                        date_obj = datetime.datetime.fromisoformat(date_str)
                        date_display = date_obj.strftime('%d/%m/%Y')
                    except:
                        date_display = date_str
                else:
                    date_display = "Date inconnue"
                
                success_icon = "✅" if usage.get('success', True) else "❌"
                duration = usage.get('duration_days', 0)
                duration_text = f" ({duration}j)" if duration > 0 else ""
                
                usage_text = f"{success_icon} {project_name} - {date_display}{duration_text}"
                ctk.CTkLabel(usage_frame, text=usage_text).pack(anchor="w", padx=10, pady=5)
        
        # Tags
        if block.tags:
            tags_section = ctk.CTkFrame(content_frame)
            tags_section.pack(fill="x", padx=10, pady=10)
            
            ctk.CTkLabel(tags_section, text="🏷️ Tags", 
                        font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
            
            tags_text = " ".join([f"#{tag}" for tag in block.tags])
            ctk.CTkLabel(tags_section, text=tags_text, 
                        text_color="#2196F3").pack(anchor="w", padx=20, pady=(0, 10))
        
        # Boutons d'action
        buttons_frame = ctk.CTkFrame(main_frame)
        buttons_frame.pack(fill="x", pady=(20, 0))
        
        ctk.CTkButton(buttons_frame, text="📥 Importer dans le Projet", 
                    command=lambda: [dialog.destroy(), self.import_block_to_project(block)]).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(buttons_frame, text="📝 Éditer Tâches", 
                    command=lambda: [dialog.destroy(), self.edit_block_tasks(block)]).pack(side="left", padx=5, pady=10)
        ctk.CTkButton(buttons_frame, text="✏️ Modifier", 
                    command=lambda: [dialog.destroy(), self.edit_block(block)]).pack(side="left", padx=5, pady=10)
        ctk.CTkButton(buttons_frame, text="Fermer", 
                    command=dialog.destroy).pack(side="right", padx=10, pady=10)


    def count_nodes_in_structure(self, node_structure):
        """Compter le nombre de nœuds dans une structure"""
        if isinstance(node_structure, dict):
            count = 1  # Le nœud lui-même
            for child in node_structure.get('children', []):
                count += self.count_nodes_in_structure(child)
            return count
        return 1

    def format_node_structure(self, node_structure, indent=0):
        """Formater la structure des nœuds pour affichage"""
        if isinstance(node_structure, dict):
            text = "  " * indent + f"• {node_structure.get('text', 'Nœud')}\n"
            for child in node_structure.get('children', []):
                text += self.format_node_structure(child, indent + 1)
            return text
        return f"  " * indent + f"• {str(node_structure)}\n"

    def import_block_to_project(self, block):
        """Importer un bloc dans le projet actuel"""
        # Demander confirmation et options d'import
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Importer - {block.name}")
        dialog.geometry("600x500")
        dialog.transient(self)
        dialog.grab_set()
        
        # Centrer la fenêtre
        dialog.geometry("+%d+%d" % (
            self.winfo_rootx() + 100,
            self.winfo_rooty() + 100
        ))
        
        # Frame principal
        main_frame = ctk.CTkScrollableFrame(dialog)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Informations du bloc
        info_frame = ctk.CTkFrame(main_frame)
        info_frame.pack(fill='x', pady=(0, 20))
        
        ctk.CTkLabel(info_frame, text=f"📦 Import du bloc : {block.name}", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        stats_text = f"Inclus : {self.count_nodes_in_structure(block.nodes) if block.nodes else 0} nœuds, {len(block.tasks)} tâches"
        ctk.CTkLabel(info_frame, text=stats_text).pack(pady=5)
        
        # Options d'import
        options_frame = ctk.CTkFrame(main_frame)
        options_frame.pack(fill='x', pady=10)
        
        ctk.CTkLabel(options_frame, text="🔧 Options d'import", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Position d'insertion
        pos_frame = ctk.CTkFrame(options_frame)
        pos_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(pos_frame, text="Position dans l'arbre:").pack(anchor="w", padx=10, pady=5)
        position_var = tk.StringVar(value="racine")
        
        ctk.CTkRadioButton(pos_frame, text="Créer comme nouvelle racine", 
                        variable=position_var, value="racine").pack(anchor="w", padx=20, pady=2)
        ctk.CTkRadioButton(pos_frame, text="Ajouter comme enfant du nœud sélectionné", 
                        variable=position_var, value="enfant").pack(anchor="w", padx=20, pady=2)
        ctk.CTkRadioButton(pos_frame, text="Remplacer l'arbre actuel", 
                        variable=position_var, value="remplacer").pack(anchor="w", padx=20, pady=2)
        
        # Options d'adaptation
        adapt_frame = ctk.CTkFrame(options_frame)
        adapt_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(adapt_frame, text="Adaptations:").pack(anchor="w", padx=10, pady=5)
        
        import_tasks_var = tk.BooleanVar(value=True)
        adapt_dates_var = tk.BooleanVar(value=True)
        preserve_links_var = tk.BooleanVar(value=True)
        
        ctk.CTkCheckBox(adapt_frame, text="Importer les tâches associées", 
                    variable=import_tasks_var).pack(anchor="w", padx=20, pady=2)
        ctk.CTkCheckBox(adapt_frame, text="Adapter les dates au projet actuel", 
                    variable=adapt_dates_var).pack(anchor="w", padx=20, pady=2)
        ctk.CTkCheckBox(adapt_frame, text="Préserver les liens entre nœuds et tâches", 
                    variable=preserve_links_var).pack(anchor="w", padx=20, pady=2)
        
        # Nom du projet pour l'historique
        project_frame = ctk.CTkFrame(main_frame)
        project_frame.pack(fill='x', pady=10)
        
        ctk.CTkLabel(project_frame, text="📊 Suivi d'utilisation", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(project_frame, text="Nom du projet (pour statistiques):").pack(anchor="w", padx=10, pady=(5, 0))
        project_name_entry = ctk.CTkEntry(project_frame, width=400, 
                                        placeholder_text="Ex: Projet IoT Client XYZ")
        project_name_entry.pack(fill="x", padx=10, pady=(5, 10))
        
        # Variable pour le résultat
        result = {"imported": False}
        
        def perform_import():
            try:
                position = position_var.get()
                project_name = project_name_entry.get().strip() or "Projet sans nom"
                
                # Import des nœuds
                if block.nodes and position != "skip":
                    imported_nodes = self.import_nodes_from_structure(block.nodes, position)
                    print(f"✅ {len(imported_nodes)} nœuds importés")
                
                # Import des tâches
                if import_tasks_var.get() and block.tasks:
                    imported_tasks = self.import_tasks_from_block(block, adapt_dates_var.get(), preserve_links_var.get())
                    print(f"✅ {len(imported_tasks)} tâches importées")
                
                # Enregistrer l'utilisation
                block.add_usage_record(project_name, 0, True, "Import dans projet")
                self.save_project_blocks()
                
                # Enregistrement dans le journal
                if hasattr(self, 'add_automatic_log_entry'):
                    self.add_automatic_log_entry(
                        title=f"Bloc importé : '{block.name}'",
                        description=f"Bloc importé dans le projet '{project_name}'.\nPosition: {position}\nTâches incluses: {import_tasks_var.get()}",
                        category="Block"
                    )
                
                result["imported"] = True
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'import :\n{str(e)}")
        
        def cancel():
            dialog.destroy()
        
        # Boutons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill='x', pady=20)
        
        ctk.CTkButton(button_frame, text="Annuler", command=cancel).pack(side='right', padx=(5, 0))
        ctk.CTkButton(button_frame, text="📥 Importer", command=perform_import).pack(side='right')
        
        # Attendre la fermeture
        dialog.wait_window()
        
        # Rafraîchir les vues si importé
        if result["imported"]:
            if hasattr(self, 'refresh_task_view'):
                self.refresh_task_view()
            if hasattr(self, 'redraw_tree_all'):
                self.redraw_tree_all()
            self.refresh_block_view()
            self.update_status(f"Bloc '{block.name}' importé avec succès")

    def import_nodes_from_structure(self, node_structure, position="racine"):
        """Importer des nœuds depuis une structure sauvegardée"""
        if not hasattr(self, 'tree_nodes'):
            self.tree_nodes = []
        
    def create_new_block(self):
        """Créer un nouveau bloc vide"""
        self.edit_block(None)

    def create_block_from_tree(self):
        """Créer un bloc à partir de l'arbre actuel"""
        if not hasattr(self, 'tree_nodes') or not self.tree_nodes:
            messagebox.showwarning("Avertissement", "Aucun diagramme en arbre trouvé!")
            return
        
        if not hasattr(self, 'selected_tree_node') or not self.selected_tree_node:
            messagebox.showwarning("Avertissement", "Sélectionnez d'abord un nœud racine dans l'arbre!")
            return
        
        # Demander les informations du bloc
        dialog = ctk.CTkToplevel(self)
        dialog.title("Créer un Bloc depuis l'Arbre")
        dialog.geometry("500x400")
        dialog.transient(self)
        dialog.grab_set()
        
        # Centrer la fenêtre
        dialog.geometry("+%d+%d" % (
            self.winfo_rootx() + 100,
            self.winfo_rooty() + 100
        ))
        
        # Frame principal
        main_frame = ctk.CTkScrollableFrame(dialog)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Informations du nœud sélectionné
        info_frame = ctk.CTkFrame(main_frame)
        info_frame.pack(fill='x', pady=(0, 20))
        
        ctk.CTkLabel(info_frame, text="🌳 Nœud racine sélectionné", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        ctk.CTkLabel(info_frame, text=f"Nœud: {self.selected_tree_node.text}").pack(anchor='w', padx=10)
        
        # Compter les descendants
        descendants = self.selected_tree_node.get_all_descendants()
        ctk.CTkLabel(info_frame, text=f"Sous-nœuds inclus: {len(descendants)}").pack(anchor='w', padx=10, pady=(0, 10))
        
        # Nom du bloc
        ctk.CTkLabel(main_frame, text="Nom du bloc:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        name_entry = ctk.CTkEntry(main_frame, width=400)
        name_entry.pack(fill='x', pady=(0, 10))
        name_entry.insert(0, f"Bloc - {self.selected_tree_node.text}")
        
        # Description
        ctk.CTkLabel(main_frame, text="Description:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        desc_textbox = ctk.CTkTextbox(main_frame, height=80, width=400)
        desc_textbox.pack(fill='x', pady=(0, 10))
        desc_textbox.insert("1.0", f"Bloc créé à partir du nœud '{self.selected_tree_node.text}' et ses {len(descendants)} sous-nœuds.")
        
        # Catégorie
        ctk.CTkLabel(main_frame, text="Catégorie:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        category_var = tk.StringVar(value="Process")
        categories = ["Process", "Testing", "CI/CD", "Hardware", "Software", "Integration", "Validation", "Documentation", "Planning", "Quality", "Security", "General"]
        category_menu = ctk.CTkOptionMenu(main_frame, values=categories, variable=category_var)
        category_menu.pack(fill='x', pady=(0, 10))
        
        # Domaine
        ctk.CTkLabel(main_frame, text="Domaine:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        domain_var = tk.StringVar(value="General")
        domains = ["General", "Embedded", "Web", "Mobile", "IoT", "Desktop", "Cloud", "AI/ML", "Data"]
        domain_menu = ctk.CTkOptionMenu(main_frame, values=domains, variable=domain_var)
        domain_menu.pack(fill='x', pady=(0, 10))
        
        # Client
        ctk.CTkLabel(main_frame, text="Client (optionnel):", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        client_entry = ctk.CTkEntry(main_frame, width=400, placeholder_text="Nom du client spécifique")
        client_entry.pack(fill='x', pady=(0, 10))
        
        # Tags
        ctk.CTkLabel(main_frame, text="Tags (séparés par des virgules):", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        tags_entry = ctk.CTkEntry(main_frame, width=400, placeholder_text="standard, testé, éprouvé")
        tags_entry.pack(fill='x', pady=(0, 20))
        
        # Variable pour le résultat
        result = {"saved": False}
        
        def save_block():
            if not name_entry.get().strip():
                messagebox.showerror("Erreur", "Le nom du bloc est obligatoire!")
                return
            
            # Créer le bloc
            new_block = ProjectBlock(
                name=name_entry.get().strip(),
                description=desc_textbox.get("1.0", "end-1c"),
                category=category_var.get(),
                domain=domain_var.get(),
                client=client_entry.get().strip()
            )
            
            # Traiter les tags
            tags_text = tags_entry.get().strip()
            if tags_text:
                new_block.tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]
            
            # Sauvegarder les nœuds
            new_block.nodes = self.serialize_tree_branch(self.selected_tree_node)
            
            # Chercher les tâches liées
            if hasattr(self, 'tasks'):
                linked_tasks = [task for task in self.tasks if task.linked_node and 
                            (task.linked_node == self.selected_tree_node or task.linked_node in descendants)]
                new_block.tasks = [task.to_dict() for task in linked_tasks]
            
            # Ajouter à la bibliothèque
            self.project_blocks.append(new_block)
            self.save_project_blocks()
            
            # Enregistrement dans le journal
            if hasattr(self, 'add_automatic_log_entry'):
                self.add_automatic_log_entry(
                    title=f"Bloc créé : '{new_block.name}'",
                    description=f"Nouveau bloc créé depuis l'arbre.\nNœuds inclus: {len(new_block.nodes)}\nTâches liées: {len(new_block.tasks)}",
                    category="Block"
                )
            
            result["saved"] = True
            dialog.destroy()
        
        def cancel():
            dialog.destroy()
        
        # Boutons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill='x', pady=10)
        
        ctk.CTkButton(button_frame, text="Annuler", command=cancel).pack(side='right', padx=(5, 0))
        ctk.CTkButton(button_frame, text="Créer le Bloc", command=save_block).pack(side='right')
        
        # Focus sur le nom
        name_entry.focus()
        
        # Attendre la fermeture
        dialog.wait_window()
        
        # Rafraîchir l'affichage si sauvegardé
        if result["saved"]:
            self.refresh_block_view()
            self.update_status("Bloc créé depuis l'arbre")

    def serialize_tree_branch(self, root_node):
        """Sérialiser une branche d'arbre en format JSON"""
        def node_to_dict(node):
            return {
                'text': node.text,
                'x': node.x,
                'y': node.y,
                'color': node.color,
                'border_color': node.border_color,
                'children': [node_to_dict(child) for child in node.children]
            }
        
        return node_to_dict(root_node)

    def view_block_details(self, block):
        """Afficher les détails complets d'un bloc"""
        # Créer une nouvelle fenêtre
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Détails - {block.name}")
        dialog.geometry("800x700")
        dialog.transient(self)
        
        # Frame principal avec onglets
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # En-tête
        header_frame = ctk.CTkFrame(main_frame)
        header_frame.pack(fill="x", pady=(0, 20))
        
        # Titre avec icône
        title_frame = ctk.CTkFrame(header_frame)
        title_frame.pack(fill="x", padx=10, pady=10)
        
        icon_label = ctk.CTkLabel(title_frame, text=block.get_category_icon(), 
                                font=ctk.CTkFont(size=32))
        icon_label.pack(side="left", padx=(10, 15))
        
        info_frame = ctk.CTkFrame(title_frame)
        info_frame.pack(side="left", fill="x", expand=True)
        
        name_label = ctk.CTkLabel(info_frame, text=block.name, 
                                font=ctk.CTkFont(size=18, weight="bold"))
        name_label.pack(anchor="w", pady=(5, 0))
        
        meta_text = f"🏷️ {block.category}"
        if block.domain:
            meta_text += f" • 🌐 {block.domain}"
        if block.client:
            meta_text += f" • 👤 {block.client}"
        
        meta_label = ctk.CTkLabel(info_frame, text=meta_text, 
                                font=ctk.CTkFont(size=12))
        meta_label.pack(anchor="w", pady=(0, 5))
        
        # Statistiques rapides
        stats_frame = ctk.CTkFrame(header_frame)
        stats_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        stats_text = f"📊 Utilisé {block.usage_count} fois"
        if block.usage_count > 0:
            stats_text += f" • ✅ {block.success_rate:.0f}% de succès"
            if block.average_duration > 0:
                stats_text += f" • ⏱️ {block.average_duration:.0f}j en moyenne"
        
        stats_label = ctk.CTkLabel(stats_frame, text=stats_text)
        stats_label.pack(padx=10, pady=5)
        
        # Contenu avec onglets simulés
        content_frame = ctk.CTkScrollableFrame(main_frame)
        content_frame.pack(fill="both", expand=True)
        
        # Description
        desc_section = ctk.CTkFrame(content_frame)
        desc_section.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(desc_section, text="📝 Description", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        desc_text = ctk.CTkTextbox(desc_section, height=80)
        desc_text.pack(fill="x", padx=10, pady=(0, 10))
        desc_text.insert("1.0", block.description)
        desc_text.configure(state="disabled")
        
        # Nœuds inclus
        if block.nodes:
            nodes_section = ctk.CTkFrame(content_frame)
            nodes_section.pack(fill="x", padx=10, pady=10)
            
            ctk.CTkLabel(nodes_section, text=f"🌳 Structure ({self.count_nodes_in_structure(block.nodes)} nœuds)", 
                        font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
            
            nodes_text = ctk.CTkTextbox(nodes_section, height=100)
            nodes_text.pack(fill="x", padx=10, pady=(0, 10))
            nodes_text.insert("1.0", self.format_node_structure(block.nodes))
            nodes_text.configure(state="disabled")
        
        # Tâches
        if block.tasks:
            tasks_section = ctk.CTkFrame(content_frame)
            tasks_section.pack(fill="x", padx=10, pady=10)
            
            ctk.CTkLabel(tasks_section, text=f"✅ Tâches templates ({len(block.tasks)})", 
                        font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
            
            for i, task in enumerate(block.tasks[:5]):  # Montrer max 5 tâches
                task_name = task.get('title', 'Tâche sans nom') if isinstance(task, dict) else str(task)
                task_frame = ctk.CTkFrame(tasks_section)
                task_frame.pack(fill="x", padx=20, pady=2)
                
                ctk.CTkLabel(task_frame, text=f"• {task_name}").pack(anchor="w", padx=10, pady=5)
            
            if len(block.tasks) > 5:
                ctk.CTkLabel(tasks_section, text=f"... et {len(block.tasks) - 5} autres tâches").pack(anchor="w", padx=20, pady=5)
        
        # Historique d'utilisation
        if block.usage_history:
            history_section = ctk.CTkFrame(content_frame)
            history_section.pack(fill="x", padx=10, pady=10)
            
            ctk.CTkLabel(history_section, text=f"📈 Historique d'utilisation ({len(block.usage_history)} projets)", 
                        font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
            
            # Afficher les 5 dernières utilisations
            recent_usage = sorted(block.usage_history, key=lambda x: x.get('date', ''), reverse=True)[:5]
            
            for usage in recent_usage:
                usage_frame = ctk.CTkFrame(history_section)
                usage_frame.pack(fill="x", padx=20, pady=2)
                
                project_name = usage.get('project_name', 'Projet inconnu')
                date_str = usage.get('date', '')
                if date_str:
                    try:
                        date_obj = datetime.datetime.fromisoformat(date_str)
                        date_display = date_obj.strftime('%d/%m/%Y')
                    except:
                        date_display = date_str
                else:
                    date_display = "Date inconnue"
                
                success_icon = "✅" if usage.get('success', True) else "❌"
                duration = usage.get('duration_days', 0)
                duration_text = f" ({duration}j)" if duration > 0 else ""
                
                usage_text = f"{success_icon} {project_name} - {date_display}{duration_text}"
                ctk.CTkLabel(usage_frame, text=usage_text).pack(anchor="w", padx=10, pady=5)
        
        # Tags
        if block.tags:
            tags_section = ctk.CTkFrame(content_frame)
            tags_section.pack(fill="x", padx=10, pady=10)
            
            ctk.CTkLabel(tags_section, text="🏷️ Tags", 
                        font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
            
            tags_text = " ".join([f"#{tag}" for tag in block.tags])
            ctk.CTkLabel(tags_section, text=tags_text, 
                        text_color="#2196F3").pack(anchor="w", padx=20, pady=(0, 10))
        
        # Boutons d'action
        buttons_frame = ctk.CTkFrame(main_frame)
        buttons_frame.pack(fill="x", pady=(20, 0))
        
        ctk.CTkButton(buttons_frame, text="📥 Importer dans le Projet", 
                    command=lambda: [dialog.destroy(), self.import_block_to_project(block)]).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(buttons_frame, text="✏️ Modifier", 
                    command=lambda: [dialog.destroy(), self.edit_block(block)]).pack(side="left", padx=5, pady=10)
        ctk.CTkButton(buttons_frame, text="Fermer", 
                    command=dialog.destroy).pack(side="right", padx=10, pady=10)
        ctk.CTkButton(buttons_frame, text="📝 Éditer Tâches", 
                    command=lambda: [dialog.destroy(), self.edit_block_tasks(block)]).pack(side="left", padx=5, pady=10)

    def count_nodes_in_structure(self, node_structure):
        """Compter le nombre de nœuds dans une structure"""
        if isinstance(node_structure, dict):
            count = 1  # Le nœud lui-même
            for child in node_structure.get('children', []):
                count += self.count_nodes_in_structure(child)
            return count
        return 1

    def format_node_structure(self, node_structure, indent=0):
        """Formater la structure des nœuds pour affichage"""
        if isinstance(node_structure, dict):
            text = "  " * indent + f"• {node_structure.get('text', 'Nœud')}\n"
            for child in node_structure.get('children', []):
                text += self.format_node_structure(child, indent + 1)
            return text
        return f"  " * indent + f"• {str(node_structure)}\n"

    def import_block_to_project(self, block):
        """Importer un bloc dans le projet actuel"""
        # Demander confirmation et options d'import
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Importer - {block.name}")
        dialog.geometry("600x500")
        dialog.transient(self)
        dialog.grab_set()
        
        # Centrer la fenêtre
        dialog.geometry("+%d+%d" % (
            self.winfo_rootx() + 100,
            self.winfo_rooty() + 100
        ))
        
        # Frame principal
        main_frame = ctk.CTkScrollableFrame(dialog)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Informations du bloc
        info_frame = ctk.CTkFrame(main_frame)
        info_frame.pack(fill='x', pady=(0, 20))
        
        ctk.CTkLabel(info_frame, text=f"📦 Import du bloc : {block.name}", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        stats_text = f"Inclus : {self.count_nodes_in_structure(block.nodes) if block.nodes else 0} nœuds, {len(block.tasks)} tâches"
        ctk.CTkLabel(info_frame, text=stats_text).pack(pady=5)
        
        # Options d'import
        options_frame = ctk.CTkFrame(main_frame)
        options_frame.pack(fill='x', pady=10)
        
        ctk.CTkLabel(options_frame, text="🔧 Options d'import", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Position d'insertion
        pos_frame = ctk.CTkFrame(options_frame)
        pos_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(pos_frame, text="Position dans l'arbre:").pack(anchor="w", padx=10, pady=5)
        position_var = tk.StringVar(value="racine")
        
        ctk.CTkRadioButton(pos_frame, text="Créer comme nouvelle racine", 
                        variable=position_var, value="racine").pack(anchor="w", padx=20, pady=2)
        ctk.CTkRadioButton(pos_frame, text="Ajouter comme enfant du nœud sélectionné", 
                        variable=position_var, value="enfant").pack(anchor="w", padx=20, pady=2)
        ctk.CTkRadioButton(pos_frame, text="Remplacer l'arbre actuel", 
                        variable=position_var, value="remplacer").pack(anchor="w", padx=20, pady=2)
        
        # Options d'adaptation
        adapt_frame = ctk.CTkFrame(options_frame)
        adapt_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(adapt_frame, text="Adaptations:").pack(anchor="w", padx=10, pady=5)
        
        import_tasks_var = tk.BooleanVar(value=True)
        adapt_dates_var = tk.BooleanVar(value=True)
        preserve_links_var = tk.BooleanVar(value=True)
        
        ctk.CTkCheckBox(adapt_frame, text="Importer les tâches associées", 
                    variable=import_tasks_var).pack(anchor="w", padx=20, pady=2)
        ctk.CTkCheckBox(adapt_frame, text="Adapter les dates au projet actuel", 
                    variable=adapt_dates_var).pack(anchor="w", padx=20, pady=2)
        ctk.CTkCheckBox(adapt_frame, text="Préserver les liens entre nœuds et tâches", 
                    variable=preserve_links_var).pack(anchor="w", padx=20, pady=2)
        
        # Nom du projet pour l'historique
        project_frame = ctk.CTkFrame(main_frame)
        project_frame.pack(fill='x', pady=10)
        
        ctk.CTkLabel(project_frame, text="📊 Suivi d'utilisation", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(project_frame, text="Nom du projet (pour statistiques):").pack(anchor="w", padx=10, pady=(5, 0))
        project_name_entry = ctk.CTkEntry(project_frame, width=400, 
                                        placeholder_text="Ex: Projet IoT Client XYZ")
        project_name_entry.pack(fill="x", padx=10, pady=(5, 10))
        
        # Variable pour le résultat
        result = {"imported": False}
        
        def perform_import():
            try:
                position = position_var.get()
                project_name = project_name_entry.get().strip() or "Projet sans nom"
                
                # Import des nœuds
                if block.nodes and position != "skip":
                    imported_nodes = self.import_nodes_from_structure(block.nodes, position)
                    print(f"✅ {len(imported_nodes)} nœuds importés")
                
                # Import des tâches
                if import_tasks_var.get() and block.tasks:
                    imported_tasks = self.import_tasks_from_block(block, adapt_dates_var.get(), preserve_links_var.get())
                    print(f"✅ {len(imported_tasks)} tâches importées")
                
                # Enregistrer l'utilisation
                block.add_usage_record(project_name, 0, True, "Import dans projet")
                self.save_project_blocks()
                
                # Enregistrement dans le journal
                if hasattr(self, 'add_automatic_log_entry'):
                    self.add_automatic_log_entry(
                        title=f"Bloc importé : '{block.name}'",
                        description=f"Bloc importé dans le projet '{project_name}'.\nPosition: {position}\nTâches incluses: {import_tasks_var.get()}",
                        category="Block"
                    )
                
                result["imported"] = True
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'import :\n{str(e)}")
        
        def cancel():
            dialog.destroy()
        
        # Boutons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill='x', pady=20)
        
        ctk.CTkButton(button_frame, text="Annuler", command=cancel).pack(side='right', padx=(5, 0))
        ctk.CTkButton(button_frame, text="📥 Importer", command=perform_import).pack(side='right')
        
        # Attendre la fermeture
        dialog.wait_window()
        
        # Rafraîchir les vues si importé
        if result["imported"]:
            if hasattr(self, 'refresh_task_view'):
                self.refresh_task_view()
            if hasattr(self, 'redraw_tree_all'):
                self.redraw_tree_all()
            self.refresh_block_view()
            self.update_status(f"Bloc '{block.name}' importé avec succès")

    def import_nodes_from_structure(self, node_structure, position="racine"):
        """Importer des nœuds depuis une structure sauvegardée"""
        if not hasattr(self, 'tree_nodes'):
            self.tree_nodes = []
        
        def create_node_from_dict(node_dict, parent=None, offset_x=0, offset_y=0):
            """Créer un nœud depuis un dictionnaire"""
            # Créer le nœud
            new_node = TreeNode(
                text=node_dict.get('text', 'Nœud'),
                x=node_dict.get('x', 100) + offset_x,
                y=node_dict.get('y', 100) + offset_y
            )
            new_node.color = node_dict.get('color', '#E3F2FD')
            new_node.border_color = node_dict.get('border_color', '#2196F3')
            
            # Définir le parent
            if parent:
                parent.add_child(new_node)
            
            # Ajouter à la liste des nœuds
            self.tree_nodes.append(new_node)
            
            # Créer les enfants récursivement
            for child_dict in node_dict.get('children', []):
                create_node_from_dict(child_dict, new_node, offset_x, offset_y)
            
            return new_node
        
        imported_nodes = []
        
        if position == "racine":
            # Nouvelle racine - décaler pour éviter les conflits
            offset_x = 500 if self.tree_nodes else 0
            offset_y = 100
            root_node = create_node_from_dict(node_structure, None, offset_x, offset_y)
            imported_nodes.append(root_node)
            
        elif position == "enfant" and hasattr(self, 'selected_tree_node') and self.selected_tree_node:
            # Enfant du nœud sélectionné
            offset_x = self.selected_tree_node.x + 150
            offset_y = self.selected_tree_node.y + 100
            child_node = create_node_from_dict(node_structure, self.selected_tree_node, offset_x, offset_y)
            imported_nodes.append(child_node)
            
        elif position == "remplacer":
            # Remplacer l'arbre actuel
            if messagebox.askyesno("Confirmation", "Remplacer complètement l'arbre actuel ?"):
                self.tree_nodes.clear()
                root_node = create_node_from_dict(node_structure, None, 400, 200)
                imported_nodes.append(root_node)
        
        # Redessiner l'arbre
        if hasattr(self, 'redraw_tree_all'):
            self.redraw_tree_all()
            
        return imported_nodes

    def import_tasks_from_block(self, block, adapt_dates=True, preserve_links=True):
        """Importer les tâches depuis un bloc"""
        if not hasattr(self, 'tasks'):
            self.tasks = []
        
        imported_tasks = []
        
        for task_data in block.tasks:
            # Créer la tâche
            if isinstance(task_data, dict):
                new_task = Task(
                    title=task_data.get('title', 'Tâche importée'),
                    description=task_data.get('description', ''),
                    status=task_data.get('status', 'À faire'),
                    priority=task_data.get('priority', 'Moyenne'),
                    assignee=task_data.get('assignee', ''),
                    due_date=task_data.get('due_date', '') if not adapt_dates else self.adapt_date_to_current(),
                    linked_node=None  # Sera lié plus tard si preserve_links
                )
            else:
                # Ancienne structure ou format différent
                new_task = Task(title=str(task_data), description="Tâche importée depuis un bloc")
            
            # Lien avec nœud si demandé
            if preserve_links and isinstance(task_data, dict) and task_data.get('linked_node'):
                # Chercher le nœud correspondant dans l'arbre actuel
                for node in getattr(self, 'tree_nodes', []):
                    if node.text == task_data['linked_node']:
                        new_task.linked_node = node
                        break
            
            self.tasks.append(new_task)
            imported_tasks.append(new_task)
        
        return imported_tasks

    def adapt_date_to_current(self):
        """Adapter une date au projet actuel (ajouter 1 semaine par exemple)"""
        from datetime import datetime, timedelta
        future_date = datetime.now() + timedelta(days=7)
        return future_date.strftime('%d/%m/%Y')

    def edit_block(self, block):
        """Éditer un bloc (nouveau ou existant)"""
        # Créer une fenêtre de dialogue
        dialog = ctk.CTkToplevel(self)
        dialog.title("Éditer le Bloc" if block else "Nouveau Bloc")
        dialog.geometry("600x700")
        dialog.transient(self)
        dialog.grab_set()
        
        # Centrer la fenêtre
        dialog.geometry("+%d+%d" % (
            self.winfo_rootx() + 100,
            self.winfo_rooty() + 100
        ))
        
        # Frame principal
        main_frame = ctk.CTkScrollableFrame(dialog)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Informations de base
        basic_frame = ctk.CTkFrame(main_frame)
        basic_frame.pack(fill='x', pady=(0, 20))
        
        ctk.CTkLabel(basic_frame, text="📦 Informations du bloc", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Nom
        ctk.CTkLabel(main_frame, text="Nom du bloc:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        name_entry = ctk.CTkEntry(main_frame, width=500)
        name_entry.pack(fill='x', pady=(0, 10))
        if block:
            name_entry.insert(0, block.name)
        
        # Description
        ctk.CTkLabel(main_frame, text="Description:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        desc_textbox = ctk.CTkTextbox(main_frame, height=100, width=500)
        desc_textbox.pack(fill='x', pady=(0, 10))
        if block:
            desc_textbox.insert("1.0", block.description)
        
        # Catégorie
        ctk.CTkLabel(main_frame, text="Catégorie:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        category_var = tk.StringVar(value=block.category if block else "Process")
        categories = ["Process", "Testing", "CI/CD", "Hardware", "Software", "Integration", "Validation", "Documentation", "Planning", "Quality", "Security", "General"]
        category_menu = ctk.CTkOptionMenu(main_frame, values=categories, variable=category_var)
        category_menu.pack(fill='x', pady=(0, 10))
        
        # Domaine
        ctk.CTkLabel(main_frame, text="Domaine:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        domain_var = tk.StringVar(value=block.domain if block else "General")
        domains = ["General", "Embedded", "Web", "Mobile", "IoT", "Desktop", "Cloud", "AI/ML", "Data", "Automotive", "Medical", "Aerospace"]
        domain_menu = ctk.CTkOptionMenu(main_frame, values=domains, variable=domain_var)
        domain_menu.pack(fill='x', pady=(0, 10))
        
        # Client
        ctk.CTkLabel(main_frame, text="Client spécifique (optionnel):", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        client_entry = ctk.CTkEntry(main_frame, width=500, placeholder_text="Nom du client pour des blocs spécialisés")
        client_entry.pack(fill='x', pady=(0, 10))
        if block:
            client_entry.insert(0, block.client)
        
        # Tags
        ctk.CTkLabel(main_frame, text="Tags (séparés par des virgules):", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        tags_entry = ctk.CTkEntry(main_frame, width=500, placeholder_text="standard, éprouvé, rapide, complexe")
        tags_entry.pack(fill='x', pady=(0, 10))
        if block and block.tags:
            tags_entry.insert(0, ", ".join(block.tags))
        
        # Notes d'utilisation
        ctk.CTkLabel(main_frame, text="Notes d'utilisation:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(10, 5))
        notes_textbox = ctk.CTkTextbox(main_frame, height=80, width=500)
        notes_textbox.pack(fill='x', pady=(0, 10))
        notes_placeholder = """Conseils d'utilisation, prérequis, points d'attention...
    Ex: - Nécessite un environnement de test isolé
        - Prévoir 2j supplémentaires pour la première utilisation
        - Compatible uniquement avec les projets > 1 mois"""
        if block:
            notes_textbox.insert("1.0", block.notes)
        else:
            notes_textbox.insert("1.0", notes_placeholder)
        
        # Statistiques (en lecture seule si bloc existant)
        if block:
            stats_frame = ctk.CTkFrame(main_frame)
            stats_frame.pack(fill='x', pady=10)
            
            ctk.CTkLabel(stats_frame, text="📊 Statistiques d'utilisation", 
                        font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(10, 5))
            
            stats_text = f"""• Utilisé {block.usage_count} fois
    • Taux de succès : {block.success_rate:.0f}%
    • Durée moyenne : {block.average_duration:.0f} jours
    • Créé le : {block.created_date.strftime('%d/%m/%Y')}
    • Dernière utilisation : {block.last_used.strftime('%d/%m/%Y') if block.last_used else 'Jamais'}"""
            
            ctk.CTkLabel(stats_frame, text=stats_text, justify="left").pack(padx=10, pady=(0, 10))
        
        # Variable pour le résultat
        result = {"saved": False}
        
        def save_block():
            if not name_entry.get().strip():
                messagebox.showerror("Erreur", "Le nom du bloc est obligatoire!")
                return
            
            if block:
                # Modifier le bloc existant
                block.name = name_entry.get().strip()
                block.description = desc_textbox.get("1.0", "end-1c")
                block.category = category_var.get()
                block.domain = domain_var.get()
                block.client = client_entry.get().strip()
                block.notes = notes_textbox.get("1.0", "end-1c")
                
                # Traiter les tags
                tags_text = tags_entry.get().strip()
                if tags_text:
                    block.tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]
                else:
                    block.tags = []
            else:
                # Créer un nouveau bloc
                new_block = ProjectBlock(
                    name=name_entry.get().strip(),
                    description=desc_textbox.get("1.0", "end-1c"),
                    category=category_var.get(),
                    domain=domain_var.get(),
                    client=client_entry.get().strip()
                )
                new_block.notes = notes_textbox.get("1.0", "end-1c")
                
                # Traiter les tags
                tags_text = tags_entry.get().strip()
                if tags_text:
                    new_block.tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]
                
                # Ajouter à la bibliothèque
                self.project_blocks.append(new_block)
            
            # Sauvegarder
            self.save_project_blocks()
            
            # Enregistrement dans le journal
            if hasattr(self, 'add_automatic_log_entry'):
                action = "modifié" if block else "créé"
                self.add_automatic_log_entry(
                    title=f"Bloc {action} : '{name_entry.get().strip()}'",
                    description=f"Bloc {action} dans la bibliothèque.\nCatégorie: {category_var.get()}\nDomaine: {domain_var.get()}",
                    category="Block"
                )
            
            result["saved"] = True
            dialog.destroy()
        
        def cancel():
            dialog.destroy()
        
        # Boutons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill='x', pady=20)
        
        ctk.CTkButton(button_frame, text="Annuler", command=cancel).pack(side='right', padx=(5, 0))
        save_text = "Sauvegarder" if block else "Créer le Bloc"
        ctk.CTkButton(button_frame, text=save_text, command=save_block).pack(side='right')
        
        # Focus sur le nom
        name_entry.focus()
        
        # Attendre la fermeture
        dialog.wait_window()
        
        # Rafraîchir l'affichage si sauvegardé
        if result["saved"]:
            self.refresh_block_view()
            action = "modifié" if block else "créé"
            self.update_status(f"Bloc {action} avec succès")

    def delete_block(self, block):
        """Supprimer un bloc de la bibliothèque"""
        if messagebox.askyesno("Confirmation", 
                            f"Supprimer définitivement le bloc '{block.name}' ?\n\n"
                            f"Cette action est irréversible.\n"
                            f"Le bloc a été utilisé {block.usage_count} fois."):
            try:
                self.project_blocks.remove(block)
                self.save_project_blocks()
                
                # Enregistrement dans le journal
                if hasattr(self, 'add_automatic_log_entry'):
                    self.add_automatic_log_entry(
                        title=f"Bloc supprimé : '{block.name}'",
                        description=f"Bloc supprimé de la bibliothèque.\nUtilisations: {block.usage_count}\nTaux de succès: {block.success_rate:.0f}%",
                        category="Block"
                    )
                
                self.refresh_block_view()
                self.update_status("Bloc supprimé")
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la suppression :\n{str(e)}")

    def export_blocks(self):
        """Exporter la bibliothèque de blocs"""
        if not self.project_blocks:
            messagebox.showwarning("Avertissement", "Aucun bloc à exporter!")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Exporter la bibliothèque de blocs"
        )
        
        if filename:
            try:
                export_data = {
                    'metadata': {
                        'export_date': datetime.datetime.now().isoformat(),
                        'total_blocks': len(self.project_blocks),
                        'exported_by': 'PCSwmm Application',
                        'version': '1.0'
                    },
                    'blocks': [block.to_dict() for block in self.project_blocks]
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
                
                messagebox.showinfo("Export réussi", 
                                f"Bibliothèque exportée avec succès !\n\n"
                                f"Fichier: {filename}\n"
                                f"Blocs exportés: {len(self.project_blocks)}")
                
                self.update_status("Bibliothèque exportée")
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'export :\n{str(e)}")

    def import_blocks(self):
        """Importer une bibliothèque de blocs"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Importer une bibliothèque de blocs"
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    import_data = json.load(f)
                
                # Vérifier la structure
                if 'blocks' not in import_data:
                    messagebox.showerror("Erreur", "Format de fichier invalide!")
                    return
                
                imported_blocks = import_data['blocks']
                metadata = import_data.get('metadata', {})
                
                # Demander confirmation
                total_blocks = len(imported_blocks)
                export_date = metadata.get('export_date', 'Inconnue')
                
                if not messagebox.askyesno("Confirmation d'import", 
                                        f"Importer {total_blocks} bloc(s) ?\n\n"
                                        f"Exporté le: {export_date}\n"
                                        f"Version: {metadata.get('version', 'Inconnue')}\n\n"
                                        f"Les blocs avec des noms identiques seront renommés."):
                    return
                
                # Importer les blocs
                imported_count = 0
                renamed_count = 0
                
                for block_data in imported_blocks:
                    try:
                        new_block = ProjectBlock.from_dict(block_data)
                        
                        # Vérifier les doublons de nom
                        original_name = new_block.name
                        counter = 1
                        while any(b.name == new_block.name for b in self.project_blocks):
                            new_block.name = f"{original_name} (Importé {counter})"
                            counter += 1
                            renamed_count += 1
                        
                        self.project_blocks.append(new_block)
                        imported_count += 1
                        
                    except Exception as e:
                        print(f"Erreur lors de l'import du bloc : {str(e)}")
                        continue
                
                # Sauvegarder
                self.save_project_blocks()
                
                # Message de confirmation
                message = f"Import réussi !\n\n"
                message += f"• {imported_count} bloc(s) importé(s)\n"
                if renamed_count > 0:
                    message += f"• {renamed_count} bloc(s) renommé(s) (doublons)\n"
                
                messagebox.showinfo("Import réussi", message)
                
                # Enregistrement dans le journal
                if hasattr(self, 'add_automatic_log_entry'):
                    self.add_automatic_log_entry(
                        title=f"Bibliothèque importée : {imported_count} blocs",
                        description=f"Import depuis: {filename}\nBlocs importés: {imported_count}\nBlocs renommés: {renamed_count}",
                        category="Block"
                    )
                
                self.refresh_block_view()
                self.update_status(f"{imported_count} blocs importés")
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'import :\n{str(e)}")

    def generate_usage_report(self):
        """Générer un rapport d'utilisation des blocs"""
        if not self.project_blocks:
            messagebox.showwarning("Avertissement", "Aucun bloc dans la bibliothèque!")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown files", "*.md"), ("Text files", "*.txt")],
            title="Sauvegarder le rapport d'usage"
        )
        
        if filename:
            try:
                # Trier les blocs par usage
                blocks_by_usage = sorted(self.project_blocks, key=lambda x: x.usage_count, reverse=True)
                
                content = f"""# 📊 Rapport d'Usage - Bibliothèque de Blocs

    *Généré le : {datetime.datetime.now().strftime('%d/%m/%Y à %H:%M')}*
    *Total de blocs : {len(self.project_blocks)}*

    ## 📈 Statistiques Globales

    """
                
                # Statistiques générales
                total_usage = sum(b.usage_count for b in self.project_blocks)
                used_blocks = len([b for b in self.project_blocks if b.usage_count > 0])
                avg_success = sum(b.success_rate for b in self.project_blocks if b.usage_count > 0) / max(used_blocks, 1)
                
                content += f"""- **Total d'utilisations** : {total_usage}
    - **Blocs utilisés** : {used_blocks}/{len(self.project_blocks)} ({used_blocks/len(self.project_blocks)*100:.0f}%)
    - **Taux de succès moyen** : {avg_success:.0f}%
    - **Blocs inutilisés** : {len(self.project_blocks) - used_blocks}

    """
                
                # Top 10 des blocs les plus utilisés
                content += "## 🏆 Top 10 - Blocs les Plus Utilisés\n\n"
                
                for i, block in enumerate(blocks_by_usage[:10]):
                    if block.usage_count > 0:
                        success_indicator = "🟢" if block.success_rate > 80 else "🟡" if block.success_rate > 60 else "🔴"
                        content += f"{i+1}. **{block.name}** {success_indicator}\n"
                        content += f"   - Utilisé {block.usage_count} fois\n"
                        content += f"   - Succès : {block.success_rate:.0f}%\n"
                        content += f"   - Durée moyenne : {block.average_duration:.0f}j\n"
                        content += f"   - Catégorie : {block.category}\n\n"
                
                # Analyse par catégorie
                content += "## 🏷️ Analyse par Catégorie\n\n"
                
                categories = {}
                for block in self.project_blocks:
                    if block.category not in categories:
                        categories[block.category] = {
                            'count': 0, 'total_usage': 0, 'avg_success': [], 'blocks': []
                        }
                    categories[block.category]['count'] += 1
                    categories[block.category]['total_usage'] += block.usage_count
                    if block.usage_count > 0:
                        categories[block.category]['avg_success'].append(block.success_rate)
                    categories[block.category]['blocks'].append(block)
                
                for category, data in sorted(categories.items()):
                    avg_success_cat = sum(data['avg_success']) / max(len(data['avg_success']), 1)
                    content += f"### {block.get_category_icon() if hasattr(block, 'get_category_icon') else '📦'} {category}\n\n"
                    content += f"- **Nombre de blocs** : {data['count']}\n"
                    content += f"- **Utilisations totales** : {data['total_usage']}\n"
                    content += f"- **Succès moyen** : {avg_success_cat:.0f}%\n"
                    content += f"- **Blocs utilisés** : {len(data['avg_success'])}/{data['count']}\n\n"
                
                # Analyse par domaine
                content += "## 🌐 Analyse par Domaine\n\n"
                
                domains = {}
                for block in self.project_blocks:
                    domain = block.domain or "Non spécifié"
                    if domain not in domains:
                        domains[domain] = {'count': 0, 'total_usage': 0, 'blocks': []}
                    domains[domain]['count'] += 1
                    domains[domain]['total_usage'] += block.usage_count
                    domains[domain]['blocks'].append(block)
                
                for domain, data in sorted(domains.items(), key=lambda x: x[1]['total_usage'], reverse=True):
                    content += f"- **{domain}** : {data['count']} blocs, {data['total_usage']} utilisations\n"
                
                # Blocs problématiques
                problematic_blocks = [b for b in self.project_blocks if b.usage_count > 0 and b.success_rate < 70]
                if problematic_blocks:
                    content += "\n## ⚠️ Blocs à Améliorer (< 70% de succès)\n\n"
                    for block in sorted(problematic_blocks, key=lambda x: x.success_rate):
                        content += f"- **{block.name}** : {block.success_rate:.0f}% de succès ({block.usage_count} utilisations)\n"
                        if block.notes:
                            content += f"  Notes : {block.notes[:100]}...\n"
                        content += "\n"
                
                # Recommandations
                content += "\n## 💡 Recommandations\n\n"
                
                unused_blocks = [b for b in self.project_blocks if b.usage_count == 0]
                if unused_blocks:
                    content += f"1. **Promouvoir l'utilisation** : {len(unused_blocks)} blocs n'ont jamais été utilisés\n"
                
                if problematic_blocks:
                    content += f"2. **Améliorer la qualité** : {len(problematic_blocks)} blocs ont un taux de succès faible\n"
                
                high_success_blocks = [b for b in self.project_blocks if b.usage_count > 2 and b.success_rate > 90]
                if high_success_blocks:
                    content += f"3. **Dupliquer les bonnes pratiques** : {len(high_success_blocks)} blocs ont un excellent taux de succès\n"
                
                content += f"\n---\n\n*Rapport généré automatiquement par l'application de gestion de projet*"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                messagebox.showinfo("Rapport généré", 
                                f"Rapport d'usage sauvegardé avec succès !\n\n"
                                f"Fichier: {filename}")
                
                self.update_status("Rapport d'usage généré")
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la génération du rapport :\n{str(e)}")

    def edit_block_tasks(self, block):
        """Éditer les tâches d'un bloc"""
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Tâches - {block.name}")
        dialog.geometry("700x600")
        dialog.transient(self)
        dialog.grab_set()
        
        # Centrer la fenêtre
        dialog.geometry("+%d+%d" % (
            self.winfo_rootx() + 100,
            self.winfo_rooty() + 100
        ))
        
        # Frame principal
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # En-tête
        header_frame = ctk.CTkFrame(main_frame)
        header_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(header_frame, text=f"📝 Tâches du bloc : {block.name}", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Toolbar avec boutons
        toolbar_frame = ctk.CTkFrame(main_frame)
        toolbar_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkButton(toolbar_frame, text="➕ Nouvelle Tâche", 
                    command=lambda: self.add_task_to_block(block, task_list_frame)).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(toolbar_frame, text="📥 Importer depuis Projet", 
                    command=lambda: self.import_project_tasks_to_block(block, task_list_frame)).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(toolbar_frame, text="🗑️ Tout Supprimer", 
                    command=lambda: self.clear_block_tasks(block, task_list_frame)).pack(side="right", padx=5, pady=5)
        
        # Liste des tâches
        task_list_frame = ctk.CTkScrollableFrame(main_frame)
        task_list_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        # Afficher les tâches existantes
        self.refresh_block_tasks_view(block, task_list_frame)
        
        # Boutons de fermeture
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x")
        
        ctk.CTkButton(button_frame, text="💾 Sauvegarder", 
                    command=lambda: self.save_block_and_close(block, dialog)).pack(side="right", padx=(5, 0))
        ctk.CTkButton(button_frame, text="Fermer", 
                    command=dialog.destroy).pack(side="right")

    def refresh_block_tasks_view(self, block, parent_frame):
        """Rafraîchir l'affichage des tâches du bloc"""
        # Nettoyer le contenu
        for widget in parent_frame.winfo_children():
            widget.destroy()
        
        if not block.tasks:
            # Message si aucune tâche
            no_tasks_label = ctk.CTkLabel(parent_frame, 
                                        text="Aucune tâche dans ce bloc\n\nUtilisez les boutons ci-dessus pour en ajouter", 
                                        font=ctk.CTkFont(size=14))
            no_tasks_label.pack(pady=50)
            return
        
        # Afficher chaque tâche
        for i, task_data in enumerate(block.tasks):
            self.create_block_task_widget(task_data, i, block, parent_frame)

    def create_block_task_widget(self, task_data, index, block, parent_frame):
        """Créer le widget pour une tâche du bloc"""
        task_frame = ctk.CTkFrame(parent_frame)
        task_frame.pack(fill="x", padx=10, pady=5)
        
        # En-tête de la tâche
        header_frame = ctk.CTkFrame(task_frame)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        # Titre et priorité
        title = task_data.get('title', 'Tâche sans nom') if isinstance(task_data, dict) else str(task_data)
        priority = task_data.get('priority', 'Moyenne') if isinstance(task_data, dict) else 'Moyenne'
        
        priority_colors = {"Basse": "#4CAF50", "Moyenne": "#FF9800", "Critique": "#F44336"}
        priority_color = priority_colors.get(priority, "#666666")
        
        title_label = ctk.CTkLabel(header_frame, text=f"📋 {title}", 
                                font=ctk.CTkFont(size=12, weight="bold"))
        title_label.pack(side="left", anchor="w")
        
        priority_label = ctk.CTkLabel(header_frame, text=f"🔥 {priority}", 
                                    text_color=priority_color, font=ctk.CTkFont(size=10))
        priority_label.pack(side="right", padx=5)
        
        # Détails de la tâche
        if isinstance(task_data, dict):
            details_frame = ctk.CTkFrame(task_frame)
            details_frame.pack(fill="x", padx=10, pady=2)
            
            if task_data.get('description'):
                desc_text = task_data['description'][:100] + "..." if len(task_data['description']) > 100 else task_data['description']
                ctk.CTkLabel(details_frame, text=f"📝 {desc_text}", 
                            font=ctk.CTkFont(size=10)).pack(anchor="w", padx=5, pady=2)
            
            if task_data.get('assignee'):
                ctk.CTkLabel(details_frame, text=f"👤 {task_data['assignee']}", 
                            font=ctk.CTkFont(size=10)).pack(anchor="w", padx=5, pady=2)
            
            if task_data.get('due_date'):
                ctk.CTkLabel(details_frame, text=f"📅 {task_data['due_date']}", 
                            font=ctk.CTkFont(size=10)).pack(anchor="w", padx=5, pady=2)
        
        # Boutons d'action
        actions_frame = ctk.CTkFrame(task_frame)
        actions_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        ctk.CTkButton(actions_frame, text="✏️ Modifier", width=80, height=25,
                    command=lambda: self.edit_block_task(task_data, index, block, parent_frame)).pack(side="left", padx=2)
        ctk.CTkButton(actions_frame, text="🗑️ Supprimer", width=80, height=25,
                    command=lambda: self.delete_block_task(index, block, parent_frame)).pack(side="right", padx=2)

    def add_task_to_block(self, block, parent_frame):
        """Ajouter une nouvelle tâche au bloc"""
        self.edit_block_task(None, -1, block, parent_frame)

    def edit_block_task(self, task_data, index, block, parent_frame):
        """Éditer une tâche du bloc"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Éditer Tâche du Bloc" if task_data else "Nouvelle Tâche du Bloc")
        dialog.geometry("500x600")
        dialog.transient(self)
        dialog.grab_set()
        
        # Centrer la fenêtre
        dialog.geometry("+%d+%d" % (
            self.winfo_rootx() + 150,
            self.winfo_rooty() + 150
        ))
        
        # Frame principal
        main_frame = ctk.CTkScrollableFrame(dialog)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Champs de saisie
        ctk.CTkLabel(main_frame, text="Titre:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        title_entry = ctk.CTkEntry(main_frame, width=400, placeholder_text="Ex: Configurer l'environnement de test")
        title_entry.pack(fill='x', pady=(0, 10))
        
        ctk.CTkLabel(main_frame, text="Description:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        desc_textbox = ctk.CTkTextbox(main_frame, height=100, width=400)
        desc_textbox.pack(fill='x', pady=(0, 10))
        
        ctk.CTkLabel(main_frame, text="Priorité:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        priority_var = tk.StringVar(value="Moyenne")
        priority_menu = ctk.CTkOptionMenu(main_frame, values=["Basse", "Moyenne", "Critique"], variable=priority_var)
        priority_menu.pack(fill='x', pady=(0, 10))
        
        ctk.CTkLabel(main_frame, text="Responsable:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        assignee_entry = ctk.CTkEntry(main_frame, width=400, placeholder_text="Nom ou rôle du responsable")
        assignee_entry.pack(fill='x', pady=(0, 10))
        
        ctk.CTkLabel(main_frame, text="Échéance estimée:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        due_entry = ctk.CTkEntry(main_frame, width=400, placeholder_text="Ex: J+5, Semaine 2, 15/01/2025")
        due_entry.pack(fill='x', pady=(0, 10))
        
        ctk.CTkLabel(main_frame, text="Statut:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(0, 5))
        status_var = tk.StringVar(value="Template")
        status_menu = ctk.CTkOptionMenu(main_frame, values=["Template", "À faire", "En cours", "Terminé"], variable=status_var)
        status_menu.pack(fill='x', pady=(0, 10))
        
        # Notes spéciales pour les blocs
        ctk.CTkLabel(main_frame, text="Notes pour réutilisation:", font=ctk.CTkFont(weight="bold")).pack(anchor='w', pady=(10, 5))
        notes_textbox = ctk.CTkTextbox(main_frame, height=80, width=400)
        notes_textbox.pack(fill='x', pady=(0, 20))
        notes_textbox.insert("1.0", "Conseils pour adapter cette tâche aux futurs projets...")
        
        # Pré-remplir si modification
        if task_data and isinstance(task_data, dict):
            title_entry.insert(0, task_data.get('title', ''))
            desc_textbox.insert("1.0", task_data.get('description', ''))
            priority_var.set(task_data.get('priority', 'Moyenne'))
            assignee_entry.insert(0, task_data.get('assignee', ''))
            due_entry.insert(0, task_data.get('due_date', ''))
            status_var.set(task_data.get('status', 'Template'))
            if task_data.get('notes'):
                notes_textbox.delete("1.0", "end")
                notes_textbox.insert("1.0", task_data['notes'])
        
        def save_task():
            if not title_entry.get().strip():
                messagebox.showerror("Erreur", "Le titre est obligatoire!")
                return
            
            new_task_data = {
                'title': title_entry.get().strip(),
                'description': desc_textbox.get("1.0", "end-1c"),
                'priority': priority_var.get(),
                'assignee': assignee_entry.get().strip(),
                'due_date': due_entry.get().strip(),
                'status': status_var.get(),
                'notes': notes_textbox.get("1.0", "end-1c"),
                'created_date': datetime.datetime.now().strftime('%d/%m/%Y')
            }
            
            if index >= 0:
                # Modification
                block.tasks[index] = new_task_data
            else:
                # Ajout
                block.tasks.append(new_task_data)
            
            dialog.destroy()
            self.refresh_block_tasks_view(block, parent_frame)
        
        # Boutons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill='x', pady=10)
        
        ctk.CTkButton(button_frame, text="Annuler", command=dialog.destroy).pack(side='right', padx=(5, 0))
        ctk.CTkButton(button_frame, text="Sauvegarder", command=save_task).pack(side='right')

    def delete_block_task(self, index, block, parent_frame):
        """Supprimer une tâche du bloc"""
        task_title = block.tasks[index].get('title', 'Tâche') if isinstance(block.tasks[index], dict) else str(block.tasks[index])
        
        if messagebox.askyesno("Confirmation", f"Supprimer la tâche '{task_title}' ?"):
            block.tasks.pop(index)
            self.refresh_block_tasks_view(block, parent_frame)

    def import_project_tasks_to_block(self, block, parent_frame):
        """Importer les tâches du projet actuel dans le bloc"""
        if not hasattr(self, 'tasks') or not self.tasks:
            messagebox.showwarning("Avertissement", "Aucune tâche dans le projet actuel!")
            return
        
        # Dialog de sélection
        dialog = ctk.CTkToplevel(self)
        dialog.title("Importer des Tâches du Projet")
        dialog.geometry("600x500")
        dialog.transient(self)
        dialog.grab_set()
        
        # Centrer la fenêtre
        dialog.geometry("+%d+%d" % (
            self.winfo_rootx() + 100,
            self.winfo_rooty() + 100
        ))
        
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(main_frame, text="Sélectionner les tâches à importer", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Liste des tâches avec checkboxes
        tasks_frame = ctk.CTkScrollableFrame(main_frame)
        tasks_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        task_vars = []
        for task in self.tasks:
            var = tk.BooleanVar()
            task_vars.append((var, task))
            
            task_frame = ctk.CTkFrame(tasks_frame)
            task_frame.pack(fill="x", padx=10, pady=2)
            
            ctk.CTkCheckBox(task_frame, text=f"{task.title} ({task.priority})", 
                        variable=var).pack(anchor="w", padx=10, pady=5)
        
        def import_selected():
            imported_count = 0
            for var, task in task_vars:
                if var.get():
                    task_dict = task.to_dict()
                    # Adapter pour le bloc
                    task_dict['status'] = 'Template'
                    task_dict['notes'] = f"Importé du projet le {datetime.datetime.now().strftime('%d/%m/%Y')}"
                    block.tasks.append(task_dict)
                    imported_count += 1
            
            if imported_count > 0:
                messagebox.showinfo("Import réussi", f"{imported_count} tâche(s) importée(s)!")
                self.refresh_block_tasks_view(block, parent_frame)
            
            dialog.destroy()
        
        # Boutons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x")
        
        ctk.CTkButton(button_frame, text="Annuler", command=dialog.destroy).pack(side='right', padx=(5, 0))
        ctk.CTkButton(button_frame, text="Importer Sélectionnées", command=import_selected).pack(side='right')

    def clear_block_tasks(self, block, parent_frame):
        """Supprimer toutes les tâches du bloc"""
        if block.tasks and messagebox.askyesno("Confirmation", f"Supprimer toutes les {len(block.tasks)} tâches du bloc ?"):
            block.tasks.clear()
            self.refresh_block_tasks_view(block, parent_frame)

    def save_block_and_close(self, block, dialog):
        """Sauvegarder le bloc et fermer la dialog"""
        self.save_project_blocks()
        messagebox.showinfo("Sauvegarde", "Tâches du bloc sauvegardées!")
        dialog.destroy()
        self.refresh_block_view()

    def save_project(self):
        """Sauvegarder tout le projet dans un fichier"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".prjt",
            filetypes=[("Project files", "*.prjt"), ("JSON files", "*.json"), ("All files", "*.*")],
            title="Sauvegarder le projet"
        )
        
        if not filename:
            return
        
        try:
            # Créer la structure de données complète du projet
            project_data = {
                'metadata': {
                    'project_name': os.path.splitext(os.path.basename(filename))[0],
                    'save_date': datetime.datetime.now().isoformat(),
                    'app_version': '1.0',
                    'file_type': 'prjt',
                    'description': f'Projet sauvegardé le {datetime.datetime.now().strftime("%d/%m/%Y à %H:%M")}'
                },
                
                # Données de la charte de projet
                'charter_data': getattr(self, 'charter_data', {}),
                
                # Données de l'arbre
                'tree_data': {
                    'nodes': self.serialize_all_tree_nodes() if hasattr(self, 'tree_nodes') and self.tree_nodes else [],
                    'selected_node': self.selected_tree_node.text if hasattr(self, 'selected_tree_node') and self.selected_tree_node else None
                },
                
                # Données des tâches
                'tasks_data': {
                    'tasks': [task.to_dict() for task in getattr(self, 'tasks', [])],
                    'view_mode': getattr(self, 'task_view_mode', 'kanban')
                },
                
                # Données du journal
                'log_data': {
                    'entries': [entry.to_dict() for entry in getattr(self, 'log_entries', [])],
                    'filters': {
                        'author': getattr(self, 'log_filter_author', 'Tous'),
                        'category': getattr(self, 'log_filter_category', 'Toutes'),
                        'date_from': getattr(self, 'log_filter_date_from', ''),
                        'date_to': getattr(self, 'log_filter_date_to', '')
                    }
                },
                
                # Données des documents
                'documents_data': {
                    'documents': [self.serialize_document(doc) for doc in getattr(self, 'documents', [])],
                    'view_mode': getattr(self, 'doc_view_mode', 'grid'),
                    'filters': {
                        'category': getattr(self, 'doc_filter_category', 'Toutes'),
                        'node': getattr(self, 'doc_filter_node', 'Tous')
                    }
                },
                
                # Données des blocs (référence seulement)
                'blocks_data': {
                    'used_blocks': [block.to_dict() for block in getattr(self, 'project_blocks', [])],
                    'view_mode': getattr(self, 'block_view_mode', 'grid'),
                    'filters': {
                        'category': getattr(self, 'block_filter_category', 'Toutes'),
                        'domain': getattr(self, 'block_filter_domain', 'Tous')
                    }
                },
                
                # Configuration de l'interface
                'ui_config': {
                    'appearance_mode': ctk.get_appearance_mode(),
                    'last_module': self.get_current_module(),
                    'window_size': f"{self.winfo_width()}x{self.winfo_height()}",
                    'window_position': f"+{self.winfo_x()}+{self.winfo_y()}"
                }
            }
            
            # Sauvegarder le fichier principal
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, ensure_ascii=False, indent=2)
            
            # Sauvegarder les fichiers associés si nécessaire
            project_dir = os.path.splitext(filename)[0] + "_files"
            if not os.path.exists(project_dir):
                os.makedirs(project_dir)
            
            # Copier les documents dans le dossier du projet
            documents_saved = 0
            if hasattr(self, 'documents') and self.documents:
                documents_project_dir = os.path.join(project_dir, "documents")
                if not os.path.exists(documents_project_dir):
                    os.makedirs(documents_project_dir)
                
                for doc in self.documents:
                    if os.path.exists(doc.stored_path):
                        new_path = os.path.join(documents_project_dir, f"{doc.id}_{doc.filename}")
                        shutil.copy2(doc.stored_path, new_path)
                        documents_saved += 1
            
            # Message de confirmation
            message = f"Projet sauvegardé avec succès !\n\n"
            message += f"📁 Fichier : {filename}\n"
            message += f"🌳 Nœuds : {len(getattr(self, 'tree_nodes', []))}\n"
            message += f"✅ Tâches : {len(getattr(self, 'tasks', []))}\n"
            message += f"💬 Entrées journal : {len(getattr(self, 'log_entries', []))}\n"
            message += f"📄 Documents : {documents_saved}\n"
            message += f"📦 Blocs : {len(getattr(self, 'project_blocks', []))}\n"
            
            messagebox.showinfo("Sauvegarde réussie", message)
            
            # Enregistrement dans le journal
            if hasattr(self, 'add_automatic_log_entry'):
                self.add_automatic_log_entry(
                    title="Projet sauvegardé",
                    description=f"Projet complet sauvegardé dans {filename}\nDonnées incluses: arbre, tâches, journal, documents, blocs",
                    category="Status"
                )
            
            self.update_status(f"Projet sauvegardé : {os.path.basename(filename)}")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde :\n{str(e)}")

    def load_project(self):
        """Charger un projet depuis un fichier"""
        filename = filedialog.askopenfilename(
            filetypes=[("Project files", "*.prjt"), ("JSON files", "*.json"), ("All files", "*.*")],
            title="Ouvrir un projet"
        )
        
        if not filename:
            return
        
        # Demander confirmation si des données existent déjà
        if self.has_project_data():
            if not messagebox.askyesno("Confirmation", 
                                    "Charger un nouveau projet effacera toutes les données actuelles.\n\n"
                                    "Voulez-vous d'abord sauvegarder le projet actuel ?"):
                # Proposer de sauvegarder
                if messagebox.askyesno("Sauvegarde", "Sauvegarder le projet actuel avant de continuer ?"):
                    self.save_project()
        
        try:
            # Charger le fichier
            with open(filename, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
            # Vérifier la structure
            if 'metadata' not in project_data:
                messagebox.showerror("Erreur", "Format de fichier invalide !")
                return
            
            # Vérifier le type de fichier
            metadata = project_data.get('metadata', {})
            file_type = metadata.get('file_type', '')
            if file_type and file_type != 'prjt':
                if not messagebox.askyesno("Avertissement", 
                                        f"Ce fichier semble être de type '{file_type}' et non '.prjt'.\n\n"
                                        f"Voulez-vous quand même essayer de l'ouvrir ?"):
                    return
            
            # Effacer les données actuelles
            self.clear_all_project_data()
            
            # Charger les métadonnées
            project_name = metadata.get('project_name', 'Projet sans nom')
            save_date = metadata.get('save_date', 'Date inconnue')
            
            # Charger la charte de projet
            self.charter_data = project_data.get('charter_data', {})
            
            # Charger l'arbre
            tree_data = project_data.get('tree_data', {})
            if tree_data.get('nodes'):
                self.load_tree_from_data(tree_data['nodes'])
                # Restaurer la sélection
                selected_node_text = tree_data.get('selected_node')
                if selected_node_text and hasattr(self, 'tree_nodes'):
                    for node in self.tree_nodes:
                        if node.text == selected_node_text:
                            self.selected_tree_node = node
                            node.selected = True
                            break
            
            # Charger les tâches
            tasks_data = project_data.get('tasks_data', {})
            self.tasks = []
            for task_dict in tasks_data.get('tasks', []):
                task = Task.from_dict(task_dict, getattr(self, 'tree_nodes', []))
                self.tasks.append(task)
            self.task_view_mode = tasks_data.get('view_mode', 'kanban')
            
            # Charger le journal
            log_data = project_data.get('log_data', {})
            self.log_entries = []
            for entry_dict in log_data.get('entries', []):
                entry = LogEntry.from_dict(entry_dict)
                self.log_entries.append(entry)
            
            # Restaurer les filtres du journal
            log_filters = log_data.get('filters', {})
            self.log_filter_author = log_filters.get('author', 'Tous')
            self.log_filter_category = log_filters.get('category', 'Toutes')
            self.log_filter_date_from = log_filters.get('date_from', '')
            self.log_filter_date_to = log_filters.get('date_to', '')
            
            # Charger les documents
            documents_data = project_data.get('documents_data', {})
            self.documents = []
            project_dir = os.path.splitext(filename)[0] + "_files"
            documents_project_dir = os.path.join(project_dir, "documents")
            
            loaded_docs = 0
            for doc_dict in documents_data.get('documents', []):
                doc = self.deserialize_document(doc_dict, documents_project_dir)
                if doc:
                    self.documents.append(doc)
                    loaded_docs += 1
            
            self.doc_view_mode = documents_data.get('view_mode', 'grid')
            doc_filters = documents_data.get('filters', {})
            self.doc_filter_category = doc_filters.get('category', 'Toutes')
            self.doc_filter_node = doc_filters.get('node', 'Tous')
            
            # Charger les blocs
            blocks_data = project_data.get('blocks_data', {})
            self.project_blocks = []
            for block_dict in blocks_data.get('used_blocks', []):
                block = ProjectBlock.from_dict(block_dict)
                self.project_blocks.append(block)
            
            self.block_view_mode = blocks_data.get('view_mode', 'grid')
            block_filters = blocks_data.get('filters', {})
            self.block_filter_category = block_filters.get('category', 'Toutes')
            self.block_filter_domain = block_filters.get('domain', 'Tous')
            
            # Restaurer la configuration de l'interface
            ui_config = project_data.get('ui_config', {})
            if ui_config.get('appearance_mode'):
                ctk.set_appearance_mode(ui_config['appearance_mode'])
            
            # Message de confirmation
            message = f"Projet '{project_name}' chargé avec succès !\n\n"
            message += f"📅 Sauvegardé le : {save_date[:10] if save_date != 'Date inconnue' else save_date}\n"
            message += f"🌳 Nœuds : {len(getattr(self, 'tree_nodes', []))}\n"
            message += f"✅ Tâches : {len(self.tasks)}\n"
            message += f"💬 Entrées journal : {len(self.log_entries)}\n"
            message += f"📄 Documents : {loaded_docs}\n"
            message += f"📦 Blocs : {len(self.project_blocks)}\n"
            
            messagebox.showinfo("Chargement réussi", message)
            
            # Enregistrement dans le journal
            self.add_automatic_log_entry(
                title="Projet chargé",
                description=f"Projet '{project_name}' chargé depuis {filename}\nDonnées restaurées: arbre, tâches, journal, documents, blocs",
                category="Status"
            )
            
            # Rafraîchir l'affichage actuel
            current_module = ui_config.get('last_module', 'home')
            self.restore_module_view(current_module)
            
            self.update_status(f"Projet chargé : {project_name}")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement :\n{str(e)}")

    def serialize_all_tree_nodes(self):
        """Sérialiser tous les nœuds de l'arbre"""
        if not hasattr(self, 'tree_nodes') or not self.tree_nodes:
            return []
        
        # Trouver les nœuds racines (sans parent)
        root_nodes = [node for node in self.tree_nodes if node.parent is None]
        
        def node_to_dict(node):
            """Convertir un nœud en dictionnaire"""
            return {
                'text': node.text,
                'x': node.x,
                'y': node.y,
                'width': getattr(node, 'width', 80),
                'height': getattr(node, 'height', 40),
                'color': getattr(node, 'color', '#E3F2FD'),
                'text_color': getattr(node, 'text_color', '#000000'),
                'border_color': getattr(node, 'border_color', '#2196F3'),
                'selected': getattr(node, 'selected', False),
                'children': [node_to_dict(child) for child in getattr(node, 'children', [])]
            }
        
        return [node_to_dict(root) for root in root_nodes]

    def load_tree_from_data(self, nodes_data):
        """Charger l'arbre depuis les données sérialisées"""
        if not hasattr(self, 'tree_nodes'):
            self.tree_nodes = []
        else:
            self.tree_nodes.clear()
        
        self.selected_tree_node = None
        
        def create_node_from_dict(node_dict, parent=None):
            node = TreeNode(
                text=node_dict.get('text', 'Nœud'),
                x=node_dict.get('x', 100),
                y=node_dict.get('y', 100),
                parent=parent
            )
            
            node.width = node_dict.get('width', 80)
            node.height = node_dict.get('height', 40)
            node.color = node_dict.get('color', '#E3F2FD')
            node.text_color = node_dict.get('text_color', '#000000')
            node.border_color = node_dict.get('border_color', '#2196F3')
            node.selected = node_dict.get('selected', False)
            
            if parent:
                parent.add_child(node)
            
            self.tree_nodes.append(node)
            
            # Créer les enfants récursivement
            for child_dict in node_dict.get('children', []):
                create_node_from_dict(child_dict, node)
            
            return node
        
        # Créer tous les nœuds
        for root_dict in nodes_data:
            create_node_from_dict(root_dict)

    def serialize_document(self, doc):
        """Sérialiser un document pour la sauvegarde"""
        # Vérifier que upload_date est un datetime
        upload_date_iso = doc.upload_date.isoformat() if isinstance(doc.upload_date, datetime.datetime) else datetime.datetime.now().isoformat()
        
        return {
            'id': getattr(doc, 'id', id(doc)),
            'filename': doc.filename,
            'original_path': getattr(doc, 'file_path', ''),
            'stored_path': getattr(doc, 'stored_path', ''),
            'category': doc.category,
            'version': doc.version,
            'description': getattr(doc, 'description', ''),
            'tags': getattr(doc, 'tags', []),
            'upload_date': upload_date_iso,
            'file_size': getattr(doc, 'file_size', 0),
            'file_type': getattr(doc, 'file_type', ''),
            'linked_node_text': doc.linked_node.text if getattr(doc, 'linked_node', None) else None
        }

    def deserialize_document(self, doc_dict, documents_dir):
        """Désérialiser un document depuis la sauvegarde"""
        try:
            # Récréer le document
            doc = Document(
                filename=doc_dict.get('filename', ''),
                file_path=doc_dict.get('original_path', ''),
                category=doc_dict.get('category', 'General'),
                version=doc_dict.get('version', '1.0'),
                description=doc_dict.get('description', '')
            )
            
            doc.id = doc_dict.get('id', id(doc))
            doc.tags = doc_dict.get('tags', [])
            doc.upload_date = datetime.datetime.fromisoformat(doc_dict.get('upload_date', datetime.datetime.now().isoformat()))
            doc.file_size = doc_dict.get('file_size', 0)
            doc.file_type = doc_dict.get('file_type', '')
            
            # Chercher le fichier dans le dossier du projet
            expected_file = os.path.join(documents_dir, f"{doc.id}_{doc.filename}")
            if os.path.exists(expected_file):
                # Copier vers le stockage de l'application
                if not hasattr(self, 'documents_storage_path'):
                    self.documents_storage_path = os.path.join(os.getcwd(), "documents_storage")
                    if not os.path.exists(self.documents_storage_path):
                        os.makedirs(self.documents_storage_path)
                
                new_stored_path = os.path.join(self.documents_storage_path, f"{doc.id}_{doc.filename}")
                shutil.copy2(expected_file, new_stored_path)
                doc.stored_path = new_stored_path
            else:
                print(f"⚠️ Document manquant : {doc.filename}")
                return None
            
            # Lier au nœud si spécifié
            linked_node_text = doc_dict.get('linked_node_text')
            if linked_node_text and hasattr(self, 'tree_nodes'):
                for node in self.tree_nodes:
                    if node.text == linked_node_text:
                        doc.linked_node = node
                        break
            
            return doc
            
        except Exception as e:
            print(f"Erreur lors de la désérialisation du document : {str(e)}")
            return None

    def has_project_data(self):
        """Vérifier si des données de projet existent"""
        return (hasattr(self, 'tree_nodes') and self.tree_nodes) or \
            (hasattr(self, 'tasks') and self.tasks) or \
            (hasattr(self, 'log_entries') and self.log_entries) or \
            (hasattr(self, 'documents') and self.documents) or \
            (hasattr(self, 'charter_data') and self.charter_data)

    def clear_all_project_data(self):
        """Effacer toutes les données du projet"""
        # Effacer l'arbre
        if hasattr(self, 'tree_nodes'):
            self.tree_nodes.clear()
        self.selected_tree_node = None
        
        # Effacer les tâches
        if hasattr(self, 'tasks'):
            self.tasks.clear()
        
        # Effacer le journal
        if hasattr(self, 'log_entries'):
            self.log_entries.clear()
        
        # Effacer les documents
        if hasattr(self, 'documents'):
            self.documents.clear()
        
        # Effacer les blocs
        if hasattr(self, 'project_blocks'):
            self.project_blocks.clear()
        
        # Effacer la charte
        self.charter_data = {}
        
        # Réinitialiser les filtres
        self.task_view_mode = "kanban"
        self.doc_view_mode = "grid"
        self.block_view_mode = "grid"
        self.log_filter_author = "Tous"
        self.log_filter_category = "Toutes"
        self.log_filter_date_from = ""
        self.log_filter_date_to = ""
        self.doc_filter_category = "Toutes"
        self.doc_filter_node = "Tous"
        self.block_filter_category = "Toutes"
        self.block_filter_domain = "Tous"

    def get_current_module(self):
        """Obtenir le module actuellement affiché"""
        title = self.main_title.cget("text")
        
        if "Accueil" in title:
            return "home"
        elif "Cadrage" in title:
            return "charter"
        elif "Arbre" in title:
            return "tree"
        elif "Tâches" in title:
            return "tasks"
        elif "Journal" in title:
            return "log"
        elif "Documents" in title:
            return "documents"
        elif "Blocs" in title:
            return "blocks"
        else:
            return "home"

    def restore_module_view(self, module):
        """Restaurer la vue d'un module"""
        try:
            if module == "charter":
                self.show_project_charter()
            elif module == "tree":
                self.show_tree_diagram()
            elif module == "tasks":
                self.show_task_tracker()
            elif module == "log":
                self.show_decision_log()
            elif module == "documents":
                self.show_document_manager()
            elif module == "blocks":
                self.show_block_library()
            else:
                self.show_home()
        except:
            # En cas d'erreur, retourner à l'accueil
            self.show_home()

    def new_project(self):
        """Créer un nouveau projet"""
        if self.has_project_data():
            if not messagebox.askyesno("Nouveau projet", 
                                    "Créer un nouveau projet effacera toutes les données actuelles.\n\n"
                                    "Voulez-vous d'abord sauvegarder le projet actuel ?"):
                return
            
            # Proposer de sauvegarder
            if messagebox.askyesno("Sauvegarde", "Sauvegarder le projet actuel avant de continuer ?"):
                self.save_project()
        
        # Effacer toutes les données
        self.clear_all_project_data()
        
        # Retourner à l'accueil
        self.show_home()
        
        # Enregistrement dans le journal
        if hasattr(self, 'add_automatic_log_entry'):
            self.add_automatic_log_entry(
                title="Nouveau projet créé",
                description="Nouveau projet initialisé, toutes les données précédentes ont été effacées",
                category="Status"
            )
        
        self.update_status("Nouveau projet créé")
        messagebox.showinfo("Nouveau projet", "Nouveau projet créé avec succès !")

    def get_project_statistics(self):
        """Obtenir les statistiques du projet actuel"""
        stats = []
        
        # Arbre
        tree_count = len(getattr(self, 'tree_nodes', []))
        stats.append(f"🌳 Nœuds d'arbre : {tree_count}")
        
        # Tâches
        tasks_count = len(getattr(self, 'tasks', []))
        if tasks_count > 0:
            todo = len([t for t in self.tasks if t.status == "À faire"])
            in_progress = len([t for t in self.tasks if t.status == "En cours"])
            done = len([t for t in self.tasks if t.status == "Terminé"])
            stats.append(f"✅ Tâches : {tasks_count} (🔄 {todo} à faire, ⚡ {in_progress} en cours, ✅ {done} terminées)")
        else:
            stats.append(f"✅ Tâches : {tasks_count}")
        
        # Journal
        log_count = len(getattr(self, 'log_entries', []))
        if log_count > 0:
            manual = len([e for e in self.log_entries if e.entry_type == "manual"])
            auto = len([e for e in self.log_entries if e.entry_type == "auto"])
            stats.append(f"💬 Entrées journal : {log_count} (👤 {manual} manuelles, 🤖 {auto} automatiques)")
        else:
            stats.append(f"💬 Entrées journal : {log_count}")
        
        # Documents
        docs_count = len(getattr(self, 'documents', []))
        if docs_count > 0:
            total_size = sum(doc.file_size for doc in self.documents)
            size_text = f"{total_size/(1024*1024):.1f} MB" if total_size > 1024*1024 else f"{total_size/1024:.1f} KB"
            stats.append(f"📄 Documents : {docs_count} ({size_text})")
        else:
            stats.append(f"📄 Documents : {docs_count}")
        
        # Blocs
        blocks_count = len(getattr(self, 'project_blocks', []))
        stats.append(f"📦 Blocs réutilisables : {blocks_count}")
        
        # Charte
        charter_status = "✅ Complétée" if getattr(self, 'charter_data', {}) else "❌ Vide"
        stats.append(f"📋 Charte de projet : {charter_status}")
        
        return "\n".join(stats)


def main():
    """Fonction principale"""
    app = App()
    
    # Gestionnaire de fermeture
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Centrer la fenêtre
    app.update_idletasks()
    width = app.winfo_width()
    height = app.winfo_height()
    x = (app.winfo_screenwidth() // 2) - (width // 2)
    y = (app.winfo_screenheight() // 2) - (height // 2)
    app.geometry(f'{width}x{height}+{x}+{y}')
    
    # Démarrer l'application
    app.mainloop()

if __name__ == "__main__":
    main()