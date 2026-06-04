import sqlite3
from datetime import datetime
import config

def init_db():
    """
    Creates the database tables if they do not exist yet.
    Sets up a relational structure linking 'messages' back to specific 'sessions'.
    """
    conn = sqlite3.connect(config.DB_NAME)
    c = conn.cursor()
    
    # Create the 'sessions' parent table
    c.execute('''CREATE TABLE IF NOT EXISTS sessions 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 document_id TEXT NOT NULL,
                  title TEXT, 
                  created_at DATETIME)''')
                  
    # Create the 'messages' child table with a foreign key referencing the parent table
    c.execute('''CREATE TABLE IF NOT EXISTS messages 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  session_id INTEGER,
                  role TEXT, 
                  content TEXT, 
                  timestamp DATETIME,
                  FOREIGN KEY(session_id) REFERENCES sessions(id))''')
    conn.commit()
    conn.close()

def get_sessions():
    """
    Fetches all unique chat sessions from the database, sorted newest first.
    Returns a list of tuples: [(id, title), (id, title), ...]
    """
    conn = sqlite3.connect(config.DB_NAME)
    c = conn.cursor()
    c.execute(
        """
        SELECT id, title, document_id
        FROM sessions
        ORDER BY created_at DESC
        """
    )
    data = c.fetchall()
    conn.close()
    return data

def create_session(document_id, title="New Chat"):
    conn = sqlite3.connect(config.DB_NAME)
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

def get_session_by_document(document_id):
    conn = sqlite3.connect(config.DB_NAME)
    c = conn.cursor()
    c.execute(
        """
        SELECT id, title, document_id
        FROM sessions
        WHERE document_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (document_id,),
    )
    row = c.fetchone()
    conn.close()
    return row

def get_document_id_for_session(session_id):
    conn = sqlite3.connect(config.DB_NAME)
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

def save_message(session_id, role, content):
    conn = sqlite3.connect(config.DB_NAME)
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
    conn = sqlite3.connect(config.DB_NAME)
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