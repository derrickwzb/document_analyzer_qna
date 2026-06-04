import sqlite3
from datetime import datetime
from config import DB_NAME

def init_db():
    """Initializes the SQLite database and creates the table if it doesn't exist."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS summaries 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  filename TEXT, 
                  summary TEXT, 
                  category TEXT, 
                  created_at DATETIME)''')
    conn.commit()
    conn.close()


def save_summary(filename, summary, rating, category):
    """Saves a new analysis record to the database."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""INSERT INTO summaries (filename, summary, rating, category, created_at) 
                 VALUES (?, ?, ?, ?, ?)""", 
              (filename, summary, rating, category, datetime.now()))
    conn.commit()
    conn.close()