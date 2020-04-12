import os

from flask import Flask, session, render_template, request, redirect, url_for, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import math

os.environ['DATABASE_URL'] = "postgres://dkyqpiphkaurxc:925de28539e0d693231bc829c7bae75e384f70e6ca737ce6f42416d280b50f82@ec2-54-217-204-34.eu-west-1.compute.amazonaws.com:5432/d3nlsgf4egup6j"
KEY = "T1GNWtVnkUqq4k4alkHA"

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
        return render_template("unsuccess.html")
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
        session['logged_in'] = True
        session['username'] = username
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
    if column == "title":
        search_result = db.execute(
            "SELECT * FROM books WHERE LOWER(title) LIKE (LOWER(:query) || '%') ORDER BY title ASC LIMIT :per_page OFFSET :offset_num", {"query": query, "per_page": per_page, "offset_num": page}).fetchall()
        return search_result
    if column == "author":
        search_result = db.execute(
            "SELECT * FROM books WHERE LOWER(author) LIKE (LOWER(:query) || '%') ORDER BY title ASC LIMIT :per_page OFFSET :offset_num", {"query": query, "per_page": per_page, "offset_num": page}).fetchall()
        return search_result
    if column == "isbn":
        search_result = db.execute(
            "SELECT * FROM books WHERE LOWER(isbn) LIKE (LOWER(:query) || '%') ORDER BY title ASC LIMIT :per_page OFFSET :offset_num", {"query": query, "per_page": per_page, "offset_num": page}).fetchall()
        return search_result


@app.route("/book-search", methods=["GET", "POST"])
def book_search():
    if request.method == 'GET':
        if session['logged_in'] == True:
            total_pages = 1
            # fetch 20 books
            books_initial = db.execute(
                "SELECT * FROM books ORDER BY title ASC LIMIT 20").fetchall()
            return render_template("book-search.html", username=session.get("username"), books=books_initial, total_pages=total_pages)
        else:
            return redirect(url_for('index'))
    else:
        if session['logged_in'] == True:
            page = 1
            try:
                query = request.form.get("title")
                author = request.form.get("author")
                isbn = request.form.get("isbn")
            except ValueError:
                return render_template("error.html", message="Invalid search criteria")
        if query != None:
            return redirect(url_for('paginate', title="title", query=query, page=page))


@app.route("/book-search/<title>/<query>/<int:page>")
def paginate(title, query, page):
    if session['logged_in'] == True:
        print(title, query, page)
        total_result = query_total_result("title", title)
        total_pages = math.ceil((total_result / per_page))
        search_result = query_books("title", title, page, per_page)
        return render_template("unsuccess.html")
    return render_template("unsuccess.html")
    render_template("book-search.html", username=session.get("username"))

       if len(search_result) == 0:
            return render_template("error.html", message="Sorry, there is no book in our inventory according to your search criteria")
        else:

    render_template("book-search.html", username=session.get("username"),
                    books=search_result, current_page=page, total_pages=total_pages)

    #   if author != None:
    #     search_result = query_books(author, author, page, per_page)
    #     if len(search_result) == 0:
    #         return render_template("error.html", message="Sorry, there is no book in our inventory according to your search criteria")
    #     else:
    #         return render_template("book-search.html", username=session.get("username"), books=search_result)
    # if isbn != None:
    #     search_result = query_books(author, author, page, per_page)
    #     print(search_result)
    #     if len(search_result) == 0:
    #         return render_template("error.html", message="Sorry, there is no book in our inventory according to your search criteria")
    #     else:
    #         return render_template("book-search.html", username=session.get("username"), books=search_result)
    # total_result = 0
    # per_page = 20
    # total_pages = 0


@app.route("/book-search/<book_isbn>")
def book(book_isbn):
    if session['logged_in'] == True:
        return render_template("book.html")
    else:
        return redirect(url_for('index'))
