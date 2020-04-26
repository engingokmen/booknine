# Project 1

Web Programming with Python and JavaScript

1. [main.css](~/static/main.css)
   This file just includes 2 lines of style. Remaining styling is provided by [Bootstrap](https://getbootstrap.com/).
2. [layout.html](~/templates/layout.html)
   This is needed for repeating parts on every page like files, styling, navigation etc.
3. [index.html](~/templates/index.html)
   A simple login page contains login form and register link for register.html.
4. [register.html](~/templates/register.html)
   A simple form for registeration. If registeration fails, user is directed to error.html. Otherwise, user is directed to success.html.
5. [book-search.html](~/templates/book-search.html)
   This page is for to search query and display results with pagination.
6. [book.html](~/templates/book.html)
   This page displays book information like title, author, publication year, isbn, goodreads average rating. User can make own review on this page and see list of past reviews of anyone.
7. [success.html](~/templates/success.html)
   This is a generic prompt for a user to inform him/her that current action is resulted with success.
8. [error.html](~/templates/error.html)
   This is a generic prompt for a user to inform him/her that current action is resulted with an error.
9. [application.py](~/application.py)
   This is main file that includes all logic inside.
10. [import.py](~/import.py)
    This file is to create tables and insert books from books.csv file.
