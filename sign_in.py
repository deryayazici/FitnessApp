import sqlite3

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect("users.db")
    return g.db


conn = get_db
c  = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
)
''')
conn.commit()

def create_user(username, password,email):

    c.execute("SELECT username FROM users WHERE username = ?", (username,))
    if c.fetchone():
        return "Username already exists. Please choose another one."

    try:
        
        c.execute("INSERT INTO users (username, password, email) VALUES (?, ?,?)", (username, password,email))
        conn.commit()
        return "User created successfully"
    except sqlite3.IntegrityError:
        return "There was an error creating the user."

# def login_user(username, password):
#     cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
#     user = cursor.fetchone()
#     return "Login successful" if user else "Invalid username or password"