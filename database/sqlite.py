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
    c.execute("SELECT id, title FROM sessions ORDER BY created_at DESC")
    data = c.fetchall()
    conn.close()
    return data

def create_session(title="New Chat"):
    """
    Inserts a fresh conversation session record into the sessions table.
    Returns the unique auto-incremented primary key ID of the new row.
    """
    conn = sqlite3.connect(config.DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO sessions (title, created_at) VALUES (?, ?)", 
              (title, datetime.now()))
    session_id = c.lastrowid  # Captures the unique ID automatically assigned to this row
    conn.commit()
    conn.close()
    return session_id

def save_message(session_id, role, content):
    """
    Saves an individual message dialogue log (user or assistant) to the database.
    If it is the very first user message in this session, it renames the placeholder session title.
    """
    conn = sqlite3.connect(config.DB_NAME)
    c = conn.cursor()
    
    # 1. Log the message entry
    c.execute("INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
              (session_id, role, content, datetime.now()))
    
    # 2. Automatically generate a dynamic chat title from the first prompt
    if role == "user":
        c.execute("SELECT COUNT(*) FROM messages WHERE session_id = ?", (session_id,))
        if c.fetchone()[0] == 1:
            # Shorten the message preview string if it exceeds 30 characters
            title = content[:30] + "..." if len(content) > 30 else content
            c.execute("UPDATE sessions SET title = ? WHERE id = ?", (title, session_id))
            
    conn.commit()
    conn.close()

def get_chat_history(session_id):
    """
    Retrieves all past messages for a single session ID.
    Transforms raw database records into standard dictionary arrays required by the LLM SDK.
    """
    conn = sqlite3.connect(config.DB_NAME)
    c = conn.cursor()
    c.execute("SELECT role, content FROM messages WHERE session_id = ? ORDER BY timestamp ASC", (session_id,))
    
    # Map tabular database results into key-value pairs matching LLM expectations
    messages = [{"role": row[0], "content": row[1]} for row in c.fetchall()]
    conn.close()
    return messages