from flask import Flask, render_template, request, redirect, url_for, session, flash
from api_service import fetch_books
from database import *
import os

app = Flask(__name__)

init_table()

@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    search_query = request.args.get('q', 'subject:classics')
    books_data = fetch_books(search_query) 
    return render_template("starterhtml.html", books=books_data)

@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            flash('Please fill out all fields!')
            return render_template('signup.html')
            
        if create_user(username, password):
            flash('Account created successfully! Please log in.')
            return redirect(url_for('home'))
        else:
            flash('Username already exists. Try another.')
            
    return render_template('signup.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    user_id = verify_user(username, password)
    
    if user_id:  # FIX: Checks for valid user ID
        session['logged_in'] = True
        session['username'] = username
        session['user_id'] = user_id
        return redirect(url_for('home'))
    
    flash('Invalid username or password!')
    return redirect(url_for('home'))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/save_book', methods=['POST'])
def save():
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    user_id = session.get('user_id')
    title = request.form.get('title')
    author = request.form.get('author')
    year = request.form.get('year')
    cover = request.form.get('cover_url')
    status = request.form.get('status', 'Read')
    query = request.form.get('search_query')
    
    save_books(user_id, title, author, year, cover, status)
    
    if query:
        return redirect(url_for('home', q=query))
    return redirect(url_for('home'))

@app.route('/like_book', methods=['POST'])
def like():
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    user_id = session.get('user_id')
    title = request.form.get('title')
    author = request.form.get('author')
    year = request.form.get('year')
    cover_url = request.form.get('cover_url', '')
    query = request.form.get('search_query')
    
    like_books(user_id, title, author, year, cover_url)
    
    if query:
        return redirect(url_for('home', q=query))
    return redirect(url_for('home'))

@app.route('/unread_book', methods=['POST'])
def unread():
    if not session.get('logged_in'):
        return redirect(url_for('home'))

    user_id = session.get('user_id')
    title = request.form.get('title')
    author = request.form.get('author')
    year = request.form.get('year')
    cover = request.form.get('cover_url')
    query = request.form.get('search_query')
    
    unread_books(user_id, title, author, year, cover)
    
    if query:
        return redirect(url_for('home', q=query))
    return redirect(url_for('home'))

@app.route('/review_book', methods=['POST'])
def review():
    if not session.get('logged_in'):
        return redirect(url_for('home'))

    user_id = session.get('user_id')
    title = request.form.get('title')
    author = request.form.get('author')
    year = request.form.get('year')
    cover = request.form.get('cover_url')
    review_text = request.form.get('review_text')
    query = request.form.get('search_query')
    
    save_review(user_id, title, author, year, cover, review_text)
    
    if query:
        return redirect(url_for('home', q=query))
    return redirect(url_for('home'))

@app.route('/rate_book', methods=['POST'])
def rate():
    if not session.get('logged_in'):
        return redirect(url_for('home'))

    user_id = session.get('user_id')
    title = request.form.get('title')
    author = request.form.get('author')
    year = request.form.get('year')
    cover = request.form.get('cover_url')
    rating = int(request.form.get('rating', 0))

    # Save specifically via save_rating
    save_rating(user_id, title, author, year, cover, rating)
    
    return redirect(request.referrer or url_for('my_list'))

@app.route('/remove_book/<int:book_id>', methods=['POST'])
def remove_book(book_id):
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    
    user_id = session.get('user_id')    
    conn = sqlite3.connect("bookshelf.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM saved_books WHERE id = ? AND user_id = ?", (book_id, user_id))
    conn.commit()
    conn.close()
    
    return redirect(request.referrer or url_for('my_list'))

@app.route('/my-list')
def my_list():
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    user_id = session.get('user_id')
    saved_books = get_all_saved_books(user_id)
    return render_template('saved.html', books=saved_books)

@app.route('/my-review')
def view_reviews():
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    user_id = session.get('user_id')
    reviewed_books = get_reviewed_books(user_id)
    return render_template('reviews.html', books=reviewed_books)

@app.route('/my-likes')
def my_likes():
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    user_id = session.get('user_id')
    liked_books = get_liked_books(user_id)  # FIX: Passes user_id to get_liked_books
    return render_template('liked.html', books=liked_books)

@app.route('/my-readlist')
def my_readlist():
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    user_id = session.get('user_id')
    readlist_books = get_unread_books(user_id)
    return render_template('readlist.html', books=readlist_books)

@app.route('/my-profile')
def my_profile():
    return render_template('profile.html')

if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True)