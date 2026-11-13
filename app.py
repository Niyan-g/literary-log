from flask import Flask, render_template, request, redirect, url_for, session, flash
from api_service import fetch_books
from database import *
import os
from functools import wraps

app = Flask(__name__)
# Read the secret key from the environment so sessions survive restarts and
# work no matter how the app is started (python app.py, flask run, gunicorn).
# The fallback is only for local development — never use it in production.
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")

init_table()


def login_required(func):
    """Redirect to the login page unless the user is logged in."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('home'))
        result = func(*args, **kwargs)
        return result
    return wrapper

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
@login_required
def save():
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
@login_required
def like():
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
@login_required
def unread():
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
@login_required
def review():
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
@login_required
def rate():
    user_id = session.get('user_id')
    title = request.form.get('title')
    author = request.form.get('author')
    year = request.form.get('year')
    cover = request.form.get('cover_url')
    # Reject missing, non-numeric or out-of-range ratings instead of crashing
    try:
        rating = int(request.form.get('rating', ''))
    except ValueError:
        rating = 0
    if not 1 <= rating <= 5:
        flash('Rating must be between 1 and 5.')
        return redirect(request.referrer or url_for('my_list'))

    save_rating(user_id, title, author, year, cover, rating)
    
    return redirect(request.referrer or url_for('my_list'))

@app.route('/remove_book/<int:book_id>', methods=['POST'])
@login_required
def remove_book(book_id):
    
    remove_saved_book(session.get('user_id'), book_id)
    return redirect(request.referrer or url_for('my_list'))

@app.route('/remove_readlist_book/<int:book_id>', methods=['POST'])
@login_required
def remove_from_readlist(book_id):
    remove_readlist_book(session.get('user_id'), book_id)
    return redirect(url_for('my_readlist'))

@app.route('/my-list')
@login_required
def my_list():
    user_id = session.get('user_id')
    saved_books = get_all_saved_books(user_id)
    return render_template('saved.html', books=saved_books)

@app.route('/my-review')
@login_required
def view_reviews():
    user_id = session.get('user_id')
    reviewed_books = get_reviewed_books(user_id)
    return render_template('reviews.html', books=reviewed_books)

@app.route('/my-likes')
@login_required
def my_likes():
    user_id = session.get('user_id')
    liked_books = get_liked_books(user_id)  # FIX: Passes user_id to get_liked_books
    return render_template('liked.html', books=liked_books)

@app.route('/my-readlist')
@login_required
def my_readlist():
    user_id = session.get('user_id')
    readlist_books = get_unread_books(user_id)
    return render_template('readlist.html', books=readlist_books)

@app.route('/my-profile')
@login_required
def my_profile():
    return render_template('profile.html')

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")