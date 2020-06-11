import os
import requests

from flask import Flask, session, render_template, request, redirect, url_for, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import math

os.environ['DATABASE_URL'] = "postgres://cirmwacpuuhlha:e98f033dd24351340531cdb496cd6ef069b6a2ecff3f52fdbefbdcd50f95fc19@ec2-54-247-122-209.eu-west-1.compute.amazonaws.com:5432/d18fs835ggnl48"
KEY = "e98f033dd24351340531cdb496cd6ef069b6a2ecff3f52fdbefbdcd50f95fc19"

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# code snippet against browser cache for development
@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)


def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                     endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)
# end of code snippet against browser cache for development


@app.route("/logout")
def logout():
    session['logged_in'] = False
    session['username'] = ""
    return redirect(url_for('index'))


@app.route("/")
def index():
    if session.get('logged_in') == None or False:
        session['logged_in'] = False
        session['username'] = ''
        return render_template("index.html", logged_in=session['logged_in'])
    username = session.get('username')
    return render_template("index.html", username=username, logged_in=session['logged_in'])


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/register-user", methods=["POST"])
def register_user():
    username = request.form.get("username")
    password = request.form.get("password")
    if db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).rowcount > 0:
        return render_template("error.html", message="This username is not available")
    db.execute("INSERT INTO users (username, password) VALUES (:username, :password)",
               {"username": username, "password": password})
    db.commit()
    return render_template("success.html")


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")
    if db.execute("SELECT * FROM users WHERE username = :username AND password = :password",
                  {"username": username, "password": password}).rowcount == 1:
        user = db.execute("SELECT * FROM users WHERE username = :username AND password = :password",
                          {"username": username, "password": password}).fetchone()
        session['logged_in'] = True
        session['user_id'] = user.id
        session['username'] = user.username
        return redirect(url_for('book_search'))
    else:
        session['logged_in'] = False
        return redirect(url_for('index'))


def query_total_result(column, query):
    if column == "title":
        total_result = db.execute(
            "SELECT * FROM books WHERE LOWER(title) LIKE (LOWER(:query) || '%')", {"query": query}).rowcount
        return total_result
    if column == "author":
        total_result = db.execute(
            "SELECT * FROM books WHERE LOWER(author) LIKE (LOWER(:query) || '%')", {"query": query}).rowcount
        return total_result
    if column == "isbn":
        total_result = db.execute(
            "SELECT * FROM books WHERE LOWER(isbn) LIKE (LOWER(:query) || '%')", {"query": query}).rowcount
        return total_result


def query_books(column, query, page, per_page):
    offset_num = (page-1) * per_page
    if column == "title":
        search_result = db.execute(
            "SELECT * FROM books WHERE LOWER(title) LIKE (LOWER(:query) || '%') ORDER BY title ASC LIMIT :per_page OFFSET :offset_num", {"query": query, "per_page": per_page, "offset_num": offset_num}).fetchall()
        return search_result
    if column == "author":
        search_result = db.execute(
            "SELECT * FROM books WHERE LOWER(author) LIKE (LOWER(:query) || '%') ORDER BY title ASC LIMIT :per_page OFFSET :offset_num", {"query": query, "per_page": per_page, "offset_num": offset_num}).fetchall()
        return search_result
    if column == "isbn":
        search_result = db.execute(
            "SELECT * FROM books WHERE LOWER(isbn) LIKE (LOWER(:query) || '%') ORDER BY title ASC LIMIT :per_page OFFSET :offset_num", {"query": query, "per_page": per_page, "offset_num": offset_num}).fetchall()
        return search_result


@app.route("/book-search", methods=["GET", "POST"])
def book_search():
    if session['logged_in'] == False:
        return redirect(url_for('index'))
    else:
        per_page = 20
        page = 1
        if request.method == 'GET':
            total_pages = 1
            # fetch 20 books
            books_initial = db.execute(
                "SELECT * FROM books ORDER BY title ASC LIMIT :per_page", {"per_page": per_page}).fetchall()
            return render_template("book-search.html", username=session.get("username"), books=books_initial, page=page, total_pages=total_pages)
        else:
            try:
                query = request.form.get("title")
                column = "title"
                if query == None:
                    query = request.form.get("author")
                    column = "author"
                if query == None:
                    query = request.form.get("isbn")
                    column = "isbn"
            except ValueError:
                return render_template("error.html", message="Invalid search criteria")
            return redirect(url_for('paginate', column=column, page=page, query=query))


@app.route("/book-search/<column>/<int:page>/<query>")
def paginate(column, page, query):
    if session['logged_in'] == False:
        return redirect(url_for('index'))
    else:
        per_page = 20
        total_result = query_total_result(column, query)
        search_result = query_books(column, query, page, per_page)
        total_pages = math.ceil((total_result / per_page))
        if len(search_result) == 0:
            return render_template("error.html", message="Sorry, there is no book in our inventory according to your search criteria")
        else:
            return render_template("book-search.html", username=session.get("username"),
                                   books=search_result, page=page, total_pages=total_pages, column=column, query=query)


@app.route("/book/<isbn>")
def goto_book_page(isbn):
    if session['logged_in'] == False:
        return redirect(url_for('index'))
    else:
        res = requests.get("https://www.goodreads.com/book/review_counts.json",
                           params={"key": "T1GNWtVnkUqq4k4alkHA", "isbns": isbn}).json()
        goodreads_average_rating = res['books'][0]['average_rating']
        book = db.execute(
            "SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
        reviews = db.execute(
            "SELECT * FROM reviews WHERE book_isbn = :book_isbn", {"book_isbn": isbn}).fetchall()
        return render_template("book.html", username=session.get("username"), book=book, reviews=reviews, goodreads_average_rating=goodreads_average_rating)


@app.route("/book/<isbn>/review", methods=["POST"])
def review(isbn):
    rating = request.form.get("rating")
    comment = request.form.get("comment")
    if db.execute("SELECT * FROM reviews WHERE book_isbn = :book_isbn AND user_id = :user_id",
                  {"book_isbn": isbn, "user_id": session.get("user_id")}).rowcount >= 1:
        return render_template("error.html", message="You may review only one time per book")
    db.execute(
        "INSERT INTO reviews (rating, comment, user_id, book_isbn) VALUES (:rating, :comment, :user_id, :book_isbn)", {"rating": rating, "comment": comment, "user_id": session.get("user_id"), "book_isbn": isbn})
    db.commit()
    return redirect(url_for('goto_book_page', isbn=isbn))


@app.route("/api/<isbn>")
def api_isbn(isbn):
    book = db.execute(
        "SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    if book is None:
        return jsonify({"error": "Book is not in our inventory"}), 404
    review_count = db.execute(
        "SELECT * FROM reviews WHERE book_isbn = :book_isbn", {"book_isbn": isbn}).rowcount
    if review_count > 0:
        average_score_object = db.execute("SELECT AVG (rating) FROM reviews WHERE book_isbn = :book_isbn", {
            "book_isbn": isbn}).fetchone()
    for row in average_score_object:
        average_score = float(row)
    return jsonify({
        "title": book.title,
        "author": book.author,
        "year": book.year,
        "isbn": book.isbn,
        "review_count": review_count,
        "average_score": average_score
    })
