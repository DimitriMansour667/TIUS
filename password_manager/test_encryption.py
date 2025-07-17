import sqlite3
import bcrypt
import os
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

def test_encryption_decryption():
    """Test le chiffrement et déchiffrement des mots de passe"""
    
    print("🔐 Test du système de chiffrement/déchiffrement")
    print("=" * 50)
    
    # Test 1: Génération de clé avec salt
    print("\n1. Test de génération de clé avec salt:")
    password = "test_password"
    salt = os.urandom(16)
    
    def generate_encryption_key(password: str, salt: bytes = None) -> tuple:
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
    
    key1, salt1 = generate_encryption_key(password)
    key2, salt2 = generate_encryption_key(password, salt1)  # Même salt
    
    print(f"   Clé 1: {key1[:20]}... (avec salt généré)")
    print(f"   Clé 2: {key2[:20]}... (avec même salt)")
    print(f"   Clés identiques: {key1 == key2}")
    
    # Test 2: Chiffrement/déchiffrement
    print("\n2. Test de chiffrement/déchiffrement:")
    test_password = "mon_mot_de_passe_secret"
    
    def encrypt_password(password: str, encryption_key: bytes) -> str:
        f = Fernet(encryption_key)
        encrypted_password = f.encrypt(password.encode())
        return base64.urlsafe_b64encode(encrypted_password).decode()
    
    def decrypt_password(encrypted_password: str, encryption_key: bytes) -> str:
        f = Fernet(encryption_key)
        encrypted_data = base64.urlsafe_b64decode(encrypted_password.encode())
        decrypted_password = f.decrypt(encrypted_data)
        return decrypted_password.decode()
    
    encrypted = encrypt_password(test_password, key1)
    decrypted = decrypt_password(encrypted, key2)  # Utiliser la même clé
    
    print(f"   Mot de passe original: {test_password}")
    print(f"   Mot de passe chiffré: {encrypted[:30]}...")
    print(f"   Mot de passe déchiffré: {decrypted}")
    print(f"   Déchiffrement réussi: {test_password == decrypted}")
    
    # Test 3: Test avec base de données
    print("\n3. Test avec base de données:")
    test_db = "test_encryption.db"
    
    # Nettoyer la base de test existante
    if os.path.exists(test_db):
        os.remove(test_db)
    
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    
    # Créer la table
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password_hash TEXT,
            encryption_salt BLOB
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE passwords (
            id INTEGER PRIMARY KEY,
            title TEXT,
            password_encrypted TEXT,
            created_by TEXT
        )
    ''')
    
    # Créer un utilisateur de test
    username = "testuser"
    user_password = "user123"
    hashed_password = bcrypt.hashpw(user_password.encode('utf-8'), bcrypt.gensalt())
    encryption_key, salt = generate_encryption_key(user_password)
    
    cursor.execute(
        "INSERT INTO users (username, password_hash, encryption_salt) VALUES (?, ?, ?)",
        (username, hashed_password, salt)
    )
    
    # Chiffrer et stocker un mot de passe
    secret_password = "super_secret_password"
    encrypted_secret = encrypt_password(secret_password, encryption_key)
    
    cursor.execute(
        "INSERT INTO passwords (title, password_encrypted, created_by) VALUES (?, ?, ?)",
        ("Test Password", encrypted_secret, username)
    )
    
    conn.commit()
    
    # Simuler une connexion et déchiffrement
    cursor.execute("SELECT password_hash, encryption_salt FROM users WHERE username = ?", (username,))
    user_data = cursor.fetchone()
    
    if user_data and bcrypt.checkpw(user_password.encode('utf-8'), user_data[0]):
        stored_salt = user_data[1]
        user_encryption_key, _ = generate_encryption_key(user_password, stored_salt)
        
        # Récupérer et déchiffrer le mot de passe
        cursor.execute("SELECT password_encrypted FROM passwords WHERE created_by = ?", (username,))
        encrypted_data = cursor.fetchone()[0]
        
        decrypted_secret = decrypt_password(encrypted_data, user_encryption_key)
        
        print(f"   Mot de passe stocké: {secret_password}")
        print(f"   Mot de passe déchiffré: {decrypted_secret}")
        print(f"   Test base de données réussi: {secret_password == decrypted_secret}")
    
    conn.close()
    os.remove(test_db)
    
    print("\n✅ Tous les tests terminés")

def test_existing_database():
    """Test la base de données existante"""
    
    print("\n🔍 Test de la base de données existante")
    print("=" * 40)
    
    db_path = 'password_manager.db'
    
    if not os.path.exists(db_path):
        print("❌ Aucune base de données trouvée")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Vérifier la structure
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    
    print(f"Colonnes dans la table users: {columns}")
    
    has_salt = 'encryption_salt' in columns
    print(f"Colonne encryption_salt présente: {has_salt}")
    
    # Compter les utilisateurs
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM passwords")
    password_count = cursor.fetchone()[0]
    
    print(f"Nombre d'utilisateurs: {user_count}")
    print(f"Nombre de mots de passe: {password_count}")
    
    if has_salt:
        cursor.execute("SELECT username, encryption_salt FROM users")
        users = cursor.fetchall()
        
        users_with_salt = sum(1 for user in users if user[1] is not None)
        print(f"Utilisateurs avec salt: {users_with_salt}/{len(users)}")
    
    conn.close()

if __name__ == "__main__":
    test_encryption_decryption()
    test_existing_database()
