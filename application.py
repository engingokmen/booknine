import os

from flask import Flask, session, render_template, request, redirect, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

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
        return render_template("index.html", logged_in=session['logged_in'])
    else:
        return render_template("index.html", username=session['username'], logged_in=session['logged_in'])


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


@app.route("/book-search", methods=["GET"])
def book_search():
    if session['logged_in'] == True:
        return render_template("book-search.html")
    else:
        return redirect(url_for('index'))


@app.route("/book-search/search-results", methods=["POST"])
def search_results():
    if session['logged_in'] == True:
        search_query = request.form.get("query")
        print(search_query)
        search_results = db.execute("SELECT * FROM books WHERE title = :title",
                                    {"title": search_query})
        return search_results
