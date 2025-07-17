import sqlite3
import os
from datetime import datetime

def migrate_database():
    """Migre la base de données existante pour ajouter le support du salt"""
    
    db_path = 'password_manager.db'
    
    if not os.path.exists(db_path):
        print("❌ Aucune base de données trouvée à migrer")
        return
    
    # Faire une sauvegarde
    backup_path = f"password_manager_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"✅ Sauvegarde créée : {backup_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Vérifier si la colonne encryption_salt existe déjà
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'encryption_salt' not in columns:
            print("🔧 Ajout de la colonne encryption_salt...")
            cursor.execute("ALTER TABLE users ADD COLUMN encryption_salt BLOB")
            conn.commit()
            print("✅ Colonne encryption_salt ajoutée")
        else:
            print("ℹ️  La colonne encryption_salt existe déjà")
        
        # Vérifier les utilisateurs sans salt
        cursor.execute("SELECT username FROM users WHERE encryption_salt IS NULL")
        users_without_salt = cursor.fetchall()
        
        if users_without_salt:
            print(f"⚠️  {len(users_without_salt)} utilisateur(s) sans salt détecté(s)")
            print("   Ces utilisateurs devront se reconnecter pour générer leur salt")
            
            for user in users_without_salt:
                print(f"   - {user[0]}")
        
        print("✅ Migration terminée avec succès")
        
    except Exception as e:
        print(f"❌ Erreur lors de la migration : {e}")
        # Restaurer la sauvegarde
        shutil.copy2(backup_path, db_path)
        print("🔄 Sauvegarde restaurée")
    
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔄 Migration de la base de données")
    print("=" * 40)
    migrate_database()
