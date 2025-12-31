import sqlite3
import os
import stat
from pathlib import Path

# Define paths
APP_DIR = Path.home() / ".r-mail"
DB_PATH = APP_DIR / "data.db"
VAULT_PATH = APP_DIR / "secrets.enc"

def get_db():
    """Connects to the database and returns the connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    return conn

def init_app():
    """Initializes the application directory and database with strict permissions."""
    # 1. Create Directory with 700 permissions (rwx------)
    if not APP_DIR.exists():
        APP_DIR.mkdir(parents=True)

    os.chmod(APP_DIR, 0o700)

    # 2. Initialize Database
    conn = get_db()
    with open(Path(__file__).parent / "schema.sql") as f:
        conn.executescript(f.read())
    conn.close()

    # 3. Secure the Database File (rw-------)
    if DB_PATH.exists():
        os.chmod(DB_PATH, 0o600)

    # 4. Secure the Vault File if it exists (rw-------)
    if VAULT_PATH.exists():
        os.chmod(VAULT_PATH, 0o600)

    print(f"Initialized r-mail at {APP_DIR}")

def query_db(query, args=(), one=False):
    """Helper function to run queries."""
    conn = get_db()
    cur = conn.execute(query, args)
    rv = cur.fetchall()
    conn.commit()
    conn.close()
    return (rv[0] if rv else None) if one else rv
