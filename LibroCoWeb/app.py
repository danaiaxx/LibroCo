from flask import Flask, render_template, request, redirect, flash, url_for, session
from dbhelper import *
from flask import send_from_directory
import os
import random
import sqlite3
import string
import logging

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__)
uploadfolder = "static/images"
UPLOAD_FOLDER = 'uploads/images/'
app.config['UPLOAD_FOLDER'] = uploadfolder
app.secret_key = os.urandom(24) 

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
                # Store user_id in the session
                session['user_id'] = user[0]["user_id"]
                print("Session user_id set:", session['user_id'])

                session.pop('error_message', None) 

                # Redirect based on user type
                if user[0]["user_id"] == 1:  # Check if the user is a librarian (assuming user_id == 1 is the librarian)
                    return redirect(url_for("books"))
                else:
                    return redirect(url_for("library"))
            else:
                error_message = "Invalid email or password."
        else:
            error_message = "No user found with that email."
        
        session['error_message'] = error_message
        return redirect(url_for("login"))

    # Retrieve error message from session if it exists
    error_message = session.pop('error_message', None)
    return render_template("login.html", pageheader="Login", error_message=error_message)


#REGISTER
@app.route("/create_account", methods=['GET', 'POST'])
def create_account():
    error_message = None

    if 'error_message' in session:
        error_message = session.pop('error_message', None)

    if request.method == 'POST':
        full_name = request.form.get("fullname")
        email = request.form.get("email")
        password = request.form.get("password")

        if not full_name or not email or not password:
            session['error_message'] = "Please fill in all fields."
            return redirect(url_for("create_account"))

        # Validate email format
        if "@" not in email or "." not in email.split('@')[-1]:
            session['error_message'] = "Please provide a valid email address."
            return redirect(url_for("create_account"))

        # Check if email already exists
        sql = "SELECT * FROM users WHERE user_email = ?"
        user = getprocess(sql, (email,))

        if user:
            session['error_message'] = "Email is already in use."
            return redirect(url_for("create_account"))

        # Generate a random user verification code
        user_code = ''.join(random.choices(string.digits, k=5))

        # Insert new user into the database
        sql = 'INSERT INTO users (user_name, user_email, user_password, user_code) VALUES (?, ?, ?, ?)'
        params = (full_name, email, password, user_code)

        if postprocess(sql, params): 
            # Fetch the newly inserted user to retrieve the user_id
            # Use a query to fetch the user using their email
            sql = "SELECT * FROM users WHERE user_email = ?"
            new_user = getprocess(sql, (email,))

            if new_user:
                # Set the user_id into the session
                session['user_id'] = new_user[0]["user_id"]

                flash("Account created successfully! Please log in.", "success")
                return redirect(url_for("login"))
            else:
                session['error_message'] = "Failed to retrieve new user details."
                return redirect(url_for("create_account"))
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

#Librarian View Book
@app.route("/lib_viewbook/<int:book_id>")
def lib_viewbook(book_id):
    book = get_book_by_id(book_id)  # Fetch book details using the modified function
    return render_template("lib_viewbook.html", book=book)

# Add this function in your app.py or appropriate database utility file
def get_book_by_id(book_id):
    conn = sqlite3.connect('libroco.db')  # Your database file
    conn.row_factory = sqlite3.Row  # This allows access by column name
    cursor = conn.cursor()
    query = "SELECT * FROM books WHERE book_id = ?"
    cursor.execute(query, (book_id,))
    book = cursor.fetchone()  # Fetch the row as a dictionary-like object
    conn.close()
    return book


@app.route("/view_book_details/<int:book_id>")
def view_book_details(book_id):
    sql = "SELECT * FROM books WHERE book_id = ?"
    book = getprocess(sql, (book_id,))

    if book:
        return render_template("lib_viewbook.html", book=book[0])
    else:
        flash("Book not found.", "error")
        return redirect(url_for("books"))
    
#Librarian Edit Book
# Route to edit book information
@app.route('/book/edit/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    if request.method == 'POST':
        # Get form data
        book_title = request.form['book_title']
        author = request.form['author']
        publication_year = request.form['publication_year']
        genre = request.form['genre']
        description = request.form['description']

        # Check if a new image file is uploaded
        image_upload = request.files['image_upload']
        image_path = None
        if image_upload and image_upload.filename != '':
            # Generate a unique filename using the book_id to avoid filename conflicts
            image_filename = f"{book_id}_{image_upload.filename}"
            image_path = os.path.join(uploadfolder, image_filename)
            image_upload.save(image_path)

        # If no new image is uploaded, keep the current image path (if exists)
        if not image_path:
            book_data = getprocess("SELECT image FROM books WHERE book_id = ?", (book_id,))
            image_path = book_data[0]['image'] if book_data else 'static/images/blank_image.png'

        # SQL update query
        sql = """
        UPDATE books
        SET book_title = ?, author = ?, publication_year = ?, genre = ?, description = ?, image = ?
        WHERE book_id = ?
        """
        params = (book_title, author, publication_year, genre, description, image_path, book_id)

        # Update the book in the database
        if postprocess(sql, params):
            flash("Book updated successfully")
            return redirect(url_for('view_book_details', book_id=book_id))
        flash("Error updating book")
        return redirect(url_for('edit_book', book_id=book_id))

    # Show edit form if GET request
    book = getprocess("SELECT * FROM books WHERE book_id = ?", (book_id,))
    if book:
        return render_template('edit_book.html', book=dict(book[0]))
    flash("Book not found")
    return redirect(url_for('books'))

# Route to list all books
@app.route('/books')
def list_books():
    books = getall_records("books")
    return render_template('list_books.html', books=books)

#REQUESTS PAGE
def get_requests():
    # Connect to the database
    conn = sqlite3.connect('libroco.db')
    cursor = conn.cursor()
    
    # Query to get all requests along with book and user information
    cursor.execute("""
        SELECT books.book_title, books.author, books.genre, status.availability, users.user_name, requests.request_id
        FROM requests
        JOIN books ON requests.book_id = books.book_id
        JOIN users ON requests.user_id = users.user_id
        LEFT JOIN status ON books.book_id = status.book_id
    """)
    
    # Fetch all results
    requests = cursor.fetchall()
    conn.close()
    
    return requests

@app.route('/requests')
def requests():
    # Get the list of requests
    requests = get_requests()
    return render_template('requests.html', requests=requests)

@app.route('/approve_request', methods=['POST'])
def approve_request():
    request_id = request.form['request_id']
    # Handle approval logic here (e.g., update status to Approved in the database)
    # Redirect back to the requests page
    return redirect(url_for('requests'))

@app.route('/decline_request', methods=['POST'])
def decline_request():
    request_id = request.form['request_id']
    # Handle decline logic here (e.g., delete or update status to Declined in the database)
    # Redirect back to the requests page
    return redirect(url_for('requests'))

@app.route('/uploads/images/<filename>')
def upload_image(filename):
    # Ensure the file exists in the 'uploads/images' folder
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route("/readers")
def readers():
    all_users = getall_records("users")
    readers = [user for user in all_users if user["user_id"] != 1]

    readers_with_history = []
    for reader in readers:
        reader_id = reader['user_id']

        # Fetch book history
        sql_history = """
            SELECT books.book_title 
            FROM requests
            JOIN books ON requests.book_id = books.book_id
            WHERE requests.user_id = ?
        """
        history = getprocess(sql_history, (reader_id,))

        # Fetch user image
        sql_image = """
            SELECT user_image
            FROM profileimages
            WHERE user_id = ?
        """
        user_image = getprocess(sql_image, (reader_id,))
        image_path = f"static/{user_image[0]['user_image']}" if user_image else url_for('static', filename='images/default_profile.png')

        readers_with_history.append({
            "name": reader["user_name"],
            "contact": reader["user_contact"] or "",
            "email": reader["user_email"],
            "history": [h['book_title'] for h in history],
            "user_image": image_path  # Pass the relative image path to the template
        })

    # Sort readers by name
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
        return redirect(url_for("login"))

    user_id = session['user_id']

    sql = """
    SELECT u.user_name, u.user_email, u.user_contact, 
           COALESCE(p.user_image, 'static/images/default_profile.png') AS user_image
    FROM users u
    LEFT JOIN profileimages p ON u.user_id = p.user_id
    WHERE u.user_id = ?
    """
    user = getprocess(sql, (user_id,))

    if user:
        user_data = dict(user[0])
        user_data['user_image'] = user_data['user_image'].replace("\\", "/")
        return render_template("profile.html", user=user_data)
    else:
        flash("Error loading profile.")
        return redirect(url_for("login"))

@app.before_request
def before_request():
    print("Session data:", session)

@app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():
    if 'user_id' not in session:
        flash("Please log in first.")
        return redirect(url_for("login"))

    user_id = session['user_id']

    if user_id != 1:
        flash("You do not have permission to edit this profile.")
        return redirect(url_for("reader_profile"))

    uploadfolder = os.path.join('static', 'images')
    if not os.path.exists(uploadfolder):
        os.makedirs(uploadfolder)

    if request.method == "POST":
        full_name = request.form['full_name']
        contact = request.form['contact']
        email = request.form['email']

        file = request.files.get('user_image')
        if file:
            filename = os.path.join(uploadfolder, file.filename)
            try:
                file.save(filename)  
            except Exception as e:
                flash(f"Error saving the image: {str(e)}")
                filename = 'static/images/default_profile.png'
        else:
            filename = request.form.get('current_image', 'static/images/default_profile.png')

        sql_update_user = """
            UPDATE users
            SET user_name = ?, user_contact = ?, user_email = ?
            WHERE user_id = ?
        """
        params = (full_name, contact, email, user_id)
        result = postprocess(sql_update_user, params)

        check_image_sql = "SELECT * FROM profileimages WHERE user_id = ?"
        existing_image = getprocess(check_image_sql, (user_id,))

        if existing_image:
            sql_update_image = """
                UPDATE profileimages
                SET user_image = ?
                WHERE user_id = ?
            """
            postprocess(sql_update_image, (filename, user_id))
        else:
            sql_insert_image = """
                INSERT INTO profileimages (user_id, user_image)
                VALUES (?, ?)
            """
            postprocess(sql_insert_image, (user_id, filename))

        if result:
            flash("Profile updated successfully.")
        else:
            flash("An error occurred while updating the profile.")

        return redirect(url_for("profile"))

    sql = """
        SELECT u.user_name, u.user_email, u.user_contact, p.user_image
        FROM users u
        LEFT JOIN profileimages p ON u.user_id = p.user_id
        WHERE u.user_id = ?
    """
    user_data = getprocess(sql, (user_id,))

    if user_data:
        user = user_data[0]
        user_data = {
            "full_name": user["user_name"],
            "email": user["user_email"],
            "contact": user["user_contact"],
            "user_image": user["user_image"] if user["user_image"] else 'static/images/default_profile.png'
        }
        return render_template("editprofile.html", user=user_data)
    else:
        flash("Error loading profile.")
        return redirect(url_for("profile"))
    

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
    return render_template('your_template.html', book={
        'book_title': 'Example Book',
        'author': 'Author Name',
        'publication_year': '2024',
        'genre': 'Fiction',
        'description': 'This is a description of the book.',
        'image': 'mermeed.png'
    })

#READER'S LIBRARY
@app.route("/library")
def library():
    if 'user_id' not in session:
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

#VIEW READER PROFILE
@app.route("/reader_profile")
def reader_profile():
    print("Session data in reader profile route:", session) 
    if 'user_id' not in session:
        return redirect(url_for("login"))

    user_id = session.get('user_id')

    sql_user = """
    SELECT u.user_name, u.user_email, u.user_contact, p.user_image
    FROM users u
    LEFT JOIN profileimages p ON u.user_id = p.user_id
    WHERE u.user_id = ?
    """
    user = getprocess(sql_user, (user_id,))

    if user:
        user_data = user[0]

        sql_history = """
        SELECT books.book_title, books.author, books.genre, requests.request_date
        FROM requests
        JOIN books ON requests.book_id = books.book_id
        WHERE requests.user_id = ?
        """
        history = getprocess(sql_history, (user_id,))

        book_history = [
            {
                "title": record['book_title'],
                "author": record['author'],
                "genre": record['genre'],
                "date": record['request_date']
            }
            for record in history
        ]

        return render_template(
            "reader_profile.html",
            user=user_data,
            book_history=book_history
        )
    else:
        flash("Profile not found.")
        return redirect(url_for("login"))

#EDIT READER PROFILE (READER DASHBOARD)
@app.route("/edit_reader_profile", methods=["GET", "POST"])
def edit_reader_profile():
    if 'user_id' not in session:
        flash("Please log in first.")
        return redirect(url_for("login"))

    user_id = session['user_id']

    if user_id == 1:
        flash("Librarians cannot edit reader profiles.")
        return redirect(url_for("reader_profile"))

    uploadfolder = os.path.join('static', 'images')
    if not os.path.exists(uploadfolder):
        os.makedirs(uploadfolder)

    if request.method == "POST":
        full_name = request.form['full_name']
        contact = request.form['contact']
        email = request.form['email']
        
        file = request.files.get('user_image')
        if file:
            filename = os.path.join(uploadfolder, file.filename)
            try:
                file.save(filename)
                filename = 'images/' + file.filename  # Save only the relative path
            except Exception as e:
                flash(f"Error saving the image: {str(e)}")
                filename = 'images/default_profile.png'
        else:
            filename = request.form.get('current_image', 'images/default_profile.png')

                # Store just the filename in the database, not the full path
        relative_path = filename

        sql_update_user = """
            UPDATE users
            SET user_name = ?, user_contact = ?, user_email = ?
            WHERE user_id = ?
        """
        params = (full_name, contact, email, user_id)
        result = postprocess(sql_update_user, params)

        check_image_sql = "SELECT * FROM profileimages WHERE user_id = ?"
        existing_image = getprocess(check_image_sql, (user_id,))
        if existing_image:
            sql_update_image = """
                UPDATE profileimages
                SET user_image = ?
                WHERE user_id = ?
            """
            postprocess(sql_update_image, (relative_path, user_id))
        else:
            sql_insert_image = """
                INSERT INTO profileimages (user_id, user_image)
                VALUES (?, ?)
            """
            postprocess(sql_insert_image, (user_id, relative_path))

        if result:
            flash("Profile updated successfully.")
        else:
            flash("An error occurred while updating the profile.")

        return redirect(url_for("reader_profile"))

    sql = """
        SELECT u.user_name, u.user_email, u.user_contact, p.user_image
        FROM users u
        LEFT JOIN profileimages p ON u.user_id = p.user_id
        WHERE u.user_id = ?
    """
    user_data = getprocess(sql, (user_id,))

    if user_data:
        user = user_data[0]
        user_data = {
            "full_name": user["user_name"],
            "email": user["user_email"],
            "contact": user["user_contact"],
            "user_image": user["user_image"] if user["user_image"] else 'static/images/default_profile.png'
        }
        return render_template("reader-editprofile.html", user=user_data)
    else:
        flash("Error loading profile.")
        return redirect(url_for("reader_profile"))

#READER'S WISHLIST
@app.route("/wishlist")
def wishlist():
    if 'user_id' not in session:
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
    app.config.update(
        SESSION_COOKIE_NAME='my_session',
        SESSION_COOKIE_SECURE=False,  # Set this to True in production
        SESSION_PERMANENT=False
    )
    app.debug = True
    app.run(debug=True)