import os
import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


os.environ['DATABASE_URL'] = "postgres://dkyqpiphkaurxc:925de28539e0d693231bc829c7bae75e384f70e6ca737ce6f42416d280b50f82@ec2-54-217-204-34.eu-west-1.compute.amazonaws.com:5432/d3nlsgf4egup6j"
KEY = "T1GNWtVnkUqq4k4alkHA"

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


db.execute(
    "CREATE TABLE users (id SERIAL PRIMARY KEY, username VARCHAR NOT NULL, password VARCHAR NOT NULL)")

db.execute(
    "CREATE TABLE reviews (id SERIAL PRIMARY KEY, rating SMALLINT NOT NULL, comment VARCHAR(600), users_id INTEGER REFERENCES users )")

db.execute("CREATE TABLE books (id SERIAL PRIMARY KEY, isbn VARCHAR NOT NULL, title VARCHAR NOT NULL, author VARCHAR NOT NULL, year INTEGER, review_id INTEGER REFERENCES reviews)")
f = open("books.csv")
reader = csv.reader(f)
for isbn, title, author, year in reader:  # loop gives each column a name
    db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
               {"isbn": isbn, "title": title, "author": author, "year": year})  # substitute values from CSV line into SQL command, as per this dict
    print(
        f"Added book: {isbn}, {title}, {author}, {year} ")
db.commit()  # transactions are assumed, so close the transaction finished
