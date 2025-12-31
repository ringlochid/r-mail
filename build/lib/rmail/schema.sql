PRAGMA foreign_keys = ON;

-- 1. DOMAINS: SMTP Configuration
CREATE TABLE IF NOT EXISTS domains (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    smtp_host TEXT NOT NULL,
    smtp_port INTEGER NOT NULL,
    smtp_user TEXT,
    security TEXT DEFAULT 'STARTTLS',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 2. SENDERS: The "From" identities
CREATE TABLE IF NOT EXISTS senders (
    id INTEGER PRIMARY KEY,
    alias TEXT UNIQUE NOT NULL,
    fullname TEXT NOT NULL,
    email TEXT NOT NULL,
    domain_id INTEGER NOT NULL,
    FOREIGN KEY(domain_id) REFERENCES domains(id) ON DELETE RESTRICT
);

-- 3. RECEIVERS: Address book
CREATE TABLE IF NOT EXISTS receivers (
    id INTEGER PRIMARY KEY,
    alias TEXT UNIQUE NOT NULL,
    name TEXT,
    email TEXT NOT NULL,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 4. CONTEXTS: New workflow
CREATE TABLE IF NOT EXISTS contexts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    template_name TEXT, -- Optional: Link to a specific template filename
    data JSON NOT NULL  -- Store the variables as a JSON string
);
