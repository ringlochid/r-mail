import os
import json
from cryptography.fernet import Fernet
from pathlib import Path

VAULT_FILE = Path.home() / ".r-mail" / "secrets.enc"

class Vault:
    def __init__(self):
        # Try to get the master key from ENV, or fail effectively
        self.key = os.getenv("RMAIL_MASTER_KEY")
        if not self.key:
            # You could add logic here to prompt the user if interactive
            # But for cron/servers, ENV vars are safer.
            raise ValueError("Missing RMAIL_MASTER_KEY environment variable.")

        self.fernet = Fernet(self.key.encode())

    def _load_db(self):
        if not VAULT_FILE.exists():
            return {}
        try:
            with open(VAULT_FILE, "rb") as f:
                encrypted_data = f.read()
            decrypted_data = self.fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data)
        except Exception:
            return {} # Return empty if corrupt or wrong key

    def _save_db(self, data):
        json_bytes = json.dumps(data).encode('utf-8')
        encrypted_data = self.fernet.encrypt(json_bytes)

        # Ensure directory exists and permissions are strict (0o600)
        VAULT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(VAULT_FILE, "wb") as f:
            f.write(encrypted_data)
        os.chmod(VAULT_FILE, 0o600)

    def set_password(self, service_name, username, password):
        db = self._load_db()
        if service_name not in db:
            db[service_name] = {}
        db[service_name][username] = password
        self._save_db(db)

    def get_password(self, service_name, username):
        db = self._load_db()
        return db.get(service_name, {}).get(username)

# Helper to generate a key for you to put in your .bashrc
def generate_new_key():
    return Fernet.generate_key().decode()
