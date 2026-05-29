"""
J.A.V.I.S. Database — SQLite storage for messages, conversations, contacts, logs
"""
import sqlite3
import datetime
from config import DATABASE_PATH


def get_conn():
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS contacts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            identifier  TEXT UNIQUE NOT NULL,   -- email addr or phone number
            name        TEXT DEFAULT '',
            channel     TEXT DEFAULT 'email',   -- 'email' | 'sms'
            first_seen  TEXT,
            last_seen   TEXT,
            total_msgs  INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS conversations (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id  INTEGER NOT NULL,
            subject     TEXT DEFAULT '',
            status      TEXT DEFAULT 'open',    -- 'open' | 'resolved'
            created_at  TEXT,
            updated_at  TEXT,
            FOREIGN KEY (contact_id) REFERENCES contacts(id)
        );

        CREATE TABLE IF NOT EXISTS messages (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            direction       TEXT NOT NULL,      -- 'inbound' | 'outbound'
            body            TEXT NOT NULL,
            ai_draft        TEXT DEFAULT '',    -- AI-generated reply draft
            status          TEXT DEFAULT 'pending',  -- 'pending'|'approved'|'sent'|'auto_sent'
            created_at      TEXT,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        );

        CREATE TABLE IF NOT EXISTS activity_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            event       TEXT NOT NULL,
            detail      TEXT DEFAULT '',
            created_at  TEXT
        );
    """)

    conn.commit()
    conn.close()
    print("[JAVIS-DB] Database initialised:", DATABASE_PATH)


def log_event(event: str, detail: str = ""):
    conn = get_conn()
    conn.execute(
        "INSERT INTO activity_log (event, detail, created_at) VALUES (?, ?, ?)",
        (event, detail, datetime.datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()


def upsert_contact(identifier: str, channel: str, name: str = "") -> int:
    now = datetime.datetime.utcnow().isoformat()
    conn = get_conn()
    row = conn.execute("SELECT id FROM contacts WHERE identifier=?", (identifier,)).fetchone()
    if row:
        conn.execute(
            "UPDATE contacts SET last_seen=?, total_msgs=total_msgs+1 WHERE id=?",
            (now, row["id"])
        )
        conn.commit()
        cid = row["id"]
    else:
        cur = conn.execute(
            "INSERT INTO contacts (identifier, name, channel, first_seen, last_seen, total_msgs) VALUES (?,?,?,?,?,1)",
            (identifier, name, channel, now, now)
        )
        conn.commit()
        cid = cur.lastrowid
    conn.close()
    return cid


def save_inbound_message(contact_id: int, subject: str, body: str, ai_draft: str) -> int:
    now = datetime.datetime.utcnow().isoformat()
    conn = get_conn()

    # Find or create open conversation
    conv = conn.execute(
        "SELECT id FROM conversations WHERE contact_id=? AND status='open' ORDER BY id DESC LIMIT 1",
        (contact_id,)
    ).fetchone()

    if conv:
        conv_id = conv["id"]
        conn.execute("UPDATE conversations SET updated_at=? WHERE id=?", (now, conv_id))
    else:
        cur = conn.execute(
            "INSERT INTO conversations (contact_id, subject, status, created_at, updated_at) VALUES (?,?,?,?,?)",
            (contact_id, subject, "open", now, now)
        )
        conv_id = cur.lastrowid

    cur = conn.execute(
        "INSERT INTO messages (conversation_id, direction, body, ai_draft, status, created_at) VALUES (?,?,?,?,?,?)",
        (conv_id, "inbound", body, ai_draft, "pending", now)
    )
    conn.commit()
    msg_id = cur.lastrowid
    conn.close()
    return msg_id


def mark_message_sent(msg_id: int, auto: bool = False):
    status = "auto_sent" if auto else "sent"
    conn = get_conn()
    conn.execute("UPDATE messages SET status=? WHERE id=?", (status, msg_id))
    conn.commit()
    conn.close()


def get_pending_messages():
    conn = get_conn()
    rows = conn.execute("""
        SELECT m.id, m.body, m.ai_draft, m.created_at,
               c.identifier, c.name, c.channel,
               conv.subject, conv.id as conv_id
        FROM messages m
        JOIN conversations conv ON m.conversation_id = conv.id
        JOIN contacts c ON conv.contact_id = c.id
        WHERE m.status = 'pending'
        ORDER BY m.created_at DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_conversations(limit: int = 50):
    conn = get_conn()
    rows = conn.execute("""
        SELECT conv.id, conv.subject, conv.status, conv.updated_at,
               c.identifier, c.name, c.channel,
               COUNT(m.id) as msg_count
        FROM conversations conv
        JOIN contacts c ON conv.contact_id = c.id
        LEFT JOIN messages m ON m.conversation_id = conv.id
        GROUP BY conv.id
        ORDER BY conv.updated_at DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_stats():
    conn = get_conn()
    today = datetime.datetime.utcnow().date().isoformat()
    stats = {
        "total_messages"   : conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0],
        "pending_approval" : conn.execute("SELECT COUNT(*) FROM messages WHERE status='pending'").fetchone()[0],
        "sent_today"       : conn.execute("SELECT COUNT(*) FROM messages WHERE (status='sent' OR status='auto_sent') AND created_at LIKE ?", (today+"%",)).fetchone()[0],
        "open_conversations": conn.execute("SELECT COUNT(*) FROM conversations WHERE status='open'").fetchone()[0],
        "total_contacts"   : conn.execute("SELECT COUNT(*) FROM contacts").fetchone()[0],
    }
    conn.close()
    return stats
