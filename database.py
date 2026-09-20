import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

DB_NAME = "bookshelf.db"

def init_table():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saved_books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            author TEXT,
            year TEXT,
            cover_url TEXT,
            status TEXT DEFAULT 'Read',
            rating INTEGER DEFAULT 0,
            review TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id))
    ''')

    try:
        cursor.execute("ALTER TABLE saved_books ADD COLUMN review TEXT")
    except sqlite3.OperationalError:
        pass 

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS readlist_books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            author TEXT,
            year TEXT,
            cover_url TEXT
        )
    ''')

    cursor.execute('''
       CREATE TABLE IF NOT EXISTS users(
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           username TEXT UNIQUE NOT NULL,
           password_hash TEXT NOT NULL
       )
    ''')
    conn.commit()
    conn.close()

def create_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    hashed_pw = generate_password_hash(password)
    try:
        cursor.execute('''
            INSERT INTO users (username, password_hash) 
            VALUES (?, ?)
        ''', (username, hashed_pw))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  
    finally:
        conn.close()

def verify_user(username, password):
    """Verifies stored password hash and returns the integer user_id if valid, else None."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user and check_password_hash(user['password_hash'], password):
        return user['id']  # FIX: Return integer ID instead of True
    return None

def save_books(user_id, title, author, year, cover_url, status='Read', rating=0):
    if cover_url and str(cover_url).startswith('http://'):
        cover_url = str(cover_url).replace('http://', 'https://', 1)
        
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, cover_url, rating FROM saved_books WHERE user_id = ? AND title = ?", (user_id, title))
    existing = cursor.fetchone()
    
    if existing:
        final_cover = cover_url if cover_url else existing[1]
        # Use new rating if provided (greater than 0), otherwise keep existing rating
        final_rating = rating if rating > 0 else existing[2]
        
        cursor.execute(
            "UPDATE saved_books SET author = ?, year = ?, cover_url = ?, status = ?, rating = ? WHERE id = ?",
            (author, year, final_cover, status, final_rating, existing[0])
        )
    else:
        cursor.execute(
            "INSERT INTO saved_books (user_id, title, author, year, cover_url, status, rating) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, title, author, year, cover_url, status, rating)
        )
    conn.commit()
    conn.close()


def save_rating(user_id, title, author, year, cover_url, rating):
    """Updates or inserts a rating directly for a book."""
    if cover_url and str(cover_url).startswith('http://'):
        cover_url = str(cover_url).replace('http://', 'https://', 1)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM saved_books WHERE user_id = ? AND title = ?", (user_id, title))
    existing = cursor.fetchone()

    if existing:
        cursor.execute(
            "UPDATE saved_books SET rating = ? WHERE id = ?",
            (rating, existing[0])
        )
    else:
        cursor.execute(
            "INSERT INTO saved_books (user_id, title, author, year, cover_url, status, rating) VALUES (?, ?, ?, ?, ?, 'Read', ?)",
            (user_id, title, author, year, cover_url, rating)
        )
    conn.commit()
    conn.close()

def like_books(user_id, title, author, year, cover_url, status='Liked', rating=0):
    # Route through save_books to handle duplicate prevention and status updates seamlessly
    save_books(user_id, title, author, year, cover_url, status=status, rating=rating)

def unread_books(user_id, title, author, year, cover_url):
    if cover_url and cover_url.startswith('http://'):
        cover_url = cover_url.replace('http://', 'https://', 1)
        
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO readlist_books (user_id, title, author, year, cover_url)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, title, author, year, cover_url))
    conn.commit()
    conn.close()

def save_review(user_id, title, author, year, cover_url, review_text):
    if cover_url and str(cover_url).startswith('http://'):
        cover_url = str(cover_url).replace('http://', 'https://', 1)
        
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, cover_url FROM saved_books WHERE user_id = ? AND title = ?", (user_id, title))
    existing = cursor.fetchone()
    
    if existing:
        # Update review AND fill in cover_url if it was previously missing
        final_cover = cover_url if cover_url else existing[1]
        cursor.execute(
            "UPDATE saved_books SET review = ?, cover_url = ? WHERE id = ?",
            (review_text, final_cover, existing[0])
        )
    else:
        cursor.execute('''
            INSERT INTO saved_books (user_id, title, author, year, cover_url, status, review)
            VALUES (?, ?, ?, ?, ?, 'Read', ?)
        ''', (user_id, title, author, year, cover_url, review_text))
    conn.commit()
    conn.close()

def get_reviewed_books(user_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM saved_books WHERE user_id = ? AND review IS NOT NULL AND review != ""', (user_id,))
    books = cursor.fetchall()
    conn.close()
    return books    

def get_unread_books(user_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM readlist_books WHERE user_id = ?', (user_id,))
    books = cursor.fetchall()
    conn.close()
    return books

def get_all_saved_books(user_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM saved_books WHERE user_id = ?', (user_id,))
    books = cursor.fetchall()
    conn.close()
    return books

def get_books_by_status(user_id, status_type):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # FIX: Allows key-based access like book['cover_url'] in templates
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM saved_books WHERE user_id = ? AND status = ?', (user_id, status_type))
    books = cursor.fetchall()
    conn.close()
    return books

def get_liked_books(user_id):
    return get_books_by_status(user_id, 'Liked')