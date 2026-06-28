import sqlite3
import json
from datetime import datetime

DB_FILE = "vc_wallet.sqlite"

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS holder (
    holder_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    did            TEXT UNIQUE NOT NULL,
    display_name   TEXT,
    email          TEXT,
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS issuer (
    issuer_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    did            TEXT UNIQUE NOT NULL,
    display_name   TEXT,
    endpoint       TEXT,
    public_key_jwk TEXT,
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS credential (
    credential_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    holder_id         INTEGER NOT NULL,
    issuer_id         INTEGER NOT NULL,
    vc_id             TEXT UNIQUE NOT NULL,
    type              TEXT NOT NULL,
    context           TEXT NOT NULL,
    schema_uri        TEXT,
    issuance_date     DATETIME NOT NULL,
    expiration_date   DATETIME,
    revoked           INTEGER DEFAULT 0 CHECK (revoked IN (0,1)),
    tags              TEXT,
    credential_subject TEXT NOT NULL,
    proof             TEXT NOT NULL,
    raw_vc            TEXT NOT NULL,
    created_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (holder_id) REFERENCES holder(holder_id) ON DELETE CASCADE,
    FOREIGN KEY (issuer_id) REFERENCES issuer(issuer_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS presentation (
    presentation_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    holder_id         INTEGER NOT NULL,
    vp_id             TEXT UNIQUE NOT NULL,
    type              TEXT NOT NULL,
    context           TEXT NOT NULL,
    verifiable_credentials TEXT NOT NULL,
    proof             TEXT NOT NULL,
    created_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (holder_id) REFERENCES holder(holder_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS key_pair (
    key_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    holder_id        INTEGER NOT NULL,
    type             TEXT NOT NULL,
    public_key_jwk   TEXT NOT NULL,
    private_key_jwk  TEXT,
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (holder_id) REFERENCES holder(holder_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS audit_log (
    log_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    holder_id        INTEGER,
    action           TEXT NOT NULL,
    details          TEXT,
    timestamp        DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (holder_id) REFERENCES holder(holder_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_credential_holder ON credential(holder_id);
CREATE INDEX IF NOT EXISTS idx_credential_issuer ON credential(issuer_id);
CREATE INDEX IF NOT EXISTS idx_credential_revoked ON credential(revoked);
CREATE INDEX IF NOT EXISTS idx_presentation_holder ON presentation(holder_id);
CREATE INDEX IF NOT EXISTS idx_audit_holder ON audit_log(holder_id);
"""

def create_schema(conn):
    conn.executescript(SCHEMA_SQL)

def sample_data_exists(conn):
    return conn.execute("SELECT COUNT(*) FROM credential").fetchone()[0] > 0

def insert_sample_data(conn):
    # Insert holder
    conn.execute("""
        INSERT OR IGNORE INTO holder (did, display_name, email)
        VALUES (?, ?, ?)
    """, ("did:example:123", "Alice", "alice@example.com"))

    # Insert issuer
    conn.execute("""
        INSERT OR IGNORE INTO issuer (did, display_name, endpoint, public_key_jwk)
        VALUES (?, ?, ?, ?)
    """, (
        "did:example:issuer",
        "Example University",
        "https://example.edu/issuer",
        json.dumps({"kty": "OKP", "crv": "Ed25519", "x": "Base64KeyHere"})
    ))

    holder_id = conn.execute("SELECT holder_id FROM holder WHERE did=?", ("did:example:123",)).fetchone()[0]
    issuer_id = conn.execute("SELECT issuer_id FROM issuer WHERE did=?", ("did:example:issuer",)).fetchone()[0]

    vc_id = "urn:uuid:abc123"
    issuance_time = datetime.utcnow().isoformat() + "Z"

    conn.execute("""
        INSERT OR IGNORE INTO credential (
            holder_id, issuer_id, vc_id, type, context, schema_uri, issuance_date, tags,
            credential_subject, proof, raw_vc
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        holder_id,
        issuer_id,
        vc_id,
        json.dumps(["VerifiableCredential", "UniversityDegreeCredential"]),
        json.dumps(["https://www.w3.org/2018/credentials/v1"]),
        "https://example.edu/schemas/degree.json",
        issuance_time,
        json.dumps(["education", "degree", "computer-science"]),
        json.dumps({
            "id": "did:example:123",
            "degree": {"type": "BachelorDegree", "name": "B.Sc. Computer Science"}
        }),
        json.dumps({
            "type": "Ed25519Signature2018",
            "created": issuance_time,
            "proofPurpose": "assertionMethod",
            "verificationMethod": "did:example:issuer#keys-1",
            "jws": "Base64SignatureHere"
        }),
        json.dumps({
            "@context": ["https://www.w3.org/2018/credentials/v1"],
            "id": vc_id,
            "type": ["VerifiableCredential", "UniversityDegreeCredential"],
            "issuer": "did:example:issuer",
            "issuanceDate": issuance_time
        })
    ))

    # Add audit log entry
    conn.execute("""
        INSERT INTO audit_log (holder_id, action, details)
        VALUES (?, ?, ?)
    """, (
        holder_id,
        "ADD_CREDENTIAL",
        json.dumps({"vc_id": vc_id, "issuer": "Example University"})
    ))

def query_credentials_with_names(conn):
    rows = conn.execute("""
        SELECT c.vc_id, c.type, c.issuance_date, c.revoked, c.tags,
               h.display_name AS holder_name, i.display_name AS issuer_name
        FROM credential c
        JOIN holder h ON c.holder_id = h.holder_id
        JOIN issuer i ON c.issuer_id = i.issuer_id
    """).fetchall()

    print("\nStored Credentials:")
    for row in rows:
        print(f"VC ID: {row[0]}")
        print(f"Type: {row[1]}")
        print(f"Issued: {row[2]}")
        print(f"Revoked: {row[3]}")
        print(f"Tags: {row[4]}")
        print(f"Holder: {row[5]}")
        print(f"Issuer: {row[6]}")
        print("-" * 50)

if __name__ == "__main__":
    with sqlite3.connect(DB
