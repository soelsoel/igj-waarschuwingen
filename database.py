import sqlite3
import os
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'igj_warnings.db')


def get_connection(db_path=None):
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db_path=None):
    conn = get_connection(db_path)
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS warnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guid TEXT UNIQUE NOT NULL,
            title_raw TEXT NOT NULL,
            company TEXT,
            reference_code TEXT,
            apparatus_name TEXT,
            link TEXT NOT NULL,
            description TEXT,
            pub_date TEXT NOT NULL,
            fetched_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_pub_date ON warnings(pub_date DESC);
        CREATE INDEX IF NOT EXISTS idx_guid ON warnings(guid);

        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    """)

    # Create FTS5 table if it doesn't exist
    try:
        cur.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS warnings_fts USING fts5(
                title_raw, company, apparatus_name, description,
                content='warnings', content_rowid='id'
            )
        """)

        # Triggers to keep FTS in sync
        cur.executescript("""
            CREATE TRIGGER IF NOT EXISTS warnings_ai AFTER INSERT ON warnings BEGIN
                INSERT INTO warnings_fts(rowid, title_raw, company, apparatus_name, description)
                VALUES (new.id, new.title_raw, new.company, new.apparatus_name, new.description);
            END;

            CREATE TRIGGER IF NOT EXISTS warnings_ad AFTER DELETE ON warnings BEGIN
                INSERT INTO warnings_fts(warnings_fts, rowid, title_raw, company, apparatus_name, description)
                VALUES ('delete', old.id, old.title_raw, old.company, old.apparatus_name, old.description);
            END;

            CREATE TRIGGER IF NOT EXISTS warnings_au AFTER UPDATE ON warnings BEGIN
                INSERT INTO warnings_fts(warnings_fts, rowid, title_raw, company, apparatus_name, description)
                VALUES ('delete', old.id, old.title_raw, old.company, old.apparatus_name, old.description);
                INSERT INTO warnings_fts(rowid, title_raw, company, apparatus_name, description)
                VALUES (new.id, new.title_raw, new.company, new.apparatus_name, new.description);
            END;
        """)
    except Exception:
        # FTS5 not available — search will fall back to LIKE
        pass

    conn.commit()
    conn.close()


def insert_warning(conn, warning):
    """Insert a warning, ignoring duplicates by guid. Returns True if inserted."""
    try:
        conn.execute(
            """INSERT OR IGNORE INTO warnings
               (guid, title_raw, company, reference_code, apparatus_name, link, description, pub_date)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                warning['guid'],
                warning['title_raw'],
                warning.get('company'),
                warning.get('reference_code'),
                warning.get('apparatus_name'),
                warning['link'],
                warning.get('description'),
                warning['pub_date'],
            )
        )
        conn.commit()
        return conn.total_changes > 0
    except sqlite3.Error:
        return False


def get_recent_warnings(conn, limit=20):
    return conn.execute(
        "SELECT * FROM warnings ORDER BY pub_date DESC LIMIT ?", (limit,)
    ).fetchall()


def get_warning_by_guid(conn, guid):
    return conn.execute(
        "SELECT * FROM warnings WHERE guid = ?", (guid,)
    ).fetchone()


def get_all_warnings(conn, page=1, per_page=20):
    offset = (page - 1) * per_page
    rows = conn.execute(
        "SELECT * FROM warnings ORDER BY pub_date DESC LIMIT ? OFFSET ?",
        (per_page, offset)
    ).fetchall()
    total = conn.execute("SELECT COUNT(*) FROM warnings").fetchone()[0]
    return rows, total


def search_warnings(conn, query, limit=50):
    """Search using FTS5, falling back to LIKE if FTS5 is unavailable."""
    if not query or not query.strip():
        return []
    try:
        return conn.execute(
            """SELECT w.* FROM warnings_fts fts
               JOIN warnings w ON w.id = fts.rowid
               WHERE warnings_fts MATCH ?
               ORDER BY rank
               LIMIT ?""",
            (query, limit)
        ).fetchall()
    except sqlite3.OperationalError:
        # FTS5 not available, fall back to LIKE
        like = f"%{query}%"
        return conn.execute(
            """SELECT * FROM warnings
               WHERE title_raw LIKE ? OR company LIKE ?
                     OR apparatus_name LIKE ? OR description LIKE ?
               ORDER BY pub_date DESC LIMIT ?""",
            (like, like, like, like, limit)
        ).fetchall()


def get_last_fetch_time(conn):
    row = conn.execute(
        "SELECT value FROM metadata WHERE key = 'last_fetch_time'"
    ).fetchone()
    if row:
        return datetime.fromisoformat(row[0])
    return None


def set_last_fetch_time(conn):
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT OR REPLACE INTO metadata (key, value) VALUES ('last_fetch_time', ?)",
        (now,)
    )
    conn.commit()
