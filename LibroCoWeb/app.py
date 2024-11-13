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
    # Generate a random 5-character verification code
    return ''.join(random.choices(string.ascii_letters + string.digits, k=5))

def send_verification_code(email, user_code):
    # Simulate sending an email by printing out the email content
    print(f"Sending email to: {email}")
    print(f"Verification code: {user_code}")
    
    # Simulate the email content (In practice, this would be sent through an SMTP server or API)
    # You would normally call an email-sending function here (such as using SMTP directly or an external service)
    try:
        # Simulate email sending (in actual implementation, send the email using your service here)
        print(f"Email content sent to {email}:")
        print(f"Your verification code is: {user_code}")
        # In practice, you would call your email API or SMTP server here
        # For example: send_email_via_smtp(email, user_code)
        print(f"Verification code {user_code} sent to {email}")
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        flash("There was an error sending the email. Please try again later.", "error")

@app.route("/login", methods=['GET', 'POST'])
def login():
    error_message = None

    if request.method == 'POST':
        email = request.form.get("email")
        password = request.form.get("password")

        # Validate if the fields are filled in
        if not email or not password:
            error_message = "Please fill in all fields."
            session['error_message'] = error_message
            return redirect(url_for("login"))

        # Retrieve the user from the database based on email
        sql = "SELECT * FROM users WHERE user_email = ?"
        user = getprocess(sql, (email,))

        if user:
            # Check if the password matches the one in the database (without hashing)
            if user[0]["user_password"] == password:
                session['user_id'] = user[0]["user_id"]
                
                # Check if the user is an admin or a reader
                if user[0]["user_id"] == 1:  # Admin (Librarian)
                    return redirect(url_for("books"))  # Admin page
                else:  # Reader
                    return redirect(url_for("library"))  # Reader page (Library)
            else:
                error_message = "Invalid email or password."
                session['error_message'] = error_message  
        else:
            error_message = "No user found with that email."
            session['error_message'] = error_message 

        return redirect(url_for("login")) 

    if 'error_message' in session:
        error_message = session['error_message']
        session.pop('error_message', None)  # Clear the error message from session after use

    return render_template("login.html", pageheader="Login", error_message=error_message)

@app.route("/create_account", methods=['GET', 'POST'])
def create_account():
    error_message = None

    # Check if there is an error message in the session
    if 'error_message' in session:
        error_message = session['error_message']
        session.pop('error_message', None)  # Clear the error message from session after using it

    if request.method == 'POST':
        full_name = request.form.get("fullname")
        email = request.form.get("email")
        password = request.form.get("password")

        # Check if all fields are filled
        if not full_name or not email or not password:
            session['error_message'] = "Please fill in all fields."
            return redirect(url_for("create_account"))

        # Email validation
        if "@" not in email or "." not in email.split('@')[-1]:
            session['error_message'] = "Please provide a valid email address."
            return redirect(url_for("create_account"))

        # Check if the email already exists using the getprocess method from dbhelper
        sql = "SELECT * FROM users WHERE user_email = ?"
        user = getprocess(sql, (email,))

        if user:
            session['error_message'] = "Email is already in use."
            return redirect(url_for("create_account"))

        # Generate a 5-digit user code for readers (not admin)
        user_code = ''.join(random.choices(string.digits, k=5))

        # If no errors, insert new user into the database using the postprocess method from dbhelper
        sql = 'INSERT INTO users (user_name, user_email, user_password, user_code) VALUES (?, ?, ?, ?)'
        params = (full_name, email, password, user_code)
        if postprocess(sql, params):  # Add the new user
            flash("Account created successfully! Please log in.", "success")
            return redirect(url_for("login"))
        else:
            session['error_message'] = "An error occurred while creating your account."
            return redirect(url_for("create_account"))

    return render_template("create_acc.html", error_message=error_message)

@app.route('/account-recovery', methods=['GET', 'POST'])
def account_recov():
    error_message = None  # Initialize error_message variable

    if request.method == 'POST':
        email = request.form['email']
        
        # Check if the email field is empty
        if not email:
            error_message = 'Please fill in this field.'
        else:
            # Check if the email exists in the database
            sql = "SELECT * FROM users WHERE user_email = ?"
            user = getprocess(sql, (email,))

            if user:
                # Store email in session
                session['user_email'] = email
                
                # Generate the verification code
                user_code = generate_verification_code()
                
                # Save the generated code to the database (if needed) for later verification
                sql_update = "UPDATE users SET user_code = ? WHERE user_email = ?"
                update = postprocess(sql_update, (user_code, email))

                # Send the verification code to the user's email
                send_verification_code(email, user_code)
                
                flash('Verification code sent to your email!', 'success')
                return redirect(url_for('send_code'))  # Redirect to send_code.html
            else:
                error_message = 'No user found with that email'  # Set error message if email is not found
    
    return render_template('account_recov.html', error_message=error_message)



@app.route('/send-code', methods=['GET', 'POST'])
def send_code():
    email = session.get('user_email')  # Retrieve email from session
    
    if not email:
        flash('Session expired. Please start over.', 'error')
        return redirect(url_for('account_recov'))
    
    # Retrieve the stored verification code from the database
    sql = "SELECT user_code FROM users WHERE user_email = ?"
    result = getprocess(sql, (email,))
    
    if request.method == 'POST':
        entered_code = request.form['user_code']
        
        # Check if the entered code matches the one stored in the database
        if result and result[0]['user_code'] == entered_code:
            flash('Code verified successfully. Please reset your password.', 'success')
            return redirect(url_for('reset_pass'))  # Redirect to reset_pass.html upon successful code verification
        else:
            flash('Invalid verification code. Please try again.', 'error')
    
    return render_template('send_code.html', user_code=result[0]['user_code'] if result else None)  # Pass the code to the template


@app.route("/reset_pass", methods=['GET', 'POST'])
def reset_pass():
    # Ensure the email is in session, indicating the user is going through the recovery process
    email = session.get('user_email')
    if not email:
        flash('Session expired. Please start over.', 'error')
        return redirect(url_for('account_recov'))
    
    error_message = None  # Initialize error message variable

    # Handle form submission to reset password
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        # Check if any fields are empty
        if not new_password or not confirm_password:
            error_message = "Please fill in all fields."
            session['error_message'] = error_message  # Store the error message in session
            return redirect(url_for('reset_pass'))  # Redirect back to the reset pass page

        # Check if the passwords match
        elif new_password != confirm_password:
            error_message = "Passwords don't match. Please try again."
            session['error_message'] = error_message  # Store the error message in session
            return redirect(url_for('reset_pass'))  # Redirect back to the reset pass page
        else:
            # Update the password in the database
            sql_update = "UPDATE users SET user_password = ? WHERE user_email = ?"
            update = postprocess(sql_update, (new_password, email))
            
            if update:
                flash("Password has been successfully reset. Please log in.", 'success')
                session.pop('user_email', None)  # Clear the email session
                return redirect(url_for('login'))  # Redirect to login page after successful reset
            else:
                error_message = "An error occurred while resetting the password. Please try again."
                session['error_message'] = error_message  # Store the error message in session
                return redirect(url_for('reset_pass'))  # Redirect back to the reset pass page

    # Return the password reset page, passing the error message if any
    if 'error_message' in session:
        error_message = session['error_message']
        session.pop('error_message', None)  # Clear the error message from session after using it

    return render_template('reset_pass.html', error_message=error_message)

@app.route("/books")
def books()-> None:
    if 'user_id' not in session:
        flash("Please log in first.")
        return redirect(url_for("login"))
    
    # If user is logged in, render the books page (admin only, for example)
    user_id = session.get('user_id')
    sql = "SELECT * FROM users WHERE user_id = ?"
    user = getprocess(sql, (user_id,))

    if user and user[0]["user_id"] == 1:  # Admin
        books: list = getall_records('books')
        return render_template("books.html", books=books)
    else:
        flash("You do not have permission to view this page.")
        return redirect(url_for("library"))  # Redirect readers to the library page
    
    
@app.route("/savebook", methods=['GET', 'POST'])
def savebook()-> None:
    if not os.path.exists(uploadfolder):
        os.makedirs(uploadfolder)
    
    # Get book data
    book_title = request.form['book_title']
    author = request.form['author']
    publication_year = request.form['publication_year']
    genre = request.form['genre']
    description = request.form['description']

    # Handle image upload
    file = request.files['image_upload']
    if file:
        # Generate a secure filename for the uploaded file
        filename = os.path.join(uploadfolder, file.filename)
        file.save(filename)
    else:
        # If no file is uploaded, set a default image or handle as needed
        filename = 'static/images/blank_image.png'

    # Save the book data in the database
    sql = '''INSERT INTO books (book_title, author, publication_year, genre, description, image) 
             VALUES (?, ?, ?, ?, ?, ?)'''
    params = (book_title, author, publication_year, genre, description, filename)
    ok = postprocess(sql, params)
    
    if ok:
        flash("Registration Successful")
    else:
        flash("Registration Failed")
    
    return redirect("/books")

@app.route("/addbook")
def addbook():
    return render_template("addbook.html")

@app.route("/requests")
def requests():
    return render_template("requests.html")

@app.route("/readers")
def readers():
    # Get all users except admin
    all_users = getall_records("users")
    readers = [user for user in all_users if user["user_id"] != 1]

    # Retrieve book history for each reader
    readers_with_history = []
    for reader in readers:
        reader_id = reader['user_id']

        # Fetch book titles from the requests table for this reader
        sql_history = """
            SELECT books.book_title 
            FROM requests
            JOIN books ON requests.book_id = books.book_id
            WHERE requests.user_id = ?
        """
        history = getprocess(sql_history, (reader_id,))

        # Append reader details with book history, using empty string if contact is missing
        readers_with_history.append({
            "name": reader["user_name"],
            "contact": reader["user_contact"] or "",
            "email": reader["user_email"],
            "history": [h['book_title'] for h in history]
        })

    return render_template("readers.html", readers=readers_with_history)



@app.route("/reader_history/<int:user_id>")
def reader_history(user_id):
    # Fetch book titles from the requests table for the given user_id
    sql_history = """
        SELECT books.book_title
        FROM requests
        JOIN books ON requests.book_id = books.book_id
        WHERE requests.user_id = ?
    """
    history = getprocess(sql_history, (user_id,))
    book_titles = [h['book_title'] for h in history]
    return {"history": book_titles}

@app.route("/edit_reader")
def edit_reader():
    return render_template("editreader.html")

@app.route("/update_reader")
def update_reader():
    return render_template("editreader.html")

@app.route("/profile")
def profile():
    if 'user_id' not in session:
        flash("Please log in first.")
        return redirect(url_for("login"))
    
    # Fetch user data from the session
    user_id = session.get('user_id')
    sql = "SELECT user_full_name, user_email, user_contact, profile_image FROM users WHERE user_id = ?"
    user = getprocess(sql, (user_id,))
    
    if user:
        user_data = user[0]
        return render_template("profile.html", user=user_data)
    else:
        flash("User not found")
        return redirect(url_for("login"))

@app.route("/edit_profile")
def edit_profile():
    user_id = request.args.get('id', 1, type=int)  # Get user ID from query parameters
    sql = "SELECT user_full_name, user_email, user_contact, profile_image FROM users WHERE user_id = ?"
    user = getprocess(sql, (user_id,))
    
    if user:
        user_data = user[0]
        return render_template("editprofile.html", user=user_data)
    else:
        flash("User not found")
        return redirect(url_for("login"))

@app.route("/logout", methods=['GET'])
def logout():
    print("Logout initiated.")  # Debug print
    session.clear()  # Clear the session
    print("Session cleared.") 
    return redirect(url_for("login"))

@app.route("/")
def index():
    return render_template("login.html", pageheader="Login")

@app.route("/library")
def library():
    if 'user_id' not in session:
        flash("Please log in first.")
        return redirect(url_for("login"))
    
    # Check if the user is a reader (not admin)
    user_id = session.get('user_id')
    sql = "SELECT * FROM users WHERE user_id = ?"
    user = getprocess(sql, (user_id,))

    if user and user[0]["user_id"] != 1:  # Regular user (reader)
        return render_template("library.html")
    else:
        flash("You do not have permission to view this page.")
        return redirect(url_for("books"))  # Redirect admins to the books page
    
@app.route("/viewbook/<int:book_id>")
def view_book(book_id):
    # Fetch book details from the database using the book_id
    sql = "SELECT * FROM books WHERE book_id = ?"
    book = getprocess(sql, (book_id,))

    # Check if the book exists
    if book:
        # If the book exists, render the template with the book details
        return render_template("view_book.html", book=book[0])
    else:
        # If the book doesn't exist, show an error message
        flash("Book not found.", "error")
        return redirect(url_for("books"))
        
@app.route("/book2/<int:book_id>")
def book2(book_id):
    # Fetch book details from the database using the book_id
    sql = "SELECT * FROM books WHERE book_id = ?"
    book = getprocess(sql, (book_id,))

    # Check if the book exists
    if book:
        # If the book exists, render the template with the book details
        return render_template("view_book.html", book=book[0])
    else:
        # If the book doesn't exist, show an error message
        flash("Book not found.", "error")
        return redirect(url_for("books"))

@app.route("/my_books")
def my_books():
    # Your logic for the 'my_books' page
    return render_template("my_books.html")

@app.route("/wishlist")
def wishlist():
    if 'user_id' not in session:
        flash("Please log in first.")
        return redirect(url_for("login"))
    
    # Fetch the user's wishlist from the database
    user_id = session.get('user_id')  # This should be outside the if block
    
    # Query to get all books in the user's wishlist (assuming a `wishlist` table)
    sql = """
    SELECT b.book_title, b.author, b.publication_year, b.genre
    FROM wishlist w
    JOIN books b ON w.book_id = b.book_id
    WHERE w.user_id = ?
    """
    wishlist_books = getprocess(sql, (user_id,))
    
    return render_template("wishlist.html", wishlist_books=wishlist_books)

# Route to add a book to the wishlist
@app.route("/add_to_wishlist/<int:book_id>")
def add_to_wishlist(book_id):
    if 'user_id' not in session:
        flash("Please log in first.")
        return redirect(url_for("login"))
    
    user_id = session.get('user_id')
    
    # Check if the book is already in the wishlist
    sql = "SELECT * FROM wishlist WHERE user_id = ? AND book_id = ?"
    existing_entry = getprocess(sql, (user_id, book_id))
    
    if not existing_entry:
        # If not in wishlist, add it
        sql_insert = "INSERT INTO wishlist (user_id, book_id) VALUES (?, ?)"
        postprocess(sql_insert, (user_id, book_id))
        flash("Book added to wishlist!")
    else:
        flash("This book is already in your wishlist.")
    
    return redirect(url_for("library"))

# Route to remove a book from the wishlist
@app.route("/remove_from_wishlist/<int:book_id>")
def remove_from_wishlist(book_id):
    if 'user_id' not in session:
        flash("Please log in first.")
        return redirect(url_for("login"))
    
    user_id = session.get('user_id')
    
    # Remove the book from the wishlist
    sql_delete = "DELETE FROM wishlist WHERE user_id = ? AND book_id = ?"
    postprocess(sql_delete, (user_id, book_id))
    flash("Book removed from wishlist.")
    
    return redirect(url_for("wishlist"))

@app.route("/some_route/<int:book_id>")
def some_route(book_id):
    # Redirect to view_book with the correct book_id
    return redirect(url_for("view_book", book_id=book_id))

if __name__ == "__main__":
    app.run(debug=True)