import hashlib
import sqlite3
from datetime import datetime
from config import chroma_directory,chroma_collection,db_name
from langchain_chroma import Chroma
from utils.embed import get_embedding_model

def get_vector_store():
    # Build a Chroma client for the configured collection.
    return Chroma(
        persist_directory=chroma_directory,
        embedding_function=get_embedding_model(),
        collection_name=chroma_collection,
    )

def _connect():
    # Open a SQLite connection to the configured history database.
    return sqlite3.connect(db_name)


def _column_exists(cursor, table_name, column_name):
    # Check whether a table already contains a specific column.
    cursor.execute(f"PRAGMA table_info({table_name})")
    return any(row[1] == column_name for row in cursor.fetchall())


def init_db():
    # Create the documents, sessions, and messages tables if they do not exist.
    conn = _connect()
    c = conn.cursor()

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            file_hash TEXT NOT NULL UNIQUE,
            created_at DATETIME
        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER,
            title TEXT,
            created_at DATETIME,
            FOREIGN KEY(document_id) REFERENCES documents(id)
        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            role TEXT,
            content TEXT,
            timestamp DATETIME,
            FOREIGN KEY(session_id) REFERENCES sessions(id)
        )
        """
    )

    if not _column_exists(c, "sessions", "document_id"):
        c.execute("ALTER TABLE sessions ADD COLUMN document_id INTEGER")

    conn.commit()
    conn.close()


def compute_file_hash(file_bytes):
    # Hash uploaded file bytes so duplicate documents can be detected.
    return hashlib.sha256(file_bytes).hexdigest()


def get_documents():
    # Return stored documents ordered from newest to oldest.
    conn = _connect()
    c = conn.cursor()
    c.execute(
        """
        SELECT id, file_name, file_hash, created_at
        FROM documents
        ORDER BY created_at DESC
        """
    )
    data = c.fetchall()
    conn.close()
    return data


def get_document_by_hash(file_hash):
    # Look up an existing document by its content hash.
    conn = _connect()
    c = conn.cursor()
    c.execute(
        """
        SELECT id, file_name, file_hash, created_at
        FROM documents
        WHERE file_hash = ?
        """,
        (file_hash,),
    )
    row = c.fetchone()
    conn.close()
    return row


def get_document(document_id):
    # Fetch one stored document row by ID.
    conn = _connect()
    c = conn.cursor()
    c.execute(
        """
        SELECT id, file_name, file_hash, created_at
        FROM documents
        WHERE id = ?
        """,
        (document_id,),
    )
    row = c.fetchone()
    conn.close()
    return row


def delete_document(document_id):
    # Delete a document row from SQLite by ID.
    conn = _connect()
    c = conn.cursor()
    c.execute(
        """
        DELETE FROM documents
        WHERE id = ?
        """,
        (document_id,),
    )
    deleted = c.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def create_document(file_name, file_hash):
    # Insert a new stored document row and return its ID.
    conn = _connect()
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO documents (file_name, file_hash, created_at)
        VALUES (?, ?, ?)
        """,
        (file_name, file_hash, datetime.now()),
    )
    document_id = c.lastrowid
    conn.commit()
    conn.close()
    return document_id


def get_or_create_document(file_name, file_bytes):
    # Reuse an existing document when the uploaded file hash already exists.
    file_hash = compute_file_hash(file_bytes)
    existing = get_document_by_hash(file_hash)
    if existing:
        return existing[0], False
    return create_document(file_name, file_hash), True


def get_sessions():
    # Return chat sessions joined with their document names for the sidebar.
    conn = _connect()
    c = conn.cursor()
    c.execute(
        """
        SELECT sessions.id, sessions.title, sessions.document_id, documents.file_name
        FROM sessions
        LEFT JOIN documents ON documents.id = sessions.document_id
        ORDER BY sessions.created_at DESC
        """
    )
    data = c.fetchall()
    conn.close()
    return data


def create_session(document_id, title="New Chat"):
    # Create a fresh chat session linked to one document.
    conn = _connect()
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO sessions (document_id, title, created_at)
        VALUES (?, ?, ?)
        """,
        (document_id, title, datetime.now()),
    )
    session_id = c.lastrowid
    conn.commit()
    conn.close()
    return session_id


def get_document_id_for_session(session_id):
    # Find the document ID associated with a chat session.
    conn = _connect()
    c = conn.cursor()
    c.execute(
        """
        SELECT document_id
        FROM sessions
        WHERE id = ?
        """,
        (session_id,),
    )
    row = c.fetchone()
    conn.close()
    return row[0] if row else None


def delete_sessions_for_document(document_id):
    # Remove all sessions and messages linked to one document.
    conn = _connect()
    c = conn.cursor()
    c.execute(
        """
        SELECT id
        FROM sessions
        WHERE document_id = ?
        """,
        (document_id,),
    )
    session_ids = [row[0] for row in c.fetchall()]

    if session_ids:
        placeholders = ",".join("?" for _ in session_ids)
        c.execute(
            f"""
            DELETE FROM messages
            WHERE session_id IN ({placeholders})
            """,
            session_ids,
        )
        c.execute(
            """
            DELETE FROM sessions
            WHERE document_id = ?
            """,
            (document_id,),
        )

    conn.commit()
    conn.close()
    return len(session_ids)


def save_message(session_id, role, content):
    # Store a chat message and update the session title from the first user prompt.
    conn = _connect()
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO messages (session_id, role, content, timestamp)
        VALUES (?, ?, ?, ?)
        """,
        (session_id, role, content, datetime.now()),
    )

    if role == "user":
        c.execute("SELECT COUNT(*) FROM messages WHERE session_id = ?", (session_id,))
        if c.fetchone()[0] == 1:
            title = content[:30] + "..." if len(content) > 30 else content
            c.execute("UPDATE sessions SET title = ? WHERE id = ?", (title, session_id))

    conn.commit()
    conn.close()


def get_chat_history(session_id):
    # Return the ordered message history for one chat session.
    conn = _connect()
    c = conn.cursor()
    c.execute(
        """
        SELECT role, content
        FROM messages
        WHERE session_id = ?
        ORDER BY timestamp ASC
        """,
        (session_id,),
    )
    messages = [{"role": row[0], "content": row[1]} for row in c.fetchall()]
    conn.close()
    return messages
