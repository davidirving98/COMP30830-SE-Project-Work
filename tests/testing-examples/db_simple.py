# db_simple.py
import sqlite3

# Connect to the SQLite database (file-based)
def get_connection():
    return sqlite3.connect("test.db")  # Uses a file-based database (persists data)

# Create a table
def create_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Insert a user into the database
def insert_user(name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()

# Retrieve a user by name
def get_user(name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE name = ?", (name,))
    user = cursor.fetchone()  # Fetch one row
    conn.close()
    return user  # Returns a tuple (id, name) if found, else None
