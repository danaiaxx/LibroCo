from flask import Flask, render_template, request, redirect, flash, url_for, session
from dbhelper import *
import os
import random
import string
import logging

app = Flask(__name__)
uploadfolder = "static/images/pictures"
app.config['UPLOAD_FOLDER'] = uploadfolder
app.secret_key = os.urandom(24) 

from flask import Flask, render_template, request, redirect, session, url_for
import os

def generate_verification_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=5))

def send_verification_code(email, user_code):
    print(f"Sending email to: {email}")
    print(f"Verification code: {user_code}")
    
    try:
        print(f"Email content sent to {email}:")
        print(f"Your verification code is: {user_code}")
        print(f"Verification code {user_code} sent to {email}")
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        flash("There was an error sending the email. Please try again later.", "error")


#LOGIN 
@app.route("/login", methods=['GET', 'POST'])
def login():
    error_message = None

    if request.method == 'POST':
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            error_message = "Please fill in all fields."
            session['error_message'] = error_message
            return redirect(url_for("login"))

        sql = "SELECT * FROM users WHERE user_email = ?"
        user = getprocess(sql, (email,))

        if user:
            if user[0]["user_password"] == password:
                session['user_id'] = user[0]["user_id"]
                
                if user[0]["user_id"] == 1:
                    return redirect(url_for("books")) 
                else:
                    return redirect(url_for("library"))
            else:
                error_message = "Invalid email or password."
                session['error_message'] = error_message  
        else:
            error_message = "No user found with that email."
            session['error_message'] = error_message 

        return redirect(url_for("login")) 

    if 'error_message' in session:
        error_message = session['error_message']
        session.pop('error_message', None)  

    return render_template("login.html", pageheader="Login", error_message=error_message)

#REGISTER
@app.route("/create_account", methods=['GET', 'POST'])
def create_account():
    error_message = None

    if 'error_message' in session:
        error_message = session['error_message']
        session.pop('error_message', None) 

    if request.method == 'POST':
        full_name = request.form.get("fullname")
        email = request.form.get("email")
        password = request.form.get("password")

        if not full_name or not email or not password:
            session['error_message'] = "Please fill in all fields."
            return redirect(url_for("create_account"))

        if "@" not in email or "." not in email.split('@')[-1]:
            session['error_message'] = "Please provide a valid email address."
            return redirect(url_for("create_account"))

        sql = "SELECT * FROM users WHERE user_email = ?"
        user = getprocess(sql, (email,))

        if user:
            session['error_message'] = "Email is already in use."
            return redirect(url_for("create_account"))

        user_code = ''.join(random.choices(string.digits, k=5))

        sql = 'INSERT INTO users (user_name, user_email, user_password, user_code) VALUES (?, ?, ?, ?)'
        params = (full_name, email, password, user_code)
        if postprocess(sql, params): 
            flash("Account created successfully! Please log in.", "success")
            return redirect(url_for("login"))
        else:
            session['error_message'] = "An error occurred while creating your account."
            return redirect(url_for("create_account"))

    return render_template("create_acc.html", error_message=error_message)

#ACCOUNT RECOVERY
@app.route('/account-recovery', methods=['GET', 'POST'])
def account_recov():
    error_message = None 

    if request.method == 'POST':
        email = request.form['email']
        
        if not email:
            error_message = 'Please fill in this field.'
        else:
            sql = "SELECT * FROM users WHERE user_email = ?"
            user = getprocess(sql, (email,))

            if user:
                session['user_email'] = email
                
                user_code = generate_verification_code()
                
                sql_update = "UPDATE users SET user_code = ? WHERE user_email = ?"
                update = postprocess(sql_update, (user_code, email))

                send_verification_code(email, user_code)
                
                flash('Verification code sent to your email!', 'success')
                return redirect(url_for('send_code')) 
            else:
                error_message = 'No user found with that email'  
    
    return render_template('account_recov.html', error_message=error_message)

#SEND CODE
@app.route('/send-code', methods=['GET', 'POST'])
def send_code():
    email = session.get('user_email') 
    
    if not email:
        flash('Session expired. Please start over.', 'error')
        return redirect(url_for('account_recov'))
    
    sql = "SELECT user_code FROM users WHERE user_email = ?"
    result = getprocess(sql, (email,))
    
    if request.method == 'POST':
        entered_code = request.form['user_code']
        
        if result and result[0]['user_code'] == entered_code:
            flash('Code verified successfully. Please reset your password.', 'success')
            return redirect(url_for('reset_pass'))  
        else:
            flash('Invalid verification code. Please try again.', 'error')
    
    return render_template('send_code.html', user_code=result[0]['user_code'] if result else None) 

#CHANGE PASS
@app.route("/reset_pass", methods=['GET', 'POST'])
def reset_pass():
    email = session.get('user_email')
    if not email:
        flash('Session expired. Please start over.', 'error')
        return redirect(url_for('account_recov'))
    
    error_message = None 

    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        if not new_password or not confirm_password:
            error_message = "Please fill in all fields."
            session['error_message'] = error_message  
            return redirect(url_for('reset_pass'))  

        elif new_password != confirm_password:
            error_message = "Passwords don't match. Please try again."
            session['error_message'] = error_message 
            return redirect(url_for('reset_pass'))  
        else:
            sql_update = "UPDATE users SET user_password = ? WHERE user_email = ?"
            update = postprocess(sql_update, (new_password, email))
            
            if update:
                flash("Password has been successfully reset. Please log in.", 'success')
                session.pop('user_email', None)  
                return redirect(url_for('login')) 
            else:
                error_message = "An error occurred while resetting the password. Please try again."
                session['error_message'] = error_message  
                return redirect(url_for('reset_pass'))  

    if 'error_message' in session:
        error_message = session['error_message']
        session.pop('error_message', None)  

    return render_template('reset_pass.html', error_message=error_message)

#LIBRARIAN BOOKS PAGE
@app.route("/books")
def books() -> None:
    if 'user_id' not in session:
        flash("Please log in first.")
        return redirect(url_for("login"))
    
    user_id = session.get('user_id')
    sql = "SELECT * FROM users WHERE user_id = ?"
    user = getprocess(sql, (user_id,))

    if user and user[0]["user_id"] == 1:  # Check if the user is a librarian (assuming user_id == 1 is the librarian)
        search_query = request.args.get('query', '').strip()  # Get the search query from the URL, if any
        
        if search_query:
            # Filter books based on the search query (case-insensitive), checking title, author, or genre
            sql_books = """
            SELECT * FROM books
            WHERE LOWER(book_title) LIKE ? OR LOWER(author) LIKE ? OR LOWER(genre) LIKE ?
            """
            books = getprocess(sql_books, 
                               (f'%{search_query.lower()}%', 
                                f'%{search_query.lower()}%', 
                                f'%{search_query.lower()}%'))
        else:
            books = getall_records('books')  # Fetch all books if no search query

        return render_template("books.html", books=books)
    else:
        flash("You do not have permission to view this page.")
        return redirect(url_for("login"))
    
#ADD BOOK PAGE
@app.route("/addbook")
def addbook():
    return render_template("addbook.html")

#SAVE BOOK
@app.route("/savebook", methods=['GET', 'POST'])
def savebook()-> None:
    if not os.path.exists(uploadfolder):
        os.makedirs(uploadfolder)
    
    book_title = request.form['book_title']
    author = request.form['author']
    publication_year = request.form['publication_year']
    genre = request.form['genre']
    description = request.form['description']

    file = request.files['image_upload']
    if file:
        filename = os.path.join(uploadfolder, file.filename)
        file.save(filename)
    else:
        filename = 'static/images/blank_image.png'

    sql = '''INSERT INTO books (book_title, author, publication_year, genre, description, image) 
             VALUES (?, ?, ?, ?, ?, ?)'''
    params = (book_title, author, publication_year, genre, description, filename)
    ok = postprocess(sql, params)
    
    if ok:
        flash("Registration Successful")
    else:
        flash("Registration Failed")
    
    return redirect("/books")

#REQUESTS PAGE
@app.route("/requests")
def requests():
    return render_template("requests.html")

#READERS PAGE
@app.route("/readers")
def readers():
    all_users = getall_records("users")
    readers = [user for user in all_users if user["user_id"] != 1]

    readers_with_history = []
    for reader in readers:
        reader_id = reader['user_id']

        sql_history = """
            SELECT books.book_title 
            FROM requests
            JOIN books ON requests.book_id = books.book_id
            WHERE requests.user_id = ?
        """
        history = getprocess(sql_history, (reader_id,))

        readers_with_history.append({
            "name": reader["user_name"],
            "contact": reader["user_contact"] or "",
            "email": reader["user_email"],
            "history": [h['book_title'] for h in history]
        })

    # Sort readers by name in ascending order
    readers_with_history = sorted(readers_with_history, key=lambda x: x['name'].lower())

    return render_template("readers.html", readers=readers_with_history)

#READER'S BOOK HISTORY
@app.route("/reader_history/<int:user_id>")
def reader_history(user_id):
    sql_history = """
        SELECT books.book_title
        FROM requests
        JOIN books ON requests.book_id = books.book_id
        WHERE requests.user_id = ?
    """
    history = getprocess(sql_history, (user_id,))
    book_titles = [h['book_title'] for h in history]
    return {"history": book_titles}

#EDIT READER'S PROFILE
@app.route("/edit_reader")
def edit_reader():
    return render_template("editreader.html")

@app.route("/update_reader")
def update_reader():
    return render_template("editreader.html")

#VIEW LIBRARIAN PROFILE
@app.route("/profile")
def profile():
    if 'user_id' not in session:
        flash("Please log in first.")
        return redirect(url_for("login"))
    
    user_id = session.get('user_id')
    sql = "SELECT user_full_name, user_email, user_contact, profile_image FROM users WHERE user_id = ?"
    user = getprocess(sql, (user_id,))
    
    if user:
        user_data = user[0]
        return render_template("profile.html", user=user_data)
    else:
        flash("User not found")
        return redirect(url_for("login"))

#EDIT LIBRARIAN PROFILE
@app.route("/edit_profile")
def edit_profile():
    user_id = request.args.get('id', 1, type=int) 
    sql = "SELECT user_full_name, user_email, user_contact, profile_image FROM users WHERE user_id = ?"
    user = getprocess(sql, (user_id,))
    
    if user:
        user_data = user[0]
        return render_template("editprofile.html", user=user_data)
    else:
        flash("User not found")
        return redirect(url_for("login"))

#LOGOUT
@app.route("/logout", methods=['GET'])
def logout():
    print("Logout initiated.")  
    session.clear() 
    print("Session cleared.") 
    return redirect(url_for("login"))

@app.route("/")
def index():
    return render_template("login.html", pageheader="Login")

#READER'S LIBRARY
@app.route("/library")
def library():
    if 'user_id' not in session:
        flash("Please log in first.")
        return redirect(url_for("login"))

    user_id = session.get('user_id')
    sql = "SELECT * FROM users WHERE user_id = ?"
    user = getprocess(sql, (user_id,))

    if user:
        search_query = request.args.get('query', '').strip()
        
        if search_query:
            # Filter books based on the search query (case-insensitive), checking title, author, or genre
            sql_books = """
            SELECT * FROM books
            WHERE LOWER(book_title) LIKE ? OR LOWER(author) LIKE ? OR LOWER(genre) LIKE ?
            """
            # Search will match any part of book title, author, or genre, case-insensitive
            books = getprocess(sql_books, 
                               (f'%{search_query.lower()}%', 
                                f'%{search_query.lower()}%', 
                                f'%{search_query.lower()}%'))
        else:
            books = getall_records('books')  # Fetch all books if no search query

        return render_template("library.html", books=books)
    else:
        flash("You do not have permission to view this page.")
        return redirect(url_for("login"))
    
#READER'S VIEW BOOK    
@app.route("/viewbook/<int:book_id>")
def view_book(book_id):
    sql = "SELECT * FROM books WHERE book_id = ?"
    book = getprocess(sql, (book_id,))

    if book:
        return render_template("view_book.html", book=book[0])
    else:
        flash("Book not found.", "error")
        return redirect(url_for("books"))
      
@app.route("/book2/<int:book_id>")
def book2(book_id):
    sql = "SELECT * FROM books WHERE book_id = ?"
    book = getprocess(sql, (book_id,))

    if book:
        return render_template("view_book.html", book=book[0])
    else:
        flash("Book not found.", "error")
        return redirect(url_for("books"))

#READER'S BORROWED BOOKS
@app.route("/my_books")
def my_books():
    return render_template("my_books.html")

#READER'S WISHLIST
@app.route("/wishlist")
def wishlist():
    if 'user_id' not in session:
        flash("Please log in first.")
        return redirect(url_for("login"))
    
    user_id = session.get('user_id') 
    
    sql = """
    SELECT b.book_title, b.author, b.publication_year, b.genre
    FROM wishlist w
    JOIN books b ON w.book_id = b.book_id
    WHERE w.user_id = ?
    """
    wishlist_books = getprocess(sql, (user_id,))
    
    return render_template("wishlist.html", wishlist_books=wishlist_books)

@app.route("/add_to_wishlist/<int:book_id>")
def add_to_wishlist(book_id):
    if 'user_id' not in session:
        flash("Please log in first.")
        return redirect(url_for("login"))
    
    user_id = session.get('user_id')
    
    sql = "SELECT * FROM wishlist WHERE user_id = ? AND book_id = ?"
    existing_entry = getprocess(sql, (user_id, book_id))
    
    if not existing_entry:
        sql_insert = "INSERT INTO wishlist (user_id, book_id) VALUES (?, ?)"
        postprocess(sql_insert, (user_id, book_id))
        flash("Book added to wishlist!")
    else:
        flash("This book is already in your wishlist.")
    
    return redirect(url_for("library"))

@app.route("/remove_from_wishlist/<int:book_id>")
def remove_from_wishlist(book_id):
    if 'user_id' not in session:
        flash("Please log in first.")
        return redirect(url_for("login"))
    
    user_id = session.get('user_id')
    
    sql_delete = "DELETE FROM wishlist WHERE user_id = ? AND book_id = ?"
    postprocess(sql_delete, (user_id, book_id))
    flash("Book removed from wishlist.")
    
    return redirect(url_for("wishlist"))

@app.route("/some_route/<int:book_id>")
def some_route(book_id):
    return redirect(url_for("view_book", book_id=book_id))

if __name__ == "__main__":
    app.run(debug=True)