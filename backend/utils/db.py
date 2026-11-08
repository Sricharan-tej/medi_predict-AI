import sqlite3
from config import Config

def get_db():
    """
    Returns a connection to the SQLite database.
    Sets row_factory to sqlite3.Row for dictionary-like access.
    """
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn
