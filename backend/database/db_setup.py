import sqlite3
import os
import sys
from werkzeug.security import generate_password_hash

# Add parent directory to path so config can be loaded
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import Config

def init_db():
    db_path = Config.DATABASE_PATH
    db_dir = os.path.dirname(db_path)
    
    # Ensure database folder exists
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
        print(f"Created database directory at {db_dir}")
        
    print(f"Connecting to database at {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create Predictions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        symptoms TEXT NOT NULL,
        predicted_disease TEXT NOT NULL,
        confidence_score REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    ''')
    
    # Seed default users if table is empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        print("Seeding default users...")
        
        # Admin user
        admin_pass = generate_password_hash("admin123")
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
            ("admin", "admin@medipredict.ai", admin_pass, "admin")
        )
        
        # Regular user
        user_pass = generate_password_hash("patient123")
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
            ("patient", "patient@medipredict.ai", user_pass, "user")
        )
        
        conn.commit()
        print("Default users seeded successfully:")
        print("  - Admin: admin@medipredict.ai / admin123")
        print("  - Patient: patient@medipredict.ai / patient123")
    else:
        print("Database already contains user records. Seeding skipped.")
        
    conn.close()
    print("Database initialization complete.")

if __name__ == "__main__":
    init_db()
