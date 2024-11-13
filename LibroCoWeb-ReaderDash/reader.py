import sqlite3  # Import sqlite3

# Connect to the correct database (libroco.db)
conn = sqlite3.connect('libroco.db')  # Open connection to the correct SQLite DB
cursor = conn.cursor()  # Create a cursor object to interact with the database

# Create the tables in the correct database
cursor.execute(''' 
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_full_name TEXT NOT NULL,
    user_email TEXT NOT NULL UNIQUE,
    user_password TEXT NOT NULL,
    user_contact TEXT,
    profile_image TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS books (
    book_id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_title TEXT NOT NULL,
    author TEXT NOT NULL,
    publication_year TEXT,
    genre TEXT,
    description TEXT,
    image TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS wishlist (
    wishlist_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    book_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (book_id) REFERENCES books(book_id)
)
''')

# Commit changes and close connection
conn.commit()
conn.close()
