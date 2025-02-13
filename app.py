import os
import random
import string
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'docx', 'xlsx'}

# Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_email_password'

# Initialize extensions
db = SQLAlchemy(app)
mail = Mail(app)

# Ensure uploads directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Models
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Ensure the app context is active when creating the database tables
with app.app_context():
    db.create_all()

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def home():
    return render_template('index.html')

# Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        student_id = request.form['student_id']
        name = request.form['name']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']

        # Check if student already exists
        student = Student.query.filter_by(email=email).first()
        if student:
            flash('Email already registered!', 'danger')
            return redirect(url_for('register'))

        new_student = Student(student_id=student_id, name=name, email=email, username=username, password=password)
        db.session.add(new_student)
        db.session.commit()
        flash('Registration successful!', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        student = Student.query.filter_by(username=username, password=password).first()
        if student:
            session['student_id'] = student.id
            session['student_name'] = student.name  # Store student name for message tracking
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid login details', 'danger')
    
    return render_template('login.html')

# Dashboard Route
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'student_id' not in session:
        return redirect(url_for('login'))

    student = Student.query.get(session['student_id'])

    if request.method == 'POST':
        if 'user_input' in request.form:
            user_input = request.form['user_input']
            student_name = session['student_name']

            # Save the user message with their name to a text file
            with open("messages.txt", "a", encoding="utf-8") as file:
                file.write(f"{student_name}: {user_input}\n")

            flash('Message saved!', 'success')

    return render_template('dashboard.html', student=student)

# Logout Route
@app.route('/logout')
def logout():
    session.clear()  # Clear the session to log out the user
    return redirect(url_for('login'))  # Redirect to the login page

# File Upload Route
@app.route('/upload', methods=['GET', 'POST'])
def upload_page():
    if 'student_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(url_for('upload_page'))

        file = request.files['file']

        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(url_for('upload_page'))

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash('File uploaded successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid file type!', 'danger')
            return redirect(url_for('upload_page'))

    return render_template('upload.html')

# Password Recovery
@app.route('/recover', methods=['GET', 'POST'])
def recover_password():
    if request.method == 'POST':
        email = request.form['email']
        student = Student.query.filter_by(email=email).first()
        if student:
            # Send password recovery email
            new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            student.password = new_password
            db.session.commit()

            msg = Message('Password Recovery', sender='your_email@gmail.com', recipients=[email])
            msg.body = f'Your new password is: {new_password}'
            mail.send(msg)
            flash('Password recovery email sent!', 'success')
        else:
            flash('Email not found', 'danger')

    return render_template('recover.html')

if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", port=10000)
