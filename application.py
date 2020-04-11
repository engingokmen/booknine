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


@app.route("/book-search", methods=["GET", "POST"])
def book_search(page):
    if request.method == 'GET':
        if session['logged_in'] == True:
            # fetch 20 books
            books_initial = db.execute(
                "SELECT * FROM books ORDER BY title ASC LIMIT 20").fetchall()
            return render_template("book-search.html", username=session.get("username"), books=books_initial)
        else:
            return redirect(url_for('index'))
    else:
        if session['logged_in'] == True:
            total_result = 0
            per_page = 20
            total_pages = 0
            page = page
            try:
                title = request.form.get("title")
                author = request.form.get("author")
                isbn = request.form.get("isbn")
            except ValueError:
                return render_template("error.html", message="Invalid search criteria")
            if title != None:
                total_result = db.execute(
                    "SELECT * FROM books WHERE LOWER(title) LIKE (LOWER(:title) || '%')", {"title": title}).rowcount
                total_pages = math.ceil((total_result / per_page))
                print(total_pages)
                search_result = db.execute(
                    "SELECT * FROM books WHERE LOWER(title) LIKE (LOWER(:title) || '%') ORDER BY title ASC LIMIT :per_page", {"title": title, "offset_num": page, "per_page": per_page}).fetchall()
                if len(search_result) == 0:
                    return render_template("error.html", message="Sorry, there is no book in our inventory according to your search criteria")
                else:
                    return render_template("book-search.html", username=session.get("username"), books=search_result, total_pages=total_pages)
            if author != None:
                search_result = db.execute(
                    "SELECT * FROM books WHERE LOWER(author) LIKE (LOWER(:author) || '%') ORDER BY title ASC LIMIT 20 OFFSET offset_num", {"author": author, "offset_num": offset_num}).fetchall()
                if len(search_result) == 0:
                    return render_template("error.html", message="Sorry, there is no book in our inventory according to your search criteria")
                else:
                    return render_template("book-search.html", username=session.get("username"), books=search_result)
            if isbn != None:
                print(isbn)
                search_result = db.execute(
                    "SELECT * FROM books WHERE LOWER(isbn) LIKE (LOWER(:isbn) || '%') ORDER BY title ASC LIMIT 20 OFFSET offset_num", {"isbn": isbn, "offset_num": offset_num}).fetchall()
                print(search_result)
                if len(search_result) == 0:
                    return render_template("error.html", message="Sorry, there is no book in our inventory according to your search criteria")
                else:
                    return render_template("book-search.html", username=session.get("username"), books=search_result)


@app.route("/book-search/<int:page>", methods=["GET"])
def pagination(page, query):


@app.route("/book-search/<book_isbn>")
def book(book_isbn):
    if session['logged_in'] == True:
        return render_template("book.html")
    else:
        return redirect(url_for('index'))
