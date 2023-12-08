import sqlite3

conn = sqlite3.connect('user_data.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
)
''')
conn.commit()

def create_user(username, password,email):

    cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        return "Username already exists. Please choose another one."

    try:
        
        cursor.execute("INSERT INTO users (username, password, email) VALUES (?, ?,?)", (username, password,email))
        conn.commit()
        return "User created successfully"
    except sqlite3.IntegrityError:
        return "There was an error creating the user."

def login_user(username, password):
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = cursor.fetchone()
    return "Login successful" if user else "Invalid username or password"